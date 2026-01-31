from pydantic import BaseModel
from typing import List


class NormalizedScoreInput(BaseModel):
    jd: str
    resume: str


class BatchScoreRequest(BaseModel):
    resume_ids: List[str]
    jd_ids: List[str]


class EstimateRequest(BaseModel):
    resume_id: str
    jd_id: str


class BatchEstimateRequest(BaseModel):
    resume_ids: List[str]
    jd_ids: List[str]