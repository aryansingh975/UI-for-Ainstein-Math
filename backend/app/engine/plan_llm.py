"""A plan in words, checked as maths: a local Qwen (Ollama) writes the plan as an expression, SymPy checks it.

  "find both volumes, multiply each by 8, then add"  →  Qwen  →  8*pi*r1**2*h1 + 8*pi*r2**2*h2
  SymPy: equal to the node's plan_formula.expression ("8*pi*(r1**2*h1 + r2**2*h2)")? → the plan is right

Qwen only translates; it never decides. Anything that goes wrong (Ollama not running, a timeout, an answer
that does not parse) returns None and concept_choice.py's keyword check decides alone.

The maths alone cannot tell a step the student said in other words from a step Qwen added: "volume of each,
× 8" has no "add", but Qwen still writes the sum (one expression cannot hold two separate masses). So a step
the keywords missed counts only when says() finds the student's own words for it: Qwen quotes them and the
quote must really be in the plan. An invented step has nothing to quote, so it stays missing.

hint() writes a hint aimed at a wrong step; guided.py only shows it after SymPy has checked it.
Settings: PLAN_LLM=off disables it; PLAN_LLM_URL (default http://localhost:11434); PLAN_LLM_MODEL;
PLAN_LLM_HINTS=on lets Qwen write step hints (off by default: a small model's hints can mislead).
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any, Dict, Optional

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

from app.schemas.graph import Node, PlanFormulaSpec

DEFAULT_MODEL = "qwen3.5:2b"
TIMEOUT = 20                                                   # seconds; the first call also loads the model
KEEP_ALIVE = "30m"                                             # Ollama's default (5 min) unloads it between students

_PROMPT = """You turn a student's plan for a maths problem into ONE SymPy expression.
Use only these symbols:
{symbols}
- pi: π
Write exactly what the student says, even when it is wrong (if they subtract, subtract). Do not fix it.
If a step is missing, leave it out. If the text is not a plan, return an empty expression."""

_QUOTE_PROMPT = """Here is a student's plan for a maths problem. Does the student say this step: "{idea}"?
If yes, copy the exact words from the plan that say it. If the plan does not say it, return an empty quote.
Do not guess what the student meant to say."""


def enabled() -> bool:
    return os.environ.get("PLAN_LLM", "on").lower() not in ("off", "0", "false", "no")


def hints_enabled() -> bool:
    """Qwen-written step hints: off unless PLAN_LLM_HINTS=on. Tested with qwen3.5:2b (2026-11-13), half of its
    hints were misleading in words ("the LCM must be greater than 2366") that no SymPy check can catch."""
    return enabled() and os.environ.get("PLAN_LLM_HINTS", "off").lower() in ("on", "1", "true", "yes")


def _model() -> str:
    return os.environ.get("PLAN_LLM_MODEL", DEFAULT_MODEL)


def _post(path: str, body: Dict[str, Any], timeout: float = TIMEOUT) -> Dict[str, Any]:
    url = os.environ.get("PLAN_LLM_URL", "http://localhost:11434").rstrip("/") + path
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _chat(system: str, user: str, field: str) -> str:
    """Ollama /api/chat with a JSON schema, so the answer is always {field: "..."}."""
    body = {
        "model": _model(),
        "stream": False,
        "think": False,
        "keep_alive": KEEP_ALIVE,
        "format": {"type": "object", "properties": {field: {"type": "string"}}, "required": [field]},
        "options": {"temperature": 0},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    content = _post("/api/chat", body)["message"]["content"]
    return (json.loads(content).get(field) or "").strip()


def _ask(plan: str, spec: PlanFormulaSpec) -> Optional[str]:
    """The plan as one expression, or None."""
    symbols = "\n".join(f"- {s}: {meaning}" for s, meaning in spec.symbols.items())
    return _chat(_PROMPT.format(symbols=symbols), plan, "expression") or None


def _words(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9×²³]+", text.lower()))


def says(plan: str, idea: str) -> bool:
    """True when the student's own words say this step: Qwen quotes them, and the quote is in the plan."""
    if not enabled():
        return False
    try:
        quote = _chat(_QUOTE_PROMPT.format(idea=idea), plan, "quote")
    except Exception:                                          # Ollama not running, timeout: not proven
        return False
    quote, text = _words(quote), _words(plan)
    if len(text.split()) > 6 and len(quote.split()) >= 0.8 * len(text.split()):
        return False                                          # the whole plan quoted back proves nothing
    return bool(quote) and quote != _words(idea) and f" {quote} " in f" {text} "


