import pytest

from app.graph_loader import get_graph
from app.engine import plan_llm
from app.engine.concept_choice import evaluate_plan
from app.engine.plan_llm import check_plan, same

Q6 = "g10-jemh112-ex-12-2-q6"
CHOICE = next(n for n in get_graph(Q6).nodes if n.id == "method_choice")
SPEC = CHOICE.plan_formula


@pytest.fixture
def qwen(monkeypatch):
    """A fake Qwen: answers with the expression the test gives it; says() finds a step when reply["says"] (default)."""
    monkeypatch.setenv("PLAN_LLM", "on")
    reply = {}
    monkeypatch.setattr(plan_llm, "_ask", lambda plan, spec: reply["expression"])
    monkeypatch.setattr(plan_llm, "says", lambda plan, idea: reply.get("says", True))
    return reply


@pytest.mark.parametrize("expression,expected", [
    ("8*pi*(r1**2*h1 + r2**2*h2)", True),
    ("8*pi*r1**2*h1 + 8*pi*r2**2*h2", True),                  # × 8 each, then add
    ("pi r1^2 h1 × 8 + 8 × π r2^2 h2", True),
    ("8*(3.14*12**2*220 + 3.14*8**2*60)", False),             # 3.14 is not π
    ("8*pi*(12**2*220 + 8**2*60)", True),                     # the problem's numbers
    ("8*pi*(r1**2*h1 - r2**2*h2)", False),
    ("pi*(r1**2*h1 + r2**2*h2)", False),                      # no × 8
    ("8*pi*(r**2*h)", None),                                  # a letter we did not ask for
    ("add them", None),
])
def test_sympy_compares_the_plan_in_any_order(expression, expected):
    assert same(expression, SPEC) is expected


def test_qwen_finds_a_plan_the_keywords_miss(qwen):
    plan = "work out the volume of each cylinder, multiply each one by 8 and put the masses together"
    assert evaluate_plan(plan, CHOICE).category == "partial"                 # keywords alone: no C1
    qwen["expression"] = "8*pi*r1**2*h1 + 8*pi*r2**2*h2"
    out = evaluate_plan(plan, CHOICE, llm=check_plan(plan, CHOICE), reader=plan_llm.says)
    assert out.category == "correct" and out.concepts_missing == [] and out.expression == qwen["expression"]


@pytest.mark.parametrize("plan", [
    "add the height of both cylinders and multiply by 8",                    # a wrong idea is still caught first
    "find the area of the cylinders and add them",                           # no idea found: Qwen alone is not enough
])
def test_qwen_cannot_make_a_wrong_plan_right(qwen, plan):
    qwen["expression"] = "8*pi*(r1**2*h1 + r2**2*h2)"
    assert evaluate_plan(plan, CHOICE, llm=check_plan(plan, CHOICE), reader=plan_llm.says).category != "correct"


def test_a_wrong_expression_leaves_the_keyword_check_to_decide(qwen):
    plan = "find the volume of each cylinder and multiply by 8"
    qwen["expression"] = "8*pi*r1**2*h1"
    assert evaluate_plan(plan, CHOICE, llm=check_plan(plan, CHOICE), reader=plan_llm.says).category == "partial"


def test_without_ollama_the_plan_is_checked_by_keywords(monkeypatch):
    monkeypatch.setenv("PLAN_LLM", "on")
    monkeypatch.setenv("PLAN_LLM_URL", "http://127.0.0.1:9")                # nothing listens there
    assert check_plan("find both volumes, add, × 8", CHOICE) is None


def test_plan_llm_off_never_calls_qwen(monkeypatch):
    monkeypatch.setattr(plan_llm, "_ask", lambda *a: pytest.fail("Qwen was called"))
    assert check_plan("find both volumes, add, × 8", CHOICE) is None         # conftest: PLAN_LLM=off


def test_a_step_qwen_added_does_not_make_the_plan_right(qwen):
    """No "add" in the plan: Qwen still writes the sum, but cannot quote words for it."""
    plan = "find the volume of each cylinder and multiply by 8"
    assert evaluate_plan(plan, CHOICE).concepts_missing == ["C1"]
    qwen["expression"], qwen["says"] = "(pi*r1**2*h1 + pi*r2**2*h2)*8", False
    out = evaluate_plan(plan, CHOICE, llm=check_plan(plan, CHOICE), reader=plan_llm.says)
    assert out.category == "partial" and out.concepts_missing == ["C1"]


@pytest.fixture
def quote(monkeypatch):
    """A fake Qwen for says(): answers with the quote the test gives it."""
    monkeypatch.setenv("PLAN_LLM", "on")
    reply = {}
    monkeypatch.setattr(plan_llm, "_chat", lambda system, user, field: reply["quote"])
    return reply


