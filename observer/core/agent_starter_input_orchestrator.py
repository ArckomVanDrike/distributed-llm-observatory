from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterIntake,
    AgentStarterRequirement,
    ConstraintStrength,
    EvidenceSource,
)


def derive_agent_starter_requirements(
    intake: AgentStarterIntake,
) -> list[AgentStarterRequirement]:
    requirements: list[AgentStarterRequirement] = []

    local_code_evidence = [
        evidence
        for evidence in intake.evidence
        if (
            evidence.key == "source_code_must_stay_local"
            and evidence.source is EvidenceSource.DECLARED
            and evidence.value is True
        )
    ]

    if local_code_evidence:
        requirements.append(
            AgentStarterRequirement(
                key="source_code_must_stay_local",
                value=True,
                strength=ConstraintStrength.HARD,
                evidence=local_code_evidence,
            )
        )

    return requirements
