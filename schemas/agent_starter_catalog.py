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


class AgentStarterCatalogEntry(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    identifier: str = Field(min_length=1)
    component_type: AgentStarterCatalogComponentType

    vendor: str = Field(min_length=1)
    family: str = Field(min_length=1)
    version: str = Field(min_length=1)

    capabilities: list[str] = Field(default_factory=list)
    deployment_modes: list[str] = Field(default_factory=list)
    supported_runtimes: list[str] = Field(default_factory=list)

    license: str = Field(min_length=1)
    pricing_class: str = Field(min_length=1)
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
    schema_version: Literal["0.1"] = "0.1"

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
