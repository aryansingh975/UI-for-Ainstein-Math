"""
sympy_validator.py — checks that each line of a student's work is mathematically
correct. Jev decides WHICH method the student is using; SymPy decides whether
what they wrote is TRUE.

    validate(student_work, equation="x**2 - 5*x + 6 = 0")

What it checks
  • Rewrites of the equation      x² − 2x − 3x + 6 = 0, (x−2)(x−3) = 0, (x − 5/2)² = 1/4
      → must have the same solutions as the original equation
  • Rewrites of the expression    x² − 2x − 3x + 6   (no "=")
      → must equal the original polynomial (up to a constant factor)
  • Claimed roots                 x = 2 or x = 3, x = (5 ± 1)/2
      → each value must be a real root; missing roots are reported
  • Coefficients                  a = 1, b = −5, c = 6
  • Discriminant                  D = b² − 4ac = 25 − 24 = 1, D = 1 > 0
  • Function values               f(2) = 4 − 10 + 6 = 0
  • Sum / product of roots        α + β = 5, αβ = 6
  • Pure arithmetic / ratios      3 × 96 = 288, 72:96 → 36:48, 72/96 = 3/4
Anything it can't parse is marked "unchecked" (never "wrong").
"""

from __future__ import annotations

import re
from itertools import permutations

import sympy as sp
from sympy.parsing.sympy_parser import (convert_xor, implicit_multiplication_application,
                                        parse_expr, split_symbols_custom,
                                        standard_transformations)

X = sp.Symbol("x")
A, B, C, D = sp.symbols("a b c D")
ALPHA, BETA = sp.symbols("α β")
F = sp.Function("f")

_KEEP_NAMES = {"sqrt", "gcd", "lcm", "hcf", "HCF", "GCD", "LCM", "f", "α", "β", "pi"}


def _can_split(name: str) -> bool:
    return name not in _KEEP_NAMES and name.isascii() and name.isalpha() and len(name) > 1


TRANSFORMS = standard_transformations + (convert_xor, split_symbols_custom(_can_split),
                                         implicit_multiplication_application)
LOCALS = {"x": X, "a": A, "b": B, "c": C, "D": D, "α": ALPHA, "β": BETA, "f": F,
          "sqrt": sp.sqrt, "gcd": sp.gcd, "hcf": sp.gcd, "HCF": sp.gcd, "GCD": sp.gcd,
          "lcm": sp.lcm, "LCM": sp.lcm, "pi": sp.pi,
          # stop SymPy treating these letters as built-ins (E, I, S, N, O, Q)
          **{k: sp.Symbol(k) for k in "EISNOQ"}}

REL = r"(<=|>=|!=|≠|≤|≥|=|<|>)"
SPLIT_WORDS = r"\b(?:or|and|so|then|therefore|hence|thus|since|because|where)\b|[,;:∴]|\n"


# ---------------------------------------------------------------------------
# Text clean-up
# ---------------------------------------------------------------------------
def _latex_to_plain(s: str) -> str:
    s = s.replace("\\(", "").replace("\\)", "").replace("$", "")
    s = re.sub(r"\\d?frac", r"\\frac", s)
    for k, v in {r"\pm": "±", r"\times": "*", r"\cdot": "*", r"\div": "/", r"\left": "",
                 r"\right": "", r"\alpha": "α", r"\beta": "β", r"\neq": "≠", r"\leq": "≤",
                 r"\geq": "≥", r"\Delta": "D", r"\therefore": "∴", r"\to": "→",
                 r"\Rightarrow": "→", r"\implies": "→"}.items():
        s = s.replace(k, v)
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\^\{([^{}]*)\}", r"^(\1)", s)
        s = re.sub(r"\\sqrt\{([^{}]*)\}", r"sqrt(\1)", s)
        s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"((\1)/(\2))", s)
    s = re.sub(r"\\text\{([^{}]*)\}", r" \1 ", s)
    s = re.sub(r"\\[,;:! ]", " ", s)
    return s.replace("{", "(").replace("}", ")")


def _clean(s: str) -> str:
    s = re.sub(r"(?i)\b(?:step|line)\s*\d+\s*[:.)-]", "\n", s)   # 'Step 1:' labels
    s = _latex_to_plain(s)
    for k, v in {"−": "-", "–": "-", "×": "*", "÷": "/", "·": "*", "²": "^2", "³": "^3",
                 "√": "sqrt", "+/-": "±", "+-": "±", "≤": "<=", "≥": ">=", "≠": "!=",
                 "→": "=", "⇒": "=", "=>": "=", "::": "=", "alpha": "α", "beta": "β",
                 "Δ": "D"}.items():
        s = s.replace(k, v)
    s = re.sub(r"sqrt\s*(\d+(?:\.\d+)?|[a-zA-Z])", r"sqrt(\1)", s)       # √1 → sqrt(1)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", r"(\1/\2)", s)  # 72:96 → (72/96)
    s = re.sub(r"(?<=[\d\s)])x(?=\s*\d)", "*", s)                       # 3 x 96 → 3*96
    return s


