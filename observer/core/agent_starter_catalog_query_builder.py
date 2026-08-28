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

    if goal is AgentStarterGoal.VOICE:
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

    if goal is AgentStarterGoal.PERSONAL:
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

    raise ValueError(
        "Catalog query mapping is not defined for "
        f"goal: {goal.value}"
    )
