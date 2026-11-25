"""Guided mode: the tutor asks one question at a time (graph_meta.guided = true).

The student answers the question on screen. A correct answer moves to the next question; a wrong
answer shows the node's hints in order (Hint 1, then 2, then 3). Answers are checked with the same
matching as free-form mode (accept list, expected values, SymPy), plus two optional node fields:
  keywords  - words/numbers that must all appear ("same", "birthday", "0.008")
  forbidden - words that make the answer wrong ("not": 'not the same birthday' is the given, not the goal)

Node types used on the guided path: extraction, concept, choice, step, conclusion. A "choice" node
lets the student pick a method by answering the first question of any method that follows it.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

import sympy as sp
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations, rationalize,
                                        implicit_multiplication_application)

from app.schemas.graph import SolutionGraph, Node
from app.engine.state_machine import Session, method_of
from app.engine.tutor_engine import StepResult, parse_step, match_node
from app.engine.matcher import matches_accept_any
from app.engine.method_classifier import classify_graph
from app.engine.sympy_validator import validate
from app.engine.concept_choice import evaluate_plan, _DONT_KNOW, _without_unknowns
from app.engine import plan_llm
from app.engine import linear_pair, polynomials
from app.engine.plan_llm import check_plan


def is_guided(graph: SolutionGraph) -> bool:
    return getattr(graph.graph_meta, "guided", None) is True


def _nodes(graph: SolutionGraph):
    return {n.id: n for n in graph.nodes}


def _next_of(node_id: str, graph: SolutionGraph) -> List[str]:
    return [e.to_node for e in graph.edges if e.from_node == node_id]


def _question_after(node_id: str, graph: SolutionGraph) -> Optional[str]:
    """The next question: skips method nodes (a method is entered through its first step)."""
    nodes = _nodes(graph)
    nxt = _next_of(node_id, graph)
    if not nxt:
        return graph.conclusion_node
    target = nodes.get(nxt[0])
    if target and target.type == "method":
        return _question_after(target.id, graph)
    return nxt[0]


def first_question(graph: SolutionGraph) -> Optional[str]:
    return _question_after(graph.start_node, graph)


def _choices(node: Node, graph: SolutionGraph) -> List[Node]:
    """First step of every method that a choice node leads to."""
    nodes = _nodes(graph)
    return [nodes[s] for m in _next_of(node.id, graph) if nodes.get(m) and nodes[m].type == "method"
            for s in _next_of(m, graph)[:1] if s in nodes]


def _later_steps(node_id: str, graph: SolutionGraph) -> List[Node]:
    """Steps after this one in the same method (a student may skip ahead), conclusion excluded."""
    nodes, out, cur = _nodes(graph), [], _question_after(node_id, graph)
    while cur and cur != graph.conclusion_node and cur in nodes and nodes[cur].type == "step":
        out.append(nodes[cur])
        cur = _question_after(cur, graph)
    return out


def _has(text: str, word: str) -> bool:
    if re.fullmatch(r"[a-z]", word):                                          # a variable: the letter on its own
        return re.search(rf"(?<![a-z]){word}(?![a-z])", text) is not None
    if re.fullmatch(r"[a-z]+", word):
        return re.search(rf"(?<![a-z]){re.escape(word)}", text) is not None   # prefix: complement → complementary
    if re.fullmatch(r"[\d.]+", word):
        return re.search(rf"(?<![\d.]){re.escape(word)}(?![\d])", text) is not None
    return word in text


def _keywords_ok(raw: str, node: Node) -> Optional[bool]:
    """True/False when the node has keywords; None when it has none."""
    keywords = getattr(node, "keywords", None) or []
    if not keywords:
        return None
    low = raw.lower().replace("−", "-").replace("–", "-")
    return all(any(_has(low, alt) for alt in k.lower().split("|")) for k in keywords)   # "five|5": either


def _forbidden(raw: str, node: Node) -> bool:
    low = raw.lower()
    return any(_has(low, w.lower()) for w in getattr(node, "forbidden", None) or [])


_TRANSFORMS = standard_transformations + (rationalize,)       # 0.992 is read as 124/125, exactly
_LABEL = re.compile(r"^(?:p\s*\(.*\)|[a-zπ][a-zπ*()+/ ]*)$")   # P(not a ₹5 coin), x, total, V1, π r² h
_NUMERIC = re.compile(r"^[\d\s.+\-*/()]+$")
_UNIT = re.compile(r"(?<=[\d)])\s*(kg|cm|mm|km|g|m)(?:\s*\*\*\s*([23])|\s?([23])(?![\d.]))?(?![a-z])")   # 12 cm, 99475.2 cm³, 8g


def _maths(text: str) -> str:
    """Lower case, with ×, ÷, ^, ², ³, ≈ and the minus signs written the way SymPy reads them."""
    text = re.sub(r"(?<=[A-Za-z])\.(?=\d)", ". ", text)       # "volumes.99475.2": a full stop, then a number
    t = (text.lower().replace("−", "-").replace("–", "-").replace("×", "*").replace("÷", "/").replace("^", "**")
         .replace("²", "**2").replace("³", "**3").replace("≈", "="))
    for words, unit in _UNIT_WORDS:                           # "892262.4 grams" → "892262.4 g"
        t = re.sub(words, unit, t)
    return t


_UNIT_WORDS = [
    (r"\bkilo\s?grams?\b|\bkgs\b", "kg"),
    (r"\bgrams?\b|\bgms?\b", "g"),
    (r"\bcubic\s+(?:cm|centimet(?:er|re)s?)\b|\bcu\.?\s?cm\b|\bcc\b|\bcm\s+cubed?\b", "cm**3"),
    (r"\bsq(?:uare)?\.?\s+(?:cm|centimet(?:er|re)s?)\b", "cm**2"),
    (r"\bcubic\s+m(?:et(?:er|re)s?)?\b|\bm\s+cubed?\b", "m**3"),
    (r"\bsq(?:uare)?\.?\s+m(?:et(?:er|re)s?)?\b", "m**2"),
    (r"\bcentimet(?:er|re)s?\b", "cm"),
]


def _with_pi(raw: str, problem_text: str) -> str:
    """'Use π = 3.14' in the question: π or pi in the answer means 3.14 ('pi × 12² × 220 = 99475.2')."""
    m = re.search(r"π\s*=\s*(\d+(?:\.\d+)?(?:/\d+)?)", problem_text or "")
    return re.sub(r"π|(?<![a-z])pi(?![a-z])", f"({m.group(1)})", raw, flags=re.I) if m else raw


def _sides(text: str) -> Optional[List[Tuple[str, Optional[sp.Expr]]]]:
    """Split 'P(not ₹5) = 170/180 = 17/18' into (side, exact value or None for a name). None if a side is neither.
    A unit stays with its side ('892.26 kg') so that sides in different units are not compared."""
    out = []
    text = re.sub(r"\b(hcf|lcm|gcd)\s*\([^)]*\)", r"\1", _maths(text))   # "HCF(26, 91)" is a name, like "HCF"
    for side in (s.strip() for s in text.split("=")):
        number = _UNIT.sub("", side).strip()
        if _NUMERIC.fullmatch(number.replace("**", "*")) and re.search(r"\d", number):
            try:
                out.append((side, sp.nsimplify(parse_expr(number, transformations=_TRANSFORMS), rational=True)))
            except Exception:
                return None
        elif _LABEL.fullmatch(re.sub(r"(?<=[a-z])\d+|\*\*\d", "", side)):     # digits only as V1 or r**2
            out.append((side, None))
        else:
            return None
    return out


def _pretty(side: str) -> str:
    """Back to the way the student wrote it: '12**2 * 220' → '12² × 220'."""
    side = re.sub(r"\((\d+(?:\.\d+)?)\)", r"\1", side)       # "(3.14)" from π or pi → "3.14"
    return side.replace("**2", "²").replace("**3", "³").replace("*", "×")


def _unit(side: str) -> Optional[str]:
    """'99475.2 cm**3' → 'cm3', '892.26 kg' → 'kg', no unit → None."""
    m = _UNIT.search(side)
    return m.group(1) + (m.group(2) or m.group(3) or "") if m else None


def _show_unit(unit: str) -> str:
    return unit.replace("3", "³").replace("2", "²")


# A result: a number on its own, with or without a unit ("12057.6 cm³", "892.26", "892262.4 g.")
_RESULT = re.compile(r"\s*(\d+(?:\.\d+)?)(\s*(?:kg|cm|mm|km|g|m)(?:\s*\*\*\s*[23]|\s?[23](?![\d.]))?)?\s*\.?\s*")


def _unit_check(answer: str, graph: SolutionGraph, session: Session) -> Optional[dict]:
    """Every result needs its unit: '3.14 × 64 × 60' needs none, '3.14 × 64 × 60 = 12057.6' needs cm³, and in
    '892262.4 ≈ 892.26 kg' the 892262.4 needs g. A result is a number on its own after '=', '≈' or 'is', or a
    line that is just a number. The unit a value should have comes from the JSON. None when the units are fine."""
    t = _maths(answer)
    parts = t.split("=")
    sides = parts if len(parts) == 1 or _RESULT.fullmatch(parts[0]) else parts[1:]   # "892262.4 ≈ 892.26 kg": both
    sides[-1] = re.split(r"\bis\b", sides[-1])[-1]          # "the mass of the pole is 892.26"
    known = _known_values(graph) + session.free_values
    what = "calculation" if re.search(r"\d\s*[-+*/]", t) else "value"
    for side in sides:
        m = _RESULT.fullmatch(side)
        value = _exact(m.group(1)) if m else None
        if value is None:
            continue
        number, written = m.group(1), _unit("0" + m.group(2)) if m.group(2) else None
        expected = {u for k, u in known if u and _close(number, value, k)}
        if not expected or written in expected:
            continue
        message = (f"The {what} is correct, but the unit is missing after {number}." if written is None else
                   f"The {what} is correct, but {number} is not in {_show_unit(written)}. Check the unit.")
        return {"kind": "value", "isTrue": False, "text": answer, "message": message}
    return None


def _close(written: str, value: sp.Expr, target: sp.Expr) -> bool:
    """Equal, or a decimal target rounded to the 2+ decimal places the student wrote (892.26 for 892.2624).
    A fraction that is not a finite decimal (17/18) must be written exactly: 0.94 is not 17/18."""
    if _same(value, target):
        return True
    m = re.search(r"\d\.(\d{2,})(?!\d)", written)
    finite = target.is_Rational and set(sp.factorint(target.q)) <= {2, 5}
    return bool(m) and finite and abs(float(value) - round(float(target), len(m.group(1)))) < 1e-9


def _step_values(node: Node) -> List[sp.Expr]:
    """The value a calculation step asks for, from its accept list: '1 − 1/18 = 17/18' gives 17/18."""
    values: List[sp.Expr] = []
    for accepted in node.accept or []:
        sides = _sides(accepted)
        if sides and sides[-1][1] is not None and sides[-1][1] not in values:
            values.append(sides[-1][1])
    return values


def _broken_chain(numbers: List[Tuple[str, sp.Expr]]) -> Optional[dict]:
    """'3.14 × 12² × 220 = 99000': every number in a chain must be equal (a change of unit is not compared)."""
    for (a, va), (b, vb) in zip(numbers, numbers[1:]):
        conversion = _unit(a) != _unit(b) and _FINAL.fullmatch(_UNIT.sub("", a).strip())
        if not conversion and not _close(b, vb, va):          # "892262.4 g = 892.26 kg" is a change of unit
            a, b = _pretty(a), _pretty(b)
            return {"accepted": False, "wrong_claim": True,
                    "claim": {"kind": "arith", "is_true": False, "text": f"{a} = {b}", "lhs": a, "rhs": b,
                              "lhs_val": float(va), "rhs_val": float(vb)}}
    return None


def _value_check(raw: str, node: Node) -> Optional[dict]:
    """SymPy: any correct way of writing the step's value is accepted ('P(not a ₹5 coin) = 170/180' for 17/18).
    Every number in a chain must be equal; a chain that breaks is a mistake. None when it does not apply."""
    if node.type != "step":
        return None
    sides, targets = _sides(raw), _step_values(node)
    if not sides or not targets:
        return None
    numbers = [(s, v) for s, v in sides if v is not None]
    if not numbers:
        return None
    broken = _broken_chain(numbers)
    if broken:
        return broken
    last, value = numbers[-1]
    if any(_close(last, value, t) for t in targets):
        return {"accepted": True}
    if _FINAL.fullmatch(_UNIT.sub("", last).strip()):         # "0.08": just a wrong answer (hint follows)
        return {"accepted": False}
    return {"accepted": False, "wrong_claim": True,           # "P(E) = 1 + 0.992": the calculation gives 1.992
            "claim": {"kind": "value", "isTrue": False, "text": raw, "got": str(value),
                      "message": f"{last} = {value}, which is not the answer to this question."}}


_X = re.compile(r"(?<![a-z])x(?![a-z])")


def _equation_check(raw: str, equation: Optional[str]) -> Optional[dict]:
    """SymPy on a line with x: it must have the same solution as the problem's equation (x + 124/125 = 1).
    None when SymPy cannot read the line ('x = P(same birthday)') or there is no equation."""
    if not equation or "=" not in raw or not _X.search(raw.lower()):
        return None
    try:
        lines = validate(raw, equation).get("lines", [])
    except Exception:
        return None
    bad = next((l for l in lines if l.get("status") == "invalid"), None)
    if bad:
        return {"accepted": False, "wrong_claim": True,
                "claim": {"kind": "equation", "isTrue": False, "text": raw, "message": bad.get("message") or ""}}
    if lines and all(l.get("status") == "valid" for l in lines):
        return {"accepted": True}
    return None


_FINAL = re.compile(r"^-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?$")     # 0.008, 1/125: a value, not a calculation


def _furthest_with_same_answer(raw: str, node: Node, graph: SolutionGraph) -> Node:
    """'P(E) = 1/125' answers both 'What is P(E)?' and the next 'What is the probability?': skip the repeat.
    Only for a final value; 'P(E) = 1 − 0.992' still answers just this question."""
    sides = _sides(raw)
    if not sides or sides[-1][1] is None or not _FINAL.fullmatch(_UNIT.sub("", sides[-1][0]).strip()):
        return node
    value = sides[-1][1]
    for later in _later_steps(node.id, graph):
        if not any(sp.simplify(value - t) == 0 for t in _step_values(later)):
            break
        node = later
    return node


# A number or a calculation inside a sentence: "1/125", "1 − 0.992", "(170/180)" - not the 50 in "50p" or the 5 in "₹5"
_RUN = re.compile(r"(?<![\w₹.*])\(?-?\d+(?:\.\d+)?\)?(?:\s*(?:\*\*|[-+*/])\s*\(?-?\d+(?:\.\d+)?\)?)*(?![\w.])")


def _exact(text: str) -> Optional[sp.Expr]:
    try:
        return sp.nsimplify(parse_expr(text, transformations=_TRANSFORMS), rational=True)
    except Exception:
        return None


def _runs(text: str) -> List[Tuple[str, sp.Expr]]:
    out = []
    for m in _RUN.finditer(text):
        value = _exact(m.group(0))
        if value is not None:
            out.append((m.group(0).strip(), value))
    return out


def _same(a: sp.Expr, b: sp.Expr) -> bool:
    return sp.simplify(a - b) == 0


def _conclusion_check(raw: str, node: Node, problem_text: str) -> Optional[dict]:
    """SymPy on the final answer: every value in answer_values must be there (in order), any other number must
    equal an answer, and a chain like '170/180 = 17/19' must hold. Numbers from the question ('2 students')
    are ignored. Words are still checked by the node's keywords. None when the node has no answer_values.
    An answer may have forms in other units, split by '|' ('892262.4|892.2624' for g or kg); a value rounded to
    2+ decimal places counts ('0.56' for 5/9)."""
    answers = [[v for v in (_exact(f) for f in a.split("|")) if v is not None]
               for a in getattr(node, "answer_values", None) or []]
    answers = [forms for forms in answers if forms]
    if node.type != "conclusion" or not answers:
        return None
    text = re.sub(r"(\d)(kg|cm|mm|g)(?![a-z])", r"\1 \2", _maths(raw))   # "892.26kg" → "892.26 kg"

    parts = text.split("=")                                   # a chain must hold: "1 - 0.992 = 0.08" is a mistake
    for left, right in zip(parts, parts[1:]):
        a = re.search(rf"({_RUN.pattern})\s*$", left)          # numbers right next to "=", not "10/18 and P(..) ="
        b = re.match(rf"\s*({_RUN.pattern})(\s*(?:kg|cm|mm|km|g|m)(?![a-z]))?", right)
        va, vb = (_exact(a.group(1)) if a else None), (_exact(b.group(1)) if b else None)
        if b and b.group(2) and _FINAL.fullmatch(a.group(1).strip() if a else ""):
            continue                                          # "892262.4 ≈ 892.26 kg": a change of unit
        if va is not None and vb is not None and not _close(b.group(1), vb, va):
            lhs, rhs = _pretty(a.group(1).strip()), _pretty(b.group(1).strip())
            return {"accepted": False, "wrong_claim": True,
                    "claim": {"kind": "arith", "is_true": False, "text": f"{lhs} = {rhs}",
                              "lhs": lhs, "rhs": rhs, "lhs_val": float(va), "rhs_val": float(vb)}}

    given = set(re.findall(r"\d+(?:\.\d+)?", problem_text))
    values = [(s, v) for s, v in _runs(text) if s not in given]

    def is_answer(written: str, value: sp.Expr, forms: List[sp.Expr]) -> bool:
        return any(_close(written, value, f) for f in forms)

    i = 0
    for forms in answers:                                     # each answer, in order
        i = next((j + 1 for j in range(i, len(values)) if is_answer(*values[j], forms)), None)
        if i is None:
            return {"accepted": False}
    if any(not any(is_answer(s, v, forms) for forms in answers) for s, v in values):
        return {"accepted": False}                            # "5/9 and 17/18 or 17/19"
    return {"accepted": _keywords_ok(raw, node) is not False}


_PRODUCT = re.compile(r"\(?\d+\)?(?:\s*\*\*\s*\d+)?(?:\s*\*\s*\(?\d+\)?(?:\s*\*\*\s*\d+)?)*")


def _factors(product: str) -> Optional[List[Tuple[int, int]]]:
    """'2**2 * 5 * 7' → [(2, 2), (5, 1), (7, 1)]; None if it is not a product of whole numbers."""
    t = product.replace(" ", "").replace("(", "").replace(")", "")
    if not re.fullmatch(r"\d+(?:\*\*\d+)?(?:\*\d+(?:\*\*\d+)?)*", t):
        return None
    return [(int(b), int(e or 1)) for b, e in re.findall(r"(\d+)(?:\*\*(\d+))?", t)]


def _factor_check(raw: str, node: Node) -> Optional[dict]:
    """Prime factorisation (node.factorise): every listed number must appear as a product of primes,
    '140 = 2² × 5 × 7' (or '2 × 2 × 5 × 7'). '140 = 4 × 35' is true but not prime; '2 × 5 × 7' is not 140.
    Several numbers may be in one answer, split by ',', ';', 'and' or new lines. None if no product is written."""
    wanted = list(getattr(node, "factorise", None) or [])
    if not wanted:
        return None
    done, composite, wrong = _factored_numbers(raw, node)
    if wrong:
        return {"accepted": False, "wrong_claim": True,
                "claim": {"kind": "value", "isTrue": False, "text": raw, "message": wrong}}
    if composite and not set(wanted) <= done:
        n, bad = composite[0]
        names = " and ".join(str(b) for b in bad)
        return {"accepted": False, "wrong_claim": True,
                "claim": {"kind": "value", "isTrue": False, "text": raw,
                          "message": f"That equals {n}, but {names} {'is' if len(bad) == 1 else 'are'} not prime. "
                                     f"Break {'it' if len(bad) == 1 else 'them'} into primes too."}}
    if not done and not composite:
        return None
    return {"accepted": set(wanted) <= done}


def _poly_check(raw: str, node: Node) -> Optional[dict]:
    """A polynomial node (engine/polynomials.py): accepted / wrong_claim with SymPy's message; None: not one."""
    spec = getattr(node, "value_of", None)
    result = polynomials.value_step(raw, spec) if spec else None
    pair = linear_pair.node_check(node)
    if result is None and pair:
        r = linear_pair.step(pair[0], raw, pair[1], [])
        result = None if r is None else {"ok": bool(r.get("done")), "message": r.get("message") if r.get("wrong")
                                         else None, "plain": not r.get("wrong")}
    if result is None and getattr(node, "relation_of", None):
        r = polynomials.relation_step(raw, node.relation_of, [])
        result = None if r is None else {"ok": bool(r.get("done")), "message": r.get("message") if not r["ok"]
                                         else None, "plain": r["ok"]}
    if result is None and getattr(node, "quadratic_with", None):
        result = polynomials.quadratic_step(raw, node.quadratic_with)
    if result is None and getattr(node, "given_polys", None):     # "What is given?": the question's polynomials
        result = polynomials.given_polys_step(raw, node.given_polys)
    if result is None and getattr(node, "given_pairs", None):
        result = polynomials.given_pairs_step(raw, node.given_pairs)
    if result is None and getattr(node, "zeroes_of", None):
        r = polynomials.zeroes_step(raw, node.zeroes_of, [])
        result = None if r is None else {"ok": bool(r.get("done")), "message": r.get("message")}
    if result is None:
        return None
    if result["ok"]:
        return {"accepted": True}
    if result.get("plain") or not result.get("message"):
        return {"accepted": False}
    return {"accepted": False, "wrong_claim": True,
            "claim": {"kind": "value", "isTrue": False, "text": raw, "message": result["message"]}}


