"""NCERT Class 10 Ex 3.3 Q2 (ii), Nuri and Sonu: form, solve (elimination or substitution), verify (Qwen off)."""
import os

os.environ["PLAN_LLM"] = "off"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.engine import linear_pair as L  # noqa: E402
from app.graph_loader import get_graph, load_all_graphs  # noqa: E402

load_all_graphs(force_reload=True)
client = TestClient(app)
PID = "g10-jemh103-ex-3-3-q2-ii"
INTRO = ["5 years ago Nuri was 3 times Sonu, 10 years later Nuri will be twice Sonu", "their present ages",
         "let the ages be x and y, form two equations and solve by elimination"]
SPEC = get_graph(PID).nodes[[n.id for n in get_graph(PID).nodes].index("p1_form")].pair_form


def _steps(lines):
    sid = client.post("/api/v1/sessions/start", json={"problem_id": PID}).json()["session_id"]
    return [client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": line}).json() for line in lines]


@pytest.mark.parametrize("line,done", [
    ("x − 5 = 3(y − 5) and x + 10 = 2(y + 10)", True), ("x − 3y = −10\nx − 2y = 10", True),
    ("n − 5 = 3(s − 5); n + 10 = 2(s + 10)", True), ("Nuri − 5 = 3(Sonu − 5), Nuri + 10 = 2(Sonu + 10)", True),
    ("2x − 6y = −20", False),
])
def test_forming_the_equations(line, done):
    r = L.form_step(line, SPEC, [])
    assert bool(r.get("done")) is done and not r.get("wrong")


@pytest.mark.parametrize("line", ["x + 5 = 3(y + 5)", "x − 5 = 3y − 5", "x − 5 = 2(y − 5)"])
def test_a_wrong_equation_names_its_sentence(line):
    message = L.form_step(line, SPEC, [])["message"]
    assert "does not say" in message or "for their ages today" in message   # x − 5 = 3y − 5 is x = 3y


@pytest.mark.parametrize("line,kind", [
    ("(x − 3y) − (x − 2y) = −10 − 10", "working"), ("−y = −20", "working"), ("y = 20", "found"),
    ("x = 3y − 10", "working"), ("(3y − 10) − 2y = 10", "working"), ("y = 20, x = 50", "done"),
    ("x = 50 and y = 20", "done"), ("−y = 0", "wrong"), ("x = 40", "wrong"),
])
def test_solving_steps(line, kind):
    assert L.solve_step(line, SPEC, []).get(kind)


def test_methods_are_named():
    assert L.solve_step("(x − 3y) − (x − 2y) = −20", SPEC, [])["method"] == "m1"
    assert L.solve_step("x = 3y − 10", SPEC, [])["method"] == "m2"


@pytest.mark.parametrize("line,kind", [
    ("45 = 3 × 15 and 60 = 2 × 30", "done"), ("50 − 5 = 3(20 − 5), 50 + 10 = 2(20 + 10)", "done"),
    ("45 = 3 × 15", "found"), ("45 = 2 × 15", "wrong"),
])
def test_verify(line, kind):
    assert L.verify_step(line, SPEC, []).get(kind)


def test_full_flow_by_elimination():
    steps = _steps(INTRO + ["x − 5 = 3(y − 5)", "x + 10 = 2(y + 10)", "(x − 3y) − (x − 2y) = −10 − 10",
                            "−y = −20 so y = 20", "x − 2(20) = 10 so x = 50", "45 = 3 × 15", "60 = 2 × 30",
                            "Nuri is 50 and Sonu is 20"])
    assert [s["verdict"] for s in steps[3:]] == ["WORKING", "ACCEPT", "WORKING", "WORKING", "ACCEPT", "WORKING",
                                                 "ACCEPT", "CONCLUSION_RIGHT"]


def test_full_flow_by_substitution_and_its_hints():
    steps = _steps(INTRO + ["x − 3y = −10, x − 2y = 10", "x = 3y − 10", "(3y − 10) − 2y = 0"])
    assert steps[-1]["verdict"] == "WRONG_CLAIM" and "x − y = 1 gives x = y + 1" in steps[-1]["hint"]


def test_dont_know_years_ago_gets_the_meaning():
    out = _steps(INTRO + ["i dont know what is years ago"])[-1]
    assert out["verdict"] == "DONT_KNOW" and "take n away" in out["feedback_message"]


def test_hints_use_other_numbers():
    for n in get_graph(PID).nodes:
        for h in (n.hints or [])[:-1]:
            assert not any(k in h for k in ("= 3(y − 5)", "= 2(y + 10)", "y = 20", "x = 50"))


def test_the_whole_solution_in_one_answer_goes_to_verify():
    work = ("present Sonu age=y,Nuri age=x then 5 years ago, Sonu age=y−5,Nuri age=(x−5) then,(x−5)=3(y−5),"
            "x−5=3y−15,x−3y=-10,x=(3y-10) after 10 years, Sonu age =10+y, Nuri age =(10+x) then,10+x=2(10+y),"
            "10+x=20+2y,\nx-2y=10,3y-10-2y=10,y=20,x=50.\n\nNuri's age 50 years , Sonu's age 20 years")
    out = _steps(INTRO[:2] + [work])[-1]
    assert out["verdict"] == "ACCEPT" and out["active_label"] == "Verify"
    half = _steps(INTRO + ["x − 5 = 3(y − 5), x + 10 = 2(y + 10), y = 20"])[-1]
    assert half["active_label"] == "Solve the Pair"


def test_the_students_own_letters():
    steps = _steps(INTRO + ["let Sonu's age be x and Nuri's age be y", "y − 5 = 3(x − 5)", "y + 10 = 2(x + 10)",
                            "(y − 3x) − (y − 2x) = −10 − 10", "x = 20", "y = 50"])
    assert "Nuri = y, Sonu = x" in steps[3]["feedback_message"]
    assert [s["verdict"] for s in steps[4:]] == ["WORKING", "ACCEPT", "WORKING", "WORKING", "ACCEPT"]
    assert "x = 20" in steps[-2]["feedback_message"] and steps[-1]["active_label"] == "Verify"
    other = _steps(INTRO + ["Nuri = a, Sonu = b", "a − 5 = 3(b − 5) and a + 10 = 2(b + 10)", "b = 20, a = 50"])
    assert other[-1]["active_label"] == "Verify"


def test_ages_the_wrong_way_round():
    assert "wrong way round" in L.step("pair_form", "y − 5 = 3(x − 5)", SPEC, [])["message"]
    swapped = L.step("pair_form", "Sonu = x, Nuri = y, x − 5 = 3(y − 5)", SPEC, [])
    assert "wrong way round" in swapped["message"] and "x − 5 = 3(y − 5)" in swapped["message"]


def test_form_hints_follow_the_stage():
    steps = _steps(INTRO + ["i dont know", "5 years ago Nuri = x − 5, Sonu = y − 5", "i dont know",
                            "x − 5 = 3(y − 5)", "i dont know"])
    assert "your own age five years ago" in steps[3]["hint"]                       # Stage 3
    assert steps[4]["verdict"] == "WORKING" and "three times another" in steps[4]["hint"]   # Stage 4
    assert "Example: 'two years ago" in steps[5]["hint"]                           # stuck again: its example
    assert "ten years from today" in steps[7]["hint"]                              # Stage 5
    swapped = _steps(INTRO + ["Sonu = x, Nuri = y", "x − 5 = 3y", "x − 5 = 3y", "x − 5 = 3y"])[-1]
    assert swapped["hint"] == "y − 5 = 3(x − 5)"                                   # in the student's letters


@pytest.mark.parametrize("line,where", [
    ("5 years ago Nuri = x − 5, Sonu = y − 5", "Form the Equations"), ("Nuri = x, Sonu = y", "Form the Equations"),
    ("x − 5 = 3(y − 5)", "Form the Equations"), ("x − 5 = 3y", "Form the Equations"),
    ("Nuri is 50 and Sonu is 20", "Form the Equations"), ("x − 3y = −10, x − 2y = 10, y = 20, x = 50", "Verify"),
])
def test_work_instead_of_a_plan(line, where):
    out = _steps(INTRO[:2] + [line])[-1]
    assert out["active_label"] == where and out["verdict"] != "PLAN_FEEDBACK"


def test_dont_know_at_the_plan_asks_four_questions_in_order():
    steps = _steps(INTRO[:2] + ["i dont know", "their ages", "Nuri and Sonu, present ages", "i dont know",
                                "Nuri x − 5 and Sonu y − 5", "x − 5 = 3y", "x − 5 = 3(y − 5)",
                                "x + 10 = 2(y + 10)"])
    assert "Whose ages are unknown" in steps[2]["hint"]
    assert steps[3]["verdict"] == "WRONG_CLAIM" and "Whose ages" in steps[3]["next_prompt"]   # must be answered
    assert "your own age five years ago" in steps[4]["next_prompt"]
    assert steps[5]["verdict"] == "DONT_KNOW" and "a − 3" in steps[5]["hint"]
    assert "three times another" in steps[6]["next_prompt"]
    assert steps[7]["verdict"] == "WRONG_CLAIM"
    assert "ten years from today" in steps[8]["next_prompt"]
    assert steps[9]["active_label"] == "Solve the Pair"


def test_the_relationship_for_today_is_a_right_step_in_the_plan_questions():
    steps = _steps(INTRO[:2] + ["i dont know", "Nuri and Sonu, present ages", "x − 5 and y − 5",
                                "person 1 age =x person 2 age =y then,x=3y", "x − 5 = 3(y − 5)", "x = 2y"])
    assert steps[5]["verdict"] == "WORKING" and "five years ago" in steps[5]["next_prompt"]
    assert "ten years from today" in steps[6]["next_prompt"]
    assert steps[7]["verdict"] == "WORKING" and "ten years later" in steps[7]["next_prompt"]
