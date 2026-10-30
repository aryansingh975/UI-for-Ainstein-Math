import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.graph_loader import load_all_graphs, get_graph
from app.engine.state_machine import (
    new_session,
    apply_result,
    method_for_node,
    get_method_node,
    first_step_of,
    method_chain,
    successor_of,
)
from app.engine.tutor_engine import process_step

client = TestClient(app)


@pytest.fixture(scope="module")
def graphs():
    return load_all_graphs()


def test_all_32_graphs_method_resolution(graphs):
    """Verify that every step across all 32 solution graphs resolves to a valid method node."""
    for pid, g in graphs.items():
        steps = [n for n in g.nodes if n.type == "step"]
        for s in steps:
            m = method_for_node(s.id, g)
            assert m is not None, f"Step {s.id} in {pid} failed to resolve to a method"
            mn = get_method_node(m, g)
            assert mn is not None, f"Method {m} for step {s.id} in {pid} has no method node"
            assert mn.type == "method"
            assert mn.label is not None and len(mn.label) > 0


def test_all_32_graphs_first_step_resolution(graphs):
    """Verify that first_step_of always returns a step node (never a method or conclusion)."""
    for pid, g in graphs.items():
        methods = [n for n in g.nodes if n.type == "method"]
        node_map = {n.id: n for n in g.nodes}
        for mn in methods:
            fs_id = first_step_of(mn.id, g)
            node = node_map.get(fs_id)
            assert node is not None, f"First step {fs_id} for method {mn.id} in {pid} not found"
            assert node.type == "step", f"First step {fs_id} for method {mn.id} in {pid} is type {node.type}, expected 'step'"


def test_all_32_graphs_method_chain(graphs):
    """Verify that method_chain traverses multiple steps rather than stopping at method_id."""
    for pid, g in graphs.items():
        methods = [n for n in g.nodes if n.type == "method"]
        for mn in methods:
            chain = method_chain(mn.id, g)
            assert len(chain) >= 2, f"Method chain for {mn.id} in {pid} too short: {chain}"


def test_chapter7_silent_method_discovery_via_api():
    """Verify that typing math calculation '24' silently locks Method 1 and returns method_label."""
    res_start = client.post("/api/v1/sessions/start", json={"problem_id": "g08-hegp107-ex001"})
    assert res_start.status_code == 200
    sid = res_start.json()["session_id"]

    # Turn 1: Givens
    client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "3:4 and 72:96"})
    # Turn 2: Goal
    res_goal = client.post(
        f"/api/v1/sessions/{sid}/step",
        json={"student_input": "whether the ratios are proportional"},
    )
    assert res_goal.json()["method_label"] is None  # No method locked yet

    # Turn 3: Student calculates HCF = 24 directly
    res_calc = client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "24"})
    data = res_calc.json()
    assert data["verdict"] == "ACCEPT"
    assert "Simplification" in data["method_label"]
    assert "divide" in data["next_prompt"].lower() or "72" in data["next_prompt"]


def test_chapter9_percentages_silent_method_discovery_via_api():
    """Verify that in percentages (which uses step1_profit), method is cleanly resolved."""
    res_start = client.post("/api/v1/sessions/start", json={"problem_id": "g08-hegp201-ex-p19-q1"})
    assert res_start.status_code == 200
    sid = res_start.json()["session_id"]

    # Givens & Goal (CP=75, SP=110)
    client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "CP = 75, SP = 110"})
    client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "Profit and profit percentage"})

    # Student enters profit calculation: 110 - 75 = 35
    res_calc = client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": "35"})
    data = res_calc.json()
    assert data["verdict"] == "ACCEPT"
    assert data["method_label"] == "Method 1: Profit % Formula"


def test_method_junction_never_prompts_choice_of_method():
    """Verify that start_session and check_step never prompt 'Choose a method'."""
    res = client.post("/api/v1/sessions/start", json={"problem_id": "g08-hegp107-ex001"})
    assert "choose a method" not in res.json()["prompt"].lower()
