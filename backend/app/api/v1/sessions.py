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
from app.engine.state_machine import (
    Session,
    new_session,
    apply_result,
    hint_for,
    get_method_node,
    first_step_of,
    begin_method,
    method_of,
)
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
    if active_id in node_map and node_map[active_id].type == "method":
        active_id = first_step_of(active_id, graph)
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
        if plan and plan.get("concept_hint") and not plan.get("accepted"):
            k = plan["concept_hint"]
            next_prompt = f"Hint {k['id']}: {k['question']}\nThen try again. {cur.prompt}"
        if plan and plan.get("next_question") and not plan.get("accepted"):
            next_prompt = plan["next_question"]
            if plan.get("category") == "explain":
                active_label = "Explain the Plan"
        if getattr(session, "prompt_override", None):
            next_prompt = session.prompt_override
        if getattr(session, "free_solving", False):
            active_label = "Solve on Your Own"
            next_prompt = ("Keep going, one step per line. I'll only stop you if something is wrong."
                           if getattr(session, "plan_skipped", False)
                           else getattr(cur, "solve_prompt", None) or "Now solve it on your own, one step per line.")
    elif not session.completed and not active_id and not session.method_id:
        active_label = "Step 1"
        next_prompt = "Great! Now that we know what is given and what to find, what is your first step to solve this problem?"

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

    method_node = get_method_node(session.method_id, graph) if session.method_id else None
    method_label = method_node.label if method_node else None

    # Feedback messages
    feedback_msg = None
    if plan:                                                  # a plan in words: the plan's own reply
        feedback_msg = plan["message"]
    elif getattr(result, "feedback", None):
        feedback_msg = result.feedback
    elif result.verdict in ("ACCEPT", "MULTI_STEP_ACCEPT"):
        feedback_msg = "That's correct."
    elif result.verdict == "CONCLUSION_RIGHT":
        feedback_msg = concl_node.description if concl_node else "Your solution is complete."
    elif result.verdict == "CONCLUSION_WRONG":
        feedback_msg = "Your conclusion does not match this problem. Recheck your steps."
    elif result.verdict == "EXTRACTION_REQUIRED":
        feedback_msg = "Let's first identify the given information for this problem."
    elif result.verdict == "METHOD_LOCKED":
        feedback_msg = "Let's continue solving with your current method."
    elif result.verdict == "PARTIAL_EXTRACTION":
        feedback_msg = "Good start! What other information is given?"
    elif result.verdict == "MISCONCEPTION":
        feedback_msg = f"🔴 {explanation}" if explanation else "Review the mathematical operation needed."
    elif result.verdict == "WRONG_CLAIM":
        if isinstance(result.claim, dict) and result.claim.get("message"):
            feedback_msg = f"🔴 {result.claim['message']} Fix this step and try it again."
        elif explanation:
            feedback_msg = f"🔴 {explanation} Fix this step and try it again."
        else:
            feedback_msg = "This step contains a mathematical mistake. Fix this calculation and try again."
    elif result.verdict == "IRRELEVANT_TRUE":
        feedback_msg = f'"{result.parsed.raw}" is true, but it does not yet help answer this question. Connect your step to the quantities in the problem.'
    elif result.verdict == "UNIT_ISSUE":
        feedback_msg = result.claim.get("message") if isinstance(result.claim, dict) else "Check the unit."
    elif result.verdict == "WRONG_ANSWER":
        feedback_msg = "That is not the answer to this question yet."
    elif result.verdict in ("PART", "WORKING"):
        feedback_msg = (result.claim or {}).get("message", "") if isinstance(result.claim, dict) else ""
    elif result.verdict == "DONT_KNOW":
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
        "next_prompt": next_prompt,
        "hint": hint,
        "explanation": explanation,
        "is_correct": result.verdict in ("ACCEPT", "MULTI_STEP_ACCEPT", "CONCLUSION_RIGHT", "WORKING"),
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

    session.method_id = method_of(session.current_node_id) or session.method_id

    node_map = {n.id: n for n in graph.nodes}
    active_node = node_map.get(session.current_node_id)
    return MethodLockResponse(
        method_id=session.method_id,
        method_label=node_map[req.method_id].label if req.method_id in node_map else req.method_id,
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

