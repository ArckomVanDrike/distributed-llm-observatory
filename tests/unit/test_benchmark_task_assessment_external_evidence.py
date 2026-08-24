from datetime import datetime, timezone

from observer.core.benchmark_task_assessment import (
    BenchmarkTaskAssessmentRunner,
)
from observer.core.benchmark_task_runner import BenchmarkTaskRunner
from observer.core.task_evaluator import TaskEvaluator
from observer.core.task_evaluator_registry import TaskEvaluatorRegistry
from observer.core.task_evidence import TaskCriterionEvidence
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


class MockAdapter(SUTAdapter):
    manifest = TargetManifest(
        target_id="mock-agent",
        display_name="Mock Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
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
        )


class ExternalEvidenceEvaluator(TaskEvaluator):
    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence: tuple[TaskCriterionEvidence, ...] | None = None,
    ) -> TaskEvaluation:
        assert evidence is not None

        item = evidence[0]

        return TaskEvaluation(
            task_id=benchmark.task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion=benchmark.success_criteria[0].description,
                    passed=item.passed,
                    evidence=item.evidence,
                ),
            ],
            passed=item.passed,
        )


def test_assessment_passes_external_evidence_to_evaluator():
    task = BenchmarkTask(
        task_id="agent-evidence-001",
        benchmark_version="0.1",
        evaluator_id="external-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Complete the task.",
        required_capabilities={
            TargetCapability.TEXT,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="completed",
                description="The task is complete.",
            ),
        ],
    )

    task_runner = BenchmarkTaskRunner(
        MockAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "external-evidence-v0-1",
        ExternalEvidenceEvaluator(),
    )

    runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    assessed = runner.run(
        task,
        evidence=(
            TaskCriterionEvidence(
                criterion_id="completed",
                passed=True,
                evidence="Observed by harness.",
            ),
        ),
    )

    assert assessed.evaluation.passed is True
    assert (
        assessed.evaluation.criteria[0].evidence
        == "Observed by harness."
    )
