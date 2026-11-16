"""NCERT Class 10 Ex 1.1 Q1 (prime factorisation) and Q2 (LCM and HCF): parts in any order, each number by
either method (repeated division or a factor tree)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.graph_loader import get_graph

client = TestClient(app)

Q1, Q2 = "g10-jemh101-ex-1-1-q1", "g10-jemh101-ex-1-1-q2"
Q1_INTRO = ["140, 156, 3825, 5005, 7429", "each number as a product of prime factors"]
Q2_INTRO = ["26 and 91, 510 and 92, 336 and 54", "the LCM and HCF of each pair"]
Q1_ALL = "140 = 2² × 5 × 7, 156 = 2² × 3 × 13, 3825 = 3² × 5² × 17, 5005 = 5 × 7 × 11 × 13, 7429 = 17 × 19 × 23"
Q1_REST = ["156 = 2² × 3 × 13", "3825 = 3² × 5² × 17", "5005 = 5 × 7 × 11 × 13", "7429 = 17 × 19 × 23"]


def _steps(problem, lines):
    sid = client.post("/api/v1/sessions/start", json={"problem_id": problem}).json()["session_id"]
    return [client.post(f"/api/v1/sessions/{sid}/step", json={"student_input": line}).json() for line in lines]


def test_both_problems_load_with_chapter_1_context():
    for pid in (Q1, Q2):
        meta = get_graph(pid).graph_meta
        assert meta.guided is True and meta.problem_context["chapter"] == "1"
        assert meta.problem_context["topic"] == "Real Numbers"
    assert get_graph(Q1).graph_meta.total_methods == 2


@pytest.mark.parametrize("line", ["3825 = 3 × 5² × 17", "3825 = 3² × 5 × 17"])
def test_q1_a_near_copy_of_the_answer_is_not_accepted(line):
    """The text is almost the accepted answer, but the product is wrong."""
    steps = _steps(Q1, Q1_INTRO + ["140 ÷ 2 = 70", "140 = 2² × 5 × 7", "156 = 2² × 3 × 13", line])
    assert steps[-1]["verdict"] == "WRONG_CLAIM" and steps[-1]["active_label"] == "(iii) 3825"


def test_q2_full_flow():
    steps = _steps(Q2, Q2_INTRO + [
        "26 = 2 × 13 and 91 = 7 × 13",                       # work at the plan step goes straight to the parts
        "HCF(26, 91) = 13", "LCM = 2 × 7 × 13 = 182", "182 × 13 = 2366 = 26 × 91",
        "510 = 2 × 3 × 5 × 17 and 92 = 2² × 23", "HCF = 2", "LCM = 23460", "23460 × 2 = 46920 and 510 × 92 = 46920",
        "336 = 2^4 × 3 × 7, 54 = 2 × 3^3", "HCF = 6", "LCM = 2⁴ × 3³ × 7 = 3024", "3024 × 6 = 18144 = 336 × 54",
        "(i) HCF = 13, LCM = 182 (ii) HCF = 2, LCM = 23460 (iii) HCF = 6, LCM = 3024"])
    assert all(s["verdict"] == "ACCEPT" for s in steps[:-1])
    assert steps[-1]["verdict"] == "CONCLUSION_RIGHT"


@pytest.mark.parametrize("line,verdict", [
    ("HCF = 13", "ACCEPT"),
    ("HCF(26, 91) = 13", "ACCEPT"),
    ("HCF = 12", "WRONG_ANSWER"),
    ("HCF = 26", "WRONG_ANSWER"),
])
def test_q2_hcf(line, verdict):
    assert _steps(Q2, Q2_INTRO + ["26 = 2 × 13 and 91 = 7 × 13", line])[-1]["verdict"] == verdict


def test_q2_hcf_in_brackets_is_read_as_a_name():
    """'HCF(510, 92) = 4': the 2 inside 92 must not pass the keyword check."""
    out = _steps(Q2, Q2_INTRO + ["26 = 2 × 13 and 91 = 7 × 13", "HCF = 13", "LCM = 182", "182 × 13 = 2366",
                                  "510 = 2 × 3 × 5 × 17 and 92 = 2² × 23", "HCF(510, 92) = 4"])[-1]
    assert out["verdict"] != "ACCEPT"


def test_q2_factorising_one_number_counts_and_asks_for_the_other():
    one, other = _steps(Q2, Q2_INTRO + ["26 = 2 × 13", "91 = 7 × 13"])[-2:]
    assert one["verdict"] == "WORKING" and "Now write 91 too" in one["feedback_message"]
    assert one["active_label"] == "(i) Factorise 26 and 91"
    assert other["verdict"] == "ACCEPT" and other["active_label"] == "(i) HCF of 26 and 91"


@pytest.mark.parametrize("line,verdict", [
    ("LCM = 182", "ACCEPT"),
    ("LCM = 183", "WRONG_ANSWER"),
    ("LCM = 2 × 7 × 13 = 183", "WRONG_CLAIM"),
])
def test_q2_lcm(line, verdict):
    steps = _steps(Q2, Q2_INTRO + ["26 = 2 × 13 and 91 = 7 × 13", "HCF = 13", line])
    assert steps[-1]["verdict"] == verdict


# ─── "Describe the Plan" (like Q6): complete, partial, misconception, no idea ─────────────────────────────
@pytest.mark.parametrize("plan", [
    "divide by the smallest prime again and again until all factors are prime",
    "make a factor tree: split into two factors and keep splitting until only primes",
])
def test_q1_a_complete_plan_opens_every_part(plan):
    out = _steps(Q1, Q1_INTRO + [plan])[-1]
    assert out["verdict"] == "ACCEPT" and out["choice"]["category"] == "correct" and out["active_label"] == "(i) 140"
    assert out["next_prompt"].startswith("Solve the parts in any order: (i) 140, (ii) 156, (iii) 3825")


def test_q1_partial_plan_gets_the_ladder_then_explains_the_given_step():
    steps = _steps(Q1, Q1_INTRO + ["divide 140 by 2", "keep going", "not sure", "no idea"])
    first, second, given, explained = steps[-4:]
    assert first["choice"]["concepts_found"] == ["C1"] and first["verdict"] == "PLAN_FEEDBACK"
    assert second["choice"]["concepts_found"] == ["C1", "C3"]
    assert given["choice"]["category"] == "explain" and given["active_label"] == "Explain the Plan"
    assert explained["verdict"] == "ACCEPT" and explained["active_label"] == "(i) 140"


@pytest.mark.parametrize("line", ["add prime numbers to make 140", "2 and 5", "divide 140 by 2"])
def test_q1_words_at_the_plan_are_never_taken_as_the_first_step(line):
    assert _steps(Q1, Q1_INTRO + [line])[-1]["verdict"] == "PLAN_FEEDBACK"


def test_q1_adding_is_a_misconception():
    out = _steps(Q1, Q1_INTRO + ["add prime numbers to make 140"])[-1]
    assert out["choice"]["category"] == "misconception"


def test_q1_no_idea_gets_k1_k2_k3_then_the_plan():
    steps = _steps(Q1, Q1_INTRO + ["i dont know", "2 and 5", "guide me", "no idea", "dont know"])
    assert [s["choice"]["concept_hint"]["id"] for s in steps[2:5]] == ["K1", "K2", "K3"]
    assert steps[5]["choice"]["category"] == "explain" and steps[6]["verdict"] == "ACCEPT"


def test_q2_complete_plan_opens_every_pair():
    plan = ("factorise both numbers into primes, HCF is the product of common primes with smallest power, "
            "LCM is the product of all primes with greatest power, then verify LCM × HCF equals the product")
    out = _steps(Q2, Q2_INTRO + [plan])[-1]
    assert out["choice"]["category"] == "correct" and out["active_label"] == "(i) Factorise 26 and 91"


def test_q2_partial_plan_keeps_progress_one_idea_at_a_time():
    steps = _steps(Q2, Q2_INTRO + ["find the prime factors of both numbers", "hcf uses the common primes"])
    assert steps[-2]["choice"]["concepts_found"] == ["C1"]
    assert steps[-1]["choice"]["concepts_found"] == ["C1", "C2"]
    assert steps[-1]["next_prompt"].startswith("And how do you get the LCM")


def test_q2_swapping_hcf_and_lcm_is_a_misconception():
    out = _steps(Q2, Q2_INTRO + ["factorise both, then lcm uses only the common primes"])[-1]
    assert out["choice"]["category"] == "misconception"


def test_q2_factorising_at_the_plan_starts_the_parts():
    out = _steps(Q2, Q2_INTRO + ["26 = 2 × 13 and 91 = 7 × 13"])[-1]
    assert out["verdict"] == "ACCEPT" and out["active_label"] == "(i) HCF of 26 and 91"


# ─── "I don't know what a prime number is" at any question: the term, then the next hint ─────────────────
PLAN_A = "divide by the smallest prime again and again until all factors are prime"


@pytest.mark.parametrize("problem,before,line,term", [
    (Q1, [], "i dont know what is prime factor", "A prime factor is"),
    (Q1, Q1_INTRO[:1], "what is a prime number?", "A prime number has exactly two factors"),
    (Q1, Q1_INTRO + [PLAN_A], "i dont know what a prime number is", "A prime number has exactly two factors"),
    (Q2, Q2_INTRO + ["26 = 2 × 13 and 91 = 7 × 13"], "I don't know what HCF means", "The HCF (highest common factor)"),
])
def test_dont_know_a_term_gets_its_definition_and_the_hint(problem, before, line, term):
    out = _steps(problem, before + [line])[-1]
    assert out["verdict"] == "DONT_KNOW"
    assert out["feedback_message"].startswith("That's fine. " + term) and out["hint"]


def test_prime_factor_is_one_term_not_prime_plus_factor():
    out = _steps(Q1, ["i dont know what is prime factor"])[-1]
    assert "A prime number has" not in out["feedback_message"] and "A factor of" not in out["feedback_message"]


def test_two_terms_get_two_definitions():
    out = _steps(Q2, Q2_INTRO + ["26 = 2 × 13 and 91 = 7 × 13", "HCF = 13", "what is lcm and what is a multiple?"])[-1]
    assert "The LCM (lowest" in out["feedback_message"] and "A multiple of" in out["feedback_message"]


def test_dont_know_uses_a_hint_level_and_is_never_called_wrong():
    first, second = _steps(Q1, Q1_INTRO + [PLAN_A, "i don't know", "still no idea"])[-2:]
    node = next(n for n in get_graph(Q1).nodes if n.id == "p1_answer")
    assert first["verdict"] == second["verdict"] == "DONT_KNOW"
    assert first["hint"] == node.hints[0] and second["hint"] == node.hints[1]
    assert "not the answer" not in first["feedback_message"]


def test_dont_know_with_a_number_is_still_an_answer():
    assert _steps(Q1, Q1_INTRO + [PLAN_A, "not sure, maybe 140 = 2 × 70"])[-1]["verdict"] != "DONT_KNOW"


def test_at_the_plan_the_definition_follows_thats_fine():
    out = _steps(Q1, Q1_INTRO + ["i dont know what is prime factor"])[-1]
    assert out["verdict"] == "PLAN_FEEDBACK"
    assert out["feedback_message"].startswith("That's fine. A prime factor is")


def test_glossary_definitions_never_use_the_questions_numbers():
    for pid in (Q1, Q2):
        meta = get_graph(pid).graph_meta
        asked = set(__import__("re").findall(r"\d+", meta.problem_text))
        for entry in meta.glossary:
            assert not set(__import__("re").findall(r"\d+", entry["definition"])) & (asked - {"1", "2", "3", "5"}), entry


# ─── Hints teach with other numbers: only the last hint (the answer) uses the question's numbers ─────────
import re as _re
from app.engine.tutor_engine import parse_step


def _teaching_hints(graph):
    """Every hint but the last of each question, the plan's ladder hints, K hints and misconception replies."""
    for n in graph.nodes:
        yield from ((n.id, h) for h in n.hints[:-1])
        for c in n.concepts_required:
            yield from ((n.id, h) for h in c.hints)
        yield from ((n.id, k.question) for k in n.concept_hints)
        yield from ((n.id, m.response) for m in n.misconceptions)


