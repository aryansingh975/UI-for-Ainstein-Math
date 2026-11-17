"""
"My Jev" — a local method detector. No API key, no AI. Python port of my_jev.js.

It answers the same question Jev answers: "Which solution method is the
student using?" — and returns the same shape Jev returns:
  { status: 'selected' | 'uncertain' | 'off_graph',
    methodKey, methodId, confidence,
    probabilities: { method1: 0.91, method2: 0.06, method3: 0.03 },
    off_graph: False }

How it decides (all evidence comes from the problem's graph.json):
  1. Each student line is compared with every method's accept lists
     (the method node + all of its step nodes).
  2. Each comparison gives a score from 0 to 1:
       1.00  same text (ignoring spaces / case / ×, ÷, − symbols)
       0.90  same definition                ("daughter = 0.2x" vs "daughter = x/5")
       0.85  same equation, side by side   ("5x+6=3(x+6)" vs "5x + 6 = 3(x + 6)")
       0.85  contains an accept entry       ("D = b^2 - 4ac" contains "b^2 - 4ac")
       0.80  is part of an accept entry     ("x + 6" is part of "x + 6 and 5x + 6")
       0.60  equation with this method's answer for x (x = 6 in Method 1, x = 30 in Method 2)
       0.60  shares key words with an accept entry ("ratio", "units", "factor"…)
       0.40  uses the same numbers as an accept entry
  3. A line that fits several methods equally (a shared step) gives no
     preference. Lines that fit only one method push its probability up.
  4. Scores are turned into probabilities with a softmax. Nothing fits → off_graph.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.schemas.graph import SolutionGraph

CONFIDENCE_THRESHOLD = 0.7   # same threshold the server uses for Jev
SHARPNESS = 8                # higher = more decisive probabilities
OFF_GRAPH_SCORE = 0.35       # best evidence below this → "not one of our methods"


# ─── 1. Text clean-up ────────────────────────────────────────────────────────
def clean(text: Any) -> str:
    s = str(text).lower()
    s = re.sub(r"[−–—]", "-", s).replace("×", "*").replace("÷", "/")
    s = s.replace("²", "^2").replace("’", "'")
    return re.sub(r"\s+", " ", s).strip()


def compact(text: Any) -> str:
    return re.sub(r"\s+", "", clean(text))


STOP_WORDS = set((
    "a an the is are of to and or so then we i my let be by in on at for with "
    "it this that its as from into find get have has do does use using now"
).split(" "))


def words(text: Any) -> List[str]:
    return [w for w in re.sub(r"[^a-z\s]", " ", clean(text)).split(" ")
            if len(w) >= 3 and w not in STOP_WORDS]


def numbers(text: Any) -> List[float]:
    return [float(n) for n in re.findall(r"\d+(?:\.\d+)?", clean(text))]


# ─── 2. A small, safe maths evaluator ────────────────────────────────────────
# Handles + − * / ^ ( ), decimals, implicit multiplication (5x, 3(x+6), x/5) and
# single-letter variables. Returns None if the text is not an expression.
def prepare(expr: str) -> Optional[Tuple[str, Set[str]]]:
    s = clean(expr)
    s = re.sub(r"(\d)\s*([a-z(])", r"\1*\2", s)          # 5x, 3(
    s = re.sub(r"\)\s*([a-z\d(])", r")*\1", s)           # )(, )x
    s = re.sub(r"\b([a-z])\s*\(", r"\1*(", s)            # x(
    s = re.sub(r"\b([a-z])\s+([a-z])\b", r"\1*\2", s)    # x y
    if not re.fullmatch(r"[a-z0-9+\-*/^().\s]+", s):
        return None
    letters = re.findall(r"[a-z]+", s)
    if any(len(w) > 1 for w in letters):                 # words left → not maths
        return None
    return s, set(letters)


def _pow(b: float, e: float) -> float:
    # Behaves like JavaScript's Math.pow: NaN / ±Infinity instead of exceptions.
    try:
        return math.pow(b, e)
    except OverflowError:
        return -math.inf if b < 0 and float(e).is_integer() and int(e) % 2 else math.inf
    except ValueError:
        return math.inf if b == 0 and e < 0 else math.nan


def evaluate(src: str, values: Dict[str, float]) -> Optional[float]:
    stripped = re.sub(r"\s+", "", src)
    tokens = re.findall(r"\d+(?:\.\d+)?|[a-z]|[+\-*/^()]", stripped)
    if not tokens or "".join(tokens) != stripped:
        return None
    pos = 0

    def peek() -> Optional[str]:
        return tokens[pos] if pos < len(tokens) else None

    def expr() -> Optional[float]:
        nonlocal pos
        v = term()
        if v is None:
            return None
        while peek() in ("+", "-"):
            op = tokens[pos]; pos += 1
            r = term()
            if r is None:
                return None
            v = v + r if op == "+" else v - r
        return v

    def term() -> Optional[float]:
        nonlocal pos
        v = unary()
        if v is None:
            return None
        while peek() in ("*", "/"):
            op = tokens[pos]; pos += 1
            r = unary()
            if r is None:
                return None
            if op == "/" and r == 0:
                return None
            v = v * r if op == "*" else v / r
        return v

    def unary() -> Optional[float]:
        nonlocal pos
        if peek() == "-":
            pos += 1
            v = unary()
            return None if v is None else -v
        if peek() == "+":
            pos += 1
            return unary()
        return power()

    def power() -> Optional[float]:
        nonlocal pos
        b = atom()
        if b is None:
            return None
        if peek() == "^":
            pos += 1
            e = unary()
            return None if e is None else _pow(b, e)
        return b

    def atom() -> Optional[float]:
        nonlocal pos
        t = peek()
        pos += 1
        if t is None:
            return None
        if t[0].isdigit():
            return float(t)
        if re.fullmatch(r"[a-z]", t):
            return values.get(t)
        if t == "(":
            v = expr()
            if peek() != ")":
                pos += 1
                return None
            pos += 1
            return v
        return None

    v = expr()
    return None if (v is None or pos != len(tokens) or not math.isfinite(v)) else v


TRIALS = [3, 7.5, 11, 40]


def same_value(a: str, b: str) -> bool:
    """Same value for every x?"""
    pa, pb = prepare(a), prepare(b)
    if not pa or not pb:
        return False
    variables = pa[1] | pb[1]
    for t in TRIALS:
        values = {v: t for v in variables}
        va, vb = evaluate(pa[0], values), evaluate(pb[0], values)
        if va is None or vb is None or abs(va - vb) > 1e-6 * max(1, abs(vb)):
            return False
    return True


def split_equation(text: str) -> Optional[Tuple[str, str]]:
    """'5x + 6 = 3x + 18' → ('5x + 6', '3x + 18') if it is one equation with a variable."""
    parts = clean(text).split("=")
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        return None
    l, r = prepare(parts[0]), prepare(parts[1])
    if not l or not r or len(l[1] | r[1]) != 1:      # exactly one variable
        return None
    return parts[0].strip(), parts[1].strip()


def linear_root(eq: Tuple[str, str]) -> Optional[float]:
    """Solve a LINEAR equation numerically: f(x) = left − right is a straight line."""
    left, right = prepare(eq[0]), prepare(eq[1])
    var = next(iter(left[1] | right[1]))

    def f(x: float) -> Optional[float]:
        lv, rv = evaluate(left[0], {var: x}), evaluate(right[0], {var: x})
        return None if lv is None or rv is None else lv - rv

    f0, f1, f2 = f(0), f(1), f(2)
    if f0 is None or f1 is None or f2 is None:
        return None
    if abs((f2 - f1) - (f1 - f0)) > 1e-9 or abs(f1 - f0) < 1e-12:   # not linear
        return None
    return -f0 / (f1 - f0)


def split_definition(text: str) -> Optional[Tuple[str, str]]:
    """'daughter = x/5' / 'mother is 5x' → (name, expr)"""
    s = re.sub(r"'s\b", "", clean(text))
    parts = s.split("=")
    if len(parts) != 2:
        parts = re.split(r"\bis\b", s)
        if len(parts) != 2:
            return None
    name = re.sub(r"\b(let|the|present|current|now|age|ages|of|be|years?|old)\b", " ", parts[0])
    name = re.sub(r"\s+", " ", name).strip()
    expr = re.sub(r"\b(years?|old)\b", " ", parts[1]).strip()
    if not re.fullmatch(r"[a-z]{2,}( [a-z]{2,})?", name) or not prepare(expr):
        return None
    return name, expr


# ─── 3. Read the methods from a graph ────────────────────────────────────────
def methods_of(graph: SolutionGraph) -> List[Dict[str, Any]]:
    by_id = {n.id: n for n in graph.nodes}

    def next_id(node_id: str) -> Optional[str]:
        return next((e.to_node for e in graph.edges if e.from_node == node_id), None)

    methods = []
    for m in graph.nodes:
        if m.type != "method":
            continue
        accepts = list(m.accept or [])
        cur, seen = next_id(m.id), set()
        while cur and cur not in seen and cur in by_id and by_id[cur].type == "step":
            seen.add(cur)
            accepts.extend(by_id[cur].accept or [])
            cur = next_id(cur)
        # this method's value of x = the root of its first linear equation
        root = None
        for a in accepts:
            eq = split_equation(a)
            if eq:
                root = linear_root(eq)
                if root is not None:
                    break
        methods.append({"id": m.id, "label": m.label, "accepts": accepts, "root": root})
    return methods


# ─── 4. Score one student line against one method ────────────────────────────
def _has_maths(t: str) -> bool:
    """Letters AND an operator."""
    return bool(re.search(r"[a-z]", t)) and bool(re.search(r"[+\-*/^=()]", t))


def _working(text: str) -> List[str]:
    """The numeric calculations in a line: '12² × 220 + 8² × 60 = 35000' → ['12^2 * 220 + 8^2 * 60']."""
    return [s.strip() for s in clean(text).split("=")
            if re.search(r"\d\s*[+\-*/^]\s*\d", s) and not re.search(r"[a-z]", s)]


def score_line(line: str, method: Dict[str, Any]) -> float:
    best = 0.0
    line_compact = compact(line)
    line_no_zero = re.sub(r"=0$", "", line_compact)       # "(x-2)(x-3)=0" → "(x-2)(x-3)"
    line_eq = split_equation(line)
    line_def = split_definition(line)
    line_words = set(words(line))
    line_nums = numbers(line)
    line_work = _working(line)

    for a in method["accepts"]:
        ac = compact(a)
        if ac == line_compact or ac == line_no_zero:         # same text
            return 1
        d = split_definition(a) if line_def else None
        if d and d[0] == line_def[0] and same_value(line_def[1], d[1]):
            best = max(best, 0.9)
        eq = split_equation(a) if line_eq else None
        if eq and same_value(line_eq[0], eq[0]) and same_value(line_eq[1], eq[1]):
            best = max(best, 0.85)
        if any(same_value(w, aw) for w in line_work for aw in _working(a)):  # same working, any result
            best = max(best, 0.75)
        if len(ac) >= 4 and _has_maths(ac) and ac in line_compact:          # line contains it
            best = max(best, 0.85)
        if len(line_compact) >= 3 and _has_maths(line_compact) and not line_eq and line_compact in ac:  # part of it
            best = max(best, 0.8)

        aw = words(a)                                         # key words
        if aw and line_words:
            shared = [w for w in aw
                      if w in line_words or any(x.startswith(w) or w.startswith(x) for x in line_words)]
            if shared:
                best = max(best, 0.6 * len(shared) / max(len(aw), len(line_words)))
        an = numbers(a)                                       # same numbers
        if len(line_nums) >= 2 and len(an) >= 2 and all(n in an for n in line_nums):
            best = max(best, 0.4)

    if line_eq and method["root"] is not None:                 # gives this method's x
        r = linear_root(line_eq)
        if r is not None and abs(r - method["root"]) < 1e-6:
            best = max(best, 0.6)
    return best


# ─── 5. Classify: lines → probabilities ──────────────────────────────────────
def _js_round3(x: float) -> float:
    # Math.round(1000 * x) / 1000 — JavaScript rounds .5 up, Python's round() does not.
    return math.floor(1000 * x + 0.5) / 1000


def classify_graph(graph: SolutionGraph, student_work: str,
                   threshold: float = CONFIDENCE_THRESHOLD) -> Dict[str, Any]:
    methods = methods_of(graph)
    lines = [s.strip() for s in re.split(r"\n|;", str(student_work)) if s.strip()]
    evidence = {m["id"]: 0.0 for m in methods}
    strongest = 0.0

    for line in lines:
        scores = [score_line(line, m) for m in methods]
        top = max(scores, default=-math.inf)
        strongest = max(strongest, top)
        if top == 0:
            continue
        # a shared line (several methods score the same) adds no preference
        for m, s in zip(methods, scores):
            evidence[m["id"]] += s - top

    ids = [m["id"] for m in methods]
    exps = [math.exp(SHARPNESS * evidence[i]) for i in ids]
    total = sum(exps)
    probabilities = {i: _js_round3(e / total) for i, e in zip(ids, exps)}

    if strongest < OFF_GRAPH_SCORE:
        return {"status": "off_graph", "confidence": 1 - strongest,
                "probabilities": probabilities, "off_graph": True}
    best_id = ids[0]
    for i in ids[1:]:
        if probabilities[i] > probabilities[best_id]:
            best_id = i
    confidence = probabilities[best_id]
    if confidence < threshold:
        return {"status": "uncertain", "confidence": confidence,
                "probabilities": probabilities, "off_graph": False}
    return {"status": "selected", "methodKey": best_id, "methodId": best_id, "confidence": confidence,
            "probabilities": probabilities, "off_graph": False}
