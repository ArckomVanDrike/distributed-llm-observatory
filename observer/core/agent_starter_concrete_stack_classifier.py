from __future__ import annotations

from schemas.agent_starter import RecommendationVerdict
from schemas.agent_starter_result import (
    AgentStarterConcreteStackClassification,
    AgentStarterConcreteStackResolution,
)


def classify_agent_starter_concrete_stacks(
    resolution: AgentStarterConcreteStackResolution,
) -> AgentStarterConcreteStackClassification:
    recommended_architecture_ids: list[str] = []
    possible_architecture_ids: list[str] = []
    possible_but_not_recommended_architecture_ids: list[str] = []
    not_recommended_architecture_ids: list[str] = []

    for assessment in (
        resolution.catalog_result.plan.candidate_assessments
    ):
        if (
            assessment.recommendation
            is RecommendationVerdict.RECOMMENDED
        ):
            recommended_architecture_ids.append(
                assessment.architecture_id
            )
        elif (
            assessment.recommendation
            is RecommendationVerdict.POSSIBLE
        ):
            possible_architecture_ids.append(
                assessment.architecture_id
            )
        elif (
            assessment.recommendation
            is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
        ):
            possible_but_not_recommended_architecture_ids.append(
                assessment.architecture_id
            )
        elif (
            assessment.recommendation
            is RecommendationVerdict.NOT_RECOMMENDED
        ):
            not_recommended_architecture_ids.append(
                assessment.architecture_id
            )

    return AgentStarterConcreteStackClassification(
        resolution=resolution,
        recommended_architecture_ids=(
            recommended_architecture_ids
        ),
        possible_architecture_ids=possible_architecture_ids,
        possible_but_not_recommended_architecture_ids=(
            possible_but_not_recommended_architecture_ids
        ),
        not_recommended_architecture_ids=(
            not_recommended_architecture_ids
        ),
    )
