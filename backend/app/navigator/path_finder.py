"""DAG Path Reachability and Intermediate Node Importance Engine for Navigator v2.

Determines whether a valid forward path exists between two nodes in the DAG,
and inspects all intermediate nodes for importance = 'yes' to detect step jumps.
"""

from __future__ import annotations

from typing import Any

try:
    from .graph_loader import build_adjacency, is_optional_node
except ImportError:
    from graph_loader import build_adjacency, is_optional_node


def find_directed_paths(
    from_node_id: str,
    to_node_id: str,
    dag: dict[str, Any],
) -> list[list[str]]:
    """Find all simple directed paths in the DAG from from_node_id to to_node_id."""
    if from_node_id == to_node_id:
        return []

    adj = build_adjacency(dag)
    paths: list[list[str]] = []

    def dfs(curr: str, current_path: list[str]) -> None:
        if curr == to_node_id:
            paths.append(list(current_path))
            return

        for neighbor in adj.get(curr, []):
            if neighbor not in current_path:  # Guard against cycles
                current_path.append(neighbor)
                dfs(neighbor, current_path)
                current_path.pop()

    dfs(from_node_id, [from_node_id])
    return paths


def select_best_path(
    from_node_id: str,
    to_node_id: str,
    dag: dict[str, Any],
    active_solution_paths: list[list[str]] | None = None,
) -> list[str] | None:
    """Select the most representative path between two nodes.

    Prioritizes subpaths that are already part of the active solution paths
    that the student is traversing. If none match or no active paths are given,
    falls back to the shortest directed path in the DAG.
    """
    # Try finding subpaths in currently active solution paths
    if active_solution_paths:
        candidate_subpaths: list[list[str]] = []
        for sol_path in active_solution_paths:
            if from_node_id in sol_path and to_node_id in sol_path:
                idx_from = sol_path.index(from_node_id)
                idx_to = sol_path.index(to_node_id)
                if idx_to > idx_from:
                    candidate_subpaths.append(sol_path[idx_from : idx_to + 1])

        if candidate_subpaths:
            # Pick the shortest subpath among the active solution paths
            candidate_subpaths.sort(key=len)
            return candidate_subpaths[0]

    # Fallback to all directed paths in DAG
    dag_paths = find_directed_paths(from_node_id, to_node_id, dag)
    if not dag_paths:
        return None

    dag_paths.sort(key=len)
    return dag_paths[0]


