from observer.core.action_gateway import ObservedActionCall
from observer.core.observed_action_data_flow_evidence import (
    ObservedActionDataFlowEvidenceCollector,
)
from schemas.benchmark import (
    BenchmarkExpectedActionCall,
    BenchmarkExpectedPropagation,
    BenchmarkToolResult,
)


def expected_actions():
    return (
        BenchmarkExpectedActionCall(
            tool_name="create_item",
            arguments={
                "name": "delta",
                "count": 4,
            },
        ),
        BenchmarkExpectedActionCall(
            tool_name="inspect_item",
            arguments={},
        ),
    )


def tool_results():
    return (
        BenchmarkToolResult(
            tool_name="create_item",
            result={
                "item_id": "item-742",
            },
        ),
    )


def expected_propagations():
    return (
        BenchmarkExpectedPropagation(
            source_action_index=0,
            source_result_field="item_id",
            target_action_index=1,
            target_argument="item_id",
        ),
    )


def collect(
    calls: tuple[ObservedActionCall, ...],
):
    collector = ObservedActionDataFlowEvidenceCollector(
        expected_actions=expected_actions(),
        tool_results=tool_results(),
        expected_propagations=expected_propagations(),
        calls_provider=lambda: calls,
    )

    return collector.collect()


def passed_by_id(evidence):
    return {
        item.criterion_id: item.passed
        for item in evidence
    }


def test_data_flow_accepts_propagated_tool_result():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="create_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "item_id": "item-742",
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
        "tool-result-propagated",
    ]

    assert all(
        item.passed
        for item in evidence
    )


def test_data_flow_rejects_wrong_propagated_value():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="create_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "item_id": "wrong-item",
                },
            ),
        )
    )

    assert passed_by_id(evidence) == {
        "tool-calls-observed": True,
        "tool-sequence-length-match": True,
        "tool-sequence-order-match": True,
        "tool-sequence-arguments-match": False,
        "tool-result-propagated": False,
    }


def test_data_flow_rejects_missing_propagated_argument():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="create_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={},
            ),
        )
    )

    assert passed_by_id(evidence) == {
        "tool-calls-observed": True,
        "tool-sequence-length-match": True,
        "tool-sequence-order-match": True,
        "tool-sequence-arguments-match": False,
        "tool-result-propagated": False,
    }


def test_data_flow_rejects_reverse_order():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "item_id": "item-742",
                },
            ),
            ObservedActionCall(
                tool_name="create_item",
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
        "tool-result-propagated": False,
    }


def test_data_flow_rejects_extra_call():
    evidence = collect(
        (
            ObservedActionCall(
                tool_name="create_item",
                arguments={
                    "name": "delta",
                    "count": 4,
                },
            ),
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "item_id": "item-742",
                },
            ),
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "item_id": "item-742",
                },
            ),
        )
    )

    result = passed_by_id(evidence)

    assert result["tool-sequence-length-match"] is False
    assert result["tool-sequence-order-match"] is False
    assert result["tool-sequence-arguments-match"] is False


def test_data_flow_uses_json_scalar_semantics():
    collector = ObservedActionDataFlowEvidenceCollector(
        expected_actions=(
            BenchmarkExpectedActionCall(
                tool_name="create_item",
                arguments={},
            ),
            BenchmarkExpectedActionCall(
                tool_name="inspect_item",
                arguments={},
            ),
        ),
        tool_results=(
            BenchmarkToolResult(
                tool_name="create_item",
                result={
                    "value": 4,
                },
            ),
        ),
        expected_propagations=(
            BenchmarkExpectedPropagation(
                source_action_index=0,
                source_result_field="value",
                target_action_index=1,
                target_argument="value",
            ),
        ),
        calls_provider=lambda: (
            ObservedActionCall(
                tool_name="create_item",
                arguments={},
            ),
            ObservedActionCall(
                tool_name="inspect_item",
                arguments={
                    "value": 4.0,
                },
            ),
        ),
    )

    result = passed_by_id(
        collector.collect()
    )

    assert (
        result["tool-sequence-arguments-match"]
        is True
    )
    assert result["tool-result-propagated"] is True
