from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from schemas.benchmark import BenchmarkTask


class TaskBankError(Exception):
    """Raised when the benchmark task bank cannot be loaded safely."""


class TaskBank:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load_task(self, path: Path) -> BenchmarkTask:
        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise TaskBankError(
                f"Unable to read task file: {path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise TaskBankError(
                f"Invalid JSON in task file: {path}"
            ) from exc

        try:
            return BenchmarkTask.model_validate(raw_data)
        except ValidationError as exc:
            raise TaskBankError(
                f"Invalid benchmark task: {path}"
            ) from exc

    def load_all(self) -> list[BenchmarkTask]:
        if not self.root.exists():
            raise TaskBankError(
                f"Task bank directory does not exist: {self.root}"
            )

        tasks = [
            self.load_task(path)
            for path in sorted(self.root.rglob("*.json"))
        ]

        task_ids = [
            task.task_id
            for task in tasks
        ]

        if len(task_ids) != len(set(task_ids)):
            raise TaskBankError(
                "Duplicate task_id detected in task bank."
            )

        return tasks

    def load_enabled(self) -> list[BenchmarkTask]:
        return [
            task
            for task in self.load_all()
            if task.enabled
        ]
