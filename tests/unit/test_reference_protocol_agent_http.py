import json
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

from observer.reference_protocol_agent import (
    ReferenceProtocolAgent,
)
from observer.reference_protocol_agent_http import (
    make_reference_protocol_handler,
)


def test_reference_protocol_http_serves_manifest():
    agent = ReferenceProtocolAgent()

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_reference_protocol_handler(agent),
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        with urlopen(
            f"http://{host}:{port}/v1/manifest",
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        assert response.status == 200

        assert payload == {
            "schema_version": "0.1",
            "manifest": {
                "schema_version": "0.1",
                "target_id": (
                    "dllo-reference-protocol-agent"
                ),
                "display_name": (
                    "DLLO Reference Protocol Agent"
                ),
                "target_type": "agent",
                "capabilities": [
                    "text",
                    "tools",
                ],
            },
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_reference_protocol_http_executes_task():
    agent = ReferenceProtocolAgent()

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_reference_protocol_handler(agent),
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        request_payload = {
            "schema_version": "0.1",
            "context": {
                "observer_id": "observer-test",
                "region_code": "CL-Los-Lagos",
                "benchmark_version": "0.1",
                "task_id": "agent-protocol-smoke-001",
                "target_id": (
                    "dllo-reference-protocol-agent"
                ),
            },
            "task": (
                "Return exactly DLLO-AGENT-SMOKE-001 "
                "and no additional characters."
            ),
            "metadata": None,
        }

        request = Request(
            f"http://{host}:{port}/v1/execute",
            data=json.dumps(
                request_payload
            ).encode("utf-8"),
            headers={
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

        assert response.status == 200

        assert payload["schema_version"] == "0.1"

        assert (
            payload["context"]
            == request_payload["context"]
        )

        assert payload["task_completed"] is True
        assert payload["output_text"] == (
            "DLLO-AGENT-SMOKE-001"
        )

        assert payload["retry_count"] == 0
        assert (
            payload["human_intervention_count"]
            == 0
        )
        assert payload["error_type"] is None

        assert payload["latency_ms"] >= 0
        assert payload["started_at_utc"]
        assert payload["finished_at_utc"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_reference_protocol_agent_passes_agent_protocol_v1():
    from datetime import datetime, timezone

    from observer.core.agent_lab_protocol_runner import (
        AgentLabProtocolRunner,
    )

    agent = ReferenceProtocolAgent()

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_reference_protocol_handler(agent),
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
        )

        result = runner.run(
            base_url=f"http://{host}:{port}",
            generated_at_utc=datetime.now(
                timezone.utc,
            ),
        )

        assert result.session.target.target_id == (
            "dllo-reference-protocol-agent"
        )

        assert result.session.suite_id == (
            "agent-protocol-core"
        )
        assert result.session.suite_version == "1.0"

        assert len(result.session.results) == 11

        assert all(
            task_result.evaluation.passed
            for task_result in result.session.results
        )

        assert result.report.total_tasks == 11
        assert result.report.passed_tasks == 11
        assert result.report.failed_tasks == 0
        assert result.report.pass_rate == 1.0
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
