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


def prompt_order_key(
    *,
    observer_id: str,
    sampling_date: date,
    prompt_id: str,
) -> bytes:
    """
    Return a deterministic ordering key.

    The order changes between observers and dates while remaining
    perfectly reproducible for the same inputs.
    """
    payload = (
        f"{observer_id}|"
        f"{sampling_date.isoformat()}|"
        f"{prompt_id}"
    ).encode()

    return hashlib.sha256(payload).digest()


def order_prompts(
    prompt_ids: list[str],
    *,
    observer_id: str,
    sampling_date: date,
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
        key=lambda prompt_id: prompt_order_key(
            observer_id=observer_id,
            sampling_date=sampling_date,
            prompt_id=prompt_id,
        ),
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
    - different observers/dates receive different prompt ordering
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
