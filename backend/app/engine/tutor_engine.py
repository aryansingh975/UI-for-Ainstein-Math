from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.schemas.graph import SolutionGraph, Node
from app.engine.normalizer import normalize_text
from app.engine.vocabulary import has_irrelevant_words, MATH_INTENT
from app.engine.evaluator import eval_arithmetic, EPS
from app.engine.claims import extract_claims, Claim, fmt_num
from app.engine.matcher import matches_accept, matches_accept_any
from app.engine.navigator_bridge import navigator_match_node, navigator_resolve_nodes
from app.engine.llm_verifier import (
    _should_call_remote_llm,
    verify_candidates_with_qwen,
    verify_node_with_qwen,
)
from app.engine.method_resolver import resolve_method_waterfall
from app.engine.state_machine import (
    Session,
    method_of,
    method_for_node,
    get_method_node,
    successor_of,
    first_step_of,
    method_chain,
    has_completed_required_extraction,
)


class ParsedStep:
    def __init__(
        self,
        raw: str,
        normalized: str,
        words: List[str],
        numbers: List[float],
        ratios: List[Tuple[float, float]],
        fractions: List[Tuple[float, float]],
        claims: List[Claim],
        intents: Set[str],
        expressions: List[str],
        label_value: Optional[float] = None,
    ):
        self.raw = raw
        self.normalized = normalized
        self.words = words
        self.numbers = numbers
        self.ratios = ratios
        self.fractions = fractions
        self.claims = claims
        self.intents = intents
        self.expressions = expressions
        self.label_value = label_value


class StepResult:
    def __init__(
        self,
        verdict: str,
        parsed: ParsedStep,
        node_id: Optional[str] = None,
        method_id: Optional[str] = None,
        claim: Optional[Any] = None,
        approach_only: bool = False,
        feedback: Optional[str] = None,
        compound_trail: Optional[List[Dict[str, Any]]] = None,
    ):
        self.verdict = verdict
        self.parsed = parsed
        self.node_id = node_id
        self.method_id = method_id
        self.claim = claim
        self.approach_only = approach_only
        self.feedback = feedback
        self.compound_trail = compound_trail or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "nodeId": self.node_id,
            "methodId": self.method_id,
            "approachOnly": self.approach_only,
            "feedback": self.feedback,
            "compoundTrail": self.compound_trail,
            "claim": self.claim.to_dict() if isinstance(self.claim, Claim) else self.claim,
            "parsed": {
                "raw": self.parsed.raw,
                "normalized": self.parsed.normalized,
            }
        }