@pytest.mark.parametrize("pid", [Q1, Q2])
def test_hints_never_use_the_questions_numbers(pid):
    graph = get_graph(pid)
    known = set(_re.findall(r"\d+", graph.graph_meta.problem_text))
    for n in graph.nodes:
        known |= set(_re.findall(r"\d+", " ".join(n.accept) + " " + n.description))
    known = {k for k in known if int(k) >= 11}                # 2, 3, 5, 7 are every student's primes
    for node_id, hint in _teaching_hints(graph):
        assert not set(_re.findall(r"\d+", hint)) & known, (node_id, hint)


@pytest.mark.parametrize("pid", [Q1, Q2])
def test_every_worked_example_in_a_hint_is_true(pid):
    checked = 0
    for node_id, hint in _teaching_hints(get_graph(pid)):
        for part in _claims_in(hint):
            for claim in parse_step(part).claims:
                checked += 1
                assert claim.is_true is not False, (node_id, part)
    assert checked >= 15                                      # the examples really were read


def _claims_in(hint):
    """'Worked example: 60 ÷ 2 = 30, 30 ÷ 2 = 15, so 60 = 2² × 3 × 5.' → '60 ÷ 2 = 30', '30 ÷ 2 = 15', …"""
    text = _re.sub(r"(?i)(worked )?example:\s*|for \d+ and \d+,\s*", "", hint)
    for part in _re.split(r"[.?;]\s+|,\s*(?:so\s+|and\s+|or\s+|but\s+)?|\s+and\s+(?=[\dA-Z(])|\s+or\s+", text):
        part = _re.sub(r"\((?:\d+, )?\d+\)|^[A-Za-z ]*?(?=[\d(])", "", part).strip().rstrip(".")
        if "=" in part:
            yield part


