"""A pair of linear equations in two variables, checked with SymPy (NCERT Class 10 Chapter 3).

A node may carry one of (spec = graph's pair: vars, names, equations, solution, conditions, shown):
  pair_form     form one equation per condition, in any order and any equivalent form
  pair_solve    solve them: any true step of elimination (m1) or substitution (m2); both values found
  pair_verify   put the values back into each condition ("45 = 3 × 15")

Each step returns None when the line is not an attempt; otherwise one of
  {"done", "have"}  {"found", "have", "message"}  {"working", "message"}  {"wrong", "message"}
with "method" ("m1" elimination, "m2" substitution) when the line shows one.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import sympy as sp

from app.engine.polynomials import expr, _show

KINDS = ("pair_form", "pair_solve", "pair_verify")
_JOINS = re.compile(r"[;\n]|⇒|=>|→|,|\band\b|\b(?:so|hence|therefore|thus|then|which gives|gives|i\.e\.)\b", re.I)
_REF = re.compile(r"(?<![\w)])\(\s*[12]\s*\)")                 # "(1) − (2)", "… = 10 (2)": equation labels


def node_check(node) -> Optional[Tuple[str, Dict]]:
    for kind in KINDS:
        spec = getattr(node, kind, None)
        if spec:
            return kind, spec
    return None


def _symbols(spec: Dict):
    return [sp.Symbol(v) for v in spec["vars"]]


def _people(spec: Dict) -> Dict[str, str]:
    return {k: v for k, v in spec.get("names", {}).items() if len(k) > 1}       # nuri → x, sonu → y


def _label_patterns(spec: Dict):
    names = "|".join(map(re.escape, _people(spec)))
    age = r"(?:'s)?(?:\s+(?:present|current))?(?:\s+age)?"
    return [re.compile(rf"(?:^|\s)(?:let\s+)?(?:the\s+)?(?:present\s+|current\s+)?(?:age\s+of\s+)?({names}){age}"
                       rf"\s*(?:=|is|be|as)\s*([a-z])\s*(?:years?)?\s*$"),
            re.compile(rf"(?:^|\s)(?:let\s+)?([a-z])\s*(?:=|be|is|as)\s*(?:the\s+)?(?:present\s+)?(?:age\s+of\s+)?"
                       rf"({names}){age}\s*$")]


def _label(claim: str, spec: Dict) -> Optional[Tuple[str, str]]:
    """'present Sonu age = x', 'let y be Nuri's age' → (name, letter); None for anything else."""
    low = claim.lower().replace("’", "'").strip(" .:")
    first, second = _label_patterns(spec)
    m = first.search(low)
    if m:
        return m.group(1), m.group(2)
    m = second.search(low)
    return (m.group(2), m.group(1)) if m else None


def labels(answer: str, spec: Dict) -> Dict[str, str]:
    """The student's letters → the graph's: 'Sonu = x, Nuri = y' → {x: y, y: x}; 'Nuri = a' → {a: x}."""
    people = _people(spec)
    chosen = dict(l for c in _JOINS.split(answer) if c and (l := _label(c, spec)))
    out = {}
    for name, letter in chosen.items():
        if letter != people[name]:
            out[letter] = people[name]
    if len(chosen) == 1 and out:                               # one name given: the other takes the other letter
        (name, letter), = chosen.items()
        other = next(n for n in people if n != name)
        if letter == people[other]:
            out[people[name]] = people[other]
    return out


def _relabel(text: str, letters: Dict[str, str]) -> str:
    if not letters:
        return text
    return re.sub(r"(?<![a-z'])([a-z])(?![a-z])", lambda m: letters.get(m.group(1), m.group(1)), text)


def _prepare(claim: str, spec: Dict) -> str:
    """Names → the variables ('Nuri' → x), equation labels and words out: only the maths is left."""
    t = _relabel(claim.lower().replace("’", "'"), spec.get("letters") or {})
    for name, var in sorted(spec.get("names", {}).items(), key=lambda kv: -len(kv[0])):
        if len(name) > 1:
            t = re.sub(rf"\b{re.escape(name)}(?:'s)?(?:\s+age)?\b", f" {var} ", t)
    t = _REF.sub(" ", t)
    t = re.sub(rf"(?<![a-z])([{''.join(spec['vars'])}])\s+(?:is|was|will be)\s+(?=[-−\d(])", r"\1 = ", t)  # Nuri is 50
    t = re.sub(r"\b(?:age|ages|years?|yrs?|old|now|present|let|be|is|are|was|will|the|of|we|get)\b", " ", t)
    return t.strip(" :.")


