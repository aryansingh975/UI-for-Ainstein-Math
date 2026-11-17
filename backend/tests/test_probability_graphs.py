import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.graph_loader import get_graph
from app.engine.method_classifier import classify_graph
from app.engine.tutor_engine import parse_step
from app.engine.sympy_validator import validate

client = TestClient(app)

Q4 = "g10-jemh114-ex-14-1-q4"


@pytest.mark.parametrize("work,expected", [
    ("0 ≤ P(E) ≤ 1", "m1_range"),
    ("15% = 15/100 = 0.15", "m1_range"),
    ("P(not E) = 1 - P(E)", "m2_complement"),
    ("1 - (-1.5) = 2.5", "m2_complement"),
    ("P(E) = favourable outcomes / total outcomes", "m3_definition"),
    ("-1.5 = -3/2", "m3_definition"),
    ("I like pizza", "off_graph"),
])
def test_jev_identifies_probability_methods(work, expected):
    result = classify_graph(get_graph(Q4), work)
    assert (result["methodId"] if result["status"] == "selected" else result["status"]) == expected


def test_q4_graph_meta():
    meta = get_graph(Q4).graph_meta
    assert meta.use_jev is True and meta.sympy_can_finish is False
    assert meta.problem_context["correct_option"] == "B"
    assert client.post("/api/v1/sessions/start", json={"problem_id": Q4}).json()["use_jev"] is True


@pytest.mark.parametrize("line,is_true", [
    ("-1.5 < 0", True), ("−1.5 < 0", True), ("-1.5 > 0", False),
    ("2.5 > 1", True), ("2.5 < 1", False), ("0 ≤ 0.7 ≤ 1", True), ("0.7 >= 1", False),
])
def test_inequalities_are_checked_claims(line, is_true):
    claims = parse_step(line).claims
    assert claims and all(c.is_true for c in claims) == is_true


@pytest.mark.parametrize("line", ["a -> b", "x => 5", "35 ÷ 75 × 100 = 46.67%"])
def test_arrows_and_percent_labels_are_not_claims(line):
    assert parse_step(line).claims == []


@pytest.mark.parametrize("line,valid", [
    ("1 - 0.7 = 0.3", True), ("0.1 + 0.2 = 0.3", True), ("1 - 0.7 = 0.4", False), ("2/3 = 0.67", False),
])
def test_sympy_allows_float_rounding_only(line, valid):
    assert validate(line, None)["is_valid"] is valid


PATHS = [
    (["0 ≤ P(E) ≤ 1"], "m1_range", ["15% = 15/100 = 0.15", "-1.5 < 0", "(B) -1.5"]),
    (["0 <= P(E) <= 1"], "m1_range", ["2/3 ≈ 0.67", "-1.5 is negative", "option B"]),
    (["0 ≤ P(E) ≤ 1"], "m1_range", ["-1.5 < 0", "the answer is (B)"]),                  # skipping a step
    (["P(not E) = 1 - P(E)"], "m2_complement", ["1 - (-1.5) = 2.5", "2.5 > 1", "(B) -1.5"]),
    (["P(E) + P(not E) = 1"], "m2_complement", ["1 - 0.7 = 0.3", "1 - (-1.5) = 2.5", "2.5 > 1", "B"]),
    (["P(E) = favourable outcomes / total outcomes"], "m3_definition",
     ["0.7 = 7/10", "-1.5 = -3/2", "-1.5 cannot be a probability"]),
]


def _locked_session(jev_lines, method):
    sid = client.post("/api/v1/sessions/start", json={"problem_id": Q4}).json()["session_id"]
    check = client.post("/api/v1/jev/classify", json={"problem_id": Q4, "lines": jev_lines}).json()
    assert check["method"]["methodId"] == method
    assert client.post(f"/api/v1/sessions/{sid}/method", json={"method_id": method}).status_code == 200
    for line in jev_lines:
        assert client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": line}).json()["verdict"] == "ACCEPT"
    return sid


def _step(sid, line):
    return client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": line}).json()


@pytest.mark.parametrize("jev_lines,method,rest", PATHS)
def test_full_jev_flow_solves_q4(jev_lines, method, rest):
    sid = _locked_session(jev_lines, method)
    for line in rest:
        step = _step(sid, line)
        assert step["verdict"] in ("ACCEPT", "CONCLUSION_RIGHT"), line
    assert step["completed"] is True


