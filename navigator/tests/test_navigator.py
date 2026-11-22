"""Comprehensive Standalone Test Suite for Ainstein Navigator.

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

from navigator.graph_loader import (
    get_all_solution_paths,
    load_dag,
)
from navigator.navigator import Navigator
from navigator.normalizer import normalize, to_token_set
from navigator.path_finder import evaluate_transition
from navigator.ranker import DEFAULT_THRESHOLD, resolve_with_details, resolve_with_score
from navigator.scorer import jaccard_similarity, score_phrase, weighted_jaccard


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
# 2. Scorer Tests (Deterministic Scorer)
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


def test_ranker_tie_detection_exact_and_fuzzy():
    # Test 1: Multiple nodes with identical exact match phrase
    nodes_exact = [
        {"id": "step_a", "label": "Step A", "accept": ["15"]},
        {"id": "step_b", "label": "Step B", "accept": ["15"]},
        {"id": "step_c", "label": "Step C", "accept": ["15"]},
    ]
    winner, score, mtype, phrase, tied = resolve_with_details("15", nodes_exact)
    assert len(tied) == 3
    assert [c["node"]["id"] for c in tied] == ["step_a", "step_b", "step_c"]
    assert winner is not None
    assert winner["id"] == "step_a"  # Stable order tie-break
    assert score == 1.0
    assert "TIE_BROKEN_BY_SPECIFICITY" in mtype

    # Test 2: Unique match has empty tied list
    nodes_unique = [
        {"id": "step_1", "accept": ["prime factors"]},
        {"id": "step_2", "accept": ["unrelated"]},
    ]
    winner2, score2, mtype2, phrase2, tied2 = resolve_with_details("prime factors", nodes_unique)
    assert winner2 is not None
    assert winner2["id"] == "step_1"
    assert len(tied2) == 0


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

from navigator.graph_loader import (
    build_adjacency,
    get_dag_corpus,
    get_node_by_id,
    is_optional_node,
)


def test_is_optional_node_logic():
    """Test is_optional_node() to ensure mandatory vs optional nodes are correctly flagged.

    - Nodes with optional=True can be skipped during problem solving.
    - Nodes with optional=False are mandatory and cannot be skipped.
    - Missing or non-boolean optional values must default to False (mandatory).
    """
    # Case 1: Explicitly optional node (can be skipped)
    optional_node = {"id": "hint_step", "optional": True}
    assert is_optional_node(optional_node) is True

    # Case 2: Explicitly mandatory node (cannot be skipped)
    mandatory_node = {"id": "solve_equation", "optional": False}
    assert is_optional_node(mandatory_node) is False

    # Case 3: Node without 'optional' key -> must default to False (mandatory)
    node_without_key = {"id": "step_default"}
    assert is_optional_node(node_without_key) is False

    # Case 4: Node with non-boolean 'optional' value (e.g. string or None) -> must default to False
    invalid_val_node = {"id": "step_bad", "optional": "yes"}
    assert is_optional_node(invalid_val_node) is False


def test_build_adjacency_directed_graph():
    """Test build_adjacency() constructs correct directed graph representations.

    Verifies:
    1. Directed edges map source -> [destinations].
    2. Branching out-degree is captured (one node pointing to multiple children).
    3. Isolated nodes (no incoming or outgoing edges) are still indexed with [].
    """
    sample_dag = {
        "nodes": [
            {"id": "start"},
            {"id": "branch_a"},
            {"id": "branch_b"},
            {"id": "conclusion"},
            {"id": "isolated_node"},
        ],
        "edges": [
            {"from": "start", "to": "branch_a"},
            {"from": "start", "to": "branch_b"},
            {"from": "branch_a", "to": "conclusion"},
            {"from": "branch_b", "to": "conclusion"},
        ],
    }

    adj = build_adjacency(sample_dag)

    # 'start' should branch into both 'branch_a' and 'branch_b'
    assert adj["start"] == ["branch_a", "branch_b"]

    # Both branches should converge at 'conclusion'
    assert adj["branch_a"] == ["conclusion"]
    assert adj["branch_b"] == ["conclusion"]

    # 'conclusion' has no outgoing edges
    assert adj["conclusion"] == []

    # 'isolated_node' exists in the node list but has no edges -> empty list
    assert adj["isolated_node"] == []


def test_get_all_solution_paths_branching_and_cycles():
    """Test get_all_solution_paths() enumerates all valid directed solution paths.

    Verifies:
    1. Linear path enumeration.
    2. Multi-path branching (e.g., Method 1 vs Method 2).
    3. Cycle guard: DFS does not loop infinitely if an edge points backwards.
    """
    # Branching graph with 2 distinct valid paths to conclusion
    branching_dag = {
        "start_node": "start",
        "conclusion_node": "conclusion",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "m1", "type": "method"},
            {"id": "m2", "type": "method"},
            {"id": "conclusion", "type": "conclusion"},
        ],
        "edges": [
            {"from": "start", "to": "m1"},
            {"from": "start", "to": "m2"},
            {"from": "m1", "to": "conclusion"},
            {"from": "m2", "to": "conclusion"},
        ],
    }

    paths = get_all_solution_paths(branching_dag)

    # Expect exactly 2 paths
    assert len(paths) == 2
    assert ["start", "m1", "conclusion"] in paths
    assert ["start", "m2", "conclusion"] in paths

    # Cycle test: Add a back-edge from m1 back to start (should be safely ignored by cycle guard)
    branching_dag["edges"].append({"from": "m1", "to": "start"})
    safe_paths = get_all_solution_paths(branching_dag)
    assert len(safe_paths) == 2


def test_load_dag_ingestion_and_normalization():
    """Test load_dag() correctly normalizes fields, creates precomputations, and isolates memory.

    Verifies:
    1. Deep copy isolation: Modifying the output DAG does not mutate the source dictionary.
    2. Field normalization: Nodes without 'accept' get [], and 'optional' is normalized to boolean.
    3. In-memory precomputations: 'node_map' and 'all_solution_paths' are created automatically.
    """
    source_dict = {
        "start_node": "A",
        "conclusion_node": "C",
        "nodes": [
            {"id": "A"},                            # Missing 'accept' and 'optional'
            {"id": "B", "optional": False},         # Explicitly mandatory
            {"id": "C", "optional": True, "accept": ["done"]},  # Explicitly optional
        ],
        "edges": [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
        ],
    }

    # Load and normalize the DAG
    dag = load_dag(source_dict)

    # 1. Verify deep copy memory isolation: mutating loaded dag should not affect source_dict
    dag["nodes"][0]["accept"].append("mutated_phrase")
    assert "accept" not in source_dict["nodes"][0], "Mutating dag should not alter original dictionary!"

    # 2. Verify normalization on node A
    node_a = dag["nodes"][0]
    assert node_a["optional"] is False  # Defaulted to mandatory
    assert "mutated_phrase" in node_a["accept"]

    # 3. Verify precomputations attached by load_dag()
    assert "node_map" in dag
    assert isinstance(dag["node_map"], dict)
    assert "all_solution_paths" in dag
    assert dag["all_solution_paths"] == [["A", "B", "C"]]


def test_get_node_by_id_o1_lookup():
    """Test get_node_by_id() retrieves nodes by ID in O(1) time using node_map.

    Verifies:
    1. Correct node dictionary returned for valid node IDs.
    2. Returns None for nonexistent node IDs without raising KeyError.
    3. Gracefully falls back to linear scan if node_map is absent.
    """
    sample_dag = {
        "start_node": "node_1",
        "conclusion_node": "node_2",
        "nodes": [
            {"id": "node_1", "label": "First Step"},
            {"id": "node_2", "label": "Final Step"},
        ],
        "edges": [{"from": "node_1", "to": "node_2"}],
    }
    dag = load_dag(sample_dag)

    # Fast O(1) lookup
    n1 = get_node_by_id(dag, "node_1")
    assert n1 is not None
    assert n1["id"] == "node_1"
    assert n1["label"] == "First Step"

    # Lookup non-existent node
    n_missing = get_node_by_id(dag, "ghost_node")
    assert n_missing is None

    # Fallback lookup: Even if node_map is removed, it still resolves via linear search
    del dag["node_map"]
    fallback_n2 = get_node_by_id(dag, "node_2")
    assert fallback_n2 is not None and fallback_n2["id"] == "node_2"


def test_load_dag_validation_failures():
    """Test fail-fast validation in load_dag() when presented with malformed or invalid DAGs.

    In a backend service, corrupted DAG files must fail immediately during load_dag()
    rather than causing silent logic failures mid-session.
    """
    # 1. Non-existent file path -> FileNotFoundError
    with pytest.raises(FileNotFoundError):
        load_dag("non_existent_directory/fake_graph.json")

    # 2. Invalid source type -> TypeError
    with pytest.raises(TypeError):
        load_dag(12345)  # Integers are not valid DAG sources

    # 3. Missing or empty 'nodes' list -> ValueError
    with pytest.raises(ValueError, match="non-empty 'nodes' list"):
        load_dag({"nodes": [], "edges": []})

    # 4. Duplicate node IDs -> ValueError
    with pytest.raises(ValueError, match="duplicate node ID"):
        load_dag({
            "start_node": "A",
            "conclusion_node": "A",
            "nodes": [{"id": "A"}, {"id": "A"}],
            "edges": [],
        })

    # 5. Missing node ID on a node -> ValueError
    with pytest.raises(ValueError, match="must have a non-empty 'id'"):
        load_dag({
            "nodes": [{"label": "Unnamed node without ID"}],
            "edges": [],
        })

    # 6. Dangling edge (source or target node does not exist) -> ValueError
    with pytest.raises(ValueError, match="Dangling edge"):
        load_dag({
            "start_node": "A",
            "conclusion_node": "B",
            "nodes": [{"id": "A"}, {"id": "B"}],
            "edges": [{"from": "A", "to": "GHOST_NODE"}],
        })

    # 7. Disconnected graph (no path from start to conclusion) -> ValueError
    with pytest.raises(ValueError, match="No directed path found"):
        load_dag({
            "start_node": "A",
            "conclusion_node": "B",
            "nodes": [{"id": "A"}, {"id": "B"}],
            "edges": [],  # No edge connects A to B
        })


def test_load_dag_from_disk_bundled_file():
    """Test loading a real solution DAG JSON file from disk.

    Verifies that real problem DAGs stored in the repository parse,
    validate, and precompute successfully without errors.
    """
    iron_pole_path = Path(__file__).resolve().parent / "graphs" / "iron_pole_mass.json"
    assert iron_pole_path.exists(), f"Expected test graph at: {iron_pole_path}"

    dag = load_dag(iron_pole_path)

    # Verify structural properties of real graph
    assert dag["start_node"] == "start"
    assert dag["conclusion_node"] == "conclusion"
    assert len(dag["nodes"]) == 14
    assert len(dag["edges"]) == 14

    # Verify O(1) node_map was built
    assert "start" in dag["node_map"]
    assert "conclusion" in dag["node_map"]

    # Verify multiple solution paths were found
    assert len(dag["all_solution_paths"]) == 2


def test_get_dag_corpus_text_extraction():
    """Test get_dag_corpus() aggregates all textual elements from the DAG.

    Verifies extraction of problem statement, descriptions, prompts, labels, and accept phrases.
    """
    sample_dag = {
        "graph_meta": {
            "problem_text": "Find the mass of an iron pole.",
            "description": "NCERT Class 10 Surface Area and Volumes",
        },
        "nodes": [
            {
                "id": "step1",
                "label": "Volume calculation",
                "description": "Calculate cylinder volume",
                "prompt": "What is the formula for volume?",
                "accept": ["pi r squared h", "volume formula"],
            }
        ],
    }

    corpus = get_dag_corpus(sample_dag)

    # Check that all relevant textual fields were collected
    assert "Find the mass of an iron pole." in corpus
    assert "NCERT Class 10 Surface Area and Volumes" in corpus
    assert "Volume calculation" in corpus
    assert "Calculate cylinder volume" in corpus
    assert "What is the formula for volume?" in corpus
    assert "pi r squared h" in corpus
    assert "volume formula" in corpus


# ===========================================================================
# 5. Path Reachability & Step Jump Tests
# ===========================================================================

def test_step_jump_detected_on_mandatory_node():
    sample_dag = {
        "start_node": "start",
        "conclusion_node": "conclusion",
        "nodes": [
            {"id": "start", "optional": True, "accept": ["start"]},
            {"id": "step1", "optional": False, "label": "Key Step 1", "prompt": "Do step 1", "accept": ["step 1"]},
            {"id": "step2", "optional": True, "label": "Step 2", "accept": ["step 2"]},
            {"id": "conclusion", "optional": False, "accept": ["done"]},
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

    # 2. Skip step1 (optional=False / mandatory) directly to step2
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


def test_step_jump_detected_when_node_lacks_optional_field():
    """Verify that nodes without any 'optional' key are treated strictly as mandatory.

    If an author creates a DAG without specifying 'optional', jumping over that
    intermediate node must trigger a STEP_JUMP violation and not be skipped.
    """
    sample_dag = {
        "start_node": "start",
        "conclusion_node": "conclusion",
        "nodes": [
            {"id": "start", "accept": ["start"]},
            # Note: intermediate node has NO 'optional' key at all!
            {"id": "step_no_optional", "label": "Implicitly Mandatory Step", "accept": ["do intermediate"]},
            {"id": "conclusion", "accept": ["done"]},
        ],
        "edges": [
            {"from": "start", "to": "step_no_optional"},
            {"from": "step_no_optional", "to": "conclusion"},
        ],
    }
    nav = Navigator(sample_dag, threshold=0.1)

    # 1. Ingestion check: dag['nodes'][1]['optional'] must be normalized to False (mandatory)
    assert nav.dag["nodes"][1]["optional"] is False

    # 2. Start session
    r1 = nav.process_input("start")
    assert r1.status == "FIRST_MATCH"

    # 3. Try jumping directly to conclusion, skipping 'step_no_optional'
    r2 = nav.process_input("done")
    assert r2.status == "STEP_JUMP"
    assert "STEP JUMP DETECTED" in r2.message
    assert len(r2.skipped_nodes) == 1
    assert r2.skipped_nodes[0]["id"] == "step_no_optional"
    assert r2.skipped_nodes[0]["optional"] is False
    # Pointer must remain at start
    assert nav.current_node["id"] == "start"


def test_invalid_path_backward_or_unreachable():
    sample_dag = {
        "start_node": "start",
        "conclusion_node": "conclusion",
        "nodes": [
            {"id": "start", "optional": True, "accept": ["start"]},
            {"id": "pathA_1", "optional": False, "accept": ["method a"]},
            {"id": "pathB_1", "optional": False, "accept": ["method b"]},
            {"id": "conclusion", "optional": False, "accept": ["conclusion"]},
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
            {"id": "start", "optional": True, "accept": ["start"]},
            {"id": "middle", "optional": False, "accept": ["middle node"]},
            {"id": "conclusion", "optional": False, "accept": ["end node"]},
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


def test_navigator_on_bundled_cbrt_graph():
    graph_path = Path(__file__).resolve().parent / "graphs" / "cube_root_3375.json"
    assert graph_path.exists(), f"Bundled graph missing at {graph_path}"

    nav = Navigator(str(graph_path), threshold=0.5)
    assert nav.dag["start_node"] == "start"
    assert nav.dag["conclusion_node"] == "conclusion"
    assert len(nav.session.all_solution_paths) == 2

    # Traversal step 1: identify given
    r1 = nav.process_input("3375")
    assert r1.status == "FIRST_MATCH"
    assert nav.current_node["id"] == "given_extraction"

    # Traversal step 2: identify goal
    r2 = nav.process_input("cube root of 3375")
    assert r2.status == "ADVANCED"
    assert nav.current_node["id"] == "goal_extraction"

    # Traversal step 3: select method 1
    r3 = nav.process_input("prime factorisation")
    assert r3.status == "ADVANCED"
    assert nav.current_node["id"] == "method1"

    # Active paths narrowed to method 1 only
    assert len(nav.session.active_solution_paths) == 1
    assert "method1" in nav.session.active_solution_paths[0]


def test_navigator_on_bundled_iron_pole_graph():
    graph_path = Path(__file__).resolve().parent / "graphs" / "iron_pole_mass.json"
    assert graph_path.exists()

    nav = Navigator(str(graph_path), threshold=0.5)
    assert len(nav.dag.get("nodes", [])) == 14
    assert len(nav.session.all_solution_paths) == 2

    # Step 1: given extraction
    r1 = nav.process_input("220 cm, 24 cm, 60 cm, 8 cm and 8 g")
    assert r1.status == "FIRST_MATCH"
    assert nav.current_node["id"] == "given_extraction"

    # Step 2: goal extraction
    r2 = nav.process_input("mass of the iron pole")
    assert r2.status == "ADVANCED"
    assert nav.current_node["id"] == "goal_extraction"

    # Step 3: Test STEP_JUMP over mandatory node!
    # m1_s3, method_choice, m1_add_volumes are mandatory (optional=False).
    # If student jumps directly from goal_extraction to m1_s4 (Mass of the Pole):
    r3 = nav.process_input("892262.4 g")
    assert r3.status == "STEP_JUMP"
    assert "STEP JUMP DETECTED" in r3.message
    assert any(n["id"] == "m1_s3" for n in r3.skipped_nodes)
    assert nav.current_node["id"] == "goal_extraction"


