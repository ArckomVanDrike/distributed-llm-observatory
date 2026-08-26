from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path
from urllib.parse import urlparse

from observer.core.agent_lab_artifact_io import (
    write_agent_lab_run_artifact,
)
from observer.core.agent_lab_observation_qualification import (
    qualify_agent_observation,
)
from observer.core.agent_lab_protocol_runner import (
    AgentLabProtocolRunner,
)


@dataclass(frozen=True)
class AgentLabBridgeConfig:
    observer_id: str
    region_code: str
    history_root: Path


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

            self._send_json(
                404,
                {
                    "error": "not_found",
                },
            )

        def do_POST(self) -> None:
            parsed = urlparse(self.path)

            if parsed.path == "/v1/agent-tests":
                self._handle_agent_test()
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

            length = int(raw_length)

            if length <= 0:
                raise ValueError(
                    "Request body is required."
                )

            raw_body = self.rfile.read(length)

            payload = json.loads(
                raw_body.decode("utf-8")
            )

            if not isinstance(
                payload,
                dict,
            ):
                raise ValueError(
                    "JSON request body must be an object."
                )

            return payload

        def _handle_agent_test(
            self,
        ) -> None:
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

            runner = runner_factory(
                config
            )

            result = runner.run(
                base_url=base_url,
                generated_at_utc=datetime.now(
                    timezone.utc
                ),
            )

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
