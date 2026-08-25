from observer.core.action_gateway import (
    ObservedActionCall,
    ObservedActionOutcome,
)
from observer.core.observed_action_recovery_evidence import (
    ObservedActionRecoveryEvidenceCollector,
)
from schemas.benchmark import (
    BenchmarkExpectedActionCall,
    BenchmarkExpectedRecovery,
    BenchmarkToolFailure,
)


def make_collector(
    *,
    calls,
    outcomes,
    expected_actions=None,
):
    if expected_actions is None:
        expected_actions = (
            BenchmarkExpectedActionCall(
                tool_name="persist_primary",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
            BenchmarkExpectedActionCall(
                tool_name="persist_fallback",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
        )

    return ObservedActionRecoveryEvidenceCollector(
        expected_actions=expected_actions,
        tool_failures=(
            BenchmarkToolFailure(
                tool_name="persist_primary",
                status_code=503,
                error={
                    "code": "temporary_unavailable",
                },
            ),
        ),
        expected_recovery=BenchmarkExpectedRecovery(
            failed_action_index=0,
            recovery_action_index=1,
        ),
        calls_provider=lambda: tuple(calls),
        outcomes_provider=lambda: tuple(outcomes),
    )


def criterion_results(collector):
    return {
        criterion.criterion_id: criterion.passed
        for criterion in collector.collect()
    }


def primary_call():
    return ObservedActionCall(
        tool_name="persist_primary",
        arguments={
            "name": "delta",
            "count": 4,
        },
    )


def fallback_call():
    return ObservedActionCall(
        tool_name="persist_fallback",
        arguments={
            "name": "delta",
            "count": 4,
        },
    )


def failed_primary_outcome():
    return ObservedActionOutcome(
        tool_name="persist_primary",
        status_code=503,
        succeeded=False,
        error={
            "code": "temporary_unavailable",
        },
    )


def successful_fallback_outcome():
    return ObservedActionOutcome(
        tool_name="persist_fallback",
        status_code=200,
        succeeded=True,
    )


def test_recovery_evidence_passes_for_observed_failure_then_success():
    collector = make_collector(
        calls=[
            primary_call(),
            fallback_call(),
        ],
        outcomes=[
            failed_primary_outcome(),
            successful_fallback_outcome(),
        ],
    )

    assert criterion_results(collector) == {
        "tool-calls-observed": True,
        "tool-sequence-length-match": True,
        "tool-sequence-order-match": True,
        "tool-sequence-arguments-match": True,
        "tool-failure-observed": True,
        "recovery-after-failure": True,
    }


def test_recovery_evidence_rejects_wrong_failure_status():
    collector = make_collector(
        calls=[
            primary_call(),
            fallback_call(),
        ],
        outcomes=[
            ObservedActionOutcome(
                tool_name="persist_primary",
                status_code=500,
                succeeded=False,
                error={
                    "code": "temporary_unavailable",
                },
            ),
            successful_fallback_outcome(),
        ],
    )

    results = criterion_results(collector)

    assert results["tool-sequence-order-match"] is True
    assert results["tool-failure-observed"] is False
    assert results["recovery-after-failure"] is False


def test_recovery_evidence_rejects_wrong_failure_error():
    collector = make_collector(
        calls=[
            primary_call(),
            fallback_call(),
        ],
        outcomes=[
            ObservedActionOutcome(
                tool_name="persist_primary",
                status_code=503,
                succeeded=False,
                error={
                    "code": "different_error",
                },
            ),
            successful_fallback_outcome(),
        ],
    )

    results = criterion_results(collector)

    assert results["tool-failure-observed"] is False
    assert results["recovery-after-failure"] is False


def test_recovery_evidence_requires_successful_recovery_outcome():
    collector = make_collector(
        calls=[
            primary_call(),
            fallback_call(),
        ],
        outcomes=[
            failed_primary_outcome(),
            ObservedActionOutcome(
                tool_name="persist_fallback",
                status_code=503,
                succeeded=False,
                error={
                    "code": "fallback_failed",
                },
            ),
        ],
    )

    results = criterion_results(collector)

    assert results["tool-failure-observed"] is True
    assert results["recovery-after-failure"] is False


def test_recovery_evidence_detects_missing_recovery_call():
    collector = make_collector(
        calls=[
            primary_call(),
        ],
        outcomes=[
            failed_primary_outcome(),
        ],
    )

    results = criterion_results(collector)

    assert results["tool-sequence-length-match"] is False
    assert results["tool-failure-observed"] is True
    assert results["recovery-after-failure"] is False


def test_recovery_evidence_rejects_reversed_actions():
    collector = make_collector(
        calls=[
            fallback_call(),
            primary_call(),
        ],
        outcomes=[
            successful_fallback_outcome(),
            failed_primary_outcome(),
        ],
    )

    results = criterion_results(collector)

    assert results["tool-sequence-order-match"] is False
    assert results["tool-failure-observed"] is False
    assert results["recovery-after-failure"] is False


def test_recovery_evidence_supports_retrying_same_tool():
    expected_actions = (
        BenchmarkExpectedActionCall(
            tool_name="persist_primary",
            arguments={
                "name": "delta",
                "count": 4,
            },
        ),
        BenchmarkExpectedActionCall(
            tool_name="persist_primary",
            arguments={
                "name": "delta",
                "count": 4,
            },
        ),
    )

    collector = make_collector(
        expected_actions=expected_actions,
        calls=[
            primary_call(),
            primary_call(),
        ],
        outcomes=[
            failed_primary_outcome(),
            ObservedActionOutcome(
                tool_name="persist_primary",
                status_code=200,
                succeeded=True,
            ),
        ],
    )

    results = criterion_results(collector)

    assert results["tool-sequence-order-match"] is True
    assert results["tool-failure-observed"] is True
    assert results["recovery-after-failure"] is True
