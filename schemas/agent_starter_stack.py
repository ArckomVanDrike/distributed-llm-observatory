from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from schemas.agent_starter import (
    AgentStarterEvidence,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
)


class AgentStarterStackRequirement(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    component_type: AgentStarterCatalogComponentType

    required_capabilities: list[str] = Field(
        default_factory=list,
    )
    required_deployment_modes: list[str] = Field(
        default_factory=list,
    )
    required_runtime: str | None = None
    required_pricing_class: str | None = None

    supporting_evidence: list[AgentStarterEvidence] = Field(
        min_length=1,
    )
    reason: str = Field(min_length=1)
