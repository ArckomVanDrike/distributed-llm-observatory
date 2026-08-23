from pathlib import Path

from consumer_probe.importer import (
    load_export,
    normalize_export,
)
from consumer_probe.storage.sqlite import (
    ConsumerProbeSQLiteStore,
)

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "web_collector_export_v01.json"
)


def test_web_collector_export_round_trips_into_consumer_store(
    tmp_path: Path,
):
    export = load_export(FIXTURE)

    assert export.export_schema_version == "0.1"
    assert export.sample_count == 1

    browser_record = export.records[0]

    assert browser_record.measurement_mode == (
        "consumer-ui-manual-v0.1"
    )
    assert browser_record.first_output_measurement_mode == (
        "human-observed-click-v0.1"
    )
    assert browser_record.time_to_first_output_ms == 4000
    assert browser_record.total_latency_ms == 9000
    assert browser_record.response_capture_enabled is False
    assert browser_record.response_text is None

    normalized = normalize_export(
        export,
        observer_id="observer-web-contract-test",
        region_code="CL-Los-Lagos",
        observer_timezone="America/Santiago",
    )

    assert len(normalized) == 1

    record = normalized[0]

    assert record.probe_id == browser_record.probe_id
    assert record.measurement_mode == (
        "consumer-ui-manual-v0.1"
    )
    assert record.first_output_measurement_mode == (
        "human-observed-click-v0.1"
    )
    assert record.schedule_offset_ms == 60000
    assert record.response_capture_enabled is False
    assert record.response_text is None

    store = ConsumerProbeSQLiteStore(
        tmp_path / "collector-contract.db"
    )
    store.append(record)

    loaded = store.load_all()

    assert len(loaded) == 1
    assert loaded[0].probe_id == record.probe_id
    assert loaded[0].first_output_measurement_mode == (
        "human-observed-click-v0.1"
    )
    assert loaded[0].response_capture_enabled is False
    assert loaded[0].response_text is None

MULTI_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "web_collector_export_multi_v01.json"
)


def test_web_collector_multi_export_round_trips_into_consumer_store(
    tmp_path: Path,
):
    export = load_export(MULTI_FIXTURE)

    assert export.export_schema_version == "0.1"
    assert export.sample_count == 2
    assert len(export.records) == 2

    assert export.records[0].first_output_measurement_mode == (
        "human-observed-click-v0.1"
    )
    assert export.records[1].generation_failed is True
    assert export.records[1].time_to_first_output_ms is None
    assert export.records[1].first_output_measurement_mode is None

    normalized = normalize_export(
        export,
        observer_id="observer-web-multi-contract-test",
        region_code="CL-Los-Lagos",
        observer_timezone="America/Santiago",
    )

    assert len(normalized) == 2

    store = ConsumerProbeSQLiteStore(
        tmp_path / "collector-multi-contract.db"
    )

    for record in normalized:
        store.append(record)

    loaded = store.load_all()

    assert len(loaded) == 2

    by_probe_id = {
        str(record.probe_id): record
        for record in loaded
    }

    failed = by_probe_id[
        "172d47a0-41a5-4443-8534-01287f763015"
    ]

    assert failed.generation_failed is True
    assert failed.time_to_first_output_ms is None
    assert failed.first_output_measurement_mode is None
    assert failed.response_capture_enabled is False
    assert failed.response_text is None

PUBLIC_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "web_collector_export_public_v01.json"
)


def test_public_web_collector_preserves_unscheduled_provenance():
    export = load_export(PUBLIC_FIXTURE)

    assert export.sample_count == 1

    record = export.records[0]

    assert record.prompt_id == "coding-001"
    assert record.scheduled_at_utc is None
    assert record.schedule_offset_ms is None
    assert record.time_to_first_output_ms is None
    assert record.first_output_measurement_mode is None
    assert record.response_capture_enabled is False
    assert record.response_text is None
