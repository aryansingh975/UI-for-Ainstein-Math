from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.schemas.graph import SolutionGraph, Node
from app.engine.normalizer import normalize_text
from app.engine.vocabulary import has_irrelevant_words, MATH_INTENT
from app.engine.evaluator import eval_arithmetic, EPS
from app.engine.claims import extract_claims, Claim
from app.engine.matcher import matches_accept, matches_accept_any
from app.engine.state_machine import (
    Session,
    method_of,
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


class StepResult:
    def __init__(
        self,
        verdict: str,
        parsed: ParsedStep,
        node_id: Optional[str] = None,
        method_id: Optional[str] = None,
        claim: Optional[Any] = None,
        approach_only: bool = False,
    ):
        self.verdict = verdict
        self.parsed = parsed
        self.node_id = node_id
        self.method_id = method_id
        self.claim = claim
        self.approach_only = approach_only

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "nodeId": self.node_id,
            "methodId": self.method_id,
            "approachOnly": self.approach_only,
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

    if len(nums) == 1:
        return {"kind": "number", "value": nums[0]}
    if len(nums) > 1:
        return {"kind": "values", "values": nums}
    return None


def verify_against_expected(parsed: ParsedStep, exp: Dict[str, Any]) -> Dict[str, Any]:
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
            all_in = all(any(abs(n - x) < EPS for x in exp["values"]) for n in parsed.numbers)
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


def match_node(parsed: ParsedStep, node: Node) -> Dict[str, Any]:
    if matches_accept_any(parsed.raw, node.accept):
        return {"accepted": True}
    exp = expected_for(node)
    if not exp:
        return {"accepted": False}
    return verify_against_expected(parsed, exp)


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


def detect_conclusion(
    parsed: ParsedStep, session: Session, graph: SolutionGraph, ctx: Dict[str, Tuple[float, float]]
) -> Optional[Dict[str, Any]]:
    node_map = {n.id: n for n in graph.nodes}
    concl = node_map.get(graph.conclusion_node)
    if not concl:
        return None

    norm = parsed.normalized
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

    if matches_accept_any(parsed.raw, concl.accept):
        return {"detected": True, "correct": not negated and not bool(re.match(r"^(no|nope)\b", norm))}

    if re.search(r"\bproportional\b", norm):
        has_first = any(is_ratio_pair(r[0], r[1], first_pair) for r in parsed.ratios)
        has_second = any(is_ratio_pair(r[0], r[1], second_pair) for r in parsed.ratios)
        if has_first and has_second:
            return {"detected": True, "correct": not negated}

    return None


def find_global_step_match(
    parsed: ParsedStep, session: Session, graph: SolutionGraph
) -> Optional[Dict[str, Any]]:
    if is_bare_yes_no(parsed):
        return None

    steps = [
        n for n in graph.nodes
        if n.type == "step" and (not session.method_id or method_of(n.id) == session.method_id)
    ]

    scored = []
    for n in steps:
        score = 0
        nm = method_of(n.id)
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
            return {"node_id": node.id, "method_id": method_of(node.id)}

    # Pass 2: semantic verification
    for node in ordered:
        exp = expected_for(node)
        if not exp:
            continue
        m = verify_against_expected(parsed, exp)
        if m.get("accepted"):
            return {"node_id": node.id, "method_id": method_of(node.id)}

    return None


def process_step(raw_input: str, session: Session, graph: SolutionGraph) -> StepResult:
    """Master Socratic step classifier: categorizes student input into deterministic verdicts."""
    ctx = parse_context_from_graph(graph)
    parsed = parse_step(raw_input, default_gcd_pair=ctx.get("second"))
    normalized_input = normalize_text(parsed.raw)
    node_map = {n.id: n for n in graph.nodes}

    exact_graph_answer = any(
        node.type in ("method", "step", "conclusion", "extraction")
        and any(normalize_text(a) == normalized_input for a in (node.accept or []))
        for node in graph.nodes
    )

    if is_garbage(parsed) and not exact_graph_answer:
        return StepResult(verdict="GARBAGE", parsed=parsed)

    # 1. Current-node match
    if session.current_node_id:
        node = node_map.get(session.current_node_id)
        if node and node.type == "conclusion":
            concl = detect_conclusion(parsed, session, graph, ctx)
            if concl and concl["detected"]:
                v = "CONCLUSION_RIGHT" if concl["correct"] else "CONCLUSION_WRONG"
                return StepResult(verdict=v, parsed=parsed)
        elif node and node.accept:
            m = match_node(parsed, node)
            if m.get("accepted"):
                return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node.id, method_id=method_of(node.id))
            if m.get("wrong_claim"):
                return StepResult(
                    verdict="WRONG_CLAIM",
                    parsed=parsed,
                    node_id=node.id,
                    method_id=method_of(node.id),
                    claim=m.get("claim"),
                )

    # 2. Conclusion match
    concl = detect_conclusion(parsed, session, graph, ctx)
    if concl and concl["detected"]:
        v = "CONCLUSION_RIGHT" if concl["correct"] else "CONCLUSION_WRONG"
        return StepResult(verdict=v, parsed=parsed)

    # 3. Reject reversed ratios (e.g. 4:3 instead of 3:4)
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

    # 4. Any explicit false claim -> immediate correction
    false_claim = next((c for c in parsed.claims if not c.is_true), None)
    if false_claim:
        return StepResult(
            verdict="WRONG_CLAIM",
            parsed=parsed,
            node_id=session.current_node_id,
            method_id=session.method_id,
            claim=false_claim,
        )

    # 5. Extraction fast path when no method is locked
    if not session.method_id:
        given_ext = node_map.get("given_extraction")
        goal_ext = node_map.get("goal_extraction")
        has_given = any(t.get("nodeId") == "given_extraction" for t in session.trail)
        has_goal = any(t.get("nodeId") == "goal_extraction" for t in session.trail)

        if not has_given and given_ext:
            m = match_node(parsed, given_ext)
            if m.get("accepted"):
                return StepResult(verdict="ACCEPT", parsed=parsed, node_id=given_ext.id)
        elif has_given and not has_goal and goal_ext:
            m = match_node(parsed, goal_ext)
            if m.get("accepted"):
                return StepResult(verdict="ACCEPT", parsed=parsed, node_id=goal_ext.id)

    # 6. Method keyword approach
    if not session.method_id and has_completed_required_extraction(session, graph):
        mk = detect_method_keyword(parsed, graph)
        if mk:
            return StepResult(verdict="ACCEPT", parsed=parsed, method_id=mk, approach_only=True)

    # 7. Global step search (silent inference / skip-ahead)
    g = find_global_step_match(parsed, session, graph)
    if g:
        return StepResult(verdict="ACCEPT", parsed=parsed, node_id=g["node_id"], method_id=g["method_id"])

    # 8. True math, but irrelevant
    if any(c.is_true for c in parsed.claims):
        return StepResult(verdict="IRRELEVANT_TRUE", parsed=parsed)

    # 9. Relevant words but nothing checkable
    return StepResult(verdict="UNPARSED", parsed=parsed)

