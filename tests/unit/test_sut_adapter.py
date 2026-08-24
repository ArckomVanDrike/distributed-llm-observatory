from datetime import datetime, timezone

import pytest

from observer.sut.base import (
    SUTAdapter,
    SUTExecutionContext,
    SUTExecutionResult,
    SUTRequest,
)
from observer.sut.runner import SUTRunner
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


class MockSUTAdapter(SUTAdapter):
    manifest = TargetManifest(
        target_id="mock-agent",
        display_name="Mock Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
    )

    def execute(
        self,
        context: SUTExecutionContext,
        request: SUTRequest,
    ) -> SUTExecutionResult:
        started = datetime.now(timezone.utc)

        return SUTExecutionResult(
            context=context,
            started_at_utc=started,
            finished_at_utc=started,
            latency_ms=0.0,
            task_completed=True,
            output_text="done",
            retry_count=0,
            human_intervention_count=0,
            error_type=None,
            metrics={
                "tool_calls": 2,
            },
        )


def test_sut_adapter_executes_normalized_task():
    adapter = MockSUTAdapter()

    context = SUTExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="agent-coding-001",
        target_id="mock-agent",
    )

    request = SUTRequest(
        task="Fix the failing test.",
    )

    result = adapter.execute(
        context,
        request,
    )

    assert adapter.manifest.target_type is TargetType.AGENT
    assert result.context == context
    assert result.task_completed is True
    assert result.output_text == "done"
    assert result.metrics["tool_calls"] == 2


def test_sut_context_identifies_target_not_provider():
    context = SUTExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="memory-001",
        target_id="custom-jarvis",
    )

    assert context.target_id == "custom-jarvis"
    assert not hasattr(context, "provider")
    assert not hasattr(context, "model")


def test_sut_runner_executes_matching_target():
    adapter = MockSUTAdapter()
    runner = SUTRunner(adapter)

    context = SUTExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="agent-coding-001",
        target_id="mock-agent",
    )

    request = SUTRequest(
        task="Fix the failing test.",
    )

    run = runner.run(
        context,
        request,
    )

    assert run.context == context
    assert run.request == request
    assert run.result.task_completed is True


def test_sut_runner_rejects_mismatched_target():
    adapter = MockSUTAdapter()
    runner = SUTRunner(adapter)

    context = SUTExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="agent-coding-001",
        target_id="different-agent",
    )

    with pytest.raises(
        ValueError,
        match="target does not match",
    ):
        runner.run(
            context,
            SUTRequest(
                task="Fix the failing test.",
            ),
        )
