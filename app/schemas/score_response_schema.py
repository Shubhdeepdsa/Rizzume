from pydantic import BaseModel

from app.schemas.jd_questions_schema import JDQuestions
from app.schemas.rag_scoring import ResumeRagResult


class ScoreResponse(BaseModel):
    success: bool
    result: ResumeRagResult
    jd_text_length: int
    resume_text_length: int
    questions: JDQuestions
    message: str

