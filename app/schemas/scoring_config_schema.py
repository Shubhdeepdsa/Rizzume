from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ScoringConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    education_weight: int = Field(default=25, ge=0, le=100)
    experience_weight: int = Field(default=25, ge=0, le=100)
    technical_weight: int = Field(default=25, ge=0, le=100)
    soft_skills_weight: int = Field(default=25, ge=0, le=100)
    mandatory_question_weight: float = Field(default=2.0, ge=0)
    optional_question_weight: float = Field(default=1.0, ge=0)
    mandatory_cap_weight: float = Field(default=0.5, ge=0, le=1)
    is_default: bool = False

    @model_validator(mode='after')
    def weights_must_sum_to_100(self):
        total = self.education_weight + self.experience_weight + self.technical_weight + self.soft_skills_weight
        if abs(total - 100.0) > 0.5:  # Tolerance for floating point, frontend sends integers
            raise ValueError(f'Category weights must sum to 100, got {total}')
        return self


class ScoringConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    education_weight: Optional[int] = Field(None, ge=0, le=100)
    experience_weight: Optional[int] = Field(None, ge=0, le=100)
    technical_weight: Optional[int] = Field(None, ge=0, le=100)
    soft_skills_weight: Optional[int] = Field(None, ge=0, le=100)
    mandatory_question_weight: Optional[float] = Field(None, ge=0)
    optional_question_weight: Optional[float] = Field(None, ge=0)
    mandatory_cap_weight: Optional[float] = Field(None, ge=0, le=1)
    is_default: Optional[bool] = None

    @model_validator(mode='after')
    def weights_must_sum_to_100_if_all_present(self):
        weights = [self.education_weight, self.experience_weight, self.technical_weight, self.soft_skills_weight]
        # Only validate sum when ALL four weights are provided
        if all(w is not None for w in weights):
            total = sum(weights)
            if abs(total - 100.0) > 0.5:
                raise ValueError(f'Category weights must sum to 100, got {total}')
        return self
