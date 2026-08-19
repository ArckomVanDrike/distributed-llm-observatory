from datetime import datetime, timedelta, timezone

import pytest

from consumer_probe.analytics import (
    summarize_schedule_adherence,
)
from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
)


def make_record(
    *,
    offset_ms: float | None,
) -> ConsumerProbeRecord:
    started = datetime(
        2026,
        8,
        19,
        20,
        0,
        tzinfo=timezone.utc,
    )

    scheduled = None

    if offset_ms is not None:
        scheduled = (
            started
            - timedelta(
                milliseconds=offset_ms
            )
        )

    return ConsumerProbeRecord(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        platform=ConsumerPlatform.CHATGPT,
        benchmark_version="0.1",
        prompt_id="mathematics-001",
        scheduled_at_utc=scheduled,
        schedule_offset_ms=offset_ms,
        started_at_utc=started,
        first_output_at_utc=(
            started + timedelta(seconds=1)
        ),
        completed_at_utc=(
            started + timedelta(seconds=3)
        ),
        time_to_first_output_ms=1000,
        total_latency_ms=3000,
    )


def test_schedule_adherence_separates_legacy_samples():
    records = [
        make_record(offset_ms=1000),
        make_record(offset_ms=None),
        make_record(offset_ms=None),
    ]

    summary = summarize_schedule_adherence(
        records
    )

    assert summary.sample_count == 3
    assert summary.scheduled_samples == 1
    assert summary.unscheduled_samples == 2


def test_schedule_adherence_tracks_early_and_late():
    records = [
        make_record(offset_ms=-60_000),
        make_record(offset_ms=0),
        make_record(offset_ms=120_000),
    ]

    summary = summarize_schedule_adherence(
        records
    )

    assert summary.early_samples == 1
    assert summary.exact_samples == 1
    assert summary.late_samples == 1


def test_schedule_adherence_calculates_signed_median():
    records = [
        make_record(offset_ms=-60_000),
        make_record(offset_ms=60_000),
        make_record(offset_ms=180_000),
    ]

    summary = summarize_schedule_adherence(
        records
    )

    assert summary.median_offset_ms == 60_000


def test_schedule_adherence_calculates_absolute_metrics():
    records = [
        make_record(offset_ms=-60_000),
        make_record(offset_ms=120_000),
        make_record(offset_ms=300_000),
    ]

    summary = summarize_schedule_adherence(
        records
    )

    assert (
        summary.median_absolute_offset_ms
        == 120_000
    )

    assert (
        summary.p95_absolute_offset_ms
        == pytest.approx(282_000)
    )


def test_default_tolerance_is_plus_or_minus_five_minutes():
    records = [
        make_record(offset_ms=-300_000),
        make_record(offset_ms=0),
        make_record(offset_ms=300_000),
        make_record(offset_ms=300_001),
    ]

    summary = summarize_schedule_adherence(
        records
    )

    assert summary.tolerance_ms == 300_000
    assert summary.within_tolerance_samples == 3
    assert summary.within_tolerance_rate == pytest.approx(
        0.75
    )


def test_custom_tolerance_is_supported():
    records = [
        make_record(offset_ms=30_000),
        make_record(offset_ms=90_000),
    ]

    summary = summarize_schedule_adherence(
        records,
        tolerance_ms=60_000,
    )

    assert summary.within_tolerance_samples == 1
    assert summary.within_tolerance_rate == 0.5


def test_legacy_only_dataset_has_no_adherence_rate():
    summary = summarize_schedule_adherence(
        [
            make_record(offset_ms=None),
            make_record(offset_ms=None),
        ]
    )

    assert summary.scheduled_samples == 0
    assert summary.unscheduled_samples == 2

    assert summary.median_offset_ms is None
    assert summary.p95_offset_ms is None

    assert (
        summary.median_absolute_offset_ms
        is None
    )

    assert (
        summary.p95_absolute_offset_ms
        is None
    )

    assert summary.within_tolerance_rate is None


def test_negative_tolerance_is_rejected():
    with pytest.raises(
        ValueError,
        match="tolerance_ms",
    ):
        summarize_schedule_adherence(
            [],
            tolerance_ms=-1,
        )
