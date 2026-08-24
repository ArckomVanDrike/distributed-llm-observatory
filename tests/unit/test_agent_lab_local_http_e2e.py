import json
import threading
from datetime import datetime, timezone
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)

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
from observer.core.task_evaluator import TaskEvaluator
from observer.core.task_evaluator_registry import (
    TaskEvaluatorRegistry,
)
from observer.sut.base import SUTExecutionResult
from observer.sut.local_http import LocalHTTPSUTAdapter
from schemas.agent_lab import (
    AgentTestSessionStatus,
    AgentTestTaskSelectionStatus,
)
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkSuccessCriterion,
    BenchmarkTask,
)
from schemas.evaluation import (
    TaskCriterionEvaluation,
    TaskEvaluation,
    TaskEvaluationMethod,
)
from schemas.target import TargetCapability


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
                    evidence=(
                        "DLLO observed the normalized SUT "
                        "execution result."
                    ),
                ),
            ],
            passed=passed,
        )


def test_agent_lab_session_runs_end_to_end_through_local_http():
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
                        "target_id": "agent-lab-http-agent",
                        "display_name": "Agent Lab HTTP Agent",
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
                    "latency_ms": 12.5,
                    "task_completed": True,
                    "output_text": "remote task completed",
                    "retry_count": 1,
                    "human_intervention_count": 0,
                    "error_type": None,
                    "metrics": {
                        "steps": 2,
                        "tool_calls": 1,
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

        compatible_task = BenchmarkTask(
            task_id="agent-http-session-001",
            benchmark_version="0.1",
            evaluator_id="completion-evaluator-v0-1",
            family=BenchmarkFamily.AGENT,
            category=BenchmarkCategory.TECHNICAL,
            difficulty=BenchmarkDifficulty.EASY,
            task="Complete the remote Agent Lab task.",
            required_capabilities={
                TargetCapability.TEXT,
            },
            success_criteria=[
                BenchmarkSuccessCriterion(
                    criterion_id="completed",
                    description="The remote task is completed.",
                ),
            ],
        )

        incompatible_task = BenchmarkTask(
            task_id="agent-http-filesystem-001",
            benchmark_version="0.1",
            evaluator_id="completion-evaluator-v0-1",
            family=BenchmarkFamily.AGENT,
            category=BenchmarkCategory.TECHNICAL,
            difficulty=BenchmarkDifficulty.EASY,
            task="Write a file in the remote workspace.",
            required_capabilities={
                TargetCapability.TEXT,
                TargetCapability.FILESYSTEM,
            },
            success_criteria=[
                BenchmarkSuccessCriterion(
                    criterion_id="file-created",
                    description="The requested file exists.",
                ),
            ],
        )

        task_runner = BenchmarkTaskRunner(
            adapter,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )

        registry = TaskEvaluatorRegistry()
        registry.register(
            "completion-evaluator-v0-1",
            CompletionEvaluator(),
        )

        assessment_runner = BenchmarkTaskAssessmentRunner(
            task_runner=task_runner,
            registry=registry,
        )

        session_runner = AgentTestSessionRunner(
            assessment_runner=assessment_runner,
        )

        session = session_runner.run(
            suite_id="agent-http-core",
            suite_version="0.1",
            tasks=[
                compatible_task,
                incompatible_task,
            ],
        )

        assert session.status is AgentTestSessionStatus.COMPLETED

        assert session.target.target_id == (
            "agent-lab-http-agent"
        )
        assert session.target.capabilities == {
            TargetCapability.TEXT,
        }

        assert len(session.selections) == 2

        assert (
            session.selections[0].status
            is AgentTestTaskSelectionStatus.SELECTED
        )

        assert (
            session.selections[1].status
            is AgentTestTaskSelectionStatus.INCOMPATIBLE
        )
        assert session.selections[1].missing_capabilities == {
            TargetCapability.FILESYSTEM,
        }

        assert len(execute_requests) == 1
        assert (
            execute_requests[0]["context"]["task_id"]
            == compatible_task.task_id
        )

        assert len(session.results) == 1

        result = session.results[0]

        assert result.task_id == compatible_task.task_id
        assert result.task_completed is True
        assert result.evaluation.passed is True
        assert result.output_text == "remote task completed"
        assert result.latency_ms == 12.5
        assert result.retry_count == 1
        assert result.metrics == {
            "steps": 2,
            "tool_calls": 1,
        }

        serialized = json.loads(
            session.model_dump_json()
        )

        assert serialized["suite_id"] == "agent-http-core"
        assert (
            serialized["target"]["target_id"]
            == "agent-lab-http-agent"
        )
        assert len(serialized["results"]) == 1
        assert len(serialized["selections"]) == 2

        report = build_agent_technical_report(
            session,
            generated_at_utc=datetime.now(timezone.utc),
        )

        assert report.session_id == session.session_id
        assert report.target_id == "agent-lab-http-agent"
        assert report.suite_id == "agent-http-core"
        assert report.suite_version == "0.1"

        assert report.total_tasks == 1
        assert report.passed_tasks == 1
        assert report.failed_tasks == 0
        assert report.task_completion_rate == 1.0
        assert report.pass_rate == 1.0
        assert report.median_latency_ms == 12.5
        assert report.total_retries == 1
        assert report.total_human_interventions == 0

    finally:
        server.shutdown()
        server.server_close()
        thread.join()