def test_q4_mistakes_are_caught():
    sid = _locked_session(["0 ≤ P(E) ≤ 1"], "m1_range")
    assert _step(sid, "15% = 1.5")["verdict"] != "ACCEPT"
    assert _step(sid, "-1.5 > 0")["verdict"] == "WRONG_CLAIM"
    assert _step(sid, "-1.5 < 0")["verdict"] == "ACCEPT"
    for wrong in ("(A) 2/3", "option c", "(d) 0.7"):
        assert _step(sid, wrong)["verdict"] == "CONCLUSION_WRONG", wrong
    assert _step(sid, "(B)")["completed"] is True


# ─── Ex 14.1 Q7: P(not same birthday) = 0.992 ───────────────────────────────
Q7 = "g10-jemh114-ex-14-1-q7"


@pytest.mark.parametrize("work,expected", [
    ("P(E) + P(not E) = 1", "m1_complement"),
    ("x + 0.992 = 1", "m2_equation"),
    ("let x be the probability", "m2_equation"),
    ("I like pizza", "off_graph"),
])
def test_jev_identifies_q7_methods(work, expected):
    result = classify_graph(get_graph(Q7), work)
    assert (result["methodId"] if result["status"] == "selected" else result["status"]) == expected


def _guided(lines):
    """Answer the guided questions in order; return every response."""
    sid = client.post("/api/v1/sessions/start", json={"problem_id": Q7}).json()["session_id"]
    return [_step(sid, line) for line in lines]


def test_q7_is_guided_and_starts_with_what_is_given():
    start = client.post("/api/v1/sessions/start", json={"problem_id": Q7}).json()
    assert start["guided"] is True
    assert start["prompt"] == "What is given in the question?"


@pytest.mark.parametrize("lines,method", [
    (["0.992", "P(same birthday)", "complementary events", "P(E) + P(not E) = 1", "P(E) = 1 - 0.992", "0.008",
      "The probability that the 2 students have the same birthday is 0.008"], "m1"),
    (["P(not same birthday) = 0.992", "find the probability that the 2 students have the same birthday",
      "they are complementary", "x = P(same birthday)", "x + 0.992 = 1", "x = 1 - 0.992 = 0.008",
      "P(same birthday) = 0.008"], "m2"),
    (["0.992", "same birthday", "complementary", "P(E) + P(not E) = 1", "P(E) = 0.008",       # skips a question
      "P(same birthday) = 0.008"], "m1"),
])
def test_q7_guided_paths_solve(lines, method):
    steps = _guided(lines)
    assert [s["verdict"] for s in steps[:-1]] == ["ACCEPT"] * (len(lines) - 1)
    assert steps[-1]["verdict"] == "CONCLUSION_RIGHT" and steps[-1]["completed"] is True
    assert steps[-1]["method_id"] == method


def test_q7_questions_follow_the_pdf():
    steps = _guided(["0.992", "P(same birthday)", "complementary events"])
    assert steps[0]["next_prompt"] == "What do we need to find?"
    assert "How are they related?" in steps[1]["next_prompt"]
    assert "1. How are P(E) and P(not E) related?" in steps[2]["next_prompt"]
    assert "2. Let the unknown probability be x. What does x stand for?" in steps[2]["next_prompt"]


def test_q7_hints_come_in_order_after_wrong_answers():
    steps = _guided(["0.992", "P(same birthday)", "they are equal", "dunno", "no idea", "no idea", "complementary"])
    assert [s["hint"] for s in steps[2:6]] == [
        "Can both happen at the same time?",
        "They are opposites of each other. What do we call such events?",
        "They are called complementary events.",
        "They are called complementary events.",                       # stays on the last hint
    ]
    assert steps[6]["verdict"] == "ACCEPT" and steps[6]["hint"] is None


def test_q7_wrong_answers_get_the_right_methods_hints():
    intro = ["0.992", "P(same birthday)", "complementary"]
    m1 = _guided(intro + ["P(E) + P(not E) = 2"])[-1]
    assert m1["verdict"] == "WRONG_ANSWER" and m1["hint"] == "Can both events happen together? Is there a third possibility?"
    m2 = _guided(intro + ["x = P(not same birthday)"])[-1]
    assert m2["verdict"] == "WRONG_ANSWER" and m2["hint"] == "What are we trying to find?"


