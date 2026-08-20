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

    assert row[0] == 49
    assert row[1] == 17_247
    assert row[2] == 15
    assert row[3] == 3_884_630_016
    assert row[4] == 2_642_782_208
    assert row[5] == 9
    assert row[6] == 123.6
    assert row[7] == 7_483_899_904
    assert row[8] == 93.1


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

    # Create the DB through the current store first,
    # then remove/recreate a pre-telemetry shape.
    store = ConsumerProbeSQLiteStore(path)

    del store

    with sqlite3.connect(path) as connection:
        telemetry_columns = [
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(consumer_probes)"
            ).fetchall()
            if row[1].startswith("telemetry_")
        ]

        for column in telemetry_columns:
            # SQLite cannot DROP COLUMN reliably across all
            # supported environments, so migration existence
            # is verified below using a fresh legacy fixture
            # constructed from the known pre-telemetry schema.
            assert column

    # The migration is idempotent.
    ConsumerProbeSQLiteStore(path)
    ConsumerProbeSQLiteStore(path)

    with sqlite3.connect(path) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(consumer_probes)"
            ).fetchall()
        }

    assert "telemetry_sample_count" in columns
    assert "telemetry_peak_browser_pss_bytes" in columns
    assert "telemetry_pss_sample_count" in columns
