import json
import threading
from datetime import datetime, timezone
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from urllib.request import Request, urlopen

import pytest

from observer.core.agent_lab_protocol_runner import (
    AgentLabProtocolRunner,
)


@pytest.mark.parametrize(
    (
        "runtime_state",
        "chosen_tool_name",
        "chosen_arguments",
        "expected_pass",
    ),
    [
        (
            "missing",
            "create_item",
            {
                "name": "delta",
                "count": 4,
            },
            True,
        ),
        (
            "present",
            "inspect_item",
            {
                "name": "delta",
            },
            True,
        ),
        (
            "missing",
            "inspect_item",
            {
                "name": "delta",
            },
            False,
        ),
        (
            "present",
            "create_item",
            {
                "name": "delta",
                "count": 4,
            },
            False,
        ),
    ],
)
def test_protocol_runner_evaluates_multi_branch_runtime_decision(
    tmp_path,
    runtime_state,
    chosen_tool_name,
    chosen_arguments,
    expected_pass,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"
    suite_root.mkdir()
    task_root.mkdir()

    task_payload = {
        "schema_version": "0.1",
        "task_id": "agent-protocol-multi-branch-001",
        "benchmark_version": "0.1",
        "evaluator_id": "deterministic-evidence-v0-1",
        "family": "agent",
        "category": "technical",
        "difficulty": "easy",
        "task": (
            "Check the state of item delta and take "
            "the appropriate next action."
        ),
        "required_capabilities": [
            "text",
            "tools",
        ],
        "success_criteria": [
            {
                "criterion_id": "tool-calls-observed",
                "description": (
                    "Tool calls were observed."
                ),
            },
            {
                "criterion_id": (
                    "tool-sequence-length-match"
                ),
                "description": (
                    "The observed sequence length matches."
                ),
            },
            {
                "criterion_id": (
                    "tool-sequence-order-match"
                ),
                "description": (
                    "The observed sequence order matches."
                ),
            },
            {
                "criterion_id": (
                    "tool-sequence-arguments-match"
                ),
                "description": (
                    "The observed sequence arguments match."
                ),
            },
            {
                "criterion_id": (
                    "branch-source-result-observed"
                ),
                "description": (
                    "The runtime branch source value "
                    "matched a configured option."
                ),
            },
            {
                "criterion_id": "branch-selected",
                "description": (
                    "The branch selected for the runtime "
                    "value was correct."
                ),
            },
        ],
        "available_tools": [
            {
                "tool_name": "check_item",
                "description": (
                    "Return the current state of an item."
                ),
                "parameters": {
                    "name": "string",
                },
            },
            {
                "tool_name": "create_item",
                "description": "Create an item.",
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
            {
                "tool_name": "inspect_item",
                "description": "Inspect an existing item.",
                "parameters": {
                    "name": "string",
                },
            },
        ],
        "tool_results": [
            {
                "tool_name": "check_item",
                "result": {
                    "state": runtime_state,
                },
            },
        ],
        "expected_actions": [
            {
                "tool_name": "check_item",
                "arguments": {
                    "name": "delta",
                },
            },
        ],
        "expected_branches": {
            "source_action_index": 0,
            "source_result_field": "state",
            "options": [
                {
                    "expected_value": "missing",
                    "action": {
                        "tool_name": "create_item",
                        "arguments": {
                            "name": "delta",
                            "count": 4,
                        },
                    },
                },
                {
                    "expected_value": "present",
                    "action": {
                        "tool_name": "inspect_item",
                        "arguments": {
                            "name": "delta",
                        },
                    },
                },
            ],
        },
        "enabled": True,
    }

    suite_payload = {
        "schema_version": "0.1",
        "suite_id": "agent-protocol-core",
        "suite_version": "0.10",
        "family": "agent",
        "harness_profile": "sut_protocol",
        "task_ids": [
            "agent-protocol-multi-branch-001",
        ],
        "enabled": True,
    }

    (
        task_root
        / "agent-protocol-multi-branch-001.json"
    ).write_text(
        json.dumps(task_payload),
        encoding="utf-8",
    )

    (
        suite_root
        / "agent-protocol-core-v0-10.json"
    ).write_text(
        json.dumps(suite_payload),
        encoding="utf-8",
    )

    execute_requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/v1/manifest":
                self.send_response(404)
                self.end_headers()
                return

            payload = json.dumps(
                {
                    "schema_version": "0.1",
                    "manifest": {
                        "schema_version": "0.1",
                        "target_id": "multi-branch-agent",
                        "display_name": "Multi Branch Agent",
                        "target_type": "agent",
                        "capabilities": [
                            "text",
                            "tools",
                        ],
                    },
                }
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json",
            )
            self.send_header(
                "Content-Length",
                str(len(payload)),
            )
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self):
            if self.path != "/v1/execute":
                self.send_response(404)
                self.end_headers()
                return

            length = int(
                self.headers["Content-Length"]
            )
            request_payload = json.loads(
                self.rfile.read(length).decode("utf-8")
            )

            execute_requests.append(request_payload)

            metadata = request_payload["metadata"]
            metadata_text = json.dumps(
                metadata,
                sort_keys=True,
            )

            assert "expected_branches" not in metadata_text
            assert "tool_results" not in metadata_text
            assert '"state": "missing"' not in metadata_text
            assert '"state": "present"' not in metadata_text

            tools = {
                tool["tool_name"]: tool
                for tool in metadata[
                    "dllo_action_gateway"
                ]["tools"]
            }

            check_tool = tools["check_item"]

            check_request = Request(
                check_tool["endpoint"],
                data=json.dumps(
                    {
                        "name": "delta",
                    }
                ).encode("utf-8"),
                headers={
                    "Authorization": (
                        "Bearer "
                        + check_tool[
                            "authorization"
                        ]["token"]
                    ),
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urlopen(
                check_request,
                timeout=2,
            ) as check_response:
                check_payload = json.loads(
                    check_response.read().decode("utf-8")
                )

            observed_state = check_payload[
                "result"
            ]["state"]

            assert observed_state == runtime_state

            chosen_tool = tools[chosen_tool_name]

            branch_request = Request(
                chosen_tool["endpoint"],
                data=json.dumps(
                    chosen_arguments
                ).encode("utf-8"),
                headers={
                    "Authorization": (
                        "Bearer "
                        + chosen_tool[
                            "authorization"
                        ]["token"]
                    ),
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urlopen(
                branch_request,
                timeout=2,
            ) as branch_response:
                assert branch_response.status == 200

            now = datetime.now(
                timezone.utc,
            ).isoformat()

            payload = json.dumps(
                {
                    "schema_version": "0.1",
                    "context": request_payload["context"],
                    "started_at_utc": now,
                    "finished_at_utc": now,
                    "latency_ms": 6.0,
                    "task_completed": False,
                    "output_text": None,
                    "retry_count": 0,
                    "human_intervention_count": 0,
                    "error_type": None,
                    "metrics": {
                        "steps": 2,
                    },
                }
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json",
            )
            self.send_header(
                "Content-Length",
                str(len(payload)),
            )
            self.end_headers()
            self.wfile.write(payload)

        def log_message(
            self,
            format,
            *args,
        ):
            return

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        Handler,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        runner = AgentLabProtocolRunner(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
            suite_root=suite_root,
            task_root=task_root,
        )

        result = runner.run(
            base_url=f"http://{host}:{port}",
            generated_at_utc=datetime.now(
                timezone.utc,
            ),
        )

        assert result.session.suite_version == "0.10"
        assert len(execute_requests) == 1
        assert len(result.session.results) == 1

        task_result = result.session.results[0]

        assert (
            task_result.task_id
            == "agent-protocol-multi-branch-001"
        )
        assert (
            task_result.evaluation.passed
            is expected_pass
        )

        criteria = [
            criterion.passed
            for criterion
            in task_result.evaluation.criteria
        ]

        expected_criteria = (
            [True, True, True, True, True, True]
            if expected_pass
            else [
                True,
                True,
                False,
                False,
                True,
                False,
            ]
        )

        assert criteria == expected_criteria

        assert result.report.total_tasks == 1
        assert (
            result.report.passed_tasks
            == int(expected_pass)
        )

    finally:
        server.shutdown()
        server.server_close()
        thread.join()
