from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime

from consumer_probe.sampling import (
    SamplingPolicy,
    build_daily_schedule,
)


@dataclass(frozen=True)
class ProbeQueueItem:
    scheduled_at_utc: datetime
    prompt_id: str


def validate_prompt_ids(
    prompt_ids: list[str],
) -> None:
    if not prompt_ids:
        raise ValueError(
            "prompt_ids cannot be empty."
        )

    normalized = [
        prompt_id.strip()
        for prompt_id in prompt_ids
    ]

    if any(
        not prompt_id
        for prompt_id in normalized
    ):
        raise ValueError(
            "prompt_ids cannot contain empty values."
        )

    if len(set(normalized)) != len(normalized):
        raise ValueError(
            "prompt_ids cannot contain duplicates."
        )


def prompt_base_order_key(
    *,
    observer_id: str,
    prompt_id: str,
) -> bytes:
    """
    Return a stable observer-specific prompt ordering key.

    The date is deliberately excluded. Daily variation is handled by
    deterministic rotation so prompt coverage remains fair over time.
    """
    payload = (
        f"{observer_id}|{prompt_id}"
    ).encode()

    return hashlib.sha256(payload).digest()


def stable_prompt_order(
    prompt_ids: list[str],
    *,
    observer_id: str,
) -> list[str]:
    validate_prompt_ids(prompt_ids)

    if not observer_id.strip():
        raise ValueError(
            "observer_id cannot be empty."
        )

    return sorted(
        (
            prompt_id.strip()
            for prompt_id in prompt_ids
        ),
        key=lambda prompt_id: prompt_base_order_key(
            observer_id=observer_id,
            prompt_id=prompt_id,
        ),
    )


def rotation_offset(
    sampling_date: date,
    prompt_count: int,
) -> int:
    if prompt_count <= 0:
        raise ValueError(
            "prompt_count must be greater than zero."
        )

    return sampling_date.toordinal() % prompt_count


def order_prompts(
    prompt_ids: list[str],
    *,
    observer_id: str,
    sampling_date: date,
) -> list[str]:
    """
    Return the fair deterministic prompt order for one day.

    A stable observer-specific base ordering is rotated by one position
    per calendar day. Over a complete cycle every prompt therefore
    receives equal access to the available daily slots.
    """
    base_order = stable_prompt_order(
        prompt_ids,
        observer_id=observer_id,
    )

    offset = rotation_offset(
        sampling_date,
        len(base_order),
    )

    return (
        base_order[offset:]
        + base_order[:offset]
    )


def build_daily_queue(
    sampling_date: date,
    *,
    observer_id: str,
    prompt_ids: list[str],
    sampling_policy: SamplingPolicy | None = None,
) -> list[ProbeQueueItem]:
    """
    Build one deterministic daily Consumer Probe run queue.

    Properties:

    - at most one benchmark is assigned to each sampling slot
    - no prompt is repeated during the same daily queue
    - queue order is deterministic
    - different observers receive different base ordering
    - daily rotation provides fair long-term prompt coverage
    - excess prompts are deferred rather than creating request bursts
    """
    schedule = build_daily_schedule(
        sampling_date,
        observer_id=observer_id,
        policy=sampling_policy,
    )

    prompts = order_prompts(
        prompt_ids,
        observer_id=observer_id,
        sampling_date=sampling_date,
    )

    queue_size = min(
        len(schedule),
        len(prompts),
    )

    return [
        ProbeQueueItem(
            scheduled_at_utc=schedule[index],
            prompt_id=prompts[index],
        )
        for index in range(queue_size)
    ]
