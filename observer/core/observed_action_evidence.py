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
from schemas.benchmark import BenchmarkExpectedAction


class ObservedActionEvidenceCollector(TaskEvidenceCollector):
    """
    Converts Observatory-observed tool calls into deterministic
    criterion evidence.

    This component evaluates observed gateway state only. It does not
    execute the SUT and does not use SUT self-reported completion.
    """

    def __init__(
        self,
        *,
        expected_action: BenchmarkExpectedAction,
        calls_provider: Callable[
            [],
            tuple[ObservedActionCall, ...],
        ],
    ) -> None:
        self.expected_action = expected_action
        self.calls_provider = calls_provider

    def collect(
        self,
    ) -> tuple[TaskCriterionEvidence, ...]:
        calls = self.calls_provider()

        tool_called = bool(calls)

        tool_name_match = (
            tool_called
            and all(
                call.tool_name
                == self.expected_action.tool_name
                for call in calls
            )
        )

        tool_arguments_match = (
            tool_called
            and all(
                json_flat_object_equal(
                    call.arguments,
                    self.expected_action.arguments,
                )
                for call in calls
            )
        )

        tool_call_count_match = (
            len(calls)
            == self.expected_action.call_count
        )

        return (
            TaskCriterionEvidence(
                criterion_id="tool-called",
                passed=tool_called,
                evidence=(
                    "Observed at least one tool call."
                    if tool_called
                    else "Observed no tool calls."
                ),
            ),
            TaskCriterionEvidence(
                criterion_id="tool-name-match",
                passed=tool_name_match,
                evidence=(
                    "Observed tool name matches "
                    "the expected tool."
                    if tool_name_match
                    else (
                        "Observed tool name does not "
                        "match the expected tool."
                    )
                ),
            ),
            TaskCriterionEvidence(
                criterion_id="tool-arguments-match",
                passed=tool_arguments_match,
                evidence=(
                    "Observed tool arguments match "
                    "the expected arguments."
                    if tool_arguments_match
                    else (
                        "Observed tool arguments do not "
                        "match the expected arguments."
                    )
                ),
            ),
            TaskCriterionEvidence(
                criterion_id="tool-call-count-match",
                passed=tool_call_count_match,
                evidence=(
                    "Observed tool call count matches "
                    "the expected count."
                    if tool_call_count_match
                    else (
                        "Observed tool call count does not "
                        "match the expected count."
                    )
                ),
            ),
        )
