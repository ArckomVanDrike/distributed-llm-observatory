from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
    LocalTelemetryRecord,
)
from consumer_probe.telemetry_analytics import (
    summarize_local_telemetry_by_collector,
    summarize_local_telemetry_for_collector,
    summarize_local_telemetry_records,
)


def make_record(
    *,
    rss: int | None = 1000,
    pss: int | None = 700,
    pss_samples: int | None = 2,
    browser_cpu: float | None = 50,
    memory_available: int | None = 5000,
    samples: int = 4,
    duration_ms: float = 1000,
    telemetry_error: str | None = None,
    with_telemetry: bool = True,
) -> ConsumerProbeRecord:
    probe_id = uuid4()

    started = datetime(
        2026,
        8,
        20,
        tzinfo=timezone.utc,
    )

    telemetry = None

    if with_telemetry:
        telemetry = LocalTelemetryRecord(
            probe_id=probe_id,
            started_at_utc=started,
            stopped_at_utc=(
                started
                + timedelta(
                    milliseconds=duration_ms
                )
            ),
            sample_count=samples,
            duration_ms=duration_ms,
            collector_version=(
                "linux-proc-firefox-tree-fastslow-v0.1"
            ),
            browser_scope="firefox-process-tree",
            memory_method="rss+pss",
            fast_interval_target_ms=250,
            pss_interval_target_ms=1500,
            peak_browser_process_count=5,
            peak_browser_rss_bytes=rss,
            peak_browser_pss_bytes=pss,
            pss_sample_count=pss_samples,
            peak_browser_cpu_percent=browser_cpu,
            min_system_memory_available_bytes=(
                memory_available
            ),
            peak_system_cpu_percent=30,
        )

    return ConsumerProbeRecord(
        probe_id=probe_id,
        observer_id="observer-test",
        region_code="TEST-LOCAL",
        platform=ConsumerPlatform.CHATGPT,
        benchmark_version="0.1",
        prompt_id="technical-001",
        started_at_utc=started,
        completed_at_utc=(
            started + timedelta(seconds=1)
        ),
        total_latency_ms=1000,
        local_telemetry=telemetry,
        local_telemetry_error=telemetry_error,
    )


def test_summary_counts_instrumentation_states():
    records = [
        make_record(),
        make_record(
            with_telemetry=False,
            telemetry_error="failed",
        ),
        make_record(
            with_telemetry=False,
        ),
    ]

    summary = summarize_local_telemetry_records(
        records
    )

    assert summary.record_count == 3
    assert summary.telemetry_records == 1
    assert summary.telemetry_error_records == 1
    assert summary.uninstrumented_records == 1
    assert summary.pss_records == 1


def test_summary_calculates_memory_metrics():
    records = [
        make_record(
            rss=1000,
            pss=600,
        ),
        make_record(
            rss=3000,
            pss=1800,
        ),
    ]

    summary = summarize_local_telemetry_records(
        records
    )

    assert (
        summary.median_peak_browser_rss_bytes
        == 2000
    )

    assert (
        summary.median_peak_browser_pss_bytes
        == 1200
    )

    assert (
        summary.p95_peak_browser_rss_bytes
        == pytest.approx(2900)
    )

    assert (
        summary.p95_peak_browser_pss_bytes
        == pytest.approx(1740)
    )


def test_summary_calculates_browser_cpu_metrics():
    records = [
        make_record(
            browser_cpu=50,
        ),
        make_record(
            browser_cpu=150,
        ),
    ]

    summary = summarize_local_telemetry_records(
        records
    )

    assert (
        summary.median_peak_browser_cpu_percent
        == 100
    )

    assert (
        summary.p95_peak_browser_cpu_percent
        == pytest.approx(145)
    )


def test_summary_calculates_sampling_rates():
    records = [
        make_record(
            samples=4,
            pss_samples=2,
            duration_ms=1000,
        ),
        make_record(
            samples=8,
            pss_samples=2,
            duration_ms=2000,
        ),
    ]

    summary = summarize_local_telemetry_records(
        records
    )

    assert (
        summary.median_fast_sampling_hz
        == pytest.approx(4)
    )

    assert (
        summary.median_pss_sampling_hz
        == pytest.approx(1.5)
    )


def test_summary_tracks_system_memory_pressure():
    records = [
        make_record(
            memory_available=5000,
        ),
        make_record(
            memory_available=3000,
        ),
        make_record(
            memory_available=7000,
        ),
    ]

    summary = summarize_local_telemetry_records(
        records
    )

    assert (
        summary.minimum_system_memory_available_bytes
        == 3000
    )

    assert (
        summary.median_min_system_memory_available_bytes
        == 5000
    )


def test_legacy_only_dataset_returns_empty_metrics():
    records = [
        make_record(
            with_telemetry=False,
        ),
        make_record(
            with_telemetry=False,
        ),
    ]

    summary = summarize_local_telemetry_records(
        records
    )

    assert summary.telemetry_records == 0
    assert summary.pss_records == 0

    assert (
        summary.median_peak_browser_rss_bytes
        is None
    )

    assert (
        summary.median_peak_browser_pss_bytes
        is None
    )

    assert summary.median_fast_sampling_hz is None
    assert summary.median_pss_sampling_hz is None


def test_collector_summary_does_not_mix_versions():
    collector_a = (
        "linux-proc-firefox-tree-fastslow-v0.1"
    )
    collector_b = "synthetic-collector-v0.2"

    record_a = make_record(
        rss=1000,
    )

    record_b = make_record(
        rss=9000,
    )

    assert record_b.local_telemetry is not None

    record_b.local_telemetry.collector_version = (
        collector_b
    )

    summary = (
        summarize_local_telemetry_for_collector(
            [record_a, record_b],
            collector_a,
        )
    )

    assert summary.record_count == 1
    assert summary.telemetry_records == 1
    assert (
        summary.median_peak_browser_rss_bytes
        == 1000
    )


def test_collector_breakdown_separates_versions():
    collector_a = (
        "linux-proc-firefox-tree-fastslow-v0.1"
    )
    collector_b = "synthetic-collector-v0.2"

    record_a = make_record(
        rss=1000,
    )

    record_b = make_record(
        rss=9000,
    )

    assert record_b.local_telemetry is not None

    record_b.local_telemetry.collector_version = (
        collector_b
    )

    breakdown = (
        summarize_local_telemetry_by_collector(
            [record_a, record_b]
        )
    )

    assert set(breakdown) == {
        collector_a,
        collector_b,
    }

    assert (
        breakdown[
            collector_a
        ].median_peak_browser_rss_bytes
        == 1000
    )

    assert (
        breakdown[
            collector_b
        ].median_peak_browser_rss_bytes
        == 9000
    )


def test_collector_breakdown_keeps_legacy_separate():
    current = make_record(
        rss=1000,
    )

    legacy = make_record(
        rss=5000,
    )

    assert legacy.local_telemetry is not None

    legacy.local_telemetry.telemetry_schema_version = (
        "0.1"
    )
    legacy.local_telemetry.collector_version = None
    legacy.local_telemetry.browser_scope = None
    legacy.local_telemetry.memory_method = None
    legacy.local_telemetry.fast_interval_target_ms = None
    legacy.local_telemetry.pss_interval_target_ms = None

    breakdown = (
        summarize_local_telemetry_by_collector(
            [current, legacy]
        )
    )

    assert None in breakdown

    assert (
        breakdown[
            None
        ].median_peak_browser_rss_bytes
        == 5000
    )

    assert (
        breakdown[
            "linux-proc-firefox-tree-fastslow-v0.1"
        ].median_peak_browser_rss_bytes
        == 1000
    )
