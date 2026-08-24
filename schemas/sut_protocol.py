from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from schemas.target import TargetManifest


class SUTProtocolExecutionContext(BaseModel):
    observer_id: str = Field(min_length=1)
    region_code: str = Field(min_length=1)
    benchmark_version: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)


class SUTProtocolManifestResponse(BaseModel):
    schema_version: str = "0.1"

    manifest: TargetManifest


class SUTProtocolExecutionRequest(BaseModel):
    schema_version: str = "0.1"

    context: SUTProtocolExecutionContext
    task: str = Field(min_length=1)

    metadata: dict[str, Any] | None = None


class SUTProtocolExecutionResponse(BaseModel):
    schema_version: str = "0.1"

    context: SUTProtocolExecutionContext

    started_at_utc: datetime
    finished_at_utc: datetime
    latency_ms: float = Field(ge=0)

    task_completed: bool
    output_text: str | None = None

    retry_count: int = Field(default=0, ge=0)
    human_intervention_count: int = Field(
        default=0,
        ge=0,
    )
    error_type: str | None = None

    metrics: dict[str, Any] = Field(
        default_factory=dict,
    )