# ---------------------------------------------------------------------------
# Problem context
# ---------------------------------------------------------------------------
class Problem:
    def __init__(self, equation: str | None):
        self.poly = None
        self.roots: list = []
        self.values: dict = {}
        if not equation:
            return
        lhs, rhs = _clean(equation).split("=")
        p = sp.expand(_parse(lhs) - _parse(rhs))
        self.poly = p
        self.roots = sorted(sp.solve(sp.Eq(p, 0), X), key=lambda r: complex(r).real)
        coeffs = sp.Poly(p, X).all_coeffs()
        if len(coeffs) == 3:
            a, b, c = coeffs
            self.values = {A: a, B: b, C: c, D: b ** 2 - 4 * a * c}


def pretty(e) -> str:
    """SymPy/plain text -> student-friendly: x**2 - 5*x -> x² − 5x, (x-2)*(x+3) -> (x − 2)(x + 3)."""
    t = e if isinstance(e, str) else sp.sstr(e)
    t = t.replace("**2", "²").replace("**3", "³").replace("^2", "²").replace("^3", "³").replace("**", "^")
    t = t.replace(")*(", ")(")
    t = re.sub(r"(\d)\s*\*\s*(?=[a-zα-ω(])", r"\1", t)        # 5*x -> 5x
    t = re.sub(r"\s*\*\s*", " × ", t)
    t = re.sub(r"(?<=[\w)²³ ])-(?=[\w( ])", "−", t)          # minus sign
    t = re.sub(r"(^|[\s(=])-(?=[\w(])", r"\1−", t)          # leading minus: -5 -> −5
    return t


def _parse(s: str):
    return parse_expr(s.strip(), local_dict=LOCALS, transformations=TRANSFORMS, evaluate=True)


def _same_solutions(expr, prob: Problem) -> bool:
    try:
        sols = sp.solve(sp.Eq(sp.expand(expr), 0), X)
    except Exception:
        return False
    return set(map(sp.nsimplify, sols)) == set(map(sp.nsimplify, prob.roots))


def _equal(u, v) -> bool:
    try:
        return sp.simplify(u - v) == 0
    except Exception:
        return False


def _holds(u, op, v) -> bool:
    if op == "=":
        return _equal(u, v)
    if op == "!=":
        return not _equal(u, v)
    try:
        return bool({"<": u < v, ">": u > v, "<=": u <= v, ">=": u >= v}[op])
    except TypeError:
        return False


def _substitute(e, prob: Problem, order):
    e = e.subs(prob.values)
    if prob.poly is not None:
        e = e.replace(F, lambda k: prob.poly.subs(X, k))
        if order:
            e = e.subs({ALPHA: order[0], BETA: order[1]})
    return e


# ---------------------------------------------------------------------------
# One statement (no "or"/"," inside), possibly a chain  A = B = C > 0
# ---------------------------------------------------------------------------
def _check_statement(text: str, prob: Problem) -> dict:
    # "x = (5 ± 1)/2 = 3"  ->  check "x = (5 ± 1)/2" and "x = 3" separately
    if "±" in text and re.match(r"\s*x\s*=", text) and not re.search(r"[<>!]", text):
        parts = text.split("=")
        last_pm = max(i for i, p in enumerate(parts) if "±" in p)
        if last_pm < len(parts) - 1:
            head = _check_statement("=".join(parts[:last_pm + 1]), prob)
            if head["status"] != "root_claim":
                return head
            vals = list(head["values"])
            for t in parts[last_pm + 1:]:
                r = _check_variant(f"x = {t}", prob)
                if r["status"] != "root_claim":
                    return r
                vals += r["values"]
            return {"status": "root_claim", "values": vals}
    variants = [text.replace("±", "+"), text.replace("±", "-")] if "±" in text else [text]
    results = [_check_variant(v, prob) for v in variants]
    if len(results) == 2 and all(r["status"] == "root_claim" for r in results):
        return {"status": "root_claim", "values": results[0]["values"] + results[1]["values"]}
    for r in results:
        if r["status"] != "valid" and r["status"] != "root_claim":
            return r
    return results[0]


