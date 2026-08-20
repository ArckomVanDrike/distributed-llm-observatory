from __future__ import annotations

import sqlite3
from pathlib import Path

from pydantic import ValidationError

from consumer_probe.schemas import ConsumerProbeRecord


class ConsumerProbeStoreError(Exception):
    """Raised when Consumer Probe persistence fails."""


class ConsumerProbeSQLiteStore:
    """
    SQLite-backed storage for normalized Consumer Probe observations.

    probe_id is the primary key, making repeated imports idempotent.
    The complete validated record is preserved as JSON while selected
    fields are indexed for later analysis.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS consumer_probes (
                    probe_id TEXT PRIMARY KEY,
                    schema_version TEXT NOT NULL,

                    observer_id TEXT NOT NULL,
                    region_code TEXT NOT NULL,

                    platform TEXT NOT NULL,
                    account_tier TEXT,
                    model_label TEXT,

                    benchmark_version TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,

                    scheduled_at_utc TEXT,
                    schedule_offset_ms REAL,

                    started_at_utc TEXT NOT NULL,
                    first_output_at_utc TEXT,
                    completed_at_utc TEXT,

                    time_to_first_output_ms REAL,
                    first_output_measurement_mode TEXT,
                    total_latency_ms REAL,

                    generation_failed INTEGER NOT NULL,
                    interrupted INTEGER NOT NULL,
                    retry_observed INTEGER NOT NULL,

                    measurement_mode TEXT NOT NULL,

                    telemetry_schema_version TEXT,
                    telemetry_collector_version TEXT,
                    telemetry_browser_scope TEXT,
                    telemetry_memory_method TEXT,
                    telemetry_fast_interval_target_ms REAL,
                    telemetry_pss_interval_target_ms REAL,

                    telemetry_sample_count INTEGER,
                    telemetry_duration_ms REAL,
                    telemetry_peak_browser_process_count INTEGER,
                    telemetry_peak_browser_rss_bytes INTEGER,
                    telemetry_peak_browser_pss_bytes INTEGER,
                    telemetry_pss_sample_count INTEGER,
                    telemetry_peak_browser_cpu_percent REAL,
                    telemetry_min_system_memory_available_bytes INTEGER,
                    telemetry_peak_system_cpu_percent REAL,

                    payload_json TEXT NOT NULL
                )
                """
            )

            self._ensure_column(
                connection,
                "scheduled_at_utc",
                "TEXT",
            )

            self._ensure_column(
                connection,
                "schedule_offset_ms",
                "REAL",
            )

            self._ensure_column(
                connection,
                "first_output_measurement_mode",
                "TEXT",
            )

            telemetry_columns = {
                "telemetry_schema_version": "TEXT",
                "telemetry_collector_version": "TEXT",
                "telemetry_browser_scope": "TEXT",
                "telemetry_memory_method": "TEXT",
                "telemetry_fast_interval_target_ms": "REAL",
                "telemetry_pss_interval_target_ms": "REAL",
                "telemetry_sample_count": "INTEGER",
                "telemetry_duration_ms": "REAL",
                "telemetry_peak_browser_process_count": "INTEGER",
                "telemetry_peak_browser_rss_bytes": "INTEGER",
                "telemetry_peak_browser_pss_bytes": "INTEGER",
                "telemetry_pss_sample_count": "INTEGER",
                "telemetry_peak_browser_cpu_percent": "REAL",
                "telemetry_min_system_memory_available_bytes": "INTEGER",
                "telemetry_peak_system_cpu_percent": "REAL",
            }

            for (
                column_name,
                definition,
            ) in telemetry_columns.items():
                self._ensure_column(
                    connection,
                    column_name,
                    definition,
                )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consumer_probe_telemetry_collector
                ON consumer_probes(
                    telemetry_collector_version
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consumer_probe_telemetry_pss
                ON consumer_probes(
                    telemetry_peak_browser_pss_bytes
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consumer_probe_schedule
                ON consumer_probes(scheduled_at_utc)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consumer_probe_time
                ON consumer_probes(started_at_utc)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consumer_probe_platform
                ON consumer_probes(platform)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consumer_probe_region
                ON consumer_probes(region_code)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consumer_probe_prompt
                ON consumer_probes(prompt_id)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consumer_probe_analysis
                ON consumer_probes(
                    platform,
                    region_code,
                    prompt_id,
                    started_at_utc
                )
                """
            )

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection,
        column_name: str,
        definition: str,
    ) -> None:
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(consumer_probes)"
            ).fetchall()
        }

        if column_name in columns:
            return

        connection.execute(
            f"ALTER TABLE consumer_probes "
            f"ADD COLUMN {column_name} {definition}"
        )

    def append(self, record: ConsumerProbeRecord) -> bool:
        """
        Persist one observation.

        Returns True when inserted and False when probe_id already exists.
        """
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO consumer_probes (
                        probe_id,
                        schema_version,
                        observer_id,
                        region_code,
                        platform,
                        account_tier,
                        model_label,
                        benchmark_version,
                        prompt_id,
                        scheduled_at_utc,
                        schedule_offset_ms,
                        started_at_utc,
                        first_output_at_utc,
                        completed_at_utc,
                        time_to_first_output_ms,
                        first_output_measurement_mode,
                        total_latency_ms,
                        generation_failed,
                        interrupted,
                        retry_observed,
                        measurement_mode,
                        telemetry_schema_version,
                        telemetry_collector_version,
                        telemetry_browser_scope,
                        telemetry_memory_method,
                        telemetry_fast_interval_target_ms,
                        telemetry_pss_interval_target_ms,
                        telemetry_sample_count,
                        telemetry_duration_ms,
                        telemetry_peak_browser_process_count,
                        telemetry_peak_browser_rss_bytes,
                        telemetry_peak_browser_pss_bytes,
                        telemetry_pss_sample_count,
                        telemetry_peak_browser_cpu_percent,
                        telemetry_min_system_memory_available_bytes,
                        telemetry_peak_system_cpu_percent,
                        payload_json
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        str(record.probe_id),
                        record.schema_version,
                        record.observer_id,
                        record.region_code,
                        record.platform.value,
                        record.account_tier,
                        record.model_label,
                        record.benchmark_version,
                        record.prompt_id,
                        (
                            record.scheduled_at_utc.isoformat()
                            if record.scheduled_at_utc
                            else None
                        ),
                        record.schedule_offset_ms,
                        record.started_at_utc.isoformat(),
                        (
                            record.first_output_at_utc.isoformat()
                            if record.first_output_at_utc
                            else None
                        ),
                        (
                            record.completed_at_utc.isoformat()
                            if record.completed_at_utc
                            else None
                        ),
                        record.time_to_first_output_ms,
                        record.first_output_measurement_mode,
                        record.total_latency_ms,
                        int(record.generation_failed),
                        int(record.interrupted),
                        int(record.retry_observed),
                        record.measurement_mode,
                        (
                            record.local_telemetry
                            .telemetry_schema_version
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .collector_version
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .browser_scope
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .memory_method
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .fast_interval_target_ms
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .pss_interval_target_ms
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry.sample_count
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry.duration_ms
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .peak_browser_process_count
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .peak_browser_rss_bytes
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .peak_browser_pss_bytes
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .pss_sample_count
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .peak_browser_cpu_percent
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .min_system_memory_available_bytes
                            if record.local_telemetry
                            else None
                        ),
                        (
                            record.local_telemetry
                            .peak_system_cpu_percent
                            if record.local_telemetry
                            else None
                        ),
                        record.model_dump_json(),
                    ),
                )

                return cursor.rowcount == 1

        except sqlite3.Error as exc:
            raise ConsumerProbeStoreError(
                f"Unable to persist Consumer Probe in {self.path}."
            ) from exc

    def append_many(
        self,
        records: list[ConsumerProbeRecord],
    ) -> tuple[int, int]:
        """
        Persist multiple observations.

        Returns:
            (inserted_count, duplicate_count)
        """
        inserted = 0
        duplicates = 0

        for record in records:
            if self.append(record):
                inserted += 1
            else:
                duplicates += 1

        return inserted, duplicates

    def load_all(self) -> list[ConsumerProbeRecord]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT payload_json
                    FROM consumer_probes
                    ORDER BY started_at_utc, probe_id
                    """
                ).fetchall()

        except sqlite3.Error as exc:
            raise ConsumerProbeStoreError(
                f"Unable to read Consumer Probes from {self.path}."
            ) from exc

        records: list[ConsumerProbeRecord] = []

        for row in rows:
            try:
                records.append(
                    ConsumerProbeRecord.model_validate_json(
                        row["payload_json"]
                    )
                )
            except ValidationError as exc:
                raise ConsumerProbeStoreError(
                    "Stored Consumer Probe failed schema validation."
                ) from exc

        return records

    def count(self) -> int:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM consumer_probes
                    """
                ).fetchone()

        except sqlite3.Error as exc:
            raise ConsumerProbeStoreError(
                f"Unable to count Consumer Probes in {self.path}."
            ) from exc

        return int(row["total"]) if row else 0
