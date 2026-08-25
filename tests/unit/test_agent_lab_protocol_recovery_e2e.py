import json
import threading
from datetime import datetime, timezone
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from observer.core.agent_lab_protocol_runner import (
    AgentLabProtocolRunner,
)


@pytest.mark.parametrize(
    (
        "recover_after_failure",
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
                True,
            ],
        ),
        (
            False,
            False,
            [
                True,
                False,
                False,
                False,
                True,
                False,
            ],
        ),
    ],
)
def test_protocol_runner_evaluates_recovery_after_tool_failure(
    tmp_path,
    recover_after_failure,
    expected_pass,
    expected_criteria,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"
    suite_root.mkdir()
    task_root.mkdir()

    task_payload = {
        "schema_version": "0.1",
        "task_id": "agent-protocol-recovery-001",
        "benchmark_version": "0.1",
        "evaluator_id": "deterministic-evidence-v0-1",
        "family": "agent",
        "category": "technical",
        "difficulty": "easy",
        "task": (
            "Persist an item named delta with count 4. "
            "If an attempt fails, recover using the "
            "available tools."
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
                "criterion_id": "tool-failure-observed",
                "description": (
                    "The configured runtime tool failure "
                    "was observed."
                ),
            },
            {
                "criterion_id": "recovery-after-failure",
                "description": (
                    "A successful recovery action followed "
                    "the runtime failure."
                ),
            },
        ],
        "available_tools": [
            {
                "tool_name": "persist_primary",
                "description": (
                    "Persist an item using the primary "
                    "backend."
                ),
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
            {
                "tool_name": "persist_fallback",
                "description": (
                    "Persist an item using the fallback "
                    "backend."
                ),
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
        ],
        "tool_failures": [
            {
                "tool_name": "persist_primary",
                "status_code": 503,
                "error": {
                    "code": "temporary_unavailable",
                },
            },
        ],
        "expected_actions": [
            {
                "tool_name": "persist_primary",
                "arguments": {
                    "name": "delta",
                    "count": 4,
                },
            },
            {
                "tool_name": "persist_fallback",
                "arguments": {
                    "name": "delta",
                    "count": 4,
                },
            },
        ],
        "expected_recovery": {
            "failed_action_index": 0,
            "recovery_action_index": 1,
        },
        "enabled": True,
    }

    suite_payload = {
        "schema_version": "0.1",
        "suite_id": "agent-protocol-core",
        "suite_version": "0.8",
        "family": "agent",
        "harness_profile": "sut_protocol",
        "task_ids": [
            "agent-protocol-recovery-001",
        ],
        "enabled": True,
    }

    (
        task_root
        / "agent-protocol-recovery-001.json"
    ).write_text(
        json.dumps(task_payload),
        encoding="utf-8",
    )

    (
        suite_root
        / "agent-protocol-core-v0-8.json"
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
                        "target_id": "recovery-agent",
                        "display_name": "Recovery Agent",
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

            # Observer-only failure/recovery expectations
            # must not be visible before tool execution.
            assert "tool_failures" not in metadata_text
            assert "expected_recovery" not in metadata_text
            assert (
                "temporary_unavailable"
                not in metadata_text
            )
            assert "status_code" not in metadata_text

            tools = {
                tool["tool_name"]: tool
                for tool in metadata[
                    "dllo_action_gateway"
                ]["tools"]
            }

            primary_tool = tools["persist_primary"]

            primary_request = Request(
                primary_tool["endpoint"],
                data=json.dumps(
                    {
                        "name": "delta",
                        "count": 4,
                    }
                ).encode("utf-8"),
                headers={
                    "Authorization": (
                        "Bearer "
                        + primary_tool[
                            "authorization"
                        ]["token"]
                    ),
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            try:
                urlopen(
                    primary_request,
                    timeout=2,
                )
            except HTTPError as exc:
                assert exc.code == 503

                failure_payload = json.loads(
                    exc.read().decode("utf-8")
                )
            else:
                raise AssertionError(
                    "Expected primary tool failure."
                )

            assert failure_payload == {
                "schema_version": "0.1",
                "accepted": True,
                "error": {
                    "code": "temporary_unavailable",
                },
            }

            # The SUT learns that recovery is necessary
            # only after observing the real tool failure.
            failure_code = failure_payload[
                "error"
            ]["code"]

            if recover_after_failure:
                assert (
                    failure_code
                    == "temporary_unavailable"
                )

                fallback_tool = tools[
                    "persist_fallback"
                ]

                fallback_request = Request(
                    fallback_tool["endpoint"],
                    data=json.dumps(
                        {
                            "name": "delta",
                            "count": 4,
                        }
                    ).encode("utf-8"),
                    headers={
                        "Authorization": (
                            "Bearer "
                            + fallback_tool[
                                "authorization"
                            ]["token"]
                        ),
                        "Content-Type": (
                            "application/json"
                        ),
                    },
                    method="POST",
                )

                with urlopen(
                    fallback_request,
                    timeout=2,
                ) as fallback_response:
                    assert fallback_response.status == 200

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
                        "steps": (
                            2
                            if recover_after_failure
                            else 1
                        ),
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

        assert result.session.suite_version == "0.8"
        assert len(execute_requests) == 1
        assert len(result.session.results) == 1

        task_result = result.session.results[0]

        assert (
            task_result.task_id
            == "agent-protocol-recovery-001"
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
