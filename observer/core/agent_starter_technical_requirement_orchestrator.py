from __future__ import annotations

from observer.core.agent_starter_technical_requirement_matcher import (
    assess_agent_starter_technical_requirement,
)
from schemas.agent_starter import (
    AgentStarterCandidateArchitecture,
    AgentStarterPreparedInput,
    AgentStarterTechnicalRequirementAssessment,
    ConstraintStrength,
)

_CANDIDATE_EVIDENCE_KEY_BY_REQUIREMENT = {
    "filesystem_write": "candidate_supports_filesystem_write",
}


def build_agent_starter_technical_requirement_assessments(
    *,
    prepared: AgentStarterPreparedInput,
    candidate: AgentStarterCandidateArchitecture,
) -> list[AgentStarterTechnicalRequirementAssessment]:
    assessments: list[
        AgentStarterTechnicalRequirementAssessment
    ] = []

    for requirement in prepared.requirements:
        if requirement.strength is not ConstraintStrength.HARD:
            continue

        if requirement.value is not True:
            continue

        candidate_evidence_key = (
            _CANDIDATE_EVIDENCE_KEY_BY_REQUIREMENT.get(
                requirement.key
            )
        )
        if candidate_evidence_key is None:
            continue

        required_capability = next(
            (
                evidence
                for evidence in requirement.evidence
                if evidence.key == requirement.key
            ),
            None,
        )
        if required_capability is None:
            continue

        assessments.append(
            assess_agent_starter_technical_requirement(
                required_capability=required_capability,
                candidate_evidence=candidate.evidence,
                candidate_evidence_key=candidate_evidence_key,
            )
        )

    return assessments
