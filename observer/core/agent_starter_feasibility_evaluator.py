from __future__ import annotations

from observer.core.agent_starter_feasibility import (
    technical_feasibility_from_compatibility,
)
from observer.core.agent_starter_technical_requirement_orchestrator import (
    build_agent_starter_technical_requirement_assessments,
)
from schemas.agent_starter import (
    AgentStarterCandidateArchitecture,
    AgentStarterEvidence,
    AgentStarterPreparedInput,
    AgentStarterTechnicalFeasibilityAssessment,
    AgentStarterTechnicalRequirementAssessment,
    EvidenceSource,
    TechnicalFeasibility,
    TechnicalRequirementStatus,
)
from schemas.compatibility import CompatibilityAssessment


def evaluate_agent_starter_technical_feasibility(
    *,
    prepared: AgentStarterPreparedInput,
    candidate: AgentStarterCandidateArchitecture,
    compatibility_assessment: CompatibilityAssessment | None = None,
    technical_requirements: (
        list[AgentStarterTechnicalRequirementAssessment] | None
    ) = None,
) -> AgentStarterTechnicalFeasibilityAssessment:
    if candidate.goal is not prepared.goal:
        raise ValueError(
            "Candidate goal must match prepared input goal."
        )

    if technical_requirements is None:
        requirement_assessments = (
            build_agent_starter_technical_requirement_assessments(
                prepared=prepared,
                candidate=candidate,
            )
        )
    else:
        requirement_assessments = technical_requirements

    unsatisfied_requirements = [
        requirement
        for requirement in requirement_assessments
        if requirement.status is TechnicalRequirementStatus.UNSATISFIED
    ]

    if unsatisfied_requirements:
        return AgentStarterTechnicalFeasibilityAssessment(
            architecture_id=candidate.architecture_id,
            goal=candidate.goal,
            technical_feasibility=TechnicalFeasibility.NOT_FEASIBLE,
            reasons=[
                reason
                for requirement in unsatisfied_requirements
                for reason in requirement.reasons
            ],
            supporting_evidence=[
                evidence
                for requirement in unsatisfied_requirements
                for evidence in requirement.supporting_evidence
            ],
        )

    unknown_requirements = [
        requirement
        for requirement in requirement_assessments
        if requirement.status is TechnicalRequirementStatus.UNKNOWN
    ]

    if unknown_requirements:
        return AgentStarterTechnicalFeasibilityAssessment(
            architecture_id=candidate.architecture_id,
            goal=candidate.goal,
            technical_feasibility=TechnicalFeasibility.UNKNOWN,
            reasons=[
                reason
                for requirement in unknown_requirements
                for reason in requirement.reasons
            ],
            supporting_evidence=[
                evidence
                for requirement in unknown_requirements
                for evidence in requirement.supporting_evidence
            ],
        )

    satisfied_evidence = [
        evidence
        for requirement in requirement_assessments
        if requirement.status is TechnicalRequirementStatus.SATISFIED
        for evidence in requirement.supporting_evidence
    ]

    if compatibility_assessment is None:
        if requirement_assessments:
            return AgentStarterTechnicalFeasibilityAssessment(
                architecture_id=candidate.architecture_id,
                goal=candidate.goal,
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                reasons=[
                    (
                        "All candidate-specific technical "
                        "requirements are satisfied by the "
                        "available evidence."
                    ),
                ],
                supporting_evidence=satisfied_evidence,
            )

        return AgentStarterTechnicalFeasibilityAssessment(
            architecture_id=candidate.architecture_id,
            goal=candidate.goal,
            technical_feasibility=TechnicalFeasibility.UNKNOWN,
            reasons=[
                (
                    "Technical feasibility cannot be established "
                    "without candidate-specific technical requirements "
                    "or compatibility evidence."
                ),
            ],
            supporting_evidence=satisfied_evidence,
        )

    technical_feasibility = (
        technical_feasibility_from_compatibility(
            compatibility_assessment
        )
    )

    compatibility_evidence = AgentStarterEvidence(
        key="candidate_compatibility_verdict",
        source=EvidenceSource.DERIVED,
        value=compatibility_assessment.verdict.value,
        reason=compatibility_assessment.summary,
    )

    return AgentStarterTechnicalFeasibilityAssessment(
        architecture_id=candidate.architecture_id,
        goal=candidate.goal,
        technical_feasibility=technical_feasibility,
        reasons=[
            compatibility_assessment.summary,
            *compatibility_assessment.reasons,
        ],
        supporting_evidence=[
            *satisfied_evidence,
            compatibility_evidence,
        ],
    )
