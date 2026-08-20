import pytest

from consumer_probe.aggregation import (
    AggregatedProbeGroup,
    AggregationKey,
)
from consumer_probe.analytics import (
    FirstOutputMeasurementSummary,
    ProbeAnalyticsSummary,
)
from consumer_probe.comparison import (
    AnomalyLevel,
    ComparisonPolicy,
    compare_groups,
)


def make_summary(
    *,
    samples=20,
    ttfo=1000,
    latency=2000,
    failure_rate=0.0,
    retry_rate=0.0,
):
    return ProbeAnalyticsSummary(
        sample_count=samples,
        successful_samples=samples,
        mean_ttfo_ms=ttfo,
        median_ttfo_ms=ttfo,
        p95_ttfo_ms=ttfo,
        mean_latency_ms=latency,
        median_latency_ms=latency,
        p95_latency_ms=latency,
        min_latency_ms=latency,
        max_latency_ms=latency,
        latency_stdev_ms=0.0,
        failure_rate=failure_rate,
        retry_rate=retry_rate,
        interruption_rate=0.0,
    )


def make_group(
    *,
    region="CL-Los-Lagos",
    platform="chatgpt",
    prompt_id="reasoning-001",
    benchmark_version="0.1",
    bucket=20,
    samples=20,
    ttfo=1000,
    latency=2000,
    failure_rate=0.0,
    retry_rate=0.0,
    first_output_mode=None,
    first_output_samples=None,
):
    return AggregatedProbeGroup(
        key=AggregationKey(
            platform=platform,
            region_code=region,
            benchmark_version=benchmark_version,
            prompt_id=prompt_id,
            bucket_start_utc=bucket,
        ),
        bucket_label=f"{bucket:02d}:00 UTC",
        analytics=make_summary(
            samples=samples,
            ttfo=ttfo,
            latency=latency,
            failure_rate=failure_rate,
            retry_rate=retry_rate,
        ),
        first_output_by_mode=(
            {
                first_output_mode:
                    FirstOutputMeasurementSummary(
                        measurement_mode=first_output_mode,
                        sample_count=(
                            first_output_samples
                            if first_output_samples
                            is not None
                            else samples
                        ),
                        mean_first_output_ms=ttfo,
                        median_first_output_ms=ttfo,
                        p95_first_output_ms=ttfo,
                    )
            }
            if (
                first_output_mode is not None
                or first_output_samples is not None
            )
            else {}
        ),
    )


def test_insufficient_data_prevents_anomaly_claim():
    baseline = make_group(
        samples=2,
        latency=2000,
    )

    candidate = make_group(
        samples=2,
        latency=6000,
    )

    result = compare_groups(
        candidate,
        baseline,
    )

    assert result.level == AnomalyLevel.INSUFFICIENT_DATA


def test_normal_candidate():
    baseline = make_group(
        latency=2000,
    )

    candidate = make_group(
        latency=2200,
    )

    result = compare_groups(
        candidate,
        baseline,
    )

    assert result.level == AnomalyLevel.NORMAL
    assert result.latency_ratio == pytest.approx(1.1)


def test_watch_candidate():
    baseline = make_group(
        latency=2000,
    )

    candidate = make_group(
        latency=2600,
    )

    result = compare_groups(
        candidate,
        baseline,
    )

    assert result.level == AnomalyLevel.WATCH
    assert result.latency_ratio == pytest.approx(1.3)


def test_degraded_candidate():
    baseline = make_group(
        latency=2000,
    )

    candidate = make_group(
        latency=3000,
    )

    result = compare_groups(
        candidate,
        baseline,
    )

    assert result.level == AnomalyLevel.DEGRADED
    assert result.latency_ratio == pytest.approx(1.5)


def test_failure_rate_can_trigger_degraded():
    baseline = make_group(
        failure_rate=0.0,
    )

    candidate = make_group(
        failure_rate=0.10,
    )

    result = compare_groups(
        candidate,
        baseline,
    )

    assert result.level == AnomalyLevel.DEGRADED
    assert result.failure_rate_delta == pytest.approx(0.10)


def test_custom_policy_is_supported():
    policy = ComparisonPolicy(
        min_samples_per_group=10,
        watch_latency_ratio=2.0,
        degraded_latency_ratio=3.0,
    )

    baseline = make_group(
        samples=10,
        latency=1000,
    )

    candidate = make_group(
        samples=10,
        latency=1500,
    )

    result = compare_groups(
        candidate,
        baseline,
        policy=policy,
    )

    assert result.level == AnomalyLevel.NORMAL


def test_different_platforms_are_rejected():
    baseline = make_group(
        platform="chatgpt",
    )

    candidate = make_group(
        platform="claude",
    )

    with pytest.raises(
        ValueError,
        match="different platforms",
    ):
        compare_groups(
            candidate,
            baseline,
        )


def test_different_prompts_are_rejected():
    baseline = make_group(
        prompt_id="reasoning-001",
    )

    candidate = make_group(
        prompt_id="coding-001",
    )

    with pytest.raises(
        ValueError,
        match="different benchmark prompts",
    ):
        compare_groups(
            candidate,
            baseline,
        )


def test_first_output_ratio_requires_matching_explicit_mode():
    mode = "human-observed-click-v0.1"

    baseline = make_group(
        ttfo=1000,
        latency=2000,
        first_output_mode=mode,
    )

    candidate = make_group(
        ttfo=2000,
        latency=2000,
        first_output_mode=mode,
    )

    result = compare_groups(
        candidate,
        baseline,
    )

    assert result.ttfo_ratio == pytest.approx(2.0)
    assert result.first_output_measurement_mode == mode

    # First-output alone can trigger degradation when the
    # provenance is compatible and sufficiently sampled.
    assert result.level == AnomalyLevel.DEGRADED


def test_first_output_ratio_rejects_different_modes():
    baseline = make_group(
        ttfo=1000,
        latency=2000,
        first_output_mode=(
            "human-observed-click-v0.1"
        ),
    )

    candidate = make_group(
        ttfo=3000,
        latency=2000,
        first_output_mode=(
            "future-api-first-token-v0.1"
        ),
    )

    result = compare_groups(
        candidate,
        baseline,
    )

    assert result.ttfo_ratio is None
    assert result.first_output_measurement_mode is None
    assert result.level == AnomalyLevel.NORMAL


def test_first_output_ratio_does_not_use_legacy_unknown_mode():
    baseline = make_group(
        ttfo=1000,
        latency=2000,
        first_output_mode=None,
        first_output_samples=20,
    )

    candidate = make_group(
        ttfo=5000,
        latency=2000,
        first_output_mode=None,
        first_output_samples=20,
    )

    result = compare_groups(
        candidate,
        baseline,
    )

    assert result.ttfo_ratio is None
    assert result.first_output_measurement_mode is None
    assert result.level == AnomalyLevel.NORMAL


def test_first_output_ratio_requires_enough_mode_specific_samples():
    mode = "human-observed-click-v0.1"

    baseline = make_group(
        samples=20,
        ttfo=1000,
        latency=2000,
        first_output_mode=mode,
        first_output_samples=5,
    )

    candidate = make_group(
        samples=20,
        ttfo=5000,
        latency=2000,
        first_output_mode=mode,
        first_output_samples=5,
    )

    result = compare_groups(
        candidate,
        baseline,
    )

    assert result.first_output_measurement_mode == mode
    assert result.ttfo_ratio is None

    # Total probe count is sufficient, but the compatible
    # first-output subset is not, so it cannot trigger anomaly.
    assert result.level == AnomalyLevel.NORMAL
