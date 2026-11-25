"""Tests for the Unified Socratic Navigator + Method Waterfall + Qwen 3.5 Verifier."""
from __future__ import annotations

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.graph_loader import get_graph
from app.engine.state_machine import new_session, apply_result
from app.engine.tutor_engine import process_step
from app.engine.navigator_bridge import navigator_match_node
from app.engine.method_resolver import resolve_method_waterfall

client = TestClient(app)


def _start_age_session() -> str:
    res = client.post("/api/v1/sessions/start", json={"problem_id": "g08-hegp206-age-q7"})
    assert res.status_code == 200
    return res.json()["session_id"]


def test_age_problem_final_answer_triggers_step_jump_without_method_lock():
    """Entering '6 years' immediately after extraction must return STEP_JUMP, not block on method selection."""
    sid = _start_age_session()

    r1 = client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "Mother is 5 times daughter's age"})
    assert r1.status_code == 200
    assert r1.json()["verdict"] == "ACCEPT"

    r2 = client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "age of daughter"})
    assert r2.status_code == 200
    assert r2.json()["verdict"] == "ACCEPT"

    # Jump straight to final answer '6 years' without selecting method or writing steps
    r3 = client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "6 years"})
    assert r3.status_code == 200
    data = r3.json()
    assert data["verdict"] == "STEP_JUMP"
    assert not data["completed"]


def test_navigator_identifies_method_directly_from_step_node():
    """Entering a Method 1 step ('mother = 5x') right after extraction auto-identifies Method 1."""
    sid = _start_age_session()
    client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "Mother is 5 times daughter's age"})
    client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "age of daughter"})

    r3 = client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "mother = 5x"})
    assert r3.status_code == 200
    data = r3.json()
    assert data["verdict"] == "ACCEPT"
    assert data["method_id"] is not None
    assert "1" in data["method_id"] or "Equation" in (data.get("method_label") or "")


def test_navigator_jaccard_accepts_paraphrase_but_blocks_wrong_numbers():
    """Navigator Jaccard (>= 0.70) accepts minor wording variants, never wrong numbers/equations."""
    graph = get_graph("g08-hegp206-age-q7")
    assert graph is not None
    node_map = {n.id: n for n in graph.nodes}

    goal_node = node_map["goal_extraction"]
    assert navigator_match_node("present age of the daughter", goal_node, threshold=0.70)["accepted"] is True

    given_node = node_map["given_extraction"]
    assert navigator_match_node("Mother is 5 times her daughter's present age", given_node, threshold=0.70)["accepted"] is True
    assert navigator_match_node("Mother is 9 times her daughter's present age", given_node, threshold=0.70)["accepted"] is False

    step4_node = node_map["m1_step4"]
    assert navigator_match_node("daughter is 9", step4_node, threshold=0.70)["accepted"] is False
    assert navigator_match_node("5x - 6 = 18", node_map["m1_step3"], threshold=0.70)["accepted"] is False


def test_qwen_fallback_verifies_unlisted_goal_and_step_respecting_dag_gating():
    """Qwen 3.5 fallback verifies creative phrasing for Goal/Step nodes, while still enforcing DAG step-jumps."""
    graph = get_graph("g08-hegp206-age-q7")
    assert graph is not None
    session = new_session(graph)
    session.current_node_id = "given_extraction"

    r1 = process_step("Mother is 5 times daughter's age", session, graph)
    assert r1.verdict == "ACCEPT"
    apply_result(session, r1, graph)

    # Creative goal wording that misses exact/Jaccard threshold -> handled by Qwen 3.5 mock
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "AINSTEIN_ENABLE_LLM_VERIFIER": "1"}), patch(
        "app.engine.llm_verifier._post_openrouter",
        return_value={"is_valid": True, "confidence": 0.93, "reason": "States daughter's present age as target."},
    ):
        r2 = process_step("we need to figure out how old the little girl currently is", session, graph)
        assert r2.verdict == "ACCEPT"
        assert r2.node_id == "goal_extraction"
        apply_result(session, r2, graph)

    # If Qwen identifies a downstream step (m1_step3) before m1_step1, DAG check MUST still return STEP_JUMP
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "AINSTEIN_ENABLE_LLM_VERIFIER": "1"}), patch(
        "app.engine.llm_verifier._post_openrouter",
        return_value={
            "matched_node_id": "m1_step3",
            "is_valid": True,
            "confidence": 0.91,
            "reason": "Student solved equation to x = 6",
        },
    ):
        r3 = process_step("solving that gives x equals six", session, graph)
        assert r3.verdict == "STEP_JUMP"


def test_method_waterfall_falls_back_from_local_jev_to_global_jev():
    """Method resolver checks Navigator -> Local JEV -> Global JEV strictly for method identification."""
    graph = get_graph("g08-hegp206-age-q7")
    assert graph is not None

    # Local JEV handles explicit declaration
    local_res = resolve_method_waterfall("let daughter be x", graph)
    assert local_res is not None
    assert local_res["method_id"] == "method1"

    # Ambiguous phrasing falls back to Global JEV via OpenRouter API
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "AINSTEIN_ENABLE_GLOBAL_JEV": "1"}), patch(
        "app.engine.method_resolver._post_openrouter",
        return_value={
            "status": "selected",
            "method_id": "method2",
            "confidence": 0.88,
            "reason": "Student prefers setting mother's age as the variable.",
        },
    ):
        global_res = resolve_method_waterfall(
            "I want to assign the unknown variable to the older parent first",
            graph,
        )
        assert global_res is not None
        assert global_res["method_id"] == "method2"
        assert global_res["source"] == "global_jev"
