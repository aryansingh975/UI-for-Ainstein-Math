"""Core Navigator Engine (v2) for Ainstein Socratic Math Tutor.

Coordinates DAG loading, Socratic session tracking,
v1 ranker cascade (String Match -> Weighted Jaccard & Input Coverage -> Specificity Tie-Breaker),
and DAG reachability / step-jump detection for important nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from .graph_loader import load_dag
    from .path_finder import evaluate_transition
    from .ranker import DEFAULT_THRESHOLD, resolve_with_score
    from .session import NavigatorSession
except ImportError:
    from graph_loader import load_dag
    from path_finder import evaluate_transition
    from navigator.ranker_v1 import DEFAULT_THRESHOLD, resolve_with_score
    from session import NavigatorSession

@dataclass
class NavigatorResult:
    """Detailed result of processing a student input against the DAG."""

    status: str
    """Status code: FIRST_MATCH | ADVANCED | STEP_JUMP | INVALID_PATH | NO_MATCH | ALREADY_AT_CURRENT_NODE."""

    message: str
    """User-facing message explaining the outcome."""

    matched_node: dict[str, Any] | None = None
    """The node that the user's input matched against in the ranker."""

    current_node: dict[str, Any] | None = None
    """The node where the navigator pointer is currently positioned after this step."""

    score: float = 0.0
    """Evaluation similarity score achieved by the ranker."""

    match_type: str = ""
    """Algorithm category that resolved the match (e.g. EXACT_STRING_MATCH, FUZZY_WEIGHTED_JACCARD)."""

    skipped_nodes: list[dict[str, Any]] = field(default_factory=list)
    """List of skipped intermediate nodes that have importance = 'yes' (on STEP_JUMP)."""

    trail: list[str] = field(default_factory=list)
    """Trail of all node IDs visited in this session."""

    def to_dict(self) -> dict[str, Any]:
        """Convert result object to dictionary."""
        return {
            "status": self.status,
            "message": self.message,
            "matched_node_id": self.matched_node["id"] if self.matched_node else None,
            "current_node_id": self.current_node["id"] if self.current_node else None,
            "score": self.score,
            "match_type": self.match_type,
            "skipped_nodes": [
                {
                    "id": n["id"],
                    "label": n.get("label", ""),
                    "prompt": n.get("prompt", ""),
                    "optional": n.get("optional", False),
                }
                for n in self.skipped_nodes
            ],
            "trail": self.trail,
        }


