from __future__ import annotations

from observer.core.agent_starter_concrete_stack_builder import (
    build_agent_starter_concrete_stack,
)
from schemas.agent_starter_result import (
    AgentStarterCatalogMatchingResult,
    AgentStarterConcreteStackResolution,
)
from schemas.agent_starter_stack import (
    AgentStarterConcreteStack,
)


def build_agent_starter_concrete_stacks(
    catalog_result: AgentStarterCatalogMatchingResult,
) -> AgentStarterConcreteStackResolution:
    assessments = list(
        catalog_result.plan.candidate_assessments
    )
    architecture_results = list(
        catalog_result.architecture_results
    )

    if len(assessments) != len(architecture_results):
        raise ValueError(
            "Candidate assessment count does not match "
            "catalog architecture result count."
        )

    stacks: list[AgentStarterConcreteStack] = []

    for assessment, architecture_result in zip(
        assessments,
        architecture_results,
        strict=True,
    ):
        if (
            assessment.architecture_id
            != architecture_result.architecture_id
        ):
            raise ValueError(
                "Catalog architecture result must correspond "
                "to the candidate assessment in the same position."
            )

        stacks.append(
            build_agent_starter_concrete_stack(
                goal=catalog_result.plan.goal,
                assessment=assessment,
                architecture_result=architecture_result,
                plan_requirements=list(
                    catalog_result.plan.requirements
                ),
            )
        )

    return AgentStarterConcreteStackResolution(
        catalog_result=catalog_result,
        stacks=stacks,
    )
