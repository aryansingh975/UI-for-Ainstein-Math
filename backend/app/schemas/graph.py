from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

NodeType = Literal["start", "extraction", "method", "step", "conclusion"]


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

