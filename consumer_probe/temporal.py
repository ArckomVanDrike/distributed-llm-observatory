from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from consumer_probe.analytics import (
    ProbeAnalyticsSummary,
    summarize,
)
from consumer_probe.schemas import ConsumerProbeRecord


@dataclass(frozen=True)
class TimeBucketSummary:
    start_hour_utc: int
    end_hour_utc: int
    label: str
    analytics: ProbeAnalyticsSummary


@dataclass(frozen=True)
class LocalTimeBucketSummary:
    start_hour_local: int
    end_hour_local: int
    timezone_name: str
    label: str
    analytics: ProbeAnalyticsSummary


def validate_bucket_hours(bucket_hours: int) -> None:
    if bucket_hours <= 0:
        raise ValueError(
            "bucket_hours must be greater than zero."
        )

    if 24 % bucket_hours != 0:
        raise ValueError(
            "bucket_hours must divide 24 evenly."
        )


def bucket_start_hour(
    hour: int,
    bucket_hours: int,
) -> int:
    validate_bucket_hours(bucket_hours)

    if not 0 <= hour <= 23:
        raise ValueError(
            "hour must be between 0 and 23."
        )

    return (hour // bucket_hours) * bucket_hours


def make_bucket_label(
    start_hour: int,
    bucket_hours: int,
    suffix: str = "UTC",
) -> str:
    end_hour = start_hour + bucket_hours

    return (
        f"{start_hour:02d}:00–"
        f"{end_hour:02d}:00 {suffix}"
    )


def summarize_by_utc_bucket(
    records: list[ConsumerProbeRecord],
    *,
    bucket_hours: int = 4,
    include_empty: bool = True,
) -> list[TimeBucketSummary]:
    validate_bucket_hours(bucket_hours)

    buckets: dict[int, list[ConsumerProbeRecord]] = {
        start: []
        for start in range(
            0,
            24,
            bucket_hours,
        )
    }

    for record in records:
        start = bucket_start_hour(
            record.started_at_utc.hour,
            bucket_hours,
        )

        buckets[start].append(record)

    summaries: list[TimeBucketSummary] = []

    for start in sorted(buckets):
        bucket_records = buckets[start]

        if not include_empty and not bucket_records:
            continue

        summaries.append(
            TimeBucketSummary(
                start_hour_utc=start,
                end_hour_utc=start + bucket_hours,
                label=make_bucket_label(
                    start,
                    bucket_hours,
                    "UTC",
                ),
                analytics=summarize(
                    bucket_records
                ),
            )
        )

    return summaries


def resolve_timezone(
    records: list[ConsumerProbeRecord],
    timezone_name: str | None,
) -> str:
    if timezone_name is not None:
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"Invalid timezone: {timezone_name}"
            ) from exc

        return timezone_name

    timezones = {
        record.observer_timezone
        for record in records
        if record.observer_timezone
    }

    if not timezones:
        raise ValueError(
            "Observer timezone is unavailable. "
            "Provide timezone_name explicitly."
        )

    if len(timezones) != 1:
        raise ValueError(
            "Records contain multiple observer timezones. "
            "Analyze them separately or provide timezone_name."
        )

    return next(iter(timezones))


def summarize_by_local_bucket(
    records: list[ConsumerProbeRecord],
    *,
    timezone_name: str | None = None,
    bucket_hours: int = 4,
    include_empty: bool = True,
) -> list[LocalTimeBucketSummary]:
    """
    Group observations using the Observer's local clock.

    timezone_name may be passed explicitly for historical records that
    were collected before observer_timezone became part of the schema.
    """
    validate_bucket_hours(bucket_hours)

    resolved_timezone = resolve_timezone(
        records,
        timezone_name,
    )

    timezone = ZoneInfo(resolved_timezone)

    buckets: dict[int, list[ConsumerProbeRecord]] = {
        start: []
        for start in range(
            0,
            24,
            bucket_hours,
        )
    }

    for record in records:
        local_time = record.started_at_utc.astimezone(
            timezone
        )

        start = bucket_start_hour(
            local_time.hour,
            bucket_hours,
        )

        buckets[start].append(record)

    summaries: list[LocalTimeBucketSummary] = []

    for start in sorted(buckets):
        bucket_records = buckets[start]

        if not include_empty and not bucket_records:
            continue

        summaries.append(
            LocalTimeBucketSummary(
                start_hour_local=start,
                end_hour_local=start + bucket_hours,
                timezone_name=resolved_timezone,
                label=make_bucket_label(
                    start,
                    bucket_hours,
                    resolved_timezone,
                ),
                analytics=summarize(
                    bucket_records
                ),
            )
        )

    return summaries
