# pyrefly: ignore [missing-import]
import pytest
from ainstein_math.verification.trace_checker import verify_trace_dependencies
from ainstein_math.verification.evaluator import evaluate_reasoning_trace


def test_verify_valid_trace():
    steps = [
        {"step_id": "E1", "type": "EXTRACT", "entity": "debt", "value": "-20"},
        {"step_id": "E2", "type": "EXTRACT", "entity": "deposit", "value": "100"},
        {"step_id": "M1", "type": "MAP", "trigger": "deposit", "gen_trigger": "deposit", "concept": "add", "operator": "ADD"},
        {"step_id": "B1", "type": "BIND", "dependencies": ["E1", "E2", "M1"], "logic": "add deposit to debt", "roles": {"LEFT": "-20", "RIGHT": "100"}},
        {"step_id": "CONSTRUCT", "type": "CONSTRUCT", "ast_expression": "ADD[balance](-20, 100)", "target": "dollars"}
    ]

    res = verify_trace_dependencies(steps)
    assert res["valid"] is True
    assert len(res["errors"]) == 0


def test_verify_invalid_dependency():
    steps = [
        {"step_id": "E1", "type": "EXTRACT", "entity": "debt", "value": "-20"},
        {"step_id": "B1", "type": "BIND", "dependencies": ["E1", "E99"], "logic": "invalid ref", "roles": {}},
        {"step_id": "CONSTRUCT", "type": "CONSTRUCT", "ast_expression": "-20", "target": "dollars"}
    ]

    res = verify_trace_dependencies(steps)
    assert res["valid"] is False
    assert any("E99" in err for err in res["errors"])


def test_evaluate_reasoning_trace():
    trace_text = """
    [E1] EXTRACT entity: "debt of 20 dollars" -> val: -20
    [E2] EXTRACT entity: "deposit of 100 dollars" -> val: 100
    [M1] MAP trigger: "deposit is made" -> gen_trigger: "deposit" -> concept: "incremental addition to state" -> op: ADD
    [B1] <E1, E2, M1> BIND logic: "Initial account state modified by deposit" -> role: LEFT = -20, RIGHT = 100
    [CONSTRUCT] Tree: ADD[balance](-20, 100) -> target: "dollars"
    """

    res = evaluate_reasoning_trace(trace_text)

    assert res["result"] == 80
    assert res["target_unit"] == "dollars"
    assert "ADD[balance]" in res["ascii_tree"]
    assert "-20" in res["ascii_tree"]
    assert "100" in res["ascii_tree"]
