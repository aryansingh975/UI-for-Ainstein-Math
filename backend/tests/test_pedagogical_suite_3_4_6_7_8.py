import pytest
from app.graph_loader import load_all_graphs
from app.engine.state_machine import new_session, apply_result
from app.engine.tutor_engine import process_step


@pytest.fixture(scope="module")
def graphs():
    return load_all_graphs()


def test_problem_3_acknowledge_and_redirect_on_word_problems(graphs):
    """Problem 3: In word problems with required extraction (optional: false),
    jumping straight to calculation should return EXTRACTION_REQUIRED with praise and redirect."""
    g_tv = graphs["g08-hegp201-ex010"]  # TV depreciation: optional=false for extractions
    s = new_session(g_tv)
    assert s.current_node_id == "given_extraction"

    # Student jumps straight to calculation: 1050 (or 21000 * 0.05 = 1050)
    r = process_step("1050", s, g_tv)
    assert r.verdict == "EXTRACTION_REQUIRED"
    assert r.node_id == "given_extraction"
    assert "Great calculation" in r.feedback
    assert "let's first list what is given" in r.feedback

    # State must not have erroneously advanced
    apply_result(s, r, g_tv)
    assert s.current_node_id == "given_extraction"
    assert s.fail_streak == 0


def test_problem_4_enforcing_method_commitment(graphs):
    """Problem 4: Once a method is active (session.method_id), prevent switching to another method."""
    g1 = graphs["g08-hegp107-ex001"]
    s = new_session(g1)

    # Student starts with Method 1 (HCF = 24)
    r1 = process_step("24", s, g1)
    assert r1.verdict == "ACCEPT"
    assert r1.method_id == "m1"
    apply_result(s, r1, g1)
    assert s.method_id == "m1"
    cur_node = s.current_node_id

    # Mid-solution, student attempts Cross Multiplication (Method 5: 288)
    r2 = process_step("288", s, g1)
    assert r2.verdict == "METHOD_LOCKED"
    assert r2.method_id == "m1"
    assert "Method 5" in r2.feedback or "Cross Multiplication" in r2.feedback
    assert "currently solving with" in r2.feedback

    # State machine keeps the current node and method unchanged
    apply_result(s, r2, g1)
    assert s.current_node_id == cur_node
    assert s.method_id == "m1"


def test_problem_6_fast_learner_compound_input(graphs):
    """Problem 6: If student solves current step and successor in one compound input, advance 2 steps."""
    g1 = graphs["g08-hegp107-ex001"]
    s = new_session(g1)

    # Method 7: m7_s1 accepts 0.75, m7_s3 is successor which accepts '0.75 = 0.75'
    # Start at m7_s1
    r_start = process_step("0.75", s, g1)
    assert r_start.verdict == "ACCEPT"
    apply_result(s, r_start, g1)
    assert s.method_id == "m7"
    assert s.current_node_id == "m7_s3"

    # Now compound input solving m7_s3 and conclusion: '0.75 = 0.75, so yes'
    r_compound = process_step("0.75 = 0.75, so yes", s, g1)
    assert r_compound.verdict == "MULTI_STEP_ACCEPT"
    assert len(r_compound.compound_trail) == 2
    assert "Excellent work" in r_compound.feedback

    apply_result(s, r_compound, g1)
    # Both steps applied to trail
    assert len(s.trail) >= 3


def test_problem_7_conceptual_misconceptions(graphs):
    """Problem 7: Catch cognitive traps (depreciation addition, percent without division, reversed ratio)."""
    g_tv = graphs["g08-hegp201-ex010"]
    s = new_session(g_tv)

    # 1. Depreciation addition misconception
    r_deprec = process_step("21000 + 1050 = 22050", s, g_tv)
    assert r_deprec.verdict == "MISCONCEPTION"
    assert "Depreciation means the asset loses value" in r_deprec.feedback
    assert "subtract" in r_deprec.feedback

    # 2. Percentage multiplication without division by 100
    r_pct = process_step("21000 * 5 = 105000", s, g_tv)
    assert r_pct.verdict == "MISCONCEPTION"
    assert "percentage means 'per hundred'" in r_pct.feedback

    # 3. Reversed ratio in g08-hegp107-ex001
    g1 = graphs["g08-hegp107-ex001"]
    s_ratio = new_session(g1)
    r_rev = process_step("4:3", s_ratio, g1)
    assert r_rev.verdict == "MISCONCEPTION"
    assert "Notice the order of terms" in r_rev.feedback


def test_problem_8_incremental_entity_extraction(graphs):
    """Problem 8: Multi-turn extraction preserves partial givens until all required entities are stated."""
    g_tv = graphs["g08-hegp201-ex010"]
    s = new_session(g_tv)
    assert s.current_node_id == "given_extraction"
    assert len(s.extracted_entities) == 0

    # Turn 1: Student extracts only purchase price
    r1 = process_step("The price is 21000", s, g_tv)
    assert r1.verdict == "PARTIAL_EXTRACTION"
    assert "21000" in s.extracted_entities
    assert "What else is given" in r1.feedback
    apply_result(s, r1, g_tv)
    assert s.current_node_id == "given_extraction"

    # Turn 2: Student extracts rate and time
    r2 = process_step("5% for 1 year", s, g_tv)
    assert r2.verdict == "ACCEPT"
    assert "5" in s.extracted_entities
    assert "1" in s.extracted_entities
    apply_result(s, r2, g_tv)

    # Now it advances to goal_extraction!
    assert s.current_node_id == "goal_extraction"