def _check_variant(text: str, prob: Problem) -> dict:
    tokens = re.split(REL, text)
    parts, ops = tokens[0::2], tokens[1::2]
    try:
        exprs = [_parse(p) for p in parts]
    except Exception:
        return {"status": "unchecked", "reason": "could not read this as maths"}
    if any(p.strip() == "" for p in parts):
        return {"status": "unchecked", "reason": "incomplete expression"}

    has_x = any(e.has(X) for e in exprs)

    # --- expression only (no relation) ---------------------------------
    if not ops:
        e = exprs[0]
        if (has_x and prob.poly is not None and isinstance(sp.expand(e), sp.Add)
                and sp.degree(prob.poly, X) >= 2):
            ratio = sp.simplify(e / prob.poly)
            if ratio.free_symbols == set() and ratio != 0:
                return {"status": "valid", "kind": "rewrite of the expression"}
            return {"status": "invalid", "kind": "rewrite of the expression",
                    "message": f"{pretty(e)} is not equal to {pretty(prob.poly)}."}
        return {"status": "unchecked", "reason": "no statement to check"}

    # --- root claim  x = number ------------------------------------------
    if has_x and len(exprs) >= 2 and exprs[0] == X and parts[0].strip() == "x" and not any(e.has(X) for e in exprs[1:]):
        vals = [sp.nsimplify(e) for e in exprs[1:]]
        if len(set(vals)) > 1:
            return {"status": "invalid", "kind": "calculation",
                    "message": "The values in this chain are not equal."}
        return {"status": "root_claim", "values": [vals[-1]]}

    # --- statements with x: rewrites / equivalent equations --------------
    if has_x:
        if prob.poly is None:
            return {"status": "unchecked", "reason": "no equation given for the problem"}
        for i, (u, op, v) in enumerate(zip(exprs, ops, exprs[1:])):
            if op != "=":
                return {"status": "unchecked", "reason": "inequality in x"}
            if sp.expand(u - v) == 0:
                continue                          # identity: a valid rewrite
            if not _same_solutions(u - v, prob):
                sols = sp.solve(sp.Eq(u, v), X)
                gives = f" It gives x = {pretty(sols[0])}, but the answer should be x = {pretty(prob.roots[0])}." \
                    if len(sols) == 1 and len(prob.roots) == 1 else ""
                return {"status": "invalid", "kind": "equation",
                        "message": f"{pretty(parts[i].strip())} = {pretty(parts[i + 1].strip())} does not have the same "
                                   f"solutions as the original equation.{gives}"}
        return {"status": "valid", "kind": "equation"}

    # --- coefficient definitions  a = 1 ----------------------------------
    if len(exprs) == 2 and exprs[0] in (A, B, C) and prob.values:
        true = prob.values[exprs[0]]
        if _equal(_substitute(exprs[1], prob, None), true):
            return {"status": "valid", "kind": "coefficient"}
        return {"status": "invalid", "kind": "coefficient",
                "message": f"{exprs[0]} should be {pretty(true)}, not {pretty(exprs[1])}."}

    # --- numeric chains (discriminant, f(k), α/β, arithmetic, ratios) ----
    orders = list(permutations(prob.roots, 2)) if (prob.roots and len(prob.roots) == 2) else [None]
    for order in orders:
        vals = [_substitute(e, prob, order) for e in exprs]
        if any(v.free_symbols for v in vals):
            return {"status": "unchecked", "reason": "contains letters that can't be evaluated"}
        bad = [i for i, (u, op, v) in enumerate(zip(vals, ops, vals[1:])) if not _holds(u, op, v)]
        if not bad:
            kind = "discriminant" if any(e.has(D) for e in exprs) else "calculation"
            return {"status": "valid", "kind": kind}
    i = bad[0]
    lhs, rhs = parts[i].strip(), parts[i + 1].strip()
    if exprs[0] == D and i == 0:
        msg = f"D should be b² − 4ac = {pretty(prob.values[D])}, but {pretty(rhs)} = {pretty(vals[1])}."
    else:
        msg = f"{pretty(lhs)} {ops[i]} {pretty(rhs)} is not true ({pretty(vals[i])} vs {pretty(vals[i + 1])})."
    return {"status": "invalid", "kind": "calculation", "message": msg}


_MATH_WORDS = {"sqrt", "gcd", "lcm", "hcf", "HCF", "GCD", "LCM", "pi", "f"}


