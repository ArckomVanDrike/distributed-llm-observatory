from __future__ import annotations

from observer.core.agent_starter_technical_requirement_matcher import (
    assess_agent_starter_technical_requirement,
)
from schemas.agent_starter import (
    AgentStarterCandidateArchitecture,
    AgentStarterPreparedInput,
    AgentStarterTechnicalRequirementAssessment,
    EvidenceSource,
)

_CANDIDATE_EVIDENCE_KEY_BY_REQUIREMENT = {
    "filesystem_read": "candidate_supports_filesystem_read",
    "filesystem_write": "candidate_supports_filesystem_write",
    "ocr_required": "candidate_supports_ocr",
    "shell_execution": "candidate_supports_shell_execution",
    "test_execution": "candidate_supports_test_execution",
}


def build_agent_starter_technical_requirement_assessments(
    *,
    prepared: AgentStarterPreparedInput,
    candidate: AgentStarterCandidateArchitecture,
) -> list[AgentStarterTechnicalRequirementAssessment]:
    assessments: list[
        AgentStarterTechnicalRequirementAssessment
    ] = []

    for evidence in prepared.evidence:
        if evidence.source is not EvidenceSource.DERIVED:
            continue

        if evidence.value is not True:
            continue

        candidate_evidence_key = (
            _CANDIDATE_EVIDENCE_KEY_BY_REQUIREMENT.get(
                evidence.key
            )
        )
        if candidate_evidence_key is None:
            continue

        assessments.append(
            assess_agent_starter_technical_requirement(
                required_capability=evidence,
                candidate_evidence=candidate.evidence,
                candidate_evidence_key=candidate_evidence_key,
            )
        )

    return assessments
