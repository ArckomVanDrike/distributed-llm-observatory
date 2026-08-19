from datetime import datetime, timezone

from consumer_probe.aggregation import (
    aggregate_by_region_and_utc,
)
from consumer_probe.baseline import (
    build_historical_baseline,
)
from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
)


def make_record(
    day: int,
    hour: int = 21,
    *,
    region: str = "CL-Los-Lagos",
    platform=ConsumerPlatform.CHATGPT,
    prompt_id: str = "reasoning-001",
    latency: float = 3000,
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
        platform=platform,
        page_hostname="chatgpt.com",
        benchmark_version="0.1",
        prompt_id=prompt_id,
        started_at_utc=timestamp,
        first_output_at_utc=timestamp,
        completed_at_utc=timestamp,
        time_to_first_output_ms=1000,
        total_latency_ms=latency,
    )


def candidate_group():
    record = make_record(
        19,
        hour=21,
        latency=5000,
    )

    return aggregate_by_region_and_utc(
        [record]
    )[0]


def test_baseline_uses_only_prior_records():
    records = [
        make_record(17),
        make_record(18),
        make_record(19),
    ]

    baseline = build_historical_baseline(
        records,
        candidate_group(),
        candidate_start_utc=datetime(
            2026,
            8,
            19,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert baseline.matched_records == 2
    assert baseline.group.analytics.sample_count == 2


def test_baseline_excludes_future_records():
    records = [
        make_record(18),
        make_record(20),
    ]

    baseline = build_historical_baseline(
        records,
        candidate_group(),
        candidate_start_utc=datetime(
            2026,
            8,
            19,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert baseline.matched_records == 1


def test_baseline_matches_same_time_bucket():
    records = [
        make_record(18, hour=21),
        make_record(18, hour=10),
    ]

    baseline = build_historical_baseline(
        records,
        candidate_group(),
        candidate_start_utc=datetime(
            2026,
            8,
            19,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert baseline.matched_records == 1


def test_baseline_matches_region():
    records = [
        make_record(
            18,
            region="CL-Los-Lagos",
        ),
        make_record(
            18,
            region="IT-Lombardia",
        ),
    ]

    baseline = build_historical_baseline(
        records,
        candidate_group(),
        candidate_start_utc=datetime(
            2026,
            8,
            19,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert baseline.matched_records == 1


def test_baseline_matches_platform():
    records = [
        make_record(
            18,
            platform=ConsumerPlatform.CHATGPT,
        ),
        make_record(
            18,
            platform=ConsumerPlatform.CLAUDE,
        ),
    ]

    baseline = build_historical_baseline(
        records,
        candidate_group(),
        candidate_start_utc=datetime(
            2026,
            8,
            19,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert baseline.matched_records == 1


def test_baseline_respects_lookback_window():
    records = [
        make_record(18),
        make_record(10),
    ]

    baseline = build_historical_baseline(
        records,
        candidate_group(),
        candidate_start_utc=datetime(
            2026,
            8,
            19,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        lookback_days=5,
    )

    assert baseline.matched_records == 1


def test_empty_baseline_is_valid():
    baseline = build_historical_baseline(
        [],
        candidate_group(),
        candidate_start_utc=datetime(
            2026,
            8,
            19,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert baseline.matched_records == 0
    assert baseline.group.analytics.sample_count == 0


def test_invalid_lookback_is_rejected():
    try:
        build_historical_baseline(
            [],
            candidate_group(),
            candidate_start_utc=datetime(
                2026,
                8,
                19,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            lookback_days=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError."
        )
