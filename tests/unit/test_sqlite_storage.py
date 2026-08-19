from pathlib import Path

import pytest

from observer.core.benchmark_runner import BenchmarkRunner
from observer.core.recording import build_observation_record
from observer.providers.mock import MockProvider, MockProviderConfig
from observer.storage.sqlite import (
    SQLiteObservationStore,
    SQLiteObservationStoreError,
)
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkPrompt,
)


def make_record():
    benchmark = BenchmarkPrompt(
        prompt_id="reasoning-001",
        benchmark_version="0.1",
        category=BenchmarkCategory.REASONING,
        difficulty=BenchmarkDifficulty.EASY,
        prompt="What is 2 + 2?",
    )

    provider = MockProvider(
        MockProviderConfig(
            response_text="4",
            input_tokens=8,
            output_tokens=1,
            latency_ms=200,
        )
    )

    runner = BenchmarkRunner(
        provider=provider,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        model="mock-model",
    )

    return build_observation_record(
        runner.run(
            benchmark,
            temperature=0.0,
            max_tokens=64,
        )
    )


def test_sqlite_store_creates_database(tmp_path: Path):
    path = tmp_path / "observatory.db"

    SQLiteObservationStore(path)

    assert path.exists()


def test_sqlite_store_appends_and_loads_record(tmp_path: Path):
    store = SQLiteObservationStore(tmp_path / "observatory.db")
    original = make_record()

    store.append(original)

    records = store.load_all()

    assert len(records) == 1
    assert records[0].observation_id == original.observation_id
    assert records[0].execution.response_text == "4"


def test_sqlite_store_counts_records(tmp_path: Path):
    store = SQLiteObservationStore(tmp_path / "observatory.db")

    store.append(make_record())
    store.append(make_record())

    assert store.count() == 2


def test_sqlite_store_rejects_duplicate_observation(tmp_path: Path):
    store = SQLiteObservationStore(tmp_path / "observatory.db")
    record = make_record()

    store.append(record)

    with pytest.raises(
        SQLiteObservationStoreError,
        match="already exists",
    ):
        store.append(record)


def test_sqlite_store_creates_parent_directories(tmp_path: Path):
    path = tmp_path / "nested" / "data" / "observatory.db"

    SQLiteObservationStore(path)

    assert path.exists()
