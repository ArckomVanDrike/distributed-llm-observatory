from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observer.core.benchmark_task_runner import (
    BenchmarkTaskRun,
    BenchmarkTaskRunner,
)
from observer.core.task_evaluator_registry import TaskEvaluatorRegistry
from observer.core.task_evidence import (
    TaskCriterionEvidence,
    TaskEvidenceCollector,
)
from schemas.benchmark import BenchmarkTask
from schemas.evaluation import TaskEvaluation


@dataclass(frozen=True)
class AssessedBenchmarkTaskRun:
    run: BenchmarkTaskRun
    evaluation: TaskEvaluation


class BenchmarkTaskAssessmentRunner:
    """
    Executes a benchmark task and evaluates the resulting SUT observation.
    """

    def __init__(
        self,
        *,
        task_runner: BenchmarkTaskRunner,
        registry: TaskEvaluatorRegistry,
    ) -> None:
        self.task_runner = task_runner
        self.registry = registry

    def run(
        self,
        benchmark: BenchmarkTask,
        *,
        metadata: dict[str, Any] | None = None,
        evidence: tuple[TaskCriterionEvidence, ...] | None = None,
        evidence_collector: TaskEvidenceCollector | None = None,
    ) -> AssessedBenchmarkTaskRun:
        if evidence is not None and evidence_collector is not None:
            raise ValueError(
                "Provide either evidence or evidence_collector, not both."
            )

        run = self.task_runner.run(
            benchmark,
            metadata=metadata,
        )

        if evidence_collector is not None:
            evidence = evidence_collector.collect()

        evaluator = self.registry.resolve(benchmark)

        if evidence is None:
            evaluation = evaluator.evaluate(
                benchmark,
                run.observation.result,
            )
        else:
            evaluation = evaluator.evaluate(
                benchmark,
                run.observation.result,
                evidence=evidence,
            )

        if evaluation.task_id != benchmark.task_id:
            raise ValueError(
                "Task evaluation task_id does not match "
                f"the benchmark task_id: "
                f"evaluation={evaluation.task_id!r}, "
                f"benchmark={benchmark.task_id!r}."
            )

        return AssessedBenchmarkTaskRun(
            run=run,
            evaluation=evaluation,
        )
