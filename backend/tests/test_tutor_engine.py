import pytest
from app.graph_loader import get_graph, load_all_graphs
from app.engine.state_machine import new_session, begin_method, apply_result
from app.engine.tutor_engine import process_step


@pytest.fixture(scope="module")
def graphs():
    return load_all_graphs()


def step(raw_input, session, graph):
    r = process_step(raw_input, session, graph)
    apply_result(session, r, graph)
    return r


def test_dialogue_flows(graphs):
    g1 = graphs["g08-hegp107-ex001"]
    ex011 = graphs["g08-hegp107-ex011"]
    quad = graphs["g10-quad-ex001"]

    assert ex011 is not None

    # JEV method routes
    s_jev = new_session(quad)
    assert begin_method(s_jev, "m1_factor", quad) is True
    assert s_jev.current_node_id == "m1_s1"

    r = step("-2 and -3", s_jev, quad)
    assert r.verdict == "ACCEPT"
    assert r.node_id == "m1_s1"

    # Cannot switch method once locked
    assert begin_method(s_jev, "m2_formula", quad) is False
    assert begin_method(s_jev, "start", quad) is False

    # Flow A: Full simplification route
    s = new_session(g1)
    # A1 garbage rejected
    r = step("i love paris", s, g1)
    assert r.verdict == "GARBAGE"

    # A2 irrelevant true flagged
    r = step("3+4=7", s, g1)
    assert r.verdict == "IRRELEVANT_TRUE"

    # A3 wrong gcd corrected immediately
    r = step("hcf is 25", s, g1)
    assert r.verdict == "WRONG_CLAIM"

    # A4 correct gcd accepted (unlisted phrasing) & method silently inferred
    r = step("hcf of 72 and 96 is 24", s, g1)
    assert r.verdict == "ACCEPT"
    assert s.method_id == "m1"

    # A5 divide step accepted
    r = step("72/24=3 and 96/24=4", s, g1)
    assert r.verdict == "ACCEPT"

    # A6 simplified ratio accepted
    r = step("3:4", s, g1)
    assert r.verdict == "ACCEPT"

    # A7 comparison accepted
    r = step("3:4 = 3:4", s, g1)
    assert r.verdict == "ACCEPT"

    # A8 conclusion auto-detected
    r = step("yes", s, g1)
    assert r.verdict == "CONCLUSION_RIGHT"
    assert s.completed is True


def test_flows_b_c_d_e(graphs):
    g1 = graphs["g08-hegp107-ex001"]

    # Flow B: 72=24×3
    s = new_session(g1)
    r = step("72 = 24 × 3 and 96 = 24 × 4", s, g1)
    assert r.verdict == "ACCEPT"
    r = step("3:4 and 72:96 are proportional", s, g1)
    assert r.verdict == "CONCLUSION_RIGHT"

    # Flow C: Decimal route
    s = new_session(g1)
    r = step("0.75", s, g1)
    assert r.verdict == "ACCEPT"
    assert s.method_id == "m7"
    r = step("0.75", s, g1)
    assert r.verdict == "ACCEPT"
    r = step("0.75 = 0.75", s, g1)
    assert r.verdict == "ACCEPT"
    r = step("yes", s, g1)
    assert r.verdict == "CONCLUSION_RIGHT"

    # Flow D: Cross multiplication
    s = new_session(g1)
    r = step("288", s, g1)
    assert r.verdict == "ACCEPT"
    assert s.method_id == "m5"
    # Wrong product
    r = step("3*96=287", s, g1)
    assert r.verdict == "WRONG_CLAIM"
    # Corrected
    r = step("288", s, g1)
    assert r.verdict == "ACCEPT"
    r = step("288 = 288", s, g1)
    assert r.verdict == "ACCEPT"
    r = step("yes", s, g1)
    assert r.verdict == "CONCLUSION_RIGHT"

    # Flow E: Step-by-step reduction
    s = new_session(g1)
    r = step("36:48", s, g1)
    assert r.verdict == "ACCEPT"
    assert s.method_id == "m4"
    for step_val in ["18:24", "9:12", "3:4", "3:4 = 3:4"]:
        r = step(step_val, s, g1)
        assert r.verdict == "ACCEPT"
    r = step("yes", s, g1)
    assert r.verdict == "CONCLUSION_RIGHT"


