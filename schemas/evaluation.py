from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


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



class TaskEvaluationMethod(str, Enum):
    DETERMINISTIC = "deterministic"
    HUMAN = "human"


class TaskCriterionEvaluation(BaseModel):
    criterion: str = Field(min_length=1)
    passed: bool
    evidence: str | None = None

    @field_validator("criterion")
    @classmethod
    def validate_criterion(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("criterion cannot be empty.")

        return value


class TaskEvaluation(BaseModel):
    schema_version: str = "0.1"

    task_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    method: TaskEvaluationMethod
    criteria: list[TaskCriterionEvaluation] = Field(
        min_length=1,
    )
    passed: bool

    @model_validator(mode="after")
    def validate_overall_result(self) -> TaskEvaluation:
        criteria_passed = all(
            criterion.passed
            for criterion in self.criteria
        )

        if self.passed != criteria_passed:
            raise ValueError(
                "Task evaluation overall result must match "
                "the criterion results."
            )

        return self
