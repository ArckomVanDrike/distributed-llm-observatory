from __future__ import annotations

from observer.core.benchmark_runner import BenchmarkRun
from schemas.observation import BenchmarkInfo, ModelExecution, ObserverInfo
from schemas.record import GenerationSettings, ObservationRecord


def build_observation_record(run: BenchmarkRun) -> ObservationRecord:
    context = run.observation.context
    request = run.observation.request
    result = run.observation.result
    benchmark = run.benchmark

    return ObservationRecord(
        observer=ObserverInfo(
            observer_id=context.observer_id,
            region_code=context.region_code,
            observer_version="0.1",
        ),
        benchmark=BenchmarkInfo(
            benchmark_version=benchmark.benchmark_version,
            prompt_id=benchmark.prompt_id,
            category=benchmark.category.value,
            difficulty=benchmark.difficulty.value,
        ),
        generation=GenerationSettings(
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        ),
        execution=ModelExecution(
            provider=context.provider,
            model=context.model,
            timestamp_utc=result.started_at_utc,
            prompt_id=context.prompt_id,
            response_text=result.response_text,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            reasoning_tokens=result.reasoning_tokens,
            time_to_first_token_ms=result.time_to_first_token_ms,
            latency_ms=result.latency_ms,
            tokens_per_second=result.tokens_per_second,
            error_type=result.error_type,
            retry_count=result.retry_count,
            truncated=result.truncated,
        ),
    )