def _equations(claim: str, spec: Dict) -> Optional[List[Tuple[sp.Expr, str]]]:
    """The equations of one claim: each '=' between two sides (an expansion step 'a = a' is left out).
    None when a side is not maths in the pair's letters."""
    t = _prepare(claim, spec)
    if "=" not in t:
        return None
    letters = "".join(spec["vars"]) + "".join(k for k in spec.get("names", {}) if len(k) == 1)
    sides = [s for s in t.split("=")]
    exprs = [expr(s, letters) for s in sides]
    if any(e is None for e in exprs):
        return None
    swap = {sp.Symbol(k): sp.Symbol(v) for k, v in spec.get("names", {}).items() if len(k) == 1}
    exprs = [e.subs(swap) for e in exprs]
    out = []
    for (a, sa), (b, sb) in zip(zip(exprs, sides), list(zip(exprs, sides))[1:]):
        e = sp.expand(a - b)
        if e != 0:
            out.append((e, f"{sa.strip()} = {sb.strip()}"))
    return out


def _linear(e: sp.Expr, xs) -> bool:
    try:
        return sp.Poly(e, *xs).total_degree() <= 1
    except Exception:
        return False


def _holds(e: sp.Expr, spec: Dict) -> bool:
    values = {sp.Symbol(k): sp.sympify(v) for k, v in spec["solution"].items()}
    return sp.simplify(e.subs(values)) == 0


def _proportional(e: sp.Expr, t: sp.Expr, xs) -> bool:
    k = sp.Symbol("k_")
    return bool(sp.solve(sp.Poly(sp.expand(e - k * t), *xs).coeffs(), k)) or sp.expand(e - t) == 0


_SPEC: Dict = {}


def _claims(answer: str) -> List[str]:
    return [c for c in _JOINS.split(answer) if c and c.strip() and not (_SPEC and _label(c, _SPEC))]


# ─── form the equations ─────────────────────────────────────────────────────────────────────────────────────────
def form_step(answer: str, spec: Dict, have: List[str]) -> Optional[dict]:
    xs = _symbols(spec)
    targets = [sp.sympify(t, locals={v: sp.Symbol(v) for v in spec["vars"]}) for t in spec["equations"]]
    got, seen = list(have), False
    for claim in _claims(answer):
        eqs = _equations(claim, spec)
        if not eqs:
            continue
        for e, text in eqs:
            if not e.free_symbols & set(xs):
                continue
            seen = True
            if not _linear(e, xs):
                return {"wrong": True, "message": f"{text} is not linear: each age appears on its own, never "
                                                  f"multiplied by the other."}
            match = next((i for i, t in enumerate(targets) if _proportional(e, t, xs)), None)
            if match is not None:
                if str(match) not in got:
                    got.append(str(match))
                continue
            if _holds(e, spec):                               # true, but a mix of the two conditions
                continue
            relations = [sp.sympify(r, locals={v: sp.Symbol(v) for v in spec["vars"]})
                         for r in spec.get("relations", [])]
            rel = next((i for i, r in enumerate(relations) if _proportional(e, r, xs)), None)
            if rel is not None:                               # x = 3y: "thrice" for today's ages, not then
                return {"wrong": True, "relation": rel,
                        "message": f"{text} says \"thrice\" for their ages today. {spec['relation_next'][rel]}"
                                   if rel == 0 else
                                   f"{text} says \"twice\" for their ages today. {spec['relation_next'][rel]}"}
            swapped = e.subs({xs[0]: xs[1], xs[1]: xs[0]}, simultaneous=True)
            back = next((i for i, t in enumerate(targets) if _proportional(swapped, t, xs)), None)
            if back is not None:                               # x − 5 = 3(y − 5) for Sonu thrice Nuri
                return {"wrong": True, "message": f"{text} has the two ages the wrong way round for "
                                                  f"\"{spec['conditions'][back]}\". Who is older, and whose age is "
                                                  f"multiplied?"}
            k = _closest(e, targets, xs)
            return {"wrong": True, "message": f"{text} does not say \"{spec['conditions'][k]}\". "
                                              f"{spec['ask'][k]}"}
    if not seen:
        return None
    if len(got) >= len(targets):
        return {"done": True, "have": got}
    if not got:                                               # true lines, but neither equation yet: "x = 50, y = 20"
        solved = solve_step(answer, spec, [])
        found = ", ".join(f"{v} = {spec['solution'][v]}" for v in spec["vars"])
        return {"working": True, "have": got,
                "message": (f"Right: {found} fits both sentences. Now show the equations it comes from: one for "
                            f"each sentence." if solved and solved.get("done") else
                            "That is true, but it is not one of the two sentences yet. Write one equation for each "
                            "sentence.")}
    left = next(i for i in range(len(targets)) if str(i) not in got)
    return {"found": True, "have": got,
            "message": f"Right: that is the equation for \"{spec['conditions'][1 - left]}\". Now the other one: "
                       f"\"{spec['conditions'][left]}\"."}


