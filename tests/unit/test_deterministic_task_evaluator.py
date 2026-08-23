from datetime import datetime, timezone

import pytest

from observer.core.deterministic_task_evaluator import (
    DeterministicTaskEvaluator,
)
from observer.sut.base import (
    SUTCriterionEvidence,
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


def build_result(
    evidence: tuple[SUTCriterionEvidence, ...],
) -> SUTExecutionResult:
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
        criterion_evidence=evidence,
    )


def test_deterministic_evaluator_maps_structured_evidence():
    evaluator = DeterministicTaskEvaluator()

    evaluation = evaluator.evaluate(
        build_task(),
        build_result(
            (
                SUTCriterionEvidence(
                    criterion_id="tests-pass",
                    passed=True,
                    evidence="pytest: 42 passed",
                ),
                SUTCriterionEvidence(
                    criterion_id="no-unrelated-changes",
                    passed=True,
                    evidence="git diff clean outside expected files",
                ),
            )
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
        build_result(
            (
                SUTCriterionEvidence(
                    criterion_id="tests-pass",
                    passed=False,
                    evidence="pytest: 1 failed",
                ),
                SUTCriterionEvidence(
                    criterion_id="no-unrelated-changes",
                    passed=True,
                ),
            )
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
            build_result(
                (
                    SUTCriterionEvidence(
                        criterion_id="tests-pass",
                        passed=True,
                    ),
                )
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
            build_result(
                (
                    SUTCriterionEvidence(
                        criterion_id="tests-pass",
                        passed=True,
                    ),
                    SUTCriterionEvidence(
                        criterion_id="tests-pass",
                        passed=True,
                    ),
                    SUTCriterionEvidence(
                        criterion_id="no-unrelated-changes",
                        passed=True,
                    ),
                )
            ),
        )
