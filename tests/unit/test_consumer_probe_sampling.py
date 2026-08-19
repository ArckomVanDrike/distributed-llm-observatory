from datetime import date

import pytest

from consumer_probe.sampling import (
    SamplingPolicy,
    build_daily_schedule,
)


def test_schedule_is_reproducible():
    sampling_date = date(2026, 8, 19)

    first = build_daily_schedule(
        sampling_date,
        observer_id="observer-a",
    )

    second = build_daily_schedule(
        sampling_date,
        observer_id="observer-a",
    )

    assert first == second


def test_different_observers_receive_different_offsets():
    sampling_date = date(2026, 8, 19)

    first = build_daily_schedule(
        sampling_date,
        observer_id="observer-a",
    )

    second = build_daily_schedule(
        sampling_date,
        observer_id="observer-b",
    )

    assert first != second


def test_default_policy_covers_all_four_hour_buckets():
    schedule = build_daily_schedule(
        date(2026, 8, 19),
        observer_id="observer-a",
    )

    assert len(schedule) == 6

    bucket_starts = {
        (timestamp.hour // 4) * 4
        for timestamp in schedule
    }

    assert bucket_starts == {
        0,
        4,
        8,
        12,
        16,
        20,
    }


def test_multiple_samples_per_bucket():
    policy = SamplingPolicy(
        bucket_hours=4,
        samples_per_bucket=3,
    )

    schedule = build_daily_schedule(
        date(2026, 8, 19),
        observer_id="observer-a",
        policy=policy,
    )

    assert len(schedule) == 18

    counts = {
        bucket: 0
        for bucket in range(0, 24, 4)
    }

    for timestamp in schedule:
        bucket = (
            timestamp.hour // 4
        ) * 4

        counts[bucket] += 1

    assert all(
        count == 3
        for count in counts.values()
    )


def test_schedule_respects_edge_guard():
    policy = SamplingPolicy(
        bucket_hours=4,
        samples_per_bucket=5,
        edge_guard_minutes=15,
    )

    schedule = build_daily_schedule(
        date(2026, 8, 19),
        observer_id="observer-a",
        policy=policy,
    )

    for timestamp in schedule:
        bucket_start_hour = (
            timestamp.hour // 4
        ) * 4

        minutes_from_bucket_start = (
            (timestamp.hour - bucket_start_hour) * 60
            + timestamp.minute
            + timestamp.second / 60
            + timestamp.microsecond / 60_000_000
        )

        assert minutes_from_bucket_start >= 15
        assert minutes_from_bucket_start < 225


def test_schedule_is_sorted():
    schedule = build_daily_schedule(
        date(2026, 8, 19),
        observer_id="observer-a",
        policy=SamplingPolicy(
            samples_per_bucket=4,
        ),
    )

    assert schedule == sorted(schedule)


def test_empty_observer_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="observer_id cannot be empty",
    ):
        build_daily_schedule(
            date(2026, 8, 19),
            observer_id="   ",
        )


def test_invalid_sample_count_is_rejected():
    with pytest.raises(
        ValueError,
        match="samples_per_bucket",
    ):
        build_daily_schedule(
            date(2026, 8, 19),
            observer_id="observer-a",
            policy=SamplingPolicy(
                samples_per_bucket=0,
            ),
        )


def test_negative_edge_guard_is_rejected():
    with pytest.raises(
        ValueError,
        match="edge_guard_minutes",
    ):
        build_daily_schedule(
            date(2026, 8, 19),
            observer_id="observer-a",
            policy=SamplingPolicy(
                edge_guard_minutes=-1,
            ),
        )


def test_edge_guard_cannot_consume_bucket():
    with pytest.raises(
        ValueError,
        match="no usable bucket window",
    ):
        build_daily_schedule(
            date(2026, 8, 19),
            observer_id="observer-a",
            policy=SamplingPolicy(
                bucket_hours=4,
                edge_guard_minutes=120,
            ),
        )
