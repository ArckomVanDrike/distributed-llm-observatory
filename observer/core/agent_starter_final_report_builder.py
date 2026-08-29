from __future__ import annotations

from observer.core.agent_starter_candidate_explanation_orchestrator import (
    build_agent_starter_candidate_explanations,
)
from observer.core.agent_starter_technical_requirement_orchestrator import (
    extract_agent_starter_requested_capabilities,
)
from schemas.agent_starter import (
    AgentStarterRequirement,
    ConstraintStrength,
    EvidenceSource,
)
from schemas.agent_starter_report import (
    AgentStarterFinalReport,
    AgentStarterFinalReportContext,
)


def build_agent_starter_final_report(
    context: AgentStarterFinalReportContext,
) -> AgentStarterFinalReport:
    prepared_evidence = list(context.prepared.evidence)
    requirements = list(context.prepared.requirements)

    classification = context.classification

    stacks_by_id = {
        stack.architecture_id: stack
        for stack in classification.resolution.stacks
    }

    recommended_stacks = [
        stacks_by_id[architecture_id]
        for architecture_id
        in classification.recommended_architecture_ids
    ]

    alternative_stacks = [
        stacks_by_id[architecture_id]
        for architecture_id
        in classification.possible_architecture_ids
    ]

    blockers: list[AgentStarterRequirement] = []

    for assessment in (
        context
        .classification
        .resolution
        .catalog_result
        .plan
        .candidate_assessments
    ):
        for requirement in assessment.blocking_requirements:
            if requirement not in blockers:
                blockers.append(requirement)

    return AgentStarterFinalReport(
        context=context,
        candidate_explanations=(
            build_agent_starter_candidate_explanations(
                context.classification
            )
        ),
        observed_evidence=[
            evidence
            for evidence in prepared_evidence
            if evidence.source is EvidenceSource.OBSERVED
        ],
        declared_evidence=[
            evidence
            for evidence in prepared_evidence
            if evidence.source is EvidenceSource.DECLARED
        ],
        derived_evidence=[
            evidence
            for evidence in prepared_evidence
            if evidence.source is EvidenceSource.DERIVED
        ],
        unknown_evidence=[
            evidence
            for evidence in prepared_evidence
            if evidence.source is EvidenceSource.UNKNOWN
        ],
        hard_constraints=[
            requirement
            for requirement in requirements
            if requirement.strength is ConstraintStrength.HARD
        ],
        soft_preferences=[
            requirement
            for requirement in requirements
            if requirement.strength is ConstraintStrength.SOFT
        ],
        requested_capabilities=(
            extract_agent_starter_requested_capabilities(
                context.prepared
            )
        ),
        recommended_architecture_ids=list(
            classification.recommended_architecture_ids
        ),
        recommended_stacks=recommended_stacks,
        alternative_architecture_ids=list(
            classification.possible_architecture_ids
        ),
        alternative_stacks=alternative_stacks,
        possible_but_not_recommended_architecture_ids=list(
            classification
            .possible_but_not_recommended_architecture_ids
        ),
        not_recommended_architecture_ids=list(
            classification.not_recommended_architecture_ids
        ),
        blockers=blockers,
        upgrade_paths=[],
    )
