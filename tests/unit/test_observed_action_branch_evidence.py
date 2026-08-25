from observer.core.action_gateway import (
    ObservedActionCall,
    ObservedActionOutcome,
)
from observer.core.observed_action_branch_evidence import (
    ObservedActionBranchEvidenceCollector,
)
from schemas.benchmark import (
    BenchmarkExpectedActionCall,
    BenchmarkExpectedBranch,
    BenchmarkToolResult,
)


def check_call():
    return ObservedActionCall(
        tool_name="check_item",
        arguments={
            "name": "delta",
        },
    )


def create_call():
    return ObservedActionCall(
        tool_name="create_item",
        arguments={
            "name": "delta",
            "count": 4,
        },
    )


def inspect_call():
    return ObservedActionCall(
        tool_name="inspect_item",
        arguments={
            "name": "delta",
        },
    )


def missing_outcome():
    return ObservedActionOutcome(
        tool_name="check_item",
        status_code=200,
        succeeded=True,
        result={
            "state": "missing",
        },
    )


def make_collector(
    *,
    calls,
    outcomes,
):
    return ObservedActionBranchEvidenceCollector(
        expected_actions=(
            BenchmarkExpectedActionCall(
                tool_name="check_item",
                arguments={
                    "name": "delta",
                },
            ),
            BenchmarkExpectedActionCall(
                tool_name="create_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
        ),
        tool_results=(
            BenchmarkToolResult(
                tool_name="check_item",
                result={
                    "state": "missing",
                },
            ),
        ),
        expected_branch=BenchmarkExpectedBranch(
            source_action_index=0,
            source_result_field="state",
            expected_value="missing",
            branch_action_index=1,
        ),
        calls_provider=lambda: tuple(calls),
        outcomes_provider=lambda: tuple(outcomes),
    )


def criterion_results(collector):
    return {
        criterion.criterion_id: criterion.passed
        for criterion in collector.collect()
    }


def test_branch_evidence_passes_for_runtime_selected_branch():
    collector = make_collector(
        calls=[
            check_call(),
            create_call(),
        ],
        outcomes=[
            missing_outcome(),
            ObservedActionOutcome(
                tool_name="create_item",
                status_code=200,
                succeeded=True,
            ),
        ],
    )

    assert criterion_results(collector) == {
        "tool-calls-observed": True,
        "tool-sequence-length-match": True,
        "tool-sequence-order-match": True,
        "tool-sequence-arguments-match": True,
        "branch-source-result-observed": True,
        "branch-selected": True,
    }


def test_branch_evidence_rejects_wrong_runtime_value():
    collector = make_collector(
        calls=[
            check_call(),
            create_call(),
        ],
        outcomes=[
            ObservedActionOutcome(
                tool_name="check_item",
                status_code=200,
                succeeded=True,
                result={
                    "state": "present",
                },
            ),
            ObservedActionOutcome(
                tool_name="create_item",
                status_code=200,
                succeeded=True,
            ),
        ],
    )

    results = criterion_results(collector)

    assert results["tool-sequence-order-match"] is True
    assert (
        results["branch-source-result-observed"]
        is False
    )
    assert results["branch-selected"] is False


def test_branch_evidence_rejects_wrong_branch_action():
    collector = make_collector(
        calls=[
            check_call(),
            inspect_call(),
        ],
        outcomes=[
            missing_outcome(),
            ObservedActionOutcome(
                tool_name="inspect_item",
                status_code=200,
                succeeded=True,
            ),
        ],
    )

    results = criterion_results(collector)

    assert (
        results["branch-source-result-observed"]
        is True
    )
    assert results["tool-sequence-order-match"] is False
    assert results["branch-selected"] is False


def test_branch_evidence_rejects_missing_branch_action():
    collector = make_collector(
        calls=[
            check_call(),
        ],
        outcomes=[
            missing_outcome(),
        ],
    )

    results = criterion_results(collector)

    assert (
        results["branch-source-result-observed"]
        is True
    )
    assert (
        results["tool-sequence-length-match"]
        is False
    )
    assert results["branch-selected"] is False


def test_branch_evidence_requires_successful_source_outcome():
    collector = make_collector(
        calls=[
            check_call(),
            create_call(),
        ],
        outcomes=[
            ObservedActionOutcome(
                tool_name="check_item",
                status_code=503,
                succeeded=False,
                error={
                    "code": "unavailable",
                },
            ),
            ObservedActionOutcome(
                tool_name="create_item",
                status_code=200,
                succeeded=True,
            ),
        ],
    )

    results = criterion_results(collector)

    assert (
        results["branch-source-result-observed"]
        is False
    )
    assert results["branch-selected"] is False


def test_branch_selection_does_not_require_branch_success():
    collector = make_collector(
        calls=[
            check_call(),
            create_call(),
        ],
        outcomes=[
            missing_outcome(),
            ObservedActionOutcome(
                tool_name="create_item",
                status_code=500,
                succeeded=False,
                error={
                    "code": "write_failed",
                },
            ),
        ],
    )

    results = criterion_results(collector)

    assert (
        results["branch-source-result-observed"]
        is True
    )
    assert results["tool-sequence-order-match"] is True
    assert results["branch-selected"] is True
