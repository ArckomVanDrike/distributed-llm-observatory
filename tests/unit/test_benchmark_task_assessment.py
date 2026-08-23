from datetime import datetime, timezone

import pytest

from observer.core.benchmark_task_assessment import (
    BenchmarkTaskAssessmentRunner,
)
from observer.core.benchmark_task_runner import BenchmarkTaskRunner
from observer.core.task_evaluator import TaskEvaluator
from observer.core.task_evaluator_registry import TaskEvaluatorRegistry
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
from schemas.evaluation import (
    TaskCriterionEvaluation,
    TaskEvaluation,
    TaskEvaluationMethod,
)
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


class MockAssessmentAdapter(SUTAdapter):
    manifest = TargetManifest(
        target_id="mock-agent",
        display_name="Mock Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
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


class FailingCriterionEvaluator(TaskEvaluator):
    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
    ) -> TaskEvaluation:
        return TaskEvaluation(
            task_id=benchmark.task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion=benchmark.success_criteria[0].description,
                    passed=False,
                    evidence="Expected verification did not pass.",
                ),
            ],
            passed=False,
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
            TargetCapability.CODE_EXECUTION,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="tests-pass",
                description="All tests pass.",
            ),
        ],
    )


def build_runner(
    evaluator: TaskEvaluator,
) -> BenchmarkTaskAssessmentRunner:
    task_runner = BenchmarkTaskRunner(
        MockAssessmentAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "test-evaluator-v0-1",
        evaluator,
    )

    return BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )


def test_assessment_combines_execution_and_evaluation():
    runner = build_runner(
        FailingCriterionEvaluator(),
    )

    assessed = runner.run(build_task())

    assert assessed.run.benchmark.task_id == "agent-coding-001"
    assert assessed.run.observation.result.task_completed is True
    assert assessed.evaluation.passed is False


def test_assessment_preserves_execution_and_evaluation_as_distinct_signals():
    runner = build_runner(
        FailingCriterionEvaluator(),
    )

    assessed = runner.run(build_task())

    assert assessed.run.observation.result.task_completed is True
    assert assessed.evaluation.criteria[0].passed is False


def test_assessment_passes_metadata_to_execution():
    runner = build_runner(
        FailingCriterionEvaluator(),
    )

    assessed = runner.run(
        build_task(),
        metadata={
            "experiment_id": "exp-001",
        },
    )

    assert assessed.run.observation.request.metadata == {
        "experiment_id": "exp-001",
    }


def test_assessment_rejects_evaluation_for_different_task():
    class WrongTaskEvaluator(TaskEvaluator):
        def evaluate(
            self,
            benchmark: BenchmarkTask,
            result: SUTExecutionResult,
        ) -> TaskEvaluation:
            return TaskEvaluation(
                task_id="different-task",
                method=TaskEvaluationMethod.DETERMINISTIC,
                criteria=[
                    TaskCriterionEvaluation(
                        criterion="All tests pass.",
                        passed=True,
                    ),
                ],
                passed=True,
            )

    runner = build_runner(
        WrongTaskEvaluator(),
    )

    with pytest.raises(
        ValueError,
        match="task_id",
    ):
        runner.run(build_task())
