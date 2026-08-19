from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ObserverInfo(BaseModel):
    observer_id: str = Field(min_length=1)
    region_code: str = Field(min_length=2)
    observer_version: str = Field(min_length=1)


class BenchmarkInfo(BaseModel):
    benchmark_version: str = Field(min_length=1)
    prompt_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)


class ModelExecution(BaseModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    timestamp_utc: datetime
    prompt_id: str = Field(min_length=1)

    response_text: str

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)

    time_to_first_token_ms: float | None = Field(default=None, ge=0)
    latency_ms: float = Field(ge=0)
    tokens_per_second: float = Field(ge=0)

    error_type: str | None = None
    retry_count: int = Field(default=0, ge=0)
    truncated: bool = False
