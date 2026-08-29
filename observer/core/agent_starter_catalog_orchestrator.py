from __future__ import annotations

from observer.core.agent_starter_catalog_matcher import (
    match_agent_starter_catalog_entries,
)
from observer.core.agent_starter_catalog_query_builder import (
    build_agent_starter_catalog_queries,
)
from schemas.agent_starter import (
    AgentStarterGoal,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogArchitectureResult,
    AgentStarterCatalogQueryMatch,
    AgentStarterCatalogSnapshot,
)


def match_agent_starter_architecture_to_catalog(
    *,
    goal: AgentStarterGoal,
    assessment: CandidateArchitectureAssessment,
    snapshot: AgentStarterCatalogSnapshot,
    plan_requirements: list[
        AgentStarterRequirement
    ] | None = None,
) -> AgentStarterCatalogArchitectureResult:
    queries = build_agent_starter_catalog_queries(
        goal=goal,
        assessment=assessment,
        plan_requirements=plan_requirements,
    )

    query_matches = [
        AgentStarterCatalogQueryMatch(
            architecture_id=assessment.architecture_id,
            catalog_snapshot_id=snapshot.snapshot_id,
            query=query,
            matched_entries=match_agent_starter_catalog_entries(
                snapshot=snapshot,
                query=query,
            ),
        )
        for query in queries
    ]

    return AgentStarterCatalogArchitectureResult(
        architecture_id=assessment.architecture_id,
        catalog_snapshot_id=snapshot.snapshot_id,
        query_matches=query_matches,
    )


def match_agent_starter_candidates_to_catalog(
    *,
    goal: AgentStarterGoal,
    assessments: list[CandidateArchitectureAssessment],
    snapshot: AgentStarterCatalogSnapshot,
    plan_requirements: list[
        AgentStarterRequirement
    ] | None = None,
) -> list[AgentStarterCatalogArchitectureResult]:
    return [
        match_agent_starter_architecture_to_catalog(
            goal=goal,
            assessment=assessment,
            snapshot=snapshot,
            plan_requirements=plan_requirements,
        )
        for assessment in assessments
    ]
