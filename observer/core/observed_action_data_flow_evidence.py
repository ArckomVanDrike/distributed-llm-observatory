from __future__ import annotations

from collections.abc import Callable

from observer.core.action_gateway import ObservedActionCall
from observer.core.json_value_comparison import (
    json_scalar_equal,
)
from observer.core.observed_action_sequence_evidence import (
    ObservedActionSequenceEvidenceCollector,
)
from observer.core.task_evidence import (
    TaskCriterionEvidence,
    TaskEvidenceCollector,
)
from schemas.benchmark import (
    BenchmarkExpectedActionCall,
    BenchmarkExpectedPropagation,
    BenchmarkToolResult,
)


class ObservedActionDataFlowEvidenceCollector(
    TaskEvidenceCollector
):
    """
    Evaluates an observed ordered action sequence whose later
    arguments depend on deterministic results returned by earlier
    tool calls.

    Static expected arguments and observer-side propagation rules
    are combined into effective expected arguments before applying
    the normal ordered-sequence checks.
    """

    def __init__(
        self,
        *,
        expected_actions: tuple[
            BenchmarkExpectedActionCall,
            ...,
        ],
        tool_results: tuple[
            BenchmarkToolResult,
            ...,
        ],
        expected_propagations: tuple[
            BenchmarkExpectedPropagation,
            ...,
        ],
        calls_provider: Callable[
            [],
            tuple[ObservedActionCall, ...],
        ],
    ) -> None:
        self.expected_actions = expected_actions
        self.tool_results = tool_results
        self.expected_propagations = (
            expected_propagations
        )
        self.calls_provider = calls_provider

    def _effective_expected_actions(
        self,
    ) -> tuple[BenchmarkExpectedActionCall, ...]:
        arguments = [
            dict(action.arguments)
            for action in self.expected_actions
        ]

        results_by_tool = {
            tool_result.tool_name: tool_result.result
            for tool_result in self.tool_results
        }

        for propagation in self.expected_propagations:
            source_action = self.expected_actions[
                propagation.source_action_index
            ]

            source_result = results_by_tool[
                source_action.tool_name
            ]

            value = source_result[
                propagation.source_result_field
            ]

            arguments[
                propagation.target_action_index
            ][propagation.target_argument] = value

        return tuple(
            BenchmarkExpectedActionCall(
                tool_name=action.tool_name,
                arguments=action_arguments,
            )
            for action, action_arguments in zip(
                self.expected_actions,
                arguments,
                strict=True,
            )
        )

    def collect(
        self,
    ) -> tuple[TaskCriterionEvidence, ...]:
        calls = self.calls_provider()

        sequence_evidence = (
            ObservedActionSequenceEvidenceCollector(
                expected_actions=(
                    self._effective_expected_actions()
                ),
                calls_provider=lambda: calls,
            ).collect()
        )

        order_match = next(
            evidence.passed
            for evidence in sequence_evidence
            if (
                evidence.criterion_id
                == "tool-sequence-order-match"
            )
        )

        results_by_tool = {
            tool_result.tool_name: tool_result.result
            for tool_result in self.tool_results
        }

        propagation_match = order_match

        if propagation_match:
            for propagation in self.expected_propagations:
                target_index = (
                    propagation.target_action_index
                )

                if target_index >= len(calls):
                    propagation_match = False
                    break

                target_call = calls[target_index]

                if (
                    propagation.target_argument
                    not in target_call.arguments
                ):
                    propagation_match = False
                    break

                source_action = self.expected_actions[
                    propagation.source_action_index
                ]

                expected_value = results_by_tool[
                    source_action.tool_name
                ][propagation.source_result_field]

                observed_value = target_call.arguments[
                    propagation.target_argument
                ]

                if not json_scalar_equal(
                    observed_value,
                    expected_value,
                ):
                    propagation_match = False
                    break

        propagation_evidence = TaskCriterionEvidence(
            criterion_id="tool-result-propagated",
            passed=propagation_match,
            evidence=(
                "Observed later tool arguments propagate "
                "the configured earlier tool results."
                if propagation_match
                else (
                    "Observed later tool arguments do not "
                    "propagate the configured earlier "
                    "tool results."
                )
            ),
        )

        return (
            *sequence_evidence,
            propagation_evidence,
        )
