import json
import threading
from datetime import datetime, timezone
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)

import pytest

from observer.core.agent_lab_protocol_runner import (
    AgentLabProtocolRun,
    AgentLabProtocolRunner,
    AgentLabProtocolRunnerError,
)
from schemas.agent_lab import (
    AgentLabRunArtifact,
    AgentTechnicalReport,
    AgentTestSession,
    AgentTestSessionStatus,
)
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)

EXPECTED_OUTPUT = "DLLO-AGENT-SMOKE-001"
INSTRUCTION_EXPECTED_OUTPUT = "alpha,bravo,charlie,delta"
STRUCTURED_EXPECTED_OUTPUT = '{"name":"delta","count":4,"active":true}'


def test_protocol_runner_builds_session_and_report():
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
                        "target_id": "protocol-runner-agent",
                        "display_name": "Protocol Runner Agent",
                        "target_type": "agent",
                        "capabilities": [
                            "text",
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

            now = datetime.now(
                timezone.utc,
            ).isoformat()

            payload = json.dumps(
                {
                    "schema_version": "0.1",
                    "context": request_payload["context"],
                    "started_at_utc": now,
                    "finished_at_utc": now,
                    "latency_ms": 4.5,
                    "task_completed": False,
                    "output_text": {
                            "agent-protocol-smoke-001": EXPECTED_OUTPUT,
                            "agent-protocol-instruction-001": (
                                INSTRUCTION_EXPECTED_OUTPUT
                            ),
                            "agent-protocol-structured-output-001": (
                                STRUCTURED_EXPECTED_OUTPUT
                            ),
                        }[request_payload["context"]["task_id"]],
                    "retry_count": 0,
                    "human_intervention_count": 0,
                    "error_type": None,
                    "metrics": {
                        "steps": 1,
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

    generated_at = datetime(
        2026,
        8,
        24,
        19,
        0,
        tzinfo=timezone.utc,
    )

    try:
        host, port = server.server_address

        runner = AgentLabProtocolRunner(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )

        result = runner.run(
            base_url=f"http://{host}:{port}",
            generated_at_utc=generated_at,
        )

        assert (
            result.session.status
            is AgentTestSessionStatus.COMPLETED
        )
        assert (
            result.session.target.target_id
            == "protocol-runner-agent"
        )
        assert result.session.suite_id == "agent-protocol-core"
        assert result.session.suite_version == "0.4"

        assert [
            request["context"]["task_id"]
            for request in execute_requests
        ] == [
            "agent-protocol-smoke-001",
            "agent-protocol-instruction-001",
            "agent-protocol-structured-output-001",
        ]

        assert len(result.session.results) == 3

        action_selection = next(
            selection
            for selection in result.session.selections
            if (
                selection.task_id
                == "agent-protocol-action-001"
            )
        )

        assert (
            action_selection.status.value
            == "incompatible"
        )
        assert {
            capability.value
            for capability
            in action_selection.missing_capabilities
        } == {
            "tools",
        }

        assert all(
            task_result.task_completed is False
            for task_result in result.session.results
        )
        assert all(
            task_result.evaluation.passed is True
            for task_result in result.session.results
        )

        assert result.report.session_id == result.session.session_id
        assert result.report.target_id == "protocol-runner-agent"
        assert result.report.suite_id == "agent-protocol-core"
        assert result.report.suite_version == "0.4"
        assert result.report.generated_at_utc == generated_at
        assert result.report.total_tasks == 3
        assert result.report.passed_tasks == 3
        assert result.report.pass_rate == 1.0

    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_protocol_runner_normalizes_operational_errors():
    runner = AgentLabProtocolRunner(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    with pytest.raises(
        AgentLabProtocolRunnerError,
        match="localhost or loopback",
    ):
        runner.run(
            base_url="https://example.com",
            generated_at_utc=datetime.now(timezone.utc),
        )


def test_protocol_run_builds_valid_artifact():
    now = datetime.now(timezone.utc)

    session = AgentTestSession(
        target=TargetManifest(
            target_id="artifact-agent",
            display_name="Artifact Agent",
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        ),
        suite_id="agent-protocol-core",
        suite_version="0.1",
        status=AgentTestSessionStatus.COMPLETED,
        started_at_utc=now,
        completed_at_utc=now,
    )

    report = AgentTechnicalReport(
        session_id=session.session_id,
        target_id=session.target.target_id,
        suite_id=session.suite_id,
        suite_version=session.suite_version,
        generated_at_utc=now,
        total_tasks=0,
        passed_tasks=0,
        failed_tasks=0,
        task_completion_rate=0.0,
        pass_rate=None,
        median_latency_ms=None,
    )

    run = AgentLabProtocolRun(
        session=session,
        report=report,
    )

    artifact = run.to_artifact()

    assert isinstance(
        artifact,
        AgentLabRunArtifact,
    )
    assert artifact.session == session
    assert artifact.technical_report == report


def test_protocol_runner_executes_observed_action_task(
    tmp_path,
):
    from urllib.request import Request, urlopen

    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    task_payload = {
        "schema_version": "0.1",
        "task_id": "agent-protocol-action-001",
        "benchmark_version": "0.1",
        "evaluator_id": "deterministic-evidence-v0-1",
        "family": "agent",
        "category": "technical",
        "difficulty": "easy",
        "task": (
            "Use the available record_item tool exactly once "
            "with name delta and count 4."
        ),
        "required_capabilities": [
            "text",
            "tools",
        ],
        "success_criteria": [
            {
                "criterion_id": "tool-called",
                "description": (
                    "At least one tool call was observed."
                ),
            },
            {
                "criterion_id": "tool-name-match",
                "description": (
                    "The observed tool name matches."
                ),
            },
            {
                "criterion_id": "tool-arguments-match",
                "description": (
                    "The observed tool arguments match."
                ),
            },
            {
                "criterion_id": "tool-call-count-match",
                "description": (
                    "The observed tool call count matches."
                ),
            },
        ],
        "available_tools": [
            {
                "tool_name": "record_item",
                "description": "Record one item.",
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
        ],
        "expected_action": {
            "tool_name": "record_item",
            "arguments": {
                "name": "delta",
                "count": 4,
            },
            "call_count": 1,
        },
        "enabled": True,
    }

    suite_payload = {
        "schema_version": "0.1",
        "suite_id": "agent-protocol-core",
        "suite_version": "0.4",
        "family": "agent",
        "harness_profile": "sut_protocol",
        "task_ids": [
            "agent-protocol-action-001",
        ],
        "enabled": True,
    }

    (
        task_root
        / "agent-protocol-action-001.json"
    ).write_text(
        json.dumps(task_payload),
        encoding="utf-8",
    )

    (
        suite_root
        / "agent-protocol-core-v0-4.json"
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
                        "target_id": "observed-action-agent",
                        "display_name": (
                            "Observed Action Agent"
                        ),
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

            gateway_metadata = metadata[
                "dllo_action_gateway"
            ]

            assert (
                gateway_metadata["schema_version"]
                == "0.1"
            )

            assert len(
                gateway_metadata["tools"]
            ) == 1

            tool = gateway_metadata["tools"][0]

            assert tool["tool_name"] == "record_item"
            assert tool["description"] == "Record one item."
            assert tool["parameters"] == {
                "name": "string",
                "count": "integer",
            }

            metadata_text = json.dumps(metadata)

            assert "expected_action" not in metadata_text
            assert "call_count" not in metadata_text

            action_request = Request(
                tool["endpoint"],
                data=json.dumps(
                    {
                        "name": "delta",
                        "count": 4,
                    }
                ).encode("utf-8"),
                headers={
                    "Authorization": (
                        "Bearer "
                        + tool["authorization"]["token"]
                    ),
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urlopen(
                action_request,
                timeout=2,
            ) as action_response:
                assert action_response.status == 200

            now = datetime.now(
                timezone.utc,
            ).isoformat()

            payload = json.dumps(
                {
                    "schema_version": "0.1",
                    "context": request_payload["context"],
                    "started_at_utc": now,
                    "finished_at_utc": now,
                    "latency_ms": 5.0,

                    # Deliberately false.
                    # Observatory-owned evidence decides.
                    "task_completed": False,

                    "output_text": None,
                    "retry_count": 0,
                    "human_intervention_count": 0,
                    "error_type": None,
                    "metrics": {
                        "steps": 1,
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

        assert result.session.suite_version == "0.4"
        assert len(execute_requests) == 1

        assert len(result.session.results) == 1

        task_result = result.session.results[0]

        assert (
            task_result.task_id
            == "agent-protocol-action-001"
        )

        assert task_result.task_completed is False
        assert task_result.evaluation.passed is True

        assert all(
            criterion.passed
            for criterion
            in task_result.evaluation.criteria
        )

        assert result.report.total_tasks == 1
        assert result.report.passed_tasks == 1
        assert result.report.pass_rate == 1.0

    finally:
        server.shutdown()
        server.server_close()
        thread.join()
