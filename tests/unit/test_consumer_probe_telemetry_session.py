from datetime import datetime, timezone

import pytest

from consumer_probe.local_telemetry import (
    LocalTelemetrySample,
    LocalTelemetrySnapshot,
)
from consumer_probe.telemetry_session import (
    TelemetrySession,
    summarize_local_telemetry,
)


def make_sample(
    *,
    rss: int,
    browser_cpu: float | None,
    memory_available: int,
    system_cpu: float | None,
    processes: int = 4,
) -> LocalTelemetrySample:
    return LocalTelemetrySample(
        captured_at_utc=datetime(
            2026,
            8,
            20,
            tzinfo=timezone.utc,
        ),
        interval_ms=250,
        browser_process_count=processes,
        browser_rss_bytes=rss,
        browser_pss_bytes=rss // 2,
        browser_cpu_percent=browser_cpu,
        system_memory_available_bytes=(
            memory_available
        ),
        system_cpu_percent=system_cpu,
    )


def test_summary_tracks_local_resource_peaks():
    summary = summarize_local_telemetry(
        [
            make_sample(
                rss=100,
                browser_cpu=20,
                memory_available=1000,
                system_cpu=30,
                processes=4,
            ),
            make_sample(
                rss=250,
                browser_cpu=80,
                memory_available=700,
                system_cpu=60,
                processes=6,
            ),
            make_sample(
                rss=200,
                browser_cpu=40,
                memory_available=800,
                system_cpu=45,
                processes=5,
            ),
        ],
        duration_ms=750,
    )

    assert summary.sample_count == 3
    assert summary.duration_ms == 750

    assert (
        summary.peak_browser_process_count
        == 6
    )
    assert summary.peak_browser_rss_bytes == 250
    assert summary.peak_browser_pss_bytes == 125
    assert summary.peak_browser_cpu_percent == 80

    assert (
        summary.min_system_memory_available_bytes
        == 700
    )
    assert summary.peak_system_cpu_percent == 60


def test_empty_summary_preserves_duration():
    summary = summarize_local_telemetry(
        [],
        duration_ms=125,
    )

    assert summary.sample_count == 0
    assert summary.duration_ms == 125
    assert summary.peak_browser_rss_bytes is None
    assert summary.peak_browser_pss_bytes is None
    assert summary.peak_browser_cpu_percent is None


def test_negative_summary_duration_is_rejected():
    with pytest.raises(
        ValueError,
        match="duration_ms",
    ):
        summarize_local_telemetry(
            [],
            duration_ms=-1,
        )


def test_session_collects_and_summarizes_samples():
    captured = 0

    def capture() -> LocalTelemetrySnapshot:
        nonlocal captured
        captured += 1

        return LocalTelemetrySnapshot(
            captured_at_utc=datetime(
                2026,
                8,
                20,
                tzinfo=timezone.utc,
            ),
            monotonic_ns=(
                captured * 1_000_000_000
            ),
            browser_process_count=4,
            browser_rss_bytes=(
                captured * 100
            ),
            browser_pss_bytes=None,
            browser_cpu_ticks=(
                captured * 50
            ),
            system_memory_available_bytes=(
                10_000 - captured * 100
            ),
            system_cpu_total_ticks=(
                captured * 100
            ),
            system_cpu_idle_ticks=(
                captured * 50
            ),
        )

    session = TelemetrySession(
        sample_interval_seconds=60,
        capture=capture,
        clock_ticks_per_second=100,
    )

    session.start()

    result = session.stop()

    assert len(result.samples) == 1

    assert (
        result.summary.peak_browser_rss_bytes
        == 200
    )

    assert (
        result.summary.peak_browser_cpu_percent
        == pytest.approx(50)
    )

    assert (
        result.summary.peak_system_cpu_percent
        == pytest.approx(50)
    )

    assert result.summary.duration_ms == 1000


def test_session_cannot_be_stopped_before_start():
    session = TelemetrySession()

    with pytest.raises(
        RuntimeError,
        match="not been started",
    ):
        session.stop()


def test_sample_interval_must_be_positive():
    with pytest.raises(
        ValueError,
        match="sample_interval_seconds",
    ):
        TelemetrySession(
            sample_interval_seconds=0,
        )
