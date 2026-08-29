from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterPreparedInput,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
    ConstraintStrength,
    EvidenceSource,
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



class AgentStarterFinalReport(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    context: AgentStarterFinalReportContext

    candidate_explanations: list[
        AgentStarterCandidateExplanation
    ] = Field(default_factory=list)

    observed_evidence: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )
    declared_evidence: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )
    derived_evidence: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )
    unknown_evidence: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )

    hard_constraints: list[AgentStarterRequirement] = Field(
        default_factory=list,
    )
    soft_preferences: list[AgentStarterRequirement] = Field(
        default_factory=list,
    )

    requested_capabilities: list[AgentStarterEvidence] = Field(
        default_factory=list,
    )

    recommended_architecture_ids: list[str] = Field(
        default_factory=list,
    )
    recommended_stacks: list[AgentStarterConcreteStack] = Field(
        default_factory=list,
    )

    alternative_architecture_ids: list[str] = Field(
        default_factory=list,
    )
    alternative_stacks: list[AgentStarterConcreteStack] = Field(
        default_factory=list,
    )

    possible_but_not_recommended_architecture_ids: list[str] = Field(
        default_factory=list,
    )
    not_recommended_architecture_ids: list[str] = Field(
        default_factory=list,
    )

    blockers: list[AgentStarterRequirement] = Field(
        default_factory=list,
    )
    upgrade_paths: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_evidence_projection(
        self,
    ) -> AgentStarterFinalReport:
        prepared_evidence = list(self.context.prepared.evidence)

        expected_observed = [
            evidence
            for evidence in prepared_evidence
            if evidence.source is EvidenceSource.OBSERVED
        ]
        expected_declared = [
            evidence
            for evidence in prepared_evidence
            if evidence.source is EvidenceSource.DECLARED
        ]
        expected_derived = [
            evidence
            for evidence in prepared_evidence
            if evidence.source is EvidenceSource.DERIVED
        ]
        expected_unknown = [
            evidence
            for evidence in prepared_evidence
            if evidence.source is EvidenceSource.UNKNOWN
        ]

        if (
            self.observed_evidence != expected_observed
            or self.declared_evidence != expected_declared
            or self.derived_evidence != expected_derived
            or self.unknown_evidence != expected_unknown
        ):
            raise ValueError(
                "Final report evidence projection must match "
                "the prepared input exactly by provenance."
            )

        return self

    @model_validator(mode="after")
    def validate_requirement_projection(
        self,
    ) -> AgentStarterFinalReport:
        requirements = list(self.context.prepared.requirements)

        expected_hard = [
            requirement
            for requirement in requirements
            if requirement.strength is ConstraintStrength.HARD
        ]
        expected_soft = [
            requirement
            for requirement in requirements
            if requirement.strength is ConstraintStrength.SOFT
        ]

        if (
            self.hard_constraints != expected_hard
            or self.soft_preferences != expected_soft
        ):
            raise ValueError(
                "Final report requirement projection must match "
                "the prepared input exactly by constraint strength."
            )

        return self

    @model_validator(mode="after")
    def validate_candidate_explanations(
        self,
    ) -> AgentStarterFinalReport:
        assessments = list(
            self.context
            .classification
            .resolution
            .catalog_result
            .plan
            .candidate_assessments
        )
        stacks = list(
            self.context
            .classification
            .resolution
            .stacks
        )

        if len(self.candidate_explanations) != len(assessments):
            raise ValueError(
                "Final report must contain exactly one candidate "
                "explanation for every assessed architecture."
            )

        for explanation, assessment, stack in zip(
            self.candidate_explanations,
            assessments,
            stacks,
            strict=True,
        ):
            if (
                explanation.assessment != assessment
                or explanation.concrete_stack != stack
            ):
                raise ValueError(
                    "Final report candidate explanation must "
                    "correspond exactly to the assessed architecture "
                    "and concrete stack in plan order."
                )

        return self

    @model_validator(mode="after")
    def validate_requested_capability_provenance(
        self,
    ) -> AgentStarterFinalReport:
        for capability in self.requested_capabilities:
            if (
                capability not in self.context.prepared.evidence
                or capability.source is not EvidenceSource.DERIVED
                or capability.value is not True
            ):
                raise ValueError(
                    "Final report requested capabilities must be "
                    "derived true evidence recorded in prepared input."
                )

        return self

    @model_validator(mode="after")
    def validate_recommendation_surface(
        self,
    ) -> AgentStarterFinalReport:
        classification = self.context.classification

        if (
            self.recommended_architecture_ids
            != classification.recommended_architecture_ids
            or self.alternative_architecture_ids
            != classification.possible_architecture_ids
            or (
                self.possible_but_not_recommended_architecture_ids
                != classification
                .possible_but_not_recommended_architecture_ids
            )
            or (
                self.not_recommended_architecture_ids
                != classification.not_recommended_architecture_ids
            )
        ):
            raise ValueError(
                "Final report recommendation groups must be "
                "an exact projection of concrete stack classification."
            )

        stacks_by_id = {
            stack.architecture_id: stack
            for stack in classification.resolution.stacks
        }

        expected_recommended_stacks = [
            stacks_by_id[architecture_id]
            for architecture_id
            in classification.recommended_architecture_ids
        ]
        expected_alternative_stacks = [
            stacks_by_id[architecture_id]
            for architecture_id
            in classification.possible_architecture_ids
        ]

        if self.recommended_stacks != expected_recommended_stacks:
            raise ValueError(
                "Final report recommended stacks must be "
                "an exact projection of recommended architectures."
            )

        if self.alternative_stacks != expected_alternative_stacks:
            raise ValueError(
                "Final report alternative stacks must be "
                "an exact projection of possible architectures."
            )

        return self

    @model_validator(mode="after")
    def validate_blocker_projection(
        self,
    ) -> AgentStarterFinalReport:
        expected_blockers: list[AgentStarterRequirement] = []

        for assessment in (
            self.context
            .classification
            .resolution
            .catalog_result
            .plan
            .candidate_assessments
        ):
            for requirement in assessment.blocking_requirements:
                if requirement not in expected_blockers:
                    expected_blockers.append(requirement)

        if self.blockers != expected_blockers:
            raise ValueError(
                "Final report blockers must be an exact projection "
                "of candidate blocking requirements."
            )

        return self

    @model_validator(mode="after")
    def validate_upgrade_paths(
        self,
    ) -> AgentStarterFinalReport:
        if self.upgrade_paths:
            raise ValueError(
                "Final report upgrade paths cannot be populated "
                "until an explicit upgrade path source exists."
            )

        return self
