from datetime import datetime, timezone

from observer.core.action_gateway import ObservedActionCall
from observer.core.benchmark_task_assessment import (
    BenchmarkTaskAssessmentRunner,
)
from observer.core.benchmark_task_runner import BenchmarkTaskRunner
from observer.core.default_task_evaluator_registry import (
    build_default_task_evaluator_registry,
)
from observer.core.observed_action_evidence import (
    ObservedActionEvidenceCollector,
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
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


class ActionAdapter(SUTAdapter):
    manifest = TargetManifest(
        target_id="action-agent",
        display_name="Action Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
    )

    def __init__(
        self,
        *,
        task_completed: bool,
    ) -> None:
        self.task_completed = task_completed

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
            latency_ms=1.0,
            task_completed=self.task_completed,
        )


def make_task() -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-action-assessment-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Call record_item exactly once.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="tool-called",
                description="At least one tool call was observed.",
            ),
            BenchmarkSuccessCriterion(
                criterion_id="tool-name-match",
                description="The observed tool name matches.",
            ),
            BenchmarkSuccessCriterion(
                criterion_id="tool-arguments-match",
                description="The observed arguments match.",
            ),
            BenchmarkSuccessCriterion(
                criterion_id="tool-call-count-match",
                description="The observed call count matches.",
            ),
        ],
        available_tools=[
            {
                "tool_name": "record_item",
                "description": "Record one item.",
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
        ],
        expected_action={
            "tool_name": "record_item",
            "arguments": {
                "name": "delta",
                "count": 4,
            },
            "call_count": 1,
        },
    )


def run_assessment(
    *,
    task_completed: bool,
    calls: tuple[ObservedActionCall, ...],
):
    task = make_task()

    task_runner = BenchmarkTaskRunner(
        ActionAdapter(
            task_completed=task_completed,
        ),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=build_default_task_evaluator_registry(),
    )

    assert task.expected_action is not None

    return runner.run(
        task,
        evidence_collector=(
            ObservedActionEvidenceCollector(
                expected_action=task.expected_action,
                calls_provider=lambda: calls,
            )
        ),
    )


def test_correct_observed_action_passes_when_sut_reports_incomplete():
    assessed = run_assessment(
        task_completed=False,
        calls=(
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
        ),
    )

    assert assessed.run.observation.result.task_completed is False
    assert assessed.evaluation.passed is True
    assert all(
        criterion.passed
        for criterion in assessed.evaluation.criteria
    )


def test_missing_observed_action_fails_when_sut_reports_complete():
    assessed = run_assessment(
        task_completed=True,
        calls=(),
    )

    assert assessed.run.observation.result.task_completed is True
    assert assessed.evaluation.passed is False
    assert all(
        criterion.passed is False
        for criterion in assessed.evaluation.criteria
    )
