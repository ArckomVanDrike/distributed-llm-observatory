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
    if prepared.goal is AgentStarterGoal.CODING:
        return _generate_coding_candidates()

    if prepared.goal is AgentStarterGoal.KNOWLEDGE_RAG:
        return _generate_rag_candidates()

    if prepared.goal is AgentStarterGoal.VOICE:
        return _generate_voice_candidates()

    return []


def _generate_coding_candidates(
) -> list[AgentStarterCandidateArchitecture]:
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


def _generate_rag_candidates(
) -> list[AgentStarterCandidateArchitecture]:
    direct_context_evidence = AgentStarterEvidence(
        key="candidate_uses_retrieval",
        source=EvidenceSource.DERIVED,
        value=False,
        reason=(
            "The direct-context architecture supplies knowledge "
            "without a retrieval stage."
        ),
    )

    full_rag_evidence = AgentStarterEvidence(
        key="candidate_uses_retrieval",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The full RAG architecture retrieves relevant knowledge "
            "before generation."
        ),
    )

    return [
        AgentStarterCandidateArchitecture(
            architecture_id="direct-context-knowledge-assistant",
            goal=AgentStarterGoal.KNOWLEDGE_RAG,
            evidence=[direct_context_evidence],
        ),
        AgentStarterCandidateArchitecture(
            architecture_id="full-rag-pipeline",
            goal=AgentStarterGoal.KNOWLEDGE_RAG,
            evidence=[full_rag_evidence],
        ),
    ]


def _generate_voice_candidates(
) -> list[AgentStarterCandidateArchitecture]:
    local_evidence = [
        AgentStarterEvidence(
            key="candidate_raw_audio_remote_processing",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The local voice architecture keeps raw audio "
                "inside the user-controlled environment."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_transcript_remote_processing",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The local voice architecture keeps transcripts "
                "inside the user-controlled environment."
            ),
        ),
    ]

    hybrid_evidence = [
        AgentStarterEvidence(
            key="candidate_raw_audio_remote_processing",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The hybrid voice architecture processes raw audio "
                "inside the user-controlled environment."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_transcript_remote_processing",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The hybrid voice architecture permits transcript "
                "processing outside the user-controlled environment."
            ),
        ),
    ]

    cloud_evidence = [
        AgentStarterEvidence(
            key="candidate_raw_audio_remote_processing",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The cloud voice architecture permits raw audio "
                "processing outside the user-controlled environment."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_transcript_remote_processing",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The cloud voice architecture permits transcript "
                "processing outside the user-controlled environment."
            ),
        ),
    ]

    return [
        AgentStarterCandidateArchitecture(
            architecture_id="local-voice-pipeline",
            goal=AgentStarterGoal.VOICE,
            evidence=local_evidence,
        ),
        AgentStarterCandidateArchitecture(
            architecture_id="hybrid-voice-pipeline",
            goal=AgentStarterGoal.VOICE,
            evidence=hybrid_evidence,
        ),
        AgentStarterCandidateArchitecture(
            architecture_id="cloud-voice-pipeline",
            goal=AgentStarterGoal.VOICE,
            evidence=cloud_evidence,
        ),
    ]