@pytest.mark.parametrize("wrong,verdict", [
    ("P(E) = 0.992", "WRONG_ANSWER"),          # used the given probability
    ("P(E) = 1 + 0.992", "WRONG_CLAIM"),
])
def test_q7_method1_mistakes(wrong, verdict):
    step = _guided(["0.992", "P(same birthday)", "complementary", "P(E) + P(not E) = 1", wrong])[-1]
    assert step["verdict"] == verdict and step["hint"] == "Which one is given, P(E) or P(not E)?"


def test_q7_final_answer_must_be_stated_and_hints_follow_the_method():
    m1 = _guided(["0.992", "P(same birthday)", "complementary", "P(E) + P(not E) = 1", "P(E) = 1 - 0.992",
                  "0.008", "0.08", "0.008"])
    assert m1[6]["verdict"] == "WRONG_ANSWER" and m1[6]["hint"] == "What does P(E) stand for?"
    assert m1[7]["verdict"] == "WRONG_ANSWER"                    # just the number is not the final statement
    m2 = _guided(["0.992", "P(same birthday)", "complementary", "x = P(same birthday)", "x + 0.992 = 1",
                  "x = 0.008", "the probability is 0.08"])
    assert m2[-1]["hint"] == "What does x stand for?"


def test_q7_has_only_complement_based_methods():
    labels = [n.label for n in get_graph(Q7).nodes if n.type == "method"]
    assert labels == ["Method 1: Complement Rule P(E) = 1 − P(not E)", "Method 2: Let x Be the Probability and Solve"]


def test_free_form_problems_are_not_guided():
    for pid in (Q4, "g10-jemh110-ex-10-2-q6"):
        assert client.post("/api/v1/sessions/start", json={"problem_id": pid}).json()["guided"] is False


def test_wrong_x_is_a_mistake_in_q7():
    data = client.post("/api/v1/jev/classify", json={"problem_id": Q7, "lines": ["x = 0.08"]}).json()
    assert data["status"] == "fix_mistake"


# ─── Ex 14.1 Q10: piggy bank (guided, from the Q10 hint sheet) ─────────────
Q10 = "g10-jemh114-ex-14-1-q10"
Q10_INTRO = ["100 coins of 50p, 50 coins of ₹1, 20 coins of ₹2 and 10 coins of ₹5",
             "(i) P(50p coin) and (ii) P(not a ₹5 coin)", "100 + 50 + 20 + 10 = 180", "P(50p coin) = 100/180 = 5/9"]


def _guided10(lines):
    sid = client.post("/api/v1/sessions/start", json={"problem_id": Q10}).json()["session_id"]
    return [_step(sid, line) for line in lines]


def test_q10_is_guided_and_asks_the_sheets_questions():
    start = client.post("/api/v1/sessions/start", json={"problem_id": Q10}).json()
    assert start["guided"] is True and start["prompt"] == "What is given in the question?"
    steps = _guided10(Q10_INTRO)
    assert [s["next_prompt"].split("\n")[0] for s in steps] == [
        "What do we need to find?",
        "How many coins are there in the piggy bank altogether?",
        "(i) What is the probability that the coin is a 50p coin?",
        "For part (ii), choose a method by answering either question:",
    ]


@pytest.mark.parametrize("lines,method", [
    (Q10_INTRO + ["100 + 50 + 20 = 170", "P(not ₹5) = 170/180 = 17/18", "(i) 5/9 (ii) 17/18"], "m1"),
    (Q10_INTRO + ["P(₹5) = 10/180 = 1/18", "P(not ₹5) = 1 - 1/18 = 17/18", "(i) 5/9, (ii) 17/18"], "m2"),
    (["100, 50, 20 and 10", "P(50p) and P(not ₹5)", "180", "5/9", "170", "17/18", "5/9 and 17/18"], "m1"),
])
def test_q10_guided_paths_solve(lines, method):
    steps = _guided10(lines)
    assert [s["verdict"] for s in steps[:-1]] == ["ACCEPT"] * (len(lines) - 1)
    assert steps[-1]["completed"] is True and steps[-1]["method_id"] == method


def test_q10_hints_follow_the_sheet():
    steps = _guided10(["100, 50, 20, 5", "4 kinds", "100, 50, 20 and 10"])
    assert [s["hint"] for s in steps[:2]] == ["How many kinds of coins are in the piggy bank?",
                                             "Write how many coins there are of each kind."]
    assert all(s["verdict"] == "WRONG_ANSWER" for s in steps[:2])