def _factored_numbers(raw: str, node: Node) -> Tuple[Set[int], List[Tuple[int, List[int]]], Optional[str]]:
    """(numbers of node.factorise written as products of primes, (number, its composite factors) for true products
    that still have composite factors, the first wrong product's message)."""
    wanted = list(getattr(node, "factorise", None) or [])
    done, composite, wrong = set(), [], None
    text = re.sub(r"(?<=[\d)])\s*[x.]\s*(?=[\d(])", " * ", _maths(raw))   # "2 x 2 x 5", "2.2.5.7" as times
    text = re.sub(r"\)\s*\(", ") * (", text)                             # "(2)(2)(5)(7)"
    for part in re.split(r"[,;\n]|\band\b", text):
        sides = [x.strip().rstrip(".") for x in part.split("=")]
        products = [(x, _factors(x)) for x in sides if _PRODUCT.fullmatch(x.replace(" ", "")) and "*" in x]
        if not products:
            continue
        side, factors = products[-1]                          # the last product: "140 = 2 × 70 = 2² × 5 × 7"
        value = 1
        for b, e in factors:
            value *= b ** e
        named = [int(x) for x in sides if re.fullmatch(r"\d+", x)]
        target = named[0] if named else value
        if named and value != target:                         # "140 = 2 × 5 × 7": 70, not 140
            wrong = wrong or f"{_pretty(side)} = {value}, not {target}."
            continue
        if target not in wanted:
            continue
        bad = sorted({b for b, _ in factors if not sp.isprime(b)})
        if bad:
            composite.append((target, bad))
        else:
            done.add(target)
    return done, composite, wrong


