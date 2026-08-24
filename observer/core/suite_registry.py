from __future__ import annotations

from dataclasses import dataclass

from observer.core.suite_bank import SuiteBank
from observer.core.task_bank import TaskBank
from schemas.benchmark import (
    BenchmarkHarnessProfile,
    BenchmarkSuite,
    BenchmarkTask,
)
from schemas.target import TargetManifest


class SuiteRegistryError(Exception):
    """Raised when a benchmark suite cannot be resolved safely."""


@dataclass(frozen=True)
class ResolvedBenchmarkSuite:
    suite: BenchmarkSuite
    tasks: tuple[BenchmarkTask, ...]


class SuiteRegistry:
    def __init__(
        self,
        *,
        suite_bank: SuiteBank,
        task_bank: TaskBank,
    ) -> None:
        self.suite_bank = suite_bank
        self.task_bank = task_bank

    def candidates_for_target(
        self,
        target: TargetManifest,
        *,
        harness_profile: BenchmarkHarnessProfile | None = None,
    ) -> list[BenchmarkSuite]:
        return [
            suite
            for suite in self.suite_bank.load_enabled()
            if (
                suite.family.value
                == target.target_type.value
                and (
                    harness_profile is None
                    or suite.harness_profile
                    == harness_profile
                )
            )
        ]

    def resolve_unique_for_target(
        self,
        target: TargetManifest,
        *,
        harness_profile: BenchmarkHarnessProfile,
    ) -> ResolvedBenchmarkSuite:
        candidates = self.candidates_for_target(
            target,
            harness_profile=harness_profile,
        )

        if not candidates:
            raise SuiteRegistryError(
                "No enabled benchmark suite is available "
                f"for target type {target.target_type.value!r}."
            )

        if len(candidates) > 1:
            identities = [
                (
                    suite.suite_id,
                    suite.suite_version,
                )
                for suite in candidates
            ]

            raise SuiteRegistryError(
                "Multiple enabled benchmark suites are "
                "available for target type "
                f"{target.target_type.value!r}: "
                f"{identities!r}."
            )

        suite = candidates[0]

        return self.resolve(
            suite_id=suite.suite_id,
            suite_version=suite.suite_version,
        )

    def resolve(
        self,
        *,
        suite_id: str,
        suite_version: str,
    ) -> ResolvedBenchmarkSuite:
        suite = next(
            (
                candidate
                for candidate in self.suite_bank.load_all()
                if (
                    candidate.suite_id == suite_id
                    and candidate.suite_version
                    == suite_version
                )
            ),
            None,
        )

        if suite is None:
            raise SuiteRegistryError(
                "Benchmark suite not found: "
                f"{suite_id!r} version "
                f"{suite_version!r}."
            )

        tasks_by_id = {
            task.task_id: task
            for task in self.task_bank.load_all()
        }

        resolved_tasks: list[BenchmarkTask] = []

        for task_id in suite.task_ids:
            task = tasks_by_id.get(task_id)

            if task is None:
                raise SuiteRegistryError(
                    "Benchmark suite references "
                    f"missing task {task_id!r}."
                )

            if task.family is not suite.family:
                raise SuiteRegistryError(
                    "Benchmark suite family does not match "
                    f"task family for {task_id!r}: "
                    f"suite={suite.family.value!r}, "
                    f"task={task.family.value!r}."
                )

            resolved_tasks.append(task)

        return ResolvedBenchmarkSuite(
            suite=suite,
            tasks=tuple(resolved_tasks),
        )
