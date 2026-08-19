from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from schemas.observation import BenchmarkInfo, ModelExecution, ObserverInfo


class GenerationSettings(BaseModel):
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, ge=1)


class ObservationRecord(BaseModel):
    schema_version: str = "0.1"
    observation_id: UUID = Field(default_factory=uuid4)

    observer: ObserverInfo
    benchmark: BenchmarkInfo
    generation: GenerationSettings
    execution: ModelExecution
