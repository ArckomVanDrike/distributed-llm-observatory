from __future__ import annotations

from datetime import datetime, timezone

from observer.core.benchmark_compatibility import (
    target_supports_task,
)
from observer.core.benchmark_task_assessment import (
    BenchmarkTaskAssessmentRunner,
)
from observer.core.task_evidence import TaskEvidenceCollector
from schemas.agent_lab import (
    AgentTestSession,
    AgentTestSessionStatus,
    AgentTestTaskResult,
    AgentTestTaskSelection,
    AgentTestTaskSelectionStatus,
)
from schemas.benchmark import BenchmarkTask


class AgentTestSessionRunner:
    def __init__(
        self,
        *,
        assessment_runner: BenchmarkTaskAssessmentRunner,
    ) -> None:
        self.assessment_runner = assessment_runner

    def run(
        self,
        *,
        suite_id: str,
        suite_version: str,
        tasks: list[BenchmarkTask],
        evidence_collectors: dict[
            str,
            TaskEvidenceCollector,
        ] | None = None,
    ) -> AgentTestSession:
        started_at_utc = datetime.now(timezone.utc)

        target = (
            self.assessment_runner
            .task_runner
            .adapter
            .manifest
        )

        collectors = evidence_collectors or {}

        task_ids = [
            task.task_id
            for task in tasks
        ]

        if len(task_ids) != len(set(task_ids)):
            raise ValueError(
                "Duplicate task_id in agent test suite."
            )

        selections: list[AgentTestTaskSelection] = []
        results: list[AgentTestTaskResult] = []

        for task in tasks:
            if not task.enabled:
                selections.append(
                    AgentTestTaskSelection(
                        task_id=task.task_id,
                        benchmark_version=task.benchmark_version,
                        status=(
                            AgentTestTaskSelectionStatus.DISABLED
                        ),
                    )
                )
                continue

            if not target_supports_task(target, task):
                selections.append(
                    AgentTestTaskSelection(
                        task_id=task.task_id,
                        benchmark_version=task.benchmark_version,
                        status=(
                            AgentTestTaskSelectionStatus.INCOMPATIBLE
                        ),
                        missing_capabilities=(
                            task.required_capabilities
                            - target.capabilities
                        ),
                        family_mismatch=(
                            task.family.value
                            != target.target_type.value
                        ),
                    )
                )
                continue

            selections.append(
                AgentTestTaskSelection(
                    task_id=task.task_id,
                    benchmark_version=task.benchmark_version,
                    status=(
                        AgentTestTaskSelectionStatus.SELECTED
                    ),
                )
            )

            assessed = self.assessment_runner.run(
                task,
                evidence_collector=collectors.get(
                    task.task_id,
                ),
            )

            execution = assessed.run.observation.result

            results.append(
                AgentTestTaskResult(
                    task_id=assessed.run.benchmark.task_id,
                    benchmark_version=(
                        assessed.run.benchmark.benchmark_version
                    ),
                    started_at_utc=execution.started_at_utc,
                    finished_at_utc=execution.finished_at_utc,
                    latency_ms=execution.latency_ms,
                    task_completed=execution.task_completed,
                    output_text=execution.output_text,
                    retry_count=execution.retry_count,
                    human_intervention_count=(
                        execution.human_intervention_count
                    ),
                    error_type=execution.error_type,
                    metrics=dict(execution.metrics),
                    evaluation=assessed.evaluation,
                )
            )

        completed_at_utc = datetime.now(timezone.utc)

        return AgentTestSession(
            target=target,
            suite_id=suite_id,
            suite_version=suite_version,
            status=AgentTestSessionStatus.COMPLETED,
            started_at_utc=started_at_utc,
            completed_at_utc=completed_at_utc,
            selections=selections,
            results=results,
        )
