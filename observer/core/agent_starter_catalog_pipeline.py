from __future__ import annotations

from observer.core.agent_starter_catalog_orchestrator import (
    match_agent_starter_candidates_to_catalog,
)
from schemas.agent_starter import AgentStarterPlan
from schemas.agent_starter_catalog import (
    AgentStarterCatalogSnapshot,
)
from schemas.agent_starter_result import (
    AgentStarterCatalogMatchingResult,
)


def run_agent_starter_catalog_matching(
    *,
    plan: AgentStarterPlan,
    snapshot: AgentStarterCatalogSnapshot,
) -> AgentStarterCatalogMatchingResult:
    architecture_results = (
        match_agent_starter_candidates_to_catalog(
            goal=plan.goal,
            assessments=list(plan.candidate_assessments),
            snapshot=snapshot,
            plan_requirements=list(plan.requirements),
        )
    )

    return AgentStarterCatalogMatchingResult(
        plan=plan,
        catalog_snapshot_id=snapshot.snapshot_id,
        architecture_results=architecture_results,
    )
