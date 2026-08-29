from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from schemas.agent_starter import (
    AgentStarterEvidence,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
    AgentStarterCatalogEntry,
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



class AgentStarterConcreteStackComponent(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    requirement: AgentStarterStackRequirement
    matched_entries: list[AgentStarterCatalogEntry] = Field(
        default_factory=list,
    )
    selected_entry: AgentStarterCatalogEntry | None = None

    @model_validator(mode="after")
    def validate_selected_entry(
        self,
    ) -> AgentStarterConcreteStackComponent:
        if (
            len(self.matched_entries) > 1
            and self.selected_entry is not None
        ):
            raise ValueError(
                "A concrete stack component cannot select an "
                "entry while multiple catalog matches remain."
            )

        if (
            self.selected_entry is not None
            and self.selected_entry not in self.matched_entries
        ):
            raise ValueError(
                "The selected catalog entry must be one of "
                "the matched entries."
            )

        return self


class AgentStarterConcreteStack(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    architecture_id: str = Field(min_length=1)
    catalog_snapshot_id: str = Field(min_length=1)
    components: list[
        AgentStarterConcreteStackComponent
    ] = Field(default_factory=list)
