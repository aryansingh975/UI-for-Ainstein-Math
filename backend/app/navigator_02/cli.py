"""Interactive Terminal Entry Point for Navigator v2.

Allows interactive step-by-step traversal through a solution DAG:
- Checks DAG reachability
- Detects and flags step jumps over important nodes
- Maintains full session history and active solution paths
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.navigator_02.graph_loader import is_important_node
from app.navigator_02.navigator import Navigator, NavigatorResult
from app.navigator_02.ranker import DEFAULT_THRESHOLD

DEFAULT_DAG = str(
    Path(__file__).resolve().parents[3]
    / "solution_graph/chapter-7/ratio-proportion/g08-hegp107-ex001/graph.json"
)


def print_banner(dag: dict, threshold: float) -> None:
    """Print the welcome header and problem statement."""
    meta = dag.get("graph_meta", {})
    problem_text = meta.get("problem_text") or meta.get("title") or "Loaded DAG"
    node_count = len(dag.get("nodes", []))
    edge_count = len(dag.get("edges", []))

    print("\n" + "=" * 76)
    print("           AINSTEIN SOCRATIC NAVIGATOR V2 — INTERACTIVE CONSOLE")
    print("=" * 76)
    print(f"Problem:    {problem_text}")
    print(f"Graph Info: {node_count} nodes | {edge_count} edges | Threshold: {threshold:.2f}")
    print("-" * 76)
    print("Commands:")
    print("  • Type any math reasoning / step to navigate.")
    print("  • 'trail'  -> show breadcrumb trail of visited nodes")
    print("  • 'paths'  -> inspect remaining viable solution paths")
    print("  • 'node'   -> view details of current node")
    print("  • 'hint'   -> show hints for current node")
    print("  • 'reset'  -> restart session from beginning")
    print("  • 'q' / 'exit' / 'quit' -> exit console")
    print("=" * 76)


def render_result(res: NavigatorResult) -> None:
    """Pretty-print a NavigatorResult to the terminal."""
    if res.status == "FIRST_MATCH":
        node = res.matched_node or {}
        print("\n✔ [FIRST STEP MATCHED]")
        print(f"  -> Node ID:    '{node.get('id')}'")
        print(f"     Label:      {node.get('label', '')}")
        print(f"     Importance: {node.get('importance', 'no')}")
        if node.get("prompt"):
            print(f"     Prompt:     \"{node.get('prompt')}\"")
        print(f"  [SCORE]: {res.score:.4f} (Type: {res.match_type})")
        print(f"  [CURRENT POINTER]: {node.get('id')}")

    elif res.status == "ADVANCED":
        node = res.matched_node or {}
        print("\n✔ [STEP ADVANCED]")
        print(f"  -> Node ID:    '{node.get('id')}'")
        print(f"     Label:      {node.get('label', '')}")
        print(f"     Importance: {node.get('importance', 'no')}")
        if node.get("prompt"):
            print(f"     Prompt:     \"{node.get('prompt')}\"")
        print(f"  [SCORE]: {res.score:.4f} (Type: {res.match_type})")
        print(f"  [TRAIL]: {' -> '.join(res.trail)}")

    elif res.status == "STEP_JUMP":
        print("\n" + "!" * 76)
        print("⚠️  STEP JUMP DETECTED. THE FOLLOWING NODE HAS BEEN SKIPPED ->")
        for skipped in res.skipped_nodes:
            print(f"   • Node ID:    '{skipped.get('id')}'")
            print(f"     Label:      {skipped.get('label', '')}")
            print(f"     Importance: {skipped.get('importance', 'no')}")
            if skipped.get("prompt"):
                print(f"     Prompt:     \"{skipped.get('prompt')}\"")
        print("\nIntermediate node detected with high importance.")
        print("Please address the skipped node first before proceeding.")
        print("!" * 76)
        curr_id = res.current_node.get("id") if res.current_node else "None"
        print(f"[POINTER UNCHANGED]: Still at '{curr_id}'")

    elif res.status == "INVALID_PATH":
        print("\n✖ INVALID input, give a valid input.")
        curr_id = res.current_node.get("id") if res.current_node else "None"
        matched_id = res.matched_node.get("id") if res.matched_node else "Unknown"
        print(f"  (No directed forward path exists in DAG from '{curr_id}' to '{matched_id}')")
        print(f"[POINTER UNCHANGED]: Still at '{curr_id}'")

    elif res.status == "ALREADY_AT_CURRENT_NODE":
        curr_id = res.current_node.get("id") if res.current_node else "None"
        print(f"\nℹ You are already at node '{curr_id}'. Please enter the next step to move forward.")

    elif res.status == "NO_MATCH":
        print("\n✖ No matching node found. Please try again.")
        print(f"  [TOP SCORE]: {res.score:.4f} (Below threshold)")


def interactive_loop(nav: Navigator) -> None:
    """Run interactive REPL session with the user."""
    print_banner(nav.dag, nav.threshold)

    while True:
        curr_id = nav.current_node["id"] if nav.current_node else "start"
        try:
            user_input = input(f"\n[{curr_id}] Student Input > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting navigator console.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("exit", "quit", "q"):
            print("\nExiting session.")
            print(f"Final trail visited: {nav.session.get_trail_display()}")
            break

        if cmd == "trail":
            print(f"\nVisited Trail: {nav.session.get_trail_display()}")
            continue

        if cmd == "paths":
            print(f"\nActive Solution Paths ({len(nav.session.active_solution_paths)} viable):")
            for idx, p in enumerate(nav.session.active_solution_paths, 1):
                print(f"  {idx}. {' -> '.join(p)}")
            continue

        if cmd == "node":
            if nav.current_node:
                print("\n[CURRENT NODE DETAILS]")
                print(json.dumps(nav.current_node, indent=2, ensure_ascii=False))
            else:
                print("\nNo node has been visited yet. Provide your first input.")
            continue

        if cmd == "hint":
            if nav.current_node:
                hints = nav.current_node.get("hints") or []
                if hints:
                    print(f"\nHint: {hints[0]}")
                else:
                    print("\nNo hints available for this node.")
            else:
                print("\nNo current node.")
            continue

        if cmd == "reset":
            nav.reset()
            print("\nSession reset. Ready for first input.")
            continue

        if cmd == "help":
            print("\nCommands: trail, paths, node, hint, reset, quit")
            continue

        # Process student input
        res = nav.process_input(user_input)
        render_result(res)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="navigator-v2",
        description="Ainstein Socratic Navigator v2 — Interactive, path-coherent DAG traversal.",
    )
    parser.add_argument(
        "--dag",
        type=str,
        default=DEFAULT_DAG,
        help=f"Path to solution DAG JSON file (default: {DEFAULT_DAG}).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Minimum similarity score threshold (default: {DEFAULT_THRESHOLD}).",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        type=str,
        default=[],
        help="Optional list of input strings to run sequentially in non-interactive mode.",
    )

    args = parser.parse_args()

    # Verify DAG file
    dag_path = Path(args.dag)
    if not dag_path.exists():
        print(f"Error: DAG file not found: {dag_path}", file=sys.stderr)
        sys.exit(1)

    try:
        nav = Navigator(dag_source=dag_path, threshold=args.threshold)
    except Exception as err:
        print(f"Error initializing Navigator: {err}", file=sys.stderr)
        sys.exit(1)

    if args.inputs:
        # Non-interactive sequential execution
        print_banner(nav.dag, nav.threshold)
        for inp in args.inputs:
            print(f"\n>>> Input: {inp!r}")
            res = nav.process_input(inp)
            render_result(res)
    else:
        # Interactive REPL mode
        interactive_loop(nav)


if __name__ == "__main__":
    main()
