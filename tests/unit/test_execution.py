from datetime import datetime, timezone
from time import sleep

import pytest

from observer.core.execution import ExecutionContext, ExecutionResult, ExecutionTimer


def make_context() -> ExecutionContext:
    return ExecutionContext(
        observer_id="observer-001",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        prompt_id="reasoning-001",
        provider="test-provider",
        model="test-model",
    )


def test_execution_timer_measures_elapsed_time():
    timer = ExecutionTimer()

    timer.start()
    sleep(0.01)
    timer.stop()

    assert timer.elapsed_ms > 0
    assert timer.finished_at_utc >= timer.started_at_utc


def test_execution_timer_cannot_stop_before_start():
    timer = ExecutionTimer()

    with pytest.raises(RuntimeError):
        timer.stop()


def test_execution_result_calculates_tokens_per_second():
    now = datetime.now(timezone.utc)

    result = ExecutionResult(
        context=make_context(),
        started_at_utc=now,
        finished_at_utc=now,
        latency_ms=2000,
        response_text="Test response",
        input_tokens=100,
        output_tokens=50,
    )

    assert result.tokens_per_second == 25


def test_zero_latency_returns_zero_tokens_per_second():
    now = datetime.now(timezone.utc)

    result = ExecutionResult(
        context=make_context(),
        started_at_utc=now,
        finished_at_utc=now,
        latency_ms=0,
        response_text="",
        input_tokens=0,
        output_tokens=10,
    )

    assert result.tokens_per_second == 0