def get_skipped_mandatory_nodes(
    path: list[str],
    dag: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return all intermediate nodes along path that are mandatory (optional == False).

    Intermediate nodes are all nodes strictly between path[0] and path[-1].
    """
    if len(path) <= 2:
        return []

    node_map = {n["id"]: n for n in dag.get("nodes", [])}
    skipped: list[dict[str, Any]] = []

    for node_id in path[1:-1]:
        node = node_map.get(node_id)
        if node and not is_optional_node(node):
            skipped.append(node)

    return skipped


# Alias for backward compatibility
get_skipped_important_nodes = get_skipped_mandatory_nodes


def evaluate_transition(
    from_node_id: str,
    to_node_id: str,
    dag: dict[str, Any],
    active_solution_paths: list[list[str]] | None = None,
) -> tuple[bool, list[str], list[dict[str, Any]]]:
    """Evaluate transitioning the navigator pointer from from_node_id to to_node_id.

    Returns:
        (path_exists, chosen_path, skipped_mandatory_nodes)
    """
    if from_node_id == to_node_id:
        # Same node - no move forward
        return False, [], []

    path = select_best_path(from_node_id, to_node_id, dag, active_solution_paths)
    if not path:
        return False, [], []

    skipped_mandatory = get_skipped_mandatory_nodes(path, dag)
    return True, path, skipped_mandatory


def get_skipped_optional_nodes(
    path: list[str],
    dag: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return all intermediate nodes along path that are optional (optional == True).

    Intermediate nodes are all nodes strictly between path[0] and path[-1].
    """
    if len(path) <= 2:
        return []

    node_map = {n["id"]: n for n in dag.get("nodes", [])}
    skipped: list[dict[str, Any]] = []

    for node_id in path[1:-1]:
        node = node_map.get(node_id)
        if node and is_optional_node(node):
            skipped.append(node)

    return skipped


def main(argv: list[str] | None = None) -> None:
    """CLI runner to inspect and evaluate DAG path reachability and step jumps."""
    import argparse
    import sys
    from pathlib import Path

    try:
        from .graph_loader import load_dag, get_all_solution_paths
    except ImportError:
        from graph_loader import load_dag, get_all_solution_paths

    parser = argparse.ArgumentParser(
        description="Inspect and evaluate DAG path transitions, reachability, and step jumps."
    )
    parser.add_argument("graph_path", help="Path to graph.json file.")
    parser.add_argument(
        "from_node",
        nargs="?",
        default=None,
        help="Optional origin node ID. If omitted, enters interactive loop.",
    )
    parser.add_argument(
        "to_node",
        nargs="?",
        default=None,
        help="Optional destination node ID.",
    )
    args = parser.parse_args(argv)

    graph_path = Path(args.graph_path)
    if not graph_path.exists():
        raise FileNotFoundError(f"Graph file not found: {graph_path}")

    dag = load_dag(graph_path)
    nodes = dag.get("nodes", [])
    node_map = {n["id"]: n for n in nodes}
    all_solution_paths = get_all_solution_paths(dag)

    mandatory_nodes = [
        node for node in nodes
        if not is_optional_node(node)
    ]

    def _print_mandatory_nodes() -> None:
        print(f"\nMANDATORY NODES ({len(mandatory_nodes)} nodes with optional=false):")
        for idx, node in enumerate(mandatory_nodes, start=1):
            accept_count = len(node.get("accept", []))
            sample_accept = repr(node["accept"][:2]) if accept_count else "[]"
            print(f"    {idx:2d}. [{node.get('type', 'step')}] id='{node['id']}'")
        print()

    def _evaluate_and_print_transition(src: str, dst: str) -> None:
        print(f"\nEvaluating Transition: '{src}'  ➔  '{dst}'")
        print("-" * 64)

        if src not in node_map:
            print(f"    Error: Source node '{src}' not found in DAG.")
            return
        
        if dst not in node_map:
            print(f"    Error: Destination node '{dst}' not found in DAG.")
            return

        src_node = node_map[src]
        dst_node = node_map[dst]

        if src == dst:
            print(f"    Status:       SAME NODE / SELF-LOOP")
            print(f"    Node:         '{src}' ({src_node.get('label', '')})")
            print(f"    Verdict:      Input matches current node; pointer remains at '{src}'.")
            return

        all_paths = find_directed_paths(src, dst, dag)
        if not all_paths:
            print(f"    Status:      No path exists from '{src}' to '{dst}'.")
            return

        chosen_path = select_best_path(src, dst, dag, active_solution_paths=all_solution_paths)
        assert chosen_path is not None
        hops = len(chosen_path) - 1

        skipped_mandatory = get_skipped_mandatory_nodes(chosen_path, dag)
        skipped_optional = get_skipped_optional_nodes(chosen_path, dag)
        
        if hops == 1:
            status_line = "  DIRECT STEP (Consecutive node along DAG edge)"
        elif not skipped_mandatory:
            status_line = f" LEGAL FORWARD JUMP ({len(skipped_optional)})"
        else:
            status_line = f" STEP JUMP DETECTED ({len(skipped_mandatory)} mandatory node(s) skipped!)"

        print(f"    Status:         {status_line}")

        if skipped_mandatory:
            print(f"\n    🔴 SKIPPED MANDATORY NODES (mandatory steps jump detected):")
            for idx, n in enumerate(skipped_mandatory, 1):
                print(f"    {idx}. id='{n['id']}' ({n.get('label', '')}) [optional=False]")

        if not skipped_mandatory and not skipped_optional:
            print(f"    Intermediate:   None (consecutive transition)")

    if args.from_node and args.to_node:
        # Single-shot evaluation mode
        print("\n" + "=" * 68)
        print("                 PATH FINDER TRANSITION EVALUATION")
        print("=" * 68)
        print(f"Graph File:  {graph_path.name} ({len(nodes)} nodes, {len(all_solution_paths)} solution paths)")
        _print_mandatory_nodes()
        _evaluate_and_print_transition(args.from_node, args.to_node)
        print("=" * 68 + "\n")
    else:
        # Interactive console mode
        print("\n" + "=" * 68)
        print("       PATH FINDER CONSOLE — Test DAG Transitions & Step Jumps")
        print("=" * 68)
        print(f"Graph File: {graph_path.name} ({len(nodes)} nodes, {len(all_solution_paths)} paths)")
        _print_mandatory_nodes()
        print("-" * 68)
        print("Format:     Enter '<from_node> <to_node>' (e.g. 'given_extraction m1_s4')")
        print("-" * 68)

        # If user passed only from_node, pre-fill or ask for to_node
        if args.from_node:
            try:
                dst = input(f"Destination Node from '{args.from_node}' > ").strip()
                if dst:
                    _evaluate_and_print_transition(args.from_node, dst)
            except (KeyboardInterrupt, EOFError):
                pass

        while True:
            try:
                raw = input("\nTransition (from to) > ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting path finder console.")
                break

            if not raw:
                continue

            low = raw.lower()
            if low in ("quit", "exit", "q"):
                print("Exiting path finder console.")
                break
            
            cleaned = raw.replace("->", " ").replace("➔", " ").replace(",", " ")
            parts = cleaned.split()
            if len(parts) == 1:
                src = parts[0]
                try:
                    dst = input(f"Destination Node from '{src}' > ").strip()
                except (KeyboardInterrupt, EOFError):
                    print("\nExiting path finder console.")
                    break
                if not dst:
                    continue
                _evaluate_and_print_transition(src, dst)
            elif len(parts) >= 2:
                _evaluate_and_print_transition(parts[0], parts[1])


if __name__ == "__main__":
    main()
