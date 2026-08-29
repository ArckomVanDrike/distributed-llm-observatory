from __future__ import annotations

from observer.core.agent_starter_concrete_stack_classifier import (
    classify_agent_starter_concrete_stacks,
)
from observer.core.agent_starter_concrete_stack_orchestrator import (
    build_agent_starter_concrete_stacks,
)
from schemas.agent_starter_result import (
    AgentStarterCatalogMatchingResult,
    AgentStarterConcreteStackClassification,
)


def run_agent_starter_concrete_stack_pipeline(
    catalog_result: AgentStarterCatalogMatchingResult,
) -> AgentStarterConcreteStackClassification:
    resolution = build_agent_starter_concrete_stacks(
        catalog_result
    )

    return classify_agent_starter_concrete_stacks(
        resolution
    )
