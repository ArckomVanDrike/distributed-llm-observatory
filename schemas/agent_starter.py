from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class AgentStarterGoal(str, Enum):
    PERSONAL = "personal"
    KNOWLEDGE_RAG = "knowledge_rag"
    CODING = "coding"
    AUTOMATION = "automation"
    VOICE = "voice"


class EvidenceSource(str, Enum):
    OBSERVED = "observed"
    DECLARED = "declared"
    DERIVED = "derived"
    UNKNOWN = "unknown"


class ConstraintStrength(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class TechnicalFeasibility(str, Enum):
    FEASIBLE = "feasible"
    LIMITED = "limited"
    NOT_FEASIBLE = "not_feasible"
    UNKNOWN = "unknown"


class RecommendationVerdict(str, Enum):
    RECOMMENDED = "recommended"
    POSSIBLE = "possible"
    POSSIBLE_BUT_NOT_RECOMMENDED = (
        "possible_but_not_recommended"
    )
    NOT_RECOMMENDED = "not_recommended"


class RecommendationConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LIMITED = "limited"


class AgentStarterEvidence(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    key: str = Field(min_length=1)
    source: EvidenceSource
    value: Any | None = None
    reason: str | None = Field(
        default=None,
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_evidence(
        self,
    ) -> AgentStarterEvidence:
        if self.source is EvidenceSource.UNKNOWN:
            if self.value is not None:
                raise ValueError(
                    "Unknown evidence cannot record a value."
                )

            if self.reason is None:
                raise ValueError(
                    "Unknown evidence must explain what is unknown."
                )

            return self

        if self.value is None:
            raise ValueError(
                "Known evidence must record a value."
            )

        if (
            self.source is EvidenceSource.DERIVED
            and self.reason is None
        ):
            raise ValueError(
                "Derived evidence must record its reason."
            )

        return self


class AgentStarterRequirement(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    key: str = Field(min_length=1)
    value: Any | None
    strength: ConstraintStrength
    evidence: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_requirement(
        self,
    ) -> AgentStarterRequirement:
        if self.value is None:
            raise ValueError(
                "Requirement must record a value."
            )

        if not self.evidence:
            raise ValueError(
                "Requirement must record supporting evidence."
            )

        if all(
            item.source is EvidenceSource.UNKNOWN
            for item in self.evidence
        ):
            raise ValueError(
                "Requirement cannot be supported only "
                "by unknown evidence."
            )

        return self
