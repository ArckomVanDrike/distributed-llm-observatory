from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class QualityEvaluation(BaseModel):
    fit: int = Field(ge=1, le=6)
    efficiency: int = Field(ge=1, le=6)
    clarity: int = Field(ge=1, le=6)
    style: int = Field(ge=1, le=6)
    structure: int = Field(ge=1, le=6)
    technical_accuracy: int = Field(ge=1, le=6)
    overall: int = Field(ge=1, le=6)

    judge_model: str = Field(min_length=1)
    judge_version: str = Field(min_length=1)
    judge_agreement: float | None = Field(default=None, ge=0, le=1)
    human_verified: bool = False

    @model_validator(mode="after")
    def validate_overall_constraints(self) -> QualityEvaluation:
        dimensions = [
            self.fit,
            self.efficiency,
            self.clarity,
            self.style,
            self.structure,
            self.technical_accuracy,
        ]

        minimum = min(dimensions)

        if minimum == 1 and self.overall > 2:
            raise ValueError(
                "Overall must be <= 2 when any quality dimension is 1."
            )

        if minimum == 2 and self.overall > 3:
            raise ValueError(
                "Overall must be <= 3 when any quality dimension is 2."
            )

        if all(score >= 4 for score in dimensions) and self.overall < 4:
            raise ValueError(
                "Overall must be >= 4 when all quality dimensions are >= 4."
            )

        return self
