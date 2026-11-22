"""Scoring Hierarchy & Collision Resolution.

Scores the user input against every node in the DAG and applies hierarchy
rules and threshold guardrails to pick a single winner.
"""

from __future__ import annotations

from typing import Union

from navigator.normalizer import normalize, to_token_set
from navigator.scorer import exact_match, score_phrase


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

