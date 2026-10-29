from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProblemSummary(BaseModel):
    problem_uuid: str
    navigation_label: str
    problem_text: str
    chapter: str
    topic: str
    grade: str


class SessionStartRequest(BaseModel):
    problem_id: str


class SessionStartResponse(BaseModel):
    session_id: str
    problem_id: str
    problem_title: str
    problem_text: str
    active_node_id: Optional[str] = None
    active_label: Optional[str] = None
    prompt: Optional[str] = None
    hints: List[str] = Field(default_factory=list)
    completed: bool = False
    chapter: Optional[str] = None
    topic: Optional[str] = None
    grade: Optional[int] = None
    is_beginning: bool = True
    trail: List[Dict[str, Any]] = Field(default_factory=list)
    history: List[Dict[str, Any]] = Field(default_factory=list)


class StepRequest(BaseModel):
    student_input: str


class StepResponse(BaseModel):
    verdict: str
    parsed_input: str
    active_node_id: Optional[str] = None
    active_label: Optional[str] = None
    next_prompt: Optional[str] = None
    feedback_message: Optional[str] = None
    hint: Optional[str] = None
    explanation: Optional[str] = None
    approach_only: bool = False
    completed: bool = False
    fail_streak: int = 0
    claim: Optional[Dict[str, Any]] = None
    trail: List[Dict[str, Any]] = Field(default_factory=list)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    conclusion_prompt: Optional[str] = None
    conclusion_description: Optional[str] = None
    next_is_conclusion: bool = False
    method_id: Optional[str] = None
    method_label: Optional[str] = None

