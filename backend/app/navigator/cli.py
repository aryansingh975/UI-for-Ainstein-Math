"""Interactive Terminal Entry Point for the Navigator Module.

Performs linear matching from terminal input:
    1. Loads a solution DAG from a specified JSON file path.
    2. Accepts student input strings directly from the console prompt.
    3. Evaluates similarity and matches against the solution DAG.
    4. Prints the resulting matched node dictionary, followed immediately
       by the calculated evaluation score.
"""

from __future__ import annotations

import argparse
import json
import sys

from app.navigator.navigator import navigate_dag_with_score
from app.navigator.ranker import DEFAULT_THRESHOLD


def load_dag(filepath: str) -> dict:
    """Load and parse a solution DAG from a JSON file.

    Args:
        filepath: Path to the solution DAG JSON file.

    Returns:
        The parsed DAG dictionary.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def print_evaluation(result: dict | str, score: float, threshold: float) -> None:
    """Print the evaluated node dictionary followed immediately by the score."""
    if isinstance(result, dict):
        print("\n[MATCHED NODE]")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n[EVALUATION SCORE]: {score:.4f} (Threshold: {threshold:.2f})")
    else:
        print(f"\n{result}")
        print(f"[TOP SCORE]: {score:.4f} (Below threshold: {threshold:.2f})")


def interactive_loop(dag: dict, threshold: float) -> None:
    """Run a continuous interactive REPL session."""
    meta = dag.get("graph_meta", {})
    problem_text = meta.get("problem_text") or meta.get("title") or "Loaded DAG"
    node_count = len(dag.get("nodes", []))

    print("\n" + "=" * 70)
    print("STATELESS SOCRATIC NAVIGATOR - INTERACTIVE CONSOLE")
    print("=" * 70)
    print(f"Problem:   {problem_text}")
    print(f"Nodes:     {node_count} available nodes")
    print(f"Threshold: {threshold:.2f}")
    print("Type any student response to evaluate (or 'exit' / 'quit' to quit).")
    print("=" * 70)

    while True:
        try:
            user_input = input("\nStudent Input > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting navigator console.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("Exiting navigator console.")
            break

        result, score = navigate_dag_with_score(dag, user_input, threshold=threshold)
        print_evaluation(result, score, threshold)


def main() -> None:
    """Parse arguments and launch the evaluation terminal."""
    parser = argparse.ArgumentParser(
        prog="navigator-cli",
        description="Stateless Socratic Navigator - Match student input to a DAG node and display score.",
    )
    parser.add_argument(
        "--dag",
        type=str,
        default=None,
        help="Path to the solution DAG JSON file. Prompts if omitted.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=str,
        default=None,
        help="Optional input string for one-shot evaluation. If omitted, starts interactive console.",
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

    # Step 2: One-shot or interactive mode
    if args.input is not None:
        result, score = navigate_dag_with_score(dag, args.input, threshold=args.threshold)
        print_evaluation(result, score, args.threshold)
    else:
        interactive_loop(dag, threshold=args.threshold)


if __name__ == "__main__":
    main()
