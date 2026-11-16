from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from app.graph_loader import get_graph
from app.schemas.graph import SolutionGraph
from app.schemas.session import MethodClassifyRequest, MethodClassifyResponse
from app.engine.method_classifier import classify_graph
from app.engine.matcher import matches_accept
from app.engine.sympy_validator import validate
from app.engine.tutor_engine import parse_step, expected_for
from app.engine.evaluator import EPS
from app.engine.claims import fmt_num
from app.engine.normalizer import normalize_text

router = APIRouter(prefix="/jev")


def _method_nodes(graph: SolutionGraph):
    return [n for n in graph.nodes if n.type == "method"]


def _short_label(label: str) -> str:
    return re.sub(r"^Method \d+:\s*", "", label)


def _declared_method(line: str, graph: SolutionGraph) -> Optional[str]:
    """'mother = x', 'let daughter be x' … are method choices listed in a METHOD node's accept list.
    A line that is also a step of some method ('3x - 2x = 4 + 1') is a step, not a declaration."""
    if any(matches_accept(line, a) for n in graph.nodes if n.type == "step" for a in n.accept or []):
        return None
    for n in _method_nodes(graph):
        if any(matches_accept(line, a) for a in n.accept or []):
            return n.id
    return None


def _swap_variable(text: str, old: str, new: str) -> str:
    """Rename a stand-alone letter: 'r^2 = 49', '2r' -> 'x^2 = 49', '2x' (not the r in 'radius')."""
    return re.sub(rf"(?<![A-Za-z]){re.escape(old)}(?![A-Za-z])", new, text)


# The validator has no trigonometry: "sin θ = r/5" would be misread as "θ = r/5" and called wrong
_TRIG = re.compile(r"\b(?:sin|cos|tan|cot|sec|cosec|theta)\b|θ", re.IGNORECASE)

# "P(50p coin) = 100/180 = 5/9": SymPy checks the maths after the probability's name
_PROB_LABEL = re.compile(r"^\s*P\([^()=]*\)\s*=\s*(?=.*(?:=|[-+*/]))")


def _graph_values(graph: SolutionGraph, word: Optional[str] = None) -> List[float]:
    """Every number and worked-out value in the steps' answers (only steps that use `word`, if given)."""
    values: List[float] = []
    for node in graph.nodes:
        if word and not any(re.search(rf"\b{re.escape(word)}\b", normalize_text(a)) for a in node.accept or []):
            continue
        exp = expected_for(node) if node.type in ("step", "conclusion") else None
        if exp and exp["kind"] in ("number", "values"):
            values += ([exp["value"]] if exp["kind"] == "number" else exp["values"]) + exp.get("worked", [])
    return values


def _labelled_value(line: str, graph: SolutionGraph) -> Optional[Dict[str, Any]]:
    """'total = 180' is correct when 180 is a value of this problem; 'P(50p) = 50/180' is a mistake when
    no step of this problem has that probability."""
    parsed = parse_step(line)
    if parsed.claims:
        return None
    value, word = parsed.label_value, None
    if value is None:
        m = re.match(r"^([a-z]+)[a-z ]*=\s*(\d+(?:\.\d+)?)$", parsed.normalized)    # total = 180
        if not m:
            return None
        word, value = m.group(1), float(m.group(2))
    targets = _graph_values(graph, word)
    if word and not targets:
        return None                                       # no step uses this word: leave it unchecked
    if any(abs(value - v) < EPS for v in targets):
        return {"status": "valid", "kind": "value", "statement": line}
    what = f"the {word}" if word else "a probability in this problem"
    return {"status": "invalid", "statement": line,
            "message": f"That works out to {fmt_num(value)}, which is not {what}."}


def _validate_work(work: str, equation: Optional[str], variable: str) -> Dict[str, Any]:
    """SymPy only knows x; a graph whose unknown is e.g. r (graph_meta.variable) is checked as x.
    Lines SymPy cannot read (trigonometry, points like (0, r)) are left unchecked, never wrong."""
    def to_x(text: str) -> str:
        return text if variable == "x" else _swap_variable(text, variable, "x")

    checkable, skipped = [], []
    for line in work.split("\n"):
        line = _PROB_LABEL.sub("", line)
        if _TRIG.search(line):
            skipped.append({"status": "unchecked", "reason": "trigonometry is not checked by SymPy", "statement": line})
            continue
        try:
            validate(to_x(line), equation)
            checkable.append(line)
        except Exception:
            skipped.append({"status": "unchecked", "reason": "could not read this as maths", "statement": line})

    if checkable:
        result = validate(to_x("\n".join(checkable)), equation)
    else:
        result = {"is_valid": True, "lines": [], "errors": [], "roots_claimed": [], "missing_roots": [], "solved": False}
    if variable != "x":
        for line in result["lines"]:
            for key in ("statement", "message"):
                if line.get(key):
                    line[key] = _swap_variable(line[key], "x", variable)
    result["lines"] += skipped
    return result


