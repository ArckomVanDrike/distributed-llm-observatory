from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterCandidateArchitecture,
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterPreparedInput,
    EvidenceSource,
)


def generate_agent_starter_candidates(
    prepared: AgentStarterPreparedInput,
) -> list[AgentStarterCandidateArchitecture]:
    if prepared.goal is not AgentStarterGoal.CODING:
        return []

    local_evidence = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.DERIVED,
        value=False,
        reason=(
            "The local coding architecture processes source code "
            "inside the user-controlled environment."
        ),
    )

    remote_evidence = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The remote coding architecture processes source code "
            "outside the user-controlled environment."
        ),
    )

    return [
        AgentStarterCandidateArchitecture(
            architecture_id="local-coding-agent",
            goal=AgentStarterGoal.CODING,
            evidence=[local_evidence],
        ),
        AgentStarterCandidateArchitecture(
            architecture_id="remote-coding-agent",
            goal=AgentStarterGoal.CODING,
            evidence=[remote_evidence],
        ),
    ]
