from datetime import datetime, timezone

from observer.core.task_evaluator import TaskEvaluator
from observer.core.task_evidence import TaskCriterionEvidence
from observer.sut.base import (
    SUTExecutionContext,
    SUTExecutionResult,
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
from schemas.target import TargetCapability


class MockTaskEvaluator(TaskEvaluator):
    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence: tuple[TaskCriterionEvidence, ...] | None = None,
    ) -> TaskEvaluation:
        return TaskEvaluation(
            task_id=benchmark.task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion=criterion.description,
                    passed=result.task_completed,
                    evidence="mock evaluator",
                )
                for criterion in benchmark.success_criteria
            ],
            passed=result.task_completed,
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


def build_result() -> SUTExecutionResult:
    now = datetime.now(timezone.utc)

    context = SUTExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="agent-coding-001",
        target_id="mock-agent",
    )

    return SUTExecutionResult(
        context=context,
        started_at_utc=now,
        finished_at_utc=now,
        latency_ms=0.0,
        task_completed=True,
        output_text="done",
    )


def test_task_evaluator_produces_normalized_assessment():
    evaluator = MockTaskEvaluator()

    evaluation = evaluator.evaluate(
        build_task(),
        build_result(),
    )

    assert evaluation.task_id == "agent-coding-001"
    assert evaluation.passed is True
    assert evaluation.criteria[0].passed is True


def test_task_evaluator_is_abstract_contract():
    assert TaskEvaluator.__abstractmethods__ == {
        "evaluate",
    }
