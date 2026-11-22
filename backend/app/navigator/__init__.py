"""Navigator Module (V1) — Stateless DAG node matching via semantic similarity.

Public API:
    navigate_dag(dag, user_input, threshold) -> dict | str
    navigate_dag_with_score(dag, user_input, threshold) -> tuple[dict | str, float]
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.navigator.navigator import navigate_dag, navigate_dag_with_score

__all__ = ["navigate_dag", "navigate_dag_with_score"]


def __getattr__(name: str):
    if name in ("navigate_dag", "navigate_dag_with_score"):
        from app.navigator.navigator import navigate_dag, navigate_dag_with_score
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
