import json
import threading
from datetime import datetime, timezone
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path

from observer.core.agent_technical_report import (
    build_agent_technical_report,
)
from observer.core.agent_test_session_runner import (
    AgentTestSessionRunner,
)
from observer.core.benchmark_task_assessment import (
    BenchmarkTaskAssessmentRunner,
)
from observer.core.benchmark_task_runner import (
    BenchmarkTaskRunner,
)
from observer.core.suite_bank import SuiteBank
from observer.core.suite_registry import SuiteRegistry
from observer.core.task_bank import TaskBank
from observer.core.task_evaluator import TaskEvaluator
from observer.core.task_evaluator_registry import (
    TaskEvaluatorRegistry,
)
from observer.sut.base import SUTExecutionResult
from observer.sut.local_http import LocalHTTPSUTAdapter
from schemas.agent_lab import AgentTestSessionStatus
from schemas.benchmark import (
    BenchmarkHarnessProfile,
    BenchmarkTask,
)
from schemas.evaluation import (
    TaskCriterionEvaluation,
    TaskEvaluation,
    TaskEvaluationMethod,
)


class CompletionEvaluator(TaskEvaluator):
    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence=None,
    ) -> TaskEvaluation:
        passed = result.task_completed

        return TaskEvaluation(
            task_id=benchmark.task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion=(
                        benchmark.success_criteria[0].description
                    ),
                    passed=passed,
                    evidence="Observed normalized SUT result.",
                ),
            ],
            passed=passed,
        )


def test_agent_lab_resolves_suite_and_runs_http_session(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    (suite_root / "agent-core.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "suite_id": "agent-core",
                "suite_version": "0.1",
                "family": "agent",
                "harness_profile": "sut_protocol",
                "task_ids": [
                    "agent-http-auto-001",
                ],
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    (task_root / "agent-http-auto-001.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "task_id": "agent-http-auto-001",
                "benchmark_version": "0.1",
                "evaluator_id": "completion-evaluator-v0-1",
                "family": "agent",
                "category": "technical",
                "difficulty": "easy",
                "task": "Complete the automatically selected task.",
                "required_capabilities": [
                    "text"
                ],
                "success_criteria": [
                    {
                        "criterion_id": "completed",
                        "description": "The task is completed."
                    }
                ],
                "enabled": True,
            }
        ),
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
                        "target_id": "auto-suite-agent",
                        "display_name": "Auto Suite Agent",
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
                    "latency_ms": 8.5,
                    "task_completed": True,
                    "output_text": "automatic suite task completed",
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

        suite_registry = SuiteRegistry(
            suite_bank=SuiteBank(suite_root),
            task_bank=TaskBank(task_root),
        )

        resolved = suite_registry.resolve_unique_for_target(
            adapter.manifest,
            harness_profile=BenchmarkHarnessProfile.SUT_PROTOCOL,
        )

        assert resolved.suite.suite_id == "agent-core"
        assert resolved.suite.suite_version == "0.1"
        assert [
            task.task_id
            for task in resolved.tasks
        ] == [
            "agent-http-auto-001",
        ]

        task_runner = BenchmarkTaskRunner(
            adapter,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )

        evaluator_registry = TaskEvaluatorRegistry()
        evaluator_registry.register(
            "completion-evaluator-v0-1",
            CompletionEvaluator(),
        )

        assessment_runner = BenchmarkTaskAssessmentRunner(
            task_runner=task_runner,
            registry=evaluator_registry,
        )

        session_runner = AgentTestSessionRunner(
            assessment_runner=assessment_runner,
        )

        session = session_runner.run(
            suite_id=resolved.suite.suite_id,
            suite_version=resolved.suite.suite_version,
            tasks=list(resolved.tasks),
        )

        assert session.status is AgentTestSessionStatus.COMPLETED
        assert session.target == adapter.manifest

        assert len(execute_requests) == 1
        assert (
            execute_requests[0]["context"]["task_id"]
            == "agent-http-auto-001"
        )

        assert len(session.results) == 1
        assert session.results[0].evaluation.passed is True

        report = build_agent_technical_report(
            session,
            generated_at_utc=datetime.now(timezone.utc),
        )

        assert report.target_id == "auto-suite-agent"
        assert report.suite_id == "agent-core"
        assert report.suite_version == "0.1"
        assert report.total_tasks == 1
        assert report.passed_tasks == 1
        assert report.pass_rate == 1.0

    finally:
        server.shutdown()
        server.server_close()
        thread.join()
