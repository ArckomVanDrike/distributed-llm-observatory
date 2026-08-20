from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from consumer_probe.analytics import percentile
from consumer_probe.schemas import ConsumerProbeRecord


@dataclass(frozen=True)
class LocalTelemetryAnalyticsSummary:
    record_count: int

    telemetry_records: int
    telemetry_error_records: int
    uninstrumented_records: int
    pss_records: int

    median_peak_browser_rss_bytes: float | None
    p95_peak_browser_rss_bytes: float | None

    median_peak_browser_pss_bytes: float | None
    p95_peak_browser_pss_bytes: float | None

    median_peak_browser_cpu_percent: float | None
    p95_peak_browser_cpu_percent: float | None

    median_fast_sampling_hz: float | None
    median_pss_sampling_hz: float | None

    minimum_system_memory_available_bytes: int | None
    median_min_system_memory_available_bytes: float | None


def _sampling_hz(
    *,
    sample_count: int,
    duration_ms: float,
) -> float | None:
    if duration_ms <= 0:
        return None

    return (
        sample_count
        / (duration_ms / 1000)
    )


def summarize_local_telemetry_records(
    records: list[ConsumerProbeRecord],
) -> LocalTelemetryAnalyticsSummary:
    telemetry_records = [
        record
        for record in records
        if record.local_telemetry is not None
    ]

    telemetry_error_records = sum(
        record.local_telemetry_error is not None
        for record in records
    )

    uninstrumented_records = sum(
        record.local_telemetry is None
        and record.local_telemetry_error is None
        for record in records
    )

    telemetry = [
        record.local_telemetry
        for record in telemetry_records
        if record.local_telemetry is not None
    ]

    rss_values = [
        float(item.peak_browser_rss_bytes)
        for item in telemetry
        if item.peak_browser_rss_bytes is not None
    ]

    pss_values = [
        float(item.peak_browser_pss_bytes)
        for item in telemetry
        if item.peak_browser_pss_bytes is not None
    ]

    browser_cpu_values = [
        float(item.peak_browser_cpu_percent)
        for item in telemetry
        if item.peak_browser_cpu_percent is not None
    ]

    fast_sampling_rates = [
        rate
        for item in telemetry
        if (
            rate := _sampling_hz(
                sample_count=item.sample_count,
                duration_ms=item.duration_ms,
            )
        )
        is not None
    ]

    pss_sampling_rates = [
        rate
        for item in telemetry
        if item.pss_sample_count is not None
        and item.pss_sample_count > 0
        and (
            rate := _sampling_hz(
                sample_count=item.pss_sample_count,
                duration_ms=item.duration_ms,
            )
        )
        is not None
    ]

    memory_available_values = [
        item.min_system_memory_available_bytes
        for item in telemetry
        if item.min_system_memory_available_bytes is not None
    ]

    return LocalTelemetryAnalyticsSummary(
        record_count=len(records),

        telemetry_records=len(telemetry),
        telemetry_error_records=telemetry_error_records,
        uninstrumented_records=uninstrumented_records,
        pss_records=len(pss_values),

        median_peak_browser_rss_bytes=(
            median(rss_values)
            if rss_values
            else None
        ),
        p95_peak_browser_rss_bytes=percentile(
            rss_values,
            95,
        ),

        median_peak_browser_pss_bytes=(
            median(pss_values)
            if pss_values
            else None
        ),
        p95_peak_browser_pss_bytes=percentile(
            pss_values,
            95,
        ),

        median_peak_browser_cpu_percent=(
            median(browser_cpu_values)
            if browser_cpu_values
            else None
        ),
        p95_peak_browser_cpu_percent=percentile(
            browser_cpu_values,
            95,
        ),

        median_fast_sampling_hz=(
            median(fast_sampling_rates)
            if fast_sampling_rates
            else None
        ),
        median_pss_sampling_hz=(
            median(pss_sampling_rates)
            if pss_sampling_rates
            else None
        ),

        minimum_system_memory_available_bytes=(
            min(memory_available_values)
            if memory_available_values
            else None
        ),
        median_min_system_memory_available_bytes=(
            median(memory_available_values)
            if memory_available_values
            else None
        ),
    )
