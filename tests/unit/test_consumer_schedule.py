import json
from datetime import date
from pathlib import Path

import pytest

from observer.core.consumer_schedule import (
    ConsumerScheduleError,
    build_prompt_bank_schedule,
)


def write_prompt(
    root: Path,
    *,
    prompt_id: str,
    benchmark_version: str = "0.1",
    enabled: bool = True,
) -> None:
    path = root / f"{prompt_id}.json"
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "prompt_id": prompt_id,
        "benchmark_version": benchmark_version,
        "category": "reasoning",
        "difficulty": "medium",
        "prompt": f"Test prompt for {prompt_id}.",
        "expected_characteristics": [
            "Produces a valid response."
        ],
        "scoring_method": "observatory_rubric_v0.1",
        "enabled": enabled,
    }

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_schedule_loads_enabled_matching_version(
    tmp_path: Path,
):
    write_prompt(
        tmp_path,
        prompt_id="reasoning-001",
    )

    schedule = build_prompt_bank_schedule(
        date(2026, 8, 19),
        observer_id="observer-a",
        benchmark_version="0.1",
        prompt_bank_path=tmp_path,
    )

    assert schedule.benchmark_version == "0.1"
    assert len(schedule.items) == 1

    assert (
        schedule.items[0].benchmark.prompt_id
        == "reasoning-001"
    )


def test_schedule_excludes_disabled_prompts(
    tmp_path: Path,
):
    write_prompt(
        tmp_path,
        prompt_id="reasoning-001",
        enabled=True,
    )

    write_prompt(
        tmp_path,
        prompt_id="reasoning-002",
        enabled=False,
    )

    schedule = build_prompt_bank_schedule(
        date(2026, 8, 19),
        observer_id="observer-a",
        benchmark_version="0.1",
        prompt_bank_path=tmp_path,
    )

    prompt_ids = {
        item.benchmark.prompt_id
        for item in schedule.items
    }

    assert prompt_ids == {
        "reasoning-001",
    }


def test_schedule_excludes_other_versions(
    tmp_path: Path,
):
    write_prompt(
        tmp_path,
        prompt_id="reasoning-001",
        benchmark_version="0.1",
    )

    write_prompt(
        tmp_path,
        prompt_id="reasoning-002",
        benchmark_version="0.2",
    )

    schedule = build_prompt_bank_schedule(
        date(2026, 8, 19),
        observer_id="observer-a",
        benchmark_version="0.1",
        prompt_bank_path=tmp_path,
    )

    prompt_ids = {
        item.benchmark.prompt_id
        for item in schedule.items
    }

    assert prompt_ids == {
        "reasoning-001",
    }


def test_schedule_rejects_missing_version(
    tmp_path: Path,
):
    write_prompt(
        tmp_path,
        prompt_id="reasoning-001",
        benchmark_version="0.1",
    )

    with pytest.raises(
        ConsumerScheduleError,
        match="No enabled benchmark prompts",
    ):
        build_prompt_bank_schedule(
            date(2026, 8, 19),
            observer_id="observer-a",
            benchmark_version="9.9",
            prompt_bank_path=tmp_path,
        )


def test_schedule_is_deterministic(
    tmp_path: Path,
):
    for index in range(1, 5):
        write_prompt(
            tmp_path,
            prompt_id=f"reasoning-00{index}",
        )

    first = build_prompt_bank_schedule(
        date(2026, 8, 19),
        observer_id="observer-a",
        benchmark_version="0.1",
        prompt_bank_path=tmp_path,
    )

    second = build_prompt_bank_schedule(
        date(2026, 8, 19),
        observer_id="observer-a",
        benchmark_version="0.1",
        prompt_bank_path=tmp_path,
    )

    assert first == second


def test_scheduled_items_preserve_full_benchmark(
    tmp_path: Path,
):
    write_prompt(
        tmp_path,
        prompt_id="reasoning-001",
    )

    schedule = build_prompt_bank_schedule(
        date(2026, 8, 19),
        observer_id="observer-a",
        benchmark_version="0.1",
        prompt_bank_path=tmp_path,
    )

    benchmark = schedule.items[0].benchmark

    assert benchmark.prompt_id == "reasoning-001"
    assert benchmark.category.value == "reasoning"
    assert benchmark.difficulty.value == "medium"
    assert benchmark.enabled is True
