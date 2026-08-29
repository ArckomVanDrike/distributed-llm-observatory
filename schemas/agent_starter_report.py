from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from schemas.agent_starter import (
    AgentStarterPreparedInput,
    CandidateArchitectureAssessment,
    RecommendationVerdict,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogSnapshot,
)
from schemas.agent_starter_result import (
    AgentStarterConcreteStackClassification,
)
from schemas.agent_starter_stack import (
    AgentStarterConcreteStack,
)


class AgentStarterCandidateExplanation(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    assessment: CandidateArchitectureAssessment
    concrete_stack: AgentStarterConcreteStack

    why: list[str] = Field(default_factory=list)
    why_not: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_architecture_correspondence(
        self,
    ) -> AgentStarterCandidateExplanation:
        if (
            self.assessment.architecture_id
            != self.concrete_stack.architecture_id
        ):
            raise ValueError(
                "Candidate explanation architecture must match "
                "the concrete stack architecture."
            )

        return self

    @model_validator(mode="after")
    def validate_reason_projection(
        self,
    ) -> AgentStarterCandidateExplanation:
        recommendation_reasons = list(
            self.assessment.recommendation_reasons
        )

        if self.assessment.recommendation in {
            RecommendationVerdict.RECOMMENDED,
            RecommendationVerdict.POSSIBLE,
        }:
            expected_why = recommendation_reasons
            expected_why_not: list[str] = []
        else:
            expected_why = []
            expected_why_not = recommendation_reasons

        if (
            self.why != expected_why
            or self.why_not != expected_why_not
        ):
            raise ValueError(
                "Why / why-not content must be an exact projection "
                "of the candidate recommendation reasons."
            )

        return self


class AgentStarterFinalReportContext(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    prepared: AgentStarterPreparedInput
    classification: AgentStarterConcreteStackClassification
    catalog_snapshot: AgentStarterCatalogSnapshot

    @model_validator(mode="after")
    def validate_goal_provenance(
        self,
    ) -> AgentStarterFinalReportContext:
        plan_goal = (
            self.classification
            .resolution
            .catalog_result
            .plan
            .goal
        )

        if self.prepared.goal is not plan_goal:
            raise ValueError(
                "Final report context goal must match "
                "the evaluated plan goal."
            )

        return self

    @model_validator(mode="after")
    def validate_catalog_snapshot_provenance(
        self,
    ) -> AgentStarterFinalReportContext:
        expected_snapshot_id = (
            self.classification
            .resolution
            .catalog_result
            .catalog_snapshot_id
        )

        if (
            self.catalog_snapshot.snapshot_id
            != expected_snapshot_id
        ):
            raise ValueError(
                "Final report context catalog snapshot must match "
                "the concrete stack classification snapshot."
            )

        return self
