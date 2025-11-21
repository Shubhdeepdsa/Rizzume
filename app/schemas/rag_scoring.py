
from pydantic import BaseModel
from typing import List


class RetrievedChunk(BaseModel):
    chunk_id: int
    start: int
    end: int
    similarity: float
    text: str


class ScoredQuestion(BaseModel):
    category: str               # "education" | "experience" | "technical_skills" | "soft_skills"
    question: str
    answer: str
    score: float                # 0–10
    reasoning: str
    evidence_chars: int         # total characters of evidence used
    retrieved_chunks: List[RetrievedChunk]


class ResumeRagResult(BaseModel):
    questions: List[ScoredQuestion]
    average_score: float
