from __future__ import annotations

from observer.core.agent_starter_candidate_explanation_orchestrator import (
    build_agent_starter_candidate_explanations,
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
        blockers=blockers,
        upgrade_paths=[],
    )
