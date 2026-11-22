"""Comprehensive Test Suite for Navigator v2 (with v1 Deterministic Ranker).

Tests:
1. Normalization & Tokenization
2. Scorer: Exact Match, Token Set Equivalence, Short-Input Guardrail, Weighted Jaccard
3. Ranker Hierarchy & Tie-Breaking (Exact Match Dominance -> Weighted Jaccard -> Specificity Tie-Break)
4. Graph Loader & Solution Paths enumeration
5. Path Finder reachability & Step Jump detection
6. Interactive Session & Trail tracking
7. Multi-DAG validation across solution_graph/ files
"""

from __future__ import annotations

import glob
from pathlib import Path

import pytest

from app.navigator_02.graph_loader import (
    get_all_solution_paths,
    load_dag,
)
from app.navigator_02.navigator import Navigator
from app.navigator_02.normalizer import normalize, to_token_set
from app.navigator_02.path_finder import evaluate_transition
from app.navigator_02.ranker import DEFAULT_THRESHOLD, resolve_with_score
from app.navigator_02.scorer import jaccard_similarity, score_phrase, weighted_jaccard


# ===========================================================================
# 1. Normalizer Tests
# ===========================================================================

def test_normalizer_math_symbols():
    assert "eq" in normalize("x = 5")
    assert "div" in normalize("72 / 24")
    assert "mul" in normalize("3 * 96")
    assert "plus" in normalize("x + y")


def test_normalizer_possessives_and_ratios():
    assert normalize("teacher's ratio") == "teacher ratio"
    tokens = to_token_set("3:4")
    assert "3" in tokens and "4" in tokens


# ===========================================================================
# 2. Scorer Tests (v1 Deterministic Scorer)
# ===========================================================================

def test_scorer_exact_match_dominance():
    score, mtype = score_phrase("hcf is 24", "hcf is 24")
    assert score == 1.0
    assert mtype == "EXACT_STRING_MATCH"


def test_scorer_token_set_equivalence():
    score, mtype = score_phrase("the hcf is 24", "hcf 24")
    assert score == 1.0
    assert mtype == "EXACT_TOKEN_MATCH"


def test_scorer_short_input_guardrail():
    # 'x' against 'x' should be 1.0
    s_exact, _ = score_phrase("x", "x")
    assert s_exact == 1.0

    # 'x' against a multi-token formula should be penalized (1 / len)
    s_penalized, mtype = score_phrase("x", "x plus 20 eq 40")
    assert s_penalized < 0.35
    assert mtype == "SHORT_INPUT_GUARDRAIL"

    # 'z' against formula not containing 'z' should be 0.0
    s_mismatch, mtype2 = score_phrase("z", "x plus 20 eq 40")
    assert s_mismatch == 0.0
    assert mtype2 == "SHORT_INPUT_MISMATCH"


def test_scorer_weighted_jaccard_fuzzy():
    # Typos and partial words
    score, mtype = score_phrase("simplif ratio", "simplify ratio")
    assert score > 0.60
    assert mtype == "FUZZY_WEIGHTED_JACCARD"

    # Unrelated phrases
    s_unrelated, _ = score_phrase("apple banana", "ratio proportion")
    assert s_unrelated == 0.0


# ===========================================================================
# 3. Ranker Hierarchy & Specificity Tie-Breaking Tests
# ===========================================================================

def test_ranker_exact_match_dominance():
    nodes = [
        {"id": "node_fuzzy", "accept": ["simplify ratio using highest common factor"]},
        {"id": "node_exact", "accept": ["simplify 72:96"]},
    ]
    matched, score, mtype, phrase = resolve_with_score("simplify 72:96", nodes, threshold=0.1)
    assert matched is not None
    assert matched["id"] == "node_exact"
    assert score == 1.0
    assert mtype == "EXACT_STRING_MATCH"


def test_ranker_tie_breaker_by_specificity():
    # Two nodes with similar matching tokens, but node_specific has more specific phrase
    nodes = [
        {"id": "node_short", "accept": ["ratio"]},
        {"id": "node_specific", "accept": ["ratio of glasses to sugar"]},
    ]
    matched, score, mtype, phrase = resolve_with_score("ratio of glasses to sugar", nodes, threshold=0.1)
    assert matched is not None
    assert matched["id"] == "node_specific"
    assert score == 1.0


def test_ranker_threshold_gate():
    nodes = [
        {"id": "node_1", "accept": ["divide both numbers by 24"]},
    ]
    # Input has virtually no overlap
    matched, score, mtype, _ = resolve_with_score("completely unrelated sentence", nodes, threshold=DEFAULT_THRESHOLD)
    assert matched is None
    assert mtype in ("BELOW_THRESHOLD", "NO_MATCH")


# ===========================================================================
# 4. Graph Loader & Solution Paths Tests
# ===========================================================================

def test_graph_loader_paths():
    sample_dag = {
        "start_node": "A",
        "conclusion_node": "D",
        "nodes": [
            {"id": "A", "importance": "no", "accept": ["start"]},
            {"id": "B", "importance": "yes", "accept": ["step 1"]},
            {"id": "C", "importance": "no", "accept": ["step 2"]},
            {"id": "D", "importance": "no", "accept": ["finish"]},
        ],
        "edges": [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
            {"from": "C", "to": "D"},
        ],
    }
    dag = load_dag(sample_dag)
    paths = get_all_solution_paths(dag)
    assert len(paths) == 1
    assert paths[0] == ["A", "B", "C", "D"]
    assert dag["nodes"][1]["importance"] == "yes"


