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
    BenchmarkExpectedBranch,
    BenchmarkToolResult,
)


class ObservedActionBranchEvidenceCollector(
    TaskEvidenceCollector
):
    """
    Evaluates a runtime-dependent branch decision.

    The source value must have been actually observed in the
    Observatory-owned gateway outcome before the expected branch
    action can be considered selected.
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
        expected_branch: BenchmarkExpectedBranch,
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
        self.tool_results = tool_results
        self.expected_branch = expected_branch
        self.calls_provider = calls_provider
        self.outcomes_provider = outcomes_provider

    def collect(
        self,
    ) -> tuple[TaskCriterionEvidence, ...]:
        calls = self.calls_provider()
        outcomes = self.outcomes_provider()

        sequence_evidence = (
            ObservedActionSequenceEvidenceCollector(
                expected_actions=self.expected_actions,
                calls_provider=lambda: calls,
            ).collect()
        )

        evidence_by_id = {
            evidence.criterion_id: evidence
            for evidence in sequence_evidence
        }

        order_match = evidence_by_id[
            "tool-sequence-order-match"
        ].passed
        arguments_match = evidence_by_id[
            "tool-sequence-arguments-match"
        ].passed

        source_index = (
            self.expected_branch.source_action_index
        )
        source_action = self.expected_actions[
            source_index
        ]

        source_result_observed = False

        if (
            source_index < len(calls)
            and source_index < len(outcomes)
        ):
            source_call = calls[source_index]
            source_outcome = outcomes[source_index]

            runtime_result = source_outcome.result

            source_result_observed = (
                source_call.tool_name
                == source_action.tool_name
                and source_outcome.tool_name
                == source_action.tool_name
                and source_outcome.succeeded is True
                and 200
                <= source_outcome.status_code
                < 300
                and runtime_result is not None
                and (
                    self.expected_branch.source_result_field
                    in runtime_result
                )
                and json_scalar_equal(
                    runtime_result[
                        self.expected_branch.source_result_field
                    ],
                    self.expected_branch.expected_value,
                )
            )

        branch_selected = (
            source_result_observed
            and order_match
            and arguments_match
        )

        source_evidence = TaskCriterionEvidence(
            criterion_id="branch-source-result-observed",
            passed=source_result_observed,
            evidence=(
                "Observed the expected runtime branch source value."
                if source_result_observed
                else (
                    "Did not observe the expected runtime "
                    "branch source value."
                )
            ),
        )

        branch_evidence = TaskCriterionEvidence(
            criterion_id="branch-selected",
            passed=branch_selected,
            evidence=(
                "Observed the expected branch action after "
                "the runtime source value."
                if branch_selected
                else (
                    "Did not observe the expected branch "
                    "action after the runtime source value."
                )
            ),
        )

        return (
            *sequence_evidence,
            source_evidence,
            branch_evidence,
        )
