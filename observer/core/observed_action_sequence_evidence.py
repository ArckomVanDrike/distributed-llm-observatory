from __future__ import annotations

from collections.abc import Callable

from observer.core.action_gateway import ObservedActionCall
from observer.core.json_value_comparison import (
    json_flat_object_equal,
)
from observer.core.task_evidence import (
    TaskCriterionEvidence,
    TaskEvidenceCollector,
)
from schemas.benchmark import BenchmarkExpectedActionCall


class ObservedActionSequenceEvidenceCollector(
    TaskEvidenceCollector
):
    """
    Converts an Observatory-observed ordered tool-call sequence
    into deterministic criterion evidence.

    The observed sequence must match the expected sequence exactly
    in length, tool order, and positional arguments.
    """

    def __init__(
        self,
        *,
        expected_actions: tuple[
            BenchmarkExpectedActionCall,
            ...,
        ],
        calls_provider: Callable[
            [],
            tuple[ObservedActionCall, ...],
        ],
    ) -> None:
        self.expected_actions = expected_actions
        self.calls_provider = calls_provider

    def collect(
        self,
    ) -> tuple[TaskCriterionEvidence, ...]:
        calls = self.calls_provider()

        calls_observed = bool(calls)

        length_match = (
            len(calls)
            == len(self.expected_actions)
        )

        order_match = (
            length_match
            and all(
                observed.tool_name
                == expected.tool_name
                for observed, expected
                in zip(
                    calls,
                    self.expected_actions,
                    strict=True,
                )
            )
        )

        arguments_match = (
            length_match
            and all(
                json_flat_object_equal(
                    observed.arguments,
                    expected.arguments,
                )
                for observed, expected
                in zip(
                    calls,
                    self.expected_actions,
                    strict=True,
                )
            )
        )

        return (
            TaskCriterionEvidence(
                criterion_id="tool-calls-observed",
                passed=calls_observed,
                evidence=(
                    "Observed at least one tool call."
                    if calls_observed
                    else "Observed no tool calls."
                ),
            ),
            TaskCriterionEvidence(
                criterion_id=(
                    "tool-sequence-length-match"
                ),
                passed=length_match,
                evidence=(
                    "Observed tool-call sequence length "
                    "matches the expected sequence."
                    if length_match
                    else (
                        "Observed tool-call sequence length "
                        "does not match the expected sequence."
                    )
                ),
            ),
            TaskCriterionEvidence(
                criterion_id=(
                    "tool-sequence-order-match"
                ),
                passed=order_match,
                evidence=(
                    "Observed tool order matches "
                    "the expected sequence."
                    if order_match
                    else (
                        "Observed tool order does not match "
                        "the expected sequence."
                    )
                ),
            ),
            TaskCriterionEvidence(
                criterion_id=(
                    "tool-sequence-arguments-match"
                ),
                passed=arguments_match,
                evidence=(
                    "Observed tool arguments match "
                    "the expected sequence."
                    if arguments_match
                    else (
                        "Observed tool arguments do not match "
                        "the expected sequence."
                    )
                ),
            ),
        )
