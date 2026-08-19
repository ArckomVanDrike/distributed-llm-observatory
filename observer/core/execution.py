from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter


@dataclass(frozen=True)
class ExecutionContext:
    observer_id: str
    region_code: str
    benchmark_version: str
    prompt_id: str
    provider: str
    model: str


@dataclass(frozen=True)
class ExecutionResult:
    context: ExecutionContext
    started_at_utc: datetime
    finished_at_utc: datetime
    latency_ms: float
    response_text: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int | None = None
    time_to_first_token_ms: float | None = None
    retry_count: int = 0
    error_type: str | None = None
    truncated: bool = False

    @property
    def tokens_per_second(self) -> float:
        if self.latency_ms <= 0:
            return 0.0

        seconds = self.latency_ms / 1000
        return self.output_tokens / seconds


class ExecutionTimer:
    def __init__(self) -> None:
        self._started_at_utc: datetime | None = None
        self._finished_at_utc: datetime | None = None
        self._start_perf: float | None = None
        self._elapsed_ms: float | None = None

    def start(self) -> None:
        self._started_at_utc = datetime.now(timezone.utc)
        self._start_perf = perf_counter()

    def stop(self) -> None:
        if self._start_perf is None or self._started_at_utc is None:
            raise RuntimeError("ExecutionTimer must be started before stop().")

        self._elapsed_ms = (perf_counter() - self._start_perf) * 1000
        self._finished_at_utc = datetime.now(timezone.utc)

    @property
    def started_at_utc(self) -> datetime:
        if self._started_at_utc is None:
            raise RuntimeError("ExecutionTimer has not been started.")
        return self._started_at_utc

    @property
    def finished_at_utc(self) -> datetime:
        if self._finished_at_utc is None:
            raise RuntimeError("ExecutionTimer has not been stopped.")
        return self._finished_at_utc

    @property
    def elapsed_ms(self) -> float:
        if self._elapsed_ms is None:
            raise RuntimeError("ExecutionTimer has not been stopped.")
        return self._elapsed_ms
