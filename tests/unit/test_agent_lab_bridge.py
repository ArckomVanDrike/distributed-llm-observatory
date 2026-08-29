from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID

import pytest

from observer.agent_lab_bridge import (
    AgentLabBridgeConfig,
    make_handler,
    serve,
)
from observer.core.agent_lab_artifact_io import (
    load_agent_lab_run_artifact,
    write_agent_lab_run_artifact,
)
from observer.core.agent_lab_protocol_runner import (
    AgentLabProtocolRun,
    AgentLabProtocolRunnerError,
)
from schemas.agent_lab import (
    AgentTechnicalReport,
    AgentTestSession,
    AgentTestSessionStatus,
)
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


def make_config(
    tmp_path: Path,
) -> AgentLabBridgeConfig:
    return AgentLabBridgeConfig(
        observer_id="observer-test",
        region_code="CL-LL",
        history_root=tmp_path / "history",
    )


def run_test_server(
    config: AgentLabBridgeConfig,
):
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_handler(config),
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    return server, thread


def test_agent_lab_bridge_health(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with urlopen(
            f"http://{host}:{port}/health",
            timeout=2,
        ) as response:
            body = response.read().decode("utf-8")

        assert response.status == 200
        assert '"status": "ok"' in body
        assert (
            '"service": "dllo-agent-lab-bridge"'
            in body
        )

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_rejects_non_local_bind(
    tmp_path: Path,
):
    config = make_config(tmp_path)

    with pytest.raises(
        ValueError,
        match="localhost",
    ):
        serve(
            config,
            host="0.0.0.0",
            port=8766,
        )



def build_protocol_run() -> AgentLabProtocolRun:
    now = datetime(
        2026,
        8,
        26,
        19,
        45,
        tzinfo=timezone.utc,
    )

    session = AgentTestSession(
        observer_id="observer-test",
        region_code="CL-LL",
        target=TargetManifest(
            target_id="bridge-agent",
            display_name="Bridge Agent",
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        ),
        suite_id="agent-protocol-core",
        suite_version="1.0",
        status=AgentTestSessionStatus.COMPLETED,
        started_at_utc=now,
        completed_at_utc=now,
        selections=[],
        results=[],
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
        total_retries=0,
        total_human_interventions=0,
        findings=[
            "No benchmark task results are present."
        ],
        recommendations=[
            "Run compatible benchmark tasks."
        ],
    )

    return AgentLabProtocolRun(
        session=session,
        report=report,
    )


def test_agent_lab_bridge_runs_and_persists_test(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    protocol_run = build_protocol_run()
    runner_calls = []

    class FakeRunner:
        def run(
            self,
            *,
            base_url: str,
            generated_at_utc: datetime,
        ) -> AgentLabProtocolRun:
            runner_calls.append(
                {
                    "base_url": base_url,
                    "generated_at_utc": generated_at_utc,
                }
            )
            return protocol_run

    def runner_factory(
        received_config: AgentLabBridgeConfig,
    ):
        assert received_config is config
        return FakeRunner()

    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_handler(
            config,
            runner_factory=runner_factory,
        ),
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        request = Request(
            f"http://{host}:{port}/v1/agent-tests",
            data=json.dumps(
                {
                    "base_url":
                        "http://127.0.0.1:8000",
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
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

        assert response.status == 201
        assert payload["schema_version"] == "0.1"
        assert payload["status"] == "completed"

        assert payload["session_id"] == str(
            protocol_run.session.session_id
        )
        assert payload["target_id"] == "bridge-agent"
        assert payload["suite_id"] == "agent-protocol-core"
        assert payload["suite_version"] == "1.0"

        assert payload["observer_id"] == "observer-test"
        assert payload["region_code"] == "CL-LL"

        assert payload["observatory"] == {
            "provenance_complete": True,
            "temporal_eligible": True,
            "geographic_eligible": True,
            "reasons": [],
        }

        assert payload["total_tasks"] == 0
        assert payload["passed_tasks"] == 0
        assert payload["failed_tasks"] == 0
        assert payload["pass_rate"] is None
        assert payload["median_latency_ms"] is None

        assert payload["findings"] == [
            "No benchmark task results are present."
        ]
        assert payload["recommendations"] == [
            "Run compatible benchmark tasks."
        ]

        assert len(runner_calls) == 1
        assert runner_calls[0]["base_url"] == (
            "http://127.0.0.1:8000"
        )
        assert (
            runner_calls[0]["generated_at_utc"].tzinfo
            is not None
        )

        artifact_path = (
            config.history_root
            / f"{protocol_run.session.session_id}.json"
        )

        assert artifact_path.is_file()

        persisted = load_agent_lab_run_artifact(
            artifact_path
        )

        assert persisted == protocol_run.to_artifact()

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)



def test_agent_lab_bridge_rejects_invalid_json(
    tmp_path: Path,
):
    config = make_config(tmp_path)

    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_handler(config),
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        request = Request(
            f"http://{host}:{port}/v1/agent-tests",
            data=b"{not-json",
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with pytest.raises(HTTPError) as error:
            urlopen(
                request,
                timeout=2,
            )

        assert error.value.code == 400

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload == {
            "error": "bad_request",
            "message": "Invalid JSON request body.",
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_requires_base_url(
    tmp_path: Path,
):
    config = make_config(tmp_path)

    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_handler(config),
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        request = Request(
            f"http://{host}:{port}/v1/agent-tests",
            data=json.dumps({}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with pytest.raises(HTTPError) as error:
            urlopen(
                request,
                timeout=2,
            )

        assert error.value.code == 400

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload == {
            "error": "bad_request",
            "message": "base_url is required.",
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_reports_runner_failure(
    tmp_path: Path,
):
    config = make_config(tmp_path)

    class FailingRunner:
        def run(
            self,
            *,
            base_url: str,
            generated_at_utc: datetime,
        ):
            raise AgentLabProtocolRunnerError(
                "Unable to load agent manifest."
            )

    def runner_factory(
        _config: AgentLabBridgeConfig,
    ):
        return FailingRunner()

    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_handler(
            config,
            runner_factory=runner_factory,
        ),
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        request = Request(
            f"http://{host}:{port}/v1/agent-tests",
            data=json.dumps(
                {
                    "base_url":
                        "http://127.0.0.1:8000",
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with pytest.raises(HTTPError) as error:
            urlopen(
                request,
                timeout=2,
            )

        assert error.value.code == 500

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload == {
            "error": "agent_test_failed",
            "message": "Unable to load agent manifest.",
        }

        assert not config.history_root.exists()

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_lists_persisted_tests(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    protocol_run = build_protocol_run()
    artifact = protocol_run.to_artifact()

    config.history_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_agent_lab_run_artifact(
        artifact,
        config.history_root
        / f"{artifact.session.session_id}.json",
    )

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with urlopen(
            f"http://{host}:{port}/v1/agent-tests",
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        assert response.status == 200
        assert payload["schema_version"] == "0.1"

        assert len(payload["runs"]) == 1

        run = payload["runs"][0]

        assert run["session_id"] == str(
            artifact.session.session_id
        )
        assert run["started_at_utc"] == (
            artifact.session.started_at_utc.isoformat()
        )
        assert run["target_id"] == "bridge-agent"
        assert run["suite_id"] == "agent-protocol-core"
        assert run["suite_version"] == "1.0"

        assert run["observer_id"] == "observer-test"
        assert run["region_code"] == "CL-LL"

        assert run["total_tasks"] == 0
        assert run["passed_tasks"] == 0
        assert run["failed_tasks"] == 0
        assert run["pass_rate"] is None
        assert run["median_latency_ms"] is None

        assert run["observatory"] == {
            "provenance_complete": True,
            "temporal_eligible": True,
            "geographic_eligible": True,
            "reasons": [],
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_lists_empty_history(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with urlopen(
            f"http://{host}:{port}/v1/agent-tests",
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        assert response.status == 200
        assert payload == {
            "schema_version": "0.1",
            "runs": [],
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_lists_tests_in_canonical_history_order(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    template = build_protocol_run().to_artifact()

    earlier = datetime(
        2026,
        8,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )
    later = datetime(
        2026,
        8,
        26,
        19,
        0,
        tzinfo=timezone.utc,
    )

    earlier_id = UUID(
        "00000000-0000-0000-0000-000000000101"
    )
    later_id = UUID(
        "00000000-0000-0000-0000-000000000102"
    )

    earlier_artifact = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": earlier_id,
                    "started_at_utc": earlier,
                    "completed_at_utc": earlier,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": earlier_id,
                        "generated_at_utc": earlier,
                    },
                )
            ),
        },
    )

    later_artifact = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": later_id,
                    "started_at_utc": later,
                    "completed_at_utc": later,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": later_id,
                        "generated_at_utc": later,
                    },
                )
            ),
        },
    )

    config.history_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Deliberately reverse filesystem/name order.
    write_agent_lab_run_artifact(
        later_artifact,
        config.history_root / "a-later.json",
    )
    write_agent_lab_run_artifact(
        earlier_artifact,
        config.history_root / "z-earlier.json",
    )

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with urlopen(
            f"http://{host}:{port}/v1/agent-tests",
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        assert response.status == 200

        assert [
            run["session_id"]
            for run in payload["runs"]
        ] == [
            str(earlier_id),
            str(later_id),
        ]

        assert [
            run["started_at_utc"]
            for run in payload["runs"]
        ] == [
            earlier.isoformat(),
            later.isoformat(),
        ]

        assert "latest" not in payload
        assert "baseline" not in payload
        assert "candidate" not in payload

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_compares_selected_temporal_runs(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    template = build_protocol_run().to_artifact()

    baseline_time = datetime(
        2026,
        8,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )
    candidate_time = datetime(
        2026,
        8,
        26,
        19,
        0,
        tzinfo=timezone.utc,
    )

    baseline_id = UUID(
        "00000000-0000-0000-0000-000000000201"
    )
    candidate_id = UUID(
        "00000000-0000-0000-0000-000000000202"
    )

    baseline = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": baseline_id,
                    "started_at_utc": baseline_time,
                    "completed_at_utc": baseline_time,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": baseline_id,
                        "generated_at_utc": baseline_time,
                    },
                )
            ),
        },
    )

    candidate = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": candidate_id,
                    "started_at_utc": candidate_time,
                    "completed_at_utc": candidate_time,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": candidate_id,
                        "generated_at_utc": candidate_time,
                    },
                )
            ),
        },
    )

    config.history_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_agent_lab_run_artifact(
        baseline,
        config.history_root / "baseline.json",
    )
    write_agent_lab_run_artifact(
        candidate,
        config.history_root / "candidate.json",
    )

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        request = Request(
            (
                f"http://{host}:{port}"
                "/v1/agent-comparisons/temporal"
            ),
            data=json.dumps(
                {
                    "baseline_session_id": str(
                        baseline_id
                    ),
                    "candidate_session_id": str(
                        candidate_id
                    ),
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
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
        assert payload["comparison_type"] == "temporal"

        assert payload["baseline_session_id"] == str(
            baseline_id
        )
        assert payload["candidate_session_id"] == str(
            candidate_id
        )

        assert payload["observer_id"] == "observer-test"
        assert payload["region_code"] == "CL-LL"

        assert payload["baseline_started_at_utc"] == (
            baseline_time.isoformat()
        )
        assert payload["candidate_started_at_utc"] == (
            candidate_time.isoformat()
        )

        assert payload["changes"] == {
            "total_tasks": 0,
            "regressions": 0,
            "improvements": 0,
            "unchanged": 0,
            "pass_rate_delta": None,
            "median_latency_ms_delta": None,
            "retry_delta": 0,
            "human_intervention_delta": 0,
            "task_changes": [],
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_keeps_explicit_temporal_roles_when_rejected(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    template = build_protocol_run().to_artifact()

    baseline_id = UUID(
        "00000000-0000-0000-0000-000000000211"
    )
    candidate_id = UUID(
        "00000000-0000-0000-0000-000000000212"
    )

    baseline = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": baseline_id,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": baseline_id,
                    },
                )
            ),
        },
    )

    candidate = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": candidate_id,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": candidate_id,
                    },
                )
            ),
        },
    )

    config.history_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_agent_lab_run_artifact(
        baseline,
        config.history_root / "baseline.json",
    )
    write_agent_lab_run_artifact(
        candidate,
        config.history_root / "candidate.json",
    )

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        request = Request(
            (
                f"http://{host}:{port}"
                "/v1/agent-comparisons/temporal"
            ),
            data=json.dumps(
                {
                    "baseline_session_id": str(
                        baseline_id
                    ),
                    "candidate_session_id": str(
                        candidate_id
                    ),
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with pytest.raises(HTTPError) as error:
            urlopen(
                request,
                timeout=2,
            )

        assert error.value.code == 422

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload == {
            "error": "comparison_rejected",
            "message": (
                "Temporal comparison requires the "
                "candidate observation to occur after "
                "the baseline."
            ),
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_compares_selected_geographic_runs(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    template = build_protocol_run().to_artifact()

    baseline_time = datetime(
        2026,
        8,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )
    candidate_time = datetime(
        2026,
        8,
        26,
        18,
        5,
        tzinfo=timezone.utc,
    )

    baseline_id = UUID(
        "00000000-0000-0000-0000-000000000301"
    )
    candidate_id = UUID(
        "00000000-0000-0000-0000-000000000302"
    )

    baseline = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": baseline_id,
                    "observer_id": "observer-los-lagos",
                    "region_code": "CL-Los-Lagos",
                    "started_at_utc": baseline_time,
                    "completed_at_utc": baseline_time,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": baseline_id,
                        "generated_at_utc": baseline_time,
                    },
                )
            ),
        },
    )

    candidate = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": candidate_id,
                    "observer_id": "observer-aysen",
                    "region_code": "CL-Aysen",
                    "started_at_utc": candidate_time,
                    "completed_at_utc": candidate_time,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": candidate_id,
                        "generated_at_utc": candidate_time,
                    },
                )
            ),
        },
    )

    config.history_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_agent_lab_run_artifact(
        baseline,
        config.history_root / "baseline.json",
    )
    write_agent_lab_run_artifact(
        candidate,
        config.history_root / "candidate.json",
    )

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        request = Request(
            (
                f"http://{host}:{port}"
                "/v1/agent-comparisons/geographic"
            ),
            data=json.dumps(
                {
                    "baseline_session_id": str(
                        baseline_id
                    ),
                    "candidate_session_id": str(
                        candidate_id
                    ),
                    "max_observation_skew_seconds": 600,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
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
        assert payload["comparison_type"] == "geographic"

        assert payload["baseline_session_id"] == str(
            baseline_id
        )
        assert payload["candidate_session_id"] == str(
            candidate_id
        )

        assert payload["baseline_observer_id"] == (
            "observer-los-lagos"
        )
        assert payload["candidate_observer_id"] == (
            "observer-aysen"
        )

        assert payload["baseline_region_code"] == (
            "CL-Los-Lagos"
        )
        assert payload["candidate_region_code"] == (
            "CL-Aysen"
        )

        assert payload["baseline_started_at_utc"] == (
            baseline_time.isoformat()
        )
        assert payload["candidate_started_at_utc"] == (
            candidate_time.isoformat()
        )

        assert payload["observation_skew_seconds"] == 300
        assert payload["max_observation_skew_seconds"] == 600

        assert payload["changes"] == {
            "total_tasks": 0,
            "regressions": 0,
            "improvements": 0,
            "unchanged": 0,
            "pass_rate_delta": None,
            "median_latency_ms_delta": None,
            "retry_delta": 0,
            "human_intervention_delta": 0,
            "task_changes": [],
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_requires_explicit_geographic_max_skew(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        request = Request(
            (
                f"http://{host}:{port}"
                "/v1/agent-comparisons/geographic"
            ),
            data=json.dumps(
                {
                    "baseline_session_id": (
                        "00000000-0000-0000-0000-000000000311"
                    ),
                    "candidate_session_id": (
                        "00000000-0000-0000-0000-000000000312"
                    ),
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with pytest.raises(HTTPError) as error:
            urlopen(
                request,
                timeout=2,
            )

        assert error.value.code == 400

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload == {
            "error": "bad_request",
            "message": (
                "max_observation_skew_seconds "
                "is required."
            ),
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_accepts_zero_geographic_max_skew(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    template = build_protocol_run().to_artifact()

    observed_at = datetime(
        2026,
        8,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )

    baseline_id = UUID(
        "00000000-0000-0000-0000-000000000321"
    )
    candidate_id = UUID(
        "00000000-0000-0000-0000-000000000322"
    )

    baseline = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": baseline_id,
                    "observer_id": "observer-los-lagos",
                    "region_code": "CL-Los-Lagos",
                    "started_at_utc": observed_at,
                    "completed_at_utc": observed_at,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": baseline_id,
                        "generated_at_utc": observed_at,
                    },
                )
            ),
        },
    )

    candidate = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": candidate_id,
                    "observer_id": "observer-aysen",
                    "region_code": "CL-Aysen",
                    "started_at_utc": observed_at,
                    "completed_at_utc": observed_at,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": candidate_id,
                        "generated_at_utc": observed_at,
                    },
                )
            ),
        },
    )

    config.history_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_agent_lab_run_artifact(
        baseline,
        config.history_root / "baseline.json",
    )
    write_agent_lab_run_artifact(
        candidate,
        config.history_root / "candidate.json",
    )

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        request = Request(
            (
                f"http://{host}:{port}"
                "/v1/agent-comparisons/geographic"
            ),
            data=json.dumps(
                {
                    "baseline_session_id": str(
                        baseline_id
                    ),
                    "candidate_session_id": str(
                        candidate_id
                    ),
                    "max_observation_skew_seconds": 0,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
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
        assert payload["comparison_type"] == "geographic"
        assert payload["observation_skew_seconds"] == 0
        assert payload["max_observation_skew_seconds"] == 0

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_rejects_negative_geographic_max_skew(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    template = build_protocol_run().to_artifact()

    observed_at = datetime(
        2026,
        8,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )

    baseline_id = UUID(
        "00000000-0000-0000-0000-000000000331"
    )
    candidate_id = UUID(
        "00000000-0000-0000-0000-000000000332"
    )

    baseline = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": baseline_id,
                    "observer_id": "observer-los-lagos",
                    "region_code": "CL-Los-Lagos",
                    "started_at_utc": observed_at,
                    "completed_at_utc": observed_at,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": baseline_id,
                        "generated_at_utc": observed_at,
                    },
                )
            ),
        },
    )

    candidate = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": candidate_id,
                    "observer_id": "observer-aysen",
                    "region_code": "CL-Aysen",
                    "started_at_utc": observed_at,
                    "completed_at_utc": observed_at,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": candidate_id,
                        "generated_at_utc": observed_at,
                    },
                )
            ),
        },
    )

    config.history_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_agent_lab_run_artifact(
        baseline,
        config.history_root / "baseline.json",
    )
    write_agent_lab_run_artifact(
        candidate,
        config.history_root / "candidate.json",
    )

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        request = Request(
            (
                f"http://{host}:{port}"
                "/v1/agent-comparisons/geographic"
            ),
            data=json.dumps(
                {
                    "baseline_session_id": str(
                        baseline_id
                    ),
                    "candidate_session_id": str(
                        candidate_id
                    ),
                    "max_observation_skew_seconds": -1,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with pytest.raises(HTTPError) as error:
            urlopen(
                request,
                timeout=2,
            )

        assert error.value.code == 422

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload == {
            "error": "comparison_rejected",
            "message": (
                "max_observation_skew cannot be negative."
            ),
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

def test_agent_lab_bridge_lists_temporal_observation_pairs(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    template = build_protocol_run().to_artifact()

    baseline_time = datetime(
        2026,
        8,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )
    candidate_time = datetime(
        2026,
        8,
        26,
        19,
        0,
        tzinfo=timezone.utc,
    )

    baseline_id = UUID(
        "00000000-0000-0000-0000-000000000301"
    )
    candidate_id = UUID(
        "00000000-0000-0000-0000-000000000302"
    )

    baseline = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": baseline_id,
                    "started_at_utc": baseline_time,
                    "completed_at_utc": baseline_time,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": baseline_id,
                        "generated_at_utc": baseline_time,
                    },
                )
            ),
        },
    )

    candidate = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": candidate_id,
                    "started_at_utc": candidate_time,
                    "completed_at_utc": candidate_time,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": candidate_id,
                        "generated_at_utc": candidate_time,
                    },
                )
            ),
        },
    )

    config.history_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Deliberately reverse filesystem/name order.
    write_agent_lab_run_artifact(
        candidate,
        config.history_root / "a-candidate.json",
    )
    write_agent_lab_run_artifact(
        baseline,
        config.history_root / "z-baseline.json",
    )

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with urlopen(
            (
                f"http://{host}:{port}"
                "/v1/agent-observation-pairs/temporal"
            ),
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        assert response.status == 200
        assert payload["schema_version"] == "0.1"
        assert payload["pair_type"] == "temporal"

        assert payload["pairs"] == [
            {
                "baseline_session_id": str(
                    baseline_id
                ),
                "candidate_session_id": str(
                    candidate_id
                ),
                "baseline_started_at_utc": (
                    baseline_time.isoformat()
                ),
                "candidate_started_at_utc": (
                    candidate_time.isoformat()
                ),
                "baseline_observer_id": (
                    "observer-test"
                ),
                "candidate_observer_id": (
                    "observer-test"
                ),
                "baseline_region_code": "CL-LL",
                "candidate_region_code": "CL-LL",
                "comparable": True,
                "reasons": [],
            }
        ]

        assert "latest" not in payload
        assert "baseline" not in payload
        assert "candidate" not in payload

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

def test_agent_lab_bridge_lists_geographic_observation_pairs(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    template = build_protocol_run().to_artifact()

    baseline_time = datetime(
        2026,
        8,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )
    candidate_time = datetime(
        2026,
        8,
        26,
        18,
        5,
        tzinfo=timezone.utc,
    )

    baseline_id = UUID(
        "00000000-0000-0000-0000-000000000401"
    )
    candidate_id = UUID(
        "00000000-0000-0000-0000-000000000402"
    )

    baseline = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": baseline_id,
                    "observer_id": "observer-los-lagos",
                    "region_code": "CL-Los-Lagos",
                    "started_at_utc": baseline_time,
                    "completed_at_utc": baseline_time,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": baseline_id,
                        "generated_at_utc": baseline_time,
                    },
                )
            ),
        },
    )

    candidate = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": candidate_id,
                    "observer_id": "observer-aysen",
                    "region_code": "CL-Aysen",
                    "started_at_utc": candidate_time,
                    "completed_at_utc": candidate_time,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": candidate_id,
                        "generated_at_utc": candidate_time,
                    },
                )
            ),
        },
    )

    config.history_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_agent_lab_run_artifact(
        candidate,
        config.history_root / "a-candidate.json",
    )
    write_agent_lab_run_artifact(
        baseline,
        config.history_root / "z-baseline.json",
    )

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with urlopen(
            (
                f"http://{host}:{port}"
                "/v1/agent-observation-pairs/geographic"
                "?max_observation_skew_seconds=600"
            ),
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        assert response.status == 200
        assert payload["schema_version"] == "0.1"
        assert payload["pair_type"] == "geographic"
        assert payload[
            "max_observation_skew_seconds"
        ] == 600

        assert payload["pairs"] == [
            {
                "baseline_session_id": str(
                    baseline_id
                ),
                "candidate_session_id": str(
                    candidate_id
                ),
                "baseline_started_at_utc": (
                    baseline_time.isoformat()
                ),
                "candidate_started_at_utc": (
                    candidate_time.isoformat()
                ),
                "baseline_observer_id": (
                    "observer-los-lagos"
                ),
                "candidate_observer_id": (
                    "observer-aysen"
                ),
                "baseline_region_code": (
                    "CL-Los-Lagos"
                ),
                "candidate_region_code": (
                    "CL-Aysen"
                ),
                "comparable": True,
                "reasons": [],
            }
        ]

        assert "latest" not in payload
        assert "baseline" not in payload
        assert "candidate" not in payload

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)



