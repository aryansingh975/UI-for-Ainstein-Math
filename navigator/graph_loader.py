"""Graph Loader and Path Enumerator for Solution DAGs in Navigator.

This file is designed to ingest, validate, and normalize 
Solution Directed Acyclic Graphs (DAGs) for the Tutor Module.

Key Responsibilities:
1. Ingestion: Load from JSON file path or deep-copy an existing in-memory dictionary.
2. Structural Validation: Ensure unique node IDs, valid start/conclusion nodes, no dangling edges.
3. Node Field Normalization: Guarantee 'accept' arrays and boolean 'optional' flags.
4. Precomputations: Precompute all solution paths (DFS) and build an O(1) node lookup map.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


# ============================================================================
# 1. Node Property Helpers
# ============================================================================

def is_optional_node(node: dict[str, Any]) -> bool:
    """Check whether a node can be skipped during problem solving.

    Returns:
        True:  The node is optional (optional == True) and can be safely skipped.
        False: The node is mandatory (optional == False) and cannot be skipped.
    """
    val = node.get("optional")
    if isinstance(val, bool):
        return val
    # By default, nodes are considered mandatory unless explicitly marked optional
    return False

def get_node_by_id(dag: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    """Retrieve a node dictionary by its ID in O(1) time using precomputed node_map.

    Falls back to linear scan if node_map is not present.
    """
    node_map = dag.get("node_map")
    if isinstance(node_map, dict):
        return node_map.get(node_id)

    # Fallback to linear search across nodes list
    for node in dag.get("nodes", []):
        if node.get("id") == node_id:
            return node
    return None

# ============================================================================
# 2. Graph Topology & Path Enumeration
# ============================================================================

def build_adjacency(dag: dict[str, Any]) -> dict[str, list[str]]:
    """Build a directed adjacency list mapping: from_node_id -> [to_node_ids].

    Initializes an entry for every known node in the DAG to ensure isolated
    nodes are accounted for.
    """
    # Initialize all known node IDs with an empty neighbor list
    adj: dict[str, list[str]] = {node["id"]: [] for node in dag.get("nodes", []) if "id" in node}

    # Populate directed edges
    for edge in dag.get("edges", []):
        u = edge.get("from") or edge.get("from_node")
        v = edge.get("to") or edge.get("to_node")
        if u and v and u in adj:
            adj[u].append(v)

    return adj


def get_all_solution_paths(dag: dict[str, Any]) -> list[list[str]]:
    """Enumerate all valid directed paths from start_node to conclusion_node.

    Uses Depth-First Search (DFS) with backtracking.
    Guards against inadvertent cycles by checking if a neighbor is in the current branch.

    Returns:
        List of paths, where each path is an ordered list of node IDs:
        e.g., [["start", "step1", "conclusion"], ["start", "step2", "conclusion"]]
    """
    start = dag.get("start_node")
    end = dag.get("conclusion_node")
    if not start or not end:
        return []

    adj = build_adjacency(dag)
    paths: list[list[str]] = []

    def dfs(curr: str, current_path: list[str]) -> None:
        # Reached the target conclusion node
        if curr == end:
            paths.append(list(current_path))
            return

        # Explore outgoing directed edges
        for neighbor in adj.get(curr, []):
            if neighbor not in current_path:  # Prevent infinite loops in cyclic graphs
                current_path.append(neighbor)
                dfs(neighbor, current_path)
                current_path.pop()  # Backtrack

    dfs(start, [start])
    return paths


# ============================================================================
# 3. Core Ingestion & Validation Pipeline
# ============================================================================

def load_dag(source: str | Path | dict[str, Any]) -> dict[str, Any]:
    """Load, validate, normalize, and pre-index a Solution DAG.

    Args:
        source: File path (str / Path) or an in-memory dictionary.

    Returns:
        Normalized DAG dictionary enriched with:
        - 'start_node': ID of the initial problem node.
        - 'conclusion_node': ID of the final goal node.
        - 'node_map': Dict[str, dict] mapping node_id -> node object for O(1) lookup.
        - 'all_solution_paths': List[List[str]] precomputed paths from start to conclusion.

    Raises:
        FileNotFoundError: If a file path is provided but does not exist.
        TypeError: If source is neither a path nor a dictionary.
        ValueError: If DAG fails structural integrity checks (duplicate IDs,
                    missing start/conclusion, dangling edges, or no paths).
    """
    # ------------------------------------------------------------------------
    # Step 1: Ingestion (File reading or isolated in-memory deep copy)
    # ------------------------------------------------------------------------
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Solution DAG file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            dag = json.load(f)
    elif isinstance(source, dict):
        # Deep copy to ensure each session has an isolated object and
        # will not mutate shared in-memory caches used by other concurrent sessions
        dag = copy.deepcopy(source)
    else:
        raise TypeError(f"Invalid source type for DAG: {type(source).__name__}. Expected str, Path, or dict.")

    # ------------------------------------------------------------------------
    # Step 2: Validate Nodes Array & Unique Node IDs
    # ------------------------------------------------------------------------
    nodes = dag.get("nodes")
    if not isinstance(nodes, list) or len(nodes) == 0:
        raise ValueError("Solution DAG must contain a non-empty 'nodes' list.")

    edges = dag.get("edges")
    if not isinstance(edges, list):
        edges = []

    # Verify all nodes have an 'id' and that all IDs are strictly unique
    node_ids: list[str] = []
    seen_ids: set[str] = set()
    for n in nodes:
        nid = n.get("id")
        if not nid:
            raise ValueError(f"Every node in DAG must have a non-empty 'id': {n}")
        if nid in seen_ids:
            raise ValueError(f"DAG contains duplicate node ID: '{nid}'. Node IDs must be unique.")
        seen_ids.add(nid)
        node_ids.append(nid)

    # ------------------------------------------------------------------------
    # Step 3: Resolve Start & Conclusion Nodes (with fail-fast validation)
    # ------------------------------------------------------------------------
    start_node = dag.get("start_node")
    conclusion_node = dag.get("conclusion_node")

    # If start_node not explicitly defined at top-level, infer by type or ID
    if not start_node:
        for n in nodes:
            if n.get("type") == "start" or n.get("id") == "start":
                start_node = n.get("id")
                break
        if not start_node:
            # Fallback to the first node in the array
            start_node = node_ids[0]

    # If conclusion_node not explicitly defined at top-level, infer by type or ID
    if not conclusion_node:
        for n in nodes:
            if n.get("type") == "conclusion" or n.get("id") == "conclusion":
                conclusion_node = n.get("id")
                break
        if not conclusion_node:
            # Fallback to the last node in the array
            conclusion_node = node_ids[-1]

    # Verify start and conclusion nodes actually exist in the node set
    if start_node not in seen_ids:
        raise ValueError(f"Resolved start_node '{start_node}' does not exist in DAG nodes.")
    if conclusion_node not in seen_ids:
        raise ValueError(f"Resolved conclusion_node '{conclusion_node}' does not exist in DAG nodes.")

    dag["start_node"] = start_node
    dag["conclusion_node"] = conclusion_node

    # ------------------------------------------------------------------------
    # Step 4: Validate Edges (Check for dangling endpoints)
    # ------------------------------------------------------------------------
    for edge in edges:
        u = edge.get("from") or edge.get("from_node")
        v = edge.get("to") or edge.get("to_node")
        if not u or not v:
            raise ValueError(f"Edge missing 'from' or 'to' endpoint: {edge}")
        if u not in seen_ids:
            raise ValueError(f"Dangling edge: source node '{u}' does not exist in DAG nodes.")
        if v not in seen_ids:
            raise ValueError(f"Dangling edge: target node '{v}' does not exist in DAG nodes.")

    # ------------------------------------------------------------------------
    # Step 5: Normalize Node Fields (accept array & optional boolean flag)
    # ------------------------------------------------------------------------
    for node in nodes:
        # Ensure accept is always a list of strings
        if "accept" not in node or node["accept"] is None:
            node["accept"] = []
        # Ensure optional is an explicit boolean (False = mandatory, True = optional)
        node["optional"] = is_optional_node(node)

    dag["nodes"] = nodes
    dag["edges"] = edges

    # ------------------------------------------------------------------------
    # Step 6: Precompute O(1) Node Lookup Map & Solution Paths
    # ------------------------------------------------------------------------
    # Build dictionary for fast O(1) node lookup by ID
    dag["node_map"] = {node["id"]: node for node in nodes}

    # Precalculate all valid solution paths from start_node to conclusion_node
    paths = get_all_solution_paths(dag)
    if not paths:
        raise ValueError(
            f"Invalid Solution DAG: No directed path found from start_node '{start_node}' "
            f"to conclusion_node '{conclusion_node}'."
        )
    dag["all_solution_paths"] = paths

    return dag


# ============================================================================
# 4. Developer CLI & Standalone Inspection Tool
# ============================================================================

def main(argv: list[str] | None = None) -> None:
    """CLI runner to inspect, validate, and test graph_loader independently."""
    import argparse

    parser = argparse.ArgumentParser(description="Load, validate, and inspect a Solution DAG.")
    parser.add_argument(
        "graph_path",
        nargs="?",
        default=None,
        help="Path to graph.json file",
    )
    args = parser.parse_args(argv)

    if not args.graph_path:
        print("Usage: python graph_loader.py <path/to/graph.json>")
        return

    graph_path = Path(args.graph_path)
    print(f"Loading and validating DAG from: {graph_path}")

    try:
        dag = load_dag(graph_path)
    except Exception as exc:
        print(f"\n[ERROR] DAG Validation Failed: {exc}")
        return

    print("\n" + "=" * 60)
    print("GRAPH VALIDATION: SUCCESSFUL")
    print("=" * 60)

    meta = dag.get("graph_meta", {})
    if meta.get("problem_text"):
        print(f"  Problem Text:     {meta.get('problem_text')[:100]}...")
    print(f"  Start Node:       {dag['start_node']}")
    print(f"  Conclusion Node:  {dag['conclusion_node']}")
    print(f"  Total Nodes:      {len(dag.get('nodes', []))}")
    print(f"  Total Edges:      {len(dag.get('edges', []))}")

    mandatory_nodes = [
        node for node in dag.get("nodes", [])
        if not is_optional_node(node)
    ]
    print("~" * 60)
    print(f"MANDATORY NODES ({len(mandatory_nodes)} nodes with optional=false):")

    for idx, node in enumerate(mandatory_nodes, start=1):
        print(f"  {idx:2d}. [{node.get('type', 'step')}] id='{node['id']}' — {node.get('label', 'N/A')}")

    paths = dag.get("all_solution_paths", [])
    print("~" * 60)
    print(f"ALL POSSIBLE SOLUTION PATHS ({len(paths)} path(s) found):")
    for idx, p in enumerate(paths, start=1):
        print(f"Path {idx}:\n{' -> '.join(p)}")


if __name__ == "__main__":
    main()
