from pydantic import BaseModel

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