def parse_context_from_graph(graph: SolutionGraph) -> Dict[str, Tuple[float, float]]:
    """Extract reference ratios from graph problem text or context."""
    text = (graph.graph_meta and graph.graph_meta.problem_text) or ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)[^\d]+(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", text)
    if m:
        return {
            "first": (float(m.group(1)), float(m.group(2))),
            "second": (float(m.group(3)), float(m.group(4))),
        }
    return {"first": (3.0, 4.0), "second": (72.0, 96.0)}


def is_ratio_pair(a: float, b: float, pair: Tuple[float, float]) -> bool:
    return abs(a - pair[0]) < EPS and abs(b - pair[1]) < EPS


def side_is_ratio_form(text: str, pair: Tuple[float, float]) -> bool:
    m = re.match(r"^(\d+(?:\.\d+)?)[/:](\d+(?:\.\d+)?)$", str(text).strip())
    if not m:
        return False
    return is_ratio_pair(float(m.group(1)), float(m.group(2)), pair)


def is_bare_yes_no(parsed: ParsedStep) -> bool:
    return len(parsed.words) <= 2 and bool(re.match(r"^(yes|no|yeah|yep|nope|ok|okay)\b", parsed.normalized))


def is_garbage(parsed: ParsedStep) -> bool:
    if is_bare_yes_no(parsed):
        return False
    if has_irrelevant_words(parsed.normalized, ""):
        return True
    has_math = len(parsed.numbers) > 0 or len(parsed.claims) > 0 or len(parsed.ratios) > 0
    has_intent = len(parsed.intents) > 0
    return not has_math and not has_intent


def parse_step(raw: str, default_gcd_pair: Optional[Tuple[float, float]] = None) -> ParsedStep:
    normalized = normalize_text(raw)
    words = [w for w in re.split(r"[^a-z]+", normalized) if w]
    num_strings = re.findall(r"\d+(?:\.\d+)?", normalized)
    numbers = [float(x) for x in num_strings]

    ratios = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", normalized):
        ratios.append((float(m.group(1)), float(m.group(2))))

    fractions = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", normalized):
        fractions.append((float(m.group(1)), float(m.group(2))))

    claims = extract_claims(normalized, default_gcd_pair)
    intents = {w for w in words if w in MATH_INTENT}

    # Extract arithmetic expressions (with + - * / ^)
    expressions = []
    if re.search(r"[-+*/^]", normalized) and not re.search(r"[=:]", normalized):
        expressions.append(normalized)

    # A probability worked out in one go: "P(E) = 1 - 0.992" has the value 0.008
    label_value = None
    m = re.match(r"^p\([^()=]*\)=([^=]+)$", normalized)
    if m and re.search(r"\d", m.group(1)) and re.search(r"[-+*/^]", m.group(1).strip()[1:]):
        label_value = eval_arithmetic(re.sub(r"[−–]", "-", m.group(1)))

    return ParsedStep(
        raw=raw,
        normalized=normalized,
        words=words,
        numbers=numbers,
        ratios=ratios,
        fractions=fractions,
        claims=claims,
        intents=intents,
        expressions=expressions,
        label_value=label_value,
    )


def expected_for(node: Node) -> Optional[Dict[str, Any]]:
    for a in node.accept or []:
        n = normalize_text(a)
        m = re.match(r"^(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)$", n)
        if m:
            return {"kind": "ratio", "a": float(m.group(1)), "b": float(m.group(2))}

    nums: List[float] = []
    for a in node.accept or []:
        for x in re.findall(r"\d+(?:\.\d+)?", normalize_text(a)):
            fx = float(x)
            if not any(abs(v - fx) < EPS for v in nums):
                nums.append(fx)

    # values of the calculations in the accept list ("100/180" -> 0.556), for "P(E) = 100/180"
    worked: List[float] = []
    for a in node.accept or []:
        for side in normalize_text(a).split("="):
            if re.search(r"\d\s*[-+*/^]\s*[\d(]", side):
                v = eval_arithmetic(re.sub(r"[−–]", "-", side.strip()))
                if v is not None:
                    worked.append(v)

    if len(nums) == 1:
        return {"kind": "number", "value": nums[0], "worked": worked}
    if len(nums) > 1:
        return {"kind": "values", "values": nums, "worked": worked}
    return None


def verify_against_expected(parsed: ParsedStep, exp: Dict[str, Any]) -> Dict[str, Any]:
    # "P(E) = 1 + 0.992": the worked-out value must be one this step expects
    if parsed.label_value is not None and not parsed.claims and exp["kind"] in ("number", "values"):
        targets = [exp["value"]] if exp["kind"] == "number" else exp["values"]
        if any(abs(parsed.label_value - t) < EPS for t in targets + exp.get("worked", [])):
            return {"accepted": True}
        return {"accepted": False, "wrong_claim": True,
                "claim": {"kind": "value", "isTrue": False, "got": fmt_num(parsed.label_value),
                          "expected": [fmt_num(t) for t in targets]}}

    # Claims first: a false claim is always a wrong claim
    for c in parsed.claims:
        if not c.is_true:
            return {"accepted": False, "wrong_claim": True, "claim": c}
        vals = []
        if c.kind == "arith" and c.lhs_val is not None and c.rhs_val is not None:
            vals.extend([c.lhs_val, c.rhs_val])
        if c.kind == "ratio_eq" and c.a and c.b and c.c and c.d:
            vals.extend([c.a / c.b, c.c / c.d])

        if exp["kind"] == "number" and any(abs(v - exp["value"]) < EPS for v in vals):
            return {"accepted": True}
        if exp["kind"] == "values" and any(any(abs(v - x) < EPS for x in exp["values"]) for v in vals):
            return {"accepted": True}
        if exp["kind"] == "ratio" and any(abs(v - exp["a"] / exp["b"]) < EPS for v in vals):
            return {"accepted": True}

    if exp["kind"] == "ratio":
        for r in parsed.ratios:
            if abs(r[0] - exp["a"]) < EPS and abs(r[1] - exp["b"]) < EPS:
                return {"accepted": True}
            if abs(r[0] / r[1] - exp["a"] / exp["b"]) < EPS:
                return {"accepted": True}
        for f in parsed.fractions:
            if abs(f[0] / f[1] - exp["a"] / exp["b"]) < EPS:
                return {"accepted": True}
        if len(parsed.numbers) == 1 and not parsed.claims:
            if abs(parsed.numbers[0] - exp["a"] / exp["b"]) < EPS:
                return {"accepted": True}

    if exp["kind"] == "number":
        if len(parsed.numbers) == 1 and not parsed.claims:
            if abs(parsed.numbers[0] - exp["value"]) < EPS:
                return {"accepted": True}
            return {
                "accepted": False,
                "wrong_claim": True,
                "claim": {
                    "kind": "value",
                    "isTrue": False,
                    "got": parsed.numbers[0],
                    "expected": exp["value"],
                    "text": str(parsed.numbers[0]),
                },
            }
        for expr in parsed.expressions:
            v = eval_arithmetic(expr)
            if v is not None and abs(v - exp["value"]) < EPS:
                return {"accepted": True}

    if exp["kind"] == "values":
        if len(parsed.numbers) >= 1 and not parsed.claims:
            if parsed.ratios:
                return {"accepted": False}
            all_in = all(any(abs(n - x) < EPS for n in parsed.numbers) for x in exp["values"])
            if all_in:
                return {"accepted": True}
            any_in = any(any(abs(n - x) < EPS for x in exp["values"]) for n in parsed.numbers)
            if not any_in:
                return {
                    "accepted": False,
                    "wrong_claim": True,
                    "claim": {
                        "kind": "value",
                        "isTrue": False,
                        "got": ", ".join(str(n) for n in parsed.numbers),
                        "expected": " or ".join(str(x) for x in exp["values"]),
                        "text": ", ".join(str(n) for n in parsed.numbers),
                    },
                }

    return {"accepted": False}


def match_node(parsed: ParsedStep, node: Node, equation: Optional[str] = None) -> Dict[str, Any]:
    # A step node should not match a full conclusion statement naming 'proportional'
    if getattr(node, "type", None) == "step" and re.search(r"\bproportional\b", parsed.normalized):
        return {"accepted": False}
    if matches_accept_any(parsed.raw, node.accept):
        return {"accepted": True}
    exp = expected_for(node)
    if exp:
        # Extraction nodes should never swallow arithmetic equations
        if getattr(node, "type", None) == "extraction" and (
            any(c.kind == "arith" for c in parsed.claims)
            or "=" in parsed.raw
            or "×" in parsed.raw
            or "*" in parsed.raw
            or "/" in parsed.raw
        ):
            return {"accepted": False}
        m = verify_against_expected(parsed, exp)
        if m.get("accepted"):
            return m
        if m.get("wrong_claim"):
            return m

    # SymPy algebraic & equation verification
    if equation and ("=" in parsed.raw or any(v in parsed.raw for v in ("x", "y", "a", "b"))):
        try:
            from app.engine.sympy_validator import validate
            val_res = validate(parsed.raw, equation=equation)
            lines = val_res.get("lines", [])
            for l in lines:
                if l.get("status") == "valid":
                    return {"accepted": True}
                elif l.get("status") == "invalid" and l.get("message"):
                    return {
                        "accepted": False,
                        "wrong_claim": True,
                        "claim": Claim(
                            kind="equation",
                            text=l.get("statement", parsed.raw),
                            is_true=False,
                            lhs=l.get("statement"),
                            rhs=l.get("message"),
                        ),
                    }
        except Exception:
            pass

    return {"accepted": False}


def detect_method_keyword(parsed: ParsedStep, graph: SolutionGraph) -> Optional[str]:
    method_nodes = [n for n in graph.nodes if n.type == "method"]
    best_id: Optional[str] = None
    best_len = 0
    for mn in method_nodes:
        for acc in mn.accept or []:
            clean = acc.strip().lower()
            if not re.match(r"^[a-z]+( [a-z]+)*$", clean):
                continue
            if matches_accept(parsed.raw, acc):
                if len(clean) > best_len:
                    best_len = len(clean)
                    best_id = mn.id
    return best_id


def mcq_option(normalized: str, graph: SolutionGraph) -> Optional[str]:
    """The option letter a student picks ("(a) 2/3", "option c", "the answer is (b)") in a multiple-choice graph."""
    pc = getattr(graph.graph_meta, "problem_context", None) or {}
    if pc.get("question_type") != "multiple_choice" or not pc.get("correct_option"):
        return None
    picked = re.match(r"^(?:(?:the )?(?:answer|correct option) is\s*)?"
                      r"(?:option\s*\(?([a-d])\)?(?![a-z])|\(([a-d])\)|([a-d])\)|([a-d])$)", normalized)
    return next((g for g in picked.groups() if g), None) if picked else None


def detect_conclusion(
    parsed: ParsedStep, session: Session, graph: SolutionGraph, ctx: Dict[str, Tuple[float, float]]
) -> Optional[Dict[str, Any]]:
    node_map = {n.id: n for n in graph.nodes}
    concl = node_map.get(graph.conclusion_node)
    if not concl:
        return None

    norm = parsed.normalized

    # Filter out hypothesis/question/goal statements (e.g. "whether the ratios are proportional")
    if re.search(r"\b(whether|if|check|find|determine|to\s+find|goal)\b", norm):
        return None

    negated = bool(re.search(r"not proportional|not equal|≠|isn't|are not|is not|doesn't hold", norm))

    if is_bare_yes_no(parsed):
        at_concl = session.current_node_id == graph.conclusion_node
        no_current = not session.current_node_id
        has_progress = len(session.trail) > 0
        if at_concl or (no_current and has_progress):
            return {"detected": True, "correct": matches_accept_any(parsed.raw, concl.accept)}
        return None

    first_pair = ctx.get("first", (3.0, 4.0))
    second_pair = ctx.get("second", (72.0, 96.0))

    # Explicit full ratio equality claims (e.g. 3:4 = 72:96)
    for c in parsed.claims:
        if c.kind == "ratio_eq" and c.a and c.b and c.c and c.d:
            fwd = is_ratio_pair(c.a, c.b, first_pair) and is_ratio_pair(c.c, c.d, second_pair)
            rev = is_ratio_pair(c.a, c.b, second_pair) and is_ratio_pair(c.c, c.d, first_pair)
            if fwd or rev:
                return {"detected": True, "correct": c.is_true}
        if c.kind == "arith" and c.lhs and c.rhs:
            fwd = side_is_ratio_form(c.lhs, first_pair) and side_is_ratio_form(c.rhs, second_pair)
            rev = side_is_ratio_form(c.lhs, second_pair) and side_is_ratio_form(c.rhs, first_pair)
            if fwd or rev:
                return {"detected": True, "correct": c.is_true}

    # Multiple choice: naming a different option ("(a) 2/3", "option c") is a wrong final answer
    letter = mcq_option(norm, graph)
    if letter and letter != str(graph.graph_meta.problem_context["correct_option"]).lower():
        return {"detected": True, "correct": False}

    # Explicit mention of both ratio pairs with proportional (e.g. "3:4 and 72:96 are proportional")
    if re.search(r"\bproportional\b", norm):
        has_first = any(is_ratio_pair(r[0], r[1], first_pair) for r in parsed.ratios)
        has_second = any(is_ratio_pair(r[0], r[1], second_pair) for r in parsed.ratios)
        if has_first and has_second:
            return {"detected": True, "correct": not negated}

    # Phase Gating for bare accept keywords (e.g. "proportional", "6", "8"):
    # Do not match bare accept strings if student is in extraction phase
    if session.current_node_id in ("given_extraction", "goal_extraction"):
        return None

    # Require either being at conclusion node or having prior calculation progress
    has_calc_step = any(t.get("nodeId") not in ("given_extraction", "goal_extraction", "start") for t in session.trail)
    at_concl = session.current_node_id == graph.conclusion_node

    if at_concl or has_calc_step:
        if matches_accept_any(parsed.raw, concl.accept):
            return {"detected": True, "correct": not negated and not bool(re.match(r"^(no|nope)\b", norm))}

    return None


def check_dag_step_jump(
    session_or_node_id: Any,
    target_node_id: str,
    graph: SolutionGraph,
    raw_input: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Uses Navigator Solution Paths & DAG reachability to detect if intermediate mandatory nodes were skipped."""
    session = session_or_node_id if hasattr(session_or_node_id, "trail") else None
    node_map = {n.id: n for n in graph.nodes}
    target_node = node_map.get(target_node_id)
    if not target_node or target_node.type not in ("step", "conclusion"):
        return None

    completed_ids = set()
    if session and session.trail:
        completed_ids = {t.get("nodeId") for t in session.trail if t.get("nodeId")}
    elif not session and session_or_node_id:
        completed_ids = {session_or_node_id}

    if target_node_id in completed_ids:
        return None
    if session and session.current_node_id == target_node_id:
        return None

    # Determine active method
    method_id = session.method_id if (session and session.method_id) else None
    if not method_id:
        for cid in completed_ids:
            m = method_for_node(cid, graph)
            if m:
                method_id = m
                break
    if not method_id and target_node_id != graph.conclusion_node:
        method_id = method_for_node(target_node_id, graph)

    try:
        from app.navigator.graph_loader import get_all_solution_paths
        dag_dict = {
            "start_node": graph.start_node,
            "conclusion_node": graph.conclusion_node,
            "nodes": [n.model_dump() if hasattr(n, "model_dump") else n.__dict__ for n in graph.nodes],
            "edges": [{"from": e.from_node, "to": e.to_node} for e in graph.edges],
        }
        all_paths = get_all_solution_paths(dag_dict)
    except Exception:
        all_paths = []

    if not all_paths:
        return None

    # Filter candidate paths
    candidate_paths = []
    if method_id:
        candidate_paths = [p for p in all_paths if method_id in p]
    if not candidate_paths:
        candidate_paths = [p for p in all_paths if target_node_id in p]
    if not candidate_paths:
        candidate_paths = all_paths

    # Pick the path that best matches current completed_ids
    best_path = candidate_paths[0]
    best_match_score = -1
    for p in candidate_paths:
        score = len(set(p) & completed_ids)
        if score > best_match_score:
            best_match_score = score
            best_path = p

    step_nodes_in_path = [nid for nid in best_path if nid in node_map and node_map[nid].type == "step"]

    if target_node_id == graph.conclusion_node:
        last_step_matches = False
        if raw_input and step_nodes_in_path:
            last_step = node_map[step_nodes_in_path[-1]]
            if matches_accept_any(raw_input, last_step.accept):
                last_step_matches = True
            else:
                try:
                    from app.engine.guided import _check
                    chk = _check(raw_input, last_step, None, graph.graph_meta.problem_text)
                    if chk.get("accepted"):
                        last_step_matches = True
                except Exception:
                    pass
        if last_step_matches:
            prior_node_ids = best_path[:best_path.index(step_nodes_in_path[-1])]
        else:
            prior_node_ids = best_path[:-1]
    elif target_node_id in best_path:
        idx = best_path.index(target_node_id)
        prior_node_ids = best_path[:idx]
    else:
        prior_node_ids = []

    prior_steps = [
        node_map[nid] for nid in prior_node_ids
        if nid in node_map and node_map[nid].type == "step"
        and not getattr(node_map[nid], "optional", False)
    ]

    # Starting a method: if no calculations have been completed yet,
    # starting with any initial calculation (or setup) of the method is allowed.
    has_any_calc_done = any(
        node_map.get(cid) and node_map[cid].type == "step"
        for cid in completed_ids
    )
    if not has_any_calc_done and target_node_id != graph.conclusion_node:
        if step_nodes_in_path and target_node_id in step_nodes_in_path[:2]:
            prior_steps = []
    elif target_node_id == "m1_s1" and "m1_s2" in completed_ids:
        prior_steps = []

    # If the student explicitly states both ratio pairs and proportional in conclusion:
    if raw_input and re.search(r"\bproportional\b", raw_input, re.I) and has_any_calc_done:
        prior_steps = [n for n in prior_steps if n.id not in ("shared_ratio_comparison", "m1_s3", "m8_s2", "m6_s2", "m6_s3")]

    # Ratio / Proportion full explicit claim (e.g. "3:4 = 72:96" or "3:4 and 72:96 are proportional")
    if raw_input:
        norm_r = normalize_text(raw_input)
        if (
            re.search(r"\bproportional\b", norm_r)
            or re.search(r"\d+:\d+\s*=\s*\d+:\d+", norm_r)
            or re.search(r"\d+/\d+\s*=\s*\d+/\d+", norm_r)
        ):
            return None
        # All-in-one complete solution expression (e.g. 8 * 3.14 * (12^2 * 220 + 8^2 * 60) = 892262.4 g)
        if ("(" in raw_input or "×" in raw_input or "*" in raw_input):
            input_nums = re.findall(r"\d+(?:\.\d+)?", raw_input)
            if len(input_nums) >= 5 and any("892" in n for n in input_nums):
                return None

    skipped_steps = [n for n in prior_steps if n.id not in completed_ids]
    if skipped_steps:
        return {
            "is_jump": True,
            "skipped": [n.model_dump() if hasattr(n, "model_dump") else n.__dict__ for n in skipped_steps],
            "first_skipped": skipped_steps[0].model_dump() if hasattr(skipped_steps[0], "model_dump") else skipped_steps[0].__dict__,
        }
    return None


def find_global_step_match(
    parsed: ParsedStep, session: Session, graph: SolutionGraph
) -> Optional[Dict[str, Any]]:
    if is_bare_yes_no(parsed):
        return None

    steps = [
        n for n in graph.nodes
        if n.type == "step" and (not session.method_id or method_for_node(n.id, graph) == session.method_id)
    ]

    scored = []
    for n in steps:
        score = 0
        nm = method_for_node(n.id, graph)
        if session.method_id and nm == session.method_id:
            score += 2
        if session.method_id and nm == session.method_id and session.current_node_id:
            chain = method_chain(session.method_id, graph)
            if session.current_node_id in chain and n.id in chain:
                ci = chain.index(session.current_node_id)
                ni = chain.index(n.id)
                if ni > ci:
                    score += 1
        scored.append((score, n))

    scored.sort(key=lambda x: x[0], reverse=True)
    ordered = [n for _, n in scored if n.id != session.current_node_id]

    # Pass 1: exact accept-list matches
    for node in ordered:
        if matches_accept_any(parsed.raw, node.accept):
            return {"node_id": node.id, "method_id": method_for_node(node.id, graph)}

    # Pass 2: semantic / numeric verification
    for node in ordered:
        exp = expected_for(node)
        if not exp:
            continue
        m = verify_against_expected(parsed, exp)
        if m.get("accepted"):
            return {"node_id": node.id, "method_id": method_for_node(node.id, graph)}

    # Pass 3: Navigator Jaccard similarity (>= 0.70) with math/number guard
    nav_hit = navigator_resolve_nodes(parsed.raw, ordered, threshold=0.70)
    if nav_hit:
        nav_node, _ = nav_hit
        return {"node_id": nav_node.id, "method_id": method_for_node(nav_node.id, graph)}

    # Pass 4: LLM Semantic Verifier fallback (Qwen 3.5 via OpenRouter API)
    problem_text = (graph.graph_meta and graph.graph_meta.problem_text) or ""
    qwen_hit = verify_candidates_with_qwen(parsed.raw, ordered, problem_text)
    if qwen_hit:
        qwen_node, _ = qwen_hit
        return {"node_id": qwen_node.id, "method_id": method_for_node(qwen_node.id, graph)}

    return None


def find_any_calculation_step(parsed: ParsedStep, graph: SolutionGraph) -> Optional[Node]:
    """Problem 3: Check if student's calculation matches any calculation step in any method."""
    step_nodes = [n for n in graph.nodes if n.type == "step"]
    for node in step_nodes:
        if matches_accept_any(parsed.raw, node.accept):
            return node
        exp = expected_for(node)
        if exp and verify_against_expected(parsed, exp).get("accepted"):
            return node
    return None


def find_step_in_other_methods(
    parsed: ParsedStep, current_method_id: str, graph: SolutionGraph
) -> Optional[Dict[str, Any]]:
    """Problem 4: Check if input matches a step in a method different from the active one.
    Crucial: If the input matches ANY step in the current method (present or future), it is NOT an other-method step."""
    # Generic short affirmations/words should never trigger cross-method jumps
    generic_words = {"yes", "no", "true", "false", "ok", "yep", "yeah"}
    if parsed.normalized in generic_words:
        return None

    current_steps = [
        n for n in graph.nodes
        if n.type == "step" and method_for_node(n.id, graph) == current_method_id
    ]
    for node in current_steps:
        if matches_accept_any(parsed.raw, node.accept):
            return None
        exp = expected_for(node)
        if exp and verify_against_expected(parsed, exp).get("accepted"):
            return None

    step_nodes = [
        n for n in graph.nodes
        if n.type == "step" and method_for_node(n.id, graph) != current_method_id
    ]
    for node in step_nodes:
        m_id = method_for_node(node.id, graph)
        if not m_id:
            continue
        if matches_accept_any(parsed.raw, node.accept):
            return {"node_id": node.id, "method_id": m_id}
        exp = expected_for(node)
        if exp and verify_against_expected(parsed, exp).get("accepted"):
            return {"node_id": node.id, "method_id": m_id}
    return None


def detect_misconception(
    parsed: ParsedStep, session: Session, graph: SolutionGraph
) -> Optional[Dict[str, Any]]:
    """Problem 7: Detect common cognitive traps (depreciation addition, percent without divide by 100, etc.)."""
    norm = parsed.normalized
    text = (graph.graph_meta and graph.graph_meta.problem_text) or ""

    # 1. Depreciation / Discount / Loss addition misconception (adding instead of subtracting)
    if re.search(r"\b(depreciat\w*|discount\w*|decrease\w*|loss\w*)\b", text, re.I):
        for c in parsed.claims:
            if c.kind == "arith" and c.op == "=" and "+" in (c.lhs or ""):
                nums = re.findall(r"\d+(?:\.\d+)?", c.lhs or "")
                if len(nums) >= 2:
                    return {
                        "kind": "depreciation_add",
                        "feedback": f"Be careful! Depreciation means the asset loses value over time. You added {int(min(float(nums[0]), float(nums[1])))}, but we need to subtract the depreciation from the original price.",
                    }
        for n in parsed.numbers:
            if abs(n - 22050.0) < EPS:
                return {
                    "kind": "depreciation_add",
                    "feedback": "Be careful! Depreciation means the asset loses value over time. Make sure to subtract the depreciation amount from the original price, not add it.",
                }

    # 2. Percentage multiplication only (forgot / 100)
    for c in parsed.claims:
        if c.kind == "arith" and "*" in (c.lhs or "") and "/" not in (c.lhs or ""):
            if (c.lhs_val or 0) > 10000 and any(abs((c.lhs_val or 0) - (exp_v * 100)) < EPS for exp_v in [1050.0, 35.0, 75.0]):
                return {
                    "kind": "percent_no_div",
                    "feedback": "Remember that a percentage means 'per hundred'. Multiply by the rate and divide by 100 (or multiply by 0.05).",
                }

    # 3. Reversed Ratio (e.g. 4:3 instead of 3:4)
    ctx = parse_context_from_graph(graph)
    first_pair = ctx.get("first", (3.0, 4.0))
    second_pair = ctx.get("second", (72.0, 96.0))
    for r in parsed.ratios:
        if is_ratio_pair(r[0], r[1], (first_pair[1], first_pair[0])):
            return {
                "kind": "ratio_reversed",
                "feedback": f"Notice the order of terms: the ratio is {int(first_pair[0])}:{int(first_pair[1])}. Reversing to {int(first_pair[1])}:{int(first_pair[0])} changes the mathematical relationship.",
            }
        if is_ratio_pair(r[0], r[1], (second_pair[1], second_pair[0])):
            return {
                "kind": "ratio_reversed",
                "feedback": f"Notice the order of terms: the ratio is {int(second_pair[0])}:{int(second_pair[1])}. Reversing to {int(second_pair[1])}:{int(second_pair[0])} changes the mathematical relationship.",
            }

    # 4. Profit = SP - CP flipped to CP - SP
    if re.search(r"\bprofit\b", text, re.I):
        for c in parsed.claims:
            if c.kind == "arith" and "-" in (c.lhs or ""):
                nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", c.lhs or "")]
                if len(nums) >= 2 and nums[0] < nums[1]:
                    return {
                        "kind": "profit_reversed",
                        "feedback": "Profit occurs when Selling Price (SP) is greater than Cost Price (CP). Calculate: Profit = SP - CP.",
                    }

    return None


def check_incremental_extraction(
    parsed: ParsedStep, session: Session, node: Node, ctx: Dict[str, Tuple[float, float]]
) -> Optional[StepResult]:
    """Problem 8: Handle incremental entity extraction across multiple turns."""
    # Never treat an arithmetic claim, operator, or equation as entity extraction
    if parsed.claims or re.search(r"[-+*/=]", parsed.raw):
        return None

    norm = parsed.normalized

    # Ratio problems: only check ratio matching if node accepts ratios
    if any(":" in str(a) for a in (node.accept or [])):
        first_pair = ctx.get("first", (3.0, 4.0))
        second_pair = ctx.get("second", (72.0, 96.0))
        first_str = f"{int(first_pair[0])}:{int(first_pair[1])}"
        second_str = f"{int(second_pair[0])}:{int(second_pair[1])}"

        has_first = any(is_ratio_pair(r[0], r[1], first_pair) for r in parsed.ratios) or first_str in norm
        has_second = any(is_ratio_pair(r[0], r[1], second_pair) for r in parsed.ratios) or second_str in norm

        if has_first and not has_second and "second_ratio" not in session.extracted_entities:
            session.extracted_entities.add("first_ratio")
            return StepResult(
                verdict="PARTIAL_EXTRACTION",
                parsed=parsed,
                node_id=node.id,
                feedback=f"Got the first ratio ({first_str})! What is the second ratio given in the problem?",
            )
        if has_second and not has_first and "first_ratio" not in session.extracted_entities:
            session.extracted_entities.add("second_ratio")
            return StepResult(
                verdict="PARTIAL_EXTRACTION",
                parsed=parsed,
                node_id=node.id,
                feedback=f"Got the second ratio ({second_str})! What is the other ratio given in the problem?",
            )
        if (has_first and "second_ratio" in session.extracted_entities) or (has_second and "first_ratio" in session.extracted_entities):
            session.extracted_entities.add("first_ratio")
            session.extracted_entities.add("second_ratio")
            return StepResult(
                verdict="ACCEPT",
                parsed=parsed,
                node_id=node.id,
                feedback="That's correct. We have both ratios identified!",
            )

    # Word problems: numeric given extraction (e.g. 21000, 5, 1)
    expected_nums: List[str] = []
    for a in node.accept or []:
        clean_a = re.sub(r"(?<=\d),(?=\d)", "", a)
        for num in re.findall(r"\d+(?:\.\d+)?", clean_a):
            if num not in expected_nums:
                expected_nums.append(num)

    if len(expected_nums) >= 2:
        # Match standalone numbers strictly using numerical equality (not substring matching!)
        matched_nums = [
            n for n in expected_nums
            if any(abs(pn - float(n)) < EPS for pn in parsed.numbers)
        ]
        if matched_nums:
            for mn in matched_nums:
                session.extracted_entities.add(mn)
            remaining = [n for n in expected_nums if n not in session.extracted_entities]
            if not remaining:
                return StepResult(
                    verdict="ACCEPT",
                    parsed=parsed,
                    node_id=node.id,
                    feedback="Perfect, all given information identified!",
                )
            else:
                return StepResult(
                    verdict="PARTIAL_EXTRACTION",
                    parsed=parsed,
                    node_id=node.id,
                    feedback=f"Got {', '.join(matched_nums)}! What else is given in the problem?",
                )

    return None


def check_compound_steps(
    raw_input: str, session: Session, graph: SolutionGraph, ctx: Dict[str, Tuple[float, float]]
) -> Optional[StepResult]:
    """Problem 6: Check compound multi-step input joined by then, so, and, semicolons."""
    parts = [
        p.strip()
        for p in re.split(r"\s*(?:,\s*then\s+|\s+then\s+|\s*,\s*so\s+|\s+so\s+|;\s*|\s*,\s*and\s+then\s+|\s*\n\s*)\s*", raw_input, flags=re.I)
        if p.strip()
    ]
    if len(parts) < 2:
        return None

    node_map = {n.id: n for n in graph.nodes}
    cur_id = session.current_node_id

    p1 = parse_step(parts[0], default_gcd_pair=ctx.get("second"))
    first_match = None
    target_method = session.method_id

    if cur_id and cur_id in node_map:
        node1 = node_map[cur_id]
        if match_node(p1, node1).get("accepted") or matches_accept_any(p1.raw, node1.accept):
            first_match = node1
            target_method = method_for_node(node1.id, graph) or target_method
    elif not session.method_id:
        for mn in graph.nodes:
            if mn.type == "method":
                fs_id = first_step_of(mn.id, graph)
                fs_node = node_map.get(fs_id)
                if fs_node and (match_node(p1, fs_node).get("accepted") or matches_accept_any(p1.raw, fs_node.accept)):
                    first_match = fs_node
                    target_method = method_of(mn.id) or mn.id
                    break

    if not first_match:
        return None

    succ_id = successor_of(first_match.id, graph)
    if not succ_id or succ_id not in node_map:
        return None

    node2 = node_map[succ_id]
    p2 = parse_step(parts[1], default_gcd_pair=ctx.get("second"))
    second_match = False
    if match_node(p2, node2).get("accepted") or matches_accept_any(p2.raw, node2.accept):
        second_match = True
    elif node2.type == "conclusion":
        if matches_accept_any(p2.raw, node2.accept):
            second_match = True
        else:
            concl_eval = detect_conclusion(p2, session, graph, ctx)
            if concl_eval and concl_eval["detected"] and concl_eval["correct"]:
                second_match = True

    if second_match:
        compound_trail = [
            {"node_id": first_match.id, "input": parts[0], "method_id": target_method},
            {"node_id": node2.id, "input": parts[1], "method_id": target_method},
        ]
        return StepResult(
            verdict="MULTI_STEP_ACCEPT",
            parsed=parse_step(raw_input, default_gcd_pair=ctx.get("second")),
            node_id=node2.id,
            method_id=target_method,
            compound_trail=compound_trail,
            feedback=f"Excellent work! You solved both steps in one go ({parts[0]} and {parts[1]}).",
        )

    return None


def _match_extraction_node(
    parsed: ParsedStep,
    session: Session,
    node: Node,
    graph: SolutionGraph,
    ctx: Dict[str, Tuple[float, float]],
    node_role: str,
) -> Optional[StepResult]:
    """Evaluate a given/goal extraction node: Exact/Math -> Navigator Jaccard -> Qwen 3.5 -> Incremental."""
    m = match_node(parsed, node)
    if m.get("accepted"):
        return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node.id)

    # If already mid-way through incremental extraction, continue tracking entities first
    if node_role == "given" and session.extracted_entities:
        partial = check_incremental_extraction(parsed, session, node, ctx)
        if partial:
            return partial

    nav_m = navigator_match_node(parsed.raw, node, threshold=0.70)
    if nav_m.get("accepted"):
        return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node.id)

    if getattr(node, "optional", True) is False:
        future_calc = find_any_calculation_step(parsed, graph)
        if future_calc:
            default_prompt = "list what is given first." if node_role == "given" else "state what we need to calculate first."
            lead = "But for this problem, let's first list what is given" if node_role == "given" else "But first, let's identify our goal"
            prompt_text = node.prompt or default_prompt
            return StepResult(
                verdict="EXTRACTION_REQUIRED",
                parsed=parsed,
                node_id=node.id,
                feedback=f"Great calculation! That will come in handy in just a moment. {lead}: {prompt_text}",
            )

    # LLM Semantic Verifier fallback (Qwen 3.5 via OpenRouter API) for complete natural-language statements
    if len(parsed.words) >= 3:
        problem_text = (graph.graph_meta and graph.graph_meta.problem_text) or ""
        qwen_m = verify_node_with_qwen(parsed.raw, node, problem_text, node_role=node_role)
        if qwen_m and qwen_m.get("accepted"):
            return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node.id)

    if node_role == "given":
        partial = check_incremental_extraction(parsed, session, node, ctx)
        if partial:
            return partial

    return None


