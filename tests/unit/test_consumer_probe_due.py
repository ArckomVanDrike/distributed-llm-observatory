from datetime import date, datetime, timedelta, timezone

import pytest

from consumer_probe.due import (
    find_due_probe,
    find_next_probe,
)
from observer.core.consumer_schedule import (
    ConsumerDailySchedule,
    ScheduledBenchmark,
)
from schemas.benchmark import BenchmarkPrompt


def make_benchmark(
    prompt_id: str,
) -> BenchmarkPrompt:
    return BenchmarkPrompt(
        prompt_id=prompt_id,
        benchmark_version="0.1",
        category="reasoning",
        difficulty="medium",
        prompt=f"Test prompt for {prompt_id}.",
        expected_characteristics=[
            "Produces a valid response."
        ],
        enabled=True,
    )


def make_schedule() -> ConsumerDailySchedule:
    items = [
        ScheduledBenchmark(
            scheduled_at_utc=datetime(
                2026,
                8,
                19,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            benchmark=make_benchmark(
                "reasoning-001"
            ),
        ),
        ScheduledBenchmark(
            scheduled_at_utc=datetime(
                2026,
                8,
                19,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            benchmark=make_benchmark(
                "reasoning-002"
            ),
        ),
        ScheduledBenchmark(
            scheduled_at_utc=datetime(
                2026,
                8,
                19,
                14,
                0,
                tzinfo=timezone.utc,
            ),
            benchmark=make_benchmark(
                "reasoning-003"
            ),
        ),
    ]

    return ConsumerDailySchedule(
        sampling_date=date(2026, 8, 19),
        observer_id="observer-test",
        benchmark_version="0.1",
        items=items,
    )


def test_probe_is_due_at_exact_scheduled_time():
    schedule = make_schedule()

    result = find_due_probe(
        schedule,
        now_utc=datetime(
            2026,
            8,
            19,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert result is not None
    assert (
        result.item.benchmark.prompt_id
        == "reasoning-001"
    )
    assert result.overdue_by == timedelta(0)


def test_probe_is_due_within_grace_window():
    schedule = make_schedule()

    result = find_due_probe(
        schedule,
        now_utc=datetime(
            2026,
            8,
            19,
            10,
            30,
            tzinfo=timezone.utc,
        ),
        grace_minutes=60,
    )

    assert result is not None
    assert result.overdue_by == timedelta(
        minutes=30
    )


def test_expired_probe_is_not_due():
    schedule = make_schedule()

    result = find_due_probe(
        schedule,
        now_utc=datetime(
            2026,
            8,
            19,
            11,
            1,
            tzinfo=timezone.utc,
        ),
        grace_minutes=60,
    )

    assert result is None


def test_completed_probe_is_skipped():
    schedule = make_schedule()

    result = find_due_probe(
        schedule,
        now_utc=datetime(
            2026,
            8,
            19,
            12,
            15,
            tzinfo=timezone.utc,
        ),
        completed_prompt_ids={
            "reasoning-001",
        },
    )

    assert result is not None
    assert (
        result.item.benchmark.prompt_id
        == "reasoning-002"
    )


def test_next_probe_returns_future_item():
    schedule = make_schedule()

    result = find_next_probe(
        schedule,
        now_utc=datetime(
            2026,
            8,
            19,
            11,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert result is not None
    assert (
        result.benchmark.prompt_id
        == "reasoning-002"
    )


def test_next_probe_skips_completed_future_item():
    schedule = make_schedule()

    result = find_next_probe(
        schedule,
        now_utc=datetime(
            2026,
            8,
            19,
            11,
            0,
            tzinfo=timezone.utc,
        ),
        completed_prompt_ids={
            "reasoning-002",
        },
    )

    assert result is not None
    assert (
        result.benchmark.prompt_id
        == "reasoning-003"
    )


def test_next_probe_returns_none_after_schedule():
    schedule = make_schedule()

    result = find_next_probe(
        schedule,
        now_utc=datetime(
            2026,
            8,
            19,
            16,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert result is None


def test_naive_datetime_is_rejected():
    schedule = make_schedule()

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        find_due_probe(
            schedule,
            now_utc=datetime(
                2026,
                8,
                19,
                10,
                0,
            ),
        )


def test_negative_grace_is_rejected():
    schedule = make_schedule()

    with pytest.raises(
        ValueError,
        match="grace_minutes",
    ):
        find_due_probe(
            schedule,
            now_utc=datetime(
                2026,
                8,
                19,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            grace_minutes=-1,
        )


def test_non_utc_datetime_is_normalized():
    schedule = make_schedule()

    local_timezone = timezone(
        timedelta(hours=-4)
    )

    result = find_due_probe(
        schedule,
        now_utc=datetime(
            2026,
            8,
            19,
            6,
            30,
            tzinfo=local_timezone,
        ),
    )

    assert result is not None
    assert (
        result.item.benchmark.prompt_id
        == "reasoning-001"
    )
    assert result.overdue_by == timedelta(
        minutes=30
    )
