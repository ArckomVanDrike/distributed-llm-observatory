from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ExecutionLocation(str, Enum):
    ON_DEVICE = "on_device"
    REMOTE = "remote"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class ModelProfile(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    model_id: str = Field(min_length=1)

    parameter_count: int | None = Field(
        default=None,
        gt=0,
    )
    quantization: str | None = Field(
        default=None,
        min_length=1,
    )
    context_window_tokens: int | None = Field(
        default=None,
        gt=0,
    )
    runtime: str | None = Field(
        default=None,
        min_length=1,
    )

    execution_location: ExecutionLocation
