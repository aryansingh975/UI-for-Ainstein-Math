import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.graph_loader import get_graph, find_graph_files
from app.schemas.graph import SolutionGraph
from app.engine.concept_choice import evaluate_plan, normalise
from app.engine.method_classifier import classify_graph

client = TestClient(app)

Q6 = "g10-jemh112-ex-12-2-q6"
PLAN_PROBLEMS = {Q6, "g10-jemh101-ex-1-1-q1", "g10-jemh101-ex-1-1-q2",   # the "Describe the Plan" problems
                 "g10-jemh102-ex-2-2-q1", "g10-jemh102-ex-2-2-q2", "g10-jemh103-ex-3-3-q2-ii"}
INTRO = ["big cylinder: h = 220 cm, d = 24 cm; small cylinder: h = 60 cm, r = 8 cm; 1 cm³ = 8 g",
         "the mass of the pole"]
GRAPH = get_graph(Q6)
CHOICE = next(n for n in GRAPH.nodes if n.id == "method_choice")


def _plan(text, **kw):
    return evaluate_plan(text, CHOICE, classify_graph(GRAPH, text), default_path="m1_add_volumes", **kw)


def _guided(lines):
    sid = client.post("/api/v1/sessions/start", json={"problem_id": Q6}).json()["session_id"]
    return [client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": line}).json() for line in lines]


@pytest.mark.parametrize("answer,category,missing", [
    ("find both volumes with πr²h, add, × 8", "correct", []),
    ("umm πr²h both add then into 8 lol", "correct", []),
    ("multiply 8 after adding volumn of cylender both, volumn is pi r sq h", "correct", []),
    ("find the volume using πr²h and × 8", "partial", ["C1"]),
    ("big volume minus small volume then × 8", "misconception", ["C1"]),
    ("add or maybe subtract, then × 8", "contradiction", ["C2", "C1"]),   # "add" without a volume: C1 not done
    ("i dont know", "dont_know", ["C2", "C1", "C3"]),
    ("can i go to lunch", "off_topic", ["C2", "C1", "C3"]),
])
def test_sample_answers_are_classified(answer, category, missing):
    out = _plan(answer)
    assert out.category == category and out.concepts_missing == missing
    assert out.accepted is (category == "correct")


@pytest.mark.parametrize("raw,expected", [
    ("pi r square h", "πr²h"), ("π r^2 h", "πr²h"), ("pi r2 h", "πr²h"), ("then into 8", "then × 8"),
    ("multiply by 8", "× 8"), ("times 8", "× 8"), ("multiply by 8.", "× 8."), ("volumn of cylender", "volume of cylinder"),
])
def test_normalise_maps_synonyms_and_spelling(raw, expected):
    assert normalise(raw, CHOICE) == expected


def test_partial_names_found_concepts_and_hints_only_the_first_missing():
    out = _plan("find the volume using πr²h and × 8")
    assert out.message == ("Good, finding the volumes and × 8 for the mass is right. The pole is made of two "
                           "cylinders. How do you get the volume of the whole pole from its two parts?")
    assert out.concept_hint is None and out.next_question == CHOICE.concepts_required[1].hints[0]   # one hint only


@pytest.mark.parametrize("plan,path", [
    ("find both volumes with πr²h, add, × 8", "m1_add_volumes"),
    ("take pi common: pi(r1² h1 + r2² h2) then times 8", "m2_factor_pi"),
    ("πr²h, add, × 8", "m1_add_volumes"),                     # no path signal: default_path
])
def test_correct_plan_picks_path_from_signals(plan, path):
    assert _plan(plan).path == path


@pytest.mark.parametrize("jev,path", [
    ({"status": "selected", "methodId": "m2_factor_pi", "confidence": 0.9}, "m2_factor_pi"),   # Jev is sure: its method
    ({"status": "uncertain", "methodId": None, "confidence": 0.4}, "m1_add_volumes"),         # not sure: path_signals
    (None, "m1_add_volumes"),
])
def test_jev_picks_the_method_of_a_correct_plan(jev, path):
    out = evaluate_plan("find both volumes with πr²h, add, × 8", CHOICE, jev, default_path="m1_add_volumes")
    assert out.category == "correct" and out.path == path


@pytest.mark.parametrize("failed,k", [(0, "K1"), (1, "K2"), (2, "K3")])
def test_plans_with_no_idea_get_k1_k2_k3_in_order(failed, k):
    for answer in ["i dont know", "can i go to lunch"]:
        out = _plan(answer, failed=failed)
        assert not out.accepted and out.concept_hint["id"] == k


def test_a_wrong_idea_gets_its_own_question_and_no_second_hint():
    out = _plan("big volume minus small volume then × 8")
    assert out.category == "misconception" and out.concept_hint is None


def test_correct_plan_needs_no_hint():
    out = _plan("Find the volume of both cylinders, add them, multiply by 8.")
    assert out.accepted and out.concept_hint is None and out.message.endswith("Now solve it on your own.")


def test_answering_the_k_question_is_not_called_off_topic():
    assert _plan("can i go to lunch").message == CHOICE.off_topic_response
    assert _plan("two cylinders", failed=1).message == CHOICE.retry_response


def test_reveal_after_k3_asks_to_explain_a_step_then_continues_on_default_path():
    out = _plan("i dont know", failed=len(CHOICE.concept_hints))
    assert not out.accepted and out.category == "explain" and out.message.startswith(CHOICE.reveal)
    assert out.concepts_given == ["C2", "C1", "C3"] and out.next_question == CHOICE.concepts_required[0].explain.question
    done = _plan("i dont know", progress=out.progress)        # a wrong explanation: the idea is said, then go on
    assert done.accepted and done.path == "m1_add_volumes"
    assert done.message.startswith("Here's the idea. " + CHOICE.concepts_required[0].explain.understanding)


def test_api_returns_the_plan_outcome_with_the_k_hint():
    partial, done = _guided(INTRO + ["find the volume using πr²h and × 8", "find both volumes with πr²h, add, × 8"])[-2:]
    assert partial["verdict"] == "PLAN_FEEDBACK" and partial["choice"]["category"] == "partial"
    assert partial["feedback_message"] == partial["choice"]["message"]
    assert partial["hint"] is None and partial["choice"]["concept_hint"] is None       # the ladder: one hint
    assert partial["next_prompt"] == partial["choice"]["next_question"] == CHOICE.concepts_required[1].hints[0]
    assert set(partial["choice"]) >= {"category", "concepts_found", "concepts_missing", "path", "message", "accepted"}
    assert done["verdict"] == "ACCEPT" and done["choice"]["path"] == "m1_add_volumes"
    assert done["next_prompt"] == CHOICE.solve_prompt


def test_api_k_ladder_then_reveal_then_explain():
    steps = _guided(INTRO + ["i dont know", "two cylinders", "guide me", "no idea", "each cm³ of iron weighs 8 g"])
    assert [s["choice"]["concept_hint"]["id"] for s in steps[-5:-2]] == ["K1", "K2", "K3"]
    reveal, done = steps[-2:]
    assert reveal["verdict"] == "PLAN_FEEDBACK" and reveal["choice"]["message"].startswith(CHOICE.reveal)
    assert reveal["active_label"] == "Explain the Plan" and reveal["next_prompt"] == reveal["choice"]["next_question"]
    assert done["verdict"] == "ACCEPT" and done["choice"]["message"].startswith("Yes, exactly.")   # not a calculation
    assert done["active_label"] == "Solve on Your Own"


def test_calculations_at_the_choice_still_work():
    right = _guided(INTRO + ["12² × 220 + 8² × 60 = 35520"])[-1]
    wrong = _guided(INTRO + ["V1 = 3.14 × 12² × 220 = 99000"])[-1]
    assert right["verdict"] == "ACCEPT" and right["choice"] is None
    assert wrong["verdict"] == "WRONG_CLAIM" and wrong["choice"] is None


def test_every_existing_graph_still_loads_and_old_choice_nodes_have_no_plan():
    for path in find_graph_files():
        graph = SolutionGraph(**json.loads(path.read_text(encoding="utf-8")))
        for node in graph.nodes:
            if node.type == "choice" and graph.graph_meta.problem_uuid not in PLAN_PROBLEMS:
                assert node.concepts_required == []


@pytest.mark.parametrize("answer,category,found", [
    ("I think I will add the height of two pole and divide them by radius", "misconception", []),
    ("add the two areas then × 8", "partial", ["C3"]),                     # "add" without a volume is not C1
    ("add the volumes then × 8", "correct", ["C2", "C1", "C3"]),
])
def test_add_counts_only_for_volumes(answer, category, found):
    out = _plan(answer)
    assert out.category == category and out.concepts_found == found
    assert "adding the two volumes is right" not in out.message


@pytest.mark.parametrize("answer,category", [
    ("find the volume of both cylinder and multiply by 8", "correct"),
    ("volumes of both cylinders × 8", "correct"),
    ("find the volumes and multiply by 8", "partial"),
])
def test_volume_of_both_cylinders_means_adding_them(answer, category):
    assert _plan(answer).category == category


def test_a_wrong_idea_is_caught_even_when_all_three_ideas_are_there():
    out = _plan("add or maybe subtract the volumes, then × 8")
    assert out.category == "contradiction" and not out.accepted


# ─── The three rules: a hint ladder, kept progress, and explaining a given step ──────────────────────────────
def _walk(answers):
    """Answer one after another, keeping the plan's progress (as guided.py does)."""
    progress, failed, outs = None, 0, []
    for a in answers:
        out = _plan(a, failed=failed, progress=progress)
        progress, failed = out.progress, failed + (not out.accepted and out.category != "explain")
        outs.append(out)
    return outs


def test_each_missing_idea_gets_a_question_then_a_nudge_then_the_step():
    c1 = CHOICE.concepts_required[1]
    first, second, third = _walk(["find the volume of each cylinder", "not sure", "no idea"])
    assert first.message.endswith(c1.hints[0]) and second.message == c1.hints[1]        # question, then nudge
    assert third.message.startswith(c1.answer) and third.concepts_given == ["C1"]        # then the step itself
    assert third.next_question == CHOICE.concepts_required[2].hints[0]                    # and on to the next idea


def test_ideas_said_once_are_kept_so_the_plan_is_never_retyped():
    first, second = _walk(["find the volume of each cylinder", "add them, then multiply by 8"])
    assert first.category == "partial" and first.concepts_found == ["C2"]
    assert second.accepted and second.category == "correct" and second.concepts_found == ["C2", "C1", "C3"]


def test_put_them_together_answers_the_question_about_adding():
    """C1 needs a volume in the text, but not when the student answers the question about adding."""
    assert _walk(["find the volume of each cylinder", "put them together"])[-1].concepts_found == ["C2", "C1"]


def test_a_given_step_is_explained_before_solving():
    outs = _walk(["find the volume of each cylinder", "add them", "no idea", "dunno"])   # C3: nudge, then given
    ask, = [o for o in outs if o.category == "explain"]
    assert not ask.accepted and ask.next_question == CHOICE.concepts_required[2].explain.question   # the step given
    done = _plan("because 1 cm³ weighs 8 g", progress=ask.progress)
    assert done.accepted and done.message.startswith("Yes, exactly.")
    assert done.concepts_found == ["C2", "C1"] and done.concepts_given == ["C3"]           # "8 g" here is no new idea


def test_a_plan_found_alone_is_never_asked_to_explain():
    out = _walk(["find the volume of each cylinder", "add them, then multiply by 8"])[-1]
    assert out.accepted and out.next_question is None and out.concepts_given == []


# ─── Solving alone: relationships in words or letters (the node's formulas, with their words) ────────────────
@pytest.mark.parametrize("line,verdict", [
    ("mass = total volume ×8", "ACCEPT"),
    ("mass = volume × 8", "ACCEPT"),
    ("m = V × 8", "ACCEPT"),
    ("mass = 8V", "ACCEPT"),
    ("total volume = V1 + V2", "ACCEPT"),                                   # v1 is one symbol, not v × 1
    ("total volume = volume of big cylinder + volume of small cylinder", "ACCEPT"),
    ("total volume = πr1²h1 + πr2²h2", "ACCEPT"),                          # not checked against πr²h
    ("V = π(r1²h1 + r2²h2)", "ACCEPT"),
    ("V1 = πr²h", "ACCEPT"),
    ("mass = total volume ÷ 8", "WRONG_CLAIM"),
    ("mass = volume + 8", "WRONG_CLAIM"),
    ("total volume = V1 - V2", "WRONG_CLAIM"),
    ("total volume = πr1²h1 - πr2²h2", "WRONG_CLAIM"),
    ("volume = πr²", "WRONG_CLAIM"),
])
def test_relationships_in_words_are_checked_while_solving(line, verdict):
    assert _guided(INTRO + ["find both volumes with πr²h, add, × 8", line])[-1]["verdict"] == verdict