def _candidate_equations(graph: SolutionGraph) -> List[Optional[str]]:
    """One SymPy equation per method when methods use x differently, otherwise the problem's equation."""
    per_method = [getattr(n, "sympy_equation", None) for n in _method_nodes(graph)]
    found: List[Optional[str]] = []
    for eq in per_method + [getattr(graph.graph_meta, "equation", None)]:
        if eq and eq not in found:
            found.append(eq)
    return found or [None]


def _pick_validation(graph: SolutionGraph, method: Dict[str, Any], results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The selected method's equation if Jev is sure, otherwise the reading that finds the work correct."""
    if not results:
        return {"status": "unavailable"}
    if method.get("status") == "selected":
        node = next((n for n in _method_nodes(graph) if n.id == method.get("methodId")), None)
        eq = getattr(node, "sympy_equation", None) if node else None
        match = next((v for v in results if eq and v["equation"] == eq), None)
        if match:
            return match

    def score(v: Dict[str, Any]) -> int:
        return (-1000 * len(v["errors"]) if v["errors"] else 0) + sum(1 for l in v["lines"] if l["status"] == "valid")

    return sorted(results, key=score, reverse=True)[0]


def _combine(graph: SolutionGraph, method: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, str]:
    """Jev result + SymPy result -> one answer. SymPy's verdict on correctness comes first."""
    labels = {n.id: _short_label(n.label) for n in _method_nodes(graph)}
    sympy_ok = validation.get("status") != "unavailable"
    jev_ok = method.get("status") != "unavailable"
    checked = sum(1 for l in validation.get("lines", []) if l["status"] == "valid") if sympy_ok else 0
    can_finish = getattr(graph.graph_meta, "sympy_can_finish", None) is not False

    # 1. A maths mistake always wins.
    if sympy_ok and validation["errors"]:
        e = validation["errors"][0]
        return {"status": "fix_mistake",
                "feedback": f'There is a mistake in "{e["statement"]}". {e.get("message") or ""}'.strip()}

    # 2. Every root found and every line correct.
    if sympy_ok and validation["solved"] and can_finish:
        return {"status": "solved", "feedback": f"Correct! x = {' or x = '.join(validation['roots_claimed'])}."}

    missing_root = (f" You found x = {', '.join(validation['roots_claimed'])}. There is one more root to find."
                    if sympy_ok and can_finish and validation["missing_roots"] else "")

    # 3. No mistakes — now use Jev's classification.
    if jev_ok and method.get("status") == "selected":
        prefix = "Correct so far." if checked else "Looks good."
        label = labels.get(method["methodKey"], str(method["methodKey"]).replace("_", " "))
        return {"status": "on_track", "feedback": f"{prefix} You are using {label}.{missing_root}"}
    if jev_ok and method.get("status") == "off_graph":
        lead = "Your working is correct, but I" if checked else "I"
        return {"status": "off_graph",
                "feedback": f"{lead} don't recognise this method. Which method are you using?{missing_root}"}
    if jev_ok and method.get("status") == "uncertain":
        lead = "Correct so far. " if checked else ""
        return {"status": "uncertain", "feedback": f"{lead}Which method are you using?{missing_root}"}

    # 4. Jev unavailable — SymPy-only feedback.
    if sympy_ok:
        return {"status": "on_track" if checked else "unchecked",
                "feedback": f"Correct so far.{missing_root}" if checked
                else "I could not check this step. Try writing it as an equation."}
    return {"status": "unavailable", "feedback": "Checking is unavailable right now. Please try again."}


@router.post("/classify", response_model=MethodClassifyResponse)
def classify_method(req: MethodClassifyRequest):
    """Local Jev (which method?) + SymPy (is the maths correct?) for every line written so far."""
    graph = get_graph(req.problem_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Problem '{req.problem_id}' not found.")
    lines = [l.strip() for l in req.lines if l and l.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="At least one line of student work is required.")

    work = "\n".join(lines)
    try:
        method = classify_graph(graph, work)
    except Exception:
        method = {"status": "unavailable"}

    variable = str(getattr(graph.graph_meta, "variable", None) or "x")
    results = []
    for eq in _candidate_equations(graph):
        try:
            results.append({**_validate_work(work, eq, variable), "equation": eq})
        except Exception:
            continue
    validation = _pick_validation(graph, method, results)
    labelled = [v for v in (_labelled_value(l, graph) for l in lines) if v]
    if labelled and validation.get("status") != "unavailable":
        unknown = [v for v in labelled if v["status"] == "invalid"]
        validation = {**validation, "lines": validation.get("lines", []) + labelled,
                      "errors": unknown + validation.get("errors", []),
                      "is_valid": validation.get("is_valid", True) and not unknown}

    return MethodClassifyResponse(
        **_combine(graph, method, validation),
        method=method,
        validation=validation,
        method_labels={n.id: _short_label(n.label) for n in _method_nodes(graph)},
        declared_methods=[_declared_method(l, graph) for l in lines],
    )
