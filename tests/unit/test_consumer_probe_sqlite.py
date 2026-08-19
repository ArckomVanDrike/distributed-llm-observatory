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
