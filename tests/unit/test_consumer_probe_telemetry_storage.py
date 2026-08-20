import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
    LocalTelemetryRecord,
)
from consumer_probe.storage.sqlite import (
    ConsumerProbeSQLiteStore,
)


def make_record(
    *,
    with_telemetry: bool = True,
) -> ConsumerProbeRecord:
    probe_id = uuid4()

    telemetry = None

    if with_telemetry:
        telemetry = LocalTelemetryRecord(
            probe_id=probe_id,
            started_at_utc=datetime(
                2026,
                8,
                20,
                3,
                48,
                11,
                tzinfo=timezone.utc,
            ),
            stopped_at_utc=datetime(
                2026,
                8,
                20,
                3,
                48,
                28,
                tzinfo=timezone.utc,
            ),
            sample_count=49,
            duration_ms=17_247,
            collector_version=(
                "linux-proc-firefox-tree-fastslow-v0.1"
            ),
            browser_scope="firefox-process-tree",
            memory_method="rss+pss",
            fast_interval_target_ms=250,
            pss_interval_target_ms=1500,
            peak_browser_process_count=15,
            peak_browser_rss_bytes=3_884_630_016,
            peak_browser_pss_bytes=2_642_782_208,
            pss_sample_count=9,
            peak_browser_cpu_percent=123.6,
            min_system_memory_available_bytes=(
                7_483_899_904
            ),
            peak_system_cpu_percent=93.1,
        )

    return ConsumerProbeRecord(
        probe_id=probe_id,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        platform=ConsumerPlatform.CHATGPT,
        benchmark_version="0.1",
        prompt_id="technical-001",
        started_at_utc=datetime(
            2026,
            8,
            20,
            3,
            48,
            11,
            tzinfo=timezone.utc,
        ),
        completed_at_utc=datetime(
            2026,
            8,
            20,
            3,
            48,
            28,
            tzinfo=timezone.utc,
        ),
        total_latency_ms=17_000,
        local_telemetry=telemetry,
    )


def test_sqlite_preserves_local_telemetry(
    tmp_path: Path,
):
    path = tmp_path / "consumer.db"

    store = ConsumerProbeSQLiteStore(path)

    original = make_record()

    assert store.append(original) is True

    restored = store.load_all()[0]

    assert restored.local_telemetry is not None

    assert (
        restored.local_telemetry.telemetry_schema_version
        == "0.2"
    )

    assert (
        restored.local_telemetry.collector_version
        == "linux-proc-firefox-tree-fastslow-v0.1"
    )

    assert (
        restored.local_telemetry.sample_count
        == 49
    )

    assert (
        restored.local_telemetry
        .peak_browser_pss_bytes
        == 2_642_782_208
    )

    assert (
        restored.local_telemetry.pss_sample_count
        == 9
    )


def test_sqlite_materializes_telemetry_columns(
    tmp_path: Path,
):
    path = tmp_path / "consumer.db"

    store = ConsumerProbeSQLiteStore(path)
    store.append(make_record())

    with sqlite3.connect(path) as connection:
        row = connection.execute(
            """
            SELECT
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
                telemetry_peak_system_cpu_percent
            FROM consumer_probes
            """
        ).fetchone()

    assert row is not None

    assert row[0] == "0.2"
    assert (
        row[1]
        == "linux-proc-firefox-tree-fastslow-v0.1"
    )
    assert row[2] == "firefox-process-tree"
    assert row[3] == "rss+pss"
    assert row[4] == 250
    assert row[5] == 1500

    assert row[6] == 49
    assert row[7] == 17_247
    assert row[8] == 15
    assert row[9] == 3_884_630_016
    assert row[10] == 2_642_782_208
    assert row[11] == 9
    assert row[12] == 123.6
    assert row[13] == 7_483_899_904
    assert row[14] == 93.1


def test_legacy_record_stores_null_telemetry_columns(
    tmp_path: Path,
):
    path = tmp_path / "consumer.db"

    store = ConsumerProbeSQLiteStore(path)
    store.append(
        make_record(
            with_telemetry=False,
        )
    )

    with sqlite3.connect(path) as connection:
        row = connection.execute(
            """
            SELECT
                telemetry_sample_count,
                telemetry_peak_browser_pss_bytes
            FROM consumer_probes
            """
        ).fetchone()

    assert row == (None, None)


def test_existing_database_gains_telemetry_columns(
    tmp_path: Path,
):
    path = tmp_path / "legacy.db"

    legacy = make_record(
        with_telemetry=False,
    )

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE consumer_probes (
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
                total_latency_ms REAL,

                generation_failed INTEGER NOT NULL,
                interrupted INTEGER NOT NULL,
                retry_observed INTEGER NOT NULL,

                measurement_mode TEXT NOT NULL,

                payload_json TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            INSERT INTO consumer_probes (
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
                total_latency_ms,
                generation_failed,
                interrupted,
                retry_observed,
                measurement_mode,
                payload_json
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                str(legacy.probe_id),
                legacy.schema_version,
                legacy.observer_id,
                legacy.region_code,
                legacy.platform.value,
                legacy.account_tier,
                legacy.model_label,
                legacy.benchmark_version,
                legacy.prompt_id,
                None,
                None,
                legacy.started_at_utc.isoformat(),
                None,
                (
                    legacy.completed_at_utc.isoformat()
                    if legacy.completed_at_utc
                    else None
                ),
                legacy.time_to_first_output_ms,
                legacy.total_latency_ms,
                int(legacy.generation_failed),
                int(legacy.interrupted),
                int(legacy.retry_observed),
                legacy.measurement_mode,
                legacy.model_dump_json(),
            ),
        )

    store = ConsumerProbeSQLiteStore(path)

    assert store.count() == 1

    restored = store.load_all()

    assert len(restored) == 1
    assert restored[0].probe_id == legacy.probe_id
    assert restored[0].local_telemetry is None

    with sqlite3.connect(path) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(consumer_probes)"
            ).fetchall()
        }

        row = connection.execute(
            """
            SELECT
                telemetry_schema_version,
                telemetry_collector_version,
                telemetry_fast_interval_target_ms,
                telemetry_sample_count
            FROM consumer_probes
            WHERE probe_id = ?
            """,
            (str(legacy.probe_id),),
        ).fetchone()

    expected_columns = {
        "telemetry_schema_version",
        "telemetry_collector_version",
        "telemetry_browser_scope",
        "telemetry_memory_method",
        "telemetry_fast_interval_target_ms",
        "telemetry_pss_interval_target_ms",
        "telemetry_sample_count",
        "telemetry_duration_ms",
        "telemetry_peak_browser_process_count",
        "telemetry_peak_browser_rss_bytes",
        "telemetry_peak_browser_pss_bytes",
        "telemetry_pss_sample_count",
        "telemetry_peak_browser_cpu_percent",
        "telemetry_min_system_memory_available_bytes",
        "telemetry_peak_system_cpu_percent",
    }

    assert expected_columns <= columns
    assert row == (None, None, None, None)

    # Migration remains idempotent.
    ConsumerProbeSQLiteStore(path)
    ConsumerProbeSQLiteStore(path)

    assert store.count() == 1