@pytest.mark.parametrize("before,wrong,verdict,hint", [
    (Q10_INTRO[:2], "100 + 50 + 20 + 10 = 170", "WRONG_CLAIM", "Add the number of coins of each kind."),
    (Q10_INTRO[:3], "50/180", "WRONG_ANSWER", "P(E) = number of favourable outcomes ÷ total number of outcomes."),
    (Q10_INTRO[:3], "100/180 = 5/8", "WRONG_CLAIM", "P(E) = number of favourable outcomes ÷ total number of outcomes."),
    (Q10_INTRO, "100 + 50 + 20 = 180", "WRONG_CLAIM", "Which coins are not ₹5?"),
    (Q10_INTRO + ["P(₹5) = 1/18"], "1/18", "WRONG_ANSWER",
     "“Not ₹5” and “₹5” are complementary events, so their probabilities add up to 1."),
    (Q10_INTRO + ["P(₹5) = 1/18"], "1 - 1/18 = 16/18", "WRONG_CLAIM",
     "“Not ₹5” and “₹5” are complementary events, so their probabilities add up to 1."),
])
def test_q10_wrong_answers(before, wrong, verdict, hint):
    step = _guided10(before + [wrong])[-1]
    assert step["verdict"] == verdict and step["hint"] == hint


def test_q10_wrong_final_answer_gets_a_hint():
    step = _guided10(Q10_INTRO + ["170", "17/18", "5/9 and 17/19"])[-1]
    assert step["verdict"] == "WRONG_ANSWER" and step["hint"] == "Part (i): 100/180 = ?"


def test_q10_choice_hints_are_written_for_q5():
    choice = next(n for n in get_graph(Q10).nodes if n.id == "method_choice")
    assert choice.hints == ["Answer just one of the two questions.", "Path A: which coins are not ₹5?",
                            "Path B: how many ₹5 coins are there out of 180?"]


# ─── Guided steps: SymPy accepts any correct form of a step's value ─────────
@pytest.mark.parametrize("before,answer", [
    (Q10_INTRO + ["P(₹5) = 1/18"], "P(not a ₹5 coin)=170/180"),       # Path B's last step, written as 170/180
    (Q10_INTRO + ["P(₹5) = 1/18"], "P(not ₹5) = 34/36"),
    (Q10_INTRO + ["170"], "P(not a ₹5 coin) = 0.94 + 1/225"),          # 17/18, exactly
    (Q10_INTRO[:3], "P(50p coin) = 10/18"),
    (Q10_INTRO[:2], "2 × 90"),
    (Q10_INTRO, "180 - 10"),
])
def test_guided_step_accepts_any_correct_form(before, answer):
    assert _guided10(before + [answer])[-1]["verdict"] == "ACCEPT"


def test_guided_step_reports_a_broken_chain_as_a_mistake():
    step = _guided10(Q10_INTRO + ["P(₹5) = 1/18", "P(not a ₹5 coin) = 170/180 = 17/19"])[-1]
    assert step["verdict"] == "WRONG_CLAIM" and "17/19" in step["explanation"]


@pytest.mark.parametrize("wrong", ["1/18", "P(not ₹5) = 10/180", "P(not ₹5) = 0.94"])
def test_guided_step_rejects_other_values(wrong):
    assert _guided10(Q10_INTRO + ["P(₹5) = 1/18", wrong])[-1]["verdict"] != "ACCEPT"


def test_q7_value_written_as_a_fraction_skips_the_repeated_question():
    steps = _guided(["0.992", "P(same birthday)", "complementary", "P(E) + P(not E) = 1", "P(E) = 1/125"])
    assert steps[-1]["verdict"] == "ACCEPT" and steps[-1]["active_node_id"] == "conclusion"
    steps = _guided(["0.992", "P(same birthday)", "complementary", "P(E) + P(not E) = 1", "P(E) = 1 - 0.992"])
    assert steps[-1]["active_node_id"] == "m1_s3"                     # a calculation answers just this question


