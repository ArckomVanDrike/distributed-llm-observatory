import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
)
from consumer_probe.storage.sqlite import (
    ConsumerProbeSQLiteStore,
)


def make_record(
    *,
    probe_id=None,
    platform=ConsumerPlatform.CHATGPT,
    first_output_measurement_mode=None,
) -> ConsumerProbeRecord:
    return ConsumerProbeRecord(
        probe_id=probe_id or uuid4(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        platform=platform,
        page_hostname="chatgpt.com",
        benchmark_version="0.1",
        prompt_id="reasoning-001",
        started_at_utc=datetime.now(timezone.utc),
        first_output_at_utc=datetime.now(timezone.utc),
        completed_at_utc=datetime.now(timezone.utc),
        time_to_first_output_ms=1200,
        first_output_measurement_mode=(
            first_output_measurement_mode
        ),
        total_latency_ms=3000,
    )


def test_store_creates_database(tmp_path: Path):
    path = tmp_path / "consumer-probes.db"

    ConsumerProbeSQLiteStore(path)

    assert path.exists()


def test_store_appends_and_loads_record(tmp_path: Path):
    store = ConsumerProbeSQLiteStore(
        tmp_path / "consumer-probes.db"
    )

    original = make_record()

    inserted = store.append(original)
    records = store.load_all()

    assert inserted is True
    assert len(records) == 1
    assert records[0].probe_id == original.probe_id
    assert records[0].platform == ConsumerPlatform.CHATGPT


def test_duplicate_probe_is_ignored(tmp_path: Path):
    store = ConsumerProbeSQLiteStore(
        tmp_path / "consumer-probes.db"
    )

    record = make_record()

    assert store.append(record) is True
    assert store.append(record) is False
    assert store.count() == 1


def test_append_many_reports_duplicates(tmp_path: Path):
    store = ConsumerProbeSQLiteStore(
        tmp_path / "consumer-probes.db"
    )

    first = make_record()
    second = make_record()

    inserted, duplicates = store.append_many(
        [first, second]
    )

    assert inserted == 2
    assert duplicates == 0

    inserted, duplicates = store.append_many(
        [first, second]
    )

    assert inserted == 0
    assert duplicates == 2
    assert store.count() == 2


def test_store_preserves_measurements(tmp_path: Path):
    store = ConsumerProbeSQLiteStore(
        tmp_path / "consumer-probes.db"
    )

    record = make_record()

    store.append(record)

    restored = store.load_all()[0]

    assert restored.time_to_first_output_ms == 1200
    assert restored.total_latency_ms == 3000
    assert restored.prompt_id == "reasoning-001"
    assert restored.region_code == "CL-Los-Lagos"


def test_store_creates_parent_directories(tmp_path: Path):
    path = (
        tmp_path
        / "nested"
        / "observatory"
        / "consumer-probes.db"
    )

    ConsumerProbeSQLiteStore(path)

    assert path.exists()


def test_store_materializes_first_output_measurement_mode(
    tmp_path: Path,
):
    path = tmp_path / "consumer-probes.db"

    store = ConsumerProbeSQLiteStore(path)

    record = make_record(
        first_output_measurement_mode=(
            "human-observed-click-v0.1"
        ),
    )

    assert store.append(record) is True

    with sqlite3.connect(path) as connection:
        row = connection.execute(
            """
            SELECT first_output_measurement_mode
            FROM consumer_probes
            WHERE probe_id = ?
            """,
            (str(record.probe_id),),
        ).fetchone()

    assert row == (
        "human-observed-click-v0.1",
    )

    restored = store.load_all()[0]

    assert (
        restored.first_output_measurement_mode
        == "human-observed-click-v0.1"
    )


def test_existing_database_gains_first_output_measurement_mode(
    tmp_path: Path,
):
    path = tmp_path / "legacy.db"
    legacy = make_record()

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
                (
                    legacy.first_output_at_utc.isoformat()
                    if legacy.first_output_at_utc
                    else None
                ),
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

    with sqlite3.connect(path) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(consumer_probes)"
            )
        }

        row = connection.execute(
            """
            SELECT first_output_measurement_mode
            FROM consumer_probes
            WHERE probe_id = ?
            """,
            (str(legacy.probe_id),),
        ).fetchone()

    assert "first_output_measurement_mode" in columns
    assert row == (None,)

    restored = store.load_all()[0]

    assert restored.probe_id == legacy.probe_id
    assert restored.first_output_measurement_mode is None
