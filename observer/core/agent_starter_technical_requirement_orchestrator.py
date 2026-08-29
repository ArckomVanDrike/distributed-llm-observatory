from __future__ import annotations

from observer.core.agent_starter_technical_requirement_matcher import (
    assess_agent_starter_technical_requirement,
)
from schemas.agent_starter import (
    AgentStarterCandidateArchitecture,
    AgentStarterEvidence,
    AgentStarterPreparedInput,
    AgentStarterTechnicalRequirementAssessment,
    EvidenceSource,
)

_CANDIDATE_EVIDENCE_KEY_BY_REQUIREMENT = {
    "background_scheduling_required": (
        "candidate_supports_background_scheduling"
    ),
    "persistent_memory_required": (
        "candidate_supports_persistent_memory"
    ),
    "barge_in_turn_management_required": (
        "candidate_supports_barge_in_turn_management"
    ),
    "filesystem_read": "candidate_supports_filesystem_read",
    "filesystem_write": "candidate_supports_filesystem_write",
    "ocr_required": "candidate_supports_ocr",
    "shell_execution": "candidate_supports_shell_execution",
    "source_provenance_required": (
        "candidate_provides_source_provenance"
    ),
    "test_execution": "candidate_supports_test_execution",
}


def extract_agent_starter_requested_capabilities(
    prepared: AgentStarterPreparedInput,
) -> list[AgentStarterEvidence]:
    return [
        evidence
        for evidence in prepared.evidence
        if (
            evidence.source is EvidenceSource.DERIVED
            and evidence.value is True
            and evidence.key
            in _CANDIDATE_EVIDENCE_KEY_BY_REQUIREMENT
        )
    ]



def build_agent_starter_technical_requirement_assessments(
    *,
    prepared: AgentStarterPreparedInput,
    candidate: AgentStarterCandidateArchitecture,
) -> list[AgentStarterTechnicalRequirementAssessment]:
    assessments: list[
        AgentStarterTechnicalRequirementAssessment
    ] = []

    for evidence in extract_agent_starter_requested_capabilities(
        prepared
    ):
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