def test_a_false_worked_example_would_be_caught():
    claims = [c for part in _claims_in("Worked example: 60 ÷ 2 = 31, 31 ÷ 2 = 15.") for c in parse_step(part).claims]
    assert claims and claims[0].is_true is False



# ─── Parts: "(ii) 156" picks a part; any order; each number by either method; working is optional ─────────
def _q1(lines):
    return _steps(Q1, Q1_INTRO + [PLAN_A] + lines)


@pytest.mark.parametrize("line,message", [
    ("3825/5", "Right: 3825 ÷ 5 = 765. Keep going: which prime divides 765?"),     # the student's own case
    ("3825 ÷ 5 = 765", "Right: 3825 ÷ 5 = 765."),
    ("3825 = 25 × 153", "Right: 3825 = 25 × 153. Now break 25 and 153 into primes."),
    ("153 = 9 × 17", "Now break 9 into primes."),                                   # a factor of 3825
])
def test_q1_a_correct_division_or_split_is_working(line, message):
    out = _q1(["(iii)", line])[-1]
    assert out["verdict"] == "WORKING" and message in out["feedback_message"]
    assert out["active_label"] == "(iii) 3825"


@pytest.mark.parametrize("line,message", [
    ("3825 ÷ 2 = 1912", "3825 ÷ 2 is not a whole number, so 2 is not a factor of 3825."),
    ("3825 ÷ 5 = 755", "3825 ÷ 5 = 765, not 755."),
    ("3825 = 25 × 135", "25 × 135 = 3375, not 3825."),
    ("3825 = 1 × 3825", "Use factors bigger than 1"),
])
def test_q1_a_wrong_division_or_split_is_a_mistake(line, message):
    out = _q1(["(iii)", line])[-1]
    assert out["verdict"] == "WRONG_CLAIM" and message in out["feedback_message"]


