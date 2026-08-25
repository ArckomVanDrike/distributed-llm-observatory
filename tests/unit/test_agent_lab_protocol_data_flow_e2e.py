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
        "propagate_result",
        "expected_pass",
        "expected_criteria",
    ),
    [
        (
            True,
            True,
            [
                True,
                True,
                True,
                True,
                True,
            ],
        ),
        (
            False,
            False,
            [
                True,
                True,
                True,
                False,
                False,
            ],
        ),
    ],
)
def test_protocol_runner_evaluates_data_dependent_actions(
    tmp_path,
    propagate_result,
    expected_pass,
    expected_criteria,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    task_payload = {
        "schema_version": "0.1",
        "task_id": "agent-protocol-data-flow-001",
        "benchmark_version": "0.1",
        "evaluator_id": "deterministic-evidence-v0-1",
        "family": "agent",
        "category": "technical",
        "difficulty": "easy",
        "task": (
            "Create an item named delta with count 4, "
            "then inspect the created item."
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
                "criterion_id": "tool-result-propagated",
                "description": (
                    "The earlier tool result was propagated."
                ),
            },
        ],
        "available_tools": [
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
                "description": "Inspect an item.",
                "parameters": {
                    "item_id": "string",
                },
            },
        ],
        "tool_results": [
            {
                "tool_name": "create_item",
                "result": {
                    "item_id": "item-742",
                },
            },
        ],
        "expected_actions": [
            {
                "tool_name": "create_item",
                "arguments": {
                    "name": "delta",
                    "count": 4,
                },
            },
            {
                "tool_name": "inspect_item",
                "arguments": {},
            },
        ],
        "expected_propagations": [
            {
                "source_action_index": 0,
                "source_result_field": "item_id",
                "target_action_index": 1,
                "target_argument": "item_id",
            },
        ],
        "enabled": True,
    }

    suite_payload = {
        "schema_version": "0.1",
        "suite_id": "agent-protocol-core",
        "suite_version": "0.7",
        "family": "agent",
        "harness_profile": "sut_protocol",
        "task_ids": [
            "agent-protocol-data-flow-001",
        ],
        "enabled": True,
    }

    (
        task_root
        / "agent-protocol-data-flow-001.json"
    ).write_text(
        json.dumps(task_payload),
        encoding="utf-8",
    )

    (
        suite_root
        / "agent-protocol-core-v0-7.json"
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
                        "target_id": "data-flow-agent",
                        "display_name": "Data Flow Agent",
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

            assert "tool_results" not in metadata_text
            assert (
                "expected_propagations"
                not in metadata_text
            )
            assert "item-742" not in metadata_text

            tools = {
                tool["tool_name"]: tool
                for tool in metadata[
                    "dllo_action_gateway"
                ]["tools"]
            }

            create_tool = tools["create_item"]

            create_request = Request(
                create_tool["endpoint"],
                data=json.dumps(
                    {
                        "name": "delta",
                        "count": 4,
                    }
                ).encode("utf-8"),
                headers={
                    "Authorization": (
                        "Bearer "
                        + create_tool[
                            "authorization"
                        ]["token"]
                    ),
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urlopen(
                create_request,
                timeout=2,
            ) as create_response:
                create_payload = json.loads(
                    create_response.read().decode(
                        "utf-8"
                    )
                )

            # The SUT learns the identifier only here,
            # from the real tool response.
            created_item_id = create_payload[
                "result"
            ]["item_id"]

            inspect_item_id = (
                created_item_id
                if propagate_result
                else "wrong-item"
            )

            inspect_tool = tools["inspect_item"]

            inspect_request = Request(
                inspect_tool["endpoint"],
                data=json.dumps(
                    {
                        "item_id": inspect_item_id,
                    }
                ).encode("utf-8"),
                headers={
                    "Authorization": (
                        "Bearer "
                        + inspect_tool[
                            "authorization"
                        ]["token"]
                    ),
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urlopen(
                inspect_request,
                timeout=2,
            ) as inspect_response:
                assert inspect_response.status == 200

            now = datetime.now(
                timezone.utc,
            ).isoformat()

            payload = json.dumps(
                {
                    "schema_version": "0.1",
                    "context": request_payload["context"],
                    "started_at_utc": now,
                    "finished_at_utc": now,
                    "latency_ms": 7.0,
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

        assert result.session.suite_version == "0.7"
        assert len(execute_requests) == 1
        assert len(result.session.results) == 1

        task_result = result.session.results[0]

        assert (
            task_result.task_id
            == "agent-protocol-data-flow-001"
        )
        assert task_result.task_completed is False
        assert (
            task_result.evaluation.passed
            is expected_pass
        )

        assert [
            criterion.passed
            for criterion
            in task_result.evaluation.criteria
        ] == expected_criteria

        assert result.report.total_tasks == 1
        assert (
            result.report.passed_tasks
            == int(expected_pass)
        )
        assert (
            result.report.pass_rate
            == float(expected_pass)
        )

    finally:
        server.shutdown()
        server.server_close()
        thread.join()
