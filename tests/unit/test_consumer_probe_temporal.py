from datetime import datetime, timezone

import pytest

from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
)
from consumer_probe.temporal import (
    bucket_start_hour,
    make_bucket_label,
    summarize_by_local_bucket,
    summarize_by_utc_bucket,
)


def make_record(
    hour: int,
    *,
    ttfo: float = 1000,
    latency: float = 3000,
) -> ConsumerProbeRecord:
    timestamp = datetime(
        2026,
        8,
        19,
        hour,
        0,
        tzinfo=timezone.utc,
    )

    return ConsumerProbeRecord(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        platform=ConsumerPlatform.CHATGPT,
        page_hostname="chatgpt.com",
        benchmark_version="0.1",
        prompt_id="reasoning-001",
        started_at_utc=timestamp,
        first_output_at_utc=timestamp,
        completed_at_utc=timestamp,
        time_to_first_output_ms=ttfo,
        total_latency_ms=latency,
    )


@pytest.mark.parametrize(
    ("hour", "expected"),
    [
        (0, 0),
        (3, 0),
        (4, 4),
        (7, 4),
        (8, 8),
        (23, 20),
    ],
)
def test_four_hour_bucket_start(hour, expected):
    assert bucket_start_hour(
        hour,
        4,
    ) == expected


def test_bucket_label():
    assert make_bucket_label(
        8,
        4,
    ) == "08:00–12:00 UTC"


def test_invalid_bucket_size_is_rejected():
    with pytest.raises(ValueError):
        summarize_by_utc_bucket(
            [],
            bucket_hours=5,
        )


def test_records_are_grouped_by_utc_time():
    records = [
        make_record(
            1,
            ttfo=1000,
            latency=2000,
        ),
        make_record(
            3,
            ttfo=2000,
            latency=4000,
        ),
        make_record(
            9,
            ttfo=3000,
            latency=6000,
        ),
    ]

    buckets = summarize_by_utc_bucket(
        records,
        bucket_hours=4,
    )

    first = buckets[0]
    third = buckets[2]

    assert first.label == "00:00–04:00 UTC"
    assert first.analytics.sample_count == 2
    assert first.analytics.mean_ttfo_ms == 1500
    assert first.analytics.mean_latency_ms == 3000

    assert third.label == "08:00–12:00 UTC"
    assert third.analytics.sample_count == 1
    assert third.analytics.mean_ttfo_ms == 3000


def test_empty_buckets_are_included_by_default():
    buckets = summarize_by_utc_bucket(
        [],
        bucket_hours=4,
    )

    assert len(buckets) == 6
    assert all(
        bucket.analytics.sample_count == 0
        for bucket in buckets
    )


def test_empty_buckets_can_be_excluded():
    buckets = summarize_by_utc_bucket(
        [
            make_record(13),
        ],
        bucket_hours=4,
        include_empty=False,
    )

    assert len(buckets) == 1
    assert buckets[0].label == "12:00–16:00 UTC"


def test_midnight_and_late_night_are_separate():
    buckets = summarize_by_utc_bucket(
        [
            make_record(0),
            make_record(23),
        ],
        bucket_hours=4,
        include_empty=False,
    )

    assert len(buckets) == 2
    assert buckets[0].start_hour_utc == 0
    assert buckets[1].start_hour_utc == 20


def test_local_bucket_converts_from_utc():
    record = make_record(
        21,
        ttfo=1500,
        latency=3500,
    )

    buckets = summarize_by_local_bucket(
        [record],
        timezone_name="America/Santiago",
        bucket_hours=4,
        include_empty=False,
    )

    assert len(buckets) == 1
    assert buckets[0].start_hour_local == 16
    assert buckets[0].label == (
        "16:00–20:00 America/Santiago"
    )
    assert buckets[0].analytics.sample_count == 1


def test_local_bucket_uses_record_timezone():
    record = make_record(21)
    record.observer_timezone = "America/Santiago"

    buckets = summarize_by_local_bucket(
        [record],
        bucket_hours=4,
        include_empty=False,
    )

    assert buckets[0].start_hour_local == 16


def test_local_bucket_requires_timezone():
    record = make_record(21)

    with pytest.raises(
        ValueError,
        match="timezone is unavailable",
    ):
        summarize_by_local_bucket(
            [record],
            include_empty=False,
        )


def test_local_bucket_rejects_invalid_timezone():
    record = make_record(21)

    with pytest.raises(ValueError):
        summarize_by_local_bucket(
            [record],
            timezone_name="Planet/Mars",
        )
