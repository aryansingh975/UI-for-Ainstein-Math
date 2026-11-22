"""Automated Validator Test Suite for the Stateless Navigator Module.

Tests the 3 critical bug vectors + irrelevant input threshold:
    1. The "Good Student" Check (Fluff word stripping -> 1.0 match)
    2. The Short Input Collision (Single-char 'x' collision prevention)
    3. The Typo Resiliency Check (Character n-grams for 'daugter')
    4. The Irrelevant Input Threshold Check (Off-topic queries -> 'No node found')
"""

from __future__ import annotations

import sys
from typing import Any, Dict

from app.navigator.navigator import navigate_dag
from app.navigator.normalizer import normalize, to_token_set
from app.navigator.scorer import score_phrase


# ---------------------------------------------------------------------------
# Mock Math DAG (V1 Stateless Specification)
# ---------------------------------------------------------------------------

MOCK_MATH_DAG: Dict[str, Any] = {
    "graph_meta": {
        "graph_id": "sg-algebra-age-001",
        "title": "Father and Daughter Age Problem",
        "problem_text": "The father is 3 times as old as his daughter. In 10 years, he will be twice her age. Find the daughter's present age.",
    },
    "nodes": [
        {
            "id": "goal_extraction",
            "type": "extraction",
            "label": "Identify the Goal",
            "description": "What does the problem ask us to find?",
            "prompt": "What do we need to find?",
            "accept": [
                "daughter's present age",
                "present age of daughter",
                "age of daughter",
                "find x",
                "daughter's age now",
                "how old is the daughter",
            ],
            "hints": [
                "The problem asks for the daughter's current age.",
                "We need to find the present age of the daughter.",
            ],
        },
        {
            "id": "variable_def",
            "type": "definition",
            "label": "Define Variable",
            "description": "Let x represent the daughter's present age.",
            "prompt": "What variable represents the unknown?",
            "accept": [
                "let x be daughter's age",
                "x = daughter age",
                "x is daughter's age",
                "x",
            ],
            "hints": [
                "Assign variable x to the daughter's age.",
            ],
        },
        {
            "id": "equation_setup",
            "type": "equation",
            "label": "Set Up Equation",
            "description": "Formulate the algebraic equation relating ages in 10 years.",
            "prompt": "What equation represents the relationship in 10 years?",
            "accept": [
                "3*x + 10 = 2*(x + 10)",
                "3x + 10 = 2x + 20",
                "x + 20 = 40",
                "x + 20 eq 40",
            ],
            "hints": [
                "Set father's age in 10 years equal to 2 times daughter's age in 10 years.",
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Test Runner Functions
# ---------------------------------------------------------------------------

def test_good_student_check() -> None:
    """Vector 1: Fluff words are dropped to achieve a perfect 1.0 match."""
    input_str = "We are trying to find the daughter's present age"
    accept_phrase = "daughter present age"

    tokens_input = to_token_set(input_str)
    tokens_accept = to_token_set(accept_phrase)
    assert tokens_input == tokens_accept, (
        f"Token mismatch: {tokens_input} != {tokens_accept}"
    )

    similarity = score_phrase(input_str, accept_phrase)
    assert abs(similarity - 1.0) < 1e-6, (
        f"Expected 1.0 score, got {similarity}"
    )

    matched_node = navigate_dag(MOCK_MATH_DAG, input_str)
    assert isinstance(matched_node, dict), f"Expected node dict, got: {matched_node}"
    assert matched_node["id"] == "goal_extraction", (
        f"Expected goal_extraction, got {matched_node['id']}"
    )
    print("PASS: [Vector 1] The Good Student Check - Analytical phrase dropped fluff words and scored 1.0 against target node.")


def test_short_input_collision() -> None:
    """Vector 2: Single-char 'x' matches variable_def and avoids colliding with equations."""
    # 2a. 'x' should cleanly resolve to variable_def (where 'x' is an explicit accept entry)
    matched_x = navigate_dag(MOCK_MATH_DAG, "x")
    assert isinstance(matched_x, dict), f"Expected node dict for 'x', got: {matched_x}"
    assert matched_x["id"] == "variable_def", (
        f"Expected 'variable_def' for 'x', got '{matched_x['id']}'"
    )

    # 2b. Score of 'x' against long equation phrases must be penalized below threshold
    eq_score = score_phrase("x", "x + 20 = 40")
    assert eq_score <= 0.50, f"Expected 'x' vs equation score <= 0.50, got {eq_score}"

    # 2c. Unmatched short token 'z' must return 'No node found'
    matched_z = navigate_dag(MOCK_MATH_DAG, "z")
    assert matched_z == "No node found", (
        f"Expected 'No node found' for 'z', got: {matched_z}"
    )

    print("PASS: [Vector 2] The Short Input Collision - 'x' accurately matched variable_def, did not trigger equation collision (score <= 0.50), and 'z' returned 'No node found'.")


def test_typo_resiliency() -> None:
    """Vector 3: Typo 'daugter' scores high via character bigrams to match goal_extraction."""
    # 3a. Single word typo 'daugter'
    matched_single = navigate_dag(MOCK_MATH_DAG, "daugter")
    assert isinstance(matched_single, dict), f"Expected node dict for 'daugter', got: {matched_single}"
    assert matched_single["id"] == "goal_extraction", (
        f"Expected 'goal_extraction' for 'daugter', got '{matched_single['id']}'"
    )

    # 3b. Full phrase typo 'daugter present age'
    matched_phrase = navigate_dag(MOCK_MATH_DAG, "daugter present age")
    assert isinstance(matched_phrase, dict), f"Expected node dict for 'daugter present age', got: {matched_phrase}"
    assert matched_phrase["id"] == "goal_extraction", (
        f"Expected 'goal_extraction' for 'daugter present age', got '{matched_phrase['id']}'"
    )

    # Verify score exceeds threshold
    score_typo = score_phrase("daugter present age", "daughter present age")
    assert score_typo > 0.70, f"Expected high typo score (> 0.70), got {score_typo}"

    print("PASS: [Vector 3] The Typo Resiliency Check - 'daugter' and 'daugter present age' successfully matched goal_extraction via character n-grams.")


def test_irrelevant_input_threshold() -> None:
    """Vector 4: Irrelevant queries must return 'No node found'."""
    irrelevant_queries = [
        "photosynthesis in green plants",
        "order a large pepperoni pizza",
        "the capital of France is Paris",
    ]
    for query in irrelevant_queries:
        result = navigate_dag(MOCK_MATH_DAG, query)
        assert result == "No node found", (
            f"Expected 'No node found' for '{query}', got: {result}"
        )

    print("PASS: [Vector 4] Irrelevant Input Threshold Check - Off-topic queries returned 'No node found'.")


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all test vectors and print summary."""
    print("=" * 70)
    print("RUNNING STATELESS NAVIGATOR AUTOMATED VALIDATION SUITE")
    print("=" * 70)

    test_good_student_check()
    test_short_input_collision()
    test_typo_resiliency()
    test_irrelevant_input_threshold()

    print("=" * 70)
    print("ALL TEST CASES PASSED SUCCESSFULLY (4/4 PASS)")
    print("=" * 70)


if __name__ == "__main__":
    main()