def _check(raw: str, node: Node, equation: Optional[str], problem_text: str = "") -> dict:
    """accepted / wrong_claim (with claim) / not accepted."""
    if _forbidden(raw, node):
        return {"accepted": False}
    factored = _factor_check(raw, node)                       # "140 = 2² × 5 × 7": every factor must be prime
    if factored is not None:
        return factored
    by_poly = _poly_check(raw, node)                          # zeroes, α + β, a quadratic from its zeroes
    if by_poly is not None:
        return by_poly
    if node.type == "step":                                   # SymPy first for x-lines: the text matcher reads
        by_equation = _equation_check(raw, equation)          # "x - 0.992 = 1" like "x + 0.992 = 1"
        if by_equation is not None:
            return by_equation
    if matches_accept_any(raw, node.accept):
        return {"accepted": True}
    final = _conclusion_check(raw, node, problem_text)
    if final is not None:
        return final
    by_value = _value_check(raw, node)
    if by_value is not None:
        return by_value
    checked = match_node(parse_step(raw), node, equation=equation)
    if checked.get("wrong_claim"):
        return checked                                   # a maths mistake is reported as a mistake
    keywords = _keywords_ok(raw, node)
    if keywords is not None:                             # the node's keywords decide ("P(E) = 0.992" lacks the 1)
        return {"accepted": keywords}
    return checked


def _hint(node: Node, session: Session) -> Optional[str]:
    """Hint 1 after the first wrong answer, Hint 2 after the second, then the last hint."""
    by_method = getattr(node, "hints_by_method", None) or {}
    hints = by_method.get(session.method_id or "") or node.hints
    if not hints or session.fail_streak < 1:
        return None
    return hints[min(session.fail_streak, len(hints)) - 1]


def _staged_hint(raw: str, node: Node, session: Session) -> Optional[str]:
    """graph node form_stages {past, first, second}: the hint for where the student is in forming the equations
    (Stage 3 past ages, 4 the first equation, 5 the second); stuck again at the same stage → its next hint."""
    stages = getattr(node, "form_stages", None)
    pair = linear_pair.node_check(node)
    if not stages or not pair:
        return None
    where = linear_pair.stage(raw, pair[1], session.factored.get(node.id, []), session.letters)
    if where == "past" and session.help_level.get(f"{node.id}#past ages"):
        where = "first"                                       # the past ages were written in an earlier answer
    if where != "past":
        session.help_level[f"{node.id}#past ages"] = 1
    key = f"{node.id}#{where}"
    level = session.help_level.get(key, 0)
    session.help_level[key] = level + 1
    ladder = stages[where]
    return linear_pair.relabel_for(ladder[min(level, len(ladder) - 1)], session.letters)


def _glossary(graph: SolutionGraph) -> List[dict]:
    """graph_meta.glossary: [{term, aliases, definition}], the problem's words a student may not know."""
    return getattr(graph.graph_meta, "glossary", None) or []


def _asks_for_help(raw: str) -> bool:
    """'I don't know what a prime number is', 'what is HCF?': a request for help, not an answer. A line with a
    number left after the unknown part ('I don't know, maybe 70') is still an answer."""
    low = raw.lower().replace("’", "'").replace("‘", "'")
    rest = _without_unknowns(raw)
    if re.search(r"\d", rest):
        return False
    return any(p in low for p in _DONT_KNOW) or (low.strip().endswith("?") and not re.search(r"\d", low))


def _help_terms(raw: str, graph: SolutionGraph) -> List[dict]:
    """The glossary terms the student names, in their order: the longest alias wins ('prime factor' is not
    'prime' + 'factor'); at most two."""
    low = raw.lower().replace("’", "'")
    spans = []
    for entry in _glossary(graph):
        for alias in sorted([entry["term"], *entry.get("aliases", [])], key=len, reverse=True):
            for m in re.finditer(rf"(?<![a-z]){re.escape(alias.lower())}(?![a-z])", low):
                spans.append((m.start(), m.end(), entry))
    spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    chosen, end = [], -1
    for start, stop, entry in spans:
        if start >= end and entry not in chosen:              # spans inside a longer one are skipped
            chosen.append(entry)
            end = stop
    return chosen[:2]


def _help(raw: str, parsed, current: Node, session: Session, graph: SolutionGraph
          ) -> Tuple[StepResult, Optional[str], Optional[dict], Optional[dict]]:
    """'I don't know …' at any question: 'That's fine', the definition of the term named (from the glossary,
    written by the teacher, so always right), then the next hint. It uses up a hint, it is not a wrong answer."""
    terms = _help_terms(raw, graph)
    definitions = [_term_help(t, session) for t in terms]
    laddered = any(t.get("hints") for t in terms)
    if current.type == "choice" and current.concepts_required:   # the plan step: its own "don't know" reply
        result = _plan_step(raw, parsed, current, session, graph, None)
        if definitions and result[3] and not result[3].get("accepted"):
            msg, fine = result[3]["message"], "That's fine."
            result[3]["message"] = (f"{fine} {' '.join(definitions)}{msg[len(fine):]}" if msg.startswith(fine)
                                    else f"{' '.join(definitions)} {msg}")
        return result
    session.current_node_id = current.id
    claim = {"kind": "help", "terms": [t["term"] for t in terms], "definitions": definitions}
    if laddered:                                              # the term's own ladder: the step's hints wait
        return StepResult(verdict="DONT_KNOW", parsed=parsed, node_id=current.id, claim=claim), None, None, None
    session.fail_streak += 1
    return StepResult(verdict="DONT_KNOW", parsed=parsed, node_id=current.id, claim=claim), \
        _staged_hint(raw, current, session) or _hint(current, session), None, None


