from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterGoal,
    CandidateArchitectureAssessment,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
    AgentStarterCatalogQuery,
)


def build_agent_starter_catalog_queries(
    *,
    goal: AgentStarterGoal,
    assessment: CandidateArchitectureAssessment,
) -> list[AgentStarterCatalogQuery]:
    if goal is AgentStarterGoal.CODING:
        return [
            AgentStarterCatalogQuery(
                component_type=(
                    AgentStarterCatalogComponentType.LLM
                ),
                required_capabilities=[
                    "coding",
                ],
            )
        ]

    if goal is AgentStarterGoal.AUTOMATION:
        candidate_uses_llm = [
            evidence.value
            for evidence in assessment.supporting_evidence
            if evidence.key == "candidate_uses_llm"
        ]

        if (
            len(candidate_uses_llm) != 1
            or not isinstance(candidate_uses_llm[0], bool)
        ):
            raise ValueError(
                "Automation catalog mapping requires exactly one "
                "candidate_uses_llm evidence value."
            )

        if candidate_uses_llm[0] is False:
            return []

        return [
            AgentStarterCatalogQuery(
                component_type=(
                    AgentStarterCatalogComponentType.LLM
                ),
            )
        ]

    if goal is AgentStarterGoal.KNOWLEDGE_RAG:
        uses_retrieval_pipeline = [
            evidence.value
            for evidence in assessment.supporting_evidence
            if evidence.key == "candidate_uses_retrieval_pipeline"
        ]

        if (
            len(uses_retrieval_pipeline) != 1
            or not isinstance(uses_retrieval_pipeline[0], bool)
        ):
            raise ValueError(
                "Knowledge catalog mapping requires exactly one "
                "candidate_uses_retrieval_pipeline evidence value."
            )

        return [
            AgentStarterCatalogQuery(
                component_type=(
                    AgentStarterCatalogComponentType.LLM
                ),
            )
        ]

    if goal is AgentStarterGoal.VOICE:
        raw_audio_remote_processing = [
            evidence.value
            for evidence in assessment.supporting_evidence
            if evidence.key
            == "candidate_raw_audio_remote_processing"
        ]
        transcript_remote_processing = [
            evidence.value
            for evidence in assessment.supporting_evidence
            if evidence.key
            == "candidate_transcript_remote_processing"
        ]

        if (
            len(raw_audio_remote_processing) != 1
            or not isinstance(
                raw_audio_remote_processing[0],
                bool,
            )
        ):
            raise ValueError(
                "Voice catalog mapping requires exactly one "
                "candidate_raw_audio_remote_processing "
                "evidence value."
            )

        if (
            len(transcript_remote_processing) != 1
            or not isinstance(
                transcript_remote_processing[0],
                bool,
            )
        ):
            raise ValueError(
                "Voice catalog mapping requires exactly one "
                "candidate_transcript_remote_processing "
                "evidence value."
            )

        return [
            AgentStarterCatalogQuery(
                component_type=(
                    AgentStarterCatalogComponentType.STT
                ),
            ),
            AgentStarterCatalogQuery(
                component_type=(
                    AgentStarterCatalogComponentType.TTS
                ),
            ),
        ]

    raise ValueError(
        "Catalog query mapping is not defined for "
        f"goal: {goal.value}"
    )