def test_q1_each_number_by_either_method_in_any_order():
    steps = _q1(["(iii) 3825", "3825/5", "765 ÷ 5 = 153", "153 = 9 × 17", "3825 = 3² × 5² × 17",   # division, tree
                 "(ii) 156 = 12 × 13", "12 = 4 × 3", "156 = 2 × 2 × 3 × 13",                       # tree
                 "(i) 140 ÷ 2 = 70", "140 = 2² × 5 × 7",                                          # division
                 "(v) 7429 = 17 × 19 × 23", "(iv) 5005 = 5 × 7 × 11 × 13", Q1_ALL])
    assert [s["verdict"] for s in steps[3:]] == (
        ["PART"] + ["WORKING"] * 3 + ["ACCEPT"] + ["WORKING"] * 2 + ["ACCEPT"] + ["WORKING", "ACCEPT"]
        + ["ACCEPT", "ACCEPT", "CONCLUSION_RIGHT"])
    assert steps[-1]["completed"]


def test_q1_a_label_picks_its_part_and_lines_without_one_stay_there():
    picked, line = _q1(["(iv) 5005", "5005 ÷ 5 = 1001"])[-2:]
    assert picked["verdict"] == "PART" and picked["active_label"] == "(iv) 5005"
    assert picked["next_prompt"] == "(iv) Express 5005 as a product of its prime factors."
    assert line["verdict"] == "WORKING" and line["active_label"] == "(iv) 5005"