def _term_help(term: dict, session: Session) -> str:
    """A glossary term with 'hints' (a question, then a worked example) climbs its own ladder each time it is
    asked about; one without gives its definition."""
    hints = term.get("hints")
    if not hints:
        return term["definition"]
    level = session.help_level.get(term["term"], 0)
    session.help_level[term["term"]] = level + 1
    return hints[min(level, len(hints) - 1)]


# ─── Parts (graph_meta.parts): "(ii) 156" picks a part; parts in any order; any correct working counts ─────────
_ROMAN = r"(viii|vii|vi|iv|ix|iii|ii|v|x|i)"                 # longest first: "vi" is not "v" + "i"
_PART_LABEL = re.compile(rf"^\s*(?:part\s*)?(?:\(\s*{_ROMAN}\s*\)|{_ROMAN}\s*\))\s*[:.\-]?\s*"
                         rf"|^\s*part\s+{_ROMAN}\b\s*[:.\-]?\s*", re.I)


def _parts(graph: SolutionGraph) -> List[dict]:
    """[{id, label, title, numbers, nodes}]: the question's parts (i), (ii), …, each with its own questions."""
    return getattr(graph.graph_meta, "parts", None) or []


def _part_of_label(raw: str, graph: SolutionGraph) -> Tuple[Optional[dict], str]:
    """'(ii) 156 ÷ 2 = 78' → (part ii, '156 ÷ 2 = 78'); no label → (None, raw). 'i dont know' is no label."""
    m = _PART_LABEL.match(raw)
    if not m:
        return None, raw
    label = next(g for g in m.groups() if g).lower()
    part = next((p for p in _parts(graph) if p["label"] == label), None)
    return (part, raw[m.end():]) if part else (None, raw)


def _only_selects(rest: str, part: dict) -> bool:
    """'(ii) 156', '(i) 26 and 91', '(iii)', '(i) x² − 2x − 8': only the label and the part's own numbers or text."""
    norm = lambda x: re.sub(r"\s+", "", x.lower().replace("−", "-").replace("^2", "²").replace("**2", "²"))
    if part.get("text") and norm(rest) == norm(part["text"]):
        return True
    t = rest.lower()
    for n in part["numbers"]:
        t = re.sub(rf"(?<!\d){n}(?!\d)", " ", t)
    return not re.sub(r"\b(and|part|number|numbers|pair)\b|[,:.;\-()&]", " ", t).strip()


def _open_parts(graph: SolutionGraph, session: Session) -> List[dict]:
    return [p for p in _parts(graph) if p["id"] not in session.parts_done]


def _menu(graph: SolutionGraph, session: Session) -> str:
    return ", ".join(p["title"] for p in _open_parts(graph, session))


def _part_question(graph: SolutionGraph, session: Session, pid: str) -> Optional[str]:
    part = next(p for p in _parts(graph) if p["id"] == pid)
    i = session.part_pos.get(pid, 0)
    return part["nodes"][i] if i < len(part["nodes"]) else None


def _go_to_part(session: Session, graph: SolutionGraph, pid: str) -> None:
    """Switch parts, keeping each question's hint level and each part's method."""
    if session.current_node_id:
        session.node_fails[session.current_node_id] = session.fail_streak
    session.part = pid
    session.current_node_id = _part_question(graph, session, pid)
    session.fail_streak = session.node_fails.get(session.current_node_id, 0)
    session.method_id = session.part_method.get(pid)


def _start_parts(session: Session, graph: SolutionGraph) -> None:
    """After the plan: every part is open; a line without a label is for the first one."""
    session.parts_active = True
    first = _open_parts(graph, session)[0]
    _go_to_part(session, graph, first["id"])
    others = [p for p in _open_parts(graph, session) if p is not first]
    prompt = _nodes(graph)[session.current_node_id].prompt
    if len(_parts(graph)) == 1:                               # one question: no parts to choose from
        session.prompt_override = prompt
        return
    session.prompt_override = (f"Solve the parts in any order: {_menu(graph, session)}. Write a label to choose one"
                               + (f", like ({others[0]['label']})" if others else "") + f", or start now: {prompt}")


def _other_part(raw: str, graph: SolutionGraph, session: Session) -> Optional[dict]:
    """'3825/5' while solving (i) 140: a line that starts with another part's number."""
    first = re.match(r"\s*\(?\s*(\d+)", raw)
    if not first:
        return None
    n = int(first.group(1))
    current = next((p for p in _parts(graph) if p["id"] == session.part), None)
    if current and any(m % n == 0 for m in current["numbers"]):
        return None
    return next((p for p in _parts(graph) if p is not current and n in p["numbers"]), None)


def _working(answer: str, node: Node) -> Optional[dict]:
    """A step on the way to a prime factorisation of one of node.factorise, by either method:
    division '3825 ÷ 5 = 765' (or just '3825/5'), or a split '3825 = 25 × 153' (a factor tree). The number divided
    or split must be the part's number or one of its factors. {ok, method m1/m2, message}; None: not working."""
    wanted = list(getattr(node, "factorise", None) or [])
    if not wanted:
        return None
    text = re.sub(r"(?<=[\d)])\s*x\s*(?=[\d(])", " * ", _maths(answer))
    found = []
    for piece in (x.strip().rstrip(".") for x in re.split(r"[,;\n]|\band\b|\bthen\b|\bso\b", text)):
        if not piece:
            continue
        m = re.fullmatch(r"(\d+)\s*/\s*(\d+)(?:\s*=\s*(\d+))?", piece)
        if m:
            a, d = int(m.group(1)), int(m.group(2))
            if not any(n % a == 0 for n in wanted):
                return None                                   # not this part's numbers
            if d < 2 or a % d:
                return {"ok": False, "method": "m1",
                        "message": f"{a} ÷ {d} is not a whole number, so {d} is not a factor of {a}."}
            if m.group(3) is not None and int(m.group(3)) != a // d:
                return {"ok": False, "method": "m1", "message": f"{a} ÷ {d} = {a // d}, not {m.group(3)}."}
            found.append(("m1", a, [d, a // d]))
            continue
        sides = [x.strip() for x in piece.split("=")]
        products = [x for x in sides[1:] if "*" in x and _PRODUCT.fullmatch(x.replace(" ", ""))]
        if len(sides) >= 2 and re.fullmatch(r"\d+", sides[0]) and len(products) == len(sides) - 1:
            a = int(sides[0])
            if not any(n % a == 0 for n in wanted):
                return None
            for x in products:
                factors = _factors(x)
                value = int(sp.prod([b ** e for b, e in factors]))
                if value != a:
                    return {"ok": False, "method": "m2", "message": f"{_pretty(x)} = {value}, not {a}."}
                if any(b < 2 for b, _ in factors):
                    return {"ok": False, "method": "m2", "message": "Use factors bigger than 1: splitting off 1 "
                                                                  "does not break the number down."}
            found.append(("m2", a, [b for b, e in _factors(products[-1]) for _ in range(e)]))
            continue
        return None                                           # words or something else: not working
    if not found:
        return None
    method, a, parts = found[-1]
    n = next(w for w in wanted if w % a == 0)
    if method == "m1":
        q = parts[1]
        rest = (f"That's the last division. Now write {n} as a product of all your primes." if q == 1 else
                f"{q} is prime, so you can stop dividing. Now write {n} as a product of primes." if sp.isprime(q)
                else f"Keep going: which prime divides {q}?")
        return {"ok": True, "method": "m1", "message": f"Right: {a} ÷ {parts[0]} = {q}. {rest}"}
    composite = sorted({f for f in parts if not sp.isprime(f)})
    rest = (f"Now break {' and '.join(map(str, composite))} into primes." if composite else
            f"All of these are prime. Now write {n} as a product of primes.")
    return {"ok": True, "method": "m2", "message": f"Right: {a} = {' × '.join(map(str, parts))}. {rest}"}


def _note(verdict: str, message: str, parsed, node_id: Optional[str]):
    return StepResult(verdict=verdict, parsed=parsed, node_id=node_id,
                      claim={"kind": "note", "message": message}), None, None, None


def _part_wrong(raw: str, parsed, node: Node, session: Session, message: Optional[str]):
    session.fail_streak += 1
    hint = _hint(node, session)
    if message:
        claim = {"kind": "value", "isTrue": False, "text": raw, "message": message}
        return StepResult(verdict="WRONG_CLAIM", parsed=parsed, node_id=node.id, claim=claim), hint, None, None
    return StepResult(verdict="WRONG_ANSWER", parsed=parsed, node_id=node.id), hint, None, None


def _part_answered(raw: str, parsed, node: Node, session: Session, graph: SolutionGraph):
    """The part's question is done: its next question, or the next part, or the final answer."""
    pid = session.part
    part = next(p for p in _parts(graph) if p["id"] == pid)
    session.trail.append({"input": raw, "nodeId": node.id, "methodId": session.part_method.get(pid)})
    session.node_fails[node.id] = session.fail_streak = 0
    session.part_pos[pid] = session.part_pos.get(pid, 0) + 1
    nxt = _part_question(graph, session, pid)
    if nxt:
        session.current_node_id = nxt
        return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node.id, method_id=session.method_id), \
            None, None, None
    session.parts_done.append(pid)
    still = _open_parts(graph, session)
    if not still:                                             # every part: the final answer
        session.parts_active, session.part = False, None
        session.current_node_id = graph.conclusion_node
        return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node.id), None, None, None
    _go_to_part(session, graph, still[0]["id"])
    prompt = _nodes(graph)[session.current_node_id].prompt
    session.prompt_override = (f"Part {part['title']} is done. Still to do: {_menu(graph, session)}. "
                               f"Write a label to choose one, or go on: {prompt}")
    return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node.id), None, None, None


