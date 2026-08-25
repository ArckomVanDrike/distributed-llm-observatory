from __future__ import annotations

from collections.abc import Callable

from observer.core.action_gateway import (
    ObservedActionCall,
    ObservedActionOutcome,
)
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
    BenchmarkExpectedBranches,
)


class ObservedActionMultiBranchEvidenceCollector(
    TaskEvidenceCollector
):
    """
    Evaluates a runtime-dependent decision with multiple
    possible branch actions.

    The expected branch is selected from the actual source
    outcome observed by the Observatory-owned gateway.
    """

    def __init__(
        self,
        *,
        expected_actions: tuple[
            BenchmarkExpectedActionCall,
            ...,
        ],
        expected_branches: BenchmarkExpectedBranches,
        calls_provider: Callable[
            [],
            tuple[ObservedActionCall, ...],
        ],
        outcomes_provider: Callable[
            [],
            tuple[ObservedActionOutcome, ...],
        ],
    ) -> None:
        self.expected_actions = expected_actions
        self.expected_branches = expected_branches
        self.calls_provider = calls_provider
        self.outcomes_provider = outcomes_provider

    def _selected_action(
        self,
        calls: tuple[ObservedActionCall, ...],
        outcomes: tuple[ObservedActionOutcome, ...],
    ) -> BenchmarkExpectedActionCall | None:
        source_index = (
            self.expected_branches.source_action_index
        )

        if (
            source_index >= len(calls)
            or source_index >= len(outcomes)
        ):
            return None

        source_action = self.expected_actions[
            source_index
        ]
        source_call = calls[source_index]
        source_outcome = outcomes[source_index]

        if (
            source_call.tool_name
            != source_action.tool_name
            or source_outcome.tool_name
            != source_action.tool_name
            or source_outcome.succeeded is not True
            or not (
                200
                <= source_outcome.status_code
                < 300
            )
            or source_outcome.result is None
        ):
            return None

        field = (
            self.expected_branches.source_result_field
        )

        if field not in source_outcome.result:
            return None

        runtime_value = source_outcome.result[field]

        for option in self.expected_branches.options:
            if json_scalar_equal(
                runtime_value,
                option.expected_value,
            ):
                return option.action

        return None

    def collect(
        self,
    ) -> tuple[TaskCriterionEvidence, ...]:
        calls = self.calls_provider()
        outcomes = self.outcomes_provider()

        selected_action = self._selected_action(
            calls,
            outcomes,
        )

        source_result_observed = (
            selected_action is not None
        )

        effective_expected_actions = (
            self.expected_actions
            if selected_action is None
            else (
                *self.expected_actions,
                selected_action,
            )
        )

        sequence_evidence = (
            ObservedActionSequenceEvidenceCollector(
                expected_actions=effective_expected_actions,
                calls_provider=lambda: calls,
            ).collect()
        )

        evidence_by_id = {
            evidence.criterion_id: evidence
            for evidence in sequence_evidence
        }

        branch_selected = (
            source_result_observed
            and evidence_by_id[
                "tool-sequence-length-match"
            ].passed
            and evidence_by_id[
                "tool-sequence-order-match"
            ].passed
            and evidence_by_id[
                "tool-sequence-arguments-match"
            ].passed
        )

        source_evidence = TaskCriterionEvidence(
            criterion_id=(
                "branch-source-result-observed"
            ),
            passed=source_result_observed,
            evidence=(
                "Observed a runtime source value matching "
                "a configured branch option."
                if source_result_observed
                else (
                    "Did not observe a runtime source "
                    "value matching a configured branch "
                    "option."
                )
            ),
        )

        branch_evidence = TaskCriterionEvidence(
            criterion_id="branch-selected",
            passed=branch_selected,
            evidence=(
                "Observed the branch action selected by "
                "the runtime source value."
                if branch_selected
                else (
                    "Did not observe the branch action "
                    "selected by the runtime source value."
                )
            ),
        )

        return (
            *sequence_evidence,
            source_evidence,
            branch_evidence,
        )
