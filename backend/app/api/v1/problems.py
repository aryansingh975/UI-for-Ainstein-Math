from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException

from app.graph_loader import get_graph, list_problems
from app.schemas.session import ProblemSummary

router = APIRouter(prefix="/problems")


@router.get("", response_model=List[ProblemSummary])
def get_all_problems():
    """Retrieve catalog list of all 32 available NCERT problems."""
    raw_problems = list_problems()
    return [
        ProblemSummary(
            problem_uuid=p["problem_uuid"],
            navigation_label=p["navigation_label"],
            problem_text=p["problem_text"],
            chapter=p.get("chapter", ""),
            topic=p.get("topic", ""),
            grade=p.get("grade", ""),
        )
        for p in raw_problems
    ]


@router.get("/{problem_id}")
def get_problem_details(problem_id: str):
    """Retrieve public sanitized problem statement and context without exposing solution answers."""
    graph = get_graph(problem_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")

    meta = graph.graph_meta
    start_node = next((n for n in graph.nodes if n.id == graph.start_node), None)
    given_ext = next((n for n in graph.nodes if n.id == "given_extraction"), None)

    return {
        "problem_id": meta.problem_uuid,
        "title": meta.navigation_label or meta.problem_uuid,
        "problem_text": meta.problem_text,
        "description": meta.description,
        "context": meta.problem_context,
        "initial_prompt": (given_ext.prompt if (given_ext and given_ext.optional is False) else (start_node.prompt if start_node else meta.problem_text)),
        "extraction_optional": (given_ext.optional if given_ext else True),
    }