def _parts_step(raw: str, parsed, session: Session, graph: SolutionGraph
                ) -> Tuple[StepResult, Optional[str], Optional[dict], Optional[dict]]:
    """One line while solving the parts. A label picks its part; otherwise the line is for the part being solved.
    At a factorise question: a full factorisation of a number counts it; any correct division or split is working
    (either method, Jev names it); a wrong one is a mistake. Other questions are checked as usual."""
    part, rest = _part_of_label(raw, graph)
    if part:
        if part["id"] in session.parts_done:
            return _note("PART", f"Part {part['title']} is already done. Still to do: {_menu(graph, session)}.",
                         parsed, session.current_node_id)
        _go_to_part(session, graph, part["id"])
        if _only_selects(rest, part):
            prompt = _nodes(graph)[session.current_node_id].prompt
            session.prompt_override = prompt
            return _note("PART", f"Part {part['title']}. {prompt}", parsed, session.current_node_id)
        raw = rest
    else:
        other = _other_part(raw, graph, session)
        if other:
            done = other["id"] in session.parts_done
            return _note("PART", f"That looks like part {other['title']}" + (
                ", which is already done." if done else f". To work on it, start with ({other['label']})."),
                parsed, session.current_node_id)
    node = _nodes(graph)[session.current_node_id]
    if _glossary(graph) and _asks_for_help(raw):
        return _help(raw, parsed, node, session, graph)
    answer = _with_pi(raw, graph.graph_meta.problem_text)
    if node.factorise:
        done, _composite, wrong = _factored_numbers(answer, node)
        if done and not wrong:
            have = set(session.factored.get(node.id, [])) | done
            session.factored[node.id] = sorted(have)
            if set(node.factorise) <= have:
                return _part_answered(raw, parsed, node, session, graph)
            left = " and ".join(str(n) for n in node.factorise if n not in have)
            return _note("WORKING", f"Right: {' and '.join(map(str, sorted(done)))} as a product of primes. "
                                    f"Now write {left} too.", parsed, node.id)
        work = _working(answer, node)
        if work and work["ok"]:
            jev = _classify(answer, graph)                    # Jev names the method; the line's form if it can't
            by_jev = method_of(jev.get("methodId")) if jev and jev.get("status") == "selected" else None
            session.part_method[session.part] = session.method_id = by_jev if by_jev in ("m1", "m2") else work["method"]
            session.node_fails[node.id] = session.fail_streak
            return _note("WORKING", work["message"], parsed, node.id)
        if work or wrong:
            if work and work.get("method"):                  # a wrong division is still division: its hints
                session.part_method[session.part] = session.method_id = work["method"]
            return _part_wrong(raw, parsed, node, session, (work or {}).get("message") or wrong)
        return _part_wrong(raw, parsed, node, session, None)
    if getattr(node, "zeroes_of", None):                      # "x = 4", "(x − 4)(x + 2) = 0", "D = 36", …
        found = session.factored.get(node.id, [])
        step = polynomials.zeroes_step(answer, node.zeroes_of, found)
        if step and step.get("method"):
            jev = _classify(answer, graph)                    # Jev names the method; the line's form if it can't
            by_jev = method_of(jev.get("methodId")) if jev and jev.get("status") == "selected" else None
            session.part_method[session.part] = session.method_id = by_jev if by_jev in ("m1", "m2") else step["method"]
        if step and step.get("done"):
            return _part_answered(raw, parsed, node, session, graph)
        if step and step.get("found"):
            session.factored[node.id] = found + [str(v) for v in step["values"] if str(v) not in found]
            if polynomials.zeroes_step(", ".join(session.factored[node.id]), node.zeroes_of, []).get("done"):
                return _part_answered(raw, parsed, node, session, graph)
            return _note("WORKING", step["message"], parsed, node.id)
        if step and step.get("working"):
            session.node_fails[node.id] = session.fail_streak
            return _note("WORKING", step["message"], parsed, node.id)
        return _part_wrong(raw, parsed, node, session, (step or {}).get("message"))
    pair = linear_pair.node_check(node)
    if pair:                                                  # a pair of linear equations: form, solve, verify
        kind, spec = pair
        step = linear_pair.step(kind, answer, spec, session.factored.get(node.id, []), session.letters)
        if step:
            session.letters = step.get("letters", session.letters)
        if step and step.get("method"):
            jev = _classify(answer, graph)
            by_jev = method_of(jev.get("methodId")) if jev and jev.get("status") == "selected" else None
            session.part_method[session.part] = session.method_id = by_jev if by_jev in ("m1", "m2") else step["method"]
        if step and step.get("done"):
            result = _part_answered(raw, parsed, node, session, graph)
            while session.parts_active:                       # the same answer may also solve the next step
                nxt = _nodes(graph).get(session.current_node_id)
                more = linear_pair.node_check(nxt) if nxt else None
                if more and more[0] == "pair_verify":         # a check is written on purpose, not read off working
                    break
                ahead = linear_pair.step(more[0], answer, more[1], [], session.letters) if more else None
                if not ahead or ahead.get("wrong"):
                    break
                if ahead.get("method"):
                    session.part_method[session.part] = session.method_id = ahead["method"]
                if not ahead.get("done"):
                    session.factored[nxt.id] = ahead.get("have", [])
                    break
                result = _part_answered(raw, parsed, nxt, session, graph)
            return result
        if step and (step.get("found") or step.get("working")):
            session.factored[node.id] = step.get("have", session.factored.get(node.id, []))
            session.node_fails[node.id] = session.fail_streak
            return _note("WORKING", step["message"], parsed, node.id)
        if kind == "pair_form" and not step and linear_pair.past_ages(answer, spec, session.letters):
            result = _note("WORKING", linear_pair.relabel_for(
                "Right: five years ago their ages were x − 5 (Nuri) and y − 5 (Sonu).", session.letters),
                parsed, node.id)
            return (result[0], _staged_hint(answer, node, session), None, None)
        result = _part_wrong(raw, parsed, node, session, (step or {}).get("message"))
        staged = _staged_hint(answer, node, session)
        return (result[0], staged or result[1], None, None)
    if getattr(node, "relation_of", None):                   # the sum and the product, in any order
        step = polynomials.relation_step(answer, node.relation_of, session.factored.get(node.id, []))
        if step and step.get("done"):
            return _part_answered(raw, parsed, node, session, graph)
        if step and step["ok"]:
            session.factored[node.id] = step["got"]
            session.node_fails[node.id] = session.fail_streak
            return _note("WORKING", step["message"], parsed, node.id)
        return _part_wrong(raw, parsed, node, session, (step or {}).get("message"))
    res = _check(answer, node, None, graph.graph_meta.problem_text)
    if res.get("accepted"):
        return _part_answered(raw, parsed, node, session, graph)
    result = _part_wrong(raw, parsed, node, session, None)
    if res.get("wrong_claim") and res.get("claim"):          # "LCM = 2 × 7 × 13 = 192": SymPy's finding
        result[0].verdict, result[0].claim = "WRONG_CLAIM", res["claim"]
    return result


def _parts_would_take(raw: str, session: Session, graph: SolutionGraph) -> bool:
    """At the plan step: is this already work on the first part ('140 ÷ 2 = 70', '26 = 2 × 13')?"""
    first = _open_parts(graph, session)
    if not first:
        return False
    node = _nodes(graph)[first[0]["nodes"][session.part_pos.get(first[0]["id"], 0)]]
    answer = _with_pi(raw, graph.graph_meta.problem_text)
    if getattr(node, "zeroes_of", None):
        return polynomials.zeroes_step(answer, node.zeroes_of, []) is not None
    pair = linear_pair.node_check(node)
    if pair:                                                  # equations, labels, past ages, or the answer itself
        return (linear_pair.step(pair[0], answer, pair[1], [], session.letters) is not None
                or (pair[0] == "pair_form" and linear_pair.past_ages(answer, pair[1], session.letters)))
    if getattr(node, "quadratic_with", None):
        return polynomials.quadratic_step(answer, node.quadratic_with) is not None
    if not node.factorise:
        return False
    done, composite, wrong = _factored_numbers(answer, node)
    return bool(done or composite or wrong or _working(answer, node))


def _llm_tutor(graph: SolutionGraph) -> bool:
    """graph_meta.llm_tutor: Qwen reads plans and aims step hints (Q1, Q2, Q6)."""
    return getattr(graph.graph_meta, "llm_tutor", None) is True and plan_llm.enabled()


def _finding(claim: Optional[dict]) -> str:
    """What SymPy found, in words, for the hint writer."""
    if not isinstance(claim, dict):
        return ""
    if claim.get("message"):
        return claim["message"]
    if claim.get("lhs") is not None and claim.get("lhs_val") is not None:
        return f"{claim['lhs']} is {_num(claim['lhs_val'])}, not {claim.get('rhs')}."
    return ""


def _num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:g}"


