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
