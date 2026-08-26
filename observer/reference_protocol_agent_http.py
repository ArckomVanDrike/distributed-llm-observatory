from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from time import perf_counter

from observer.reference_protocol_agent import (
    ReferenceProtocolAgent,
)
from schemas.sut_protocol import (
    SUTProtocolExecutionRequest,
    SUTProtocolExecutionResponse,
)


def make_reference_protocol_handler(
    agent: ReferenceProtocolAgent,
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != "/v1/manifest":
                self._send_json(
                    {
                        "error": "not_found",
                    },
                    status=404,
                )
                return

            self._send_json(
                {
                    "schema_version": "0.1",
                    "manifest": agent.manifest(),
                },
                status=200,
            )

        def do_POST(self) -> None:
            if self.path != "/v1/execute":
                self._send_json(
                    {
                        "error": "not_found",
                    },
                    status=404,
                )
                return

            try:
                length = int(
                    self.headers.get(
                        "Content-Length",
                        "0",
                    )
                )

                raw_payload = json.loads(
                    self.rfile.read(length).decode(
                        "utf-8"
                    )
                )

                request_payload = (
                    SUTProtocolExecutionRequest.model_validate(
                        raw_payload
                    )
                )
            except (
                ValueError,
                UnicodeDecodeError,
                json.JSONDecodeError,
            ):
                self._send_json(
                    {
                        "error": "bad_request",
                    },
                    status=400,
                )
                return

            started_at_utc = datetime.now(
                timezone.utc
            )
            started = perf_counter()

            result = agent.execute(
                task=request_payload.task,
                metadata=request_payload.metadata,
            )

            latency_ms = (
                perf_counter() - started
            ) * 1000

            finished_at_utc = datetime.now(
                timezone.utc
            )

            response = SUTProtocolExecutionResponse(
                context=request_payload.context,
                started_at_utc=started_at_utc,
                finished_at_utc=finished_at_utc,
                latency_ms=latency_ms,
                task_completed=result.task_completed,
                output_text=result.output_text,
                retry_count=result.retry_count,
                human_intervention_count=(
                    result.human_intervention_count
                ),
                error_type=None,
                metrics=result.metrics or {},
            )

            self._send_json(
                response.model_dump(
                    mode="json"
                ),
                status=200,
            )

        def _send_json(
            self,
            payload: dict[str, object],
            *,
            status: int,
        ) -> None:
            body = json.dumps(payload).encode(
                "utf-8"
            )

            self.send_response(status)
            self.send_header(
                "Content-Type",
                "application/json",
            )
            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.end_headers()
            self.wfile.write(body)

        def log_message(
            self,
            format,
            *args,
        ) -> None:
            return

    return Handler
