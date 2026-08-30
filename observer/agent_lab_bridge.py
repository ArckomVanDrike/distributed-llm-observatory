from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from importlib.resources import files
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import UUID

from observer.core.agent_lab_artifact_io import (
    write_agent_lab_run_artifact,
)
from observer.core.agent_lab_geographic_comparison import (
    compare_geographic_agent_observations,
)
from observer.core.agent_lab_observation_pairs import (
    discover_geographic_agent_observation_pairs,
    discover_temporal_agent_observation_pairs,
)
from observer.core.agent_lab_observation_qualification import (
    qualify_agent_observation,
)
from observer.core.agent_lab_protocol_runner import (
    AgentLabProtocolRunner,
    AgentLabProtocolRunnerError,
)
from observer.core.agent_lab_run_history import (
    AgentLabRunHistory,
)
from observer.core.agent_lab_temporal_comparison import (
    compare_temporal_agent_observations,
)
from observer.core.agent_starter_catalog_bank import (
    AgentStarterCatalogBank,
    AgentStarterCatalogBankError,
)
from observer.core.agent_starter_questionnaire import (
    build_agent_starter_question_set,
)
from observer.core.agent_starter_unified_pipeline import (
    run_agent_starter_unified_pipeline,
)
from schemas.agent_starter import AgentStarterIntake


def _default_agent_starter_catalog_root() -> Path:
    return Path(
        str(
            files("observer.resources.agent_starter")
        )
    )


@dataclass(frozen=True)
class AgentLabBridgeConfig:
    observer_id: str
    region_code: str
    history_root: Path
    catalog_root: Path = field(
        default_factory=_default_agent_starter_catalog_root
    )


RunnerFactory = Callable[
    [AgentLabBridgeConfig],
    AgentLabProtocolRunner,
]


def _default_runner_factory(
    config: AgentLabBridgeConfig,
) -> AgentLabProtocolRunner:
    return AgentLabProtocolRunner(
        observer_id=config.observer_id,
        region_code=config.region_code,
    )


