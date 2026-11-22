"""Scoring Hierarchy & Collision Resolution.

Scores the user input against every node in the DAG and applies hierarchy
rules and threshold guardrails to pick a single winner.
"""

from __future__ import annotations

from typing import Union

from app.navigator.normalizer import normalize, to_token_set
from app.navigator.scorer import exact_match, score_phrase


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLD: float = 0.5
"""Default minimum similarity score.  The highest-scoring node must
*strictly exceed* this value, otherwise the navigator returns "No node found"."""

_FLOAT_EPS: float = 1e-9
"""Epsilon for floating-point tie detection."""


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def score_node(input_text: str, node: dict) -> float:
    """Return the best score this node achieves against the input.

    Iterates over every phrase in ``node["accept"]`` and returns the maximum
    ``score_phrase`` value.  Returns 0.0 if ``accept`` is empty or missing.
    """
    accepts = node.get("accept") or []
    if not accepts:
        return 0.0
    return max(score_phrase(input_text, phrase) for phrase in accepts)


def rank_all_nodes(
    input_text: str, nodes: list[dict]
) -> list[tuple[dict, float]]:
    """Score every node and return a descending-sorted leaderboard.

    Returns:
        List of ``(node_dict, best_score)`` tuples, highest score first.
    """
    scored = [(node, score_node(input_text, node)) for node in nodes]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Helpers for tie-breaking
# ---------------------------------------------------------------------------

def _best_matching_phrase_token_count(input_text: str, node: dict) -> int:
    """Return the token count of the longest matching accept phrase.

    Used for Rule 2 tie-breaking: among nodes with equal scores, the one
    whose best-matching accept phrase has the most tokens wins.
    """
    accepts = node.get("accept") or []
    if not accepts:
        return 0

    best_count = 0
    best_score = -1.0
    for phrase in accepts:
        s = score_phrase(input_text, phrase)
        tokens = to_token_set(phrase)
        if s > best_score or (abs(s - best_score) < _FLOAT_EPS and len(tokens) > best_count):
            best_score = s
            best_count = len(tokens)
    return best_count


# ---------------------------------------------------------------------------
# Resolution Pipeline
# ---------------------------------------------------------------------------

def resolve_with_score(
    input_text: str, nodes: list[dict], threshold: float = DEFAULT_THRESHOLD
) -> tuple[Union[dict, str], float]:
    """Complete collision resolution pipeline returning both node and score.

    Algorithm:
        1. **Exact-match scan (Rule 1):** Iterate all nodes.  If the normalized
           input exactly matches any accept phrase, return that node with score 1.0.
           Ties broken by longest matching phrase.
        2. **Fuzzy ranking:** Score every node via ``rank_all_nodes``.
        3. **Threshold gate:** If top score <= threshold -> ``("No node found", top_score)``.
        4. **Tie-breaking (Rule 2):** If multiple nodes share the top score,
           select the one whose best-matching accept phrase has the most tokens.
        5. **Return the winner and score.**

    Returns:
        Tuple of ``(winning_node_dict | "No node found", top_score)``.
    """
    if not nodes:
        return "No node found", 0.0

    # ------------------------------------------------------------------
    # Pass 1: Exact-match scan (Rule 1 — Exact Match Dominance)
    # ------------------------------------------------------------------
    norm_input = normalize(input_text)
    exact_candidates: list[tuple[dict, str]] = []  # (node, matched_phrase)

    for node in nodes:
        for phrase in node.get("accept") or []:
            if exact_match(norm_input, normalize(phrase)):
                exact_candidates.append((node, phrase))

    if exact_candidates:
        best = max(exact_candidates, key=lambda pair: len(to_token_set(pair[1])))
        return best[0], 1.0

    # ------------------------------------------------------------------
    # Pass 2: Fuzzy ranking
    # ------------------------------------------------------------------
    leaderboard = rank_all_nodes(input_text, nodes)
    top_node, top_score = leaderboard[0]

    # ------------------------------------------------------------------
    # Step 3: Threshold gate (strict — must *exceed* threshold)
    # ------------------------------------------------------------------
    if top_score <= threshold:
        return "No node found", top_score

    # ------------------------------------------------------------------
    # Step 4: Tie-breaking (Rule 2 — Specificity / longest phrase)
    # ------------------------------------------------------------------
    tied = [
        (node, score)
        for node, score in leaderboard
        if abs(score - top_score) < _FLOAT_EPS
    ]

    if len(tied) > 1:
        winner = max(
            tied,
            key=lambda pair: _best_matching_phrase_token_count(input_text, pair[0]),
        )
        return winner[0], top_score

    # ------------------------------------------------------------------
    # Step 5: Return the winner
    # ------------------------------------------------------------------
    return top_node, top_score


def resolve(
    input_text: str, nodes: list[dict], threshold: float = DEFAULT_THRESHOLD
) -> Union[dict, str]:
    """Complete collision resolution pipeline returning just the winning node."""
    node, _ = resolve_with_score(input_text, nodes, threshold)
    return node
