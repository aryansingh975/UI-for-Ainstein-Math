"""Ranker Pipeline for Navigator v2 (incorporating v1 Ranker).

Implements the scoring hierarchy and collision resolution pipeline:
1. Exact-match scan (Rule 1 — Exact Match Dominance).
2. Fuzzy ranking across all nodes via weighted Jaccard & grounded input coverage.
3. Strict threshold gate.
4. Specificity tie-breaking (Rule 2 — Longest Matching Phrase / most tokens).
"""

from __future__ import annotations

from typing import Any

from app.navigator_02.normalizer import normalize, to_token_set
from app.navigator_02.scorer import exact_match, score_phrase

DEFAULT_THRESHOLD: float = 0.5
_FLOAT_EPS: float = 1e-9


def score_node(
    input_text: str,
    node: dict[str, Any],
) -> tuple[float, str, str]:
    """Return the best score this node achieves against the user input.

    Iterates over every phrase in node["accept"] and returns the maximum
    score achieved. Returns (0.0, "NO_ACCEPT_PHRASES", "") if accept is empty.

    Returns:
        (best_score, match_type, best_phrase)
    """
    accepts = node.get("accept") or []
    if not accepts:
        return 0.0, "NO_ACCEPT_PHRASES", ""

    best_score = -1.0
    best_type = "NONE"
    best_phrase = ""

    for phrase in accepts:
        s, m_type = score_phrase(input_text, phrase)
        tokens = to_token_set(phrase)
        if s > best_score or (
            abs(s - best_score) < _FLOAT_EPS and len(tokens) > len(to_token_set(best_phrase))
        ):
            best_score = s
            best_type = m_type
            best_phrase = phrase

    return max(0.0, best_score), best_type, best_phrase


def rank_all_nodes(
    input_text: str,
    nodes: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], float, str, str]]:
    """Score all nodes and return sorted leaderboard (highest score first).

    Each element: (node, score, match_type, best_phrase)
    """
    scored = []
    for node in nodes:
        s, m_type, best_p = score_node(input_text, node)
        scored.append((node, s, m_type, best_p))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


def _best_matching_phrase_token_count(input_text: str, node: dict[str, Any]) -> int:
    """Return the token count of the highest-scoring accept phrase for tie-breaking."""
    accepts = node.get("accept") or []
    if not accepts:
        return 0

    best_count = 0
    best_score = -1.0
    for phrase in accepts:
        s, _ = score_phrase(input_text, phrase)
        tokens = to_token_set(phrase)
        if s > best_score or (abs(s - best_score) < _FLOAT_EPS and len(tokens) > best_count):
            best_score = s
            best_count = len(tokens)
    return best_count


def resolve_with_score(
    input_text: str,
    nodes: list[dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
) -> tuple[dict[str, Any] | None, float, str, str]:
    """Resolve input string to the winning node using the complete ranker hierarchy.

    Algorithm (from v1 ranker):
        1. Exact-match scan (Rule 1 — Exact Match Dominance):
           If normalized input exactly matches any accept phrase, return that node
           with score 1.0. Ties among exact matches are broken by longest matching phrase.
           Also checks canonical token set equivalence.
        2. Fuzzy ranking:
           Score every node via rank_all_nodes (weighted Jaccard + grounded coverage).
        3. Threshold gate:
           If top score <= threshold -> return (None, top_score, "BELOW_THRESHOLD", top_phrase).
        4. Specificity tie-breaking (Rule 2 — Longest Matching Phrase):
           If multiple nodes share the top score, select the one whose best-matching
           accept phrase has the most tokens.
        5. Return the winner.

    Returns:
        (winning_node_or_None, score, match_type, matched_phrase)
    """
    if not nodes or not input_text.strip():
        return None, 0.0, "EMPTY_INPUT", ""

    # ------------------------------------------------------------------
    # Step 1: Exact-Match Scan (Rule 1 — Exact Match Dominance)
    # ------------------------------------------------------------------
    norm_input = normalize(input_text)
    tokens_input = to_token_set(input_text)
    exact_candidates: list[tuple[dict[str, Any], str, str]] = []  # (node, phrase, match_type)

    for node in nodes:
        for phrase in node.get("accept") or []:
            norm_phrase = normalize(phrase)
            if exact_match(norm_input, norm_phrase):
                exact_candidates.append((node, phrase, "EXACT_STRING_MATCH"))
            elif tokens_input and tokens_input == to_token_set(phrase):
                exact_candidates.append((node, phrase, "EXACT_TOKEN_MATCH"))

    if exact_candidates:
        # Tie-break among exact matches by specificity (longest token count)
        best = max(exact_candidates, key=lambda pair: len(to_token_set(pair[1])))
        return best[0], 1.0, best[2], best[1]

    # ------------------------------------------------------------------
    # Step 2: Fuzzy Ranking
    # ------------------------------------------------------------------
    leaderboard = rank_all_nodes(input_text, nodes)
    if not leaderboard or leaderboard[0][1] == 0.0:
        return None, 0.0, "NO_MATCH", ""

    top_node, top_score, top_type, top_phrase = leaderboard[0]

    # ------------------------------------------------------------------
    # Step 3: Threshold Gate (Strict — must exceed threshold)
    # ------------------------------------------------------------------
    if top_score <= threshold:
        return None, top_score, "BELOW_THRESHOLD", top_phrase

    # ------------------------------------------------------------------
    # Step 4: Specificity Tie-Breaking (Rule 2 — Longest Phrase)
    # ------------------------------------------------------------------
    tied = [
        item for item in leaderboard
        if abs(item[1] - top_score) < _FLOAT_EPS
    ]

    if len(tied) > 1:
        winner = max(
            tied,
            key=lambda item: _best_matching_phrase_token_count(input_text, item[0]),
        )
        return winner[0], top_score, f"{winner[2]}_TIE_BROKEN_BY_SPECIFICITY", winner[3]

    # ------------------------------------------------------------------
    # Step 5: Return Winner
    # ------------------------------------------------------------------
    return top_node, top_score, top_type, top_phrase


def resolve(
    input_text: str,
    nodes: list[dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, Any] | None:
    """Convenience helper returning just the winning node dict or None."""
    node, _, _, _ = resolve_with_score(input_text, nodes, threshold)
    return node