def test_conclusion_and_edge_cases(graphs):
    g1 = graphs["g08-hegp107-ex001"]

    # Flow F: Wrong conclusion after reaching the conclusion point
    s = new_session(g1)
    step("72/24=3 and 96/24=4", s, g1)
    step("3:4", s, g1)
    step("3:4 = 3:4", s, g1)

    r = step("no", s, g1)
    assert r.verdict == "CONCLUSION_WRONG"
    assert s.completed is False

    r = step("they are not proportional", s, g1)
    assert r.verdict == "CONCLUSION_WRONG"

    # Flow F2: Mid-step bare no is nudged (UNPARSED), not a conclusion
    s_mid = new_session(g1)
    step("72/24=3 and 96/24=4", s_mid, g1)
    r = step("no", s_mid, g1)
    assert r.verdict == "UNPARSED"

    # Flow G: Bare yes at start is nudged (UNPARSED), not accepted as conclusion
    s_fresh = new_session(g1)
    r = step("yes", s_fresh, g1)
    assert r.verdict == "UNPARSED"

    # Flow H: direct ratio equality completes problem
    s = new_session(g1)
    r = step("3:4 = 72:96", s, g1)
    assert r.verdict == "CONCLUSION_RIGHT"

    # Flow I: Keyword approach
    s = new_session(g1)
    r = step("cross multiply", s, g1)
    assert r.verdict == "ACCEPT"
    assert r.approach_only is True
    assert s.method_id == "m5"
    assert s.current_node_id == "m5_s1"
    r = step("3*96 and 4*72", s, g1)
    assert r.verdict == "ACCEPT"
    r = step("3*96=288", s, g1)
    assert r.verdict == "ACCEPT"

    # Flow J: Garbage rejection
    assert step("i love paris 3:4", s, g1).verdict == "GARBAGE"
    assert step("hello world", s, g1).verdict == "GARBAGE"

    # Flow L: Wrong value at current step
    s = new_session(g1)
    s.current_node_id = "m1_s1"
    r = process_step("25", s, g1)
    assert r.verdict == "WRONG_CLAIM"
    assert s.fail_streak == 0
    apply_result(s, r, g1)
    assert s.fail_streak == 1
    r = step("24", s, g1)
    assert r.verdict == "ACCEPT"
    assert s.fail_streak == 0


def test_tv_depreciation_and_age_problems(graphs):
    # TV Depreciation
    tv_graph = graphs["g08-hegp201-ex010"]
    s = new_session(tv_graph)
    assert s.current_node_id == "given_extraction"

    r = step("Original value = ₹21000, Rate = 5%, Time = 1 year", s, tv_graph)
    assert r.verdict == "ACCEPT"

    r = step("Value after 1 year", s, tv_graph)
    assert r.verdict == "ACCEPT"

    r = step("1050", s, tv_graph)
    assert r.verdict == "ACCEPT"

    # The step from the user's screenshots!
    r = step("₹21,000 - ₹1050 = ₹19,950", s, tv_graph)
    assert r.verdict == "ACCEPT"

    r = step("19950", s, tv_graph)
    assert r.verdict == "CONCLUSION_RIGHT"
    assert s.completed is True


def test_new_problem_g08_lin_ex003_with_sympy(graphs):
    lin = graphs["g08-lin-ex003"]
    assert lin is not None
    s = new_session(lin)

    # 1. Expand brackets step (verified via SymPy / accept)
    r = step("3x - 6 + 5 = 2x + 4", s, lin)
    assert r.verdict == "ACCEPT"
    assert s.method_id == "m1"

    # 2. Simplify LHS
    r = step("3x - 1 = 2x + 4", s, lin)
    assert r.verdict == "ACCEPT"

    # 3. Transpose terms
    r = step("3x - 2x = 4 + 1", s, lin)
    assert r.verdict == "ACCEPT"

    # 4. Final step
    r = step("x = 5", s, lin)
    assert r.verdict == "ACCEPT"

    # 5. Conclusion
    r = step("x = 5", s, lin)
    assert r.verdict == "CONCLUSION_RIGHT"
    assert s.completed is True