class Navigator:
    """Stateful, path-aware Socratic Navigator (v2)."""

    def __init__(
        self,
        dag_source: str | Path | dict[str, Any],
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self.dag: dict[str, Any] = load_dag(dag_source)
        self.threshold: float = threshold

        # Initialize session
        self.session: NavigatorSession = NavigatorSession(self.dag)

    def reset(self) -> None:
        """Reset session to the beginning."""
        self.session.reset()

    @property
    def current_node(self) -> dict[str, Any] | None:
        return self.session.current_node

    @property
    def trail(self) -> list[str]:
        return self.session.get_trail_ids()

    def process_input(self, raw_input: str) -> NavigatorResult:
        """Process a single student input string against the DAG.

        Workflow:
            1. Ranker scores input against all nodes in the DAG.
               (Exact Match -> Weighted Jaccard & Input Coverage -> Specificity Tie-Breaker -> threshold check).
            2. If no node matches: return NO_MATCH.
            3. If first input of session:
               - Point to matched node.
               - Narrow candidate solution paths.
               - Return FIRST_MATCH.
            4. If subsequent input:
               - If matched node == current_node: return ALREADY_AT_CURRENT_NODE.
               - Check reachability: Is there a directed path from current_node to matched_node?
               - If NO path exists: return INVALID_PATH ("INVALID input, give a valid input.").
               - If path exists:
                 - Check intermediate nodes for importance == 'yes'.
                 - If ANY intermediate node is important:
                   Raise flag STEP_JUMP ("STEP JUMP DETECTED...").
                   Pointer stays at current_node.
                 - If NO intermediate node is important:
                   Advance pointer to matched_node.
                   Update trail and narrow candidate solution paths.
                   Return ADVANCED.
        """
        clean_input = str(raw_input).strip()
        if not clean_input:
            return NavigatorResult(
                status="NO_MATCH",
                message="Input is empty. Please enter a valid statement.",
                current_node=self.session.current_node,
                trail=self.session.get_trail_ids(),
            )

        nodes = self.dag.get("nodes", [])
        matched_node, score, match_type, _ = resolve_with_score(
            clean_input,
            nodes,
            threshold=self.threshold,
        )

        # --------------------------------------------------------------
        # 1. No node matched above threshold
        # --------------------------------------------------------------
        if matched_node is None:
            self.session.record_attempt(
                raw_input=clean_input,
                status="NO_MATCH",
                score=score,
            )
            return NavigatorResult(
                status="NO_MATCH",
                message="No matching node found. Please try again.",
                score=score,
                match_type=match_type,
                current_node=self.session.current_node,
                trail=self.session.get_trail_ids(),
            )

        matched_id = matched_node["id"]

        # --------------------------------------------------------------
        # 2. First input of the session
        # --------------------------------------------------------------
        if self.session.is_first_input():
            self.session.set_first_node(matched_node, raw_input=clean_input, score=score)
            return NavigatorResult(
                status="FIRST_MATCH",
                message=f"Session started. Matched node '{matched_id}' ({matched_node.get('label', '')}).",
                matched_node=matched_node,
                current_node=matched_node,
                score=score,
                match_type=match_type,
                trail=self.session.get_trail_ids(),
            )

        current_id = self.session.current_node["id"]  # type: ignore

        # --------------------------------------------------------------
        # 3. Already at matched node
        # --------------------------------------------------------------
        if matched_id == current_id:
            self.session.record_attempt(
                raw_input=clean_input,
                status="ALREADY_AT_CURRENT_NODE",
                matched_node=matched_node,
                score=score,
            )
            return NavigatorResult(
                status="ALREADY_AT_CURRENT_NODE",
                message=f"You are already at node '{current_id}'. Provide a step to move forward.",
                matched_node=matched_node,
                current_node=self.session.current_node,
                score=score,
                match_type=match_type,
                trail=self.session.get_trail_ids(),
            )

        # --------------------------------------------------------------
        # 4. Check DAG reachability and intermediate importance
        # --------------------------------------------------------------
        path_exists, chosen_path, skipped_important = evaluate_transition(
            from_node_id=current_id,
            to_node_id=matched_id,
            dag=self.dag,
            active_solution_paths=self.session.active_solution_paths,
        )

        if not path_exists:
            # No directed path exists in DAG from current_node to matched_node
            self.session.record_attempt(
                raw_input=clean_input,
                status="INVALID_PATH",
                matched_node=matched_node,
                score=score,
            )
            return NavigatorResult(
                status="INVALID_PATH",
                message="INVALID input, give a valid input.",
                matched_node=matched_node,
                current_node=self.session.current_node,
                score=score,
                match_type=match_type,
                trail=self.session.get_trail_ids(),
            )

        # Path exists! Check if any intermediate node is important
        if skipped_important:
            # Step jump detected!
            self.session.record_attempt(
                raw_input=clean_input,
                status="STEP_JUMP",
                matched_node=matched_node,
                score=score,
                skipped_nodes=skipped_important,
            )
            skipped_summary = ", ".join(
                f"'{n['id']}' ({n.get('label', '')})" for n in skipped_important
            )
            return NavigatorResult(
                status="STEP_JUMP",
                message=(
                    "STEP JUMP DETECTED. THE FOLLOWING MANDATORY NODE HAS BEEN SKIPPED -> "
                    f"{skipped_summary}\n"
                    "Mandatory intermediate node detected."
                ),
                matched_node=matched_node,
                current_node=self.session.current_node,
                score=score,
                match_type=match_type,
                skipped_nodes=skipped_important,
                trail=self.session.get_trail_ids(),
            )

        # Valid forward transition with no skipped important nodes
        self.session.advance_to(matched_node, raw_input=clean_input, score=score)
        return NavigatorResult(
            status="ADVANCED",
            message=f"Advanced to node '{matched_id}' ({matched_node.get('label', '')}).",
            matched_node=matched_node,
            current_node=matched_node,
            score=score,
            match_type=match_type,
            trail=self.session.get_trail_ids(),
        )