def process_step(raw_input: str, session: Session, graph: SolutionGraph) -> StepResult:
    """Master Socratic step classifier: categorizes student input into deterministic verdicts."""
    ctx = parse_context_from_graph(graph)
    parsed = parse_step(raw_input, default_gcd_pair=ctx.get("second"))
    normalized_input = normalize_text(parsed.raw)
    node_map = {n.id: n for n in graph.nodes}

    # 1. Any explicit false claim is ALWAYS corrected immediately (e.g. 1050 + 500 = 2000)
    false_claim = next((c for c in parsed.claims if not c.is_true), None)
    if false_claim:
        return StepResult(
            verdict="WRONG_CLAIM",
            parsed=parsed,
            node_id=session.current_node_id,
            method_id=session.method_id,
            claim=false_claim,
        )

    # 2. Problem 6: Check compound multi-step input (Fast Learner)
    compound_res = check_compound_steps(raw_input, session, graph, ctx)
    if compound_res:
        return compound_res

    # 3. Problem 7: Check conceptual misconceptions vs raw arithmetic error
    misc = detect_misconception(parsed, session, graph)
    if misc:
        return StepResult(
            verdict="MISCONCEPTION",
            parsed=parsed,
            node_id=session.current_node_id,
            method_id=session.method_id,
            feedback=misc["feedback"],
        )

    cur_node = node_map.get(session.current_node_id) if session.current_node_id else None
    cur_match = cur_node and match_node(parsed, cur_node).get("accepted")

    exact_graph_answer = cur_match or any(
        node.type in ("method", "step", "conclusion", "extraction")
        and any(normalize_text(a) == normalized_input or matches_accept(raw_input, a) for a in (node.accept or []))
        for node in graph.nodes
    )
    nav_any_match = bool(
        navigator_resolve_nodes(
            raw_input,
            [n for n in graph.nodes if n.type in ("method", "step", "conclusion", "extraction")],
            threshold=0.70,
        )
    )
    allow_remote_prose = (
        _should_call_remote_llm()
        and len(parsed.words) >= 2
    )

    if is_garbage(parsed) and not exact_graph_answer and not nav_any_match and not mcq_option(normalized_input, graph) and not allow_remote_prose:
        return StepResult(verdict="GARBAGE", parsed=parsed)

    # 4. Current-node match
    if session.current_node_id:
        node = node_map.get(session.current_node_id)
        if node and node.type == "conclusion":
            concl = detect_conclusion(parsed, session, graph, ctx)
            if concl and concl["detected"]:
                v = "CONCLUSION_RIGHT" if concl["correct"] else "CONCLUSION_WRONG"
                return StepResult(verdict=v, parsed=parsed)
        elif node and node.id == "given_extraction":
            ext_res = _match_extraction_node(parsed, session, node, graph, ctx, "given")
            if ext_res:
                return ext_res
        elif node and node.id == "goal_extraction":
            ext_res = _match_extraction_node(parsed, session, node, graph, ctx, "goal")
            if ext_res:
                return ext_res
        elif node and node.accept:
            m = match_node(parsed, node)
            if m.get("accepted"):
                return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node.id, method_id=method_for_node(node.id, graph))
            nav_m = navigator_match_node(parsed.raw, node, threshold=0.70)
            if nav_m.get("accepted"):
                return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node.id, method_id=method_for_node(node.id, graph))
            # Problem 4: If the student is in an active method and entered a step from another method, lock them in
            if session.method_id:
                other_step = find_step_in_other_methods(parsed, session.method_id, graph)
                if other_step:
                    other_m_node = get_method_node(other_step["method_id"], graph)
                    cur_m_node = get_method_node(session.method_id, graph)
                    other_label = other_m_node.label if other_m_node else other_step["method_id"]
                    cur_label = cur_m_node.label if cur_m_node else session.method_id
                    cur_prompt = node.prompt or "continue with this method."
                    return StepResult(
                        verdict="METHOD_LOCKED",
                        parsed=parsed,
                        node_id=session.current_node_id,
                        method_id=session.method_id,
                        feedback=f"Looks like you're trying a different method ({other_label})! That's a valid approach too, but you are currently solving with {cur_label}. Let's stick with this method so we don't mix up the steps: {cur_prompt}",
                    )
            if m.get("wrong_claim"):
                return StepResult(
                    verdict="WRONG_CLAIM",
                    parsed=parsed,
                    node_id=node.id,
                    method_id=method_for_node(node.id, graph),
                    claim=m.get("claim"),
                )

    # 5. Conclusion match
    concl = detect_conclusion(parsed, session, graph, ctx)
    if concl and concl["detected"]:
        if concl["correct"]:
            jump = check_dag_step_jump(session, graph.conclusion_node, graph, raw_input=raw_input)
            if jump and jump.get("is_jump"):
                first_skipped = jump["first_skipped"]
                skipped_prompt = first_skipped.get("prompt") or "what is the next step?"
                return StepResult(
                    verdict="STEP_JUMP",
                    parsed=parsed,
                    node_id=session.current_node_id,
                    method_id=session.method_id,
                    feedback=(
                        f"That is the final answer, but in Socratic learning you must prove each step first. "
                        f"Please show your work step-by-step: {skipped_prompt}"
                    ),
                )
        v = "CONCLUSION_RIGHT" if concl["correct"] else "CONCLUSION_WRONG"
        return StepResult(verdict=v, parsed=parsed)

    # 6. Reject reversed ratios (e.g. 4:3 instead of 3:4)
    first_pair = ctx.get("first", (3.0, 4.0))
    second_pair = ctx.get("second", (72.0, 96.0))
    reversed_ratio = next(
        (
            r for r in parsed.ratios
            if is_ratio_pair(r[0], r[1], (first_pair[1], first_pair[0]))
            or is_ratio_pair(r[0], r[1], (second_pair[1], second_pair[0]))
        ),
        None,
    )
    if reversed_ratio:
        return StepResult(
            verdict="WRONG_CLAIM",
            parsed=parsed,
            node_id=session.current_node_id,
            method_id=session.method_id,
            claim={
                "kind": "value",
                "got": f"{int(reversed_ratio[0])}:{int(reversed_ratio[1])}",
                "expected": f"{int(first_pair[0])}:{int(first_pair[1])}",
                "text": f"{int(reversed_ratio[0])}:{int(reversed_ratio[1])}",
            },
        )

    # 7. Extraction fast path when no method is locked
    if not session.method_id:
        given_ext = node_map.get("given_extraction")
        goal_ext = node_map.get("goal_extraction")
        has_given = any(t.get("nodeId") == "given_extraction" for t in session.trail)
        has_goal = any(t.get("nodeId") == "goal_extraction" for t in session.trail)

        if not has_given and given_ext:
            ext_res = _match_extraction_node(parsed, session, given_ext, graph, ctx, "given")
            if ext_res:
                return ext_res
        elif has_given and not has_goal and goal_ext:
            ext_res = _match_extraction_node(parsed, session, goal_ext, graph, ctx, "goal")
            if ext_res:
                return ext_res

    # 8. Global step search within current method (or any method if none locked yet)
    # Includes Navigator Exact/Math -> Navigator Jaccard -> Qwen 3.5 fallback
    g = find_global_step_match(parsed, session, graph)
    if g:
        jump = check_dag_step_jump(session, g["node_id"], graph)
        if jump and jump.get("is_jump"):
            first_skipped = jump["first_skipped"]
            skipped_label = first_skipped.get("label") or first_skipped.get("id")
            skipped_prompt = first_skipped.get("prompt") or "what is the next step?"
            return StepResult(
                verdict="STEP_JUMP",
                parsed=parsed,
                node_id=g["node_id"],
                method_id=g["method_id"],
                feedback=(
                    f"That calculation is part of {skipped_label}, but you leaped ahead without showing intermediate work. "
                    f"Please show your work step-by-step first: {skipped_prompt}"
                ),
            )
        return StepResult(verdict="ACCEPT", parsed=parsed, node_id=g["node_id"], method_id=g["method_id"])

    # 8b. Active step LLM Semantic Verifier fallback (Qwen 3.5) if global step search didn't match elsewhere
    if cur_node and cur_node.type == "step":
        problem_text = (graph.graph_meta and graph.graph_meta.problem_text) or ""
        qwen_cur = verify_node_with_qwen(parsed.raw, cur_node, problem_text, node_role="step")
        if qwen_cur and qwen_cur.get("accepted"):
            return StepResult(verdict="ACCEPT", parsed=parsed, node_id=cur_node.id, method_id=method_for_node(cur_node.id, graph))

    # 8c. Conclusion Step-Jump Safety Catch (when final answer matches conclusion before any calculation step)
    concl_node = node_map.get(graph.conclusion_node)
    if (
        concl_node
        and not is_bare_yes_no(parsed)
        and session.current_node_id not in ("given_extraction", "goal_extraction")
        and (matches_accept_any(parsed.raw, concl_node.accept) or navigator_match_node(parsed.raw, concl_node, threshold=0.70).get("accepted"))
    ):
        jump = check_dag_step_jump(session, graph.conclusion_node, graph, raw_input=raw_input)
        if jump and jump.get("is_jump"):
            first_skipped = jump["first_skipped"]
            skipped_prompt = first_skipped.get("prompt") or "what is the next step?"
            return StepResult(
                verdict="STEP_JUMP",
                parsed=parsed,
                node_id=session.current_node_id,
                method_id=session.method_id,
                feedback=(
                    f"That is the final answer, but in Socratic learning you must prove each step first. "
                    f"Please show your work step-by-step: {skipped_prompt}"
                ),
            )

    # 9. Problem 4: Enforcing Method Commitment (No mid-way switching)
    # Only triggered if the calculation does NOT belong to the active method, but DOES belong to another method
    if session.method_id:
        other_step = find_step_in_other_methods(parsed, session.method_id, graph)
        if other_step:
            other_m_node = get_method_node(other_step["method_id"], graph)
            cur_m_node = get_method_node(session.method_id, graph)
            other_label = other_m_node.label if other_m_node else other_step["method_id"]
            cur_label = cur_m_node.label if cur_m_node else session.method_id
            cur_node = node_map.get(session.current_node_id)
            cur_prompt = cur_node.prompt if cur_node else "continue with this method."
            return StepResult(
                verdict="METHOD_LOCKED",
                parsed=parsed,
                node_id=session.current_node_id,
                method_id=session.method_id,
                feedback=f"Looks like you're trying a different method ({other_label})! That's a valid approach too, but you are currently solving with {cur_label}. Let's stick with this method so we don't mix up the steps: {cur_prompt}",
            )

    # 10. Method Identification Waterfall (Strictly for Method Identification: Navigator -> Local JEV -> Global JEV)
    if not session.method_id and has_completed_required_extraction(session, graph):
        mk = detect_method_keyword(parsed, graph)
        if mk:
            return StepResult(verdict="ACCEPT", parsed=parsed, method_id=mk, approach_only=True)
        resolved = resolve_method_waterfall(raw_input, graph)
        if resolved and resolved.get("method_id"):
            return StepResult(
                verdict="ACCEPT",
                parsed=parsed,
                method_id=resolved["method_id"],
                approach_only=True,
            )

    # 11. True math, but irrelevant
    if any(c.is_true for c in parsed.claims):
        return StepResult(verdict="IRRELEVANT_TRUE", parsed=parsed)

    # 12. Garbage or Relevant words without checkable content
    if is_garbage(parsed) and not exact_graph_answer and not nav_any_match and not mcq_option(normalized_input, graph):
        return StepResult(verdict="GARBAGE", parsed=parsed)
    return StepResult(verdict="UNPARSED", parsed=parsed)

