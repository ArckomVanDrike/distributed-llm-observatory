import json
import threading
from datetime import datetime, timezone
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path

import pytest

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
from observer.core.default_task_evaluator_registry import (
    build_default_task_evaluator_registry,
)
from observer.core.suite_bank import SuiteBank
from observer.core.suite_registry import SuiteRegistry
from observer.core.task_bank import TaskBank
from observer.sut.local_http import LocalHTTPSUTAdapter
from schemas.agent_lab import AgentTestSessionStatus
from schemas.benchmark import BenchmarkHarnessProfile

EXPECTED_OUTPUT = "DLLO-AGENT-SMOKE-001"
INSTRUCTION_EXPECTED_OUTPUT = "alpha,bravo,charlie,delta"
STRUCTURED_EXPECTED_OUTPUT = '{"name":"delta","count":4,"active":true}'


@pytest.mark.parametrize(
    (
        "sut_task_completed",
        "sut_output_text",
        "expected_pass",
    ),
    [
        (
            False,
            EXPECTED_OUTPUT,
            True,
        ),
        (
            True,
            "WRONG-OUTPUT",
            False,
        ),
    ],
)
def test_agent_lab_resolves_canonical_protocol_suite_and_runs_http_session(
    sut_task_completed: bool,
    sut_output_text: str,
    expected_pass: bool,
):
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

                    # DLLO must evaluate observed output
                    # independently of SUT self-reporting.
                    "task_completed": sut_task_completed,
                    "output_text": (
                            {
                                "agent-protocol-smoke-001": EXPECTED_OUTPUT,
                                "agent-protocol-instruction-001": (
                                    INSTRUCTION_EXPECTED_OUTPUT
                                ),
                                "agent-protocol-structured-output-001": (
                                    STRUCTURED_EXPECTED_OUTPUT
                                ),
                            }[
                                request_payload["context"]["task_id"]
                            ]
                            if expected_pass
                            else sut_output_text
                        ),
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
            suite_bank=SuiteBank(
                Path("benchmark/suites"),
            ),
            task_bank=TaskBank(
                Path("benchmark/tasks"),
            ),
        )

        resolved = suite_registry.resolve_unique_for_target(
            adapter.manifest,
            harness_profile=BenchmarkHarnessProfile.SUT_PROTOCOL,
        )

        assert resolved.suite.suite_id == "agent-protocol-core"
        assert resolved.suite.suite_version == "0.10"
        assert (
            resolved.suite.harness_profile
            is BenchmarkHarnessProfile.SUT_PROTOCOL
        )

        assert [
            task.task_id
            for task in resolved.tasks
        ] == [
            "agent-protocol-smoke-001",
            "agent-protocol-instruction-001",
            "agent-protocol-structured-output-001",
            "agent-protocol-action-001",
            "agent-protocol-tool-selection-001",
            "agent-protocol-action-sequence-001",
            "agent-protocol-data-flow-001",
            "agent-protocol-recovery-001",
            "agent-protocol-branch-001",
            "agent-protocol-multi-branch-001",
            "agent-protocol-multi-branch-002",
        ]

        task_runner = BenchmarkTaskRunner(
            adapter,
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        )

        assessment_runner = BenchmarkTaskAssessmentRunner(
            task_runner=task_runner,
            registry=build_default_task_evaluator_registry(),
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

        assert [
            request["context"]["task_id"]
            for request in execute_requests
        ] == [
            "agent-protocol-smoke-001",
            "agent-protocol-instruction-001",
            "agent-protocol-structured-output-001",
        ]

        assert (
            execute_requests[0]["task"]
            == (
                "Return exactly DLLO-AGENT-SMOKE-001 "
                "and no additional characters."
            )
        )

        assert len(session.results) == 3

        action_selection = next(
            selection
            for selection in session.selections
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

        tool_selection = next(
            selection
            for selection in session.selections
            if (
                selection.task_id
                == "agent-protocol-tool-selection-001"
            )
        )

        assert (
            tool_selection.status.value
            == "incompatible"
        )
        assert {
            capability.value
            for capability
            in tool_selection.missing_capabilities
        } == {
            "tools",
        }

        sequence_selection = next(
            selection
            for selection in session.selections
            if (
                selection.task_id
                == "agent-protocol-action-sequence-001"
            )
        )

        assert (
            sequence_selection.status.value
            == "incompatible"
        )
        assert {
            capability.value
            for capability
            in sequence_selection.missing_capabilities
        } == {
            "tools",
        }

        data_flow_selection = next(
            selection
            for selection in session.selections
            if (
                selection.task_id
                == "agent-protocol-data-flow-001"
            )
        )

        assert (
            data_flow_selection.status.value
            == "incompatible"
        )
        assert {
            capability.value
            for capability
            in data_flow_selection.missing_capabilities
        } == {
            "tools",
        }

        recovery_selection = next(
            selection
            for selection in session.selections
            if (
                selection.task_id
                == "agent-protocol-recovery-001"
            )
        )

        assert (
            recovery_selection.status.value
            == "incompatible"
        )
        assert {
            capability.value
            for capability
            in recovery_selection.missing_capabilities
        } == {
            "tools",
        }

        branch_selection = next(
            selection
            for selection in session.selections
            if (
                selection.task_id
                == "agent-protocol-branch-001"
            )
        )

        assert (
            branch_selection.status.value
            == "incompatible"
        )
        assert {
            capability.value
            for capability
            in branch_selection.missing_capabilities
        } == {
            "tools",
        }


        multi_branch_selections = [
            selection
            for selection in session.selections
            if selection.task_id in {
                "agent-protocol-multi-branch-001",
                "agent-protocol-multi-branch-002",
            }
        ]

        assert len(multi_branch_selections) == 2

        for selection in multi_branch_selections:
            assert (
                selection.status.value
                == "incompatible"
            )
            assert {
                capability.value
                for capability
                in selection.missing_capabilities
            } == {
                "tools",
            }

        for result in session.results:
            assert result.task_completed is sut_task_completed

            # DLLO's verdict follows independently observed output,
            # not the SUT's task_completed self-report.
            assert result.evaluation.passed is expected_pass
            assert (
                result.evaluation.criteria[0].passed
                is expected_pass
            )

        report = build_agent_technical_report(
            session,
            generated_at_utc=datetime.now(timezone.utc),
        )

        assert report.target_id == "auto-suite-agent"
        assert report.suite_id == "agent-protocol-core"
        assert report.suite_version == "0.10"
        assert report.total_tasks == 3
        assert report.passed_tasks == 3 * int(expected_pass)
        assert report.pass_rate == float(expected_pass)

    finally:
        server.shutdown()
        server.server_close()
        thread.join()
