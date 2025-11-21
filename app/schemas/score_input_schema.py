from pydantic import BaseModel


class NormalizedScoreInput(BaseModel):
    jd: str
    resume: str