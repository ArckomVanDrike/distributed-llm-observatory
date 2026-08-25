from __future__ import annotations

from collections.abc import Callable

from observer.core.action_gateway import (
    ObservedActionCall,
    ObservedActionOutcome,
)
from observer.core.json_value_comparison import (
    json_flat_object_equal,
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
    BenchmarkExpectedRecovery,
    BenchmarkToolFailure,
)


class ObservedActionRecoveryEvidenceCollector(
    TaskEvidenceCollector
):
    """
    Evaluates an observed action sequence containing a runtime
    tool failure followed by an expected recovery action.

    The failure criterion is based on the outcome actually observed
    by the Observatory-owned gateway rather than merely on benchmark
    configuration.
    """

    def __init__(
        self,
        *,
        expected_actions: tuple[
            BenchmarkExpectedActionCall,
            ...,
        ],
        tool_failures: tuple[
            BenchmarkToolFailure,
            ...,
        ],
        expected_recovery: BenchmarkExpectedRecovery,
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
        self.tool_failures = tool_failures
        self.expected_recovery = expected_recovery
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

        order_match = next(
            evidence.passed
            for evidence in sequence_evidence
            if (
                evidence.criterion_id
                == "tool-sequence-order-match"
            )
        )

        failed_index = (
            self.expected_recovery.failed_action_index
        )
        recovery_index = (
            self.expected_recovery.recovery_action_index
        )

        failed_action = self.expected_actions[
            failed_index
        ]

        failures_by_tool = {
            failure.tool_name: failure
            for failure in self.tool_failures
        }

        expected_failure = failures_by_tool[
            failed_action.tool_name
        ]

        failure_observed = False

        if (
            failed_index < len(calls)
            and failed_index < len(outcomes)
        ):
            failed_call = calls[failed_index]
            failed_outcome = outcomes[failed_index]

            failure_observed = (
                failed_call.tool_name
                == failed_action.tool_name
                and failed_outcome.tool_name
                == failed_action.tool_name
                and failed_outcome.succeeded is False
                and (
                    failed_outcome.status_code
                    == expected_failure.status_code
                )
                and failed_outcome.result is None
                and failed_outcome.error is not None
                and json_flat_object_equal(
                    failed_outcome.error,
                    expected_failure.error,
                )
            )

        recovery_succeeded = False

        if (
            failure_observed
            and order_match
            and recovery_index < len(calls)
            and recovery_index < len(outcomes)
        ):
            recovery_action = self.expected_actions[
                recovery_index
            ]
            recovery_call = calls[recovery_index]
            recovery_outcome = outcomes[recovery_index]

            recovery_succeeded = (
                recovery_call.tool_name
                == recovery_action.tool_name
                and recovery_outcome.tool_name
                == recovery_action.tool_name
                and recovery_outcome.succeeded is True
                and 200
                <= recovery_outcome.status_code
                < 300
            )

        failure_evidence = TaskCriterionEvidence(
            criterion_id="tool-failure-observed",
            passed=failure_observed,
            evidence=(
                "Observed the configured runtime tool failure."
                if failure_observed
                else (
                    "Did not observe the configured runtime "
                    "tool failure."
                )
            ),
        )

        recovery_evidence = TaskCriterionEvidence(
            criterion_id="recovery-after-failure",
            passed=recovery_succeeded,
            evidence=(
                "Observed a successful recovery action after "
                "the expected runtime tool failure."
                if recovery_succeeded
                else (
                    "Did not observe a successful recovery "
                    "action after the expected runtime "
                    "tool failure."
                )
            ),
        )

        return (
            *sequence_evidence,
            failure_evidence,
            recovery_evidence,
        )
