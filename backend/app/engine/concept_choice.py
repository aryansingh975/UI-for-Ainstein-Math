"""Conceptual choice nodes: the student explains a plan in free text ("find both volumes with πr²h, add, × 8").

Used by guided.py at a choice node that has concepts_required. Order:
  a. normalise   - lower case, spelling fixed against the node's keywords (rapidfuzz), synonyms mapped
                   ("pi r square h" → πr²h, "into 8" → × 8)
  b. detect      - which required concepts and misconceptions appear anywhere in the text
  c. classify    - exactly one of correct | partial | misconception | contradiction | dont_know | off_topic
  d. fallback    - when no rule decides, Jev (method_classifier) is asked; its result is validated with pydantic
  e. as maths    - when the node has plan_formula, a local Qwen writes the plan as an expression and SymPy
                   checks it (plan_llm.py): a plan in other words or another order ("× 8 each, then add") is right,
                   but a step the keywords missed counts only when Qwen can quote the student's words for it
Then respond: accept with a path, or a message (partial hint, misconception response, scaffold question, reveal).
The path of a correct plan is Jev's method when Jev is sure; otherwise path_signals, then default_path.

The hint ladder (a node whose concepts have `hints`):
  1. one idea at a time, in the node's order: its question, then its nudge, then its answer (never the answer first)
  2. progress is kept between attempts (PlanProgress): an idea said once stays found, so the plan is never retyped;
     the UI ticks found ideas and shows the rest only as "one more step"
  3. when the tutor gave a step (or the whole plan, after the K hints), the student explains one given step in
     their own words before solving; the understanding is said either way, so nobody is stuck there
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ValidationError
from rapidfuzz import fuzz, process

from app.schemas.graph import Node

Category = Literal["correct", "partial", "misconception", "contradiction", "dont_know", "off_topic", "explain"]


class PlanProgress(BaseModel):
    """What the student has built so far at this plan node (kept on the session between attempts)."""
    found: List[str] = Field(default_factory=list)       # ideas the student said
    given: List[str] = Field(default_factory=list)       # ideas the tutor said (the ladder's last rung, or a reveal)
    levels: Dict[str, int] = Field(default_factory=dict) # hints shown per idea
    explain: Optional[str] = None                        # waiting for the student to explain this given idea
    path: Optional[str] = None                           # the method to follow once the explanation is in


class ChoiceOutcome(BaseModel):
    """What the UI gets back for a plan."""
    category: Category
    concepts_found: List[str] = Field(default_factory=list)
    concepts_missing: List[str] = Field(default_factory=list)
    concept_ideas: Dict[str, str] = Field(default_factory=dict)
    path: Optional[str] = None
    message: str = ""
    accepted: bool = False
    scaffold_index: Optional[int] = None          # the scaffold question being asked next (None: not scaffolding)
    concept_hint: Optional[Dict[str, str]] = None # K1, K2, … after a failed plan: {id, question}
    expression: Optional[str] = None              # the plan as maths, written by Qwen (plan_llm.py)
    concepts_given: List[str] = Field(default_factory=list)   # ideas the tutor had to give
    next_question: Optional[str] = None           # the ladder's question, or (category "explain") the explain question
    progress: Optional[Dict[str, Any]] = None     # PlanProgress, for guided.py to keep on the session


class JevVerdict(BaseModel):
    """The part of method_classifier.classify_graph's answer this module relies on."""
    status: Literal["selected", "uncertain", "off_graph"]
    methodId: Optional[str] = None
    confidence: float = 0.0
    probabilities: Dict[str, float] = Field(default_factory=dict)


# ─── a. Normalise ────────────────────────────────────────────────────────────
_SYNONYMS = [
    (r"[’‘`]", "'"),
    (r"\bpi\b", "π"),
    (r"\br\s*(?:squared?|sq|\^\s*2|\*\*\s*2)(?![a-z])", "r²"),                  # not r2: that may be "r₂"
    (r"π\s*[×x*]?\s*r(?:²|2)\s*[×x*]?\s*h(?![a-z])", "πr²h"),                    # πr2h is πr²h
    (r"(?:\b(?:into|times|multiplied by|multiply(?:ing)?(?: it| that| them| the volume)?(?: by| with)?|x)\b|[*×])"
     r"\s*(?:by\s+)?(\d+(?:\.\d+)?)(?!\d|\.\d)", r"× \1"),            # "multiply by 8." at a full stop
    (r"\s+", " "),
]
_DOMAIN_WORDS = ["volume", "cylinder", "cylinders", "mass", "multiply", "square", "squared", "radius", "height",
                 "subtract", "both", "formula", "total"]
