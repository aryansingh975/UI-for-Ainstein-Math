import pytest
from app.graph_loader import load_all_graphs
from app.engine.state_machine import new_session, apply_result
from app.engine.tutor_engine import process_step
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def graphs():
    return load_all_graphs()


def test_goal_extraction_does_not_trigger_premature_conclusion(graphs):
    """Verify that saying 'whether the ratios are proportional' during extraction does NOT trigger conclusion."""
    g1 = graphs["g08-hegp107-ex001"]
    s = new_session(g1)
    s.current_node_id = "given_extraction"

    # Turn 1: Givens
    r1 = process_step("3:4 and 72:96", s, g1)
    assert r1.verdict == "ACCEPT"
    assert r1.node_id == "given_extraction"
    apply_result(s, r1, g1)
    assert s.current_node_id == "goal_extraction"

    # Turn 2: Goal statement with 'proportional' keyword
    r2 = process_step("we need to find whether the ratios are proportional", s, g1)
    assert r2.verdict == "ACCEPT"
    assert r2.node_id == "goal_extraction"
    apply_result(s, r2, g1)

    # Must NOT have prematurely completed
    assert s.completed is False


def test_dead_prompt_gap_resolved_via_api():
    """Verify that after goal extraction, the API returns the proactive calculation prompt."""
    res_start = client.post("/api/v1/sessions/start", json={"problem_id": "g08-hegp107-ex001"})
    assert res_start.status_code == 200
    session_id = res_start.json()["session_id"]

    # Turn 1: Givens
    client.post(f"/api/v1/sessions/{session_id}/step", json={"student_input": "3:4 and 72:96"})

    # Turn 2: Goal
    res_goal = client.post(
        f"/api/v1/sessions/{session_id}/step",
        json={"student_input": "whether the ratios are proportional"},
    )
    assert res_goal.status_code == 200
    data = res_goal.json()
    assert data["verdict"] == "ACCEPT"
    assert data["completed"] is False
    assert data["next_prompt"] is not None
    assert "what is your first step to solve this problem" in data["next_prompt"].lower()


def test_real_math_prioritized_over_keyword_interception(graphs):
    """Verify that typing a calculation like 'divide by 24' directly executes the step."""
    g1 = graphs["g08-hegp107-ex001"]
    s = new_session(g1)
    s.current_node_id = "given_extraction"

    # Givens & Goal
    apply_result(s, process_step("3:4 and 72:96", s, g1), g1)
    apply_result(s, process_step("whether the ratios are proportional", s, g1), g1)

    # Student enters calculation step directly:
    r = process_step("divide by 24", s, g1)
    assert r.verdict == "ACCEPT"
    assert r.approach_only is False
    assert r.node_id == "m1_s1"
    assert r.method_id == "m1"

