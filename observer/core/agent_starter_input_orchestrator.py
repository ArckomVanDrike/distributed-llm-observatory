from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterIntake,
    AgentStarterRequirement,
    ConstraintStrength,
    EvidenceSource,
)

_HARD_LOCAL_ONLY_REQUIREMENT_KEYS = (
    "source_code_must_stay_local",
    "knowledge_data_must_stay_local",
    "raw_audio_must_stay_local",
    "transcript_must_stay_local",
)


def _declared_true_evidence(
    intake: AgentStarterIntake,
    *,
    key: str,
) -> list[AgentStarterEvidence]:
    return [
        evidence
        for evidence in intake.evidence
        if (
            evidence.key == key
            and evidence.source is EvidenceSource.DECLARED
            and evidence.value is True
        )
    ]


def derive_agent_starter_requirements(
    intake: AgentStarterIntake,
) -> list[AgentStarterRequirement]:
    requirements: list[AgentStarterRequirement] = []

    for key in _HARD_LOCAL_ONLY_REQUIREMENT_KEYS:
        supporting_evidence = _declared_true_evidence(
            intake,
            key=key,
        )

        if not supporting_evidence:
            continue

        requirements.append(
            AgentStarterRequirement(
                key=key,
                value=True,
                strength=ConstraintStrength.HARD,
                evidence=supporting_evidence,
            )
        )

    return requirements
