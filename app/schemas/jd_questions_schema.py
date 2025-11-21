from pydantic import BaseModel
from typing import List, Dict


class Question(BaseModel):
    question: str


class JDQuestions(BaseModel):
    education: List[Question]
    experience: List[Question]
    technical_skills: List[Question]
    soft_skills: List[Question]