def test_agent_lab_bridge_requires_geographic_pair_max_skew(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with pytest.raises(HTTPError) as error:
            urlopen(
                (
                    f"http://{host}:{port}"
                    "/v1/agent-observation-pairs/geographic"
                ),
                timeout=2,
            )

        assert error.value.code == 400

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload == {
            "error": "bad_request",
            "message": (
                "max_observation_skew_seconds "
                "is required."
            ),
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_rejects_empty_geographic_pair_max_skew(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with pytest.raises(HTTPError) as error:
            urlopen(
                (
                    f"http://{host}:{port}"
                    "/v1/agent-observation-pairs/geographic"
                    "?max_observation_skew_seconds="
                ),
                timeout=2,
            )

        assert error.value.code == 400

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload == {
            "error": "bad_request",
            "message": (
                "max_observation_skew_seconds "
                "is required."
            ),
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_rejects_invalid_geographic_pair_max_skew(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with pytest.raises(HTTPError) as error:
            urlopen(
                (
                    f"http://{host}:{port}"
                    "/v1/agent-observation-pairs/geographic"
                    "?max_observation_skew_seconds=banana"
                ),
                timeout=2,
            )

        assert error.value.code == 400

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload == {
            "error": "bad_request",
            "message": (
                "max_observation_skew_seconds "
                "must be a number."
            ),
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_rejects_negative_geographic_pair_max_skew(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with pytest.raises(HTTPError) as error:
            urlopen(
                (
                    f"http://{host}:{port}"
                    "/v1/agent-observation-pairs/geographic"
                    "?max_observation_skew_seconds=-1"
                ),
                timeout=2,
            )

        assert error.value.code == 422

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload == {
            "error": "comparison_rejected",
            "message": (
                "max_observation_skew cannot be negative."
            ),
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_accepts_zero_geographic_pair_max_skew(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    template = build_protocol_run().to_artifact()

    observed_at = datetime(
        2026,
        8,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )

    baseline_id = UUID(
        "00000000-0000-0000-0000-000000000411"
    )
    candidate_id = UUID(
        "00000000-0000-0000-0000-000000000412"
    )

    baseline = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": baseline_id,
                    "observer_id": "observer-los-lagos",
                    "region_code": "CL-Los-Lagos",
                    "started_at_utc": observed_at,
                    "completed_at_utc": observed_at,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": baseline_id,
                        "generated_at_utc": observed_at,
                    },
                )
            ),
        },
    )

    candidate = template.model_copy(
        update={
            "session": template.session.model_copy(
                update={
                    "session_id": candidate_id,
                    "observer_id": "observer-aysen",
                    "region_code": "CL-Aysen",
                    "started_at_utc": observed_at,
                    "completed_at_utc": observed_at,
                },
            ),
            "technical_report": (
                template.technical_report.model_copy(
                    update={
                        "session_id": candidate_id,
                        "generated_at_utc": observed_at,
                    },
                )
            ),
        },
    )

    config.history_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_agent_lab_run_artifact(
        baseline,
        config.history_root / "baseline.json",
    )
    write_agent_lab_run_artifact(
        candidate,
        config.history_root / "candidate.json",
    )

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        with urlopen(
            (
                f"http://{host}:{port}"
                "/v1/agent-observation-pairs/geographic"
                "?max_observation_skew_seconds=0"
            ),
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        assert response.status == 200
        assert payload["schema_version"] == "0.1"
        assert payload["pair_type"] == "geographic"
        assert payload[
            "max_observation_skew_seconds"
        ] == 0

        assert len(payload["pairs"]) == 1

        pair = payload["pairs"][0]

        assert pair["baseline_session_id"] == str(
            baseline_id
        )
        assert pair["candidate_session_id"] == str(
            candidate_id
        )
        assert pair["comparable"] is True
        assert pair["reasons"] == []

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_returns_coding_starter_questions(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        request = Request(
            (
                f"http://{host}:{port}"
                "/v1/agent-starter/questions"
            ),
            data=json.dumps(
                {
                    "goal": "coding",
                    "evidence": [],
                    "hardware_profile": None,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
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
        assert payload["goal"] == "coding"

        assert [
            question["key"]
            for question in payload["questions"]
        ] == [
            "offline_required",
            "free_components_only",
            "paid_external_services_allowed",
            "source_code_must_stay_local",
            "prefer_local_execution",
            "modify_files",
            "run_tests",
        ]

        assert all(
            question["kind"] == "boolean"
            for question in payload["questions"]
        )

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_omits_answered_starter_question(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        request = Request(
            (
                f"http://{host}:{port}"
                "/v1/agent-starter/questions"
            ),
            data=json.dumps(
                {
                    "goal": "coding",
                    "evidence": [
                        {
                            "key": "offline_required",
                            "source": "declared",
                            "value": True,
                        },
                    ],
                    "hardware_profile": None,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
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

        assert [
            question["key"]
            for question in payload["questions"]
        ] == [
            "free_components_only",
            "paid_external_services_allowed",
            "source_code_must_stay_local",
            "prefer_local_execution",
            "modify_files",
            "run_tests",
        ]

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_suppresses_irrelevant_starter_question(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        request = Request(
            (
                f"http://{host}:{port}"
                "/v1/agent-starter/questions"
            ),
            data=json.dumps(
                {
                    "goal": "automation",
                    "evidence": [
                        {
                            "key": (
                                "destructive_or_high_impact_actions"
                            ),
                            "source": "declared",
                            "value": False,
                        },
                    ],
                    "hardware_profile": None,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
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

        assert [
            question["key"]
            for question in payload["questions"]
        ] == [
            "offline_required",
            "free_components_only",
            "paid_external_services_allowed",
            "workflow_deterministic",
            "availability_24_7_required",
        ]

        assert "human_approval_required" not in {
            question["key"]
            for question in payload["questions"]
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_agent_lab_bridge_rejects_invalid_starter_intake(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        request = Request(
            (
                f"http://{host}:{port}"
                "/v1/agent-starter/questions"
            ),
            data=json.dumps(
                {
                    "goal": "definitely-not-a-goal",
                    "evidence": [],
                    "hardware_profile": None,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with pytest.raises(HTTPError) as error:
            urlopen(
                request,
                timeout=2,
            )

        assert error.value.code == 400

        payload = json.loads(
            error.value.read().decode("utf-8")
        )

        assert payload["error"] == "bad_request"
        assert payload["message"]

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
