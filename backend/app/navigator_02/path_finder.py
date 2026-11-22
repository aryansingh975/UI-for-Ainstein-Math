"""DAG Path Reachability and Intermediate Node Importance Engine for Navigator v2.

Determines whether a valid forward path exists between two nodes in the DAG,
and inspects all intermediate nodes for importance = 'yes' to detect step jumps.
"""

from __future__ import annotations

from typing import Any

from app.navigator_02.graph_loader import build_adjacency, is_important_node


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


def get_skipped_important_nodes(
    path: list[str],
    dag: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return all intermediate nodes along path that have importance = 'yes'.

    Intermediate nodes are all nodes strictly between path[0] and path[-1].
    """
    if len(path) <= 2:
        return []

    node_map = {n["id"]: n for n in dag.get("nodes", [])}
    skipped: list[dict[str, Any]] = []

    for node_id in path[1:-1]:
        node = node_map.get(node_id)
        if node and is_important_node(node):
            skipped.append(node)

    return skipped


def evaluate_transition(
    from_node_id: str,
    to_node_id: str,
    dag: dict[str, Any],
    active_solution_paths: list[list[str]] | None = None,
) -> tuple[bool, list[str], list[dict[str, Any]]]:
    """Evaluate transitioning the navigator pointer from from_node_id to to_node_id.

    Returns:
        (path_exists, chosen_path, skipped_important_nodes)
    """
    if from_node_id == to_node_id:
        # Same node - no move forward
        return False, [], []

    path = select_best_path(from_node_id, to_node_id, dag, active_solution_paths)
    if not path:
        return False, [], []

    skipped_important = get_skipped_important_nodes(path, dag)
    return True, path, skipped_important


def get_skipped_optional_nodes(
    path: list[str],
    dag: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return all intermediate nodes along path that are optional."""
    if len(path) <= 2:
        return []

    node_map = {n["id"]: n for n in dag.get("nodes", [])}
    skipped: list[dict[str, Any]] = []

    for node_id in path[1:-1]:
        node = node_map.get(node_id)
        if node:
            val = node.get("optional")
            if val is True or str(val).lower() in ("true", "1", "yes") or node.get("importance") == "no":
                skipped.append(node)

    return skipped


def main(argv: list[str] | None = None) -> None:
    """CLI runner to inspect and evaluate DAG path reachability and step jumps."""
    import argparse
    import sys
    from pathlib import Path

    try:
        from app.navigator_02.graph_loader import load_dag, get_all_solution_paths
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

    def _is_opt(n: dict[str, Any]) -> bool:
        val = n.get("optional")
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.strip().lower() in ("true", "yes", "1")
        return n.get("importance") != "yes"

    mandatory_nodes = [
        node for node in nodes
        if not _is_opt(node)
    ]

    def _print_mandatory_nodes() -> None:
        print(f"\n1. Mandatory Nodes ({len(mandatory_nodes)} nodes with optional=false):")
        for idx, node in enumerate(mandatory_nodes, start=1):
            accept_count = len(node.get("accept", []))
            sample_accept = repr(node["accept"][:2]) if accept_count else "[]"
            print(f"  {idx:2d}. [{node.get('type', 'step')}] id='{node['id']}' (optional=False)")
            print(f"      Label:  {node.get('label', 'N/A')}")
            print(f"      Accept: {accept_count} phrase(s) -> {sample_accept}")
        print()

    def _print_all_nodes() -> None:
        print("\nALL AVAILABLE DAG NODES:")
        for idx, n in enumerate(nodes, 1):
            status = "[OPTIONAL] " if _is_opt(n) else "[MANDATORY]"
            print(f"  {idx:2d}. {status} id='{n['id']:<18}' ({n.get('label', 'N/A')})")
        print()

    def _print_paths_list() -> None:
        print(f"\nSOLUTION PATHS ({len(all_solution_paths)} found):")
        for idx, p in enumerate(all_solution_paths, 1):
            print(f"  Path {idx}: {' ➔ '.join(p)}")
        print()

    def _evaluate_and_print_transition(src: str, dst: str) -> None:
        print(f"\nEvaluating Transition: '{src}'  ➔  '{dst}'")
        print("-" * 64)

        if src not in node_map:
            print(f"  ✖ Error: Source node '{src}' not found in DAG.")
            print("    (Type 'nodes' to view all available node IDs)")
            return
        if dst not in node_map:
            print(f"  ✖ Error: Destination node '{dst}' not found in DAG.")
            print("    (Type 'nodes' to view all available node IDs)")
            return

        src_node = node_map[src]
        dst_node = node_map[dst]

        if src == dst:
            print(f"  ✖ Status:       SAME NODE / SELF-LOOP")
            print(f"    Node:         '{src}' ({src_node.get('label', '')})")
            print(f"    Verdict:      Input matches current node; pointer remains at '{src}'.")
            return

        all_paths = find_directed_paths(src, dst, dag)
        if not all_paths:
            print(f"  ✖ Status:       UNREACHABLE / BACKWARD STEP")
            print(f"    Verdict:      No forward directed path exists from '{src}' to '{dst}'.")
            print(f"    Reason:       Student attempted to step backward or jumped across separate solution paths.")
            return

        chosen_path = select_best_path(src, dst, dag, active_solution_paths=all_solution_paths)
        assert chosen_path is not None
        hops = len(chosen_path) - 1

        skipped_mandatory = get_skipped_important_nodes(chosen_path, dag)
        skipped_optional = [
            node_map[nid] for nid in chosen_path[1:-1]
            if nid in node_map and _is_opt(node_map[nid])
        ]

        if hops == 1:
            status_line = "✔ DIRECT STEP (Consecutive node along DAG edge)"
        elif not skipped_mandatory:
            status_line = f"✔ LEGAL FORWARD JUMP ({len(skipped_optional)} optional node(s) skipped; 0 mandatory skipped)"
        else:
            status_line = f"⚡ STEP JUMP DETECTED ({len(skipped_mandatory)} mandatory node(s) skipped!)"

        print(f"  Status:         {status_line}")
        print(f"  Chosen Path:    {' ➔ '.join(chosen_path)} ({hops} hop{'s' if hops != 1 else ''})")

        if len(all_paths) > 1:
            print(f"\n  All Directed Paths ({len(all_paths)} found):")
            for idx, p in enumerate(all_paths, 1):
                star = " [CHOSEN]" if p == chosen_path else ""
                print(f"    Path {idx}: {' ➔ '.join(p)}{star}")

        if skipped_mandatory:
            print(f"\n  🔴 SKIPPED MANDATORY NODES (triggers step jump):")
            for idx, n in enumerate(skipped_mandatory, 1):
                print(f"     {idx}. id='{n['id']}' ({n.get('label', '')}) [optional=False]")

        if skipped_optional:
            print(f"\n  🟢 SKIPPED OPTIONAL NODES (safe to skip):")
            for idx, n in enumerate(skipped_optional, 1):
                print(f"     {idx}. id='{n['id']}' ({n.get('label', '')}) [optional=True]")

        if not skipped_mandatory and not skipped_optional:
            print(f"  Intermediate:   None (consecutive transition)")

    if args.from_node and args.to_node:
        print("\n" + "=" * 68)
        print("                 PATH FINDER TRANSITION EVALUATION")
        print("=" * 68)
        print(f"Graph File:  {graph_path.name} ({len(nodes)} nodes, {len(all_solution_paths)} solution paths)")
        _print_mandatory_nodes()
        _evaluate_and_print_transition(args.from_node, args.to_node)
        print("=" * 68 + "\n")
    else:
        print("\n" + "=" * 68)
        print("       PATH FINDER CONSOLE — Test DAG Transitions & Step Jumps")
        print("                 (Type 'nodes', 'paths', 'help', or 'quit')")
        print("=" * 68)
        print(f"Graph File: {graph_path.name} ({len(nodes)} nodes, {len(all_solution_paths)} paths)")
        _print_mandatory_nodes()
        print("-" * 68)
        print("Format:     Enter '<from_node> <to_node>' (e.g. 'given_extraction m1_s4')")
        print("-" * 68)

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
            if low in ("nodes", "node", "list", "mandatory", "mand"):
                _print_mandatory_nodes()
                continue
            if low in ("all", "all nodes"):
                _print_all_nodes()
                continue
            if low in ("paths", "path"):
                _print_paths_list()
                continue
            if low in ("help", "h", "?"):
                print("Commands:")
                print("  <from> <to>       Evaluate transition (e.g. 'start given_extraction')")
                print("  <from> -> <to>    Arrow syntax is also supported")
                print("  nodes             Print mandatory node IDs (optional=false)")
                print("  all               Print all nodes (both optional and mandatory)")
                print("  paths             List all complete solution paths in DAG")
                print("  quit              Exit the console")
                continue

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
