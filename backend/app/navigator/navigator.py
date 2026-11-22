"""Navigator — Public Entry Point.

Provides the single pure function that external code calls to match a raw
user string against a solution DAG and return the best-matching node.
"""

from __future__ import annotations

from typing import Union

from app.navigator.ranker import resolve, resolve_with_score, DEFAULT_THRESHOLD


def navigate_dag_with_score(
    dag: dict,
    user_input: str,
    threshold: float = DEFAULT_THRESHOLD,
) -> tuple[Union[dict, str], float]:
    """Match a user input string to the best node and return (node, score).

    Args:
        dag:        A Python dict representing the parsed DAG JSON.
        user_input: The raw, unprocessed user input string.
        threshold:  Minimum similarity score cutoff (default 0.5).

    Returns:
        Tuple of (matched_node_dict | "No node found", score).
    """
    nodes = dag.get("nodes") or []
    for node in nodes:
        if "accept" not in node:
            node["accept"] = []
    return resolve_with_score(user_input, nodes, threshold)


def navigate_dag(
    dag: dict,
    user_input: str,
    threshold: float = DEFAULT_THRESHOLD,
) -> Union[dict, str]:
    """Match a user input string to the best node in a solution DAG.

    This is a **pure function**: same inputs -> same output, every time.
    """
    node, _ = navigate_dag_with_score(dag, user_input, threshold)
    return node
