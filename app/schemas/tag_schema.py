from typing import List, Optional, Literal
from pydantic import BaseModel

class JobMetadata(BaseModel):
    job_type: Optional[Literal['full_time', 'part_time', 'contract', 'internship', 'freelance']] = None
    location_type: Optional[Literal['remote', 'onsite', 'hybrid']] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None

class JobTags(BaseModel):
    role_family: List[str] = []
    skills: List[str] = []
    seniority: List[str] = []
    domain: List[str] = []

class JDExtractionResult(BaseModel):
    metadata: JobMetadata
    tags: JobTags
