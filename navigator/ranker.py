"""Ranker Pipeline for Navigator v2 (incorporating v1 Ranker).

Implements the scoring hierarchy and collision resolution pipeline:
1. Exact-match scan (Rule 1 — Exact Match Dominance).
2. Fuzzy ranking across all nodes via weighted Jaccard & grounded input coverage.
3. Strict threshold gate.
4. Specificity tie-breaking (Rule 2 — Longest Matching Phrase / most tokens).
"""

from __future__ import annotations

from typing import Any

try:
    from .normalizer import normalize, to_token_set
    from .scorer import exact_match, score_phrase
except ImportError:
    from normalizer import normalize, to_token_set
    from scorer import exact_match, score_phrase

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


def resolve_with_details(
    input_text: str,
    nodes: list[dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
) -> tuple[dict[str, Any] | None, float, str, str, list[dict[str, Any]]]:
    """Resolve input string to winning node and return tie details if a tie occurred.

    Algorithm (from v1 ranker):
        1. Exact-match scan (Rule 1 — Exact Match Dominance):
           If normalized input matches any accept phrase, return that node with score 1.0.
           Ties among exact matches are broken by specificity (longest matching phrase)
           and then DAG order.
        2. Fuzzy ranking:
           Score every node via rank_all_nodes (weighted Jaccard + grounded coverage).
        3. Threshold gate:
           If top score <= threshold -> return (None, top_score, "BELOW_THRESHOLD", top_phrase, []).
        4. Specificity tie-breaking (Rule 2 — Longest Matching Phrase):
           If multiple nodes share the top score (within 1e-9), select the one whose
           best-matching accept phrase has the most tokens.
        5. Return the winner.

    Returns:
        (winning_node_or_None, score, match_type, matched_phrase, tied_candidates)
        where tied_candidates is a list of candidate dicts when 2 or more nodes tied
        for the top score, or an empty list if there was a unique winner or no match.
        Each candidate dict has keys: {"node", "score", "match_type", "phrase", "token_count"}.
    """
    if not nodes or not input_text.strip():
        return None, 0.0, "EMPTY_INPUT", "", []

    # ------------------------------------------------------------------
    # Step 1: Exact-Match Scan (Rule 1 — Exact Match Dominance)
    # ------------------------------------------------------------------
    norm_input = normalize(input_text)
    tokens_input = to_token_set(input_text)
    exact_candidates_map: dict[str, dict[str, Any]] = {}

    for node in nodes:
        node_id = str(node.get("id"))
        for phrase in node.get("accept") or []:
            norm_phrase = normalize(phrase)
            m_type = None
            if exact_match(norm_input, norm_phrase):
                m_type = "EXACT_STRING_MATCH"
            elif tokens_input and tokens_input == to_token_set(phrase):
                m_type = "EXACT_TOKEN_MATCH"

            if m_type:
                t_count = len(to_token_set(phrase))
                if node_id not in exact_candidates_map or t_count > exact_candidates_map[node_id]["token_count"]:
                    exact_candidates_map[node_id] = {
                        "node": node,
                        "score": 1.0,
                        "match_type": m_type,
                        "phrase": phrase,
                        "token_count": t_count,
                    }

    if exact_candidates_map:
        candidates = list(exact_candidates_map.values())
        if len(candidates) > 1:
            winner_cand = max(candidates, key=lambda c: c["token_count"])
            match_type = f"{winner_cand['match_type']}_TIE_BROKEN_BY_SPECIFICITY"
            return winner_cand["node"], 1.0, match_type, winner_cand["phrase"], candidates
        else:
            sole_cand = candidates[0]
            return sole_cand["node"], 1.0, sole_cand["match_type"], sole_cand["phrase"], []

    # ------------------------------------------------------------------
    # Step 2: Fuzzy Ranking
    # ------------------------------------------------------------------
    leaderboard = rank_all_nodes(input_text, nodes)
    if not leaderboard or leaderboard[0][1] == 0.0:
        return None, 0.0, "NO_MATCH", "", []

    top_node, top_score, top_type, top_phrase = leaderboard[0]

    # ------------------------------------------------------------------
    # Step 3: Threshold Gate (Strict — must exceed threshold)
    # ------------------------------------------------------------------
    if top_score <= threshold:
        return None, top_score, "BELOW_THRESHOLD", top_phrase, []

    # ------------------------------------------------------------------
    # Step 4: Specificity Tie-Breaking (Rule 2 — Longest Phrase)
    # ------------------------------------------------------------------
    tied_items = [
        item for item in leaderboard
        if abs(item[1] - top_score) < _FLOAT_EPS
    ]

    if len(tied_items) > 1:
        tied_candidates = [
            {
                "node": item[0],
                "score": item[1],
                "match_type": item[2],
                "phrase": item[3],
                "token_count": _best_matching_phrase_token_count(input_text, item[0]),
            }
            for item in tied_items
        ]
        winner_cand = max(
            tied_candidates,
            key=lambda c: c["token_count"],
        )
        match_type = f"{winner_cand['match_type']}_TIE_BROKEN_BY_SPECIFICITY"
        return winner_cand["node"], top_score, match_type, winner_cand["phrase"], tied_candidates

    # ------------------------------------------------------------------
    # Step 5: Return Winner (Unique match, no tie)
    # ------------------------------------------------------------------
    return top_node, top_score, top_type, top_phrase, []


def resolve_with_score(
    input_text: str,
    nodes: list[dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
) -> tuple[dict[str, Any] | None, float, str, str]:
    """Resolve input string to the winning node using the complete ranker hierarchy.

    Returns:
        (winning_node_or_None, score, match_type, matched_phrase)
    """
    winner, score, match_type, matched_phrase, _ = resolve_with_details(
        input_text, nodes, threshold=threshold
    )
    return winner, score, match_type, matched_phrase


def resolve(
    input_text: str,
    nodes: list[dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, Any] | None:
    """Convenience helper returning just the winning node dict or None."""
    node, _, _, _ = resolve_with_score(input_text, nodes, threshold)
    return node


def main(argv: list[str] | None = None) -> None:
    """CLI runner to inspect the Ranker pipeline standalone."""
    import argparse
    import json
    import sys
    from pathlib import Path

    try:
        from .graph_loader import load_dag
    except ImportError:
        from graph_loader import load_dag

    parser = argparse.ArgumentParser(description="Evaluate student input against DAG nodes using Ranker.")
    parser.add_argument("graph_path", help="Path to graph.json file.")
    parser.add_argument(
        "user_input",
        nargs="?",
        default=None,
        help="Optional student input string. If omitted, enters interactive loop.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Minimum score threshold (default: {DEFAULT_THRESHOLD}).",
    )
    args = parser.parse_args(argv)

    graph_path = Path(args.graph_path)
    if not graph_path.exists():
        raise FileNotFoundError(f"Graph file not found: {graph_path}")

    dag = load_dag(graph_path)
    nodes = dag.get("nodes", [])

    def _evaluate_and_print(inp: str) -> None:
        # 1. Print tokens from normalizer
        tokens = sorted(to_token_set(inp))
        print(f"  Tokens: {tokens}")
        print("-" * 68)

        # 2. Existing ranker evaluation output
        winner, score, match_type, matched_phrase, tied = resolve_with_details(
            inp, nodes, threshold=args.threshold
        )
        if len(tied) > 1:
            print(f"  ⚡ TIE DETECTED: {len(tied)} nodes tied with score {score:.4f}:")
            for idx, cand in enumerate(tied, start=1):
                c_node = cand["node"]
                c_phrase = cand["phrase"]
                c_tokens = cand["token_count"]
                c_type = cand["match_type"]
                print(
                    f"     {idx}. id='{c_node['id']}' ({c_node.get('label', '')})\n"
                    f"        Matched phrase: {c_phrase!r} ({c_tokens} token{'s' if c_tokens != 1 else ''}) | Match: {c_type}"
                )
            print("     -> Resolving tie using Rule 2 (Specificity: highest token count / DAG order)...\n")
            if winner:
                print(f"  ✔ Winning Node: '{winner['id']}' ({winner.get('label', '')})")
                print(f"    Score:        {score:.4f}  |  Type: {match_type}")
                print(f"    Phrase:       {matched_phrase!r}")
        elif winner:
            print(f"  ✔ Matched Node: '{winner['id']}' ({winner.get('label', '')})")
            print(f"    Score:        {score:.4f}  |  Type: {match_type}")
            print(f"    Phrase:       {matched_phrase!r}")
        else:
            print(f"  ✖ No Match:     Score {score:.4f}  |  Reason: {match_type}")
            if matched_phrase:
                print(f"    Closest:      {matched_phrase!r}")

    if args.user_input:
        # Single-shot evaluation mode
        print("\n" + "=" * 68)
        print("                      RANKER PIPELINE EVALUATION")
        print("=" * 68)
        print(f"Student Input: {args.user_input!r}")
        print(f"Graph File:    {graph_path.name} ({len(nodes)} nodes)  |  Threshold: {args.threshold:.2f}")
        print("-" * 68)
        winner, score, match_type, matched_phrase, tied = resolve_with_details(
            args.user_input, nodes, threshold=args.threshold
        )
        _evaluate_and_print(args.user_input)

        leaderboard = rank_all_nodes(args.user_input, nodes)
        print("\nFULL RANKED LEADERBOARD (Top 5):")
        tied_ids = {c["node"]["id"] for c in tied} if tied else set()
        for idx, (node, s, m_type, phrase) in enumerate(leaderboard[:5], start=1):
            if winner and node["id"] == winner["id"]:
                tag = " [WINNER]"
            elif node["id"] in tied_ids:
                tag = " [TIED]"
            else:
                tag = ""
            print(f"  {idx:2d}. id='{node['id']}'{tag}")
            print(f"      Score: {s:.4f} | Type: {m_type} | Phrase: {phrase!r}")
        print("=" * 68 + "\n")
    else:
        # Interactive single in-out terminal loop
        print("\n" + "=" * 68)
        print("       RANKER INTERACTIVE CONSOLE — Supply input to see output")
        print("                 (Type 'quit', 'exit', or 'q' to stop)")
        print("=" * 68)
        print(f"Graph File: {graph_path.name} ({len(nodes)} nodes)  |  Threshold: {args.threshold:.2f}")
        print("-" * 68)

        while True:
            try:
                raw = input("\nStudent Input > ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting ranker console.")
                break

            if not raw:
                continue
            if raw.lower() in ("quit", "exit", "q"):
                print("Exiting ranker console.")
                break

            _evaluate_and_print(raw)
        print("=" * 68 + "\n")


if __name__ == "__main__":
    main()

