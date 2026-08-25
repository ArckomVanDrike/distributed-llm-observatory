from observer.core.action_gateway import (
    ObservedActionCall,
    ObservedActionOutcome,
)
from observer.core.observed_action_multi_branch_evidence import (
    ObservedActionMultiBranchEvidenceCollector,
)
from schemas.benchmark import (
    BenchmarkExpectedActionCall,
    BenchmarkExpectedBranches,
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


def source_outcome(state):
    return ObservedActionOutcome(
        tool_name="check_item",
        status_code=200,
        succeeded=True,
        result={
            "state": state,
        },
    )


def successful_outcome(tool_name):
    return ObservedActionOutcome(
        tool_name=tool_name,
        status_code=200,
        succeeded=True,
    )


def make_collector(
    *,
    calls,
    outcomes,
):
    return ObservedActionMultiBranchEvidenceCollector(
        expected_actions=(
            BenchmarkExpectedActionCall(
                tool_name="check_item",
                arguments={
                    "name": "delta",
                },
            ),
        ),
        expected_branches=BenchmarkExpectedBranches(
            source_action_index=0,
            source_result_field="state",
            options=[
                {
                    "expected_value": "missing",
                    "action": {
                        "tool_name": "create_item",
                        "arguments": {
                            "name": "delta",
                            "count": 4,
                        },
                    },
                },
                {
                    "expected_value": "present",
                    "action": {
                        "tool_name": "inspect_item",
                        "arguments": {
                            "name": "delta",
                        },
                    },
                },
            ],
        ),
        calls_provider=lambda: tuple(calls),
        outcomes_provider=lambda: tuple(outcomes),
    )


def criterion_results(collector):
    return {
        criterion.criterion_id: criterion.passed
        for criterion in collector.collect()
    }


def test_multi_branch_selects_missing_branch():
    collector = make_collector(
        calls=[
            check_call(),
            create_call(),
        ],
        outcomes=[
            source_outcome("missing"),
            successful_outcome("create_item"),
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


def test_multi_branch_selects_present_branch():
    collector = make_collector(
        calls=[
            check_call(),
            inspect_call(),
        ],
        outcomes=[
            source_outcome("present"),
            successful_outcome("inspect_item"),
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


def test_multi_branch_rejects_wrong_action_for_missing():
    collector = make_collector(
        calls=[
            check_call(),
            inspect_call(),
        ],
        outcomes=[
            source_outcome("missing"),
            successful_outcome("inspect_item"),
        ],
    )

    results = criterion_results(collector)

    assert (
        results["branch-source-result-observed"]
        is True
    )
    assert results["tool-sequence-order-match"] is False
    assert results["branch-selected"] is False


def test_multi_branch_rejects_wrong_action_for_present():
    collector = make_collector(
        calls=[
            check_call(),
            create_call(),
        ],
        outcomes=[
            source_outcome("present"),
            successful_outcome("create_item"),
        ],
    )

    results = criterion_results(collector)

    assert (
        results["branch-source-result-observed"]
        is True
    )
    assert results["tool-sequence-order-match"] is False
    assert results["branch-selected"] is False


def test_multi_branch_rejects_unconfigured_runtime_value():
    collector = make_collector(
        calls=[
            check_call(),
            create_call(),
        ],
        outcomes=[
            source_outcome("archived"),
            successful_outcome("create_item"),
        ],
    )

    results = criterion_results(collector)

    assert (
        results["branch-source-result-observed"]
        is False
    )
    assert results["branch-selected"] is False


def test_multi_branch_requires_successful_source_outcome():
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
            successful_outcome("create_item"),
        ],
    )

    results = criterion_results(collector)

    assert (
        results["branch-source-result-observed"]
        is False
    )
    assert results["branch-selected"] is False


def test_multi_branch_decision_is_independent_of_branch_success():
    collector = make_collector(
        calls=[
            check_call(),
            create_call(),
        ],
        outcomes=[
            source_outcome("missing"),
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
    assert results["tool-sequence-arguments-match"] is True
    assert results["branch-selected"] is True
