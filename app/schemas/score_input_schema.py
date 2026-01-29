from pydantic import BaseModel


class NormalizedScoreInput(BaseModel):
    jd: str
    resume: str

from typing import List

class BatchScoreRequest(BaseModel):
    resume_ids: List[str]
    jd_ids: List[str]

class EstimateRequest(BaseModel):
    resume_id: str
    jd_id: str