def _closest(e: sp.Expr, targets, xs) -> int:
    """Which condition a wrong equation was aimed at: the nearer ratio of the two coefficients."""
    def ratio(f):
        p = sp.Poly(f, *xs)
        a, b = p.coeff_monomial(xs[0]), p.coeff_monomial(xs[1])
        return float(b / a) if a else 0.0
    try:
        r = ratio(e)
        return min(range(len(targets)), key=lambda i: abs(ratio(targets[i]) - r))
    except Exception:
        return 0


def stage(answer: str, spec: Dict, have: List[str], letters: Optional[Dict[str, str]] = None) -> str:
    """Where the student is in forming the equations (graph's form_stages):
    'past'   the ages 'five years ago' are not written yet (x − 5, y − 5)
    'first'  they are, but the first equation is not right yet
    'second' the first equation is right; the second ('ten years later') is not."""
    if "0" in have:
        return "second"
    t = _prepare(answer, {**spec, "letters": dict(letters or {})}).replace("−", "-").replace("–", "-")
    n = spec.get("past", 5)
    past = re.search(rf"(?<![a-z])[{''.join(spec['vars'])}]\s*-\s*{n}(?![\d.])", t)   # a past age: x − 5
    return "first" if past else "past"


def past_ages(answer: str, spec: Dict, letters: Optional[Dict[str, str]] = None) -> bool:
    """'5 years ago Nuri = x − 5, Sonu = y − 5': both past ages, and no equation yet."""
    t = _prepare(answer, {**spec, "letters": dict(letters or {})}).replace("−", "-").replace("–", "-")
    n = spec.get("past", 5)
    return all(re.search(rf"(?<![a-z]){v}\s*-\s*{n}(?![\d.])", t) for v in spec["vars"])


def relabel_for(text: str, letters: Dict[str, str]) -> str:
    """A hint written with x (Nuri) and y (Sonu), in the student's own letters."""
    return _relabel_case(text, {v: k for k, v in (letters or {}).items()})


# ─── solve them ──────────────────────────────────────────────────────────────────────────────────────────────────
_ELIMINATE = re.compile(r"subtract|add|eliminat|\(\s*[12]\s*\)\s*[-−+]\s*\(\s*[12]\s*\)", re.I)
_SUBSTITUTE = re.compile(r"substitut|put|plug|replace", re.I)


def _method(claim: str, e: sp.Expr, spec: Dict) -> Optional[str]:
    if _SUBSTITUTE.search(claim):
        return "m2"
    if _ELIMINATE.search(claim):
        return "m1"
    t = _prepare(claim, spec)
    xs = spec["vars"]
    lhs = t.split("=")[0].strip()
    if lhs in xs and any(v in t.split("=", 1)[1] for v in xs if v != lhs):
        return "m2"                                           # x = 3y − 10
    brackets = re.findall(r"\(([^()]*)\)", t)
    if any(all(v in b for v in xs) for b in brackets):
        return "m1"                                           # (x − 3y) − (x − 2y) = −10 − 10
    if any(any(v in b for v in xs) for b in brackets) and len(e.free_symbols) == 1:
        return "m2"                                           # (3y − 10) − 2y = 10
    return None


