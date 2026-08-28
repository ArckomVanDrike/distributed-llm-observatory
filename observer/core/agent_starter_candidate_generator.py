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

    if prepared.goal is AgentStarterGoal.AUTOMATION:
        return _generate_automation_candidates()

    if prepared.goal is AgentStarterGoal.PERSONAL:
        return _generate_personal_candidates()

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

    local_filesystem_read = AgentStarterEvidence(
        key="candidate_supports_filesystem_read",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The local coding-agent template includes filesystem "
            "read capability for repository access."
        ),
    )

    local_filesystem_write = AgentStarterEvidence(
        key="candidate_supports_filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The local coding-agent template includes filesystem "
            "write capability for code modification."
        ),
    )

    remote_filesystem_read = AgentStarterEvidence(
        key="candidate_supports_filesystem_read",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The remote coding-agent template includes filesystem "
            "read capability for repository access."
        ),
    )

    remote_filesystem_write = AgentStarterEvidence(
        key="candidate_supports_filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The remote coding-agent template includes filesystem "
            "write capability for code modification."
        ),
    )

    local_shell_execution = AgentStarterEvidence(
        key="candidate_supports_shell_execution",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The local coding-agent template includes shell "
            "execution capability."
        ),
    )

    remote_shell_execution = AgentStarterEvidence(
        key="candidate_supports_shell_execution",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The remote coding-agent template includes shell "
            "execution capability."
        ),
    )

    return [
        AgentStarterCandidateArchitecture(
            architecture_id="local-coding-agent",
            goal=AgentStarterGoal.CODING,
            evidence=[
                local_evidence,
                local_filesystem_read,
                local_filesystem_write,
                local_shell_execution,
            ],
        ),
        AgentStarterCandidateArchitecture(
            architecture_id="remote-coding-agent",
            goal=AgentStarterGoal.CODING,
            evidence=[
                remote_evidence,
                remote_filesystem_read,
                remote_filesystem_write,
                remote_shell_execution,
            ],
        ),
    ]


def _generate_rag_candidates(
) -> list[AgentStarterCandidateArchitecture]:
    direct_context_evidence = AgentStarterEvidence(
        key="candidate_uses_retrieval_pipeline",
        source=EvidenceSource.DERIVED,
        value=False,
        reason=(
            "The direct-context architecture supplies knowledge "
            "without a retrieval stage."
        ),
    )

    full_rag_evidence = AgentStarterEvidence(
        key="candidate_uses_retrieval_pipeline",
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



def _generate_automation_candidates(
) -> list[AgentStarterCandidateArchitecture]:
    traditional_evidence = [
        AgentStarterEvidence(
            key="candidate_uses_llm",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The traditional automation architecture executes "
                "the workflow without an LLM."
            ),
        ),
    ]

    supervised_evidence = [
        AgentStarterEvidence(
            key="candidate_uses_llm",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The supervised automation architecture uses an LLM "
                "for agent behavior."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_executes_autonomously",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The supervised automation architecture keeps "
                "execution under user supervision."
            ),
        ),
    ]

    autonomous_evidence = [
        AgentStarterEvidence(
            key="candidate_uses_llm",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The autonomous workflow architecture uses an LLM "
                "for agent behavior."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_executes_autonomously",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The autonomous workflow architecture can execute "
                "without per-action user supervision."
            ),
        ),
    ]

    return [
        AgentStarterCandidateArchitecture(
            architecture_id="traditional-deterministic-automation",
            goal=AgentStarterGoal.AUTOMATION,
            evidence=traditional_evidence,
        ),
        AgentStarterCandidateArchitecture(
            architecture_id="supervised-automation-agent",
            goal=AgentStarterGoal.AUTOMATION,
            evidence=supervised_evidence,
        ),
        AgentStarterCandidateArchitecture(
            architecture_id="autonomous-workflow-agent",
            goal=AgentStarterGoal.AUTOMATION,
            evidence=autonomous_evidence,
        ),
    ]



def _generate_personal_candidates(
) -> list[AgentStarterCandidateArchitecture]:
    session_only_evidence = [
        AgentStarterEvidence(
            key="candidate_supports_persistent_memory",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The session-only personal assistant does not retain "
                "memory across sessions."
            ),
        ),
    ]

    opaque_memory_evidence = [
        AgentStarterEvidence(
            key="candidate_supports_persistent_memory",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The persistent-memory architecture retains memory "
                "across sessions."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_supports_memory_inspect_edit_delete",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The opaque persistent-memory architecture does not "
                "provide explicit inspect, edit, and delete controls."
            ),
        ),
    ]

    controlled_memory_evidence = [
        AgentStarterEvidence(
            key="candidate_supports_persistent_memory",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The controlled persistent-memory architecture "
                "retains memory across sessions."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_supports_memory_inspect_edit_delete",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The controlled persistent-memory architecture "
                "provides explicit inspect, edit, and delete controls."
            ),
        ),
    ]

    return [
        AgentStarterCandidateArchitecture(
            architecture_id="session-only-personal-assistant",
            goal=AgentStarterGoal.PERSONAL,
            evidence=session_only_evidence,
        ),
        AgentStarterCandidateArchitecture(
            architecture_id="opaque-persistent-memory-assistant",
            goal=AgentStarterGoal.PERSONAL,
            evidence=opaque_memory_evidence,
        ),
        AgentStarterCandidateArchitecture(
            architecture_id="controlled-persistent-memory-assistant",
            goal=AgentStarterGoal.PERSONAL,
            evidence=controlled_memory_evidence,
        ),
    ]
