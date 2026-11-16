import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.graph_loader import get_graph
from app.engine.method_classifier import classify_graph

client = TestClient(app)

Q6, Q7 = "g10-jemh110-ex-10-2-q6", "g10-jemh110-ex-10-2-q7"

# [problem, student work (lines separated by \n), expected: method id | 'uncertain' | 'off_graph']
CASES = [
    (Q6, "r^2 + 4^2 = 5^2", "uncertain"),                                   # shared by Pythagoras and 3-4-5
    (Q6, "r^2 + 4^2 = 5^2\nr^2 = 5^2 - 4^2", "m1_pythagoras"),
    (Q6, "r^2 = (5 - 4)(5 + 4)", "m1_pythagoras"),                             # difference of squares = Pythagoras
    (Q6, "r^2 + 4^2 = 5^2\n3^2 + 4^2 = 5^2", "m2_triple"),
    (Q6, "pythagorean triple", "m2_triple"),
    (Q6, "cos θ = 4/5", "m3_trig"),
    (Q6, "by trigonometry", "m3_trig"),
    (Q6, "P = (0, 0), A = (4, 0), O = (0, r)", "m4_coordinate"),
    (Q6, "sqrt(4^2 + r^2) = 5", "m4_coordinate"),
    (Q6, "I like pizza", "off_graph"),
    (Q7, "x^2 + 3^2 = 5^2\nx^2 = 5^2 - 3^2", "uncertain"),
    (Q7, "x^2 = 25 - 9", "m1_subtract"),
    (Q7, "x^2 = (5 - 3)(5 + 3)", "m2_diff_squares"),
]


@pytest.mark.parametrize("problem,work,expected", CASES)
def test_jev_identifies_circles_methods(problem, work, expected):
    result = classify_graph(get_graph(problem), work)
    assert (result["methodId"] if result["status"] == "selected" else result["status"]) == expected


def test_circles_graphs_use_jev():
    for pid in (Q6, Q7):
        meta = get_graph(pid).graph_meta
        assert meta.use_jev is True
        assert meta.sympy_can_finish is False
        assert client.post("/api/v1/sessions/start", json={"problem_id": pid}).json()["use_jev"] is True


def test_sympy_checks_lines_written_with_r():
    # graph_meta.variable = "r": SymPy checks r as its x, and reports back in r
    ok = client.post("/api/v1/jev/classify", json={"problem_id": Q6, "lines": ["r^2 + 4^2 = 5^2"]}).json()
    assert ok["status"] == "uncertain"
    assert ok["validation"]["is_valid"] is True
    assert any(l["status"] == "valid" for l in ok["validation"]["lines"])

    bad = client.post("/api/v1/jev/classify", json={"problem_id": Q6, "lines": ["r^2 = 10"]}).json()
    assert bad["status"] == "fix_mistake"
    assert '"r² = 10"' in bad["feedback"]
    assert "x" not in bad["validation"]["errors"][0]["statement"]



def test_q6_has_only_ncert_methods():
    labels = [n.label for n in get_graph(Q6).nodes if n.type == "method"]
    assert labels == ["Method 1: Pythagoras' Theorem", "Method 2: 3-4-5 Triangle (Pythagorean Triple)",
                      "Method 3: Trigonometry", "Method 4: Coordinate Geometry"]
    assert not any("secant" in l.lower() for l in labels)   # tangent-secant theorem is not in the NCERT book


@pytest.mark.parametrize("lines", [
    ["cos θ = 4/5", "sin θ = 3/5", "sin θ = r/5"],        # SymPy has no trigonometry
    ["P = (0, 0), A = (4, 0), O = (0, r)"],               # points used to crash the validator
])
def test_lines_sympy_cannot_read_are_unchecked_not_wrong(lines):
    data = client.post("/api/v1/jev/classify", json={"problem_id": Q6, "lines": lines}).json()
    assert data["status"] != "fix_mistake"
    assert data["validation"]["is_valid"] is True
    assert all(l["status"] == "unchecked" for l in data["validation"]["lines"])


def test_sympy_still_catches_mistakes_in_new_methods():
    for wrong in ("sqrt(4^2 + r^2) = 6", "r = 5 × 4/5 = 4"):
        data = client.post("/api/v1/jev/classify", json={"problem_id": Q6, "lines": [wrong]}).json()
        assert data["status"] == "fix_mistake", wrong

PATHS = [
    (Q6, ["r^2 + 4^2 = 5^2", "r^2 = 5^2 - 4^2"], "m1_pythagoras", ["r^2 = 25 - 16 = 9", "r = 3", "radius = 3 cm"]),
    (Q6, ["r^2 + 4^2 = 5^2", "r^2 = 5^2 - 4^2"], "m1_pythagoras", ["r^2 = (5 - 4)(5 + 4)", "r = 3", "3 cm"]),
    (Q6, ["r^2 + 4^2 = 5^2", "3^2 + 4^2 = 5^2"], "m2_triple", ["r = 3", "the radius is 3 cm"]),
    (Q6, ["cos θ = 4/5"], "m3_trig", ["sin θ = √(1 - 16/25) = 3/5", "sin θ = r/5", "r = 3", "the radius is 3 cm"]),
    (Q6, ["P = (0, 0), A = (4, 0), O = (0, r)"], "m4_coordinate",
     ["sqrt(4^2 + r^2) = 5", "16 + r^2 = 25", "r^2 = 9", "r = 3", "radius = 3 cm"]),
    # skipping r² = 9 and writing r = 3 straight away must not be called a mistake
    (Q6, ["r^2 + 4^2 = 5^2", "r^2 = 5^2 - 4^2"], "m1_pythagoras", ["r = 3", "the radius is 3 cm"]),
    (Q6, ["P = (0, 0), A = (4, 0), O = (0, r)"], "m4_coordinate", ["sqrt(4^2 + r^2) = 5", "16 + r^2 = 25", "r = 3", "radius = 3 cm"]),
    (Q7, ["x^2 + 3^2 = 5^2", "x^2 = 5^2 - 3^2", "x^2 = 25 - 9 = 16"], "m1_subtract", ["x = 4", "AB = 2 × 4 = 8", "the chord is 8 cm"]),
    (Q7, ["x^2 + 3^2 = 5^2", "x^2 = 5^2 - 3^2", "x^2 = (5 - 3)(5 + 3)"], "m2_diff_squares", ["x = 4", "AB = 8", "chord = 8 cm"]),
]


@pytest.mark.parametrize("problem,jev_lines,method,rest", PATHS)
def test_full_jev_flow_solves_problem(problem, jev_lines, method, rest):
    """Same sequence as the React app: classify all lines, lock the method, replay, then normal steps."""
    sid = client.post("/api/v1/sessions/start", json={"problem_id": problem}).json()["session_id"]
    check = client.post("/api/v1/jev/classify", json={"problem_id": problem, "lines": jev_lines}).json()
    assert check["method"]["methodId"] == method

    assert client.post(f"/api/v1/sessions/{sid}/method", json={"method_id": method}).status_code == 200
    for line in jev_lines:
        step = client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": line}).json()
        assert step["verdict"] == "ACCEPT", line
    for line in rest:
        step = client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": line}).json()
        assert step["verdict"] in ("ACCEPT", "CONCLUSION_RIGHT"), line
    assert step["completed"] is True
