from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

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
