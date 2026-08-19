from datetime import datetime, timezone

from consumer_probe.aggregation import (
    aggregate_by_region_and_utc,
)
from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
)


def make_record(
    *,
    hour=21,
    region="CL-Los-Lagos",
    platform=ConsumerPlatform.CHATGPT,
    prompt_id="reasoning-001",
    ttfo=1000,
    latency=3000,
):
    timestamp = datetime(
        2026,
        8,
        19,
        hour,
        0,
        tzinfo=timezone.utc,
    )

    return ConsumerProbeRecord(
        observer_id="observer-test",
        region_code=region,
        platform=platform,
        page_hostname="chatgpt.com",
        benchmark_version="0.1",
        prompt_id=prompt_id,
        started_at_utc=timestamp,
        first_output_at_utc=timestamp,
        completed_at_utc=timestamp,
        time_to_first_output_ms=ttfo,
        total_latency_ms=latency,
    )


def test_same_group_is_aggregated():
    records = [
        make_record(
            ttfo=1000,
            latency=2000,
        ),
        make_record(
            ttfo=2000,
            latency=4000,
        ),
    ]

    groups = aggregate_by_region_and_utc(records)

    assert len(groups) == 1

    group = groups[0]

    assert group.key.platform == "chatgpt"
    assert group.key.region_code == "CL-Los-Lagos"
    assert group.key.prompt_id == "reasoning-001"
    assert group.bucket_label == "20:00–24:00 UTC"

    assert group.analytics.sample_count == 2
    assert group.analytics.median_ttfo_ms == 1500
    assert group.analytics.median_latency_ms == 3000


def test_different_regions_create_separate_groups():
    records = [
        make_record(region="CL-Los-Lagos"),
        make_record(region="IT-Lombardia"),
    ]

    groups = aggregate_by_region_and_utc(records)

    assert len(groups) == 2

    regions = {
        group.key.region_code
        for group in groups
    }

    assert regions == {
        "CL-Los-Lagos",
        "IT-Lombardia",
    }


def test_different_platforms_create_separate_groups():
    records = [
        make_record(
            platform=ConsumerPlatform.CHATGPT,
        ),
        make_record(
            platform=ConsumerPlatform.CLAUDE,
        ),
    ]

    groups = aggregate_by_region_and_utc(records)

    assert len(groups) == 2

    platforms = {
        group.key.platform
        for group in groups
    }

    assert platforms == {
        "chatgpt",
        "claude",
    }


def test_different_prompts_create_separate_groups():
    records = [
        make_record(
            prompt_id="reasoning-001",
        ),
        make_record(
            prompt_id="coding-001",
        ),
    ]

    groups = aggregate_by_region_and_utc(records)

    assert len(groups) == 2


def test_different_time_buckets_create_separate_groups():
    records = [
        make_record(hour=3),
        make_record(hour=21),
    ]

    groups = aggregate_by_region_and_utc(records)

    assert len(groups) == 2

    labels = {
        group.bucket_label
        for group in groups
    }

    assert labels == {
        "00:00–04:00 UTC",
        "20:00–24:00 UTC",
    }


def test_empty_dataset_returns_empty_groups():
    assert aggregate_by_region_and_utc([]) == []
