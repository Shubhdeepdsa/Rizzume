
from pydantic import BaseModel
from typing import List, Optional


class RetrievedChunk(BaseModel):
    chunk_id: int
    start: int
    end: int
    similarity: float
    text: str


class ScoredQuestion(BaseModel):
    category: str               # "education" | "experience" | "technical_skills" | "soft_skills"
    question: str
    is_mandatory: bool          # Whether this is a dealbreaker requirement
    answer: str
    score: float                # 0–10
    reasoning: str
    evidence_chars: int         # total characters of evidence used
    retrieved_chunks: List[RetrievedChunk]


class ActionPlan(BaseModel):
    critical_actions: List[str]
    improvement_suggestions: List[str]


class ResumeRagResult(BaseModel):
    questions: List[ScoredQuestion]
    average_score: float
    action_plan: Optional[ActionPlan] = None

