
import pytest

from observer.core.task_evaluator import TaskEvaluator
from observer.core.task_evaluator_registry import TaskEvaluatorRegistry
from observer.sut.base import (
    SUTExecutionResult,
)
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkTask,
)
from schemas.evaluation import (
    TaskCriterionEvaluation,
    TaskEvaluation,
    TaskEvaluationMethod,
)
from schemas.target import TargetCapability


class MockRegistryEvaluator(TaskEvaluator):
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
                    criterion=criterion,
                    passed=True,
                )
                for criterion in benchmark.success_criteria
            ],
            passed=True,
        )


def build_task(
    evaluator_id: str = "mock-evaluator-v0-1",
) -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-coding-001",
        benchmark_version="0.1",
        evaluator_id=evaluator_id,
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.CODING,
        difficulty=BenchmarkDifficulty.MEDIUM,
        task="Fix the failing tests.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.CODE_EXECUTION,
        },
        success_criteria=[
            "All tests pass.",
        ],
    )


def test_registry_resolves_evaluator_declared_by_benchmark():
    evaluator = MockRegistryEvaluator()
    registry = TaskEvaluatorRegistry()

    registry.register(
        "mock-evaluator-v0-1",
        evaluator,
    )

    assert registry.resolve(build_task()) is evaluator


def test_registry_rejects_unknown_evaluator():
    registry = TaskEvaluatorRegistry()

    with pytest.raises(
        KeyError,
        match="missing-evaluator-v0-1",
    ):
        registry.resolve(
            build_task(
                evaluator_id="missing-evaluator-v0-1",
            )
        )


def test_registry_rejects_duplicate_registration():
    registry = TaskEvaluatorRegistry()

    registry.register(
        "mock-evaluator-v0-1",
        MockRegistryEvaluator(),
    )

    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        registry.register(
            "mock-evaluator-v0-1",
            MockRegistryEvaluator(),
        )
