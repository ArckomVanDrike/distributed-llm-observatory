from __future__ import annotations

from observer.core.agent_starter_catalog_query_mapper import (
    map_agent_starter_stack_requirement_to_catalog_query,
)
from observer.core.agent_starter_stack_requirement_builder import (
    build_agent_starter_stack_requirements,
)
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
        requirements = build_agent_starter_stack_requirements(
            goal=goal,
            assessment=assessment,
        )

        return [
            map_agent_starter_stack_requirement_to_catalog_query(
                requirement
            )
            for requirement in requirements
        ]

    if goal is AgentStarterGoal.AUTOMATION:
        requirements = build_agent_starter_stack_requirements(
            goal=goal,
            assessment=assessment,
        )

        return [
            map_agent_starter_stack_requirement_to_catalog_query(
                requirement
            )
            for requirement in requirements
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

    if goal is AgentStarterGoal.PERSONAL:
        supports_persistent_memory = [
            evidence.value
            for evidence in assessment.supporting_evidence
            if evidence.key
            == "candidate_supports_persistent_memory"
        ]

        if (
            len(supports_persistent_memory) != 1
            or not isinstance(
                supports_persistent_memory[0],
                bool,
            )
        ):
            raise ValueError(
                "Personal catalog mapping requires exactly one "
                "candidate_supports_persistent_memory "
                "evidence value."
            )

        return [
            AgentStarterCatalogQuery(
                component_type=(
                    AgentStarterCatalogComponentType.LLM
                ),
            )
        ]

    raise ValueError(
        "Catalog query mapping is not defined for "
        f"goal: {goal.value}"
    )
