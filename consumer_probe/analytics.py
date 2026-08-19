from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, median, stdev

from consumer_probe.schemas import ConsumerProbeRecord


@dataclass(frozen=True)
class ProbeAnalyticsSummary:
    sample_count: int
    successful_samples: int

    mean_ttfo_ms: float | None
    median_ttfo_ms: float | None
    p95_ttfo_ms: float | None

    mean_latency_ms: float | None
    median_latency_ms: float | None
    p95_latency_ms: float | None

    min_latency_ms: float | None
    max_latency_ms: float | None
    latency_stdev_ms: float | None

    failure_rate: float
    retry_rate: float
    interruption_rate: float


def percentile(
    values: list[float],
    percentile_value: float,
) -> float | None:
    """
    Calculate a percentile using linear interpolation.

    This follows the common type-7 percentile definition used by
    many statistical systems.

    percentile_value must be between 0 and 100.
    """
    if not values:
        return None

    if not 0 <= percentile_value <= 100:
        raise ValueError(
            "percentile_value must be between 0 and 100."
        )

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (
        percentile_value / 100
    ) * (len(ordered) - 1)

    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    if lower_index == upper_index:
        return ordered[lower_index]

    fraction = position - lower_index

    return (
        ordered[lower_index]
        + (
            ordered[upper_index]
            - ordered[lower_index]
        )
        * fraction
    )


def summarize(
    records: list[ConsumerProbeRecord],
) -> ProbeAnalyticsSummary:
    sample_count = len(records)

    successful_records = [
        record
        for record in records
        if not record.generation_failed
        and not record.interrupted
    ]

    ttfo_values = [
        float(record.time_to_first_output_ms)
        for record in successful_records
        if record.time_to_first_output_ms is not None
    ]

    latency_values = [
        float(record.total_latency_ms)
        for record in successful_records
        if record.total_latency_ms is not None
    ]

    failures = sum(
        record.generation_failed
        for record in records
    )

    retries = sum(
        record.retry_observed
        for record in records
    )

    interruptions = sum(
        record.interrupted
        for record in records
    )

    return ProbeAnalyticsSummary(
        sample_count=sample_count,
        successful_samples=len(successful_records),

        mean_ttfo_ms=(
            mean(ttfo_values)
            if ttfo_values
            else None
        ),
        median_ttfo_ms=(
            median(ttfo_values)
            if ttfo_values
            else None
        ),
        p95_ttfo_ms=percentile(
            ttfo_values,
            95,
        ),

        mean_latency_ms=(
            mean(latency_values)
            if latency_values
            else None
        ),
        median_latency_ms=(
            median(latency_values)
            if latency_values
            else None
        ),
        p95_latency_ms=percentile(
            latency_values,
            95,
        ),

        min_latency_ms=(
            min(latency_values)
            if latency_values
            else None
        ),
        max_latency_ms=(
            max(latency_values)
            if latency_values
            else None
        ),
        latency_stdev_ms=(
            stdev(latency_values)
            if len(latency_values) >= 2
            else None
        ),

        failure_rate=(
            failures / sample_count
            if sample_count
            else 0.0
        ),
        retry_rate=(
            retries / sample_count
            if sample_count
            else 0.0
        ),
        interruption_rate=(
            interruptions / sample_count
            if sample_count
            else 0.0
        ),
    )


@dataclass(frozen=True)
class ScheduleAdherenceSummary:
    sample_count: int
    scheduled_samples: int
    unscheduled_samples: int

    early_samples: int
    late_samples: int
    exact_samples: int

    median_offset_ms: float | None
    p95_offset_ms: float | None

    median_absolute_offset_ms: float | None
    p95_absolute_offset_ms: float | None

    tolerance_ms: float
    within_tolerance_samples: int
    within_tolerance_rate: float | None


def summarize_schedule_adherence(
    records: list[ConsumerProbeRecord],
    *,
    tolerance_ms: float = 300_000,
) -> ScheduleAdherenceSummary:
    """
    Summarize how closely scheduled Consumer Probes followed their slots.

    schedule_offset_ms is signed:

    - negative: probe started before its scheduled slot
    - zero: probe started exactly on schedule
    - positive: probe started after its scheduled slot

    Legacy/manual records without schedule provenance are kept in the
    sample count but excluded from offset statistics.
    """
    if tolerance_ms < 0:
        raise ValueError(
            "tolerance_ms cannot be negative."
        )

    offsets = [
        float(record.schedule_offset_ms)
        for record in records
        if record.schedule_offset_ms is not None
    ]

    absolute_offsets = [
        abs(offset)
        for offset in offsets
    ]

    early_samples = sum(
        offset < 0
        for offset in offsets
    )

    late_samples = sum(
        offset > 0
        for offset in offsets
    )

    exact_samples = sum(
        offset == 0
        for offset in offsets
    )

    within_tolerance_samples = sum(
        absolute_offset <= tolerance_ms
        for absolute_offset in absolute_offsets
    )

    scheduled_samples = len(offsets)

    return ScheduleAdherenceSummary(
        sample_count=len(records),
        scheduled_samples=scheduled_samples,
        unscheduled_samples=(
            len(records) - scheduled_samples
        ),

        early_samples=early_samples,
        late_samples=late_samples,
        exact_samples=exact_samples,

        median_offset_ms=(
            median(offsets)
            if offsets
            else None
        ),
        p95_offset_ms=percentile(
            offsets,
            95,
        ),

        median_absolute_offset_ms=(
            median(absolute_offsets)
            if absolute_offsets
            else None
        ),
        p95_absolute_offset_ms=percentile(
            absolute_offsets,
            95,
        ),

        tolerance_ms=tolerance_ms,
        within_tolerance_samples=(
            within_tolerance_samples
        ),
        within_tolerance_rate=(
            within_tolerance_samples
            / scheduled_samples
            if scheduled_samples
            else None
        ),
    )
