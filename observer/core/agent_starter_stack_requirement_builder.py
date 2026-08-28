from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterGoal,
    CandidateArchitectureAssessment,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
)
from schemas.agent_starter_stack import (
    AgentStarterStackRequirement,
)


def build_agent_starter_stack_requirements(
    *,
    goal: AgentStarterGoal,
    assessment: CandidateArchitectureAssessment,
) -> list[AgentStarterStackRequirement]:
    if goal is AgentStarterGoal.AUTOMATION:
        llm_evidence = [
            evidence
            for evidence in assessment.supporting_evidence
            if evidence.key == "candidate_uses_llm"
        ]

        if (
            len(llm_evidence) != 1
            or not isinstance(llm_evidence[0].value, bool)
        ):
            raise ValueError(
                "Automation stack mapping requires exactly one "
                "candidate_uses_llm boolean evidence value."
            )

        if llm_evidence[0].value is False:
            return []

        return [
            AgentStarterStackRequirement(
                component_type=(
                    AgentStarterCatalogComponentType.LLM
                ),
                supporting_evidence=[
                    llm_evidence[0],
                ],
                reason=(
                    "The automation-agent architecture requires "
                    "a language model."
                ),
            )
        ]

    if goal is AgentStarterGoal.KNOWLEDGE_RAG:
        llm_evidence = [
            evidence
            for evidence in assessment.supporting_evidence
            if evidence.key == "candidate_uses_llm"
        ]
        retrieval_evidence = [
            evidence
            for evidence in assessment.supporting_evidence
            if evidence.key == "candidate_uses_retrieval_pipeline"
        ]

        if (
            len(llm_evidence) != 1
            or not isinstance(llm_evidence[0].value, bool)
            or llm_evidence[0].value is not True
        ):
            raise ValueError(
                "Knowledge stack mapping requires exactly one "
                "candidate_uses_llm evidence value equal to true."
            )

        if (
            len(retrieval_evidence) != 1
            or not isinstance(
                retrieval_evidence[0].value,
                bool,
            )
        ):
            raise ValueError(
                "Knowledge stack mapping requires exactly one "
                "candidate_uses_retrieval_pipeline boolean "
                "evidence value."
            )

        return [
            AgentStarterStackRequirement(
                component_type=(
                    AgentStarterCatalogComponentType.LLM
                ),
                supporting_evidence=[
                    llm_evidence[0],
                ],
                reason=(
                    "The knowledge-assistant architecture "
                    "requires a language model for generation."
                ),
            )
        ]

    if goal is AgentStarterGoal.VOICE:
        stt_evidence = [
            evidence
            for evidence in assessment.supporting_evidence
            if evidence.key == "candidate_uses_stt"
        ]
        tts_evidence = [
            evidence
            for evidence in assessment.supporting_evidence
            if evidence.key == "candidate_uses_tts"
        ]
        raw_audio_evidence = [
            evidence
            for evidence in assessment.supporting_evidence
            if evidence.key
            == "candidate_raw_audio_remote_processing"
        ]
        transcript_evidence = [
            evidence
            for evidence in assessment.supporting_evidence
            if evidence.key
            == "candidate_transcript_remote_processing"
        ]

        if (
            len(stt_evidence) != 1
            or not isinstance(stt_evidence[0].value, bool)
            or stt_evidence[0].value is not True
        ):
            raise ValueError(
                "Voice stack mapping requires exactly one "
                "candidate_uses_stt evidence value equal to true."
            )

        if (
            len(tts_evidence) != 1
            or not isinstance(tts_evidence[0].value, bool)
            or tts_evidence[0].value is not True
        ):
            raise ValueError(
                "Voice stack mapping requires exactly one "
                "candidate_uses_tts evidence value equal to true."
            )

        if (
            len(raw_audio_evidence) != 1
            or not isinstance(
                raw_audio_evidence[0].value,
                bool,
            )
        ):
            raise ValueError(
                "Voice stack mapping requires exactly one "
                "candidate_raw_audio_remote_processing "
                "boolean evidence value."
            )

        if (
            len(transcript_evidence) != 1
            or not isinstance(
                transcript_evidence[0].value,
                bool,
            )
        ):
            raise ValueError(
                "Voice stack mapping requires exactly one "
                "candidate_transcript_remote_processing "
                "boolean evidence value."
            )

        return [
            AgentStarterStackRequirement(
                component_type=(
                    AgentStarterCatalogComponentType.STT
                ),
                supporting_evidence=[
                    stt_evidence[0],
                ],
                reason=(
                    "The voice-pipeline architecture requires "
                    "speech-to-text for speech input processing."
                ),
            ),
            AgentStarterStackRequirement(
                component_type=(
                    AgentStarterCatalogComponentType.TTS
                ),
                supporting_evidence=[
                    tts_evidence[0],
                ],
                reason=(
                    "The voice-pipeline architecture requires "
                    "text-to-speech for speech output generation."
                ),
            ),
        ]

    if goal is not AgentStarterGoal.CODING:
        raise ValueError(
            "Stack requirement mapping is not defined for "
            f"goal: {goal.value}"
        )

    llm_evidence = [
        evidence
        for evidence in assessment.supporting_evidence
        if evidence.key == "candidate_uses_llm"
    ]

    if (
        len(llm_evidence) != 1
        or not isinstance(llm_evidence[0].value, bool)
        or llm_evidence[0].value is not True
    ):
        raise ValueError(
            "Coding stack mapping requires exactly one "
            "candidate_uses_llm evidence value equal to true."
        )

    return [
        AgentStarterStackRequirement(
            component_type=(
                AgentStarterCatalogComponentType.LLM
            ),
            required_capabilities=[
                "coding",
            ],
            supporting_evidence=[
                llm_evidence[0],
            ],
            reason=(
                "The coding-agent architecture requires a "
                "coding-capable language model."
            ),
        )
    ]
