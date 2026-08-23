import json
from pathlib import Path

import pytest

from observer.core.task_bank import TaskBank, TaskBankError
from schemas.benchmark import (
    BenchmarkFamily,
    BenchmarkTask,
)


def write_task(path: Path, **overrides) -> None:
    data = {
        "schema_version": "0.1",
        "task_id": "agent-coding-001",
        "benchmark_version": "0.1",
        "evaluator_id": "deterministic-evidence-v0-1",
        "family": "agent",
        "category": "coding",
        "difficulty": "medium",
        "task": "Fix the failing tests.",
        "required_capabilities": [
            "text",
            "code_execution",
        ],
        "success_criteria": [
            {
                "criterion_id": "tests-pass",
                "description": "All tests pass.",
            }
        ],
        "fixture_id": "repo-python-bug-001",
        "enabled": True,
    }

    data.update(overrides)
    path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )


def test_task_bank_loads_valid_task(tmp_path):
    task_file = tmp_path / "agent-coding-001.json"
    write_task(task_file)

    bank = TaskBank(tmp_path)
    tasks = bank.load_all()

    assert len(tasks) == 1
    assert isinstance(tasks[0], BenchmarkTask)
    assert tasks[0].task_id == "agent-coding-001"
    assert tasks[0].family is BenchmarkFamily.AGENT


def test_task_bank_filters_disabled_tasks(tmp_path):
    write_task(
        tmp_path / "agent-coding-001.json",
        enabled=False,
    )

    bank = TaskBank(tmp_path)

    assert bank.load_enabled() == []


def test_task_bank_rejects_invalid_json(tmp_path):
    task_file = tmp_path / "broken.json"
    task_file.write_text("{broken", encoding="utf-8")

    bank = TaskBank(tmp_path)

    with pytest.raises(TaskBankError, match="Invalid JSON"):
        bank.load_all()


def test_task_bank_rejects_invalid_schema(tmp_path):
    task_file = tmp_path / "invalid.json"
    write_task(
        task_file,
        family="foundation_model",
    )

    bank = TaskBank(tmp_path)

    with pytest.raises(
        TaskBankError,
        match="Invalid benchmark task",
    ):
        bank.load_all()


def test_task_bank_rejects_duplicate_task_ids(tmp_path):
    write_task(
        tmp_path / "first.json",
        task_id="duplicate-001",
    )
    write_task(
        tmp_path / "second.json",
        task_id="duplicate-001",
    )

    bank = TaskBank(tmp_path)

    with pytest.raises(
        TaskBankError,
        match="Duplicate task_id",
    ):
        bank.load_all()


def test_task_bank_rejects_missing_directory(tmp_path):
    bank = TaskBank(
        tmp_path / "missing",
    )

    with pytest.raises(
        TaskBankError,
        match="does not exist",
    ):
        bank.load_all()


def test_repository_task_bank_contains_valid_tasks():
    bank = TaskBank(Path("benchmark/tasks"))

    tasks = bank.load_enabled()

    assert tasks
    assert all(task.enabled for task in tasks)
    assert all(
        task.family
        in {
            BenchmarkFamily.AGENT,
            BenchmarkFamily.AI_SYSTEM,
        }
        for task in tasks
    )
