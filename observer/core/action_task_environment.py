from __future__ import annotations

from typing import Any

from observer.core.action_gateway import ActionGateway
from observer.core.observed_action_evidence import (
    ObservedActionEvidenceCollector,
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
        if task.expected_action is None:
            raise ValueError(
                "ActionTaskEnvironment requires "
                "task.expected_action."
            )

        if not task.available_tools:
            raise ValueError(
                "ActionTaskEnvironment requires "
                "task.available_tools."
            )

        self.task = task
        self.gateway = ActionGateway()

        self.collector = ObservedActionEvidenceCollector(
            expected_action=task.expected_action,
            calls_provider=lambda: self.gateway.calls,
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
