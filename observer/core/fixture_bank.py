from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from schemas.fixture import FilesystemFixture


class FixtureBankError(Exception):
    """Raised when the benchmark fixture bank cannot be loaded safely."""


class FixtureBank:
    def __init__(
        self,
        root: Path,
    ) -> None:
        self.root = root

    def load_fixture(
        self,
        path: Path,
    ) -> FilesystemFixture:
        try:
            raw_data = json.loads(
                path.read_text(
                    encoding="utf-8",
                )
            )
        except OSError as exc:
            raise FixtureBankError(
                f"Unable to read fixture file: {path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise FixtureBankError(
                f"Invalid JSON in fixture file: {path}"
            ) from exc

        try:
            return FilesystemFixture.model_validate(
                raw_data
            )
        except ValidationError as exc:
            raise FixtureBankError(
                f"Invalid fixture: {path}"
            ) from exc

    def load_all(
        self,
    ) -> list[FilesystemFixture]:
        if not self.root.exists():
            raise FixtureBankError(
                "Fixture bank directory does not exist: "
                f"{self.root}"
            )

        fixtures = [
            self.load_fixture(path)
            for path in sorted(
                self.root.rglob("*.json")
            )
        ]

        fixture_ids = [
            fixture.fixture_id
            for fixture in fixtures
        ]

        if (
            len(fixture_ids)
            != len(set(fixture_ids))
        ):
            raise FixtureBankError(
                "Duplicate fixture_id detected in fixture bank."
            )

        return fixtures
