from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from consumer_probe.temporal import validate_bucket_hours


@dataclass(frozen=True)
class SamplingPolicy:
    bucket_hours: int = 4
    samples_per_bucket: int = 1
    edge_guard_minutes: int = 15


def validate_sampling_policy(
    policy: SamplingPolicy,
) -> None:
    validate_bucket_hours(policy.bucket_hours)

    if policy.samples_per_bucket <= 0:
        raise ValueError(
            "samples_per_bucket must be greater than zero."
        )

    bucket_minutes = policy.bucket_hours * 60

    if policy.edge_guard_minutes < 0:
        raise ValueError(
            "edge_guard_minutes cannot be negative."
        )

    if (
        policy.edge_guard_minutes * 2
        >= bucket_minutes
    ):
        raise ValueError(
            "edge_guard_minutes leaves no usable bucket window."
        )


def deterministic_fraction(
    *,
    observer_id: str,
    sampling_date: date,
    bucket_start_hour: int,
    sample_index: int,
) -> float:
    payload = (
        f"{observer_id}|"
        f"{sampling_date.isoformat()}|"
        f"{bucket_start_hour}|"
        f"{sample_index}"
    ).encode()

    digest = hashlib.sha256(payload).digest()

    integer = int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    )

    return integer / ((1 << 64) - 1)


def build_daily_schedule(
    sampling_date: date,
    *,
    observer_id: str,
    policy: SamplingPolicy | None = None,
) -> list[datetime]:
    """
    Build deterministic UTC sampling times for one observer.

    Samples are stratified across UTC buckets and placed inside each
    bucket using deterministic pseudo-random offsets derived from the
    observer ID, date, bucket, and sample index.

    Rebuilding the same schedule produces identical timestamps.
    Different observers naturally receive different offsets.
    """
    policy = policy or SamplingPolicy()

    validate_sampling_policy(policy)

    if not observer_id.strip():
        raise ValueError(
            "observer_id cannot be empty."
        )

    bucket_minutes = policy.bucket_hours * 60

    usable_start = policy.edge_guard_minutes
    usable_end = (
        bucket_minutes
        - policy.edge_guard_minutes
    )

    usable_minutes = usable_end - usable_start

    schedule: list[datetime] = []

    for bucket_start_hour in range(
        0,
        24,
        policy.bucket_hours,
    ):
        bucket_start = datetime(
            sampling_date.year,
            sampling_date.month,
            sampling_date.day,
            bucket_start_hour,
            0,
            tzinfo=timezone.utc,
        )

        for sample_index in range(
            policy.samples_per_bucket
        ):
            fraction = deterministic_fraction(
                observer_id=observer_id,
                sampling_date=sampling_date,
                bucket_start_hour=bucket_start_hour,
                sample_index=sample_index,
            )

            offset_seconds = (
                usable_start * 60
                + fraction * usable_minutes * 60
            )

            schedule.append(
                bucket_start
                + timedelta(
                    seconds=offset_seconds
                )
            )

    return sorted(schedule)