def solve_step(answer: str, spec: Dict, have: List[str]) -> Optional[dict]:
    xs = _symbols(spec)
    got, seen, method, last, one = list(have), False, None, None, None
    shown = " and ".join(spec["shown"])
    for claim in _claims(answer):
        eqs = _equations(claim, spec)
        if not eqs:
            continue
        for e, text in eqs:
            if not e.free_symbols & set(xs):
                labels = re.search(rf"(?<![a-z])[{''.join(spec['vars'])}](?![a-z])", _prepare(text, spec))
                if sp.simplify(e) != 0 and not labels:        # "y = 10 + y" is a label line ("Sonu age = 10 + y")
                    return {"wrong": True, "method": method, "message": f"{text} is not true: check the arithmetic."}
                continue
            seen = True
            method = _method(claim, e, spec) or method
            if not _linear(e, xs) or not _holds(e, spec):
                return {"wrong": True, "method": method,
                        "message": f"{text} does not follow from {shown}. Check the signs when you "
                                   f"{'substitute' if method == 'm2' else 'add or subtract'}."}
            if len(e.free_symbols) == 1:
                v = next(iter(e.free_symbols))
                sides = [x.strip() for x in _prepare(text, {**spec, "letters": {}}).split("=")]   # already relabelled
                if v.name in sides and v.name not in got:         # "y = 20": found; "−y = −20": keep going
                    got.append(v.name)
                    last = v
                elif v.name not in got:
                    one = v.name
    if not seen:
        return None
    if all(v in got for v in spec["vars"]):
        return {"done": True, "have": got, "method": method}
    if last is not None or got:
        v = next(x for x in spec["vars"] if x in got)
        other = next(x for x in spec["vars"] if x not in got)
        return {"found": True, "have": got, "method": method,
                "message": f"Right: {v} = {spec['solution'][v]}. Now put it into one of the equations to find "
                           f"{other}."}
    if one:
        return {"working": True, "method": method, "have": got,
                "message": f"Right: only {one} is left. Now solve it: what is {one}?"}
    nxt = ("Now put it into the other equation." if method == "m2"
           else "Keep going: you want an equation with only one letter.")
    return {"working": True, "method": method, "message": f"Right. {nxt}"}


# ─── verify ──────────────────────────────────────────────────────────────────────────────────────────────────────
def verify_step(answer: str, spec: Dict, have: List[str]) -> Optional[dict]:
    """'45 = 3 × 15', '50 − 5 = 3(20 − 5)', '50 − 3(20) = −10': each true check counts for its condition."""
    got, seen = list(have), False
    checks = spec["checks"]                                   # [[values that check condition 1], [condition 2]]
    for claim in _claims(answer):
        t = _prepare(claim, spec)
        if "=" not in t:
            continue
        values = {sp.Symbol(k): sp.sympify(v) for k, v in spec["solution"].items()}
        sides = [expr(s, "".join(spec["vars"])) for s in t.split("=")]
        if any(s is None for s in sides):
            continue
        nums = [sp.simplify(s.subs(values)) for s in sides]
        seen = True
        times = re.search(r"[×*(]|times|twice|thrice", claim.lower())     # '50 + 10 = 60' checks nothing
        for (a, va), (b, vb) in zip(zip(t.split("="), nums), list(zip(t.split("="), nums))[1:]):
            if sp.simplify(va - vb) != 0:
                return {"wrong": True, "message": f"{a.strip()} = {_show(va)}, but {b.strip()} = {_show(vb)}: "
                                                  f"they are not equal. Check your ages or your working."}
        for i, ok in enumerate(checks):
            if times and any(sp.simplify(nums[0] - sp.sympify(v)) == 0 for v in ok) and str(i) not in got:
                got.append(str(i))
                break
    if not seen:
        return None
    if len(got) >= len(checks):
        return {"done": True, "have": got}
    left = next(i for i in range(len(checks)) if str(i) not in got)
    return {"found": True, "have": got,
            "message": f"Right. Now check the other sentence: \"{spec['conditions'][left]}\"."}


def step(kind: str, answer: str, spec: Dict, have: List[str], letters: Optional[Dict[str, str]] = None
         ) -> Optional[dict]:
    """The student's own letters count: 'Sonu = x, Nuri = y' swaps them (kept in 'letters' for later steps).
    Feedback is written back in the student's letters."""
    global _SPEC
    found = labels(answer, spec)
    letters = found or dict(letters or {})
    spec = {**spec, "letters": letters}
    _SPEC = spec
    try:
        r = {"pair_form": form_step, "pair_solve": solve_step, "pair_verify": verify_step}[kind](answer, spec, have)
    finally:
        _SPEC = {}
    back = {v: k for k, v in letters.items()}
    if r is None and any(_label(c, spec) for c in _JOINS.split(answer) if c):
        people = _people(spec)
        named = ", ".join(f"{n.title()} = {v}" for n, v in people.items())     # relabelled below
        r = {"working": True, "message": f"OK: {named}. Now write the equations."}
    if r is not None:
        r["letters"] = letters
        if r.get("message"):
            r["message"] = _relabel_case(r["message"], back)
    return r


def _relabel_case(text: str, letters: Dict[str, str]) -> str:
    """Feedback in the student's letters; capitalised words (Nuri, Sonu) are left alone."""
    if not letters:
        return text
    return re.sub(r"(?<![A-Za-z'])([a-z])(?![A-Za-z])", lambda m: letters.get(m.group(1), m.group(1)), text)
