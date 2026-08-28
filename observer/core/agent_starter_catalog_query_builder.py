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

    raise ValueError(
        "Catalog query mapping is not defined for "
        f"goal: {goal.value}"
    )
