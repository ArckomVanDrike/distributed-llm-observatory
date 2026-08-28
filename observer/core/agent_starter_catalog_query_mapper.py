from __future__ import annotations

from schemas.agent_starter_catalog import (
    AgentStarterCatalogQuery,
)
from schemas.agent_starter_stack import (
    AgentStarterStackRequirement,
)


def map_agent_starter_stack_requirement_to_catalog_query(
    requirement: AgentStarterStackRequirement,
) -> AgentStarterCatalogQuery:
    return AgentStarterCatalogQuery(
        component_type=requirement.component_type,
        required_capabilities=(
            requirement.required_capabilities
        ),
        required_deployment_modes=(
            requirement.required_deployment_modes
        ),
        required_runtime=requirement.required_runtime,
        required_pricing_class=(
            requirement.required_pricing_class
        ),
    )
