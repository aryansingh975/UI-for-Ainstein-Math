"""Interactive Multi-Input Batch CLI for the Navigator Module (V2).

Allows submitting multiple student inputs at once (e.g. step-by-step claims or
compound statements) and displays sequential evaluations against the DAG with
their matching nodes and similarity scores.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.navigator.navigator import navigate_dag_with_score
from app.navigator.ranker import DEFAULT_THRESHOLD

# Default to the probability marbles problem
DEFAULT_DAG_PATH = str(
    Path(__file__).resolve().parents[3]
    / "solution_graph/chapter-14/probability/g10-prob-marbles/graph.json"
)


def load_dag(filepath: str) -> dict:
    """Load and parse a solution DAG from a JSON file.

    Args:
        filepath: Path to the solution DAG JSON file.

    Returns:
        The parsed DAG dictionary.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def display_batch_results(
    results: list[tuple[str, dict | str, float]], threshold: float
) -> None:
    """Display evaluation results in a clean sequential view."""
    total = len(results)
    print("\n" + "=" * 70)
    print(f"BATCH EVALUATION RESULTS ({total} Input{'s' if total != 1 else ''} Evaluated)")
    print("=" * 70)

    for idx, (user_input, matched_node, score) in enumerate(results, start=1):
        print(f"\n[INPUT {idx}]: {user_input!r}")
        if isinstance(matched_node, dict):
            node_id = matched_node.get("id", "unknown_node")
            node_label = matched_node.get("label", "")
            label_suffix = f" - '{node_label}'" if node_label else ""
            print(f"-> Matched Node: '{node_id}'{label_suffix}")
            print(json.dumps(matched_node, indent=2, ensure_ascii=False))
            print(f"\n[EVALUATION SCORE]: {score:.4f} (Threshold: {threshold:.2f})")
        else:
            print(f"-> {matched_node}")
            print(f"[TOP SCORE]: {score:.4f} (Below Threshold: {threshold:.2f})")

        if idx < total:
            print("\n" + "-" * 70)

    print("\n" + "=" * 70)


def collect_inputs_interactive() -> list[str]:
    """Collect multiple student inputs one by one until empty line or 'done'."""
    inputs: list[str] = []
    idx = 1
    print("\nEnter student inputs (press [Enter] on an empty line or type 'done' to evaluate):")
    while True:
        try:
            line = input(f"Student Input {idx} > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting input collection.")
            return []

        if not line:
            break

        if line.lower() in ("done", "eval"):
            break

        if line.lower() in ("exit", "quit", "q") and idx == 1:
            return []

        inputs.append(line)
        idx += 1

    return inputs


def interactive_batch_loop(dag: dict, threshold: float) -> None:
    """Run continuous interactive session supporting multi-input batches."""
    meta = dag.get("graph_meta", {})
    problem_text = meta.get("problem_text") or meta.get("title") or "Loaded DAG"
    node_count = len(dag.get("nodes", []))

    print("\n" + "=" * 70)
    print("STATELESS SOCRATIC NAVIGATOR - MULTI-INPUT BATCH CONSOLE (V2)")
    print("=" * 70)
    print(f"Problem:   {problem_text}")
    print(f"Nodes:     {node_count} available nodes")
    print(f"Threshold: {threshold:.2f}")
    print("Submit multiple student inputs together and evaluate against the DAG.")
    print("Type 'exit' or press Ctrl+C to quit.")
    print("=" * 70)

    while True:
        inputs = collect_inputs_interactive()
        if not inputs:
            print("Session ended.")
            break

        batch_results: list[tuple[str, dict | str, float]] = []
        for inp in inputs:
            node, score = navigate_dag_with_score(dag, inp, threshold=threshold)
            batch_results.append((inp, node, score))

        display_batch_results(batch_results, threshold=threshold)


def main() -> None:
    """Parse arguments and launch multi-input batch navigator CLI."""
    parser = argparse.ArgumentParser(
        prog="navigator-cli-v2",
        description="Stateless Socratic Navigator V2 - Evaluate multiple student inputs against a DAG.",
    )
    parser.add_argument(
        "--dag",
        type=str,
        default=DEFAULT_DAG_PATH,
        help=f"Path to the solution DAG JSON file (default: probability marbles problem).",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        type=str,
        default=[],
        help="Optional list of input strings to evaluate immediately as a batch.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Minimum similarity score threshold (default: {DEFAULT_THRESHOLD}).",
    )

    args = parser.parse_args()

    # Step 1: Load DAG
    dag_path = args.dag
    if not dag_path:
        dag_path = input("Enter path to DAG JSON file: ").strip()

    try:
        dag = load_dag(dag_path)
    except FileNotFoundError:
        print(f"Error: DAG file not found at: {dag_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as err:
        print(f"Error: Invalid JSON format in {dag_path}: {err}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Evaluate one-shot batch args or start interactive loop
    if args.inputs:
        batch_results: list[tuple[str, dict | str, float]] = []
        for inp in args.inputs:
            node, score = navigate_dag_with_score(dag, inp, threshold=args.threshold)
            batch_results.append((inp, node, score))
        display_batch_results(batch_results, threshold=args.threshold)
    else:
        interactive_batch_loop(dag, threshold=args.threshold)


if __name__ == "__main__":
    main()
