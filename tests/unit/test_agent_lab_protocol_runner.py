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
        assert result.session.suite_version == "0.3"

        assert [
            request["context"]["task_id"]
            for request in execute_requests
        ] == [
            "agent-protocol-smoke-001",
            "agent-protocol-instruction-001",
            "agent-protocol-structured-output-001",
        ]

        assert len(result.session.results) == 3

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
        assert result.report.suite_version == "0.3"
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
