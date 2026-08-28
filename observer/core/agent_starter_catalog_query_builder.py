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

    raise ValueError(
        "Catalog query mapping is not defined for "
        f"goal: {goal.value}"
    )
