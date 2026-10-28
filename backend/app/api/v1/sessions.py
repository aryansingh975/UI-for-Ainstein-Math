from __future__ import annotations

import uuid
from typing import Dict, Tuple
from fastapi import APIRouter, HTTPException

from app.graph_loader import get_graph
from app.schemas.graph import SolutionGraph
from app.schemas.session import (
    SessionStartRequest,
    SessionStartResponse,
    StepRequest,
    StepResponse,
)
from app.engine.state_machine import Session, new_session, apply_result, hint_for
from app.engine.tutor_engine import process_step
from app.engine.claims import Claim, explain_claim
from app.services import session_logger

router = APIRouter(prefix="/sessions")

# Active in-memory session store: session_id -> (Session, SolutionGraph)
_SESSIONS: Dict[str, Tuple[Session, SolutionGraph]] = {}


@router.post("/start", response_model=SessionStartResponse)
def start_session(req: SessionStartRequest):
    """Start a new Socratic tutoring session for a given problem."""
    graph = get_graph(req.problem_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Problem '{req.problem_id}' not found.")

    session = new_session(graph)
    session_id = f"sess_{uuid.uuid4().hex[:10]}"
    _SESSIONS[session_id] = (session, graph)

    node_map = {n.id: n for n in graph.nodes}
    active_id = session.current_node_id or graph.start_node
    active_node = node_map.get(active_id)

    meta = graph.graph_meta
    ctx = meta.problem_context or {}
    grade_val = ctx.get("grade")
    if grade_val is not None:
        try:
            grade_val = int(str(grade_val).replace("Grade", "").strip())
        except Exception:
            grade_val = 8

    # Initialize structured session log file
    session_logger.init_session_log(
        session_id=session_id,
        problem_meta={
            "problem_id": meta.problem_uuid,
            "problem_title": meta.navigation_label or meta.problem_uuid,
            "chapter": str(ctx.get("chapter", "")),
            "topic": str(ctx.get("topic", "")),
            "grade": grade_val,
        },
    )

    return SessionStartResponse(
        session_id=session_id,
        problem_id=meta.problem_uuid,
        problem_title=meta.navigation_label or meta.problem_uuid,
        problem_text=meta.problem_text,
        active_node_id=active_id,
        active_label=active_node.label if active_node else "Problem Statement",
        prompt=active_node.prompt if active_node else meta.problem_text,
        hints=active_node.hints if active_node else [],
        completed=session.completed,
        chapter=str(ctx.get("chapter", "")),
        topic=str(ctx.get("topic", "")),
        grade=grade_val,
        is_beginning=(len(session.trail) == 0 and not session.method_id and not session.current_node_id),
        trail=[],
        history=[],
    )


@router.post("/{session_id}/step", response_model=StepResponse)
def check_step(session_id: str, req: StepRequest):
    """Evaluate a student's step against the Socratic solution graph."""
    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    session, graph = _SESSIONS[session_id]
    if session.completed:
        raise HTTPException(status_code=400, detail="Problem is already completed. Reset to start again.")

    result = process_step(req.student_input, session, graph)
    apply_result(session, result, graph)

    node_map = {n.id: n for n in graph.nodes}
    concl_node = node_map.get(graph.conclusion_node)

    # Next is conclusion?
    next_is_conclusion = (session.current_node_id == graph.conclusion_node)

    # Determine next prompt and active label
    next_prompt = None
    active_label = None
    active_id = session.current_node_id

    if session.completed:
        active_id = graph.conclusion_node
        active_label = concl_node.label if concl_node else "Final Answer"
        next_prompt = concl_node.prompt if concl_node else "Problem solved!"
    elif active_id and active_id in node_map:
        cur = node_map[active_id]
        active_label = cur.label
        next_prompt = cur.prompt

    claim_data = None
    if isinstance(result.claim, Claim):
        claim_data = result.claim.to_dict()
    elif isinstance(result.claim, dict):
        claim_data = result.claim

    # Hint & Explanation
    hint = hint_for(session, graph, result.node_id or session.current_node_id)
    if not hint and next_is_conclusion and concl_node and concl_node.hints:
        hint = concl_node.hints[0]
    explanation = explain_claim(result.claim)

    method_node = node_map.get(session.method_id) if session.method_id else None
    method_label = method_node.label if method_node else None

    # Feedback messages
    feedback_msg = None
    if result.verdict == "ACCEPT":
        feedback_msg = "That's correct."
    elif result.verdict == "CONCLUSION_RIGHT":
        feedback_msg = concl_node.description if concl_node else "Your solution is complete."
    elif result.verdict == "CONCLUSION_WRONG":
        feedback_msg = "Your conclusion does not match this problem. Recheck your steps."
    elif result.verdict == "WRONG_CLAIM":
        feedback_msg = f"🔴 {explanation} Fix this step and try it again." if explanation else "This step contains a mathematical mistake. Fix this calculation and try again."
    elif result.verdict == "IRRELEVANT_TRUE":
        feedback_msg = f'"{result.parsed.raw}" is true, but it does not yet help answer this question. Connect your step to the quantities in the problem.'
    elif result.verdict == "GARBAGE":
        feedback_msg = "That does not look related to this problem. Try a calculation or explain a method for the question above."
    else:  # UNPARSED
        feedback_msg = "Try writing a calculation or mathematical relationship that helps answer this question."

    trail_data = [{"nodeId": t.get("nodeId", ""), "input": t.get("input", "")} for t in session.trail]

    # Record every turn in conversation history (both correct and mistake attempts)
    turn_record = {
        "turn": len(session.history) + 1,
        "input": req.student_input,
        "verdict": result.verdict,
        "feedback": feedback_msg,
        "hint": hint,
        "explanation": explanation,
        "is_correct": result.verdict in ("ACCEPT", "CONCLUSION_RIGHT"),
        "node_id": result.node_id or active_id,
        "label": active_label,
    }
    session.history.append(turn_record)

    # Persist turn to session log, all_turns.jsonl, and errors.jsonl (if incorrect)
    session_logger.log_turn(
        session_id=session_id,
        turn_record=turn_record,
        completed=session.completed,
        problem_id=graph.graph_meta.problem_uuid if graph and graph.graph_meta else "",
    )

    return StepResponse(
        verdict=result.verdict,
        parsed_input=result.parsed.raw,
        active_node_id=active_id,
        active_label=active_label,
        next_prompt=next_prompt,
        feedback_message=feedback_msg,
        hint=hint,
        explanation=explanation,
        approach_only=result.approach_only,
        completed=session.completed,
        fail_streak=session.fail_streak,
        claim=claim_data,
        trail=trail_data,
        history=list(session.history),
        conclusion_prompt=concl_node.prompt if concl_node else None,
        conclusion_description=concl_node.description if concl_node else None,
        next_is_conclusion=next_is_conclusion,
        method_id=session.method_id,
        method_label=method_label,
    )


@router.post("/{session_id}/reset", response_model=SessionStartResponse)
def reset_session(session_id: str):
    """Reset problem state for a session."""
    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")

    _, graph = _SESSIONS[session_id]
    new_sess = new_session(graph)
    _SESSIONS[session_id] = (new_sess, graph)

    node_map = {n.id: n for n in graph.nodes}
    active_id = new_sess.current_node_id or graph.start_node
    active_node = node_map.get(active_id)

    meta = graph.graph_meta
    ctx = meta.problem_context or {}
    grade_val = ctx.get("grade")
    if grade_val is not None:
        try:
            grade_val = int(str(grade_val).replace("Grade", "").strip())
        except Exception:
            grade_val = 8

    # Initialize structured session log file
    session_logger.init_session_log(
        session_id=session_id,
        problem_meta={
            "problem_id": meta.problem_uuid,
            "problem_title": meta.navigation_label or meta.problem_uuid,
            "chapter": str(ctx.get("chapter", "")),
            "topic": str(ctx.get("topic", "")),
            "grade": grade_val,
        },
    )

    return SessionStartResponse(
        session_id=session_id,
        problem_id=meta.problem_uuid,
        problem_title=meta.navigation_label or meta.problem_uuid,
        problem_text=meta.problem_text,
        active_node_id=active_id,
        active_label=active_node.label if active_node else "Problem Statement",
        prompt=active_node.prompt if active_node else meta.problem_text,
        hints=active_node.hints if active_node else [],
        completed=False,
        chapter=str(ctx.get("chapter", "")),
        topic=str(ctx.get("topic", "")),
        grade=grade_val,
        is_beginning=True,
        trail=[],
        history=[],
    )

