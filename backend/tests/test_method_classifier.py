import pytest

from app.graph_loader import get_graph
from app.engine.method_classifier import classify_graph

# Ported from test_my_jev.js.
# [problem, student work (lines separated by \n), expected: method id | 'uncertain' | 'off_graph']
CASES = [
    ("g08-hegp206-age-q7", "mother = 5x", "method1"),
    ("g08-hegp206-age-q7", "daughter = x", "method1"),
    ("g08-hegp206-age-q7", "5x + 6 = 3(x + 6)", "method1"),
    ("g08-hegp206-age-q7", "5x+6=3x+18", "method1"),
    ("g08-hegp206-age-q7", "mother = x", "method2"),
    ("g08-hegp206-age-q7", "daughter = x/5", "method2"),
    ("g08-hegp206-age-q7", "daughter = 0.2x", "method2"),
    ("g08-hegp206-age-q7", "x + 6 = 3x/5 + 18", "method2"),
    ("g08-hegp206-age-q7", "5 - 1 = 4", "method3"),
    ("g08-hegp206-age-q7", "ratio method", "method3"),
    ("g08-hegp206-age-q7", "1 unit = 6 years", "method3"),
    ("g08-hegp206-age-q7", "x + 6", "uncertain"),                   # shared by Methods 1 and 2
    ("g08-hegp206-age-q7", "x + 6\n5x + 6 = 3(x + 6)", "method1"),  # shared line, then a clear one
    ("g08-hegp206-age-q7", "I like pizza", "off_graph"),

    ("g08-lin-ex003", "3x - 6 + 5 = 2x + 4", "uncertain"),          # first step is shared
    ("g08-lin-ex003", "3x - 6 + 5 = 2x + 4\n3x - 2x = 4 + 1", "m1_transpose"),
    ("g08-lin-ex003", "3x - 1 - 2x = 2x + 4 - 2x", "m2_balance"),
    ("g08-lin-ex003", "subtract 2x from both sides", "m2_balance"),
    ("g08-lin-ex003", "try x = 3", "m3_trial"),

    # (x-2)(x-3) is written in BOTH Factoring (m1_s3) and Trial (m6_s3) in the graph → truly shared
    ("g10-quad-ex001", "(x - 2)(x - 3) = 0", "uncertain"),
    ("g10-quad-ex001", "x^2 - 2x - 3x + 6\n(x - 2)(x - 3) = 0", "m1_factor"),
    ("g10-quad-ex001", "x^2 - 2x - 3x + 6", "m1_factor"),
    ("g10-quad-ex001", "D = b^2 - 4ac", "m2_formula"),
    ("g10-quad-ex001", "complete the square", "m3_square"),
    ("g10-quad-ex001", "x^2 - 5x + 25/4 = 1/4", "m3_square"),
    ("g10-quad-ex001", "sum of roots = 5", "m5_vieta"),
    ("g10-quad-ex001", "f(2) = 0", "m6_trial"),
]

# Lines that are NOT written in any graph (maths matching must do the work)
UNSEEN = [
    ("g08-hegp206-age-q7", "5y + 6 = 3(y + 6)", "method1"),         # different letter
    ("g08-hegp206-age-q7", "5x + 6 = 3*x + 18", "method1"),
    ("g08-hegp206-age-q7", "x + 6 = 0.6x + 18", "method2"),
    ("g08-hegp206-age-q7", "5(x + 6) = 3x + 90", "method2"),
    ("g08-lin-ex003", "3(x-2) + 5 - 2x = 4", "m2_balance"),          # 2x subtracted from both sides = balancing
]


def _outcome(result):
    return result["methodId"] if result["status"] == "selected" else result["status"]


@pytest.mark.parametrize("problem,work,expected", CASES + UNSEEN)
def test_classifies_method(problem, work, expected):
    assert _outcome(classify_graph(get_graph(problem), work)) == expected


@pytest.mark.parametrize("problem,work,expected", CASES + UNSEEN)
def test_probabilities_cover_every_graph_method(problem, work, expected):
    graph = get_graph(problem)
    probs = classify_graph(graph, work)["probabilities"]
    assert set(probs) == {n.id for n in graph.nodes if n.type == "method"}
    assert sum(probs.values()) == pytest.approx(1, abs=0.01)


def test_selected_result_shape_matches_jev():
    # values taken from my_jev.js on the same graph
    result = classify_graph(get_graph("g08-hegp206-age-q7"), "5x + 6 = 3(x + 6)")
    assert result == {
        "status": "selected",
        "methodKey": "method1",
        "methodId": "method1",
        "confidence": 0.992,
        "probabilities": {"method1": 0.992, "method2": 0.008, "method3": 0.0},
        "off_graph": False,
    }


def test_shared_line_splits_probability_evenly():
    result = classify_graph(get_graph("g08-lin-ex003"), "3x - 6 + 5 = 2x + 4")
    assert result["probabilities"]["m1_transpose"] == result["probabilities"]["m2_balance"] == 0.5
    assert result["confidence"] == 0.5


def test_off_graph_confidence_is_one_minus_best_evidence():
    result = classify_graph(get_graph("g08-hegp206-age-q7"), "I like pizza")
    assert result["off_graph"] is True
    assert 0.65 < result["confidence"] <= 1
