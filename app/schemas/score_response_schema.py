from pydantic import BaseModel
from typing import List, Optional

from app.schemas.jd_questions_schema import JDQuestions
from app.schemas.rag_scoring import ResumeRagResult


class ScoreResponse(BaseModel):
    success: bool
    result: ResumeRagResult
    jd_text_length: int
    resume_text_length: int
    jd_token_estimate: int
    resume_token_estimate: int
    jd_text: str
    resume_text: str
    questions: JDQuestions
    message: str


class TokenEstimateResponse(BaseModel):
    jd_text_length: int
    resume_text_length: int
    jd_token_estimate: int
    resume_token_estimate: int


class TokenStrategyDetail(BaseModel):
    """Breakdown for a single estimation strategy."""
    name: str                    # "RAG (Chunks)" or "Full Resume"
    total_tokens: int            # Total tokens for all combos under this strategy
    tokens_per_question: int     # Avg tokens per single LLM call
    context_tokens: int          # Context tokens sent per question
    context_type: str            # "Top-3 Chunks (~2100 chars)" or "Full Resume Text"


class BatchTokenEstimateResponse(BaseModel):
    # Counts
    resume_count: int
    jd_count: int
    total_combinations: int
    total_questions: int         # Total questions across all JDs

    # Active strategy (the one the user selected)
    rag_strategy: TokenStrategyDetail
    full_resume_strategy: TokenStrategyDetail

    # Comparison
    savings_tokens: int          # full_resume - rag
    savings_percentage: float    # (savings / full_resume) * 100

    # Warnings for edge cases
    warnings: List[str] = []