def _safe_hint(text: str, raw: str, answer: str, node: Node, graph: SolutionGraph) -> bool:
    """SymPy checks Qwen's hint before a student sees it: every maths claim in it must be true, and it must not
    give the step away (it would pass as the answer, or it names the step's value)."""
    if not text or len(text) > 220:
        return False
    try:
        claims = parse_step(text).claims
    except Exception:
        return False
    if any(c.is_true is False for c in claims):               # "2 × 70 = 150": a false hint is never shown
        return False
    problem = graph.graph_meta.problem_text
    if (_check(text, node, None, problem).get("accepted") or matches_accept_any(text, node.accept)
            or (_factor_check(text, node) or {}).get("accepted")):
        return False                                          # "140 = 2² × 5 × 7": that is the answer
    for n in getattr(node, "factorise", None) or []:          # "… 2 × 5 × 7 × 2 = 140": primes that make n
        for m in re.finditer(r"\d+(?:\s*(?:\*\*|\^)\s*\d+)?(?:\s*[*×x]\s*\d+(?:\s*(?:\*\*|\^)\s*\d+)?)+",
                             _maths(text)):
            factors = _factors(m.group(0).replace("^", "**").replace("x", "*"))
            if factors and all(sp.isprime(b) for b, _ in factors) and sp.prod([b ** e for b, e in factors]) == n:
                return False
    known = {_exact(x) for x in re.findall(r"\d+(?:\.\d+)?", f"{problem} {node.prompt} {raw}")}
    for target in _step_values(node):                         # "Is it 13?": the value nobody has written yet
        if target not in known and any(_exact(x) == target for x in re.findall(r"\d+(?:\.\d+)?", text)):
            return False
    return True


def _llm_hint(raw: str, answer: str, node: Node, claim: Optional[dict], fallback: str, session: Session,
              graph: SolutionGraph) -> Optional[str]:
    """Qwen's hint for this wrong answer, checked by SymPy; None → the graph's hint. The last hint (the answer
    itself) always comes from the graph."""
    if len(node.hints) < 2 or session.fail_streak >= len(node.hints):
        return None
    method = next((n.label for n in graph.nodes if n.type == "method" and method_of(n.id) == session.method_id), "")
    text = plan_llm.hint(graph.graph_meta.problem_text, node.prompt, raw, _finding(claim), fallback, method)
    return text if text and _safe_hint(text, raw, answer, node, graph) else None


def _classify(raw: str, graph: SolutionGraph) -> Optional[dict]:
    try:
        return classify_graph(graph, raw)
    except Exception:
        return None


def _attempted_method(jev: Optional[dict], choices: List[Node]) -> Optional[Node]:
    """Which method's first question a wrong answer was aimed at (Jev decides), for its hints."""
    if not jev or jev.get("status") != "selected":
        return None
    return next((c for c in choices if method_of(c.id) == method_of(jev.get("methodId"))), None)


def _jev_view(jev: Optional[dict], graph: SolutionGraph, picked: Optional[str], hinted: Optional[Node]) -> Optional[dict]:
    """What the UI shows at the method choice: Jev's probabilities and one sentence about them."""
    if not jev or not jev.get("probabilities"):
        return None
    labels = {n.id: re.sub(r"^Method \d+:\s*", "", n.label) for n in graph.nodes if n.type == "method"}
    by_prefix = {method_of(k): k for k in labels}
    sure = jev.get("status") == "selected"
    jev_key = jev.get("methodKey") or jev.get("methodId")
    pct = f"{round(100 * (jev.get('confidence') or 0))}%"
    if picked:
        key = by_prefix.get(picked)
        if sure and method_of(jev_key) == picked:
            note = f"Jev identified: {labels.get(key, key)} ({pct})."
        else:
            note = f"You chose {labels.get(key, key)}. Jev could not tell the path from this answer alone."
    elif hinted is not None and sure:
        note = f"Jev thinks you are trying {labels.get(jev_key, jev_key)} ({pct}), so the hint is for that path."
    else:
        note = "Jev could not tell which path you were trying from this answer."
    return {"note": note, "probabilities": jev.get("probabilities"), "labels": labels,
            "status": jev.get("status"), "methodId": jev.get("methodId"), "confidence": jev.get("confidence")}


def _known_values(graph: SolutionGraph) -> List[Tuple[sp.Expr, Optional[str]]]:
    """Every number the solution uses, with its unit if written: each side of each step's accepted answers,
    the final answers and the givens."""
    text = graph.graph_meta.problem_text
    values: List[Tuple[sp.Expr, Optional[str]]] = []
    for n in graph.nodes:
        if n.type in ("step", "conclusion"):
            for accepted in n.accept or []:
                values += [(v, _unit(s)) for s, v in (_sides(_with_pi(accepted, text)) or []) if v is not None]
            for answer in getattr(n, "answer_values", None) or []:
                values += [(v, None) for v in (_exact(f) for f in answer.split("|")) if v is not None]
    values += [(v, None) for v in (_exact(x) for x in re.findall(r"\d+(?:\.\d+)?", text)) if v is not None]
    return values


def _formula(side: str, names: Set[str] = frozenset()) -> Optional[sp.Expr]:
    """'πr²h' → pi*r**2*h: letters are single symbols, π is SymPy's pi; names = the formula's own symbols with a
    number (v1, v2), kept whole. None if it is not a formula in letters."""
    t = _maths(side).replace("π", "@").replace("pi", "@").strip().rstrip(".")
    if not re.search(r"[a-z]", t) or not re.fullmatch(r"[abcdhlrsvwxy@\d\s.*/+\-()]+", t):
        return None                                           # no letters, or words ("total volume × 8")
    t = re.sub(r"(?<=[a-z@])(?=[a-z@])", " ", t).replace("@", " pi ")
    try:
        return parse_expr(t, transformations=standard_transformations + (implicit_multiplication_application,),
                          local_dict={c: sp.Symbol(c) for c in "abcdhlrsvwxy"} | {"pi": sp.pi}
                          | {n: sp.Symbol(n) for n in names})
    except Exception:
        return None


def _letters(side: str, words: Dict[str, str]) -> str:
    """'total volume × 8' → 'v × 8': the words students use for a formula's letters (longest first)."""
    t = _maths(side)
    for phrase in sorted(words, key=len, reverse=True):
        t = re.sub(rf"\b{re.escape(phrase.lower())}s?\b", f" {words[phrase]} ", t)
    return t


def _formula_check(raw: str, node: Node) -> Optional[dict]:
    """'Volume of a cylinder = πr²' against the node's formulas (πr²h). None when the line names no formula."""
    parts = [p.strip() for p in raw.split("=")]
    if len(parts) < 2:
        return None
    label = re.sub(r"[^a-z0-9 ]", "", parts[0].lower()).strip()
    formulas = getattr(node, "formulas", None) or []
    targets = [parse_expr(f.expression, local_dict={"pi": sp.pi}) for f in formulas]   # two may share a name
    known = {str(x) for t in targets for x in t.free_symbols}   # every letter of this node: v1, r1, h1 …
    exact = [i for i, f in enumerate(formulas) if any(re.fullmatch(rf"{l}\d*", label) for l in f.labels)]
    for i in exact + [i for i in range(len(formulas)) if i not in exact]:   # "total volume =": that formula first
        f = formulas[i]
        if not any(re.fullmatch(rf"{l}\d*", label) or re.search(rf"\b{l}\b", label) for l in f.labels):
            continue
        target = targets[i]
        letters = {str(x) for x in target.free_symbols}       # r, h: "total volume = v1 + v2" is not this formula
        written = [(p, _formula(_letters(p, f.words), known)) for p in parts[1:]]
        written = [(p, e) for p, e in written if e is not None
                   and ({str(x) for x in e.free_symbols} & letters or (e.has(sp.pi) and target.has(sp.pi)))
                   and not ({str(x) for x in e.free_symbols} - letters) & known]   # another formula's letters
        if not written:
            continue
        bad = next((p for p, e in written if sp.simplify(e - target) != 0), None)
        if bad is None:
            return {"accepted": True}
        return {"accepted": False, "wrong_claim": True,
                "claim": {"kind": "value", "isTrue": False, "text": raw,
                          "message": f"{bad} is not the formula for the {f.name}. Check the formula."}}
    return None


def _free_step(raw: str, answer: str, parsed, session: Session, graph: SolutionGraph
               ) -> Tuple[StepResult, Optional[str], Optional[dict], Optional[dict]]:
    """After the plan (solve_freely). Several lines in one answer are checked one by one, like single lines:
    the first mistake is reported, a line of words only is skipped, the final answer ends the problem."""
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if len(lines) <= 1:
        return _free_line(raw, answer, parsed, session, graph)
    checked = None
    for line in lines:
        result = _free_line(line, _with_pi(line, graph.graph_meta.problem_text), parse_step(line), session, graph)
        if result[0].verdict == "UNPARSED":
            continue
        result[0].parsed = parsed
        if result[0].verdict != "ACCEPT":                     # a mistake, a unit to fix, or the final answer
            return result
        checked = result
    return checked or (StepResult(verdict="UNPARSED", parsed=parsed, node_id=session.current_node_id), None, None, None)


