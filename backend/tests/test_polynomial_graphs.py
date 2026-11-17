"""NCERT Class 10 Ex 2.2 (Polynomials): Q1 zeroes by either method + α + β = −b/a, αβ = c/a; Q2 k(x² − Sx + P).
Parts in any order, as in Real Numbers; every answer is checked by SymPy (engine/polynomials.py)."""
import re

import pytest
import sympy as sp
from fastapi.testclient import TestClient

from app.main import app
from app.graph_loader import get_graph
from app.engine import polynomials as P

client = TestClient(app)
Q1, Q2 = "g10-jemh102-ex-2-2-q1", "g10-jemh102-ex-2-2-q2"
Q1_INTRO = ["x² − 2x − 8, 4s² − 4s + 1, 6x² − 3 − 7x, 4u² + 8u, t² − 15, 3x² − x − 4",
            "find the zeroes and verify the relationship between zeroes and coefficients",
            "factorise to find the zeroes, then check the sum is -b/a and the product is c/a"]
Q2_INTRO = ["six pairs of sum and product", "a quadratic polynomial for each pair",
            "use x² − (sum)x + (product), put in the given numbers, and multiply by k to clear fractions"]
X2 = {"poly": "x**2 - 2*x - 8", "var": "x"}


def _steps(problem, lines):
    sid = client.post("/api/v1/sessions/start", json={"problem_id": problem}).json()["session_id"]
    return [client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": line}).json() for line in lines]


# ─── SymPy checks ─────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("line", ["x = 4, -2", "4 and −2", "x = 4 or x = −2", "x = (2 ± 6)/2", "−2, 4"])
def test_all_zeroes_in_any_form(line):
    assert P.zeroes_step(line, X2, []).get("done")


@pytest.mark.parametrize("spec,line", [
    ({"poly": "t**2 - 15", "var": "t"}, "t = ±√15"),
    ({"poly": "t**2 - 15", "var": "t"}, "√15, -√15"),
    ({"poly": "4*s**2 - 4*s + 1", "var": "s"}, "s = 1/2"),            # the same zero twice
    ({"poly": "6*x**2 - 7*x - 3", "var": "x"}, "x = 3/2, −1/3"),
    ({"poly": "4*u**2 + 8*u", "var": "u"}, "u = 0 or u = −2"),
])
def test_zeroes_with_roots_fractions_and_a_repeated_zero(spec, line):
    assert P.zeroes_step(line, spec, []).get("done")


def test_one_zero_is_kept_while_the_other_is_found():
    first = P.zeroes_step("x = 4", X2, [])
    assert first.get("found") and "other zero" in first["message"]
    assert P.zeroes_step("x = -2", X2, ["4"]).get("done")


@pytest.mark.parametrize("line,method", [
    ("x² − 2x − 8 = x² − 4x + 2x − 8", "m1"),                         # splitting the middle term
    ("x² − 2x − 8 = (x − 4)(x + 2)", "m1"),
    ("(x - 4)(x + 2) = 0", "m1"),
    ("= (x − 4)(x + 2)", "m1"),                                        # goes on from the polynomial
    ("D = b² − 4ac = (−2)² − 4(1)(−8) = 36", "m2"),                    # the quadratic formula
])
def test_working_of_either_method(line, method):
    step = P.zeroes_step(line, X2, [])
    assert step.get("working") and step["method"] == method


@pytest.mark.parametrize("line,message", [
    ("x = 3", "x = 3 is not a zero: p(3) = -5, not 0."),
    ("x + 4 = 0", "gives x = -4, but p(-4) = 16, not 0."),
    ("x² − 2x − 8 = (x − 4)(x − 2)", "(x − 4)(x − 2) expands to x² − 6x + 8, not x² − 2x − 8."),
    ("D = 30", "is 36, not 30."),
])
def test_wrong_working_is_explained(line, message):
    step = P.zeroes_step(line, X2, [])
    assert step.get("wrong") and message in step["message"]


def test_words_are_not_an_attempt():
    assert P.zeroes_step("i will factorise it", X2, []) is None


Q2I = {"sum": "1/4", "product": "-1", "var": "x", "sum_text": "1/4", "product_text": "−1"}


@pytest.mark.parametrize("line,ok", [
    ("4x² − x − 4", True), ("x² − (1/4)x − 1", True), ("k(x² − x/4 − 1)", True), ("p(x) = 4x^2 - x - 4", True),
    ("-8x² + 2x + 8", True),                                           # any multiple k ≠ 0
    ("x² + x/4 − 1", False), ("4x² − x + 4", False),
])
def test_a_quadratic_from_sum_and_product(line, ok):
    assert P.quadratic_step(line, Q2I)["ok"] is ok


def test_a_wrong_quadratic_is_told_its_own_sum_and_product():
    out = P.quadratic_step("x² + x/4 − 1", Q2I)
    assert "sum −b/a = -1/4" in out["message"] and "product c/a = -1" in out["message"]


@pytest.mark.parametrize("line,ok", [
    ("α + β = 4 + (−2) = 2 = −(−2)/1", True), ("2", True), ("−b/a = −(−2)/1 = 2", True),
    ("sum = 6", False), ("4 + (−2) = 6", False),
])
def test_checking_the_sum(line, ok):
    assert P.value_step(line, {"value": "2", "what": "the sum"})["ok"] is ok


SUM_I = {"value": "2", "value_text": "2", "what": "the sum of the zeroes", "rule": "−b/a", "work": "−(−2)/1",
         "a": "1", "b": "−2", "c": "−8"}


@pytest.mark.parametrize("line,ok,message", [
    ("4+(−2)=2,2/4=1/2 no both are not equal", False, "−b/a = −(−2)/1 = 2 here: a = 1, b = −2"),   # every claim
    ("4+(−2)=2 and -b/a = 2 so not equal", False, "Look again: both come to 2, so they are equal."),
    ("4 + (−2) = 2, −b/a = 2/1 = 2, both are equal", True, ""),
    ("sum = 3", False, "3 is not the sum of the zeroes."),
])
def test_every_claim_and_the_conclusion_are_checked(line, ok, message):
    out = P.value_step(line, SUM_I)
    assert out["ok"] is ok and message in out.get("message", "")


# ─── Through the API ────────────────────────────────────────────────────────────────────────────────────────
def test_q1_every_part_by_either_method_in_any_order():
    steps = _steps(Q1, Q1_INTRO + [
        "(v) D = b² − 4ac = 60", "t = ±√15", "0", "−15",                         # formula
        "(i) x² − 2x − 8 = (x − 4)(x + 2)", "x − 4 = 0", "x = −2", "2", "−8",    # factorisation, one zero at a time
        "(ii) s = 1/2", "1", "1/4",
        "(iii) x = (7 ± 11)/12", "7/6", "−1/2",
        "(iv) 4u(u + 2) = 0", "u = 0 or u = −2", "−2", "0",
        "(vi) x = 4/3, −1", "1/3", "−4/3",
        "sum of zeroes = −b/a and product = c/a"])
    assert steps[-1]["verdict"] == "CONCLUSION_RIGHT" and steps[-1]["completed"]
    assert all(s["verdict"] in ("ACCEPT", "WORKING") for s in steps[:-1])


def test_q1_a_part_label_up_to_vi():
    for label in ["(vi)", "vi)", "part vi", "(vi) 3x² − x − 4"]:
        assert _steps(Q1, Q1_INTRO + [label])[-1]["active_label"] == "(vi) Zeroes of 3x² − x − 4"


def test_q1_two_questions_per_part_sum_and_product_in_any_order():
    steps = _steps(Q1, Q1_INTRO + ["(i) x = 4, −2", "product = 15", "αβ = 4 × (−2) = −8 = −8/1", "2"])
    assert steps[-4]["active_label"] == "(i) Verify the Relationship"
    assert "(i) Verify the relationship between the zeroes and the coefficients." in steps[-4]["next_prompt"]
    assert steps[-3]["verdict"] == "WRONG_CLAIM" and steps[-2]["verdict"] == "WORKING"
    assert steps[-1]["verdict"] == "ACCEPT" and steps[-1]["active_label"] == "(ii) Zeroes of 4s² − 4s + 1"
    both = _steps(Q1, Q1_INTRO + ["(i) x = 4, −2", "4 + (−2) = 2 = −(−2)/1, 4 × (−2) = −8 = −8/1"])[-1]
    assert both["verdict"] == "ACCEPT" and both["active_label"] == "(ii) Zeroes of 4s² − 4s + 1"


def test_q1_hints_follow_the_method():
    zero = next(n for n in get_graph(Q1).nodes if n.id == "p1_zeroes")
    by_formula = _steps(Q1, Q1_INTRO + ["(i) D = 30"])[-1]
    by_factor = _steps(Q1, Q1_INTRO + ["(i) x² − 2x − 8 = (x − 4)(x − 2)"])[-1]
    assert by_formula["hint"] == zero.hints_by_method["m2"][0]
    assert by_factor["hint"] == zero.hints_by_method["m1"][0]


def test_q1_dont_know_a_zero_question_then_example():
    first, second, third = _steps(Q1, Q1_INTRO + ["(ii) i dont know what is a zero", "i dont know what is zeros",
                                                  "i dont know what are zeroes"])[-3:]
    assert first["verdict"] == "DONT_KNOW" and "What happens to the value" in first["feedback_message"]
    assert "Example: for x² − 5x + 6, put x = 2" in second["feedback_message"]
    assert "Example: for x² − 5x + 6, put x = 2" in third["feedback_message"]       # stays at the example
    assert first["hint"] is None and second["hint"] is None                          # the step's hints wait


def test_q1_cannot_verify_gets_three_hints():
    steps = _steps(Q1, Q1_INTRO + ["(i) x = 4, x = −2", "i dont know how to verify", "i dont know", "i dont know"])
    hints = [s["hint"] for s in steps[-3:]]
    assert "Do you notice any connection" in hints[0] and "Try expanding the factors" in hints[1]
    assert "−(−5)/1 = −b/a" in hints[2] and "6/1 = c/a" in hints[2]


def test_q2_any_order_any_multiple():
    steps = _steps(Q2, Q2_INTRO + ["(iii) x² + √5", "(i) 4x² − x − 4", "(iv) x² − x + 1", "(ii) 3x² − 3√2x + 1",
                                   "(v) k(x² + x/4 + 1/4)", "(vi) x² − 4x + 1", "x² − Sx + P"])
    assert all(s["verdict"] == "ACCEPT" for s in steps[3:-1]) and steps[-1]["verdict"] == "CONCLUSION_RIGHT"


@pytest.mark.parametrize("line,message", [
    ("(i) x² + x/4 − 1", "Your polynomial's zeroes have sum"),
    ("(vi) x^3 - 4x + 1", "That has degree 3"),
])
def test_q2_a_wrong_polynomial_is_explained(line, message):
    out = _steps(Q2, Q2_INTRO + [line])[-1]
    assert out["verdict"] == "WRONG_CLAIM" and message in out["feedback_message"]


# ─── Hints teach with other polynomials, and their worked examples are true ──────────────────────────────
def _teaching_hints(graph):
    for n in graph.nodes:
        yield from ((n.id, h) for h in n.hints[:-1])
        for hints in (getattr(n, "hints_by_method", None) or {}).values():
            yield from ((n.id, h) for h in hints[:-1])
        for c in n.concepts_required:
            yield from ((n.id, h) for h in c.hints)
        yield from ((n.id, k.question) for k in n.concept_hints)
        yield from ((n.id, m.response) for m in n.misconceptions)


def _polys(graph):
    out = []
    for n in graph.nodes:
        spec = getattr(n, "zeroes_of", None)
        if spec:
            out.append((spec["var"], sp.sympify(spec["poly"], locals={spec["var"]: sp.Symbol(spec["var"])})))
    return out


def test_q1_hints_never_use_the_questions_polynomials():
    graph = get_graph(Q1)
    for node_id, hint in _teaching_hints(graph):
        for piece in re.split(r"[=,:;]|\bso\b|\bgives?\b|\band\b", hint):
            for var, poly in _polys(graph):
                e = P.expr(piece, var)
                if e is not None and sp.Symbol(var) in e.free_symbols:
                    assert sp.simplify(e / poly).free_symbols, (node_id, hint)   # not the same polynomial


@pytest.mark.parametrize("pid", [Q1, Q2])
def test_every_worked_example_in_a_hint_expands_correctly(pid):
    checked = 0
    for node_id, hint in _teaching_hints(get_graph(pid)):
        for sentence in re.split(r"(?<=[.?])\s+|,\s*so\s+|\bgives?\b|\bthen\b|:\s*", hint):
            sides = [s for s in sentence.split("=")]
            exprs = [P.expr(s, "xy") for s in sides]
            if (len(sides) >= 2 and all(e is not None for e in exprs) and any(e.free_symbols for e in exprs)
                    and exprs[-1] != 0):                       # "(3y − 1)² = 0" is an equation, not an identity
                for a, b in zip(exprs, exprs[1:]):
                    checked += 1
                    assert sp.expand(a - b) == 0, (node_id, sentence)
    assert checked >= 3


def test_both_graphs_have_their_parts_and_both_methods_in_q1():
    q1, q2 = get_graph(Q1), get_graph(Q2)
    assert len(q1.graph_meta.parts) == 6 and len(q2.graph_meta.parts) == 6
    ids = {n.id for n in q1.nodes}
    for k in range(1, 7):
        assert {f"m1_p{k}", f"m2_p{k}", f"p{k}_zeroes", f"p{k}_verify"} <= ids


# ─── "What is given?": the words, or the question's own list (checked by SymPy) ─────────────────────────────
@pytest.mark.parametrize("problem,line,verdict,message", [
    (Q1, "(i) x² – 2x – 8 (ii) 4s² – 4s + 1 (iii) 6x² – 3 – 7x (iv) 4u² + 8u (v) t² – 15 (vi) 3x² – x – 4",
     "ACCEPT", ""),                                                     # the student's own answer
    (Q1, "x^2 - 2x - 8, 4s^2 - 4s + 1, 6x^2 - 7x - 3, 4u^2 + 8u, t^2 - 15, 3x^2 - x - 4", "ACCEPT", ""),
    (Q1, "six quadratic polynomials", "ACCEPT", ""),
    (Q1, "(i) x² – 2x – 8 (ii) 4s² – 4s + 1 (iii) 6x² – 3 – 7x (iv) 4u² + 8u (v) t² – 15", "WRONG_CLAIM",
     "You have 5 of the 6 polynomials. Which one is missing?"),
    (Q1, "(i) x² – 2x + 8 (ii) 4s² – 4s + 1", "WRONG_CLAIM", "x² – 2x + 8 is not one of the polynomials"),
    (Q2, "(i) 1/4, −1 (ii) √2, 1/3 (iii) 0, √5 (iv) 1, 1 (v) −1/4, 1/4 (vi) 4, 1", "ACCEPT", ""),
    (Q2, "1/4, -1, √2, 1/3, 0, √5, 1, 1, -1/4, 1/4, 4, 1", "ACCEPT", ""),
    (Q2, "six pairs of sum and product", "ACCEPT", ""),
    (Q2, "(i) 1/4, −1 (ii) √2, 1/3 (iii) 0, √5", "WRONG_CLAIM", "You have 3 of the 6 pairs."),
    (Q2, "(i) 1/4, 1", "WRONG_CLAIM", "(1/4, 1) is not one of the pairs in the question."),
])
def test_what_is_given_accepts_the_questions_list(problem, line, verdict, message):
    out = _steps(problem, [line])[-1]
    assert out["verdict"] == verdict and message in out["feedback_message"]


def test_q1_all_working_at_once_finds_the_zeroes():
    work = ("x² – 2x – 8 = x² − 4x + 2x − 8 = x(x − 4) + 2(x − 4) = (x − 4)(x + 2)\n"
            "(x − 4) = 0 and (x + 2) = 0\nx = 4 and x = −2")
    out = _steps(Q1, Q1_INTRO[:2] + [work])[-1]
    assert out["verdict"] == "ACCEPT" and out["active_label"] == "(i) Verify the Relationship"
    wrong = _steps(Q1, Q1_INTRO + ["(i) x² − 2x − 8 = (x − 4)(x + 2)\nx = 4 and x = 2"])[-1]
    assert wrong["verdict"] == "WRONG_CLAIM"
    one_line = ("(i) x^2-2x-8 =x^2-4x+2x-8 =x(x-4)+2(x-4) =(x-4)(x+2) =(x-4)=0 and (x+2)=0 x=4 and x=-2 "
                "zeros are 4,-2")
    assert _steps(Q1, Q1_INTRO + [one_line])[-1]["active_label"] == "(i) Verify the Relationship"


@pytest.mark.parametrize("line", ["x^2-2x-8 = (x+2)(x-4); so x=-2,4", "(x+2)(x-4)=0 ⇒ x=-2,4",
                                  "x² − 2x − 8 = (x + 2)(x − 4), hence x = −2, 4"])
def test_working_then_zeroes_on_one_line(line):
    assert P.zeroes_step(line, {"poly": "x**2 - 2*x - 8", "var": "x"}, []).get("done")
