from __future__ import annotations

from schemas.agent_starter_catalog import (
    AgentStarterCatalogEntry,
    AgentStarterCatalogQuery,
    AgentStarterCatalogSnapshot,
)


def match_agent_starter_catalog_entries(
    *,
    snapshot: AgentStarterCatalogSnapshot,
    query: AgentStarterCatalogQuery,
) -> list[AgentStarterCatalogEntry]:
    required_capabilities = set(
        query.required_capabilities
    )
    required_deployment_modes = set(
        query.required_deployment_modes
    )

    return [
        entry
        for entry in snapshot.entries
        if entry.component_type is query.component_type
        and required_capabilities.issubset(
            set(entry.capabilities)
        )
        and required_deployment_modes.issubset(
            set(entry.deployment_modes)
        )
        and (
            query.required_runtime is None
            or query.required_runtime
            in entry.supported_runtimes
        )
        and (
            query.required_pricing_class is None
            or entry.pricing_class
            == query.required_pricing_class
        )
    ]
