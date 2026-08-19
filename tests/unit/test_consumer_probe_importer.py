import json
from pathlib import Path
from uuid import uuid4

import pytest

from consumer_probe.importer import (
    ConsumerProbeImportError,
    import_export,
    load_export,
)


def make_record():
    return {
        "schema_version": "0.1",
        "probe_id": str(uuid4()),
        "prompt_id": "reasoning-001",
        "benchmark_version": "0.1",
        "platform": "chatgpt",
        "page_hostname": "chatgpt.com",
        "started_at_ms": 1000,
        "started_at_utc": "2026-08-19T21:17:04.000Z",
        "first_output_at_ms": 2000,
        "first_output_at_utc": "2026-08-19T21:17:05.000Z",
        "completed_at_ms": 4000,
        "completed_at_utc": "2026-08-19T21:17:07.000Z",
        "time_to_first_output_ms": 1000,
        "total_latency_ms": 3000,
        "generation_failed": False,
        "interrupted": False,
        "retry_observed": False,
        "response_capture_enabled": False,
        "response_text": None,
        "measurement_mode": "consumer-ui-manual-v0.1",
    }


def write_export(path: Path, records):
    payload = {
        "export_schema_version": "0.1",
        "exported_at_utc": "2026-08-19T21:20:00Z",
        "sample_count": len(records),
        "records": records,
    }

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_load_valid_export(tmp_path: Path):
    path = tmp_path / "export.json"
    write_export(path, [make_record(), make_record()])

    export = load_export(path)

    assert export.sample_count == 2
    assert len(export.records) == 2


def test_import_normalizes_observer_metadata(tmp_path: Path):
    path = tmp_path / "export.json"
    write_export(path, [make_record()])

    records = import_export(
        path,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    assert len(records) == 1
    assert records[0].observer_id == "observer-test"
    assert records[0].region_code == "CL-Los-Lagos"
    assert records[0].platform.value == "chatgpt"
    assert records[0].prompt_id == "reasoning-001"


def test_rejects_incorrect_sample_count(tmp_path: Path):
    path = tmp_path / "export.json"

    payload = {
        "export_schema_version": "0.1",
        "exported_at_utc": "2026-08-19T21:20:00Z",
        "sample_count": 99,
        "records": [make_record()],
    }

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(ConsumerProbeImportError):
        load_export(path)


def test_rejects_duplicate_probe_ids(tmp_path: Path):
    path = tmp_path / "export.json"

    record = make_record()

    write_export(path, [record, record])

    with pytest.raises(ConsumerProbeImportError):
        load_export(path)


def test_rejects_inconsistent_total_latency(tmp_path: Path):
    path = tmp_path / "export.json"

    record = make_record()
    record["total_latency_ms"] = 9999

    write_export(path, [record])

    with pytest.raises(ConsumerProbeImportError):
        load_export(path)


def test_rejects_inconsistent_ttfo(tmp_path: Path):
    path = tmp_path / "export.json"

    record = make_record()
    record["time_to_first_output_ms"] = 5000

    write_export(path, [record])

    with pytest.raises(ConsumerProbeImportError):
        load_export(path)


def test_rejects_response_when_capture_disabled(tmp_path: Path):
    path = tmp_path / "export.json"

    record = make_record()
    record["response_text"] = "Should not be here"

    write_export(path, [record])

    with pytest.raises(ConsumerProbeImportError):
        load_export(path)


def test_import_preserves_observer_timezone(tmp_path: Path):
    path = tmp_path / "export.json"
    write_export(path, [make_record()])

    records = import_export(
        path,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        observer_timezone="America/Santiago",
    )

    assert records[0].observer_timezone == "America/Santiago"


def test_import_rejects_invalid_observer_timezone(tmp_path: Path):
    path = tmp_path / "export.json"
    write_export(path, [make_record()])

    with pytest.raises(ConsumerProbeImportError):
        import_export(
            path,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
            observer_timezone="Planet/Mars",
        )
