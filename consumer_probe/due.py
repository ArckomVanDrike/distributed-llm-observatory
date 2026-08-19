from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from observer.core.consumer_schedule import (
    ConsumerDailySchedule,
    ScheduledBenchmark,
)


@dataclass(frozen=True)
class DueProbe:
    item: ScheduledBenchmark
    overdue_by: timedelta


def normalize_utc(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        raise ValueError(
            "datetime must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def find_due_probe(
    schedule: ConsumerDailySchedule,
    *,
    now_utc: datetime,
    completed_prompt_ids: set[str] | None = None,
    grace_minutes: int = 60,
) -> DueProbe | None:
    """
    Return the earliest scheduled benchmark that is due and incomplete.

    A benchmark is considered actionable from its scheduled time until
    grace_minutes after that time. Completed prompts are skipped.

    This function does not execute anything; it only selects work.
    """
    if grace_minutes < 0:
        raise ValueError(
            "grace_minutes cannot be negative."
        )

    now = normalize_utc(now_utc)
    completed = completed_prompt_ids or set()

    for item in schedule.items:
        if item.benchmark.prompt_id in completed:
            continue

        scheduled = normalize_utc(
            item.scheduled_at_utc
        )

        if now < scheduled:
            continue

        overdue = now - scheduled

        if overdue > timedelta(
            minutes=grace_minutes
        ):
            continue

        return DueProbe(
            item=item,
            overdue_by=overdue,
        )

    return None


def find_next_probe(
    schedule: ConsumerDailySchedule,
    *,
    now_utc: datetime,
    completed_prompt_ids: set[str] | None = None,
) -> ScheduledBenchmark | None:
    """
    Return the next incomplete benchmark scheduled after now.
    """
    now = normalize_utc(now_utc)
    completed = completed_prompt_ids or set()

    for item in schedule.items:
        if item.benchmark.prompt_id in completed:
            continue

        scheduled = normalize_utc(
            item.scheduled_at_utc
        )

        if scheduled > now:
            return item

    return None
