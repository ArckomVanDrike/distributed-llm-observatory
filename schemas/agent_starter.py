from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from schemas.hardware import HardwareProfile


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


class AgentStarterIntake(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    goal: AgentStarterGoal
    evidence: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )
    hardware_profile: HardwareProfile | None = None

    @model_validator(mode="after")
    def validate_intake(
        self,
    ) -> AgentStarterIntake:
        if any(
            evidence.source is EvidenceSource.DERIVED
            for evidence in self.evidence
        ):
            raise ValueError(
                "Derived evidence belongs to orchestration, "
                "not intake."
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


class AgentStarterPreparedInput(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    goal: AgentStarterGoal
    evidence: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )
    requirements: list[AgentStarterRequirement] = Field(
        default_factory=list,
    )
    hardware_profile: HardwareProfile | None = None


class AgentStarterCandidateArchitecture(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    architecture_id: str = Field(min_length=1)
    goal: AgentStarterGoal
    evidence: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )


class AgentStarterTechnicalFeasibilityAssessment(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    architecture_id: str = Field(min_length=1)
    goal: AgentStarterGoal
    technical_feasibility: TechnicalFeasibility
    reasons: list[str] = Field(default_factory=list)
    supporting_evidence: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_feasibility_assessment(
        self,
    ) -> AgentStarterTechnicalFeasibilityAssessment:
        if not self.reasons:
            raise ValueError(
                "Technical feasibility assessment must explain "
                "its verdict."
            )

        return self


class CandidateArchitectureAssessment(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    architecture_id: str = Field(min_length=1)
    technical_feasibility: TechnicalFeasibility
    recommendation: RecommendationVerdict
    confidence: RecommendationConfidence
    technical_reasons: list[str] = Field(
        default_factory=list,
    )
    recommendation_reasons: list[str] = Field(
        default_factory=list,
    )
    supporting_evidence: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )
    blocking_requirements: list[AgentStarterRequirement] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_assessment(
        self,
    ) -> CandidateArchitectureAssessment:
        if not self.technical_reasons:
            raise ValueError(
                "Candidate assessment must explain "
                "technical feasibility."
            )

        if not self.recommendation_reasons:
            raise ValueError(
                "Candidate assessment must explain "
                "its recommendation."
            )

        if not self.supporting_evidence:
            raise ValueError(
                "Candidate assessment must record "
                "supporting evidence."
            )

        if any(
            requirement.strength is not ConstraintStrength.HARD
            for requirement in self.blocking_requirements
        ):
            raise ValueError(
                "Blocking requirements must be hard constraints."
            )

        return self


class AgentStarterConstraintConflict(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    conflicting_requirements: list[AgentStarterRequirement] = Field(
        default_factory=list,
    )
    summary: str = Field(min_length=1)
    resolution_options: list[str] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_constraint_conflict(
        self,
    ) -> AgentStarterConstraintConflict:
        if not self.conflicting_requirements:
            raise ValueError(
                "Constraint conflict must identify a hard requirement."
            )

        if any(
            requirement.strength is not ConstraintStrength.HARD
            for requirement in self.conflicting_requirements
        ):
            raise ValueError(
                "Constraint conflict may contain only hard requirements."
            )

        if not self.resolution_options:
            raise ValueError(
                "Constraint conflict must expose a resolution option."
            )

        return self


class AgentStarterPlan(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    goal: AgentStarterGoal
    requirements: list[AgentStarterRequirement] = Field(
        default_factory=list,
    )
    candidate_assessments: list[
        CandidateArchitectureAssessment
    ] = Field(
        default_factory=list,
    )
    constraint_conflict: AgentStarterConstraintConflict | None = None

    @model_validator(mode="after")
    def validate_plan(
        self,
    ) -> AgentStarterPlan:
        if (
            not self.candidate_assessments
            and self.constraint_conflict is None
        ):
            raise ValueError(
                "Agent Starter plan must record candidate assessments "
                "or a constraint conflict."
            )

        if (
            self.constraint_conflict is not None
            and any(
                candidate.recommendation
                is RecommendationVerdict.RECOMMENDED
                for candidate in self.candidate_assessments
            )
        ):
            raise ValueError(
                "Constraint conflict cannot coexist with "
                "a recommended candidate."
            )

        return self
