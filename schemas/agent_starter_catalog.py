from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from schemas.model_profile import ModelProfile


class AgentStarterCatalogComponentType(str, Enum):
    LLM = "llm"
    RUNTIME = "runtime"
    AGENT_FRAMEWORK = "agent_framework"
    EMBEDDING_MODEL = "embedding_model"
    VECTOR_STORE = "vector_store"
    STT = "stt"
    TTS = "tts"
    SUPPORTING_TOOL = "supporting_tool"


class AgentStarterCatalogReleaseStatus(str, Enum):
    STABLE = "stable"
    PREVIEW = "preview"
    EXPERIMENTAL_PREVIEW = "experimental_preview"
    DEPRECATED = "deprecated"
    UNKNOWN = "unknown"


class AgentStarterCatalogLicenseCost(str, Enum):
    FREE = "free"
    PAID = "paid"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class AgentStarterCatalogAccessPricing(str, Enum):
    FREE = "free"
    FREEMIUM = "freemium"
    USAGE_BASED = "usage_based"
    SUBSCRIPTION = "subscription"
    ENTERPRISE = "enterprise"
    PROVIDER_DEPENDENT = "provider_dependent"
    UNKNOWN = "unknown"


class AgentStarterCatalogAccessKind(str, Enum):
    SELF_HOSTED = "self_hosted"
    EXTERNAL_SERVICE = "external_service"


class AgentStarterCatalogAccessOption(BaseModel):
    schema_version: Literal["0.2"] = "0.2"

    deployment_mode: str = Field(min_length=1)
    access_kind: AgentStarterCatalogAccessKind
    pricing: AgentStarterCatalogAccessPricing
    notes: str | None = Field(
        default=None,
        min_length=1,
    )


class AgentStarterCatalogEntry(BaseModel):
    schema_version: Literal["0.1", "0.2"] = "0.1"

    identifier: str = Field(min_length=1)
    component_type: AgentStarterCatalogComponentType

    vendor: str = Field(min_length=1)
    family: str = Field(min_length=1)
    version: str = Field(min_length=1)

    capabilities: list[str] = Field(default_factory=list)
    deployment_modes: list[str] = Field(default_factory=list)
    supported_runtimes: list[str] = Field(default_factory=list)

    resource_profile: dict[
        str,
        str | int | float | bool | list[str],
    ] = Field(default_factory=dict)
    context_characteristics: dict[
        str,
        str | int | float | bool | list[str],
    ] = Field(default_factory=dict)
    language_support: list[str] = Field(default_factory=list)
    streaming_support: bool | None = None

    license: str = Field(min_length=1)
    pricing_class: str = Field(min_length=1)

    release_status: AgentStarterCatalogReleaseStatus = (
        AgentStarterCatalogReleaseStatus.UNKNOWN
    )
    license_cost: AgentStarterCatalogLicenseCost = (
        AgentStarterCatalogLicenseCost.UNKNOWN
    )
    access_pricing: list[
        AgentStarterCatalogAccessPricing
    ] = Field(
        default_factory=lambda: [
            AgentStarterCatalogAccessPricing.UNKNOWN
        ],
    )
    pricing_notes: str | None = Field(
        default=None,
        min_length=1,
    )

    access_options: list[
        AgentStarterCatalogAccessOption
    ] = Field(
        default_factory=list,
    )

    privacy_implications: list[str] = Field(
        default_factory=list,
    )

    sources: list[str] = Field(min_length=1)
    verified_at: datetime

    model_profile: ModelProfile | None = None

    @field_validator("verified_at")
    @classmethod
    def validate_verified_at_timezone(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "verified_at must be timezone-aware."
            )

        return value


class AgentStarterCatalogSnapshot(BaseModel):
    schema_version: Literal["0.1", "0.2"] = "0.1"

    snapshot_id: str = Field(min_length=1)
    generated_at: datetime
    entries: list[AgentStarterCatalogEntry] = Field(
        default_factory=list,
    )

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at_timezone(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "generated_at must be timezone-aware."
            )

        return value

    @model_validator(mode="after")
    def validate_unique_entry_identifiers(
        self,
    ) -> AgentStarterCatalogSnapshot:
        identifiers = [
            entry.identifier
            for entry in self.entries
        ]

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "Catalog snapshot entry identifiers "
                "must be unique."
            )

        return self


class AgentStarterCatalogQuery(BaseModel):
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


class AgentStarterCatalogQueryMatch(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    architecture_id: str = Field(min_length=1)
    catalog_snapshot_id: str = Field(min_length=1)
    query: AgentStarterCatalogQuery

    matched_entries: list[AgentStarterCatalogEntry] = Field(
        default_factory=list,
    )
    indeterminate_entries: list[
        AgentStarterCatalogEntry
    ] = Field(
        default_factory=list,
    )
    constraint_excluded_entries: list[
        AgentStarterCatalogEntry
    ] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_result_component_types(
        self,
    ) -> AgentStarterCatalogQueryMatch:
        result_entries = [
            *self.matched_entries,
            *self.indeterminate_entries,
            *self.constraint_excluded_entries,
        ]

        if any(
            entry.component_type is not self.query.component_type
            for entry in result_entries
        ):
            raise ValueError(
                "Catalog query result entries must have the "
                "component type requested by the query."
            )

        return self

    @model_validator(mode="after")
    def validate_result_class_exclusivity(
        self,
    ) -> AgentStarterCatalogQueryMatch:
        matched_ids = {
            entry.identifier
            for entry in self.matched_entries
        }
        indeterminate_ids = {
            entry.identifier
            for entry in self.indeterminate_entries
        }
        excluded_ids = {
            entry.identifier
            for entry in self.constraint_excluded_entries
        }

        if (
            matched_ids & indeterminate_ids
            or matched_ids & excluded_ids
            or indeterminate_ids & excluded_ids
        ):
            raise ValueError(
                "A catalog entry may appear in only one "
                "query result class."
            )

        return self


class AgentStarterCatalogArchitectureResult(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    architecture_id: str = Field(min_length=1)
    catalog_snapshot_id: str = Field(min_length=1)
    query_matches: list[AgentStarterCatalogQueryMatch] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_query_match_architectures(
        self,
    ) -> AgentStarterCatalogArchitectureResult:
        if any(
            match.architecture_id != self.architecture_id
            for match in self.query_matches
        ):
            raise ValueError(
                "Catalog architecture result may contain only "
                "query matches for the same architecture."
            )

        return self


    @model_validator(mode="after")
    def validate_query_match_snapshots(
        self,
    ) -> AgentStarterCatalogArchitectureResult:
        if any(
            match.catalog_snapshot_id != self.catalog_snapshot_id
            for match in self.query_matches
        ):
            raise ValueError(
                "Catalog architecture result may contain only "
                "query matches from the same catalog snapshot."
            )

        return self
