from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterTechnicalRequirementAssessment,
    EvidenceSource,
    TechnicalRequirementStatus,
)


def assess_agent_starter_technical_requirement(
    *,
    required_capability: AgentStarterEvidence,
    candidate_evidence: list[AgentStarterEvidence],
    candidate_evidence_key: str,
) -> AgentStarterTechnicalRequirementAssessment:
    matching_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == candidate_evidence_key
    ]

    if not matching_evidence:
        return AgentStarterTechnicalRequirementAssessment(
            key=required_capability.key,
            status=TechnicalRequirementStatus.UNKNOWN,
            reasons=[
                (
                    "Candidate capability evidence is unavailable "
                    f"for {required_capability.key}."
                ),
            ],
        )

    evidence = matching_evidence[0]

    if evidence.source is EvidenceSource.UNKNOWN:
        return AgentStarterTechnicalRequirementAssessment(
            key=required_capability.key,
            status=TechnicalRequirementStatus.UNKNOWN,
            reasons=[
                evidence.reason
                or (
                    "Candidate capability support has not been "
                    "established."
                ),
            ],
            supporting_evidence=[evidence],
        )

    if evidence.value is True:
        return AgentStarterTechnicalRequirementAssessment(
            key=required_capability.key,
            status=TechnicalRequirementStatus.SATISFIED,
            reasons=[
                evidence.reason
                or (
                    "Candidate capability evidence confirms "
                    "the required capability."
                ),
            ],
            supporting_evidence=[evidence],
        )

    if evidence.value is False:
        return AgentStarterTechnicalRequirementAssessment(
            key=required_capability.key,
            status=TechnicalRequirementStatus.UNSATISFIED,
            reasons=[
                evidence.reason
                or (
                    "Candidate capability evidence confirms "
                    "the required capability is unavailable."
                ),
            ],
            supporting_evidence=[evidence],
        )

    return AgentStarterTechnicalRequirementAssessment(
        key=required_capability.key,
        status=TechnicalRequirementStatus.UNKNOWN,
        reasons=[
            (
                "Candidate capability evidence does not establish "
                "a boolean support state."
            ),
        ],
        supporting_evidence=[evidence],
    )
