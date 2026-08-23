from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observer.core.benchmark_compatibility import target_supports_task
from observer.sut.base import (
    SUTAdapter,
    SUTExecutionContext,
    SUTRequest,
)
from observer.sut.runner import SUTRun, SUTRunner
from schemas.benchmark import BenchmarkTask


@dataclass(frozen=True)
class BenchmarkTaskRun:
    benchmark: BenchmarkTask
    observation: SUTRun


class BenchmarkTaskRunner:
    """
    Executes validated agent and AI-system benchmark tasks through a SUT adapter.
    """

    def __init__(
        self,
        adapter: SUTAdapter,
        *,
        observer_id: str,
        region_code: str,
    ) -> None:
        if not observer_id.strip():
            raise ValueError("observer_id cannot be empty.")

        if not region_code.strip():
            raise ValueError("region_code cannot be empty.")

        self.adapter = adapter
        self.observer_id = observer_id
        self.region_code = region_code
        self.sut_runner = SUTRunner(adapter)

    def run(
        self,
        benchmark: BenchmarkTask,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> BenchmarkTaskRun:
        if not target_supports_task(
            self.adapter.manifest,
            benchmark,
        ):
            raise ValueError(
                "Benchmark task is not compatible with "
                f"target {self.adapter.manifest.target_id!r}."
            )

        context = SUTExecutionContext(
            observer_id=self.observer_id,
            region_code=self.region_code,
            benchmark_version=benchmark.benchmark_version,
            task_id=benchmark.task_id,
            target_id=self.adapter.manifest.target_id,
        )

        request = SUTRequest(
            task=benchmark.task,
            metadata=metadata,
        )

        observation = self.sut_runner.run(
            context=context,
            request=request,
        )

        return BenchmarkTaskRun(
            benchmark=benchmark,
            observation=observation,
        )
