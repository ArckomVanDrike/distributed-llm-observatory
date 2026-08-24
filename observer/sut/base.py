from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from schemas.target import TargetManifest


@dataclass(frozen=True)
class SUTExecutionContext:
    observer_id: str
    region_code: str
    benchmark_version: str
    task_id: str
    target_id: str


@dataclass(frozen=True)
class SUTRequest:
    task: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class SUTExecutionResult:
    context: SUTExecutionContext

    started_at_utc: datetime
    finished_at_utc: datetime
    latency_ms: float

    task_completed: bool
    output_text: str | None = None

    retry_count: int = 0
    human_intervention_count: int = 0
    error_type: str | None = None

    metrics: dict[str, Any] = field(
        default_factory=dict,
    )


class SUTAdapter(ABC):
    """
    Base interface for agents and complete AI systems.

    Unlike ProviderAdapter, this contract models an end-to-end task
    rather than a provider-specific LLM prompt execution.
    """

    manifest: TargetManifest

    @abstractmethod
    def execute(
        self,
        context: SUTExecutionContext,
        request: SUTRequest,
    ) -> SUTExecutionResult:
        raise NotImplementedError
