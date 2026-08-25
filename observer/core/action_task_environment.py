from __future__ import annotations

from typing import Any

from observer.core.action_gateway import ActionGateway
from observer.core.observed_action_data_flow_evidence import (
    ObservedActionDataFlowEvidenceCollector,
)
from observer.core.observed_action_evidence import (
    ObservedActionEvidenceCollector,
)
from observer.core.observed_action_sequence_evidence import (
    ObservedActionSequenceEvidenceCollector,
)
from schemas.benchmark import BenchmarkTask


class ActionTaskEnvironment:
    """
    Runtime environment for one benchmark task with observable actions.

    SUT-visible tool metadata is kept separate from observer-only
    expected action data and evidence collection.
    """

    def __init__(
        self,
        task: BenchmarkTask,
    ) -> None:
        if (
            task.expected_action is None
            and task.expected_actions is None
        ):
            raise ValueError(
                "ActionTaskEnvironment requires "
                "expected action data."
            )

        if not task.available_tools:
            raise ValueError(
                "ActionTaskEnvironment requires "
                "task.available_tools."
            )

        self.task = task
        self.gateway = ActionGateway(
            tool_results={
                tool_result.tool_name: dict(
                    tool_result.result
                )
                for tool_result in task.tool_results
            },
        )

        if task.expected_action is not None:
            self.collector = ObservedActionEvidenceCollector(
                expected_action=task.expected_action,
                calls_provider=lambda: self.gateway.calls,
            )
        elif task.expected_propagations is not None:
            assert task.expected_actions is not None

            self.collector = (
                ObservedActionDataFlowEvidenceCollector(
                    expected_actions=tuple(
                        task.expected_actions
                    ),
                    tool_results=tuple(
                        task.tool_results
                    ),
                    expected_propagations=tuple(
                        task.expected_propagations
                    ),
                    calls_provider=(
                        lambda: self.gateway.calls
                    ),
                )
            )
        else:
            assert task.expected_actions is not None

            self.collector = (
                ObservedActionSequenceEvidenceCollector(
                    expected_actions=tuple(
                        task.expected_actions
                    ),
                    calls_provider=(
                        lambda: self.gateway.calls
                    ),
                )
            )

    @property
    def metadata(self) -> dict[str, Any]:
        tools = []

        for tool in self.task.available_tools:
            tools.append(
                {
                    "tool_name": tool.tool_name,
                    "description": tool.description,
                    "parameters": dict(tool.parameters),
                    "endpoint": self.gateway.tool_url(
                        tool.tool_name
                    ),
                    "authorization": {
                        "scheme": "bearer",
                        "token": self.gateway.token,
                    },
                }
            )

        return {
            "dllo_action_gateway": {
                "schema_version": "0.1",
                "tools": tools,
            },
        }

    def __enter__(
        self,
    ) -> ActionTaskEnvironment:
        self.gateway.start()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.gateway.close()
