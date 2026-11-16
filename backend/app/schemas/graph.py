from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

NodeType = Literal["start", "extraction", "concept", "choice", "method", "step", "conclusion"]


class GraphContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    chapter: Optional[int] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    subject: Optional[str] = None
    grade: Optional[int] = None


class GraphMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    graph_id: str
    problem_uuid: str
    problem_text: str
    navigation_label: Optional[str] = None
    problem_context: Optional[Dict[str, Any]] = None
    graph_type: Optional[str] = "directed_acyclic_graph"
    version: Optional[str] = "1.0.0"
    description: Optional[str] = None
    created: Optional[str] = None
    total_methods: Optional[int] = None
    total_nodes: Optional[int] = None
    total_edges: Optional[int] = None


class ExplainSpec(BaseModel):
    """After the tutor gave this step: the student explains it in their own words before solving."""
    question: str                                        # "Why do we multiply the volume by 8?"
    expected_keywords: List[str] = Field(default_factory=list)
    understanding: str = ""                              # said after the answer, right or wrong


class ConceptSpec(BaseModel):
    """One idea a plan must contain ('add the two volumes'); found when any keyword appears."""
    id: str
    idea: str = ""
    keywords: List[str] = Field(default_factory=list)
    needs_any: List[str] = Field(default_factory=list)   # counts only with one of these too: "add" + "volume"
    hint: str = ""
    hints: List[str] = Field(default_factory=list)       # the ladder: a question, then a nudge (at most 2) ...
    answer: str = ""                                     # ... then the step itself, said plainly
    explain: Optional[ExplainSpec] = None


class MisconceptionSpec(BaseModel):
    """A wrong idea. signal = id of the concept it replaces: both together are a contradiction."""
    signal: str = ""
    keywords: List[str] = Field(default_factory=list)
    response: str = ""


class ScaffoldSpec(BaseModel):
    question: str
    expected_keywords: List[str] = Field(default_factory=list)


class ConceptHintSpec(BaseModel):
    """K1, K2, …: a question shown after a failed plan; the student then tries the plan again."""
    id: str
    question: str
    understanding: str = ""


class FormulaSpec(BaseModel):
    """A formula the student may write with letters ('volume = πr²h'); SymPy compares it with expression."""
    name: str
    expression: str                                  # SymPy syntax with single-letter symbols: "pi*r**2*h"
    labels: List[str] = Field(default_factory=list)  # left-hand sides that name it: "volume", "v"
    words: Dict[str, str] = Field(default_factory=dict)   # what students write for a letter: "total volume" → "v"


class PlanFormulaSpec(BaseModel):
    """The plan as maths: a local LLM turns the plan's words into an expression; SymPy compares it with this."""
    expression: str                                          # "8*pi*(r1**2*h1 + r2**2*h2)"
    symbols: Dict[str, str] = Field(default_factory=dict)    # what each letter means, told to the LLM
    values: Dict[str, float] = Field(default_factory=dict)   # the problem's numbers, for a numeric comparison


class Node(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    type: NodeType
    label: str
    description: str = ""
    prompt: str = ""
    accept: List[str] = Field(default_factory=list)
    hints: List[str] = Field(default_factory=list)
    optional: Optional[bool] = None

    # choice node: the student explains a plan in free text (all optional; see engine/concept_choice.py)
    concepts_required: List[ConceptSpec] = Field(default_factory=list)
    path_signals: Dict[str, List[str]] = Field(default_factory=dict)
    default_path: Optional[str] = None
    misconceptions: List[MisconceptionSpec] = Field(default_factory=list)
    contradiction_response: Optional[str] = None
    dont_know_response: Optional[str] = None
    off_topic_response: Optional[str] = None
    retry_response: Optional[str] = None             # after a K hint: an answer that is not yet a plan
    scaffold_questions: List[ScaffoldSpec] = Field(default_factory=list)
    concept_hints: List[ConceptHintSpec] = Field(default_factory=list)
    solve_freely: Optional[bool] = None             # after the plan: the student solves alone (feedback on mistakes)
    solve_prompt: Optional[str] = None
    formulas: List[FormulaSpec] = Field(default_factory=list)   # checked while solving alone
    factorise: List[int] = Field(default_factory=list)   # each number must be written as a product of primes
    plan_formula: Optional[PlanFormulaSpec] = None   # a plan in words, checked as maths (engine/plan_llm.py)
    partial_prefix: Optional[str] = None
    max_hints: Optional[int] = None
    reveal: Optional[str] = None


class Edge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")


class SolutionGraph(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    graph_meta: GraphMeta
    start_node: str = "start"
    conclusion_node: str = "conclusion"
    nodes: List[Node]
    edges: List[Edge]

