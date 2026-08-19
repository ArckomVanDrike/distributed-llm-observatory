from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from schemas.record import ObservationRecord


class ObservationStoreError(Exception):
    """Raised when local observation storage cannot be read safely."""


class JSONLObservationStore:
    """
    Append-only local storage for Observatory observations.

    Each line contains one complete ObservationRecord encoded as JSON.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: ObservationRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("a", encoding="utf-8") as file:
            file.write(record.model_dump_json())
            file.write("\n")

    def load_all(self) -> list[ObservationRecord]:
        if not self.path.exists():
            return []

        records: list[ObservationRecord] = []

        with self.path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue

                try:
                    record = ObservationRecord.model_validate_json(line)
                except (ValidationError, ValueError) as exc:
                    raise ObservationStoreError(
                        f"Invalid observation at line {line_number} "
                        f"in {self.path}."
                    ) from exc

                records.append(record)

        return records