def _strip_prose(stmt: str) -> str:
    """Remove English words around the maths: 'the equation becomes 3x - 6 = 2x.' -> '3x - 6 = 2x'.
    Words glued to numbers (4ac) and single letters (x, D, a) are kept."""
    stmt = re.sub(r"\b[A-Za-z]{2,}\b", lambda m: m.group(0) if m.group(0) in _MATH_WORDS else " ", stmt)
    stmt = re.sub(r"\.(?!\d)", " ", stmt)          # sentence full stops, not decimals
    stmt = re.sub(r"^[\s:=]+|[\s:=]+$", "", stmt)   # leftovers: 'LHS = ...' -> '...'
    return re.sub(r"\s+", " ", stmt).strip()


_UNIT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*([A-Za-z]{2,})")


def _mixes_units(raw: str) -> bool:
    """'1 unit = 6 years' compares different units, so it is not an arithmetic claim."""
    sides = re.split(REL, raw)[0::2]
    units = set()
    for side in sides:
        for _, word in _UNIT_RE.findall(side):
            if word not in _MATH_WORDS:
                units.add(word.lower().rstrip("s"))
    return len(units) >= 2


def _protect_commas(s: str) -> str:
    """Hide commas inside brackets, e.g. HCF(72, 96), so they don't split statements."""
    out, depth = [], 0
    for ch in s:
        depth += ch == "("
        depth -= ch == ")"
        out.append("§" if ch == "," and depth > 0 else ch)
    return "".join(out)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def validate(student_work: str, equation: str | None = None) -> dict:
    prob = Problem(equation)
    lines, roots_claimed, prev_root = [], [], False
    for raw in re.split(SPLIT_WORDS, _protect_commas(_clean(student_work))):
        raw_text = raw.strip().replace("§", ",")
        trial = bool(re.search(r"(?i)\b(?:try|trying|tried|put|putting|substitut\w*|let|if|when|check\w*|test\w*)\b", raw_text))
        rejected = bool(re.search(r"(?i)\bnot\b|isn't|\bwrong\b|!=|≠", raw_text))
        stmt = _strip_prose(raw_text)
        if _mixes_units(raw_text):
            lines.append({"status": "unchecked", "reason": "unit conversion, not arithmetic",
                          "statement": pretty(stmt)})
            prev_root = False
            continue
        if not stmt:
            continue
        if prev_root and re.fullmatch(r"[-+]?\s*[\d./()±sqrt ]+", stmt):
            stmt = f"x = {stmt}"                        # "x = 2 or 3" -> "x = 3"
        prev_root = bool(re.match(r"x\s*=", stmt))
        if not re.search(r"[\d=<>]", stmt) or re.fullmatch(r"[A-Za-z\s]+", stmt):
            continue                                   # plain words, nothing to check
        r = _check_statement(stmt, prob)
        r["statement"] = pretty(stmt)
        if r["status"] == "root_claim" and (trial or rejected):
            vals = r.pop("values")
            is_root = all(v in map(sp.nsimplify, prob.roots) for v in vals) if prob.roots else None
            if rejected and is_root:
                r.update(status="invalid", kind="trial",
                         message=f"x = {pretty(vals[0])} IS a solution: both sides are equal.")
            else:
                r.update(status="valid", kind="trial")
                if is_root:
                    roots_claimed += vals
            lines.append(r)
            prev_root = False
            continue
        if r["status"] == "root_claim":
            roots_claimed += r.pop("values")
            r["status"] = "valid"
            r["kind"] = "root"
            wrong = [v for v in set(roots_claimed) if prob.roots and v not in map(sp.nsimplify, prob.roots)]
            if wrong:
                if len(prob.roots) == 1:
                    msg = (f"x = {pretty(wrong[0])} does not satisfy the equation; "
                           f"the answer should be x = {pretty(prob.roots[0])}.")
                else:
                    msg = (f"x = {pretty(wrong[0])} is not a root: "
                           f"it gives {pretty(prob.poly.subs(X, wrong[0]))}, not 0.")
                r.update(status="invalid", message=msg)
        r.pop("values", None)
        lines.append(r)

    roots_claimed = sorted(set(roots_claimed), key=lambda r: complex(r).real)
    missing = [r for r in prob.roots if sp.nsimplify(r) not in roots_claimed] if roots_claimed else []
    errors = [l for l in lines if l["status"] == "invalid"]
    return {
        "is_valid": not errors,
        "lines": lines,
        "errors": errors,
        "roots_claimed": [sp.sstr(r) for r in roots_claimed],
        "missing_roots": [sp.sstr(r) for r in missing],
        "solved": bool(roots_claimed) and not missing and not errors,
    }


if __name__ == "__main__":
    import json, sys
    eq = "x**2 - 5*x + 6 = 0"
    for w in sys.argv[1:] or ["D = b^2 - 4ac = 25 - 24 = 1", "D = 25 - 24 = 2"]:
        print(w, "->", json.dumps(validate(w, eq), ensure_ascii=False))
