"""Interactive Session Manager for Navigator v2.

Maintains state across student inputs, tracking visited nodes, current pointer,
and filtering the active candidate solution paths as navigation progresses.
"""

from __future__ import annotations

from typing import Any

try:
    from .graph_loader import get_all_solution_paths
except ImportError:
    from graph_loader import get_all_solution_paths


class NavigatorSession:
    """Encapsulates a live interactive navigation session over a solution DAG."""

    def __init__(self, dag: dict[str, Any]) -> None:
        self.dag: dict[str, Any] = dag
        self.all_solution_paths: list[list[str]] = get_all_solution_paths(dag)
        self.active_solution_paths: list[list[str]] = list(self.all_solution_paths)
        self.current_node: dict[str, Any] | None = None
        self.visited_nodes: list[dict[str, Any]] = []
        self.history: list[dict[str, Any]] = []

    def is_first_input(self) -> bool:
        """Return True if no node has been visited yet."""
        return self.current_node is None

    def set_first_node(self, node: dict[str, Any], raw_input: str = "", score: float = 1.0) -> None:
        """Initialize session pointer to the first matched node and filter solution paths."""
        self.current_node = node
        self.visited_nodes.append(node)
        node_id = node["id"]

        # Filter active solution paths to those containing this node
        matching_paths = [p for p in self.all_solution_paths if node_id in p]
        if matching_paths:
            self.active_solution_paths = matching_paths
        else:
            self.active_solution_paths = list(self.all_solution_paths)

        self.history.append({
            "step_index": len(self.history) + 1,
            "raw_input": raw_input,
            "node_id": node_id,
            "score": score,
            "status": "INITIAL_MATCH",
            "active_paths_count": len(self.active_solution_paths),
        })

    def advance_to(self, next_node: dict[str, Any], raw_input: str = "", score: float = 1.0) -> None:
        """Advance the session pointer to next_node and narrow active solution paths."""
        prev_node_id = self.current_node["id"] if self.current_node else None
        self.current_node = next_node
        self.visited_nodes.append(next_node)
        next_id = next_node["id"]

        # Narrow active paths to those where next_id appears *after* prev_node_id
        narrowed: list[list[str]] = []
        for path in self.active_solution_paths:
            if next_id in path:
                if prev_node_id and prev_node_id in path:
                    if path.index(next_id) > path.index(prev_node_id):
                        narrowed.append(path)
                else:
                    narrowed.append(path)

        if narrowed:
            self.active_solution_paths = narrowed
        else:
            # Fallback to any solution path in graph containing next_id
            fallback = [p for p in self.all_solution_paths if next_id in p]
            if fallback:
                self.active_solution_paths = fallback

        self.history.append({
            "step_index": len(self.history) + 1,
            "raw_input": raw_input,
            "node_id": next_id,
            "score": score,
            "status": "ADVANCED",
            "active_paths_count": len(self.active_solution_paths),
        })

    def record_attempt(
        self,
        raw_input: str,
        status: str,
        matched_node: dict[str, Any] | None = None,
        score: float = 0.0,
        skipped_nodes: list[dict[str, Any]] | None = None,
    ) -> None:
        """Record an attempt that did not advance the pointer (e.g. step jump or invalid path)."""
        self.history.append({
            "step_index": len(self.history) + 1,
            "raw_input": raw_input,
            "node_id": matched_node["id"] if matched_node else None,
            "current_node_id": self.current_node["id"] if self.current_node else None,
            "score": score,
            "status": status,
            "skipped_node_ids": [n["id"] for n in (skipped_nodes or [])],
            "active_paths_count": len(self.active_solution_paths),
        })

    def get_trail_ids(self) -> list[str]:
        """Return the list of node IDs visited so far."""
        return [n["id"] for n in self.visited_nodes]

    def get_trail_display(self) -> str:
        """Return formatted breadcrumb trail of visited node IDs."""
        ids = self.get_trail_ids()
        return " -> ".join(ids) if ids else "(empty)"

    def reset(self) -> None:
        """Reset the session to initial state."""
        self.current_node = None
        self.visited_nodes = []
        self.history = []
        self.active_solution_paths = list(self.all_solution_paths)