_HINT_PROMPT = """You are a patient maths tutor for a 15-year-old. The student answered one step wrong.
Write ONE short hint (at most 25 words) that helps them find their own mistake.
- Ask a question or point at the exact mistake. Never give the final answer to this step.
- Use only true maths. Do not use numbers that are not in the question, the step or the student's answer.
Problem: {problem}
Step: {step}
Method: {method}
What the checker found: {finding}
The tutor's own hint for this moment (you may reuse its idea): {hint}"""


def hint(problem: str, step: str, answer: str, finding: str, fallback: str, method: str = "") -> Optional[str]:
    """A hint aimed at this answer, or None (Ollama not running, a timeout, an empty reply).
    guided.py checks it with SymPy before a student sees it; None or a rejected hint → the graph's hint."""
    if not enabled():
        return None
    try:
        text = _chat(_HINT_PROMPT.format(problem=problem, step=step, method=method or "any",
                                         finding=finding or "the answer is not right yet", hint=fallback),
                     f"My answer: {answer}", "hint")
    except Exception:
        return None
    text = " ".join(text.split())
    return text if 8 <= len(text) <= 220 else None


def warm_up() -> None:
    """Load the model now, so the first student does not wait for it (or time out). Never raises."""
    if not enabled():
        return
    try:
        _post("/api/generate", {"model": _model(), "keep_alive": KEEP_ALIVE}, timeout=120)
    except Exception:
        pass


def _parse(expression: str, spec: PlanFormulaSpec) -> Optional[sp.Expr]:
    names = {s: sp.Symbol(s) for s in spec.symbols} | {"pi": sp.pi}
    try:
        expr = parse_expr(expression.replace("^", "**").replace("×", "*").replace("π", "pi"), local_dict=names,
                          transformations=standard_transformations + (implicit_multiplication_application,))
    except Exception:
        return None
    if not isinstance(expr, sp.Expr) or expr.free_symbols - {names[s] for s in spec.symbols}:
        return None                                            # a letter we did not ask for
    return expr


def same(expression: str, spec: PlanFormulaSpec) -> Optional[bool]:
    """True when the expression equals the plan formula (in any order: 8V1 + 8V2 = 8(V1 + V2)); None: no maths."""
    got, want = _parse(expression, spec), _parse(spec.expression, spec)
    if got is None or want is None:
        return None
    if sp.simplify(got - want) == 0:
        return True
    if spec.values:                                            # the same number with the problem's values
        values = {sp.Symbol(s): v for s, v in spec.values.items()}
        a, b = complex(got.subs(values).evalf()), complex(want.subs(values).evalf())
        return abs(a - b) <= 1e-9 * max(1.0, abs(b))
    return False


def check_plan(plan: str, node: Node) -> Optional[Dict[str, Any]]:
    """{"expression": what Qwen wrote, "matches": True/False}, or None when there is nothing to go on."""
    if not node.plan_formula or not enabled():
        return None
    try:
        expression = _ask(plan, node.plan_formula)
    except Exception:                                          # Ollama not running, timeout, bad JSON
        return None
    matches = same(expression, node.plan_formula) if expression else None
    return None if matches is None else {"expression": expression, "matches": matches}
