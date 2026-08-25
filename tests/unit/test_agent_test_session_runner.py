from datetime import datetime, timezone

import pytest

from observer.core.agent_test_session_runner import (
    AgentTestSessionRunner,
)
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
from schemas.agent_lab import (
    AgentTestSessionStatus,
    AgentTestTaskSelectionStatus,
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


class HappyPathAdapter(SUTAdapter):
    manifest = TargetManifest(
        target_id="happy-agent",
        display_name="Happy Agent",
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
        started_at = datetime(
            2026,
            8,
            24,
            12,
            0,
            tzinfo=timezone.utc,
        )
        finished_at = datetime(
            2026,
            8,
            24,
            12,
            0,
            1,
            tzinfo=timezone.utc,
        )

        return SUTExecutionResult(
            context=context,
            started_at_utc=started_at,
            finished_at_utc=finished_at,
            latency_ms=1000.0,
            task_completed=True,
            output_text="Task completed.",
            retry_count=0,
            human_intervention_count=0,
            metrics={
                "example_metric": 1,
            },
        )


class PassingEvaluator(TaskEvaluator):
    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence=None,
    ) -> TaskEvaluation:
        return TaskEvaluation(
            task_id=benchmark.task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion=(
                        benchmark.success_criteria[0].description
                    ),
                    passed=True,
                    evidence="Observed successful execution.",
                ),
            ],
            passed=True,
        )


def test_session_runner_executes_compatible_task():
    task = BenchmarkTask(
        task_id="agent-session-001",
        benchmark_version="0.1",
        evaluator_id="passing-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Complete the test task.",
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
        HappyPathAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "passing-evaluator-v0-1",
        PassingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    session = runner.run(
        suite_id="agent-core",
        suite_version="0.1",
        tasks=[task],
    )

    assert session.status is AgentTestSessionStatus.COMPLETED
    assert session.target == HappyPathAdapter.manifest
    assert session.observer_id == "observer-test"
    assert session.region_code == "CL-Los-Lagos"

    assert len(session.selections) == 1
    assert (
        session.selections[0].status
        is AgentTestTaskSelectionStatus.SELECTED
    )
    assert session.selections[0].task_id == task.task_id

    assert len(session.results) == 1

    result = session.results[0]

    assert result.task_id == task.task_id
    assert result.benchmark_version == "0.1"
    assert result.task_completed is True
    assert result.output_text == "Task completed."
    assert result.latency_ms == 1000.0
    assert result.metrics == {
        "example_metric": 1,
    }
    assert result.evaluation.passed is True


def test_session_runner_records_incompatible_task():
    task = BenchmarkTask(
        task_id="agent-filesystem-required",
        benchmark_version="0.1",
        evaluator_id="passing-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Write a file in the workspace.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.FILESYSTEM,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="file-created",
                description="The requested file exists.",
            ),
        ],
    )

    task_runner = BenchmarkTaskRunner(
        HappyPathAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "passing-evaluator-v0-1",
        PassingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    session = runner.run(
        suite_id="agent-core",
        suite_version="0.1",
        tasks=[task],
    )

    assert session.status is AgentTestSessionStatus.COMPLETED
    assert session.results == []

    assert len(session.selections) == 1

    selection = session.selections[0]

    assert selection.task_id == task.task_id
    assert (
        selection.status
        is AgentTestTaskSelectionStatus.INCOMPATIBLE
    )
    assert selection.missing_capabilities == {
        TargetCapability.FILESYSTEM,
    }


def test_session_runner_records_disabled_task():
    task = BenchmarkTask(
        task_id="agent-disabled-001",
        benchmark_version="0.1",
        evaluator_id="passing-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="This task is disabled.",
        required_capabilities={
            TargetCapability.TEXT,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="completed",
                description="The task is complete.",
            ),
        ],
        enabled=False,
    )

    task_runner = BenchmarkTaskRunner(
        HappyPathAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "passing-evaluator-v0-1",
        PassingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    session = runner.run(
        suite_id="agent-core",
        suite_version="0.1",
        tasks=[task],
    )

    assert session.status is AgentTestSessionStatus.COMPLETED
    assert session.results == []

    assert len(session.selections) == 1

    selection = session.selections[0]

    assert selection.task_id == task.task_id
    assert (
        selection.status
        is AgentTestTaskSelectionStatus.DISABLED
    )
    assert selection.missing_capabilities == set()


class FailingEvaluator(TaskEvaluator):
    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence=None,
    ) -> TaskEvaluation:
        return TaskEvaluation(
            task_id=benchmark.task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion=(
                        benchmark.success_criteria[0].description
                    ),
                    passed=False,
                    evidence="Success criterion was not satisfied.",
                ),
            ],
            passed=False,
        )


