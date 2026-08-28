from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from schemas.agent_starter import AgentStarterPlan
from schemas.agent_starter_catalog import (
    AgentStarterCatalogArchitectureResult,
)


class AgentStarterCatalogMatchingResult(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    plan: AgentStarterPlan
    catalog_snapshot_id: str = Field(min_length=1)
    architecture_results: list[
        AgentStarterCatalogArchitectureResult
    ] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_architecture_results(
        self,
    ) -> AgentStarterCatalogMatchingResult:
        expected_ids = [
            assessment.architecture_id
            for assessment in self.plan.candidate_assessments
        ]
        actual_ids = [
            result.architecture_id
            for result in self.architecture_results
        ]

        if actual_ids != expected_ids:
            raise ValueError(
                "Catalog architecture results must correspond exactly "
                "and in order to plan candidate assessments."
            )

        return self


    @model_validator(mode="after")
    def validate_catalog_snapshot_provenance(
        self,
    ) -> AgentStarterCatalogMatchingResult:
        if any(
            result.catalog_snapshot_id != self.catalog_snapshot_id
            for result in self.architecture_results
        ):
            raise ValueError(
                "Catalog architecture results must come from "
                "the declared catalog snapshot."
            )

        return self
