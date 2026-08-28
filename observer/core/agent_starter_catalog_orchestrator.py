from __future__ import annotations

from observer.core.agent_starter_catalog_matcher import (
    match_agent_starter_catalog_entries,
)
from observer.core.agent_starter_catalog_query_builder import (
    build_agent_starter_catalog_queries,
)
from schemas.agent_starter import (
    AgentStarterGoal,
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
) -> AgentStarterCatalogArchitectureResult:
    queries = build_agent_starter_catalog_queries(
        goal=goal,
        assessment=assessment,
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
) -> list[AgentStarterCatalogArchitectureResult]:
    return [
        match_agent_starter_architecture_to_catalog(
            goal=goal,
            assessment=assessment,
            snapshot=snapshot,
        )
        for assessment in assessments
    ]