# ─── Guided method choice: Jev is shown to the student ──────────────────────
def test_guided_choice_shows_jev_for_right_and_wrong_answers():
    right = _guided10(Q10_INTRO + ["P(₹5) = 10/180 = 1/18"])[-1]
    assert right["jev"]["note"].startswith("Jev identified: Path B")
    assert right["jev"]["probabilities"]["m2_complement"] > 0.9
    assert right["method_label"].startswith("Path B")
    wrong = _guided10(Q10_INTRO + ["P(₹5) = 10/18"])[-1]
    assert wrong["hint"] == "How many ₹5 coins are there?"
    assert wrong["jev"]["note"].startswith("Jev thinks you are trying Path B")


def test_jev_is_not_sent_for_other_guided_questions():
    steps = _guided10(Q10_INTRO + ["170"])
    assert all(s["jev"] is None for s in steps[:4]) and steps[4]["jev"] is not None


# ─── Guided final answer: SymPy checks the values in the sentence ───────────
Q10_TO_END = Q10_INTRO + ["170", "17/18"]
Q7_TO_END = ["0.992", "P(same birthday)", "complementary", "P(E) + P(not E) = 1", "P(E) = 1 - 0.992", "0.008"]


@pytest.mark.parametrize("answer,verdict", [
    ("(i) 100/180 (ii) 34/36", "CONCLUSION_RIGHT"),
    ("P(50p coin) = 10/18 and P(not a ₹5 coin) = 170/180", "CONCLUSION_RIGHT"),
    ("(i) 100/180 = 5/9, (ii) 1 - 1/18 = 17/18", "CONCLUSION_RIGHT"),
    ("(i) 5/9 (ii) 170/180 = 17/19", "WRONG_CLAIM"),       # broken chain
    ("5/9 and 17/19", "WRONG_ANSWER"),
    ("17/18 and 5/9", "WRONG_ANSWER"),                      # parts swapped
    ("5/9", "WRONG_ANSWER"),                                # part (ii) missing
    ("the answers are 5/9, 17/18 and 1/18", "WRONG_ANSWER"),
])
def test_q10_final_answer_checked_by_sympy(answer, verdict):
    assert _guided10(Q10_TO_END + [answer])[-1]["verdict"] == verdict


@pytest.mark.parametrize("answer,verdict", [
    ("the probability that the 2 students have the same birthday is 1/125", "CONCLUSION_RIGHT"),   # "2" is from the question
    ("P(same birthday) = 8/1000", "CONCLUSION_RIGHT"),
    ("P(same birthday) = 1 - 0.992 = 0.08", "WRONG_CLAIM"),
    ("the probability that the 2 students have the same birthday is 0.08", "WRONG_ANSWER"),
    ("0.008", "WRONG_ANSWER"),                              # still has to say what the probability is of
])
def test_q7_final_answer_checked_by_sympy(answer, verdict):
    assert _guided(Q7_TO_END + [answer])[-1]["verdict"] == verdict


# ─── Q7: SymPy decides every number and equation line ───────────────────────
Q7_M1 = ["0.992", "P(same birthday)", "complementary", "P(E) + P(not E) = 1"]
Q7_M2 = ["0.992", "P(same birthday)", "complementary", "x = P(same birthday)"]


@pytest.mark.parametrize("before,line,verdict", [
    (Q7_M2, "1 - x = 0.992", "ACCEPT"),                   # any equivalent equation
    (Q7_M2, "0.992 = 1 - x", "ACCEPT"),
    (Q7_M2, "x - 0.992 = 1", "WRONG_CLAIM"),              # the text matcher used to accept this one
    (Q7_M2, "x + 0.992 = 2", "WRONG_CLAIM"),
    (Q7_M2, "x = 0.992 - 1", "WRONG_CLAIM"),
    (Q7_M1, "P(E) = 125/125 - 124/125", "ACCEPT"),
    (Q7_M1, "P(E) = 1 + 0.992", "WRONG_CLAIM"),
    (Q7_M1 + ["P(E) = 1 - 0.992"], "8/1000", "ACCEPT"),
    (Q7_M1 + ["P(E) = 1 - 0.992"], "1 + 0.992", "WRONG_CLAIM"),
])
def test_q7_sympy_checks_numbers_and_equations(before, line, verdict):
    assert _guided(before + [line])[-1]["verdict"] == verdict


def test_sympy_explains_a_wrong_equation():
    step = _guided(Q7_M2 + ["x - 0.992 = 1"])[-1]
    assert "does not have the same solutions" in step["explanation"]
