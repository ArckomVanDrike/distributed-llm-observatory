import json
import threading
from datetime import datetime, timezone
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)

from observer.core.benchmark_task_runner import BenchmarkTaskRunner
from observer.sut.local_http import LocalHTTPSUTAdapter
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkSuccessCriterion,
    BenchmarkTask,
)
from schemas.target import TargetCapability


def test_benchmark_task_runs_through_local_http_sut():
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
                        "target_id": "remote-test-agent",
                        "display_name": "Remote Test Agent",
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

            now = datetime.now(
                timezone.utc
            ).isoformat()

            payload = json.dumps(
                {
                    "schema_version": "0.1",
                    "context": request_payload["context"],
                    "started_at_utc": now,
                    "finished_at_utc": now,
                    "latency_ms": 4.2,
                    "task_completed": True,
                    "output_text": "completed",
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

        adapter = LocalHTTPSUTAdapter(
            f"http://{host}:{port}",
        )

        task = BenchmarkTask(
            task_id="agent-http-001",
            benchmark_version="0.1",
            evaluator_id="test-evaluator-v0-1",
            family=BenchmarkFamily.AGENT,
            category=BenchmarkCategory.TECHNICAL,
            difficulty=BenchmarkDifficulty.EASY,
            task="Complete the remote test task.",
            required_capabilities={
                TargetCapability.TEXT,
            },
            success_criteria=[
                BenchmarkSuccessCriterion(
                    criterion_id="completed",
                    description="The task is completed.",
                ),
            ],
        )

        runner = BenchmarkTaskRunner(
            adapter,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )

        run = runner.run(task)

        assert run.observation.context.target_id == "remote-test-agent"
        assert run.observation.request.task == (
            "Complete the remote test task."
        )
        assert run.observation.result.task_completed is True
        assert run.observation.result.output_text == "completed"
        assert run.observation.result.metrics["steps"] == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