def make_handler(
    config: AgentLabBridgeConfig,
    *,
    runner_factory: RunnerFactory = (
        _default_runner_factory
    ),
):
    class AgentLabBridgeHandler(
        BaseHTTPRequestHandler
    ):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)

            if parsed.path == "/health":
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "service": (
                            "dllo-agent-lab-bridge"
                        ),
                    },
                )
                return

            if (
                parsed.path
                == "/v1/agent-starter/runtime-options"
            ):
                self._handle_agent_starter_runtime_options()
                return

            if parsed.path == "/v1/agent-tests":
                self._handle_agent_test_history()
                return

            if (
                parsed.path
                == "/v1/agent-observation-pairs/temporal"
            ):
                self._handle_temporal_observation_pairs()
                return

            if (
                parsed.path
                == "/v1/agent-observation-pairs/geographic"
            ):
                self._handle_geographic_observation_pairs(
                    parsed.query
                )
                return

            self._send_json(
                404,
                {
                    "error": "not_found",
                },
            )

        def do_POST(self) -> None:
            parsed = urlparse(self.path)

            if (
                parsed.path
                == "/v1/agent-starter/questions"
            ):
                self._handle_agent_starter_questions()
                return

            if (
                parsed.path
                == "/v1/agent-starter/recommend"
            ):
                self._handle_agent_starter_recommendation()
                return

            if parsed.path == "/v1/agent-tests":
                self._handle_agent_test()
                return

            if (
                parsed.path
                == "/v1/agent-comparisons/temporal"
            ):
                self._handle_temporal_comparison()
                return

            if (
                parsed.path
                == "/v1/agent-comparisons/geographic"
            ):
                self._handle_geographic_comparison()
                return

            self._send_json(
                404,
                {
                    "error": "not_found",
                },
            )

        def _read_json_body(
            self,
        ) -> dict:
            raw_length = self.headers.get(
                "Content-Length"
            )

            if raw_length is None:
                raise ValueError(
                    "Content-Length is required."
                )

            try:
                length = int(raw_length)
            except ValueError as exc:
                raise ValueError(
                    "Invalid Content-Length."
                ) from exc

            if length <= 0:
                raise ValueError(
                    "Request body is required."
                )

            if length > 4096:
                raise ValueError(
                    "Request body is too large."
                )

            raw_body = self.rfile.read(length)

            try:
                payload = json.loads(
                    raw_body.decode("utf-8")
                )
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
            ) as exc:
                raise ValueError(
                    "Invalid JSON request body."
                ) from exc

            if not isinstance(
                payload,
                dict,
            ):
                raise ValueError(
                    "JSON request body must be an object."
                )

            return payload

        def _handle_agent_starter_questions(
            self,
        ) -> None:
            try:
                payload = self._read_json_body()

                intake = (
                    AgentStarterIntake.model_validate(
                        payload
                    )
                )

            except ValueError as exc:
                self._send_json(
                    400,
                    {
                        "error": "bad_request",
                        "message": str(exc),
                    },
                )
                return

            question_set = (
                build_agent_starter_question_set(
                    intake
                )
            )

            self._send_json(
                200,
                question_set.model_dump(
                    mode="json",
                ),
            )

        def _handle_agent_starter_runtime_options(
            self,
        ) -> None:
            try:
                snapshot = AgentStarterCatalogBank(
                    root=config.catalog_root,
                ).load_snapshot(
                    "catalog-v0-2.json",
                )
            except AgentStarterCatalogBankError as exc:
                self._send_json(
                    500,
                    {
                        "error": "catalog_unavailable",
                        "message": str(exc),
                    },
                )
                return

            runtimes = sorted(
                {
                    runtime
                    for entry in snapshot.entries
                    for runtime in entry.supported_runtimes
                }
            )

            self._send_json(
                200,
                {
                    "schema_version": "0.1",
                    "catalog_snapshot_id": (
                        snapshot.snapshot_id
                    ),
                    "runtimes": runtimes,
                },
            )

        def _handle_agent_starter_recommendation(
            self,
        ) -> None:
            try:
                payload = self._read_json_body()

                intake = (
                    AgentStarterIntake.model_validate(
                        payload
                    )
                )

            except ValueError as exc:
                self._send_json(
                    400,
                    {
                        "error": "bad_request",
                        "message": str(exc),
                    },
                )
                return

            try:
                snapshot = AgentStarterCatalogBank(
                    root=config.catalog_root,
                ).load_snapshot(
                    "catalog-v0-2.json",
                )
            except AgentStarterCatalogBankError as exc:
                self._send_json(
                    500,
                    {
                        "error": "catalog_unavailable",
                        "message": str(exc),
                    },
                )
                return

            report = (
                run_agent_starter_unified_pipeline(
                    intake=intake,
                    catalog_snapshot=snapshot,
                )
            )

            self._send_json(
                200,
                report.model_dump(
                    mode="json",
                ),
            )

        def _handle_agent_test_history(
            self,
        ) -> None:
            history = AgentLabRunHistory(
                config.history_root
            )

            artifacts = history.load_all()

            runs = []

            for artifact in artifacts:
                session = artifact.session
                report = artifact.technical_report
                qualification = (
                    qualify_agent_observation(
                        artifact
                    )
                )

                runs.append(
                    {
                        "session_id": str(
                            session.session_id
                        ),
                        "started_at_utc": (
                            session
                            .started_at_utc
                            .isoformat()
                        ),
                        "target_id": (
                            session.target.target_id
                        ),
                        "suite_id": (
                            session.suite_id
                        ),
                        "suite_version": (
                            session.suite_version
                        ),
                        "observer_id": (
                            session.observer_id
                        ),
                        "region_code": (
                            session.region_code
                        ),
                        "observatory": {
                            "provenance_complete": (
                                qualification
                                .provenance_complete
                            ),
                            "temporal_eligible": (
                                qualification
                                .temporal_eligible
                            ),
                            "geographic_eligible": (
                                qualification
                                .geographic_eligible
                            ),
                            "reasons": list(
                                qualification.reasons
                            ),
                        },
                        "total_tasks": (
                            report.total_tasks
                        ),
                        "passed_tasks": (
                            report.passed_tasks
                        ),
                        "failed_tasks": (
                            report.failed_tasks
                        ),
                        "pass_rate": (
                            report.pass_rate
                        ),
                        "median_latency_ms": (
                            report.median_latency_ms
                        ),
                    }
                )

            self._send_json(
                200,
                {
                    "schema_version": "0.1",
                    "runs": runs,
                },
            )

        def _handle_temporal_observation_pairs(
            self,
        ) -> None:
            history = AgentLabRunHistory(
                config.history_root
            )

            artifacts = history.load_all()

            discovered = (
                discover_temporal_agent_observation_pairs(
                    artifacts
                )
            )

            pairs = []

            for pair in discovered:
                pairs.append(
                    {
                        "baseline_session_id": str(
                            pair.baseline_session_id
                        ),
                        "candidate_session_id": str(
                            pair.candidate_session_id
                        ),
                        "baseline_started_at_utc": (
                            pair
                            .baseline_started_at_utc
                            .isoformat()
                        ),
                        "candidate_started_at_utc": (
                            pair
                            .candidate_started_at_utc
                            .isoformat()
                        ),
                        "baseline_observer_id": (
                            pair.baseline_observer_id
                        ),
                        "candidate_observer_id": (
                            pair.candidate_observer_id
                        ),
                        "baseline_region_code": (
                            pair.baseline_region_code
                        ),
                        "candidate_region_code": (
                            pair.candidate_region_code
                        ),
                        "comparable": pair.comparable,
                        "reasons": list(
                            pair.reasons
                        ),
                    }
                )

            self._send_json(
                200,
                {
                    "schema_version": "0.1",
                    "pair_type": "temporal",
                    "pairs": pairs,
                },
            )

        def _handle_geographic_observation_pairs(
            self,
            raw_query: str,
        ) -> None:
            query = parse_qs(
                raw_query,
                keep_blank_values=True,
            )

            max_skew_raw = query.get(
                "max_observation_skew_seconds",
                [None],
            )[0]

            if max_skew_raw in (None, ""):
                self._send_json(
                    400,
                    {
                        "error": "bad_request",
                        "message": (
                            "max_observation_skew_seconds "
                            "is required."
                        ),
                    },
                )
                return

            try:
                max_skew_seconds = float(
                    max_skew_raw
                )
            except ValueError:
                self._send_json(
                    400,
                    {
                        "error": "bad_request",
                        "message": (
                            "max_observation_skew_seconds "
                            "must be a number."
                        ),
                    },
                )
                return

            history = AgentLabRunHistory(
                config.history_root
            )

            artifacts = history.load_all()

            try:
                discovered = (
                    discover_geographic_agent_observation_pairs(
                        artifacts,
                        max_observation_skew=timedelta(
                            seconds=max_skew_seconds
                        ),
                    )
                )
            except ValueError as exc:
                self._send_json(
                    422,
                    {
                        "error": "comparison_rejected",
                        "message": str(exc),
                    },
                )
                return

            pairs = []

            for pair in discovered:
                pairs.append(
                    {
                        "baseline_session_id": str(
                            pair.baseline_session_id
                        ),
                        "candidate_session_id": str(
                            pair.candidate_session_id
                        ),
                        "baseline_started_at_utc": (
                            pair
                            .baseline_started_at_utc
                            .isoformat()
                        ),
                        "candidate_started_at_utc": (
                            pair
                            .candidate_started_at_utc
                            .isoformat()
                        ),
                        "baseline_observer_id": (
                            pair.baseline_observer_id
                        ),
                        "candidate_observer_id": (
                            pair.candidate_observer_id
                        ),
                        "baseline_region_code": (
                            pair.baseline_region_code
                        ),
                        "candidate_region_code": (
                            pair.candidate_region_code
                        ),
                        "comparable": pair.comparable,
                        "reasons": list(
                            pair.reasons
                        ),
                    }
                )

            self._send_json(
                200,
                {
                    "schema_version": "0.1",
                    "pair_type": "geographic",
                    "max_observation_skew_seconds": (
                        max_skew_seconds
                    ),
                    "pairs": pairs,
                },
            )

        def _handle_geographic_comparison(
            self,
        ) -> None:
            try:
                payload = self._read_json_body()

                baseline_raw = payload.get(
                    "baseline_session_id"
                )
                candidate_raw = payload.get(
                    "candidate_session_id"
                )
                max_skew_raw = payload.get(
                    "max_observation_skew_seconds"
                )

                if not isinstance(
                    baseline_raw,
                    str,
                ):
                    raise ValueError(
                        "baseline_session_id is required."
                    )

                if not isinstance(
                    candidate_raw,
                    str,
                ):
                    raise ValueError(
                        "candidate_session_id is required."
                    )

                if (
                    isinstance(max_skew_raw, bool)
                    or not isinstance(
                        max_skew_raw,
                        (int, float),
                    )
                ):
                    raise ValueError(
                        "max_observation_skew_seconds "
                        "is required."
                    )

                baseline_id = UUID(
                    baseline_raw
                )
                candidate_id = UUID(
                    candidate_raw
                )

                max_observation_skew = timedelta(
                    seconds=max_skew_raw
                )

            except ValueError as exc:
                self._send_json(
                    400,
                    {
                        "error": "bad_request",
                        "message": str(exc),
                    },
                )
                return

            history = AgentLabRunHistory(
                config.history_root
            )

            try:
                baseline = history.get_by_session_id(
                    baseline_id
                )
                candidate = history.get_by_session_id(
                    candidate_id
                )

                comparison = (
                    compare_geographic_agent_observations(
                        candidate,
                        baseline,
                        max_observation_skew=(
                            max_observation_skew
                        ),
                    )
                )

            except ValueError as exc:
                self._send_json(
                    422,
                    {
                        "error": "comparison_rejected",
                        "message": str(exc),
                    },
                )
                return

            changes = comparison.run_comparison

            self._send_json(
                200,
                {
                    "schema_version": "0.1",
                    "comparison_type": "geographic",
                    "baseline_session_id": str(
                        changes.baseline_session_id
                    ),
                    "candidate_session_id": str(
                        changes.candidate_session_id
                    ),
                    "baseline_observer_id": (
                        comparison.baseline_observer_id
                    ),
                    "candidate_observer_id": (
                        comparison.candidate_observer_id
                    ),
                    "baseline_region_code": (
                        comparison.baseline_region_code
                    ),
                    "candidate_region_code": (
                        comparison.candidate_region_code
                    ),
                    "baseline_started_at_utc": (
                        comparison
                        .baseline_started_at_utc
                        .isoformat()
                    ),
                    "candidate_started_at_utc": (
                        comparison
                        .candidate_started_at_utc
                        .isoformat()
                    ),
                    "observation_skew_seconds": (
                        comparison
                        .observation_skew
                        .total_seconds()
                    ),
                    "max_observation_skew_seconds": (
                        comparison
                        .max_observation_skew
                        .total_seconds()
                    ),
                    "changes": {
                        "total_tasks": (
                            changes.total_tasks
                        ),
                        "regressions": (
                            changes.regressions
                        ),
                        "improvements": (
                            changes.improvements
                        ),
                        "unchanged": (
                            changes.unchanged
                        ),
                        "pass_rate_delta": (
                            changes.pass_rate_delta
                        ),
                        "median_latency_ms_delta": (
                            changes
                            .median_latency_ms_delta
                        ),
                        "retry_delta": (
                            changes.retry_delta
                        ),
                        "human_intervention_delta": (
                            changes
                            .human_intervention_delta
                        ),
                        "task_changes": [
                            {
                                "task_id": (
                                    change.task_id
                                ),
                                "baseline_passed": (
                                    change
                                    .baseline_passed
                                ),
                                "candidate_passed": (
                                    change
                                    .candidate_passed
                                ),
                                "transition": (
                                    change
                                    .transition
                                    .value
                                ),
                            }
                            for change
                            in changes.task_changes
                        ],
                    },
                },
            )

        def _handle_temporal_comparison(
            self,
        ) -> None:
            try:
                payload = self._read_json_body()

                baseline_raw = payload.get(
                    "baseline_session_id"
                )
                candidate_raw = payload.get(
                    "candidate_session_id"
                )

                if not isinstance(
                    baseline_raw,
                    str,
                ):
                    raise ValueError(
                        "baseline_session_id is required."
                    )

                if not isinstance(
                    candidate_raw,
                    str,
                ):
                    raise ValueError(
                        "candidate_session_id is required."
                    )

                baseline_id = UUID(
                    baseline_raw
                )
                candidate_id = UUID(
                    candidate_raw
                )

            except ValueError as exc:
                self._send_json(
                    400,
                    {
                        "error": "bad_request",
                        "message": str(exc),
                    },
                )
                return

            history = AgentLabRunHistory(
                config.history_root
            )

            try:
                baseline = history.get_by_session_id(
                    baseline_id
                )
                candidate = history.get_by_session_id(
                    candidate_id
                )

                comparison = (
                    compare_temporal_agent_observations(
                        candidate,
                        baseline,
                    )
                )

            except ValueError as exc:
                self._send_json(
                    422,
                    {
                        "error": "comparison_rejected",
                        "message": str(exc),
                    },
                )
                return

            changes = comparison.run_comparison

            self._send_json(
                200,
                {
                    "schema_version": "0.1",
                    "comparison_type": "temporal",
                    "baseline_session_id": str(
                        changes.baseline_session_id
                    ),
                    "candidate_session_id": str(
                        changes.candidate_session_id
                    ),
                    "observer_id": (
                        comparison.observer_id
                    ),
                    "region_code": (
                        comparison.region_code
                    ),
                    "baseline_started_at_utc": (
                        comparison
                        .baseline_started_at_utc
                        .isoformat()
                    ),
                    "candidate_started_at_utc": (
                        comparison
                        .candidate_started_at_utc
                        .isoformat()
                    ),
                    "changes": {
                        "total_tasks": (
                            changes.total_tasks
                        ),
                        "regressions": (
                            changes.regressions
                        ),
                        "improvements": (
                            changes.improvements
                        ),
                        "unchanged": (
                            changes.unchanged
                        ),
                        "pass_rate_delta": (
                            changes.pass_rate_delta
                        ),
                        "median_latency_ms_delta": (
                            changes
                            .median_latency_ms_delta
                        ),
                        "retry_delta": (
                            changes.retry_delta
                        ),
                        "human_intervention_delta": (
                            changes
                            .human_intervention_delta
                        ),
                        "task_changes": [
                            {
                                "task_id": (
                                    change.task_id
                                ),
                                "baseline_passed": (
                                    change
                                    .baseline_passed
                                ),
                                "candidate_passed": (
                                    change
                                    .candidate_passed
                                ),
                                "transition": (
                                    change
                                    .transition
                                    .value
                                ),
                            }
                            for change
                            in changes.task_changes
                        ],
                    },
                },
            )

        def _handle_agent_test(
            self,
        ) -> None:
            try:
                payload = self._read_json_body()

                base_url = payload.get(
                    "base_url"
                )

                if not isinstance(
                    base_url,
                    str,
                ):
                    raise ValueError(
                        "base_url is required."
                    )

            except ValueError as exc:
                self._send_json(
                    400,
                    {
                        "error": "bad_request",
                        "message": str(exc),
                    },
                )
                return

            runner = runner_factory(
                config
            )

            try:
                result = runner.run(
                    base_url=base_url,
                    generated_at_utc=datetime.now(
                        timezone.utc
                    ),
                )

            except AgentLabProtocolRunnerError as exc:
                self._send_json(
                    500,
                    {
                        "error": "agent_test_failed",
                        "message": str(exc),
                    },
                )
                return

            artifact = result.to_artifact()

            qualification = (
                qualify_agent_observation(
                    artifact
                )
            )

            config.history_root.mkdir(
                parents=True,
                exist_ok=True,
            )

            artifact_path = (
                config.history_root
                / (
                    f"{artifact.session.session_id}"
                    ".json"
                )
            )

            write_agent_lab_run_artifact(
                artifact,
                artifact_path,
            )

            session = artifact.session
            report = artifact.technical_report

            self._send_json(
                201,
                {
                    "schema_version": "0.1",
                    "status": "completed",
                    "started_at_utc": (
                        session.started_at_utc.isoformat()
                    ),
                    "session_id": str(
                        session.session_id
                    ),
                    "target_id": (
                        session.target.target_id
                    ),
                    "suite_id": (
                        session.suite_id
                    ),
                    "suite_version": (
                        session.suite_version
                    ),
                    "observer_id": (
                        session.observer_id
                    ),
                    "region_code": (
                        session.region_code
                    ),
                    "observatory": {
                        "provenance_complete": (
                            qualification
                            .provenance_complete
                        ),
                        "temporal_eligible": (
                            qualification
                            .temporal_eligible
                        ),
                        "geographic_eligible": (
                            qualification
                            .geographic_eligible
                        ),
                        "reasons": list(
                            qualification.reasons
                        ),
                    },
                    "total_tasks": (
                        report.total_tasks
                    ),
                    "passed_tasks": (
                        report.passed_tasks
                    ),
                    "failed_tasks": (
                        report.failed_tasks
                    ),
                    "pass_rate": (
                        report.pass_rate
                    ),
                    "median_latency_ms": (
                        report.median_latency_ms
                    ),
                    "findings": list(
                        report.findings
                    ),
                    "recommendations": list(
                        report.recommendations
                    ),
                },
            )

        def _send_json(
            self,
            status: int,
            payload: dict,
        ) -> None:
            body = json.dumps(
                payload,
                ensure_ascii=False,
            ).encode("utf-8")

            self.send_response(status)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8",
            )
            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.send_header(
                "Cache-Control",
                "no-store",
            )
            self.end_headers()
            self.wfile.write(body)

        def log_message(
            self,
            format: str,
            *args,
        ) -> None:
            return

    return AgentLabBridgeHandler


def serve(
    config: AgentLabBridgeConfig,
    *,
    host: str = "127.0.0.1",
    port: int = 8766,
) -> None:
    if host not in {
        "127.0.0.1",
        "::1",
        "localhost",
    }:
        raise ValueError(
            "Agent Lab bridge may only bind "
            "to localhost."
        )

    server = ThreadingHTTPServer(
        (host, port),
        make_handler(config),
    )

    print(
        "DLLO Agent Lab Bridge listening on "
        f"http://{host}:{port}"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
