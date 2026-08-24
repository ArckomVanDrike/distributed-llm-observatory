from datetime import datetime, timezone

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
from schemas.target import TargetCapability


def test_deterministic_evaluator_uses_external_evidence():
    task = BenchmarkTask(
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
        ],
    )

    now = datetime.now(timezone.utc)

    result = SUTExecutionResult(
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

    evidence = (
        TaskCriterionEvidence(
            criterion_id="tests-pass",
            passed=True,
            evidence="Observed externally: tests pass.",
        ),
    )

    evaluation = DeterministicTaskEvaluator().evaluate(
        task,
        result,
        evidence=evidence,
    )

    assert evaluation.passed is True
    assert (
        evaluation.criteria[0].evidence
        == "Observed externally: tests pass."
    )
