from datetime import datetime, timezone

import pytest

from observer.core.deterministic_task_evaluator import (
    DeterministicTaskEvaluator,
)
from observer.core.task_evidence import (
    TaskCriterionEvidence,
)
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
from schemas.evaluation import TaskEvaluationMethod
from schemas.target import TargetCapability


def build_task() -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-coding-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
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
            BenchmarkSuccessCriterion(
                criterion_id="no-unrelated-changes",
                description="No unrelated files are modified.",
            ),
        ],
    )


def build_result() -> SUTExecutionResult:
    now = datetime.now(timezone.utc)

    return SUTExecutionResult(
        context=SUTExecutionContext(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
            benchmark_version="0.1",
            task_id="agent-coding-001",
            target_id="mock-agent",
        ),
        started_at_utc=now,
        finished_at_utc=now,
        latency_ms=0.0,
        task_completed=True,
    )


def test_deterministic_evaluator_maps_structured_evidence():
    evaluator = DeterministicTaskEvaluator()

    evaluation = evaluator.evaluate(
        build_task(),
        build_result(),
        evidence=(
            TaskCriterionEvidence(
                criterion_id="tests-pass",
                passed=True,
                evidence="pytest: 42 passed",
            ),
            TaskCriterionEvidence(
                criterion_id="no-unrelated-changes",
                passed=True,
                evidence="git diff clean outside expected files",
            ),
        ),
    )

    assert evaluation.method is TaskEvaluationMethod.DETERMINISTIC
    assert evaluation.passed is True
    assert evaluation.criteria[0].criterion == "All tests pass."
    assert evaluation.criteria[0].evidence == "pytest: 42 passed"


def test_deterministic_evaluator_preserves_failed_criterion():
    evaluator = DeterministicTaskEvaluator()

    evaluation = evaluator.evaluate(
        build_task(),
        build_result(),
        evidence=(
            TaskCriterionEvidence(
                criterion_id="tests-pass",
                passed=False,
                evidence="pytest: 1 failed",
            ),
            TaskCriterionEvidence(
                criterion_id="no-unrelated-changes",
                passed=True,
            ),
        ),
    )

    assert evaluation.passed is False
    assert evaluation.criteria[0].passed is False


def test_deterministic_evaluator_rejects_missing_evidence():
    evaluator = DeterministicTaskEvaluator()

    with pytest.raises(
        ValueError,
        match="Missing criterion evidence",
    ):
        evaluator.evaluate(
            build_task(),
            build_result(),
            evidence=(
                TaskCriterionEvidence(
                    criterion_id="tests-pass",
                    passed=True,
                ),
            ),
        )


def test_deterministic_evaluator_rejects_duplicate_evidence():
    evaluator = DeterministicTaskEvaluator()

    with pytest.raises(
        ValueError,
        match="Duplicate criterion evidence",
    ):
        evaluator.evaluate(
            build_task(),
            build_result(),
            evidence=(
                TaskCriterionEvidence(
                    criterion_id="tests-pass",
                    passed=True,
                ),
                TaskCriterionEvidence(
                    criterion_id="tests-pass",
                    passed=True,
                ),
                TaskCriterionEvidence(
                    criterion_id="no-unrelated-changes",
                    passed=True,
                ),
            ),
        )


def test_deterministic_evaluator_requires_external_evidence():
    evaluator = DeterministicTaskEvaluator()

    with pytest.raises(
        ValueError,
        match="external criterion evidence",
    ):
        evaluator.evaluate(
            build_task(),
            build_result(),
        )