_DONT_KNOW = ["don't know", "dont know", "do not know", "no idea", "not sure", "idk", "no clue", "give up",
              "dunno", "don't understand", "dont understand", "guide me", "help me"]


def _without_unknowns(raw: str) -> str:
    """The plan without what the student does not claim: a question ("what is a prime?") and anything from
    "I don't know" to the end of that clause ("i dont know what is prime factor" → ""), so "prime" there is not
    the idea "using prime numbers". "I divide by 2 but I don't know when to stop" keeps "I divide by 2"."""
    kept = []
    for part in re.split(r"(?<=[.,;!?\n])|\bbut\b", raw.lower().replace("’", "'").replace("‘", "'")):
        if part.strip().endswith("?"):
            continue
        hits = [part.find(p) for p in _DONT_KNOW if p in part]
        if hits:                                              # "… then I'm not sure": drop "then I'm" too
            part = re.sub(r"(?:\s*\b(?:i|i'm|im|we|still|then|and|really|actually|just))+\s*$", "",
                          part[:min(hits)])
        kept.append(part)
    return " ".join(kept)


Reader = Callable[[str, str], bool]   # plan_llm.says: do the student's own words say this idea?


def _vocabulary(node: Node) -> List[str]:
    phrases = [k for c in node.concepts_required for k in c.keywords]
    phrases += [k for c in node.concepts_required for k in c.needs_any]
    phrases += [k for m in node.misconceptions for k in m.keywords]
    phrases += [k for s in node.scaffold_questions for k in s.expected_keywords]
    phrases += [p for signals in node.path_signals.values() for p in signals]
    words = {w for p in phrases for w in re.findall(r"[a-z]{4,}", p.lower())}
    return sorted(words | set(_DOMAIN_WORDS))


def normalise(text: str, node: Node) -> str:
    vocab = _vocabulary(node)

    def fix(m: re.Match) -> str:                              # "volumn" → "volume", "cylender" → "cylinder"
        word = m.group(0)
        if word in vocab:
            return word
        best = process.extractOne(word, vocab, scorer=fuzz.ratio, score_cutoff=80)
        return best[0] if best and abs(len(best[0]) - len(word)) <= 2 else word

    t = re.sub(r"[a-z]{4,}", fix, text.lower())
    for pattern, repl in _SYNONYMS:
        t = re.sub(pattern, repl, t)
    return t.strip()


# ─── b. Detect ───────────────────────────────────────────────────────────────
def _has(text: str, keyword: str) -> bool:
    """A word matches as a word prefix (add → adding), anything else (πr²h, × 8, both volumes) as text."""
    if re.fullmatch(r"[a-z]+", keyword):
        return re.search(rf"(?<![a-z]){re.escape(keyword)}", text) is not None
    return keyword in text


def _found(text: str, keywords: List[str], node: Node) -> bool:
    return any(_has(text, normalise(k, node)) for k in keywords)


# ─── c/d. Classify and respond ───────────────────────────────────────────────
def _pick_path(text: str, node: Node, default: Optional[str]) -> Optional[str]:
    hits = {path: sum(_found(text, [s], node) for s in signals) for path, signals in node.path_signals.items()}
    best = max(hits.values(), default=0)
    winners = [p for p, h in hits.items() if h == best and h > 0]
    return winners[0] if len(winners) == 1 else default


def _jev(jev: Optional[Dict[str, Any]]) -> Optional[JevVerdict]:
    try:
        return JevVerdict.model_validate(jev) if jev else None
    except ValidationError:
        return None


def _first_hint(c) -> str:
    return (c.hints or [c.hint])[0]


def _explain_target(node: Node, ids: List[str]):
    """The first of these ideas with an explain question (else any idea with one), or None."""
    with_q = [c for c in node.concepts_required if c.explain]
    return next((c for c in with_q if c.id in ids), with_q[0] if with_q else None)


