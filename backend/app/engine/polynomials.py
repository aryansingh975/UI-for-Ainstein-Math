"""Polynomial answers, checked with SymPy (NCERT Class 10 Chapter 2).

A node may carry one of:
  zeroes_of     {"poly": "x**2 - 2*x - 8", "var": "x"}   find the zeroes (either method)
  value_of      {"value": "2", "what": "the sum of the zeroes"}   a number, e.g. α + β = −b/a
  relation_of   {"sum": value_of, "product": value_of}            both, in any order, over one or more lines
  quadratic_with {"sum": "1/4", "product": "-1", "var": "x"}   a quadratic with these zeroes' sum and product

zeroes_step() also reads working, by either method:
  m1 factorisation      x² − 2x − 8 = x² − 4x + 2x − 8 = (x − 4)(x + 2),   x − 4 = 0
  m2 quadratic formula  D = b² − 4ac = 36,   x = (2 ± 6)/2
Each check returns None when the line is not an attempt at this kind of answer.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

import sympy as sp
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                        implicit_multiplication_application, convert_xor)

_T = standard_transformations + (implicit_multiplication_application, convert_xor)
_WORDS = re.compile(r"\b(?:the|zeroes?|zeros?|roots?|are|is|and|or|so|of|polynomial|answer|then|hence|therefore|"
                    r"we|get|gives?|both|equal)\b")


def _clean(text: str) -> str:
    t = (text.replace("−", "-").replace("–", "-").replace("×", "*").replace("·", "*").replace("÷", "/")
         .replace("²", "**2").replace("³", "**3").replace("⁴", "**4").replace("½", "(1/2)").replace("¼", "(1/4)"))
    t = re.sub(r"√\s*(\(|\d+(?:\.\d+)?|[a-z])",
               lambda m: "sqrt(" if m.group(1) == "(" else f"sqrt({m.group(1)})", t)
    t = re.sub(r"sqrt\(\(", "sqrt((", t)
    return t.strip().rstrip(".").strip()


def expr(text: str, letters: str = "") -> Optional[sp.Expr]:
    """Student maths → SymPy, with only these letters as symbols ('x', or 'xk'); None if it is not maths."""
    t = _clean(text)
    if not t or re.search(r"[a-z]{2,}", re.sub(r"sqrt", "", t)):
        return None                                           # a word
    names = {c: sp.Symbol(c) for c in letters} | {"sqrt": sp.sqrt}
    try:
        e = parse_expr(t, local_dict=names, transformations=_T)
    except Exception:
        return None
    if not isinstance(e, sp.Expr) or e.free_symbols - {names[c] for c in letters}:
        return None
    return e


def _same(a: sp.Expr, b: sp.Expr) -> bool:
    try:
        return sp.simplify(a - b) == 0
    except Exception:
        return False


def _show(v: sp.Expr) -> str:
    """2*x**2 - 6*x → 2x² − 6x; sqrt(15) → √15."""
    t = re.sub(r"(\d)\*([a-z(])", r"\1\2", str(v))
    t = re.sub(r"sqrt\((\d+)\)", r"√\1", t).replace("sqrt", "√")
    return t.replace("**2", "²").replace("**3", "³").replace("**", "^").replace("*", " × ").replace(" - ", " − ")


# ─── a number: α + β = 4 + (−2) = 2 = −b/a ───────────────────────────────────────────────────────────────────
_NOT_EQUAL = re.compile(r"\b(?:not|n't|aren't|isn't|don't|doesn't)\s+(?:\w+\s+)?(?:equal|same|match)|\bunequal\b|"
                        r"\bdifferent\b|≠", re.I)
_EQUAL = re.compile(r"\b(?:equal|same|match(?:es)?|verified|true)\b|✓", re.I)


def _numeric(side: str) -> Optional[sp.Expr]:
    """The number on one side of '=': '4 + (−2)', '2/4', '1/2 no both are…' → 1/2; None for a name (α + β, −b/a)."""
    words = re.sub(r"(?:sqrt|√)", "√", side)
    if re.search(r"(?<![a-z])[a-z](?![a-z])\s*/|/\s*[a-z](?![a-z])|[α-ω]", words):
        return None                                           # −b/a, c/a, α + β: a name, not a number
    lead = re.match(r"\s*[-−–+(\d√.][-−–+*/×÷()\d√.\s²³^]*", words)
    if not lead:
        return None
    e = expr(lead.group(0).strip())
    return e if e is not None and not e.free_symbols else None


def value_step(answer: str, spec: Dict) -> Optional[dict]:
    """α + β or αβ checked against −b/a or c/a. Every claim in the line counts ('4 + (−2) = 2, 2/4 = 1/2'): each
    chain must hold, each value must be spec['value'], and a conclusion 'not equal' must not contradict them."""
    target = expr(spec["value"])
    rule = spec.get("rule", "")
    where = (f" here: a = {spec['a']}, b = {spec['b']}, c = {spec['c']}" if "a" in spec else "")
    seen = 0
    for claim in re.split(r"[,;\n]|\bbut\b|\band\b", answer):
        values = [(side.strip(), v) for side in claim.split("=") if (v := _numeric(side)) is not None]
        if not values:
            continue
        for (a, va), (b, vb) in zip(values, values[1:]):
            if not _same(va, vb):
                return {"ok": False, "message": f"{a} = {_show(sp.nsimplify(va))}, not {_show(sp.nsimplify(vb))}."}
        seen += 1
        last, v = values[-1]
        if not _same(v, target):
            rule_text = f" {rule} = {spec['work']} = {spec['value_text']}{where}." if rule else ""
            return {"ok": False, "message": f"{_show(sp.nsimplify(v))} is not {spec.get('what', 'the answer')}."
                                            f"{rule_text}"}
    if not seen:
        return None
    if _NOT_EQUAL.search(answer):                             # "… no, both are not equal": they are
        return {"ok": False, "message": f"Look again: both come to {spec.get('value_text', spec['value'])}, "
                                        f"so they are equal."}
    return {"ok": True}


# ─── "Verify the relationship between the zeroes and the coefficients": the sum and the product, any order ────
_SUM_WORDS = re.compile(r"sum|add|α\s*\+\s*β|alpha\s*\+\s*beta|b\s*/\s*a", re.I)
_PRODUCT_WORDS = re.compile(r"product|multipl|αβ|α\s*[×*.]\s*β|alpha\s*\*?\s*beta|c\s*/\s*a", re.I)


def _which(claim: str, spec: Dict) -> Optional[str]:
    """Is this claim about the sum or the product? Its words first, then its sign (×, +), then its value."""
    if _PRODUCT_WORDS.search(claim):
        return "product"
    if _SUM_WORDS.search(claim):
        return "sum"
    numbers = re.sub(r"[a-zα-ω]", "", claim.lower())
    if re.search(r"[×*]", numbers):
        return "product"
    if re.search(r"\d\s*\)?\s*\+", numbers):
        return "sum"
    values = [v for side in claim.split("=") if (v := _numeric(side)) is not None]
    if values:
        hits = [k for k in ("sum", "product") if _same(values[-1], expr(spec[k]["value"]))]
        if len(hits) == 1:
            return hits[0]
    return None


def relation_step(answer: str, spec: Dict, have: List[str]) -> Optional[dict]:
    """spec = {'sum': value_of spec, 'product': value_of spec}. Each claim is the sum's or the product's and is
    checked by value_step. {'done'} both; {'ok', 'got', 'message'} one; {'ok': False, 'message'}; None: no numbers."""
    got, any_claim = list(have), False
    for claim in re.split(r"[,;\n]|\bbut\b|\band\b", answer):
        if not any(_numeric(side) is not None for side in claim.split("=")):
            continue
        any_claim = True
        kind = _which(claim, spec)
        if kind is None:                                     # unlabelled and neither value: say both
            kind = next((k for k in ("sum", "product") if k not in got), "sum")
        result = value_step(claim, spec[kind])
        if result and not result["ok"]:
            return result
        if kind not in got:
            got.append(kind)
    if not any_claim:
        return None
    if _NOT_EQUAL.search(answer):
        return {"ok": False, "message": "Look again: your numbers and the coefficients agree, so they are equal."}
    if {"sum", "product"} <= set(got):
        return {"ok": True, "done": True, "got": got}
    s, p = spec["sum"], spec["product"]
    message = (f"Right: the sum of the zeroes is {s['value_text']} = −b/a. Now the product of the zeroes."
               if "sum" in got else
               f"Right: the product of the zeroes is {p['value_text']} = c/a. Now the sum of the zeroes.")
    return {"ok": True, "got": got, "message": message}


# ─── a quadratic from the sum and product of its zeroes ──────────────────────────────────────────────────────
def quadratic_step(answer: str, spec: Dict) -> Optional[dict]:
    """Any k(x² − Sx + P), k ≠ 0: SymPy reads a, b, c and compares −b/a and c/a."""
    var = spec.get("var", "x")
    x = sp.Symbol(var)
    side = re.split(r"=", answer)[-1] if "=" in answer else answer
    side = re.sub(r"^\s*p\s*\(\s*[a-z]\s*\)\s*", "", side)
    e = expr(side, var + "k")
    if e is None or x not in e.free_symbols:
        return None
    try:
        p = sp.Poly(sp.expand(e), x)
    except Exception:
        return None
    if p.degree() != 2:
        return {"ok": False, "message": f"That has degree {p.degree()}; a quadratic polynomial has degree 2."}
    a, b, c = p.all_coeffs()
    s, q = sp.simplify(-b / a), sp.simplify(c / a)
    want_s, want_q = expr(spec["sum"]), expr(spec["product"])
    if _same(s, want_s) and _same(q, want_q):
        return {"ok": True}
    return {"ok": False, "message": f"Your polynomial's zeroes have sum −b/a = {_show(s)} and product c/a = "
                                    f"{_show(q)}; the question gives sum {spec['sum_text']} and product "
                                    f"{spec['product_text']}."}


# ─── zeroes, and the working of either method ─────────────────────────────────────────────────────────────────
def zeroes(spec: Dict) -> List[sp.Expr]:
    x = sp.Symbol(spec["var"])
    return list(sp.roots(sp.Poly(expr(spec["poly"].replace("**", "^"), spec["var"]) or sp.sympify(spec["poly"]), x)))


def _poly(spec: Dict) -> sp.Expr:
    return sp.sympify(spec["poly"], locals={spec["var"]: sp.Symbol(spec["var"])})


def _values(piece: str, var: str) -> Optional[List[sp.Expr]]:
    """'x = 4', '-2', '±√15', '(2 ± 6)/2', '1/2' → numbers; None if the piece is not a number."""
    piece = re.sub(rf"^\s*{var}\s*=\s*", "", piece.strip())
    pieces = [piece.replace("±", "+", 1), piece.replace("±", "-", 1)] if "±" in piece else [piece]
    out = []
    for p in pieces:
        e = expr(p)
        if e is None or e.free_symbols:
            return None
        out.append(sp.nsimplify(sp.simplify(e)))
    return out


def zeroes_step(answer: str, spec: Dict, found: List[str]) -> Optional[dict]:
    """Several lines of working at once ('… = (x − 4)(x + 2)', 'x − 4 = 0 and x + 2 = 0', 'x = 4 and x = −2'):
    each line is checked; the first mistake is reported, and the zeroes found on any line count."""
    lines = []
    joins = r"[;\n]|⇒|=>|→|\b(?:so|hence|therefore|thus|then|which gives|gives|i\.e\.)\b"
    for line in re.split(rf"{joins}|(=\s*0)(?![\d./])\s*(?:and\b)?", answer, flags=re.I):  # a new claim
        if line is None or not line.strip():
            continue
        if re.fullmatch(r"=\s*0", line.strip()) and lines:
            lines[-1] += " = 0"
        else:
            lines.append(line.strip())
    split = []
    for line in lines:                                       # "A = (x − 4)(x + 2) = (x − 4) = 0": "= " chains steps
        sides = line.split("=")
        if len(sides) >= 4 and sides[-1].strip() == "0":
            split += ["=".join(sides[:-2]), f"{sides[-2]} = 0"]
        else:
            split.append(line)
    lines = split
    if len(lines) < 2:
        return _zeroes_line(answer, spec, found)
    have, last = list(found), None
    for line in lines:
        step = _zeroes_line(line, spec, have)
        if step is None:
            continue
        if step.get("wrong") or step.get("done"):
            return step
        if step.get("found"):
            have += [str(v) for v in step["values"] if str(v) not in have]
            if (_zeroes_line(", ".join(have), spec, []) or {}).get("done"):
                return {"done": True, "values": [expr(h) for h in have]}
        last = step
    return last


def _zeroes_line(answer: str, spec: Dict, found: List[str]) -> Optional[dict]:
    """{'done'} all zeroes; {'found', 'values', 'message'} some; {'working', 'method', 'message'} a step of either
    method; {'wrong', 'message', 'method'} a mistake; None: not an attempt."""
    var, x = spec["var"], sp.Symbol(spec["var"])
    poly, roots = _poly(spec), zeroes(spec)
    text = answer.strip()
    if text.startswith("="):                                   # "= (x − 4)(x + 2)": goes on from the polynomial
        text = f"{poly} {text}"
    low = text.lower()

    # m2: the discriminant  "D = b² − 4ac = (−2)² − 4(1)(−8) = 36"
    if re.match(r"^\s*(?:d\b|discriminant|b\s*(?:\^|\*\*|²)\s*2?\s*-\s*4\s*a\s*c)", low.replace("−", "-")):
        a, b, c = sp.Poly(poly, x).all_coeffs()
        d = sp.simplify(b ** 2 - 4 * a * c)
        nums = [expr(s) for s in text.split("=")[1:]]
        nums = [n for n in nums if n is not None and not n.free_symbols]
        if not nums:
            return {"working": True, "method": "m2", "message": "Right: D = b² − 4ac. Now put in a, b and c."}
        for n in nums:
            if not _same(n, d):
                return {"wrong": True, "method": "m2",
                        "message": f"D = b² − 4ac with a = {a}, b = {b}, c = {c} is {_show(d)}, not {_show(n)}."}
        return {"working": True, "method": "m2",
                "message": f"Right: D = {_show(d)}. Now use {var} = (−b ± √D) / 2a."}

    # an equation or identity in the variable: factorisation working  "… = (x − 4)(x + 2)", "x − 4 = 0"
    sides = [s for s in re.split(r"=", text)]
    if len(sides) >= 2:
        exprs = [expr(s, var) for s in sides]
        a_value = exprs[0] == x and all(e is not None and not e.free_symbols for e in exprs[1:])   # "x = 4"
        if not a_value and all(e is not None for e in exprs) and any(x in e.free_symbols for e in exprs):
            if len(exprs) == 2 and exprs[1] == 0 and exprs[0].free_symbols:
                lhs = sp.expand(exprs[0])
                if sp.Poly(lhs, x).degree() == 1:             # "x − 4 = 0": a factor set to zero
                    r = sp.solve(lhs, x)[0]
                    if any(_same(r, z) for z in roots):
                        return {"found": True, "values": [r], "method": "m1",
                                "message": f"Right: {sides[0].strip()} = 0 gives {var} = {_show(r)}."}
                    return {"wrong": True, "method": "m1",
                            "message": f"{sides[0].strip()} = 0 gives {var} = {_show(r)}, but p({_show(r)}) = "
                                       f"{_show(sp.simplify(poly.subs(x, r)))}, not 0."}
                ratio = sp.simplify(lhs / poly)
                if not ratio.free_symbols and ratio != 0:      # "(x − 4)(x + 2) = 0"
                    return {"working": True, "method": "m1",
                            "message": "Right. Now set each factor equal to 0."}
                return {"wrong": True, "method": "m1",
                        "message": f"{sides[0].strip()} is not the same as the polynomial: it expands to "
                                   f"{_show(sp.expand(exprs[0]))}."}
            base = exprs[0]
            for s, e in zip(sides[1:], exprs[1:]):
                if not _same(sp.expand(e), sp.expand(base)):
                    return {"wrong": True, "method": "m1",
                            "message": f"{s.strip()} expands to {_show(sp.expand(e))}, not {_show(sp.expand(base))}."}
            ratio = sp.simplify(base / poly)
            if ratio.free_symbols or ratio == 0:
                return None                                   # true, but about another polynomial
            last = exprs[-1]
            factored = isinstance(sp.factor_terms(last), sp.Mul) and len(sp.Mul.make_args(last)) > 1
            nxt = "Now set each factor equal to 0." if factored else "Keep going: can you factorise it?"
            return {"working": True, "method": "m1", "message": f"Right. {nxt}"}

    # numbers: the zeroes themselves  "x = 4, −2", "4 and −2", "±√15", "x = (2 ± 6)/2"
    body = _WORDS.sub(" ", low.replace("−", "-"))
    pieces = [p for p in re.split(r"[,;\n]|\s{2,}|(?<=\d)\s+(?=[-+]?\s*\d)", body) if p.strip()]
    values = []
    for p in pieces:
        v = _values(p, var)
        if v is None:
            return None
        values += v
    if not values:
        return None
    bad = [v for v in values if not any(_same(v, z) for z in roots)]
    if bad:
        v = bad[0]
        method = "m2" if "±" in text or "sqrt" in _clean(text) and "/" in text else None
        return {"wrong": True, "method": method,
                "message": f"{var} = {_show(v)} is not a zero: p({_show(v)}) = {_show(sp.simplify(poly.subs(x, v)))}, "
                           f"not 0."}
    have = {str(sp.nsimplify(z)) for z in values} | set(found)
    if all(str(sp.nsimplify(z)) in have or any(_same(z, expr(f) or z + 1) for f in have) for z in roots):
        return {"done": True, "values": values}
    return {"found": True, "values": values,
            "message": f"Right: {var} = {', '.join(_show(v) for v in values)} is a zero. What is the other zero?"}


# ─── "What is given?": the question's own list ────────────────────────────────────────────────────────────────
_LABEL = re.compile(r"\(\s*(?:viii|vii|vi|iv|ix|iii|ii|v|x|i)\s*\)|\b(?:viii|vii|vi|iv|ix|iii|ii|v|x|i)\)", re.I)


def given_polys_step(answer: str, polys: List[Dict]) -> Optional[dict]:
    """'(i) x² – 2x – 8 (ii) 4s² – 4s + 1 …': every polynomial of the question, in any order and form.
    {ok} all; {ok: False, message} some, or one that is not in the question; None: not a list of polynomials."""
    pieces = [p for p in re.split(rf"{_LABEL.pattern}|[,;\n]|\band\b", answer, flags=re.I) if p and p.strip()]
    letters = "".join(sorted({p["var"] for p in polys}))
    wanted = [(p, sp.sympify(p["poly"], locals={p["var"]: sp.Symbol(p["var"])})) for p in polys]
    seen, strange = set(), []
    for piece in pieces:
        e = expr(piece, letters)
        if e is None or not e.free_symbols:
            continue
        match = next((i for i, (_, w) in enumerate(wanted) if sp.expand(e - w) == 0), None)
        if match is None:
            strange.append(piece.strip())
        else:
            seen.add(match)
    if not seen and not strange:
        return None
    if strange:
        return {"ok": False, "message": f"{strange[0]} is not one of the polynomials in the question."}
    if len(seen) == len(wanted):
        return {"ok": True}
    left = len(wanted) - len(seen)
    return {"ok": False, "message": f"You have {len(seen)} of the {len(wanted)} polynomials. "
                                    f"Which {'one is' if left == 1 else 'ones are'} missing?"}


def given_pairs_step(answer: str, pairs: List[List[str]]) -> Optional[dict]:
    """'(i) 1/4, −1 (ii) √2, 1/3 …' (or the twelve numbers in order): every (sum, product) pair of the question."""
    wanted = [(expr(s), expr(p)) for s, p in pairs]
    if _LABEL.search(answer):
        groups = [g for g in _LABEL.split(answer) if g and g.strip()]
    else:
        flat = [x for x in re.split(r"[,;\n]|\band\b", answer) if x.strip()]
        groups = [", ".join(flat[i:i + 2]) for i in range(0, len(flat), 2)]
    got, strange = set(), []
    for g in groups:
        nums = [expr(x) for x in re.split(r"[,;]|\band\b|\s{2,}", g) if x.strip()]
        nums = [n for n in nums if n is not None and not n.free_symbols]
        if len(nums) != 2:
            continue
        match = next((i for i, (s, p) in enumerate(wanted) if _same(nums[0], s) and _same(nums[1], p)), None)
        if match is None:
            strange.append(g.strip().strip(","))
        else:
            got.add(match)
    if not got and not strange:
        return None
    if strange:
        return {"ok": False, "message": f"({strange[0]}) is not one of the pairs in the question."}
    if len(got) == len(wanted):
        return {"ok": True}
    left = len(wanted) - len(got)
    return {"ok": False, "message": f"You have {len(got)} of the {len(wanted)} pairs. "
                                    f"Which {'one is' if left == 1 else 'ones are'} missing?"}
