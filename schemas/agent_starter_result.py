from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from schemas.agent_starter import AgentStarterPlan
from schemas.agent_starter_catalog import (
    AgentStarterCatalogArchitectureResult,
)
from schemas.agent_starter_stack import (
    AgentStarterConcreteStack,
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



class AgentStarterConcreteStackResolution(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    catalog_result: AgentStarterCatalogMatchingResult
    stacks: list[AgentStarterConcreteStack] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_stack_architectures(
        self,
    ) -> AgentStarterConcreteStackResolution:
        expected_ids = [
            result.architecture_id
            for result in self.catalog_result.architecture_results
        ]
        actual_ids = [
            stack.architecture_id
            for stack in self.stacks
        ]

        if actual_ids != expected_ids:
            raise ValueError(
                "Concrete stacks must correspond exactly "
                "and in order to catalog architecture results."
            )

        return self

    @model_validator(mode="after")
    def validate_stack_catalog_snapshot(
        self,
    ) -> AgentStarterConcreteStackResolution:
        if any(
            stack.catalog_snapshot_id
            != self.catalog_result.catalog_snapshot_id
            for stack in self.stacks
        ):
            raise ValueError(
                "Concrete stacks must use the same catalog snapshot "
                "as the catalog matching result."
            )

        return self