def _free_line(raw: str, answer: str, parsed, session: Session, graph: SolutionGraph
               ) -> Tuple[StepResult, Optional[str], Optional[dict], Optional[dict]]:
    """One line after the plan: any order, either path. Feedback only on mistakes; done at the answer."""
    nodes = _nodes(graph)
    node_id = session.current_node_id
    concl = nodes[graph.conclusion_node]
    final = _conclusion_check(answer, concl, graph.graph_meta.problem_text) or {}
    if final.get("wrong_claim"):
        return StepResult(verdict="WRONG_CLAIM", parsed=parsed, node_id=node_id, claim=final["claim"]), None, None, None
    sides = _sides(answer)
    numbers = [(s, v) for s, v in sides or [] if v is not None]
    broken = _broken_chain(numbers) if numbers else None
    if broken:
        return StepResult(verdict="WRONG_CLAIM", parsed=parsed, node_id=node_id, claim=broken["claim"]), None, None, None
    unit_issue = _unit_check(answer, graph, session)          # the maths is right: is the unit?
    if unit_issue:
        return StepResult(verdict="UNIT_ISSUE", parsed=parsed, node_id=node_id, claim=unit_issue), None, None, None
    if final.get("accepted"):
        try:
            from app.engine.tutor_engine import check_dag_step_jump
            jump = check_dag_step_jump(session, concl.id, graph, raw_input=raw)
            if jump and jump.get("is_jump"):
                first_skipped = jump["first_skipped"]
                skipped_label = first_skipped.get("label") or first_skipped.get("id")
                skipped_prompt = first_skipped.get("prompt") or "what is the next step?"
                return (
                    StepResult(
                        verdict="STEP_JUMP",
                        parsed=parsed,
                        node_id=node_id,
                        method_id=session.method_id,
                        feedback=(
                            f"That is the final answer, but in Socratic learning you must prove each step first. "
                            f"Please show your work step-by-step: {skipped_prompt}"
                        ),
                    ),
                    None,
                    None,
                    None,
                )
        except Exception:
            pass
        session.completed, session.current_node_id = True, concl.id
        session.trail.append({"input": raw, "nodeId": concl.id, "methodId": session.method_id})
        return StepResult(verdict="CONCLUSION_RIGHT", parsed=parsed, node_id=concl.id), None, None, None

    formula = _formula_check(raw, nodes[node_id]) if node_id in nodes else None   # 'V = πr²' (letters, not numbers)
    if formula is not None:
        if formula.get("accepted"):
            session.trail.append({"input": raw, "nodeId": node_id, "methodId": session.method_id})
            return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node_id, method_id=session.method_id), None, None, None
        return StepResult(verdict="WRONG_CLAIM", parsed=parsed, node_id=node_id, claim=formula["claim"]), None, None, None

    steps = [n for n in graph.nodes if n.type == "step"]
    if session.method_id:
        m_curr = method_of(session.method_id) or session.method_id
        steps = sorted(steps, key=lambda n: 0 if (method_of(n.id) == m_curr or method_of(n.id) == session.method_id) else 1)
    if numbers:
        last, value = numbers[-1]
        unit = _unit(last)                                    # "111532.8 g": that value is in cm³, not g
        units = [u for k, u in _known_values(graph) + session.free_values if _close(last, value, k)]
        other = next((u for u in units if u and unit and u != unit), None)
        if not units or other:
            message = (f"{_pretty(_UNIT.sub('', last).strip())} is in {_show_unit(other)} here, not {_show_unit(unit)}. "
                       "Check the step." if other else
                       f"{_pretty(last)} is not a number this problem needs. Check the numbers you used.")
            claim = {"kind": "value", "isTrue": False, "text": raw, "got": str(value), "message": message}
            return StepResult(verdict="WRONG_CLAIM", parsed=parsed, node_id=node_id, claim=claim), None, None, None
        session.free_values.extend((v, _unit(s)) for s, v in numbers)
        matched = next((n for n in steps if any(_close(last, value, t) for t in _step_values(n))), None)
    else:                                                     # words: "volume of big cylinder is 99475.2"
        matched = next((n for n in steps if _check(answer, n, None, graph.graph_meta.problem_text).get("accepted")), None)
        if matched is None:                                   # nothing to check: not called a mistake
            return StepResult(verdict="UNPARSED", parsed=parsed, node_id=node_id), None, None, None
    if matched is not None:
        session.method_id = method_of(matched.id) or session.method_id
        try:
            from app.engine.tutor_engine import check_dag_step_jump
            jump = check_dag_step_jump(session, matched.id, graph)
            if jump and jump.get("is_jump"):
                first_skipped = jump["first_skipped"]
                skipped_label = first_skipped.get("label") or first_skipped.get("id")
                skipped_prompt = first_skipped.get("prompt") or "what is the next step?"
                return (
                    StepResult(
                        verdict="STEP_JUMP",
                        parsed=parsed,
                        node_id=node_id,
                        method_id=session.method_id,
                        feedback=(
                            f"That calculation is part of {skipped_label}, but you leaped ahead without showing intermediate work. "
                            f"Please show your work step-by-step first: {skipped_prompt}"
                        ),
                    ),
                    None,
                    None,
                    None,
                )
        except Exception:
            pass
    session.fail_streak = 0
    session.trail.append({"input": raw, "nodeId": matched.id if matched else node_id, "methodId": session.method_id})
    return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node_id, method_id=session.method_id), None, None, None


def _plan_step(raw: str, parsed, current: Node, session: Session, graph: SolutionGraph,
               jev: Optional[dict]) -> Tuple[StepResult, Optional[str], Optional[dict], Optional[dict]]:
    """A choice node with concepts_required: the student explained a plan in words (concept_choice.py)."""
    nodes = _nodes(graph)
    methods = [m for m in _next_of(current.id, graph) if m in nodes and nodes[m].type == "method"]
    explaining = bool((session.plan_progress or {}).get("explain"))
    out = evaluate_plan(raw, current, jev, session.scaffold_index, session.fail_streak, methods[0] if methods else None,
                        None if explaining else check_plan(raw, current),   # Qwen + SymPy; None without Ollama
                        session.plan_progress, plan_llm.says if _llm_tutor(graph) else None)
    session.scaffold_index = out.scaffold_index
    session.plan_progress = out.progress
    session.current_node_id = current.id
    if not out.accepted:
        if out.scaffold_index is None and out.category != "explain":   # a scaffold or explain step is no failure
            session.fail_streak += 1
        hint = out.concept_hint["question"] if out.concept_hint else None
        return StepResult(verdict="PLAN_FEEDBACK", parsed=parsed, node_id=current.id), hint, None, out.model_dump()
    if _parts(graph):                                         # the plan is done: now the parts, in any order
        session.fail_streak = 0
        session.scaffold_index = None
        session.plan_progress = None
        session.trail.append({"input": raw, "nodeId": current.id, "methodId": None})
        _start_parts(session, graph)
        return StepResult(verdict="ACCEPT", parsed=parsed, node_id=current.id), None, None, out.model_dump()
    path = out.path if out.path in methods else methods[0]
    out.path = path
    session.fail_streak = 0
    session.scaffold_index = None
    session.plan_progress = None
    session.method_id = method_of(path)
    session.trail.append({"input": raw, "nodeId": path, "methodId": method_of(path)})
    session.free_solving = bool(current.solve_freely)
    session.current_node_id = current.id if session.free_solving else _question_after(path, graph)
    # the path comes from Jev when it is sure, else from the plan's words (path_signals): no Jev note here
    return StepResult(verdict="ACCEPT", parsed=parsed, node_id=path, method_id=method_of(path)), None, None, out.model_dump()


def _plan_questions(raw: str, answer: str, parsed, node: Node, session: Session, graph: SolutionGraph):
    """node.plan_questions: "I don't know" at a plan with nothing said yet starts the questions, asked one by one;
    each must be answered before the next. check: 'keywords' (every group, 'a|b' either), 'past' (both past ages),
    'equation' (the graph's pair equation 'index'). After the last, the equations are formed: on to solving."""
    qs = node.plan_questions
    progress = session.plan_progress or {}
    if session.plan_q is None:
        if progress.get("found") or progress.get("given") or not _asks_for_help(raw) or _help_terms(raw, graph):
            return None
        session.plan_q, session.plan_q_fails = 0, 0
        session.prompt_override = qs[0]["question"]
        claim = {"kind": "help", "terms": [], "definitions": ["Let's work it out together, one question at a time."]}
        return StepResult(verdict="DONT_KNOW", parsed=parsed, node_id=node.id, claim=claim), qs[0]["question"], \
            None, None
    q = qs[session.plan_q]
    form = next(n for n in _nodes(graph).values() if getattr(n, "pair_form", None))
    spec = form.pair_form
    found = linear_pair.labels(raw, spec)
    if found:
        session.letters = found
    have = session.factored.get(form.id, [])
    step = linear_pair.step("pair_form", answer, spec, have, session.letters)
    if step and not step.get("wrong"):
        have = session.factored[form.id] = step.get("have", have)

    def ask_again(verdict: str, message: Optional[str]):
        session.plan_q_fails += 1
        hints = [linear_pair.relabel_for(h, session.letters) for h in q.get("hints", [])]
        hint = hints[min(session.plan_q_fails, len(hints)) - 1] if hints else q["question"]
        session.prompt_override = q["question"]
        if verdict == "DONT_KNOW":
            terms = _help_terms(raw, graph)
            claim = {"kind": "help", "terms": [t["term"] for t in terms],
                     "definitions": [_term_help(t, session) for t in terms] or ["Here is a hint."]}
        else:
            claim = {"kind": "value", "isTrue": False, "text": raw, "message": message} if message else None
            verdict = "WRONG_CLAIM" if message else "WRONG_ANSWER"
        return StepResult(verdict=verdict, parsed=parsed, node_id=node.id, claim=claim), hint, None, None

    if step and step.get("done"):                             # both equations already: nothing left to ask
        ok, session.plan_q = True, len(qs) - 1
    elif _asks_for_help(raw):
        return ask_again("DONT_KNOW", None)
    elif step and step.get("wrong") and step.get("relation") == q.get("index") and q.get("check") == "equation":
        nxt = linear_pair.relabel_for(spec["relation_next"][q["index"]], session.letters)
        session.prompt_override = nxt                         # "x = 3y" answers the question as asked: now "then"
        return _note("WORKING", f"Right: that is the relationship. {nxt}", parsed, node.id)
    elif step and step.get("wrong"):
        return ask_again("WRONG", step["message"])
    else:
        low = answer.lower().replace("−", "-").replace("–", "-")
        groups = q.get("keywords", [])
        by_words = bool(groups) and all(any(_has(low, a) for a in g.lower().split("|")) for g in groups)
        check = q.get("check", "keywords")
        if check == "equation":
            ok = str(q["index"]) in have
        elif check == "past":
            ok = linear_pair.past_ages(answer, spec, session.letters) or by_words
        else:
            ok = by_words or bool(found)
        if not ok:
            return ask_again("WRONG", linear_pair.relabel_for(q["wrong"], session.letters) if q.get("wrong") else None)
    session.plan_q_fails = 0
    if session.plan_q + 1 < len(qs):
        session.plan_q += 1
        nxt = linear_pair.relabel_for(qs[session.plan_q]["question"], session.letters)
        session.prompt_override = nxt
        return _note("WORKING", f"Right. {nxt}", parsed, node.id)
    session.plan_q = None                                     # all answered: the equations are formed
    session.plan_progress = None
    session.trail.append({"input": raw, "nodeId": node.id})
    _start_parts(session, graph)
    session.prompt_override = None
    if set(map(str, range(len(spec["equations"])))) <= set(have):
        _part_answered(raw, parsed, form, session, graph)     # on to solving
    return _note("WORKING", "Right: you have both equations. Now solve them.", parsed, node.id)


