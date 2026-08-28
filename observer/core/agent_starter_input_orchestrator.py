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


def derive_agent_starter_capability_evidence(
    intake: AgentStarterIntake,
) -> list[AgentStarterEvidence]:
    derived: list[AgentStarterEvidence] = []

    modify_files = bool(
        _declared_true_evidence(
            intake,
            key="modify_files",
        )
    )
    run_tests = bool(
        _declared_true_evidence(
            intake,
            key="run_tests",
        )
    )

    if modify_files:
        reason = (
            "Modifying files requires repository filesystem "
            "read and write access."
        )

        derived.extend(
            [
                AgentStarterEvidence(
                    key="filesystem_read",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=reason,
                ),
                AgentStarterEvidence(
                    key="filesystem_write",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=reason,
                ),
            ]
        )

    if run_tests:
        reason = (
            "Running tests requires shell execution and "
            "test execution capabilities."
        )

        derived.extend(
            [
                AgentStarterEvidence(
                    key="shell_execution",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=reason,
                ),
                AgentStarterEvidence(
                    key="test_execution",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=reason,
                ),
            ]
        )

    return derived