def _explain_answer(raw: str, node: Node, prog: PlanProgress, default: Optional[str], base: Dict[str, Any],
                    reader: Optional[Reader] = None) -> ChoiceOutcome:
    """The student's explanation of a given step: say the understanding, then go on (it never blocks).
    Right by its keywords, or (reader) when Qwen quotes the student's own words for the understanding."""
    c = next(c for c in node.concepts_required if c.id == prog.explain)
    base.update(concepts_found=prog.found, concepts_missing=[])   # "8 g" here explains; it is no new idea
    claimed = _without_unknowns(raw)
    right = _found(normalise(claimed, node), c.explain.expected_keywords, node) or bool(
        reader and re.search(r"[a-z]{3,}", claimed) and reader(claimed, c.explain.understanding))
    message = ("Yes, exactly. " if right else "Here's the idea. ") + c.explain.understanding
    if node.solve_freely:
        message += " Now solve it on your own."
    prog.explain = None
    return ChoiceOutcome(category="explain", message=message, accepted=True, path=prog.path or default,
                         **base, progress=prog.model_dump())


def evaluate_plan(raw: str, node: Node, jev: Optional[Dict[str, Any]] = None,
                  scaffold_index: Optional[int] = None, failed: int = 0,
                  default_path: Optional[str] = None, llm: Optional[Dict[str, Any]] = None,
                  progress: Optional[Dict[str, Any]] = None, reader: Optional[Reader] = None) -> ChoiceOutcome:
    """Classify one plan and build the reply. failed = earlier failed attempts at this node;
    default_path = the node's default_path, else the graph's first method (passed in by guided.py);
    llm = plan_llm.check_plan's {"expression", "matches"} (SymPy's verdict on the plan as maths), or None;
    progress = the PlanProgress of earlier attempts (the hint ladder), or None;
    reader = plan_llm.says, or None: an idea the keywords missed counts when Qwen quotes the student's words."""
    full = normalise(raw, node)                              # everything: for "I don't know"
    claimed = _without_unknowns(raw)                         # only what the student claims: for the ideas
    text = normalise(claimed, node)
    default = node.default_path or default_path
    ideas = {c.id: c.idea or c.id for c in node.concepts_required}
    order = [c.id for c in node.concepts_required]
    ladder = any(c.hints for c in node.concepts_required)
    prog = PlanProgress.model_validate(progress or {})
    mentioned = [c.id for c in node.concepts_required if _found(text, c.keywords, node)]
    found = [c.id for c in node.concepts_required if c.id in mentioned
             and (not c.needs_any or _found(text, c.needs_any, node)    # "add the heights" is not C1 ...
                  or prog.levels.get(c.id))]       # ... but "put them together" answers the question about adding
    wrong_idea = any(_found(text, m.keywords, node) for m in node.misconceptions)
    if (reader and not wrong_idea and not (llm and llm["matches"] is False)   # SymPy: the plan's maths is wrong
            and (found or prog.found or prog.given)           # Qwen completes a plan, it never makes one up
            and not (ladder and prog.explain) and re.search(r"[a-z]{3,}", text)):
        said = [c.id for c in node.concepts_required          # in other words: "till you can't any more"
                if c.id not in found and c.id not in prog.found + prog.given and reader(claimed, ideas[c.id])]
        found = [i for i in order if i in found or i in said]
    missing = [c.id for c in node.concepts_required if c.id not in found]
    new = [i for i in found if i not in prog.found + prog.given]   # said for the first time in this attempt
    if ladder:                                               # what was said before still counts
        found = [i for i in order if i in found or i in prog.found]
        missing = [i for i in order if i not in found and i not in prog.given]
    base = dict(concepts_found=found, concepts_missing=missing, concept_ideas=ideas, concepts_given=prog.given,
                expression=llm["expression"] if llm else None)

    if ladder and prog.explain:                              # rule 3: the explanation of a given step
        return _explain_answer(raw, node, prog, default, base, reader)

    def outcome(category: Category, message: str, accepted: bool = False, path: Optional[str] = None,
                scaffold: Optional[int] = None, k_hint: bool = True, ask: Optional[str] = None) -> ChoiceOutcome:
        if ladder:
            prog.found = list(found)
        if (k_hint and not accepted and scaffold is None and node.max_hints and failed + 1 >= node.max_hints):
            if ladder:                                       # out of K hints: show the plan, then explain one step
                prog.given = [i for i in order if i not in found]
                return explain(node.reveal or "Here is the plan.", default, [*prog.given, *order])
            return ChoiceOutcome(category=category, message=node.reveal or message, accepted=True, path=default,
                                 **base)                     # out of hints: show the plan and carry on
        hint = None                                           # a failed plan also gets the next K question
        if k_hint and not accepted and scaffold is None and failed < len(node.concept_hints):
            k = node.concept_hints[failed]
            hint = {"id": k.id, "question": k.question}
        return ChoiceOutcome(category=category, message=message, accepted=accepted, path=path,
                             scaffold_index=scaffold, concept_hint=hint, next_question=ask, **base,
                             progress=prog.model_dump() if ladder else None)

    def explain(message: str, path: Optional[str], ids: List[str]) -> ChoiceOutcome:
        """The plan is complete with the tutor's help: one given step in the student's own words first."""
        c = _explain_target(node, ids)
        base.update(concepts_given=prog.given, concepts_missing=[])
        if c is None:                                        # nothing to ask: go on
            return ChoiceOutcome(category="explain", message=message, accepted=True, path=path or default,
                                 **base, progress=prog.model_dump())
        prog.explain, prog.path = c.id, path or default
        return ChoiceOutcome(category="explain", message=f"{message} Before you solve: {c.explain.question}",
                             next_question=c.explain.question, **base, progress=prog.model_dump())

    verdict = _jev(jev)
    for m in node.misconceptions:                         # a wrong idea first: even with all three ideas
        if _found(text, m.keywords, node):
            if m.signal and m.signal in mentioned:            # "add or maybe subtract"
                return outcome("contradiction", node.contradiction_response or
                               "You said two different things. Which one is it?", k_hint=not ladder)
            return outcome("misconception", m.response, k_hint=not ladder)

    jev_path = verdict.methodId if verdict and verdict.status == "selected" else None
    if not missing:                                           # every idea is there
        path = jev_path or _pick_path(text, node, default)
        if ladder and prog.given:                             # some of it came from the tutor
            prog.found = list(found)
            return explain("That's the whole plan.", path, prog.given[::-1])   # the step given last
        done = "That's a complete plan." + (" Now solve it on your own." if node.solve_freely else "")
        if ladder:
            prog.found = list(found)
        return outcome("correct", done, True, path)

    if ladder and (found or prog.given):                      # rule 1: the ladder, one idea at a time
        said = (node.partial_prefix or "Good, {found} is right.").format(
            found=" and ".join(ideas[i] for i in new)) + " " if new else ""
        c = next(c for c in node.concepts_required if c.id == missing[0])
        level = prog.levels.get(c.id, 0)
        if level < len(c.hints):                              # its question, then its nudge
            prog.levels[c.id] = level + 1
            return outcome("partial", said + c.hints[level], k_hint=False, ask=c.hints[level])
        prog.given.append(c.id)                               # then the step itself
        missing.remove(c.id)
        base.update(concepts_missing=missing, concepts_given=prog.given)
        if not missing:
            prog.found = list(found)
            return explain(f"{said}{c.answer} That's the whole plan.", jev_path or _pick_path(text, node, default),
                           prog.given[::-1])                  # ask about the step just given
        nxt = next(n for n in node.concepts_required if n.id == missing[0])
        prog.levels[nxt.id] = 1
        return outcome("partial", f"{said}{c.answer} Next: {nxt.hints[0]}", k_hint=False, ask=nxt.hints[0])

    if scaffold_index is not None and scaffold_index < len(node.scaffold_questions):
        step = node.scaffold_questions[scaffold_index]       # walking the scaffold: one question at a time
        if _found(text, step.expected_keywords, node):
            nxt = scaffold_index + 1
            if nxt >= len(node.scaffold_questions):
                return outcome("dont_know", "Right. " + (node.reveal or "That's the plan."), True, default)
            return outcome("dont_know", "Right. " + node.scaffold_questions[nxt].question, scaffold=nxt)
        return outcome("dont_know", "Not quite. " + step.question, scaffold=scaffold_index)

    if not found and any(p in full for p in _DONT_KNOW):
        reply = node.dont_know_response or "That's fine, let's build the plan together."
        if not node.scaffold_questions:                       # concept hints (K1, K2, …) instead of a scaffold
            return outcome("dont_know", reply)
        return outcome("dont_know", f"{reply} {node.scaffold_questions[0].question}", scaffold=0)

    if found:
        prefix = (node.partial_prefix or "Good, {found} is right.").format(found=" and ".join(ideas[i] for i in found))
        hint = next(_first_hint(c) for c in node.concepts_required if c.id == missing[0])
        return outcome("partial", f"{prefix} {hint}".strip())

    if verdict and verdict.status == "selected":
        hint = next(_first_hint(c) for c in node.concepts_required if c.id == missing[0])
        return outcome("partial", hint, path=verdict.methodId)
    if failed and node.concept_hints and node.retry_response:     # likely an answer to the K question just shown
        return outcome("off_topic", node.retry_response)
    return outcome("off_topic", node.off_topic_response or "Let's get back to the problem. What is your plan?")