# ===========================================================================
# 5. Path Reachability & Step Jump Tests
# ===========================================================================

def test_step_jump_detected_on_important_node():
    sample_dag = {
        "start_node": "start",
        "conclusion_node": "conclusion",
        "nodes": [
            {"id": "start", "importance": "no", "accept": ["start"]},
            {"id": "step1", "importance": "yes", "label": "Key Step 1", "prompt": "Do step 1", "accept": ["step 1"]},
            {"id": "step2", "importance": "no", "label": "Step 2", "accept": ["step 2"]},
            {"id": "conclusion", "importance": "no", "accept": ["done"]},
        ],
        "edges": [
            {"from": "start", "to": "step1"},
            {"from": "step1", "to": "step2"},
            {"from": "step2", "to": "conclusion"},
        ],
    }
    nav = Navigator(sample_dag, threshold=0.1)

    # 1. Start session
    r1 = nav.process_input("start")
    assert r1.status == "FIRST_MATCH"
    assert nav.current_node["id"] == "start"

    # 2. Skip step1 (importance=yes) directly to step2
    r2 = nav.process_input("step 2")
    assert r2.status == "STEP_JUMP"
    assert "STEP JUMP DETECTED" in r2.message
    assert len(r2.skipped_nodes) == 1
    assert r2.skipped_nodes[0]["id"] == "step1"
    # Pointer must remain at 'start'
    assert nav.current_node["id"] == "start"

    # 3. Address the skipped node
    r3 = nav.process_input("step 1")
    assert r3.status == "ADVANCED"
    assert nav.current_node["id"] == "step1"

    # 4. Now advance to step2
    r4 = nav.process_input("step 2")
    assert r4.status == "ADVANCED"
    assert nav.current_node["id"] == "step2"

    # 5. Advance to conclusion
    r5 = nav.process_input("done")
    assert r5.status == "ADVANCED"
    assert nav.current_node["id"] == "conclusion"
    assert nav.trail == ["start", "step1", "step2", "conclusion"]


def test_invalid_path_backward_or_unreachable():
    sample_dag = {
        "start_node": "start",
        "conclusion_node": "conclusion",
        "nodes": [
            {"id": "start", "importance": "no", "accept": ["start"]},
            {"id": "pathA_1", "importance": "no", "accept": ["method a"]},
            {"id": "pathB_1", "importance": "no", "accept": ["method b"]},
            {"id": "conclusion", "importance": "no", "accept": ["conclusion"]},
        ],
        "edges": [
            {"from": "start", "to": "pathA_1"},
            {"from": "start", "to": "pathB_1"},
            {"from": "pathA_1", "to": "conclusion"},
            {"from": "pathB_1", "to": "conclusion"},
        ],
    }
    nav = Navigator(sample_dag, threshold=0.1)
    nav.process_input("method a")
    assert nav.current_node["id"] == "pathA_1"

    # Try jumping across branches to method b (unreachable)
    r = nav.process_input("method b")
    assert r.status == "INVALID_PATH"
    assert "INVALID input, give a valid input." in r.message
    assert nav.current_node["id"] == "pathA_1"


# ===========================================================================
# 6. First Input to Arbitrary Node
# ===========================================================================

def test_first_input_arbitrary_node():
    sample_dag = {
        "start_node": "start",
        "conclusion_node": "conclusion",
        "nodes": [
            {"id": "start", "importance": "no", "accept": ["start"]},
            {"id": "middle", "importance": "no", "accept": ["middle node"]},
            {"id": "conclusion", "importance": "no", "accept": ["end node"]},
        ],
        "edges": [
            {"from": "start", "to": "middle"},
            {"from": "middle", "to": "conclusion"},
        ],
    }
    nav = Navigator(sample_dag, threshold=0.1)
    r = nav.process_input("middle node")
    assert r.status == "FIRST_MATCH"
    assert nav.current_node["id"] == "middle"
    assert nav.trail == ["middle"]


# ===========================================================================
# 7. Multi-DAG Real World Tests
# ===========================================================================

def test_navigator_on_multiple_real_dags():
    root = Path(__file__).resolve().parent.parent.parent
    dag_files = [str(p) for p in root.glob("solution_graph/**/graph.json")]
    if not dag_files:
        dag_files = glob.glob("/home/saikat/UI-for-Ainstein-Math/solution_graph/**/graph.json", recursive=True)
    assert len(dag_files) >= 5, "Expected at least 5 real solution DAGs"

    tested_count = 0
    for file_path in dag_files[:6]:
        nav = Navigator(file_path, threshold=0.1)
        assert len(nav.dag.get("nodes", [])) > 0
        assert len(nav.session.all_solution_paths) > 0

        # Try matching the conclusion node
        concl_node = next(
            (n for n in nav.dag["nodes"] if n.get("type") == "conclusion" or n.get("id") == nav.dag.get("conclusion_node")),
            None,
        )
        if concl_node and concl_node.get("accept"):
            phrase = concl_node["accept"][0]
            res = nav.process_input(phrase)
            assert res.status == "FIRST_MATCH"
            assert res.matched_node["id"] == concl_node["id"]

        tested_count += 1

    assert tested_count >= 5
