"""Graph Loader and Path Enumerator for Solution DAGs in Navigator v2.

Loads DAG JSON, validates and normalizes node fields (including 'importance'),
and precomputes all solution paths from start_node to conclusion_node.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def is_important_node(node: dict[str, Any]) -> bool:
    """Return True if the node is flagged with importance = 'yes'."""
    val = node.get("importance")
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("yes", "true", "1")
    return False


def load_dag(source: str | Path | dict[str, Any]) -> dict[str, Any]:
    """Load, validate, and normalize a solution DAG dictionary.

    Args:
        source: Filepath (str/Path) or an already-loaded dict.

    Returns:
        Normalized DAG dictionary.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Solution DAG file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            dag = json.load(f)
    elif isinstance(source, dict):
        dag = json.loads(json.dumps(source))  # Deep copy
    else:
        raise TypeError(f"Invalid source type for DAG: {type(source)}")

    # Ensure nodes list and start / conclusion nodes exist
    nodes = dag.get("nodes") or []
    edges = dag.get("edges") or []

    start_node = dag.get("start_node")
    conclusion_node = dag.get("conclusion_node") or dag.get("end_node")

    # If start/conclusion not explicitly set, infer from types or degree
    if not start_node:
        for n in nodes:
            if n.get("type") == "start":
                start_node = n.get("id")
                break
        if not start_node and nodes:
            start_node = nodes[0].get("id")

    if not conclusion_node:
        for n in nodes:
            if n.get("type") == "conclusion":
                conclusion_node = n.get("id")
                break
        if not conclusion_node and nodes:
            conclusion_node = nodes[-1].get("id")

    dag["start_node"] = start_node
    dag["conclusion_node"] = conclusion_node

    # Normalize node fields (accept list and importance key)
    for node in nodes:
        if "accept" not in node or node["accept"] is None:
            node["accept"] = []
        node["importance"] = "yes" if is_important_node(node) else "no"

    dag["nodes"] = nodes
    dag["edges"] = edges
    return dag


def build_adjacency(dag: dict[str, Any]) -> dict[str, list[str]]:
    """Build a directed adjacency list mapping from_node_id -> [to_node_ids]."""
    adj: dict[str, list[str]] = {}
    for node in dag.get("nodes", []):
        adj[node["id"]] = []

    for edge in dag.get("edges", []):
        u = edge.get("from") or edge.get("from_node")
        v = edge.get("to") or edge.get("to_node")
        if u and v:
            adj.setdefault(u, []).append(v)

    return adj


def get_all_solution_paths(dag: dict[str, Any]) -> list[list[str]]:
    """Enumerate all directed paths from start_node to conclusion_node.

    Returns:
        List of paths, where each path is a list of node IDs [start, ..., conclusion].
    """
    start = dag.get("start_node")
    end = dag.get("conclusion_node")
    if not start or not end:
        return []

    adj = build_adjacency(dag)
    paths: list[list[str]] = []

    def dfs(curr: str, current_path: list[str]) -> None:
        if curr == end:
            paths.append(list(current_path))
            return

        for neighbor in adj.get(curr, []):
            if neighbor not in current_path:  # Guard against unexpected cycles
                current_path.append(neighbor)
                dfs(neighbor, current_path)
                current_path.pop()

    dfs(start, [start])
    return paths


def get_dag_corpus(dag: dict[str, Any]) -> list[str]:
    """Collect all textual content from a DAG for corpus analysis."""
    corpus: list[str] = []

    meta = dag.get("graph_meta", {})
    if meta.get("problem_text"):
        corpus.append(str(meta["problem_text"]))
    if meta.get("description"):
        corpus.append(str(meta["description"]))

    for node in dag.get("nodes", []):
        for acc in node.get("accept", []):
            if acc:
                corpus.append(str(acc))
        if node.get("label"):
            corpus.append(str(node["label"]))
        if node.get("description"):
            corpus.append(str(node["description"]))
        if node.get("prompt"):
            corpus.append(str(node["prompt"]))

    return corpus


def main(argv: list[str] | None = None) -> None:
    """CLI runner to inspect and test graph_loader independently."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Load, validate, and inspect a Solution DAG.")
    parser.add_argument(
        "graph_path",
        nargs="?",
        default=None,
        help="Path to graph.json file",
    )
    args = parser.parse_args(argv)

    # Locate graph file
    if args.graph_path:
        graph_path = Path(args.graph_path)
    else:
        raise FileNotFoundError("No graph file provided. Please specify a path to a graph.json file.")


    print(f"Loading DAG from: {graph_path}")
    dag = load_dag(graph_path)

    print("\n" + "=" * 60)
    print("GRAPH METADATA:")
    meta = dag.get("graph_meta", {})
    if meta.get("problem_text"):
        print(f"  Problem Text:    {meta.get('problem_text')}")
    print(f"  Total Nodes:     {len(dag.get('nodes', []))}")
    print(f"  Total Edges:     {len(dag.get('edges', []))}")

    mandatory_nodes = [
        node for node in dag.get("nodes", [])
        if node.get("optional") is False or str(node.get("optional")).lower() == "false"
    ]
    print(f"\n1. Mandatory Nodes ({len(mandatory_nodes)} nodes with optional=false):")
    for idx, node in enumerate(mandatory_nodes, start=1):
        accept_count = len(node.get("accept", []))
        sample_accept = repr(node["accept"][:2]) if accept_count else "[]"
        print(f"  {idx:2d}. [{node.get('type', 'step')}] id='{node['id']}' (optional=False)")
        print(f"      Label:  {node.get('label', 'N/A')}")
        print(f"      Accept: {accept_count} phrase(s) -> {sample_accept}")

    paths = get_all_solution_paths(dag)
    print(f"\nSOLUTION PATHS ({len(paths)} path(s) found):")
    for idx, p in enumerate(paths, start=1):
        print(f"  Path {idx}: {' -> '.join(p)}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

