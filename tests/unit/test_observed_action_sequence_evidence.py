from observer.core.action_gateway import ObservedActionCall
from observer.core.observed_action_sequence_evidence import (
    ObservedActionSequenceEvidenceCollector,
)
from schemas.benchmark import BenchmarkExpectedActionCall


def expected_sequence():
    return (
        BenchmarkExpectedActionCall(
            tool_name="record_item",
            arguments={
                "name": "delta",
                "count": 4,
            },
        ),
        BenchmarkExpectedActionCall(
            tool_name="inspect_item",
            arguments={
                "name": "delta",
            },
        ),
    )


def collect(
    calls: tuple[ObservedActionCall, ...],
):
    collector = ObservedActionSequenceEvidenceCollector(
        expected_actions=expected_sequence(),
        calls_provider=lambda: calls,
    )

    return collector.collect()


def passed_by_id(evidence):
    return {
        item.criterion_id: item.passed
        for item in evidence
    }


def test_sequence_evidence_accepts_expected_order():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "name": "delta",
                },
            ),
        )
    )

    assert [
        item.criterion_id
        for item in evidence
    ] == [
        "tool-calls-observed",
        "tool-sequence-length-match",
        "tool-sequence-order-match",
        "tool-sequence-arguments-match",
    ]

    assert all(
        item.passed
        for item in evidence
    )


def test_sequence_evidence_rejects_reverse_order():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "name": "delta",
                },
            ),
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
        )
    )

    assert passed_by_id(evidence) == {
        "tool-calls-observed": True,
        "tool-sequence-length-match": True,
        "tool-sequence-order-match": False,
        "tool-sequence-arguments-match": False,
    }


def test_sequence_evidence_rejects_missing_call():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
        )
    )

    assert passed_by_id(evidence) == {
        "tool-calls-observed": True,
        "tool-sequence-length-match": False,
        "tool-sequence-order-match": False,
        "tool-sequence-arguments-match": False,
    }


def test_sequence_evidence_rejects_extra_call():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "name": "delta",
                },
            ),
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "name": "delta",
                },
            ),
        )
    )

    assert passed_by_id(evidence) == {
        "tool-calls-observed": True,
        "tool-sequence-length-match": False,
        "tool-sequence-order-match": False,
        "tool-sequence-arguments-match": False,
    }


def test_sequence_evidence_rejects_wrong_arguments():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "name": "delta",
                    "count": 5,
                },
            ),
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "name": "delta",
                },
            ),
        )
    )

    assert passed_by_id(evidence) == {
        "tool-calls-observed": True,
        "tool-sequence-length-match": True,
        "tool-sequence-order-match": True,
        "tool-sequence-arguments-match": False,
    }


def test_sequence_evidence_rejects_no_calls():
    evidence = collect(())

    assert passed_by_id(evidence) == {
        "tool-calls-observed": False,
        "tool-sequence-length-match": False,
        "tool-sequence-order-match": False,
        "tool-sequence-arguments-match": False,
    }


def test_sequence_evidence_uses_json_scalar_semantics():
    collector = ObservedActionSequenceEvidenceCollector(
        expected_actions=(
            BenchmarkExpectedActionCall(
                tool_name="record_item",
                arguments={
                    "value": 4,
                    "active": True,
                },
            ),
        ),
        calls_provider=lambda: (
            ObservedActionCall(
                tool_name="record_item",
                arguments={
                    "value": 4.0,
                    "active": 1,
                },
            ),
        ),
    )

    evidence = passed_by_id(
        collector.collect()
    )

    assert evidence["tool-sequence-order-match"] is True
    assert (
        evidence["tool-sequence-arguments-match"]
        is False
    )
