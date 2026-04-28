from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ExplainRequest(BaseModel):
    session_id: str
    topic: str
    explanation: str


class GapNode(BaseModel):
    concept: str
    understood: bool
    score: float = Field(ge=0.0, le=1.0)
    feedback: str


class GapReport(BaseModel):
    topic: str
    overall_score: float = Field(ge=0.0, le=1.0)
    gaps: list[GapNode]
    strengths: list[str]
    summary: str


class GraphNode(BaseModel):
    id: str
    label: str
    score: float = Field(ge=0.0, le=1.0)
    understood: bool


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class KnowledgeGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class TutorMessage(BaseModel):
    session_id: str
    topic: str
    message: str


class TutorResponse(BaseModel):
    reply: str
    follow_up_question: Optional[str] = None
    nodes_improved: list[str] = []


class RAGRequest(BaseModel):
    session_id: str
    text: str


class UserPattern(BaseModel):
    session_id: str
    weak_topics: list[str] = []
    strong_topics: list[str] = []
    avg_score: float = 0.0
    preferred_explanation_style: str = "detailed"
    total_sessions: int = 0
    last_seen: str = ""
    common_misconceptions: list[str] = []