@pytest.mark.parametrize("label", ["(ii)", "ii)", "(ii) 156", "part ii", "Part (ii)"])
def test_q1_label_forms(label):
    assert _q1([label])[-1]["active_label"] == "(ii) 156"


def test_q1_a_line_for_another_part_says_which_part():
    out = _q1(["3825/5"])[-1]                                  # solving (i) 140
    assert out["verdict"] == "PART" and "(iii) 3825" in out["feedback_message"] and "(iii)" in out["feedback_message"]


def test_q1_a_done_part_says_so_and_lists_the_rest():
    steps = _q1(["(ii) 156 = 2² × 3 × 13", "(ii)"])
    assert steps[-2]["next_prompt"].startswith("Part (ii) 156 is done. Still to do: (i) 140, (iii) 3825")
    assert steps[-1]["verdict"] == "PART" and "already done" in steps[-1]["feedback_message"]


def test_q1_hints_follow_the_method_used_for_that_number():
    graph_node = next(n for n in get_graph(Q1).nodes if n.id == "p3_answer")
    by_division = _q1(["(iii)", "3825 ÷ 5 = 765", "765 ÷ 5 = 150"])[-1]                  # a wrong division
    by_tree = _q1(["(iii)", "3825 = 25 × 153", "153 = 9 × 18"])[-1]                    # a wrong split
    assert by_division["verdict"] == by_tree["verdict"] == "WRONG_CLAIM"
    assert by_division["hint"] == graph_node.hints_by_method["m1"][0]
    assert by_tree["hint"] == graph_node.hints_by_method["m2"][0]


def test_q1_hint_levels_are_kept_per_number():
    steps = _q1(["140 = 2 × 5", "(ii)", "156 = 2 × 3", "(i)", "140 = 2 × 5 × 5"])
    p1 = next(n for n in get_graph(Q1).nodes if n.id == "p1_answer")
    tree = p1.hints_by_method["m2"]                            # "140 = 2 × 5" is a (wrong) split: factor-tree hints
    assert steps[3]["hint"] == tree[0]
    assert steps[-1]["hint"] == tree[1]                        # (i)'s second wrong answer: its second hint


def test_q2_pairs_in_any_order():
    steps = _steps(Q2, Q2_INTRO + ["(iii) 336 and 54", "336 ÷ 2 = 168", "336 = 2^4 × 3 × 7", "54 = 2 × 3³",
                                   "HCF = 6", "LCM = 3024", "3024 × 6 = 18144 = 336 × 54", "(i)"])
    assert steps[2]["active_label"] == "(iii) Factorise 336 and 54"
    assert [s["verdict"] for s in steps[3:8]] == ["WORKING", "WORKING", "ACCEPT", "ACCEPT", "ACCEPT"]
    assert steps[8]["next_prompt"].startswith("Part (iii) 336 and 54 is done. Still to do: (i) 26 and 91")
    assert steps[-1]["active_label"] == "(i) Factorise 26 and 91"


def test_q2_a_pair_remembers_where_it_was():
    steps = _steps(Q2, Q2_INTRO + ["(i) 26 = 2 × 13 and 91 = 7 × 13", "HCF = 13", "(ii)", "(i)"])
    assert steps[-1]["active_label"] == "(i) LCM of 26 and 91"


def test_every_part_lists_its_questions_and_numbers():
    for pid, count in ((Q1, 5), (Q2, 3)):
        graph = get_graph(pid)
        nodes = {n.id for n in graph.nodes}
        parts = graph.graph_meta.parts
        assert len(parts) == count and all(set(p["nodes"]) <= nodes for p in parts)
        assert all(str(n) in graph.graph_meta.problem_text for p in parts for n in p["numbers"])


def test_q1_graph_shows_both_methods_for_every_number():
    graph = get_graph(Q1)
    ids = {n.id for n in graph.nodes}
    for k in range(1, 6):
        assert {f"m1_p{k}", f"m2_p{k}", f"m1_p{k}_s1", f"m2_p{k}_s1", f"p{k}_answer"} <= ids
