from __future__ import annotations

from observer.core.agent_starter_catalog_query_mapper import (
    map_agent_starter_stack_requirement_to_catalog_query,
)
from observer.core.agent_starter_stack_requirement_builder import (
    build_agent_starter_stack_requirements,
)
from schemas.agent_starter import (
    AgentStarterGoal,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogArchitectureResult,
)
from schemas.agent_starter_stack import (
    AgentStarterConcreteStack,
    AgentStarterConcreteStackComponent,
)


def build_agent_starter_concrete_stack(
    *,
    goal: AgentStarterGoal,
    assessment: CandidateArchitectureAssessment,
    architecture_result: AgentStarterCatalogArchitectureResult,
    plan_requirements: list[
        AgentStarterRequirement
    ] | None = None,
) -> AgentStarterConcreteStack:
    if architecture_result.architecture_id != assessment.architecture_id:
        raise ValueError(
            "Catalog architecture result must match "
            "the assessed architecture."
        )

    requirements = build_agent_starter_stack_requirements(
        goal=goal,
        assessment=assessment,
        plan_requirements=plan_requirements,
    )

    query_matches = list(architecture_result.query_matches)

    if len(query_matches) != len(requirements):
        raise ValueError(
            "Catalog query count does not match derived "
            "stack requirement count."
        )

    components: list[AgentStarterConcreteStackComponent] = []

    for requirement, query_match in zip(
        requirements,
        query_matches,
        strict=True,
    ):
        expected_query = (
            map_agent_starter_stack_requirement_to_catalog_query(
                requirement
            )
        )

        if query_match.query != expected_query:
            raise ValueError(
                "catalog query does not match derived "
                "stack requirement."
            )

        matched_entries = list(query_match.matched_entries)
        indeterminate_entries = list(
            query_match.indeterminate_entries
        )
        constraint_excluded_entries = list(
            query_match.constraint_excluded_entries
        )

        selected_entry = (
            matched_entries[0]
            if len(matched_entries) == 1
            else None
        )

        components.append(
            AgentStarterConcreteStackComponent(
                requirement=requirement,
                matched_entries=matched_entries,
                indeterminate_entries=indeterminate_entries,
                constraint_excluded_entries=(
                    constraint_excluded_entries
                ),
                selected_entry=selected_entry,
            )
        )

    return AgentStarterConcreteStack(
        architecture_id=assessment.architecture_id,
        catalog_snapshot_id=(
            architecture_result.catalog_snapshot_id
        ),
        components=components,
    )
