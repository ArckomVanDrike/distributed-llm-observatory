from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from consumer_probe.aggregation import AggregatedProbeGroup


class AnomalyLevel(str, Enum):
    INSUFFICIENT_DATA = "insufficient_data"
    NORMAL = "normal"
    WATCH = "watch"
    DEGRADED = "degraded"


@dataclass(frozen=True)
class ComparisonPolicy:
    """
    Operational thresholds for anomaly screening.

    These thresholds are policy parameters, not claims of statistical
    significance. Statistical hypothesis testing can be added later
    when sample sizes and sampling design justify it.
    """

    min_samples_per_group: int = 20

    watch_latency_ratio: float = 1.25
    degraded_latency_ratio: float = 1.50

    watch_failure_delta: float = 0.02
    degraded_failure_delta: float = 0.05


@dataclass(frozen=True)
class GroupComparison:
    level: AnomalyLevel

    candidate_samples: int
    baseline_samples: int

    ttfo_ratio: float | None
    first_output_measurement_mode: str | None
    latency_ratio: float | None

    failure_rate_delta: float
    retry_rate_delta: float

    reason: str


def metric_ratio(
    candidate: float | None,
    baseline: float | None,
) -> float | None:
    if candidate is None or baseline is None:
        return None

    if baseline <= 0:
        return None

    return candidate / baseline


def comparable_first_output_ratio(
    candidate: AggregatedProbeGroup,
    baseline: AggregatedProbeGroup,
    *,
    min_samples_per_group: int,
) -> tuple[str | None, float | None]:
    """
    Compare first-output measurements only when provenance is explicit
    and compatible.

    Legacy measurements with unknown provenance are excluded. When
    multiple explicit modes are shared, no arbitrary mode is selected.
    """
    candidate_modes = {
        mode: summary
        for mode, summary
        in candidate.first_output_by_mode.items()
        if mode is not None
    }

    baseline_modes = {
        mode: summary
        for mode, summary
        in baseline.first_output_by_mode.items()
        if mode is not None
    }

    shared_modes = (
        set(candidate_modes)
        & set(baseline_modes)
    )

    if len(shared_modes) != 1:
        return None, None

    measurement_mode = next(iter(shared_modes))

    candidate_summary = candidate_modes[
        measurement_mode
    ]
    baseline_summary = baseline_modes[
        measurement_mode
    ]

    if (
        candidate_summary.sample_count
        < min_samples_per_group
        or baseline_summary.sample_count
        < min_samples_per_group
    ):
        return measurement_mode, None

    return (
        measurement_mode,
        metric_ratio(
            candidate_summary.median_first_output_ms,
            baseline_summary.median_first_output_ms,
        ),
    )


def validate_comparable_groups(
    candidate: AggregatedProbeGroup,
    baseline: AggregatedProbeGroup,
) -> None:
    candidate_key = candidate.key
    baseline_key = baseline.key

    if candidate_key.platform != baseline_key.platform:
        raise ValueError(
            "Cannot compare groups from different platforms."
        )

    if (
        candidate_key.benchmark_version
        != baseline_key.benchmark_version
    ):
        raise ValueError(
            "Cannot compare different benchmark versions."
        )

    if candidate_key.prompt_id != baseline_key.prompt_id:
        raise ValueError(
            "Cannot compare different benchmark prompts."
        )


def compare_groups(
    candidate: AggregatedProbeGroup,
    baseline: AggregatedProbeGroup,
    *,
    policy: ComparisonPolicy | None = None,
) -> GroupComparison:
    """
    Compare a candidate group against a baseline.

    Region and UTC bucket may differ intentionally. Platform,
    benchmark version, and prompt must remain comparable.

    The result is an operational anomaly classification, not a
    statistical significance test.
    """
    validate_comparable_groups(
        candidate,
        baseline,
    )

    policy = policy or ComparisonPolicy()

    candidate_stats = candidate.analytics
    baseline_stats = baseline.analytics

    candidate_samples = candidate_stats.sample_count
    baseline_samples = baseline_stats.sample_count

    (
        first_output_measurement_mode,
        ttfo_ratio,
    ) = comparable_first_output_ratio(
        candidate,
        baseline,
        min_samples_per_group=(
            policy.min_samples_per_group
        ),
    )

    latency_ratio = metric_ratio(
        candidate_stats.median_latency_ms,
        baseline_stats.median_latency_ms,
    )

    failure_delta = (
        candidate_stats.failure_rate
        - baseline_stats.failure_rate
    )

    retry_delta = (
        candidate_stats.retry_rate
        - baseline_stats.retry_rate
    )

    if (
        candidate_samples
        < policy.min_samples_per_group
        or baseline_samples
        < policy.min_samples_per_group
    ):
        return GroupComparison(
            level=AnomalyLevel.INSUFFICIENT_DATA,
            candidate_samples=candidate_samples,
            baseline_samples=baseline_samples,
            ttfo_ratio=ttfo_ratio,
            first_output_measurement_mode=(
                first_output_measurement_mode
            ),
            latency_ratio=latency_ratio,
            failure_rate_delta=failure_delta,
            retry_rate_delta=retry_delta,
            reason=(
                "Minimum sample requirement not met: "
                f"{policy.min_samples_per_group} samples "
                "per group required."
            ),
        )

    degraded_latency = any(
        ratio is not None
        and ratio >= policy.degraded_latency_ratio
        for ratio in (
            ttfo_ratio,
            latency_ratio,
        )
    )

    degraded_failure = (
        failure_delta
        >= policy.degraded_failure_delta
    )

    if degraded_latency or degraded_failure:
        return GroupComparison(
            level=AnomalyLevel.DEGRADED,
            candidate_samples=candidate_samples,
            baseline_samples=baseline_samples,
            ttfo_ratio=ttfo_ratio,
            first_output_measurement_mode=(
                first_output_measurement_mode
            ),
            latency_ratio=latency_ratio,
            failure_rate_delta=failure_delta,
            retry_rate_delta=retry_delta,
            reason=(
                "Candidate crossed a configured "
                "degradation threshold."
            ),
        )

    watch_latency = any(
        ratio is not None
        and ratio >= policy.watch_latency_ratio
        for ratio in (
            ttfo_ratio,
            latency_ratio,
        )
    )

    watch_failure = (
        failure_delta
        >= policy.watch_failure_delta
    )

    if watch_latency or watch_failure:
        return GroupComparison(
            level=AnomalyLevel.WATCH,
            candidate_samples=candidate_samples,
            baseline_samples=baseline_samples,
            ttfo_ratio=ttfo_ratio,
            first_output_measurement_mode=(
                first_output_measurement_mode
            ),
            latency_ratio=latency_ratio,
            failure_rate_delta=failure_delta,
            retry_rate_delta=retry_delta,
            reason=(
                "Candidate crossed a configured "
                "watch threshold."
            ),
        )

    return GroupComparison(
        level=AnomalyLevel.NORMAL,
        candidate_samples=candidate_samples,
        baseline_samples=baseline_samples,
        ttfo_ratio=ttfo_ratio,
        first_output_measurement_mode=(
            first_output_measurement_mode
        ),
        latency_ratio=latency_ratio,
        failure_rate_delta=failure_delta,
        retry_rate_delta=retry_delta,
        reason=(
            "Candidate remained below configured "
            "anomaly thresholds."
        ),
    )
