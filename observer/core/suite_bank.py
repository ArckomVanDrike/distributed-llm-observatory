from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from schemas.benchmark import BenchmarkSuite


class SuiteBankError(Exception):
    """Raised when the benchmark suite bank cannot be loaded safely."""


class SuiteBank:
    def __init__(
        self,
        root: Path,
    ) -> None:
        self.root = root

    def load_suite(
        self,
        path: Path,
    ) -> BenchmarkSuite:
        try:
            raw_data = json.loads(
                path.read_text(encoding="utf-8")
            )
        except OSError as exc:
            raise SuiteBankError(
                f"Unable to read suite file: {path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise SuiteBankError(
                f"Invalid JSON in suite file: {path}"
            ) from exc

        try:
            return BenchmarkSuite.model_validate(
                raw_data
            )
        except ValidationError as exc:
            raise SuiteBankError(
                f"Invalid benchmark suite: {path}"
            ) from exc

    def load_all(
        self,
    ) -> list[BenchmarkSuite]:
        if not self.root.exists():
            raise SuiteBankError(
                "Suite bank directory does not exist: "
                f"{self.root}"
            )

        suites = [
            self.load_suite(path)
            for path in sorted(
                self.root.rglob("*.json")
            )
        ]

        identities = [
            (
                suite.suite_id,
                suite.suite_version,
            )
            for suite in suites
        ]

        if len(identities) != len(set(identities)):
            raise SuiteBankError(
                "Duplicate benchmark suite identity detected."
            )

        return suites

    def load_enabled(
        self,
    ) -> list[BenchmarkSuite]:
        return [
            suite
            for suite in self.load_all()
            if suite.enabled
        ]
