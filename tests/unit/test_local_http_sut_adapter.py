import pytest

from observer.sut.local_http import LocalHTTPSUTAdapter


@pytest.mark.parametrize(
    "base_url",
    [
        "http://example.com:8765",
        "https://example.com",
        "http://192.168.1.10:8765",
    ],
)
def test_local_http_sut_adapter_rejects_non_local_hosts(
    base_url: str,
):
    with pytest.raises(
        ValueError,
        match="localhost",
    ):
        LocalHTTPSUTAdapter(
            base_url,
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "http://127.0.0.1:8765",
        "http://localhost:8765",
        "http://[::1]:8765",
    ],
)
def test_local_http_sut_adapter_accepts_loopback_hosts(
    base_url: str,
):
    adapter = LocalHTTPSUTAdapter(
        base_url,
        load_manifest=False,
    )

    assert adapter.base_url == base_url.rstrip("/")


def test_local_http_sut_adapter_loads_manifest():
    import json
    import threading
    from http.server import (
        BaseHTTPRequestHandler,
        ThreadingHTTPServer,
    )

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
                        "target_id": "custom-agent",
                        "display_name": "Custom Agent",
                        "target_type": "agent",
                        "capabilities": [
                            "text",
                            "filesystem",
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

        adapter = LocalHTTPSUTAdapter(
            f"http://{host}:{port}",
        )

        assert adapter.manifest.target_id == "custom-agent"
        assert adapter.manifest.target_type.value == "agent"
        assert {
            capability.value
            for capability in adapter.manifest.capabilities
        } == {
            "text",
            "filesystem",
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_local_http_sut_adapter_executes_task():
    import json
    import threading
    from datetime import datetime, timezone
    from http.server import (
        BaseHTTPRequestHandler,
        ThreadingHTTPServer,
    )

    from observer.sut.base import (
        SUTExecutionContext,
        SUTRequest,
    )

    received = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            payload = json.dumps(
                {
                    "schema_version": "0.1",
                    "manifest": {
                        "schema_version": "0.1",
                        "target_id": "custom-agent",
                        "display_name": "Custom Agent",
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

            content_length = int(
                self.headers["Content-Length"]
            )

            request_payload = json.loads(
                self.rfile.read(
                    content_length
                ).decode("utf-8")
            )

            received.update(request_payload)

            now = datetime.now(
                timezone.utc
            ).isoformat()

            payload = json.dumps(
                {
                    "schema_version": "0.1",
                    "context": request_payload["context"],
                    "started_at_utc": now,
                    "finished_at_utc": now,
                    "latency_ms": 12.5,
                    "task_completed": True,
                    "output_text": "done",
                    "retry_count": 1,
                    "human_intervention_count": 0,
                    "error_type": None,
                    "metrics": {
                        "tool_calls": 2,
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

        adapter = LocalHTTPSUTAdapter(
            f"http://{host}:{port}",
        )

        context = SUTExecutionContext(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
            benchmark_version="0.1",
            task_id="agent-evidence-001",
            target_id="custom-agent",
        )

        result = adapter.execute(
            context,
            SUTRequest(
                task="Complete the task.",
                metadata={
                    "experiment_id": "exp-001",
                },
            ),
        )

        assert received["schema_version"] == "0.1"
        assert received["task"] == "Complete the task."
        assert received["metadata"] == {
            "experiment_id": "exp-001",
        }

        assert result.context == context
        assert result.task_completed is True
        assert result.output_text == "done"
        assert result.retry_count == 1
        assert result.metrics["tool_calls"] == 2
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_local_http_sut_adapter_rejects_redirects():
    import threading
    from http.server import (
        BaseHTTPRequestHandler,
        ThreadingHTTPServer,
    )

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header(
                "Location",
                "http://example.com/v1/manifest",
            )
            self.end_headers()

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

        with pytest.raises(
            ValueError,
            match="redirect",
        ):
            LocalHTTPSUTAdapter(
                f"http://{host}:{port}",
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
