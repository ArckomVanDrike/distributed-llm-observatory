from datetime import datetime, timezone

from observer.core.benchmark_task_assessment import (
    BenchmarkTaskAssessmentRunner,
)
from observer.core.benchmark_task_runner import BenchmarkTaskRunner
from observer.core.task_evaluator import TaskEvaluator
from observer.core.task_evaluator_registry import TaskEvaluatorRegistry
from observer.core.task_evidence import (
    TaskCriterionEvidence,
    TaskEvidenceCollector,
)
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


class OrderedAdapter(SUTAdapter):
    manifest = TargetManifest(
        target_id="ordered-agent",
        display_name="Ordered Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    def __init__(self, state: dict[str, bool]) -> None:
        self.state = state

    def execute(
        self,
        context: SUTExecutionContext,
        request: SUTRequest,
    ) -> SUTExecutionResult:
        self.state["executed"] = True
        now = datetime.now(timezone.utc)

        return SUTExecutionResult(
            context=context,
            started_at_utc=now,
            finished_at_utc=now,
            latency_ms=0.0,
            task_completed=True,
        )


class OrderedCollector(TaskEvidenceCollector):
    def __init__(self, state: dict[str, bool]) -> None:
        self.state = state

    def collect(
        self,
    ) -> tuple[TaskCriterionEvidence, ...]:
        assert self.state["executed"] is True
        self.state["collected"] = True

        return (
            TaskCriterionEvidence(
                criterion_id="completed",
                passed=True,
                evidence="Observed after execution.",
            ),
        )


class OrderedEvaluator(TaskEvaluator):
    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence: tuple[TaskCriterionEvidence, ...] | None = None,
    ) -> TaskEvaluation:
        assert evidence is not None

        return TaskEvaluation(
            task_id=benchmark.task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion=benchmark.success_criteria[0].description,
                    passed=evidence[0].passed,
                    evidence=evidence[0].evidence,
                ),
            ],
            passed=evidence[0].passed,
        )


def test_assessment_collects_evidence_after_execution():
    state = {
        "executed": False,
        "collected": False,
    }

    task = BenchmarkTask(
        task_id="agent-evidence-001",
        benchmark_version="0.1",
        evaluator_id="ordered-evaluator-v0-1",
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
        OrderedAdapter(state),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "ordered-evaluator-v0-1",
        OrderedEvaluator(),
    )

    runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    assessed = runner.run(
        task,
        evidence_collector=OrderedCollector(state),
    )

    assert state == {
        "executed": True,
        "collected": True,
    }
    assert assessed.evaluation.passed is True
    assert (
        assessed.evaluation.criteria[0].evidence
        == "Observed after execution."
    )
