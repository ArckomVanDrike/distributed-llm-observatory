from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ReferenceAgentResult:
    task_completed: bool
    output_text: str | None = None
    retry_count: int = 0
    human_intervention_count: int = 0
    metrics: dict[str, Any] | None = None


class ReferenceProtocolAgent:
    def manifest(self) -> dict[str, object]:
        return {
            "schema_version": "0.1",
            "target_id": "dllo-reference-protocol-agent",
            "display_name": "DLLO Reference Protocol Agent",
            "target_type": "agent",
            "capabilities": [
                "text",
                "tools",
            ],
        }

    def execute(
        self,
        *,
        task: str,
        metadata: dict[str, Any] | None,
    ) -> ReferenceAgentResult:
        if "DLLO-AGENT-SMOKE-001" in task:
            return ReferenceAgentResult(
                task_completed=True,
                output_text="DLLO-AGENT-SMOKE-001",
            )

        if "Sort these four tokens" in task:
            return ReferenceAgentResult(
                task_completed=True,
                output_text="alpha,bravo,charlie,delta",
            )

        if "Return only one JSON object" in task:
            return ReferenceAgentResult(
                task_completed=True,
                output_text=(
                    '{"name":"delta","count":4,'
                    '"active":true}'
                ),
            )

        if (
            "Use the available record_item tool exactly once"
            in task
        ):
            self._call_tool(
                metadata,
                "record_item",
                {
                    "name": "delta",
                    "count": 4,
                },
            )

            return ReferenceAgentResult(
                task_completed=True,
            )

        if (
            "Check the state of item delta"
            in task
            or (
                "Determine the current condition "
                "of item delta"
                in task
            )
        ):
            self._check_and_act(metadata)

            return ReferenceAgentResult(
                task_completed=True,
            )

        if (
            "If an attempt fails, recover using the available tools."
            in task
        ):
            arguments = {
                "name": "delta",
                "count": 4,
            }

            try:
                self._call_tool(
                    metadata,
                    "persist_primary",
                    arguments,
                )
            except HTTPError:
                self._call_tool(
                    metadata,
                    "persist_fallback",
                    arguments,
                )

            return ReferenceAgentResult(
                task_completed=True,
            )

        if (
            "then inspect the created item"
            in task
        ):
            create_response = self._call_tool(
                metadata,
                "create_item",
                {
                    "name": "delta",
                    "count": 4,
                },
            )

            result = create_response.get("result")

            if not isinstance(result, dict):
                raise ValueError(
                    "create_item did not return a result."
                )

            item_id = result.get("item_id")

            if not isinstance(item_id, str):
                raise ValueError(
                    "create_item did not return an item_id."
                )

            self._call_tool(
                metadata,
                "inspect_item",
                {
                    "item_id": item_id,
                },
            )

            return ReferenceAgentResult(
                task_completed=True,
            )

        if (
            "then inspect that item"
            in task
        ):
            self._call_tool(
                metadata,
                "record_item",
                {
                    "name": "delta",
                    "count": 4,
                },
            )

            self._call_tool(
                metadata,
                "inspect_item",
                {
                    "name": "delta",
                },
            )

            return ReferenceAgentResult(
                task_completed=True,
            )

        if (
            "using the appropriate available tool"
            in task
        ):
            self._call_tool(
                metadata,
                "record_item",
                {
                    "name": "delta",
                    "count": 4,
                },
            )

            return ReferenceAgentResult(
                task_completed=True,
            )

        return ReferenceAgentResult(
            task_completed=False,
        )

    def _check_and_act(
        self,
        metadata: dict[str, Any] | None,
    ) -> None:
        check_response = self._call_tool(
            metadata,
            "check_item",
            {
                "name": "delta",
            },
        )

        result = check_response.get("result")

        if not isinstance(result, dict):
            raise ValueError(
                "check_item did not return a result."
            )

        state = result.get("state")

        if state == "missing":
            self._call_tool(
                metadata,
                "create_item",
                {
                    "name": "delta",
                    "count": 4,
                },
            )
            return

        if state == "present":
            self._call_tool(
                metadata,
                "inspect_item",
                {
                    "name": "delta",
                },
            )
            return

        raise ValueError(
            "check_item returned an unknown state."
        )

    def _call_tool(
        self,
        metadata: dict[str, Any] | None,
        tool_name: str,
        arguments: dict[str, object],
    ) -> dict[str, Any]:
        tool = self._find_tool(
            metadata,
            tool_name,
        )

        authorization = tool["authorization"]

        request = Request(
            tool["endpoint"],
            data=json.dumps(arguments).encode("utf-8"),
            headers={
                "Authorization": (
                    f"Bearer {authorization['token']}"
                ),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        with urlopen(
            request,
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        if not isinstance(payload, dict):
            raise ValueError(
                "Tool response must be a JSON object."
            )

        return payload

    def _find_tool(
        self,
        metadata: dict[str, Any] | None,
        tool_name: str,
    ) -> dict[str, Any]:
        if metadata is None:
            raise ValueError(
                "Tool metadata is required."
            )

        gateway = metadata.get(
            "dllo_action_gateway"
        )

        if not isinstance(gateway, dict):
            raise ValueError(
                "DLLO action gateway metadata is required."
            )

        tools = gateway.get("tools")

        if not isinstance(tools, list):
            raise ValueError(
                "DLLO action gateway tools are required."
            )

        for tool in tools:
            if (
                isinstance(tool, dict)
                and tool.get("tool_name") == tool_name
            ):
                return tool

        raise ValueError(
            f"Tool is not available: {tool_name}"
        )