def test_failed_task_evaluation_does_not_fail_session():
    task = BenchmarkTask(
        task_id="agent-session-failing",
        benchmark_version="0.1",
        evaluator_id="failing-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Complete the test task.",
        required_capabilities={
            TargetCapability.TEXT,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="completed",
                description="The task satisfies the criterion.",
            ),
        ],
    )

    task_runner = BenchmarkTaskRunner(
        HappyPathAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "failing-evaluator-v0-1",
        FailingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    session = runner.run(
        suite_id="agent-core",
        suite_version="0.1",
        tasks=[task],
    )

    assert session.status is AgentTestSessionStatus.COMPLETED
    assert len(session.results) == 1

    result = session.results[0]

    assert result.task_completed is True
    assert result.evaluation.passed is False
    assert (
        result.evaluation.criteria[0].passed
        is False
    )


class TelemetryAdapter(SUTAdapter):
    manifest = TargetManifest(
        target_id="telemetry-agent",
        display_name="Telemetry Agent",
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
        started_at = datetime(
            2026,
            8,
            24,
            12,
            0,
            tzinfo=timezone.utc,
        )
        finished_at = datetime(
            2026,
            8,
            24,
            12,
            0,
            2,
            tzinfo=timezone.utc,
        )

        return SUTExecutionResult(
            context=context,
            started_at_utc=started_at,
            finished_at_utc=finished_at,
            latency_ms=2000.0,
            task_completed=False,
            output_text=None,
            retry_count=2,
            human_intervention_count=1,
            error_type="execution_timeout",
            metrics={
                "tool_calls": 3,
                "workspace_bytes": 128,
            },
        )


def test_session_runner_preserves_execution_telemetry():
    task = BenchmarkTask(
        task_id="agent-telemetry-001",
        benchmark_version="0.1",
        evaluator_id="failing-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Complete the telemetry test.",
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
        TelemetryAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "failing-evaluator-v0-1",
        FailingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    session = runner.run(
        suite_id="agent-core",
        suite_version="0.1",
        tasks=[task],
    )

    assert session.status is AgentTestSessionStatus.COMPLETED
    assert len(session.results) == 1

    result = session.results[0]

    assert result.latency_ms == 2000.0
    assert result.task_completed is False
    assert result.output_text is None
    assert result.retry_count == 2
    assert result.human_intervention_count == 1
    assert result.error_type == "execution_timeout"
    assert result.metrics == {
        "tool_calls": 3,
        "workspace_bytes": 128,
    }
    assert result.evaluation.passed is False


class EvidenceAwareEvaluator(TaskEvaluator):
    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence=None,
    ) -> TaskEvaluation:
        assert evidence is not None
        assert len(evidence) == 1

        return TaskEvaluation(
            task_id=benchmark.task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion=(
                        benchmark.success_criteria[0].description
                    ),
                    passed=evidence[0].passed,
                    evidence=evidence[0].evidence,
                ),
            ],
            passed=evidence[0].passed,
        )


