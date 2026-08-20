from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from consumer_probe.aggregation import (
    AggregatedProbeGroup,
    AggregationKey,
)
from consumer_probe.analytics import (
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
class HistoricalBaseline:
    group: AggregatedProbeGroup
    candidate_start_utc: datetime
    lookback_days: int
    matched_records: int


def build_historical_baseline(
    records: list[ConsumerProbeRecord],
    candidate: AggregatedProbeGroup,
    *,
    candidate_start_utc: datetime,
    lookback_days: int = 14,
    bucket_hours: int = 4,
) -> HistoricalBaseline:
    """
    Build a historical baseline without temporal leakage.

    Baseline observations must:

    - precede candidate_start_utc
    - fall within lookback_days
    - match platform
    - match region
    - match benchmark version
    - match prompt
    - match the candidate UTC time-of-day bucket
    """
    validate_bucket_hours(bucket_hours)

    if lookback_days <= 0:
        raise ValueError(
            "lookback_days must be greater than zero."
        )

    if candidate_start_utc.tzinfo is None:
        raise ValueError(
            "candidate_start_utc must be timezone-aware."
        )

    key = candidate.key

    lookback_start = (
        candidate_start_utc
        - timedelta(days=lookback_days)
    )

    matched: list[ConsumerProbeRecord] = []

    for record in records:
        timestamp = record.started_at_utc

        if not (
            lookback_start
            <= timestamp
            < candidate_start_utc
        ):
            continue

        if record.platform.value != key.platform:
            continue

        if record.region_code != key.region_code:
            continue

        if (
            record.benchmark_version
            != key.benchmark_version
        ):
            continue

        if record.prompt_id != key.prompt_id:
            continue

        record_bucket = bucket_start_hour(
            timestamp.hour,
            bucket_hours,
        )

        if record_bucket != key.bucket_start_utc:
            continue

        matched.append(record)

    baseline_group = AggregatedProbeGroup(
        key=AggregationKey(
            platform=key.platform,
            region_code=key.region_code,
            benchmark_version=key.benchmark_version,
            prompt_id=key.prompt_id,
            bucket_start_utc=key.bucket_start_utc,
        ),
        bucket_label=make_bucket_label(
            key.bucket_start_utc,
            bucket_hours,
        ),
        analytics=summarize(matched),
        first_output_by_mode=(
            summarize_first_output_by_mode(
                matched
            )
        ),
    )

    return HistoricalBaseline(
        group=baseline_group,
        candidate_start_utc=candidate_start_utc,
        lookback_days=lookback_days,
        matched_records=len(matched),
    )
