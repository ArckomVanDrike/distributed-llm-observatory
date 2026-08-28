from __future__ import annotations

from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
    AgentStarterCatalogEntry,
    AgentStarterCatalogSnapshot,
)


def match_agent_starter_catalog_entries(
    *,
    snapshot: AgentStarterCatalogSnapshot,
    component_type: AgentStarterCatalogComponentType,
    required_capabilities: list[str],
    required_deployment_modes: list[str] | None = None,
    required_runtime: str | None = None,
    required_pricing_class: str | None = None,
) -> list[AgentStarterCatalogEntry]:
    required = set(required_capabilities)
    required_deployment = set(
        required_deployment_modes or []
    )

    return [
        entry
        for entry in snapshot.entries
        if entry.component_type is component_type
        and required.issubset(set(entry.capabilities))
        and required_deployment.issubset(
            set(entry.deployment_modes)
        )
        and (
            required_runtime is None
            or required_runtime in entry.supported_runtimes
        )
        and (
            required_pricing_class is None
            or entry.pricing_class == required_pricing_class
        )
    ]
