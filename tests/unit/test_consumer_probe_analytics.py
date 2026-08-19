from datetime import datetime, timezone

import pytest

from consumer_probe.analytics import (
    percentile,
    summarize,
)
from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
)


def make_record(
    *,
    ttfo=1000,
    latency=3000,
    failed=False,
    retry=False,
    interrupted=False,
):
    now = datetime.now(timezone.utc)

    return ConsumerProbeRecord(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        platform=ConsumerPlatform.CHATGPT,
        page_hostname="chatgpt.com",
        benchmark_version="0.1",
        prompt_id="reasoning-001",
        started_at_utc=now,
        first_output_at_utc=now,
        completed_at_utc=now,
        time_to_first_output_ms=ttfo,
        total_latency_ms=latency,
        generation_failed=failed,
        retry_observed=retry,
        interrupted=interrupted,
    )


def test_percentile_empty_values():
    assert percentile([], 95) is None


def test_percentile_single_value():
    assert percentile([42], 95) == 42


def test_percentile_rejects_invalid_percentage():
    with pytest.raises(ValueError):
        percentile([1, 2, 3], 101)


def test_summary_calculates_basic_latency_metrics():
    records = [
        make_record(
            ttfo=1000,
            latency=2000,
        ),
        make_record(
            ttfo=2000,
            latency=4000,
        ),
    ]

    summary = summarize(records)

    assert summary.sample_count == 2
    assert summary.successful_samples == 2

    assert summary.mean_ttfo_ms == 1500
    assert summary.median_ttfo_ms == 1500

    assert summary.mean_latency_ms == 3000
    assert summary.median_latency_ms == 3000

    assert summary.min_latency_ms == 2000
    assert summary.max_latency_ms == 4000

    assert summary.failure_rate == 0
    assert summary.retry_rate == 0


def test_failed_runs_are_excluded_from_latency_statistics():
    records = [
        make_record(
            ttfo=1000,
            latency=3000,
        ),
        make_record(
            ttfo=None,
            latency=None,
            failed=True,
        ),
    ]

    summary = summarize(records)

    assert summary.sample_count == 2
    assert summary.successful_samples == 1
    assert summary.mean_ttfo_ms == 1000
    assert summary.mean_latency_ms == 3000
    assert summary.failure_rate == 0.5


def test_summary_calculates_retry_rate():
    records = [
        make_record(retry=True),
        make_record(retry=False),
        make_record(retry=True),
        make_record(retry=False),
    ]

    summary = summarize(records)

    assert summary.retry_rate == 0.5


def test_summary_calculates_interruption_rate():
    records = [
        make_record(interrupted=True),
        make_record(interrupted=False),
    ]

    summary = summarize(records)

    assert summary.interruption_rate == 0.5
    assert summary.successful_samples == 1


def test_empty_summary_is_safe():
    summary = summarize([])

    assert summary.sample_count == 0
    assert summary.successful_samples == 0

    assert summary.mean_ttfo_ms is None
    assert summary.median_ttfo_ms is None
    assert summary.p95_ttfo_ms is None

    assert summary.mean_latency_ms is None
    assert summary.p95_latency_ms is None

    assert summary.failure_rate == 0
    assert summary.retry_rate == 0
