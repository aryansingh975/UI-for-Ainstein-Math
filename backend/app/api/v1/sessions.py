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
    MethodLockRequest,
    MethodLockResponse,
)
from app.engine.state_machine import Session, new_session, apply_result, hint_for, begin_method, method_of
from app.engine.tutor_engine import process_step
from app.engine.guided import is_guided, guided_step, first_question
from app.engine.claims import Claim, explain_claim
from app.services import session_logger

router = APIRouter(prefix="/sessions")

# Active in-memory session store: session_id -> (Session, SolutionGraph)
_SESSIONS: Dict[str, Tuple[Session, SolutionGraph]] = {}


def _new_session(graph: SolutionGraph) -> Session:
    """A guided graph starts at its first question; a free-form graph as before."""
    session = new_session(graph)
    if is_guided(graph):
        session.current_node_id = first_question(graph)
    return session


@router.post("/start", response_model=SessionStartResponse)
def start_session(req: SessionStartRequest):
    """Start a new Socratic tutoring session for a given problem."""
    graph = get_graph(req.problem_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Problem '{req.problem_id}' not found.")

    session = _new_session(graph)
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
        use_jev=getattr(meta, "use_jev", None) is True,
        guided=is_guided(graph),
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

    guided, guided_jev, plan = is_guided(graph), None, None
    if guided:
        result, guided_hint, guided_jev, plan = guided_step(req.student_input, session, graph)
    else:
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
        if plan and plan.get("concept_hint") and not plan.get("accepted"):   # K1/K2/K3 in the question box
            k = plan["concept_hint"]
            next_prompt = f"Hint {k['id']}: {k['question']}\nThen try again. {cur.prompt}"
        if plan and plan.get("next_question") and not plan.get("accepted"):   # the ladder's question in the box
            next_prompt = plan["next_question"]
            if plan.get("category") == "explain":            # explain a given step before solving
                active_label = "Explain the Plan"
        if getattr(session, "prompt_override", None):        # parts: "Still to do: (ii) 156, …"
            next_prompt = session.prompt_override
        if getattr(session, "free_solving", False):          # after the plan: the student solves alone
            active_label = "Solve on Your Own"
            next_prompt = ("Keep going, one step per line. I'll only stop you if something is wrong."
                           if getattr(session, "plan_skipped", False)    # started with a calculation: no "now solve"
                           else cur.solve_prompt or "Now solve it on your own, one step per line.")

    claim_data = None
    if isinstance(result.claim, Claim):
        claim_data = result.claim.to_dict()
    elif isinstance(result.claim, dict):
        claim_data = result.claim

    # Hint & Explanation
    if guided:
        hint = guided_hint
    else:
        hint = hint_for(session, graph, result.node_id or session.current_node_id)
        if not hint and next_is_conclusion and concl_node and concl_node.hints:
            hint = concl_node.hints[0]
    explanation = explain_claim(result.claim)

    method_node = (node_map.get(session.method_id) or next(          # "m1" names the method node "m1_count"
        (n for n in graph.nodes if n.type == "method" and method_of(n.id) == session.method_id), None)
    ) if session.method_id else None
    method_label = method_node.label if method_node else None

    # Feedback messages
    feedback_msg = None
    if plan:                                                  # a plan in words: the plan's own reply
        feedback_msg = plan["message"]
    elif result.verdict == "ACCEPT":
        feedback_msg = "That's correct."
    elif result.verdict == "CONCLUSION_RIGHT":
        feedback_msg = concl_node.description if concl_node else "Your solution is complete."
    elif result.verdict == "CONCLUSION_WRONG":
        feedback_msg = "Your conclusion does not match this problem. Recheck your steps."
    elif result.verdict == "WRONG_CLAIM":
        feedback_msg = f"🔴 {explanation} Fix this step and try it again." if explanation else "This step contains a mathematical mistake. Fix this calculation and try again."
    elif result.verdict == "IRRELEVANT_TRUE":
        feedback_msg = f'"{result.parsed.raw}" is true, but it does not yet help answer this question. Connect your step to the quantities in the problem.'
    elif result.verdict == "UNIT_ISSUE":
        feedback_msg = result.claim.get("message") if isinstance(result.claim, dict) else "Check the unit."
    elif result.verdict == "WRONG_ANSWER":
        feedback_msg = "That is not the answer to this question yet."
    elif result.verdict in ("PART", "WORKING"):                # a part picked, or a correct working step
        feedback_msg = (result.claim or {}).get("message", "") if isinstance(result.claim, dict) else ""
    elif result.verdict == "DONT_KNOW":                       # a request for help: the term, then the hint
        defs = (result.claim or {}).get("definitions") if isinstance(result.claim, dict) else None
        feedback_msg = "That's fine. " + (" ".join(defs) if defs else "Let's take it one hint at a time.")
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
        "is_correct": result.verdict in ("ACCEPT", "CONCLUSION_RIGHT", "WORKING"),
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
        jev=guided_jev,
        choice=plan,
    )


@router.post("/{session_id}/method", response_model=MethodLockResponse)
def lock_method(session_id: str, req: MethodLockRequest):
    """Lock in the method Jev identified, so replayed steps are matched against that method only."""
    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    session, graph = _SESSIONS[session_id]
    if not begin_method(session, req.method_id, graph):
        raise HTTPException(status_code=409, detail=f"Method '{req.method_id}' cannot be started in this session.")

    # Method ids like "method1" don't carry the m1_ prefix the engine groups steps by,
    # so take it from the first step id (e.g. "m1_step1" -> "m1").
    session.method_id = method_of(session.current_node_id) or session.method_id

    node_map = {n.id: n for n in graph.nodes}
    active_node = node_map.get(session.current_node_id)
    return MethodLockResponse(
        method_id=session.method_id,
        method_label=node_map[req.method_id].label,
        active_node_id=session.current_node_id,
        active_label=active_node.label if active_node else None,
        prompt=active_node.prompt if active_node else None,
    )


@router.post("/{session_id}/reset", response_model=SessionStartResponse)
def reset_session(session_id: str):
    """Reset problem state for a session."""
    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")

    _, graph = _SESSIONS[session_id]
    new_sess = _new_session(graph)
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
        use_jev=getattr(meta, "use_jev", None) is True,
        guided=is_guided(graph),
        trail=[],
        history=[],
    )

