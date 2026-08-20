from datetime import datetime, timedelta, timezone

import pytest

from consumer_probe.comparison import (
    AnomalyLevel,
    ComparisonPolicy,
)
from consumer_probe.detection import detect_utc_bucket
from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
)


def make_record(
    day: int,
    hour: int = 21,
    *,
    latency: float = 3000,
    ttfo: float = 1000,
    region: str = "CL-Los-Lagos",
    first_output_measurement_mode: str | None = None,
) -> ConsumerProbeRecord:
    timestamp = datetime(
        2026,
        8,
        day,
        hour,
        0,
        tzinfo=timezone.utc,
    )

    return ConsumerProbeRecord(
        observer_id="observer-test",
        region_code=region,
        platform=ConsumerPlatform.CHATGPT,
        page_hostname="chatgpt.com",
        benchmark_version="0.1",
        prompt_id="reasoning-001",
        started_at_utc=timestamp,
        first_output_at_utc=timestamp,
        completed_at_utc=timestamp,
        time_to_first_output_ms=ttfo,
        first_output_measurement_mode=(
            first_output_measurement_mode
        ),
        total_latency_ms=latency,
    )


def candidate_start():
    return datetime(
        2026,
        8,
        19,
        20,
        0,
        tzinfo=timezone.utc,
    )


def detect(records, *, policy=None):
    return detect_utc_bucket(
        records,
        candidate_start_utc=candidate_start(),
        platform=ConsumerPlatform.CHATGPT,
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        prompt_id="reasoning-001",
        policy=policy,
    )


def test_candidate_and_baseline_are_separated():
    records = [
        make_record(17),
        make_record(18),
        make_record(19),
    ]

    result = detect(records)

    assert result.candidate.analytics.sample_count == 1
    assert result.baseline.matched_records == 2


def test_small_dataset_is_insufficient():
    result = detect(
        [
            make_record(18),
            make_record(19),
        ]
    )

    assert (
        result.comparison.level
        == AnomalyLevel.INSUFFICIENT_DATA
    )


def test_degraded_candidate_is_detected():
    records = [
        make_record(17, latency=2000),
        make_record(18, latency=2000),
        make_record(19, latency=4000),
        make_record(
            19,
            hour=22,
            latency=4000,
        ),
    ]

    policy = ComparisonPolicy(
        min_samples_per_group=2,
    )

    result = detect(
        records,
        policy=policy,
    )

    assert result.baseline.matched_records == 2
    assert result.candidate.analytics.sample_count == 2

    assert (
        result.comparison.level
        == AnomalyLevel.DEGRADED
    )

    assert result.comparison.latency_ratio == pytest.approx(
        2.0
    )


def test_other_utc_bucket_is_not_candidate_data():
    records = [
        make_record(19, hour=10),
        make_record(19, hour=21),
    ]

    result = detect(records)

    assert result.candidate.analytics.sample_count == 1


def test_unaligned_candidate_start_is_rejected():
    with pytest.raises(
        ValueError,
        match="align",
    ):
        detect_utc_bucket(
            [],
            candidate_start_utc=datetime(
                2026,
                8,
                19,
                21,
                0,
                tzinfo=timezone.utc,
            ),
            platform=ConsumerPlatform.CHATGPT,
            region_code="CL-Los-Lagos",
            benchmark_version="0.1",
            prompt_id="reasoning-001",
        )


def test_non_utc_candidate_start_is_rejected():
    non_utc = timezone(
        timedelta(hours=-4)
    )

    with pytest.raises(
        ValueError,
        match="expressed in UTC",
    ):
        detect_utc_bucket(
            [],
            candidate_start_utc=datetime(
                2026,
                8,
                19,
                20,
                0,
                tzinfo=non_utc,
            ),
            platform=ConsumerPlatform.CHATGPT,
            region_code="CL-Los-Lagos",
            benchmark_version="0.1",
            prompt_id="reasoning-001",
        )


def test_detection_compares_matching_first_output_mode():
    mode = "human-observed-click-v0.1"

    records = [
        make_record(
            17,
            latency=2000,
            ttfo=1000,
            first_output_measurement_mode=mode,
        ),
        make_record(
            18,
            latency=2000,
            ttfo=1000,
            first_output_measurement_mode=mode,
        ),
        make_record(
            19,
            latency=2000,
            ttfo=2000,
            first_output_measurement_mode=mode,
        ),
        make_record(
            19,
            hour=22,
            latency=2000,
            ttfo=2000,
            first_output_measurement_mode=mode,
        ),
    ]

    result = detect(
        records,
        policy=ComparisonPolicy(
            min_samples_per_group=2,
        ),
    )

    assert (
        result.comparison.first_output_measurement_mode
        == mode
    )
    assert result.comparison.ttfo_ratio == pytest.approx(
        2.0
    )
    assert (
        result.comparison.level
        == AnomalyLevel.DEGRADED
    )


def test_detection_does_not_compare_different_first_output_modes():
    baseline_mode = "human-observed-click-v0.1"
    candidate_mode = "future-first-output-v0.1"

    records = [
        make_record(
            17,
            latency=2000,
            ttfo=1000,
            first_output_measurement_mode=baseline_mode,
        ),
        make_record(
            18,
            latency=2000,
            ttfo=1000,
            first_output_measurement_mode=baseline_mode,
        ),
        make_record(
            19,
            latency=2000,
            ttfo=5000,
            first_output_measurement_mode=candidate_mode,
        ),
        make_record(
            19,
            hour=22,
            latency=2000,
            ttfo=5000,
            first_output_measurement_mode=candidate_mode,
        ),
    ]

    result = detect(
        records,
        policy=ComparisonPolicy(
            min_samples_per_group=2,
        ),
    )

    assert result.comparison.ttfo_ratio is None
    assert (
        result.comparison.first_output_measurement_mode
        is None
    )

    # Equal total latency means the incompatible first-output
    # measurements cannot create a false degradation signal.
    assert result.comparison.latency_ratio == pytest.approx(
        1.0
    )
    assert result.comparison.level == AnomalyLevel.NORMAL
