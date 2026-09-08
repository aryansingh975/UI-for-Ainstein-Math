from ainstein_math.reasoning_grammar.parser import (
    TraceStepType,
    classify_trace_line,
    parse_extract_line,
    parse_map_line,
    parse_bind_line,
    parse_construct_line,
    parse_full_trace,
)


def test_classify_trace_line():
    assert classify_trace_line('[E1] EXTRACT entity: "x" -> val: 5') == TraceStepType.EXTRACT
    assert classify_trace_line('[M1] MAP trigger: "x" -> gen_trigger: "y" -> concept: "z" -> op: ADD') == TraceStepType.MAP
    assert classify_trace_line('[B1] <E1> BIND logic: "l" -> role: ARG = 5') == TraceStepType.BIND
    assert classify_trace_line('[CONSTRUCT] Tree: ADD(1, 2) -> target: "items"') == TraceStepType.CONSTRUCT


def test_parse_extract_line():
    line = '[E1] EXTRACT entity: "debt of 20 dollars" -> val: -20'
    result = parse_extract_line(line)
    assert result == {
        "step_id": "E1",
        "type": "EXTRACT",
        "entity": "debt of 20 dollars",
        "value": "-20",
    }


def test_parse_map_line():
    line = (
        '[M1] MAP trigger: "deposit is made" '
        '-> gen_trigger: "deposit" '
        '-> concept: "incremental addition to state" '
        '-> op: ADD'
    )
    result = parse_map_line(line)
    assert result == {
        "step_id": "M1",
        "type": "MAP",
        "trigger": "deposit is made",
        "gen_trigger": "deposit",
        "concept": "incremental addition to state",
        "operator": "ADD",
    }


def test_parse_bind_line():
    line = (
        '[B1] <E1, E2, M1> BIND logic: '
        '"Initial account state is modified by deposit amount" '
        '-> role: LEFT = -20, RIGHT = 100'
    )
    result = parse_bind_line(line)
    assert result == {
        "step_id": "B1",
        "type": "BIND",
        "dependencies": ["E1", "E2", "M1"],
        "logic": "Initial account state is modified by deposit amount",
        "roles": {"LEFT": "-20", "RIGHT": "100"},
    }


def test_parse_construct_line():
    line = '[CONSTRUCT] Tree: ADD[balance](-20, 100) -> target: "dollars"'
    result = parse_construct_line(line)
    assert result == {
        "step_id": "CONSTRUCT",
        "type": "CONSTRUCT",
        "ast_expression": "ADD[balance](-20, 100)",
        "target": "dollars",
    }


def test_parse_full_trace():
    trace = """
    [E1] EXTRACT entity: "debt of 20 dollars" -> val: -20
    [E2] EXTRACT entity: "deposit of 100 dollars" -> val: 100
    [M1] MAP trigger: "deposit is made" -> gen_trigger: "deposit" -> concept: "incremental addition to state" -> op: ADD
    [B1] <E1, E2, M1> BIND logic: "Initial state modified by deposit" -> role: LEFT = -20, RIGHT = 100
    [CONSTRUCT] Tree: ADD[balance](-20, 100) -> target: "dollars"
    """
    steps = parse_full_trace(trace)
    assert len(steps) == 5
    assert steps[0]["step_id"] == "E1"
    assert steps[1]["step_id"] == "E2"
    assert steps[2]["step_id"] == "M1"
    assert steps[3]["step_id"] == "B1"
    assert steps[4]["step_id"] == "CONSTRUCT"