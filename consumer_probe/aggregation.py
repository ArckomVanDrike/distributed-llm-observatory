from __future__ import annotations

from dataclasses import dataclass, field

from consumer_probe.analytics import (
    FirstOutputMeasurementSummary,
    ProbeAnalyticsSummary,
    summarize,
    summarize_first_output_by_mode,
)
from consumer_probe.schemas import ConsumerProbeRecord
from consumer_probe.temporal import (
    bucket_start_hour,
    make_bucket_label,
    validate_bucket_hours,
)


@dataclass(frozen=True)
class AggregationKey:
    platform: str
    region_code: str
    benchmark_version: str
    prompt_id: str
    bucket_start_utc: int


@dataclass(frozen=True)
class AggregatedProbeGroup:
    key: AggregationKey
    bucket_label: str
    analytics: ProbeAnalyticsSummary

    first_output_by_mode: dict[
        str | None,
        FirstOutputMeasurementSummary,
    ] = field(default_factory=dict)


def aggregate_by_region_and_utc(
    records: list[ConsumerProbeRecord],
    *,
    bucket_hours: int = 4,
) -> list[AggregatedProbeGroup]:
    """
    Aggregate observations by:

    - platform
    - observer region
    - benchmark version
    - prompt ID
    - UTC time bucket

    This is the canonical aggregation intended for cross-region
    comparisons in the distributed Observatory.
    """
    validate_bucket_hours(bucket_hours)

    groups: dict[
        AggregationKey,
        list[ConsumerProbeRecord],
    ] = {}

    for record in records:
        bucket_start = bucket_start_hour(
            record.started_at_utc.hour,
            bucket_hours,
        )

        key = AggregationKey(
            platform=record.platform.value,
            region_code=record.region_code,
            benchmark_version=record.benchmark_version,
            prompt_id=record.prompt_id,
            bucket_start_utc=bucket_start,
        )

        groups.setdefault(key, []).append(record)

    results: list[AggregatedProbeGroup] = []

    for key in sorted(
        groups,
        key=lambda item: (
            item.platform,
            item.region_code,
            item.benchmark_version,
            item.prompt_id,
            item.bucket_start_utc,
        ),
    ):
        results.append(
            AggregatedProbeGroup(
                key=key,
                bucket_label=make_bucket_label(
                    key.bucket_start_utc,
                    bucket_hours,
                ),
                analytics=summarize(
                    groups[key]
                ),
                first_output_by_mode=(
                    summarize_first_output_by_mode(
                        groups[key]
                    )
                ),
            )
        )

    return results
