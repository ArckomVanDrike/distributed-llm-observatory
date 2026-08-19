from __future__ import annotations

import sqlite3
from pathlib import Path

from pydantic import ValidationError

from observer.storage.base import ObservationStore
from schemas.record import ObservationRecord


class SQLiteObservationStoreError(Exception):
    """Raised when SQLite observation persistence fails."""


class SQLiteObservationStore(ObservationStore):
    """
    SQLite-backed local Observatory storage.

    Selected fields are indexed for efficient local analysis while the full
    validated ObservationRecord is preserved as JSON.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id TEXT PRIMARY KEY,
                    schema_version TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    observer_id TEXT NOT NULL,
                    region_code TEXT NOT NULL,
                    benchmark_version TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_observations_timestamp
                ON observations(timestamp_utc)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_observations_model
                ON observations(provider, model)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_observations_region
                ON observations(region_code)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_observations_prompt
                ON observations(prompt_id)
                """
            )

    def append(self, record: ObservationRecord) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO observations (
                        observation_id,
                        schema_version,
                        timestamp_utc,
                        observer_id,
                        region_code,
                        benchmark_version,
                        prompt_id,
                        provider,
                        model,
                        payload_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(record.observation_id),
                        record.schema_version,
                        record.execution.timestamp_utc.isoformat(),
                        record.observer.observer_id,
                        record.observer.region_code,
                        record.benchmark.benchmark_version,
                        record.benchmark.prompt_id,
                        record.execution.provider,
                        record.execution.model,
                        record.model_dump_json(),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise SQLiteObservationStoreError(
                f"Observation {record.observation_id} already exists."
            ) from exc
        except sqlite3.Error as exc:
            raise SQLiteObservationStoreError(
                f"Unable to persist observation in {self.path}."
            ) from exc

    def load_all(self) -> list[ObservationRecord]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT payload_json
                    FROM observations
                    ORDER BY timestamp_utc, observation_id
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise SQLiteObservationStoreError(
                f"Unable to read observations from {self.path}."
            ) from exc

        records: list[ObservationRecord] = []

        for (payload_json,) in rows:
            try:
                records.append(
                    ObservationRecord.model_validate_json(payload_json)
                )
            except ValidationError as exc:
                raise SQLiteObservationStoreError(
                    "Stored observation failed schema validation."
                ) from exc

        return records

    def count(self) -> int:
        try:
            with self._connect() as connection:
                result = connection.execute(
                    "SELECT COUNT(*) FROM observations"
                ).fetchone()
        except sqlite3.Error as exc:
            raise SQLiteObservationStoreError(
                f"Unable to count observations in {self.path}."
            ) from exc

        return int(result[0]) if result else 0
