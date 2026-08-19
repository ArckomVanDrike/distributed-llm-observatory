from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observer.core.execution import ExecutionContext
from observer.core.runner import ObserverRun, ObserverRunner
from observer.providers.base import ProviderAdapter, ProviderRequest
from schemas.benchmark import BenchmarkPrompt


@dataclass(frozen=True)
class BenchmarkRun:
    benchmark: BenchmarkPrompt
    observation: ObserverRun


class BenchmarkRunner:
    """
    Executes validated Observatory benchmark prompts through a provider adapter.

    The runner builds the execution context automatically from the benchmark
    metadata and the local observer configuration.
    """

    def __init__(
        self,
        provider: ProviderAdapter,
        *,
        observer_id: str,
        region_code: str,
        model: str,
    ) -> None:
        if not observer_id.strip():
            raise ValueError("observer_id cannot be empty.")

        if not region_code.strip():
            raise ValueError("region_code cannot be empty.")

        if not model.strip():
            raise ValueError("model cannot be empty.")

        self.provider = provider
        self.observer_id = observer_id
        self.region_code = region_code
        self.model = model
        self.observer_runner = ObserverRunner(provider)

    def run(
        self,
        benchmark: BenchmarkPrompt,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BenchmarkRun:
        context = ExecutionContext(
            observer_id=self.observer_id,
            region_code=self.region_code,
            benchmark_version=benchmark.benchmark_version,
            prompt_id=benchmark.prompt_id,
            provider=self.provider.provider_name,
            model=self.model,
        )

        request = ProviderRequest(
            prompt=benchmark.prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
        )

        observation = self.observer_runner.run(
            context=context,
            request=request,
        )

        return BenchmarkRun(
            benchmark=benchmark,
            observation=observation,
        )
