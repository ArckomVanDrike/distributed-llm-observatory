import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from consumer_probe.importer import (
    ConsumerProbeImportError,
    import_export,
)
from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
)
from consumer_probe.storage.sqlite import (
    ConsumerProbeSQLiteStore,
)


def browser_record(
    *,
    include_schedule: bool = True,
    schedule_offset_ms: float = 180_000,
) -> dict:
    scheduled = datetime(
        2026,
        8,
        19,
        20,
        0,
        tzinfo=timezone.utc,
    )

    started = scheduled + timedelta(
        minutes=3
    )

    first = started + timedelta(
        seconds=1
    )

    completed = started + timedelta(
        seconds=3
    )

    record = {
        "schema_version": "0.1",
        "probe_id": str(uuid4()),
        "prompt_id": "mathematics-001",
        "benchmark_version": "0.1",
        "platform": "chatgpt",
        "page_hostname": "chatgpt.com",
        "started_at_ms": round(
            started.timestamp() * 1000
        ),
        "started_at_utc": started.isoformat(),
        "first_output_at_ms": round(
            first.timestamp() * 1000
        ),
        "first_output_at_utc": first.isoformat(),
        "completed_at_ms": round(
            completed.timestamp() * 1000
        ),
        "completed_at_utc": completed.isoformat(),
        "time_to_first_output_ms": 1000,
        "total_latency_ms": 3000,
        "generation_failed": False,
        "interrupted": False,
        "retry_observed": False,
        "response_capture_enabled": False,
        "response_text": None,
        "measurement_mode": "consumer-ui-manual-v0.1",
    }

    if include_schedule:
        record["scheduled_at_utc"] = (
            scheduled.isoformat()
        )
        record["schedule_offset_ms"] = (
            schedule_offset_ms
        )

    return record


def write_export(
    path: Path,
    record: dict,
) -> None:
    payload = {
        "export_schema_version": "0.1",
        "exported_at_utc": (
            "2026-08-19T23:30:00+00:00"
        ),
        "sample_count": 1,
        "records": [record],
    }

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_import_preserves_schedule_provenance(
    tmp_path: Path,
):
    path = tmp_path / "export.json"

    write_export(
        path,
        browser_record(),
    )

    records = import_export(
        path,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    record = records[0]

    assert record.scheduled_at_utc == datetime(
        2026,
        8,
        19,
        20,
        0,
        tzinfo=timezone.utc,
    )

    assert record.schedule_offset_ms == 180_000


def test_legacy_export_remains_supported(
    tmp_path: Path,
):
    path = tmp_path / "legacy.json"

    write_export(
        path,
        browser_record(
            include_schedule=False,
        ),
    )

    record = import_export(
        path,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )[0]

    assert record.scheduled_at_utc is None
    assert record.schedule_offset_ms is None


def test_inconsistent_schedule_offset_is_rejected(
    tmp_path: Path,
):
    path = tmp_path / "invalid.json"

    write_export(
        path,
        browser_record(
            schedule_offset_ms=42,
        ),
    )

    with pytest.raises(
        ConsumerProbeImportError,
    ):
        import_export(
            path,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )


def test_schedule_offset_requires_timestamp(
    tmp_path: Path,
):
    path = tmp_path / "invalid.json"

    record = browser_record(
        include_schedule=False,
    )

    record["schedule_offset_ms"] = 1000

    write_export(path, record)

    with pytest.raises(
        ConsumerProbeImportError,
    ):
        import_export(
            path,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )


def make_normalized_record() -> ConsumerProbeRecord:
    scheduled = datetime(
        2026,
        8,
        19,
        20,
        0,
        tzinfo=timezone.utc,
    )

    started = scheduled + timedelta(
        minutes=3
    )

    return ConsumerProbeRecord(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        platform=ConsumerPlatform.CHATGPT,
        benchmark_version="0.1",
        prompt_id="mathematics-001",
        scheduled_at_utc=scheduled,
        schedule_offset_ms=180_000,
        started_at_utc=started,
        first_output_at_utc=(
            started + timedelta(seconds=1)
        ),
        completed_at_utc=(
            started + timedelta(seconds=3)
        ),
        time_to_first_output_ms=1000,
        total_latency_ms=3000,
    )


def test_sqlite_preserves_schedule_provenance(
    tmp_path: Path,
):
    store = ConsumerProbeSQLiteStore(
        tmp_path / "consumer.db"
    )

    original = make_normalized_record()

    assert store.append(original) is True

    restored = store.load_all()[0]

    assert (
        restored.scheduled_at_utc
        == original.scheduled_at_utc
    )

    assert (
        restored.schedule_offset_ms
        == 180_000
    )


def test_existing_database_is_migrated(
    tmp_path: Path,
):
    path = tmp_path / "legacy.db"

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

    store = ConsumerProbeSQLiteStore(path)

    with sqlite3.connect(path) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(consumer_probes)"
            ).fetchall()
        }

    assert "scheduled_at_utc" in columns
    assert "schedule_offset_ms" in columns

    assert store.append(
        make_normalized_record()
    ) is True
