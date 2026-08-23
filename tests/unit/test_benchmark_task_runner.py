from datetime import datetime, timezone

import pytest

from observer.core.benchmark_task_runner import BenchmarkTaskRunner
from observer.sut.base import (
    SUTAdapter,
    SUTExecutionContext,
    SUTExecutionResult,
    SUTRequest,
)
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkSuccessCriterion,
    BenchmarkTask,
)
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


class MockTaskAdapter(SUTAdapter):
    manifest = TargetManifest(
        target_id="mock-agent",
        display_name="Mock Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.FILESYSTEM,
            TargetCapability.CODE_EXECUTION,
        },
    )

    def execute(
        self,
        context: SUTExecutionContext,
        request: SUTRequest,
    ) -> SUTExecutionResult:
        now = datetime.now(timezone.utc)

        return SUTExecutionResult(
            context=context,
            started_at_utc=now,
            finished_at_utc=now,
            latency_ms=0.0,
            task_completed=True,
            output_text="done",
        )


def build_task() -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-coding-001",
        benchmark_version="0.1",
        evaluator_id="test-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.CODING,
        difficulty=BenchmarkDifficulty.MEDIUM,
        task="Fix the failing tests.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.FILESYSTEM,
            TargetCapability.CODE_EXECUTION,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="tests-pass",
                description="All tests pass.",
            ),
        ],
        fixture_id="repo-python-bug-001",
    )


def test_benchmark_task_runner_executes_compatible_task():
    runner = BenchmarkTaskRunner(
        MockTaskAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    run = runner.run(build_task())

    assert run.benchmark.task_id == "agent-coding-001"
    assert run.observation.context.target_id == "mock-agent"
    assert run.observation.context.task_id == "agent-coding-001"
    assert run.observation.result.task_completed is True


def test_benchmark_task_runner_builds_normalized_request():
    runner = BenchmarkTaskRunner(
        MockTaskAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    run = runner.run(
        build_task(),
        metadata={
            "experiment_id": "exp-001",
        },
    )

    assert run.observation.request.task == "Fix the failing tests."
    assert run.observation.request.metadata == {
        "experiment_id": "exp-001",
    }


def test_benchmark_task_runner_rejects_incompatible_target():
    class TextOnlyAdapter(MockTaskAdapter):
        manifest = TargetManifest(
            target_id="text-agent",
            display_name="Text Agent",
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        )

    runner = BenchmarkTaskRunner(
        TextOnlyAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    with pytest.raises(
        ValueError,
        match="not compatible",
    ):
        runner.run(build_task())


def test_benchmark_task_runner_validates_observer_identity():
    with pytest.raises(
        ValueError,
        match="observer_id",
    ):
        BenchmarkTaskRunner(
            MockTaskAdapter(),
            observer_id=" ",
            region_code="CL-Los-Lagos",
        )


def test_benchmark_task_runner_validates_region():
    with pytest.raises(
        ValueError,
        match="region_code",
    ):
        BenchmarkTaskRunner(
            MockTaskAdapter(),
            observer_id="observer-test",
            region_code=" ",
        )
