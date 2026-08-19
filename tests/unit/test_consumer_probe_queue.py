from datetime import date

import pytest

from consumer_probe.queue import (
    build_daily_queue,
    order_prompts,
)
from consumer_probe.sampling import SamplingPolicy

PROMPTS = [
    "reasoning-001",
    "coding-001",
    "mathematics-001",
    "instruction-following-001",
    "knowledge-001",
    "writing-001",
    "technical-001",
]


def test_queue_is_reproducible():
    sampling_date = date(2026, 8, 19)

    first = build_daily_queue(
        sampling_date,
        observer_id="observer-a",
        prompt_ids=PROMPTS,
    )

    second = build_daily_queue(
        sampling_date,
        observer_id="observer-a",
        prompt_ids=PROMPTS,
    )

    assert first == second


def test_queue_has_no_duplicate_prompts():
    queue = build_daily_queue(
        date(2026, 8, 19),
        observer_id="observer-a",
        prompt_ids=PROMPTS,
    )

    prompt_ids = [
        item.prompt_id
        for item in queue
    ]

    assert len(prompt_ids) == len(set(prompt_ids))


def test_queue_has_at_most_one_prompt_per_slot():
    queue = build_daily_queue(
        date(2026, 8, 19),
        observer_id="observer-a",
        prompt_ids=PROMPTS,
    )

    timestamps = [
        item.scheduled_at_utc
        for item in queue
    ]

    assert len(timestamps) == len(set(timestamps))


def test_excess_prompts_are_deferred():
    queue = build_daily_queue(
        date(2026, 8, 19),
        observer_id="observer-a",
        prompt_ids=PROMPTS,
    )

    # Default sampling policy provides six daily slots.
    assert len(queue) == 6


def test_extra_sampling_slots_allow_more_prompts():
    policy = SamplingPolicy(
        bucket_hours=4,
        samples_per_bucket=2,
    )

    queue = build_daily_queue(
        date(2026, 8, 19),
        observer_id="observer-a",
        prompt_ids=PROMPTS,
        sampling_policy=policy,
    )

    assert len(queue) == len(PROMPTS)


def test_fewer_prompts_than_slots_are_not_repeated():
    queue = build_daily_queue(
        date(2026, 8, 19),
        observer_id="observer-a",
        prompt_ids=[
            "reasoning-001",
            "coding-001",
        ],
    )

    assert len(queue) == 2

    assert {
        item.prompt_id
        for item in queue
    } == {
        "reasoning-001",
        "coding-001",
    }


def test_different_observers_can_receive_different_order():
    sampling_date = date(2026, 8, 19)

    first = order_prompts(
        PROMPTS,
        observer_id="observer-a",
        sampling_date=sampling_date,
    )

    second = order_prompts(
        PROMPTS,
        observer_id="observer-b",
        sampling_date=sampling_date,
    )

    assert first != second


def test_different_dates_can_receive_different_order():
    first = order_prompts(
        PROMPTS,
        observer_id="observer-a",
        sampling_date=date(2026, 8, 19),
    )

    second = order_prompts(
        PROMPTS,
        observer_id="observer-a",
        sampling_date=date(2026, 8, 20),
    )

    assert first != second


def test_duplicate_prompt_ids_are_rejected():
    with pytest.raises(
        ValueError,
        match="duplicates",
    ):
        build_daily_queue(
            date(2026, 8, 19),
            observer_id="observer-a",
            prompt_ids=[
                "reasoning-001",
                "reasoning-001",
            ],
        )


def test_empty_prompt_list_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        build_daily_queue(
            date(2026, 8, 19),
            observer_id="observer-a",
            prompt_ids=[],
        )


def test_blank_prompt_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="empty values",
    ):
        build_daily_queue(
            date(2026, 8, 19),
            observer_id="observer-a",
            prompt_ids=[
                "reasoning-001",
                "   ",
            ],
        )


def test_blank_observer_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="observer_id cannot be empty",
    ):
        build_daily_queue(
            date(2026, 8, 19),
            observer_id="   ",
            prompt_ids=PROMPTS,
        )


def test_seven_prompts_six_slots_rotate_fairly():
    start = date(2026, 8, 19)

    scheduled_counts = {
        prompt_id: 0
        for prompt_id in PROMPTS
    }

    omitted_counts = {
        prompt_id: 0
        for prompt_id in PROMPTS
    }

    from datetime import timedelta

    for day_offset in range(7):
        queue = build_daily_queue(
            start + timedelta(days=day_offset),
            observer_id="observer-a",
            prompt_ids=PROMPTS,
        )

        scheduled = {
            item.prompt_id
            for item in queue
        }

        omitted = set(PROMPTS) - scheduled

        assert len(scheduled) == 6
        assert len(omitted) == 1

        for prompt_id in scheduled:
            scheduled_counts[prompt_id] += 1

        for prompt_id in omitted:
            omitted_counts[prompt_id] += 1

    assert set(
        scheduled_counts.values()
    ) == {6}

    assert set(
        omitted_counts.values()
    ) == {1}


def test_rotation_is_fair_with_fewer_slots():
    start = date(2026, 8, 19)

    policy = SamplingPolicy(
        bucket_hours=8,
        samples_per_bucket=1,
    )

    counts = {
        prompt_id: 0
        for prompt_id in PROMPTS
    }

    from datetime import timedelta

    for day_offset in range(7):
        queue = build_daily_queue(
            start + timedelta(days=day_offset),
            observer_id="observer-a",
            prompt_ids=PROMPTS,
            sampling_policy=policy,
        )

        assert len(queue) == 3

        for item in queue:
            counts[item.prompt_id] += 1

    assert set(counts.values()) == {3}
