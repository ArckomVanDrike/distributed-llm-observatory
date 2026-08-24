import json
import threading
from datetime import datetime, timezone
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)

import pytest

from observer.core.agent_lab_protocol_runner import (
    AgentLabProtocolRunner,
    AgentLabProtocolRunnerError,
)
from schemas.agent_lab import AgentTestSessionStatus

EXPECTED_OUTPUT = "DLLO-AGENT-SMOKE-001"


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
                    "output_text": EXPECTED_OUTPUT,
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
        assert result.session.suite_version == "0.1"

        assert len(execute_requests) == 1
        assert (
            execute_requests[0]["context"]["task_id"]
            == "agent-protocol-smoke-001"
        )

        assert len(result.session.results) == 1

        task_result = result.session.results[0]

        assert task_result.task_completed is False
        assert task_result.evaluation.passed is True

        assert result.report.session_id == result.session.session_id
        assert result.report.target_id == "protocol-runner-agent"
        assert result.report.suite_id == "agent-protocol-core"
        assert result.report.suite_version == "0.1"
        assert result.report.generated_at_utc == generated_at
        assert result.report.total_tasks == 1
        assert result.report.passed_tasks == 1
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