def guided_step(raw: str, session: Session, graph: SolutionGraph
                ) -> Tuple[StepResult, Optional[str], Optional[dict], Optional[dict]]:
    """Check one answer, advance the session, and return (result, hint, Jev's view at a method choice,
    the plan outcome at a conceptual choice node)."""
    nodes = _nodes(graph)
    parsed = parse_step(raw)
    current = nodes.get(session.current_node_id or "") or nodes[first_question(graph)]
    equation = getattr(graph.graph_meta, "equation", None)
    answer = _with_pi(raw, graph.graph_meta.problem_text)     # the text SymPy and the matcher check
    session.prompt_override = None                            # set again below when the next prompt differs
    if session.free_solving:
        return _free_step(raw, answer, parsed, session, graph)
    if current.type == "choice" and getattr(current, "plan_questions", None):
        asked = _plan_questions(raw, answer, parsed, current, session, graph)
        if asked:
            return asked
    if session.parts_active and _parts(graph):               # "(ii) 156 ÷ 2 = 78": the parts, in any order
        return _parts_step(raw, parsed, session, graph)
    if (_parts(graph) and current.type == "choice" and current.concepts_required
            and not (session.plan_progress or {}).get("explain")
            and (_part_of_label(raw, graph)[0] or _parts_would_take(raw, session, graph))):
        _start_parts(session, graph)                          # work instead of a plan: go straight to the parts
        session.prompt_override = None
        return _parts_step(raw, parsed, session, graph)
    if current.type == "choice" and (session.plan_progress or {}).get("explain"):
        return _plan_step(raw, parsed, current, session, graph, None)   # "each cm³ weighs 8 g" explains, not solves
    if _glossary(graph) and _asks_for_help(raw):              # "I don't know what a prime is": help, not wrong
        return _help(raw, parsed, current, session, graph)
    if current.type == "choice" and current.solve_freely:   # the plan step also takes a direct calculation
        solved = _free_step(raw, answer, parsed, session, graph)
        if solved[0].verdict != "UNPARSED":                   # maths found: it is solving, not a plan
            session.free_solving = session.plan_skipped = True
            return solved

    # 1. which answers to try, in order: a choice tries every method's first question; otherwise the exact
    #    answer to this question, then the exact answer to a later one (skipping ahead), then any correct form
    if current.type == "choice":
        candidates = [(node, "full") for node in _choices(current, graph)]
    else:
        later = _later_steps(current.id, graph) if current.type == "step" else []
        candidates = [(current, "exact"), (current, "full")] + [(node, "exact") for node in later]

    jev = _classify(raw, graph) if current.type == "choice" else None
    wrong = None
    for node, mode in candidates:
        is_current_candidate = (node.id == current.id)
        if mode == "exact":
            if _forbidden(answer, node) or not matches_accept_any(answer, node.accept):
                continue
            if node.type == "step" and (_equation_check(answer, equation) or {}).get("wrong_claim"):
                continue
            maths = _factor_check(answer, node) or _value_check(answer, node)   # text alike, maths wrong:
            if maths is not None and not maths.get("accepted"):                 # "3825 = 3 × 5² × 17"
                continue
            res = {"accepted": True}
        else:
            res = _check(answer, node, equation, graph.graph_meta.problem_text)
            if res.get("accepted") and current.type == "step":
                node = _furthest_with_same_answer(answer, node, graph)
        if res.get("accepted"):
            if not is_current_candidate and node.id != current.id:
                try:
                    from app.engine.tutor_engine import check_dag_step_jump
                    jump = check_dag_step_jump(session, node.id, graph, raw_input=raw)
                    if jump and jump.get("is_jump"):
                        first_skipped = jump["first_skipped"]
                        skipped_label = first_skipped.get("label") or first_skipped.get("id")
                        skipped_prompt = first_skipped.get("prompt") or "what is the next step?"
                        target_label = getattr(node, "label", None) or node.id
                        return (
                            StepResult(
                                verdict="STEP_JUMP",
                                parsed=parsed,
                                node_id=current.id,
                                method_id=method_of(node.id) or session.method_id,
                                feedback=(
                                    f"That calculation is part of {target_label}, but you leaped ahead without showing intermediate work. "
                                    f"Please show your work step-by-step first: {skipped_prompt}"
                                ),
                            ),
                            None,
                            None,
                            None,
                        )
                except Exception:
                    pass
            session.fail_streak = 0
            session.scaffold_index = None
            session.method_id = method_of(node.id) or session.method_id
            session.trail.append({"input": raw, "nodeId": node.id, "methodId": method_of(node.id)})
            if node.type == "conclusion":
                try:
                    from app.engine.tutor_engine import check_dag_step_jump
                    jump = check_dag_step_jump(session, node.id, graph, raw_input=raw)
                    if jump and jump.get("is_jump"):
                        first_skipped = jump["first_skipped"]
                        skipped_label = first_skipped.get("label") or first_skipped.get("id")
                        skipped_prompt = first_skipped.get("prompt") or "what is the next step?"
                        return (
                            StepResult(
                                verdict="STEP_JUMP",
                                parsed=parsed,
                                node_id=current.id,
                                method_id=method_of(node.id) or session.method_id,
                                feedback=(
                                    f"That is the final answer, but in Socratic learning you must prove each step first. "
                                    f"Please show your work step-by-step: {skipped_prompt}"
                                ),
                            ),
                            None,
                            None,
                            None,
                        )
                except Exception:
                    pass
                session.completed = True
                session.current_node_id = node.id
                return StepResult(verdict="CONCLUSION_RIGHT", parsed=parsed, node_id=node.id), None, None, None
            session.current_node_id = _question_after(node.id, graph)
            if current.type == "choice" and current.solve_freely:   # a calculation instead of a plan: go on alone
                session.free_solving, session.current_node_id = True, current.id
                session.free_values.extend((v, _unit(s)) for s, v in (_sides(answer) or []) if v is not None)
            view = _jev_view(jev, graph, method_of(node.id), None) if current.type == "choice" else None
            return StepResult(verdict="ACCEPT", parsed=parsed, node_id=node.id,
                              method_id=method_of(node.id)), None, view, None
        claim = res.get("claim")
        # a wrong number ("0.08", "4 kinds") is a wrong answer; "P(E) = 1 + 0.992" is a wrong calculation
        bare_number = isinstance(claim, dict) and claim.get("kind") == "value" and not claim.get("message") and not (
            claim.get("text") == answer and "=" in answer)
        if res.get("wrong_claim") and wrong is None and not bare_number:
            wrong = (node, claim)

    # 2. a plan in words at a conceptual choice node (a wrong calculation or bare number keeps step 3's hints)
    words = re.search(r"[a-z]{2,}", _UNIT.sub("", _maths(answer)))
    if current.type == "choice" and current.concepts_required and (
            session.scaffold_index is not None or (wrong is None and words)):
        return _plan_step(raw, parsed, current, session, graph, jev)

    # 3. wrong: count it and give the next hint of the question the student was answering
    session.fail_streak += 1
    session.current_node_id = current.id
    hint_node, view = current, None
    if current.type == "choice":
        attempted = _attempted_method(jev, [n for n, _ in candidates])
        hint_node = attempted or (wrong[0] if wrong else None) or current
        view = _jev_view(jev, graph, None, attempted)
    hint = _hint(hint_node, session)
    if hint and _llm_tutor(graph) and plan_llm.hints_enabled():   # Qwen aims the hint; SymPy checks it
        hint = _llm_hint(raw, answer, hint_node, wrong[1] if wrong else None, hint, session, graph) or hint
    if wrong:
        return StepResult(verdict="WRONG_CLAIM", parsed=parsed, node_id=current.id, claim=wrong[1]), hint, view, None
    return StepResult(verdict="WRONG_ANSWER", parsed=parsed, node_id=current.id), hint, view, None
