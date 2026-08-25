from observer.core.action_gateway import ObservedActionCall
from observer.core.observed_action_evidence import (
    ObservedActionEvidenceCollector,
)
from schemas.benchmark import BenchmarkExpectedAction


def collect(
    calls: tuple[ObservedActionCall, ...],
    *,
    arguments=None,
    call_count: int = 1,
):
    collector = ObservedActionEvidenceCollector(
        expected_action=BenchmarkExpectedAction(
            tool_name="record_item",
            arguments=(
                arguments
                if arguments is not None
                else {
                    "name": "delta",
                    "count": 4,
                    "active": True,
                }
            ),
            call_count=call_count,
        ),
        calls_provider=lambda: calls,
    )

    return collector.collect()


def passed_by_id(evidence):
    return {
        item.criterion_id: item.passed
        for item in evidence
    }


def test_observed_action_evidence_accepts_expected_call():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                    "active": True,
                },
            ),
        )
    )

    assert [
        item.criterion_id
        for item in evidence
    ] == [
        "tool-called",
        "tool-name-match",
        "tool-arguments-match",
        "tool-call-count-match",
    ]

    assert all(
        item.passed
        for item in evidence
    )


def test_observed_action_evidence_rejects_no_calls():
    evidence = collect(())

    assert passed_by_id(evidence) == {
        "tool-called": False,
        "tool-name-match": False,
        "tool-arguments-match": False,
        "tool-call-count-match": False,
    }


def test_observed_action_evidence_detects_wrong_tool():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="other_tool",
                arguments={
                    "name": "delta",
                    "count": 4,
                    "active": True,
                },
            ),
        )
    )

    assert passed_by_id(evidence) == {
        "tool-called": True,
        "tool-name-match": False,
        "tool-arguments-match": True,
        "tool-call-count-match": True,
    }


def test_observed_action_evidence_detects_wrong_arguments():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "name": "alpha",
                    "count": 4,
                    "active": True,
                },
            ),
        )
    )

    assert passed_by_id(evidence) == {
        "tool-called": True,
        "tool-name-match": True,
        "tool-arguments-match": False,
        "tool-call-count-match": True,
    }


def test_observed_action_evidence_detects_wrong_call_count():
    call = ObservedActionCall(
        tool_name="record_item",
        arguments={
            "name": "delta",
            "count": 4,
            "active": True,
        },
    )

    evidence = collect(
        (
            call,
            call,
        )
    )

    assert passed_by_id(evidence) == {
        "tool-called": True,
        "tool-name-match": True,
        "tool-arguments-match": True,
        "tool-call-count-match": False,
    }


def test_observed_action_evidence_distinguishes_boolean_from_number():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "value": 1,
                },
            ),
        ),
        arguments={
            "value": True,
        },
    )

    assert passed_by_id(evidence)[
        "tool-arguments-match"
    ] is False


def test_observed_action_evidence_treats_json_numbers_as_equivalent():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "value": 4.0,
                },
            ),
        ),
        arguments={
            "value": 4,
        },
    )

    assert passed_by_id(evidence)[
        "tool-arguments-match"
    ] is True
