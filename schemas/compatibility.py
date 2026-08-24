from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class AssessmentBasis(str, Enum):
    ESTIMATED = "estimated"
    MEASURED = "measured"


class CompatibilityVerdict(str, Enum):
    COMPATIBLE = "compatible"
    CONSTRAINED = "constrained"
    NOT_RECOMMENDED = "not_recommended"
    UNKNOWN = "unknown"


class CompatibilityAssessment(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    basis: AssessmentBasis
    verdict: CompatibilityVerdict

    summary: str = Field(min_length=1)
    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    estimated_required_memory_bytes: int | None = Field(
        default=None,
        gt=0,
    )
    measured_peak_memory_bytes: int | None = Field(
        default=None,
        gt=0,
    )

    reasons: list[str] = Field(
        default_factory=list,
    )
    recommendations: list[str] = Field(
        default_factory=list,
    )
