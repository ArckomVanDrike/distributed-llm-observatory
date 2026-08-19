from pathlib import Path

import pytest

from observer.core.benchmark_runner import BenchmarkRunner
from observer.core.recording import build_observation_record
from observer.providers.mock import MockProvider, MockProviderConfig
from observer.storage.jsonl import JSONLObservationStore, ObservationStoreError
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkPrompt,
)


def make_benchmark() -> BenchmarkPrompt:
    return BenchmarkPrompt(
        prompt_id="reasoning-001",
        benchmark_version="0.1",
        category=BenchmarkCategory.REASONING,
        difficulty=BenchmarkDifficulty.EASY,
        prompt="What is 2 + 2?",
    )


def make_record():
    provider = MockProvider(
        MockProviderConfig(
            response_text="4",
            input_tokens=8,
            output_tokens=1,
            latency_ms=200,
            time_to_first_token_ms=50,
        )
    )

    runner = BenchmarkRunner(
        provider=provider,
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        model="mock-model",
    )

    run = runner.run(
        make_benchmark(),
        temperature=0.0,
        max_tokens=64,
    )

    return build_observation_record(run)


def test_build_observation_record():
    record = make_record()

    assert record.observer.observer_id == "observer-test"
    assert record.observer.region_code == "CL-Los-Lagos"

    assert record.benchmark.prompt_id == "reasoning-001"
    assert record.benchmark.category == "reasoning"

    assert record.generation.temperature == 0.0
    assert record.generation.max_tokens == 64

    assert record.execution.provider == "mock"
    assert record.execution.response_text == "4"
    assert record.execution.output_tokens == 1


def test_jsonl_store_appends_and_loads_record(tmp_path: Path):
    path = tmp_path / "observations.jsonl"
    store = JSONLObservationStore(path)

    original = make_record()

    store.append(original)

    records = store.load_all()

    assert len(records) == 1
    assert records[0].observation_id == original.observation_id
    assert records[0].execution.response_text == "4"


def test_jsonl_store_appends_multiple_records(tmp_path: Path):
    path = tmp_path / "observations.jsonl"
    store = JSONLObservationStore(path)

    store.append(make_record())
    store.append(make_record())

    records = store.load_all()

    assert len(records) == 2
    assert records[0].observation_id != records[1].observation_id


def test_jsonl_store_creates_parent_directories(tmp_path: Path):
    path = tmp_path / "nested" / "data" / "observations.jsonl"

    store = JSONLObservationStore(path)
    store.append(make_record())

    assert path.exists()


def test_jsonl_store_returns_empty_list_when_missing(tmp_path: Path):
    store = JSONLObservationStore(tmp_path / "missing.jsonl")

    assert store.load_all() == []


def test_jsonl_store_rejects_corrupted_data(tmp_path: Path):
    path = tmp_path / "observations.jsonl"
    path.write_text('{"broken": true}\n', encoding="utf-8")

    store = JSONLObservationStore(path)

    with pytest.raises(ObservationStoreError, match="line 1"):
        store.load_all()
