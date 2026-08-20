import json
from pathlib import Path
from uuid import uuid4

import pytest

from consumer_probe.importer import (
    ConsumerProbeImportError,
    import_export,
)


def make_record() -> dict:
    probe_id = str(uuid4())

    return {
        "schema_version": "0.1",
        "probe_id": probe_id,
        "prompt_id": "technical-001",
        "benchmark_version": "0.1",
        "platform": "chatgpt",
        "page_hostname": "chatgpt.com",
        "started_at_ms": 1000,
        "started_at_utc": (
            "2026-08-20T03:48:11+00:00"
        ),
        "first_output_at_ms": None,
        "first_output_at_utc": None,
        "completed_at_ms": 18000,
        "completed_at_utc": (
            "2026-08-20T03:48:28+00:00"
        ),
        "time_to_first_output_ms": None,
        "total_latency_ms": 17000,
        "generation_failed": False,
        "interrupted": False,
        "retry_observed": False,
        "response_capture_enabled": False,
        "response_text": None,
        "measurement_mode":
            "consumer-ui-manual-v0.1",
        "local_telemetry": {
            "telemetry_schema_version": "0.1",
            "probe_id": probe_id,
            "started_at_utc":
                "2026-08-20T03:48:11+00:00",
            "stopped_at_utc":
                "2026-08-20T03:48:28+00:00",
            "sample_count": 49,
            "duration_ms": 17000,
            "peak_browser_process_count": 15,
            "peak_browser_rss_bytes":
                3_884_630_016,
            "peak_browser_pss_bytes":
                2_642_782_208,
            "pss_sample_count": 9,
            "peak_browser_cpu_percent": 123.6,
            "min_system_memory_available_bytes":
                7_483_899_904,
            "peak_system_cpu_percent": 93.1,
        },
        "local_telemetry_error": None,
    }


def write_export(
    path: Path,
    record: dict,
) -> None:
    path.write_text(
        json.dumps(
            {
                "export_schema_version": "0.1",
                "exported_at_utc":
                    "2026-08-20T04:00:00+00:00",
                "sample_count": 1,
                "records": [record],
            }
        ),
        encoding="utf-8",
    )


def test_import_preserves_local_telemetry(
    tmp_path: Path,
):
    path = tmp_path / "export.json"
    record = make_record()

    write_export(path, record)

    normalized = import_export(
        path,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )[0]

    telemetry = normalized.local_telemetry

    assert telemetry is not None
    assert telemetry.probe_id == normalized.probe_id
    assert telemetry.sample_count == 49
    assert telemetry.pss_sample_count == 9

    assert (
        telemetry.peak_browser_pss_bytes
        == 2_642_782_208
    )


def test_legacy_record_without_telemetry_still_imports(
    tmp_path: Path,
):
    path = tmp_path / "legacy.json"

    record = make_record()
    record.pop("local_telemetry")
    record.pop("local_telemetry_error")

    write_export(path, record)

    normalized = import_export(
        path,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )[0]

    assert normalized.local_telemetry is None
    assert normalized.local_telemetry_error is None


def test_telemetry_probe_id_must_match_probe(
    tmp_path: Path,
):
    path = tmp_path / "invalid.json"

    record = make_record()

    record["local_telemetry"][
        "probe_id"
    ] = str(uuid4())

    write_export(path, record)

    with pytest.raises(
        ConsumerProbeImportError,
    ):
        import_export(
            path,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )


def test_pss_count_cannot_exceed_sample_count(
    tmp_path: Path,
):
    path = tmp_path / "invalid.json"

    record = make_record()

    record["local_telemetry"][
        "pss_sample_count"
    ] = 50

    write_export(path, record)

    with pytest.raises(
        ConsumerProbeImportError,
    ):
        import_export(
            path,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )


def test_pss_peak_requires_pss_samples(
    tmp_path: Path,
):
    path = tmp_path / "invalid.json"

    record = make_record()

    record["local_telemetry"][
        "pss_sample_count"
    ] = 0

    write_export(path, record)

    with pytest.raises(
        ConsumerProbeImportError,
    ):
        import_export(
            path,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )


def test_telemetry_and_error_are_mutually_exclusive(
    tmp_path: Path,
):
    path = tmp_path / "invalid.json"

    record = make_record()
    record["local_telemetry_error"] = (
        "synthetic failure"
    )

    write_export(path, record)

    with pytest.raises(
        ConsumerProbeImportError,
    ):
        import_export(
            path,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )


def test_legacy_pss_peak_without_sample_count_imports(
    tmp_path: Path,
):
    path = tmp_path / "legacy-pss.json"

    record = make_record()

    record["local_telemetry"].pop(
        "pss_sample_count"
    )

    write_export(path, record)

    normalized = import_export(
        path,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )[0]

    telemetry = normalized.local_telemetry

    assert telemetry is not None

    assert (
        telemetry.peak_browser_pss_bytes
        == 2_642_782_208
    )

    assert telemetry.pss_sample_count is None
