import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.graph_loader import get_graph
from app.engine.method_classifier import classify_graph

client = TestClient(app)

Q6 = "g10-jemh112-ex-12-2-q6"
INTRO = ["big cylinder: h = 220 cm, d = 24 cm; small cylinder: h = 60 cm, r = 8 cm; 1 cm³ = 8 g",
         "the mass of the pole"]
PLAN = "Find the volume of both cylinders, add them, multiply by 8."
PATH_A = ["r = 24/2 = 12 cm", "V1 = 3.14 × 12² × 220 = 99475.2 cm³", "V2 = 3.14 × 8² × 60 = 12057.6 cm³",
          "V = 99475.2 + 12057.6 = 111532.8 cm³", "mass = 111532.8 × 8 = 892262.4 g"]
PATH_B = ["12² × 220 + 8² × 60 = 31680 + 3840 = 35520", "V = 3.14 × 35520 = 111532.8 cm³",
          "mass = 111532.8 × 8 = 892262.4 g"]


def _guided(lines):
    sid = client.post("/api/v1/sessions/start", json={"problem_id": Q6}).json()["session_id"]
    return [client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": line}).json() for line in lines]


def test_q6_asks_given_goal_then_the_plan():
    start = client.post("/api/v1/sessions/start", json={"problem_id": Q6}).json()
    assert start["guided"] is True and start["prompt"] == "What is given in the question?"
    assert [s["next_prompt"] for s in _guided(INTRO)] == [
        "What do we need to find?",
        "Describe your plan to solve the problem. How will you find the mass of the pole?",
    ]


@pytest.mark.parametrize("lines", [PATH_A, PATH_B, list(reversed(PATH_A[1:3])) + PATH_A[3:]])
def test_q6_correct_plan_then_solve_alone_in_any_order(lines):
    steps = _guided(INTRO + [PLAN] + lines)
    assert steps[2]["choice"]["category"] == "correct" and steps[2]["active_label"] == "Solve on Your Own"
    assert all(s["verdict"] == "ACCEPT" and s["hint"] is None for s in steps[2:-1])     # no hints while it is right
    assert steps[-1]["verdict"] == "CONCLUSION_RIGHT"


@pytest.mark.parametrize("answer", ["π × 12² × 220 = 99475.2 cm³", "3.14 × 144 × 220 = 99475.2 cm3", "r = 12 cm",
                                    "12^2*220 + 8^2*60 = 35520", "3.14 × 64 × 60"])
def test_q6_free_solving_accepts_any_correct_form(answer):
    assert _guided(INTRO + [PLAN, answer])[-1]["verdict"] == "ACCEPT"


@pytest.mark.parametrize("wrong,explains", [
    ("V1 = 3.14 × 12² × 220 = 99000", "doesn't hold"),
    ("12² × 220 + 8² × 60 = 35000", "doesn't hold"),
    ("3.14 × 24² × 220 = 397900.8", "not a number this problem needs"),      # used the diameter
    ("111532.8 × 8 = 892000", "doesn't hold"),
])
def test_q6_free_solving_gives_feedback_only_on_mistakes(wrong, explains):
    step = _guided(INTRO + [PLAN, wrong])[-1]
    assert step["verdict"] == "WRONG_CLAIM" and explains in step["explanation"] and not step["completed"]


@pytest.mark.parametrize("answer,verdict", [
    ("892262.4 g", "CONCLUSION_RIGHT"), ("892.26 kg", "CONCLUSION_RIGHT"), ("892262.4 g ≈ 892.26 kg", "CONCLUSION_RIGHT"),
    ("The mass of the pole is 892.26 kg", "CONCLUSION_RIGHT"), ("892.3 kg", "WRONG_CLAIM"), ("111532.8 g", "UNIT_ISSUE"),
    ("892262.4", "UNIT_ISSUE"), ("892262.4 kg", "UNIT_ISSUE"),
])
def test_q6_final_answer_in_g_or_kg(answer, verdict):
    prefix = PATH_A[:-1]
    assert _guided(INTRO + [PLAN] + prefix + [answer])[-1]["verdict"] == verdict


def test_q6_a_calculation_instead_of_a_plan_starts_solving():
    steps = _guided(INTRO + ["V1 = 3.14 × 12² × 220 = 99475.2 cm³"])
    assert steps[-1]["verdict"] == "ACCEPT" and steps[-1]["active_label"] == "Solve on Your Own"


@pytest.mark.parametrize("work,expected", [
    ("3.14 × 12² × 220 = 99475.2", "m1_add_volumes"),
    ("V1 = 3.14 × 12² × 220 = 99000", "m1_add_volumes"),      # wrong result, Path A's working
    ("12² × 220 + 8² × 60 = 35000", "m2_factor_pi"),          # wrong result, Path B's working
    ("35520", "m2_factor_pi"),
])
def test_jev_identifies_q6_paths(work, expected):
    result = classify_graph(get_graph(Q6), work)
    assert result["status"] == "selected" and result["methodId"] == expected


@pytest.mark.parametrize("line,verdict", [
    ("Volume of a cylinder = πr²", "WRONG_CLAIM"), ("V = πrh", "WRONG_CLAIM"), ("V = 2πrh", "WRONG_CLAIM"),
    ("Volume of a cylinder = πr²h.", "ACCEPT"), ("V = πr^2 h", "ACCEPT"), ("V1 = π × r² × h", "ACCEPT"),
    ("Mass = total volume × 8", "ACCEPT"),                 # words for its letters (the formula's words)
])
def test_q6_free_solving_checks_formulas_written_in_letters(line, verdict):
    step = _guided(INTRO + [PLAN, line])[-1]
    assert step["verdict"] == verdict
    if verdict == "WRONG_CLAIM":
        assert "not the formula for the volume of a cylinder" in step["explanation"]


@pytest.mark.parametrize("line", ["Add the two volumes.99475.2 + 12057.6 = 111532.8 cm³",
                                  "Add the two volumes.\t99475.2 + 12057.6 = 111532.8 cm³"])
def test_q6_a_full_stop_before_a_number_is_not_part_of_it(line):
    assert _guided(INTRO + [PLAN, line])[-1]["verdict"] == "ACCEPT"


@pytest.mark.parametrize("line,verdict,says", [
    ("3.14 × 64 × 60", "ACCEPT", None),                                   # no result yet: no unit needed
    ("3.14 × 64 × 60 = 12057.6", "UNIT_ISSUE", "calculation is correct, but the unit is missing after 12057.6"),
    ("3.14 × 64 × 60 = 12057.6 cm²", "UNIT_ISSUE", "12057.6 is not in cm²"),
    ("3.14 × 64 × 60 = 12057.6 cm 3", "ACCEPT", None),
    ("Add the two volumes.99475.2 + 12057.6 = 111532.8", "UNIT_ISSUE", "unit is missing after 111532.8"),
    ("r = 24/2 = 12", "UNIT_ISSUE", "unit is missing after 12"),
    ("12² × 220 + 8² × 60 = 35520", "ACCEPT", None),                      # an intermediate number: no unit
    ("111532.8 g", "UNIT_ISSUE", "value is correct, but 111532.8 is not in g"),
])
def test_q6_a_result_needs_its_unit(line, verdict, says):
    step = _guided(INTRO + [PLAN, line])[-1]
    assert step["verdict"] == verdict
    if says:
        assert says in step["feedback_message"]


@pytest.mark.parametrize("line,verdict", [
    ("V = pi r^2 h", "ACCEPT"), ("Volume of a cylinder = pir²h", "ACCEPT"), ("V = PI r² h", "ACCEPT"),
    ("V = 2 pi r h", "WRONG_CLAIM"), ("pi × 12² × 220 = 99475.2 cm³", "ACCEPT"), ("pi × 12² × 220 = 99000 cm³", "WRONG_CLAIM"),
])
def test_q6_pi_can_be_written_as_pi(line, verdict):
    assert _guided(INTRO + [PLAN, line])[-1]["verdict"] == verdict


TURN5 = ("v1= pir^2h\n3.14 × 144 × 220 = 99475.2 cm³\nv2= 3.14 × 64 × 60 = 12057.6 cm³\n"
         "Total volume = 99475.2 + 12057.6 = 111532.8 cm³\nMass = total volume × 8\t\n111532.8 × 8 = 892262.4 g")


@pytest.mark.parametrize("old,new,verdict,says", [
    (None, None, "CONCLUSION_RIGHT", None),
    ("pir^2h", "pir h", "WRONG_CLAIM", "not the formula for the volume of a cylinder"),
    ("= 12057.6 cm³", "= 12000 cm³", "WRONG_CLAIM", "12000"),
    ("= 111532.8 cm³", "= 111532.8", "UNIT_ISSUE", "unit is missing after 111532.8"),
    ("= 892262.4 g", "= 892262.4 kg", "UNIT_ISSUE", "not in kg"),
])
def test_q6_several_lines_in_one_answer_are_checked_line_by_line(old, new, verdict, says):
    text = TURN5.replace(old, new) if old else TURN5
    step = _guided(INTRO + [PLAN, text])[-1]
    assert step["verdict"] == verdict
    if says:
        assert says in (step["explanation"] or step["feedback_message"])


@pytest.mark.parametrize("answer,verdict,prompt", [
    (TURN5, "CONCLUSION_RIGHT", None),                                    # a full solution instead of a plan: done
    ("mass = 8 × 3.14 × (12² × 220 + 8² × 60) = 892262.4 g", "CONCLUSION_RIGHT", None),
    ("V1 = 3.14 × 12² × 220 = 99475.2 cm³", "ACCEPT", "Keep going"),       # started: keep going, not "now solve"
    ("Total volume = 99475.2 + 12057.6 = 111000 cm³", "WRONG_CLAIM", "Keep going"),
    ("Find the volume of both cylinders, add them, multiply by 8.", "ACCEPT", "Now solve it on your own"),
])
def test_q6_plan_step_takes_words_or_a_direct_calculation(answer, verdict, prompt):
    step = _guided(INTRO + [answer])[-1]
    assert step["verdict"] == verdict and step["completed"] is (verdict == "CONCLUSION_RIGHT")
    if prompt:
        assert step["next_prompt"].startswith(prompt)


@pytest.mark.parametrize("line,verdict", [
    ("total volume =v1+v2=99475.2+12057.6=111532.8 cm^3", "ACCEPT"),     # v1 + v2 is not the cylinder formula
    ("total volume = v1 + v2 = 99475.2 + 12057.6 = 111000 cm^3", "WRONG_CLAIM"),
    ("V = πr", "WRONG_CLAIM"),
])
def test_q6_formula_check_only_for_the_cylinder_formula(line, verdict):
    assert _guided(INTRO + [PLAN, line])[-1]["verdict"] == verdict


@pytest.mark.parametrize("answer,verdict", [
    ("892262.4", "UNIT_ISSUE"), ("The mass of the pole is 892.26", "UNIT_ISSUE"), ("892262.4 g ≈ 892.26", "UNIT_ISSUE"),
    ("892262.4 ≈ 892.26 kg", "UNIT_ISSUE"), ("mass = 892262.4 kilograms", "UNIT_ISSUE"),
    ("mass = 892262.4 grams", "CONCLUSION_RIGHT"), ("mass = 892.26 kilograms", "CONCLUSION_RIGHT"),
    ("892262.4 g ≈ 892.26 kg", "CONCLUSION_RIGHT"), ("111532.8 × 8 = 892000 g", "WRONG_CLAIM"),
    ("3.14 × 64 × 60 = 12057.6 cubic cm", "ACCEPT"), ("3.14 × 64 × 60 = 12057.6 cubic m", "UNIT_ISSUE"),
])
def test_q6_final_answer_needs_every_unit(answer, verdict):
    if verdict == "CONCLUSION_RIGHT":
        # Final conclusion requires intermediate steps to be solved first
        assert _guided(INTRO + [PLAN] + PATH_A[:-1] + [answer])[-1]["verdict"] == verdict
    else:
        assert _guided(INTRO + [PLAN, answer])[-1]["verdict"] == verdict


def test_q6_missing_v2_triggers_step_jump():
    """Leaping from V1 directly to Total Volume without calculating V2 must trigger STEP_JUMP."""
    inputs = INTRO + [
        PLAN,
        "V1 = pir^2h\nv1 = 3.14 * 144 * 220 = 99475.2 cm³\ntotal volume = 111532.8 cm³",
    ]
    steps = _guided(inputs)
    step = steps[-1]
    assert step["verdict"] == "STEP_JUMP"
    assert "Volume of the Small Cylinder" in step["feedback_message"]


def test_q6_v2_then_conclusion_triggers_step_jump():
    """User screenshot regression: entering V2 then skipping V1/total to mass must trigger STEP_JUMP."""
    inputs = INTRO + [
        PLAN,
        "v2 = 3.14 * 64 * 60 = 12057.6cm^3",
        "mass = 111532.8 * 8 = 892262.4g",
    ]
    steps = _guided(inputs)
    step = steps[-1]
    assert step["verdict"] == "STEP_JUMP"
    assert "volume of the big cylinder" in step["feedback_message"].lower()


def test_q6_v2_then_v1_then_total_then_mass_succeeds():
    """Full commutative path: solving small cylinder first, then big, then total, then mass succeeds."""
    inputs = INTRO + [
        PLAN,
        "v2 = 3.14 * 64 * 60 = 12057.6cm^3",
        "v1 = 3.14 * 144 * 220 = 99475.2cm^3",
        "total volume = 99475.2 + 12057.6 = 111532.8cm^3",
        "mass = 111532.8 * 8 = 892262.4g",
    ]
    steps = _guided(inputs)
    assert steps[-1]["verdict"] == "CONCLUSION_RIGHT"
    assert steps[-1]["completed"] is True