PLAN = "work out the volume of each cylinder, multiply each one by 8 and put the masses together"


@pytest.mark.parametrize("answer,expected", [
    ("multiply each one by 8", True),                         # the student's own words
    ("Multiply each one  by 8.", True),                       # case, spaces and full stop do not matter
    ("multiply by 8", False),                                 # not what the student wrote
    ("× 8 for the mass", False),                              # Qwen repeating the step back
    ("work out the volume of each cylinder, multiply each one by 8 and put the masses together", False),   # all of it
    ("", False),
])
def test_says_needs_a_quote_from_the_plan(quote, answer, expected):
    quote["quote"] = answer
    assert plan_llm.says(PLAN, "× 8 for the mass") is expected


def test_says_without_ollama_is_false(monkeypatch):
    monkeypatch.setenv("PLAN_LLM", "on")
    monkeypatch.setenv("PLAN_LLM_URL", "http://127.0.0.1:9")
    assert plan_llm.says(PLAN, "× 8 for the mass") is False


def test_warm_up_never_raises(monkeypatch):
    monkeypatch.setenv("PLAN_LLM", "on")
    monkeypatch.setenv("PLAN_LLM_URL", "http://127.0.0.1:9")
    plan_llm.warm_up()
    monkeypatch.setenv("PLAN_LLM", "off")
    monkeypatch.setattr(plan_llm, "_post", lambda *a, **k: pytest.fail("Qwen was called"))
    plan_llm.warm_up()


# ─── Qwen reads every plan (Q1, Q2, Q6), never past "I don't know"; its step hints are off by default ────────
from app.engine.concept_choice import _without_unknowns
from app.engine import guided


@pytest.mark.parametrize("raw,kept", [
    ("i dont know what is prime factor", ""),
    ("what is a prime number?", ""),
    ("I will divide by 2 but I don't know when to stop", "i will divide by 2"),
    ("find the volume, then I'm not sure", "find the volume,"),
])
def test_what_the_student_does_not_know_is_never_an_idea(raw, kept):
    assert " ".join(_without_unknowns(raw).split()) == kept


def test_i_dont_know_what_a_prime_is_is_dont_know_not_partial(qwen):
    q1 = next(n for n in get_graph("g10-jemh101-ex-1-1-q1").nodes if n.id == "method_choice")
    out = evaluate_plan("i dont know what is prime factor", q1, reader=plan_llm.says)
    assert out.category == "dont_know" and out.concepts_found == []


def test_the_reader_adds_an_idea_the_keywords_missed(monkeypatch):
    q1 = next(n for n in get_graph("g10-jemh101-ex-1-1-q1").nodes if n.id == "method_choice")
    plan = "break 140 down and keep going till you can't any more"
    assert evaluate_plan(plan, q1).concepts_found == ["C1", "C3"]
    out = evaluate_plan(plan, q1, reader=lambda text, idea: idea == "using prime numbers")
    assert out.concepts_found == ["C1", "C2", "C3"] and out.category == "correct"


def test_the_reader_is_not_asked_when_sympy_says_the_plan_is_wrong():
    out = evaluate_plan("find each volume and multiply by 8", CHOICE, llm={"expression": "8*pi*r1**2*h1", "matches": False},
                        reader=lambda *a: pytest.fail("Qwen was asked"))
    assert out.category == "partial"


def test_llm_hints_are_off_by_default(monkeypatch):
    monkeypatch.setenv("PLAN_LLM", "on")
    assert plan_llm.hints_enabled() is False
    monkeypatch.setenv("PLAN_LLM_HINTS", "on")
    assert plan_llm.hints_enabled() is True


Q1_STEP = next(n for n in get_graph("g10-jemh101-ex-1-1-q1").nodes if n.id == "p1_answer")


@pytest.mark.parametrize("hint,safe", [
    ("You wrote 35 as a factor, but 35 is not prime. Can you split 35?", True),
    ("Check your work: 2 × 5 × 7 = 70, but 2 × 5 × 7 × 2 = 140.", False),   # the answer in other order
    ("Try 2^2 x 5 x 7.", False),
    ("Is 2 × 70 = 150?", False),                                           # a false claim
    ("", False),
])
def test_sympy_checks_a_qwen_hint_before_a_student_sees_it(hint, safe):
    graph = get_graph("g10-jemh101-ex-1-1-q1")
    assert guided._safe_hint(hint, "140 = 2 × 5 × 7", "140 = 2 × 5 × 7", Q1_STEP, graph) is safe