class RecordingEvidenceCollector:
    def __init__(self, state: dict[str, int]) -> None:
        self.state = state

    def collect(self):
        from observer.core.task_evidence import (
            TaskCriterionEvidence,
        )

        self.state["calls"] += 1

        return (
            TaskCriterionEvidence(
                criterion_id="completed",
                passed=True,
                evidence="Task-specific external evidence.",
            ),
        )


def test_session_runner_routes_task_specific_evidence_collector():
    task = BenchmarkTask(
        task_id="agent-evidence-routing-001",
        benchmark_version="0.1",
        evaluator_id="evidence-aware-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Complete the evidence test.",
        required_capabilities={
            TargetCapability.TEXT,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="completed",
                description="The task is externally verified.",
            ),
        ],
    )

    task_runner = BenchmarkTaskRunner(
        HappyPathAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "evidence-aware-v0-1",
        EvidenceAwareEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    state = {
        "calls": 0,
    }

    collector = RecordingEvidenceCollector(state)

    session = runner.run(
        suite_id="agent-core",
        suite_version="0.1",
        tasks=[task],
        evidence_collectors={
            task.task_id: collector,
        },
    )

    assert state["calls"] == 1
    assert len(session.results) == 1
    assert session.results[0].evaluation.passed is True
    assert (
        session.results[0]
        .evaluation
        .criteria[0]
        .evidence
        == "Task-specific external evidence."
    )




def test_session_runner_routes_task_specific_metadata():
    requests: list[SUTRequest] = []

    class RecordingMetadataAdapter(SUTAdapter):
        manifest = TargetManifest(
            target_id="metadata-agent",
            display_name="Metadata Agent",
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
            requests.append(request)

            now = datetime.now(timezone.utc)

            return SUTExecutionResult(
                context=context,
                started_at_utc=now,
                finished_at_utc=now,
                latency_ms=0.0,
                task_completed=True,
            )

    def make_task(task_id: str) -> BenchmarkTask:
        return BenchmarkTask(
            task_id=task_id,
            benchmark_version="0.1",
            evaluator_id="passing-evaluator-v0-1",
            family=BenchmarkFamily.AGENT,
            category=BenchmarkCategory.TECHNICAL,
            difficulty=BenchmarkDifficulty.EASY,
            task="Complete the metadata routing test.",
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

    task_a = make_task("agent-metadata-a-001")
    task_b = make_task("agent-metadata-b-001")

    task_runner = BenchmarkTaskRunner(
        RecordingMetadataAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "passing-evaluator-v0-1",
        PassingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    runner.run(
        suite_id="agent-core",
        suite_version="0.1",
        tasks=[
            task_a,
            task_b,
        ],
        task_metadata={
            task_a.task_id: {
                "dllo_tools": [
                    {
                        "name": "record_item",
                    },
                ],
            },
        },
    )

    assert len(requests) == 2
    assert requests[0].metadata == {
        "dllo_tools": [
            {
                "name": "record_item",
            },
        ],
    }
    assert requests[1].metadata is None

def test_session_runner_rejects_duplicate_task_ids():
    task = BenchmarkTask(
        task_id="agent-duplicate-001",
        benchmark_version="0.1",
        evaluator_id="passing-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Complete the duplicate test task.",
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
        HappyPathAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "passing-evaluator-v0-1",
        PassingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate task_id",
    ):
        runner.run(
            suite_id="agent-core",
            suite_version="0.1",
            tasks=[
                task,
                task,
            ],
        )


def test_session_runner_records_family_mismatch():
    task = BenchmarkTask(
        task_id="system-family-task",
        benchmark_version="0.1",
        evaluator_id="passing-evaluator-v0-1",
        family=BenchmarkFamily.AI_SYSTEM,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Complete the AI system task.",
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
        HappyPathAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "passing-evaluator-v0-1",
        PassingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    session = runner.run(
        suite_id="agent-core",
        suite_version="0.1",
        tasks=[task],
    )

    assert session.results == []
    assert len(session.selections) == 1

    selection = session.selections[0]

    assert (
        selection.status
        is AgentTestTaskSelectionStatus.INCOMPATIBLE
    )
    assert selection.missing_capabilities == set()
    assert selection.family_mismatch is True


def test_session_runner_preserves_task_order():
    tasks = [
        BenchmarkTask(
            task_id=f"agent-order-{index}",
            benchmark_version="0.1",
            evaluator_id="passing-evaluator-v0-1",
            family=BenchmarkFamily.AGENT,
            category=BenchmarkCategory.TECHNICAL,
            difficulty=BenchmarkDifficulty.EASY,
            task=f"Complete ordered task {index}.",
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
        for index in range(1, 4)
    ]

    task_runner = BenchmarkTaskRunner(
        HappyPathAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "passing-evaluator-v0-1",
        PassingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    session = runner.run(
        suite_id="agent-core",
        suite_version="0.1",
        tasks=tasks,
    )

    expected_ids = [
        "agent-order-1",
        "agent-order-2",
        "agent-order-3",
    ]

    assert [
        selection.task_id
        for selection in session.selections
    ] == expected_ids

    assert [
        result.task_id
        for result in session.results
    ] == expected_ids


class ExplodingEvaluator(TaskEvaluator):
    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence=None,
    ) -> TaskEvaluation:
        raise RuntimeError("assessment failure")


def test_session_runner_propagates_assessment_error():
    task = BenchmarkTask(
        task_id="agent-assessment-error",
        benchmark_version="0.1",
        evaluator_id="exploding-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Trigger an assessment failure.",
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
        HappyPathAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "exploding-evaluator-v0-1",
        ExplodingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    with pytest.raises(
        RuntimeError,
        match="assessment failure",
    ):
        runner.run(
            suite_id="agent-core",
            suite_version="0.1",
            tasks=[task],
        )


def test_session_runner_preserves_supplied_task_order():
    first_task = BenchmarkTask(
        task_id="agent-order-first",
        benchmark_version="0.1",
        evaluator_id="passing-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Complete the first task.",
        required_capabilities={
            TargetCapability.TEXT,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="completed",
                description="The first task is complete.",
            ),
        ],
    )

    second_task = BenchmarkTask(
        task_id="agent-order-second",
        benchmark_version="0.1",
        evaluator_id="passing-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Complete the second task.",
        required_capabilities={
            TargetCapability.TEXT,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="completed",
                description="The second task is complete.",
            ),
        ],
    )

    task_runner = BenchmarkTaskRunner(
        HappyPathAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "passing-evaluator-v0-1",
        PassingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    session = runner.run(
        suite_id="agent-core",
        suite_version="0.1",
        tasks=[
            second_task,
            first_task,
        ],
    )

    assert [
        selection.task_id
        for selection in session.selections
    ] == [
        "agent-order-second",
        "agent-order-first",
    ]

    assert [
        result.task_id
        for result in session.results
    ] == [
        "agent-order-second",
        "agent-order-first",
    ]


class ExplodingAdapter(SUTAdapter):
    manifest = TargetManifest(
        target_id="exploding-agent",
        display_name="Exploding Agent",
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
        raise RuntimeError("SUT execution failed.")


def test_session_runner_propagates_assessment_errors():
    task = BenchmarkTask(
        task_id="agent-exception-001",
        benchmark_version="0.1",
        evaluator_id="passing-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Trigger the test execution.",
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
        ExplodingAdapter(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "passing-evaluator-v0-1",
        PassingEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    runner = AgentTestSessionRunner(
        assessment_runner=assessment_runner,
    )

    with pytest.raises(
        RuntimeError,
        match="SUT execution failed",
    ):
        runner.run(
            suite_id="agent-core",
            suite_version="0.1",
            tasks=[task],
        )
