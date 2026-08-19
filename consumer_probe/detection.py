from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from consumer_probe.aggregation import (
    AggregatedProbeGroup,
    AggregationKey,
)
from consumer_probe.analytics import summarize
from consumer_probe.baseline import (
    HistoricalBaseline,
    build_historical_baseline,
)
from consumer_probe.comparison import (
    ComparisonPolicy,
    GroupComparison,
    compare_groups,
)
from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
)
from consumer_probe.temporal import (
    make_bucket_label,
    validate_bucket_hours,
)


@dataclass(frozen=True)
class BucketDetection:
    candidate: AggregatedProbeGroup
    baseline: HistoricalBaseline
    comparison: GroupComparison


def validate_candidate_start(
    candidate_start_utc: datetime,
    bucket_hours: int,
) -> None:
    validate_bucket_hours(bucket_hours)

    if candidate_start_utc.tzinfo is None:
        raise ValueError(
            "candidate_start_utc must be timezone-aware."
        )

    if candidate_start_utc.utcoffset() != timedelta(0):
        raise ValueError(
            "candidate_start_utc must be expressed in UTC."
        )

    if any(
        (
            candidate_start_utc.minute,
            candidate_start_utc.second,
            candidate_start_utc.microsecond,
        )
    ):
        raise ValueError(
            "candidate_start_utc must start on an exact hour."
        )

    if candidate_start_utc.hour % bucket_hours != 0:
        raise ValueError(
            "candidate_start_utc must align with the "
            "configured UTC bucket."
        )


def detect_utc_bucket(
    records: list[ConsumerProbeRecord],
    *,
    candidate_start_utc: datetime,
    platform: ConsumerPlatform,
    region_code: str,
    benchmark_version: str,
    prompt_id: str,
    lookback_days: int = 14,
    bucket_hours: int = 4,
    policy: ComparisonPolicy | None = None,
) -> BucketDetection:
    """
    Evaluate one UTC time bucket against its historical baseline.

    Candidate observations are isolated to one exact UTC bucket.
    Historical observations are strictly earlier than that bucket.
    """
    validate_candidate_start(
        candidate_start_utc,
        bucket_hours,
    )

    candidate_end_utc = (
        candidate_start_utc
        + timedelta(hours=bucket_hours)
    )

    candidate_records: list[ConsumerProbeRecord] = []

    for record in records:
        timestamp = record.started_at_utc.astimezone(
            timezone.utc
        )

        if not (
            candidate_start_utc
            <= timestamp
            < candidate_end_utc
        ):
            continue

        if record.platform != platform:
            continue

        if record.region_code != region_code:
            continue

        if record.benchmark_version != benchmark_version:
            continue

        if record.prompt_id != prompt_id:
            continue

        candidate_records.append(record)

    key = AggregationKey(
        platform=platform.value,
        region_code=region_code,
        benchmark_version=benchmark_version,
        prompt_id=prompt_id,
        bucket_start_utc=candidate_start_utc.hour,
    )

    candidate = AggregatedProbeGroup(
        key=key,
        bucket_label=make_bucket_label(
            candidate_start_utc.hour,
            bucket_hours,
        ),
        analytics=summarize(candidate_records),
    )

    baseline = build_historical_baseline(
        records,
        candidate,
        candidate_start_utc=candidate_start_utc,
        lookback_days=lookback_days,
        bucket_hours=bucket_hours,
    )

    comparison = compare_groups(
        candidate,
        baseline.group,
        policy=policy,
    )

    return BucketDetection(
        candidate=candidate,
        baseline=baseline,
        comparison=comparison,
    )
