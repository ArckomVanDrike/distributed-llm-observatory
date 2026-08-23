from pathlib import Path

from observer.core.benchmark_task_assessment import (
    BenchmarkTaskAssessmentRunner,
)
from observer.core.benchmark_task_runner import BenchmarkTaskRunner
from observer.core.deterministic_task_evaluator import (
    DeterministicTaskEvaluator,
)
from observer.core.task_bank import TaskBank
from observer.core.task_evaluator_registry import TaskEvaluatorRegistry
from observer.sut.local_filesystem import LocalFilesystemSUTAdapter


def test_canonical_filesystem_task_runs_end_to_end(
    tmp_path: Path,
):
    task = TaskBank(
        Path("benchmark/tasks"),
    ).load_enabled()[0]

    adapter = LocalFilesystemSUTAdapter(
        tmp_path,
    )

    task_runner = BenchmarkTaskRunner(
        adapter,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    registry = TaskEvaluatorRegistry()
    registry.register(
        "deterministic-evidence-v0-1",
        DeterministicTaskEvaluator(),
    )

    assessment_runner = BenchmarkTaskAssessmentRunner(
        task_runner=task_runner,
        registry=registry,
    )

    assessed = assessment_runner.run(
        task,
        metadata={
            "operation": "write_file",
            "path": "dllo-probe.txt",
            "content": "DLLO-AGENT-SMOKE-001",
        },
    )

    assert assessed.run.observation.result.task_completed is True
    assert assessed.evaluation.passed is True
    assert all(
        criterion.passed
        for criterion in assessed.evaluation.criteria
    )

    assert (
        tmp_path / "dllo-probe.txt"
    ).read_text(encoding="utf-8") == "DLLO-AGENT-SMOKE-001"
