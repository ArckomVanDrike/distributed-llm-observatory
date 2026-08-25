from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from urllib.parse import quote, unquote


@dataclass(frozen=True)
class ObservedActionCall:
    tool_name: str
    arguments: dict[str, object]


class ActionGateway:
    """
    Local Observatory-owned HTTP gateway for observing tool calls.

    The gateway records accepted calls. It does not know benchmark
    expectations and does not produce evaluation verdicts.
    """

    def __init__(
        self,
        *,
        tool_results: (
            dict[str, dict[str, object]] | None
        ) = None,
    ) -> None:
        self.token = secrets.token_urlsafe(32)

        self._calls: list[ObservedActionCall] = []
        self._lock = threading.Lock()
        self._tool_results = {
            tool_name: dict(result)
            for tool_name, result
            in (tool_results or {}).items()
        }

        gateway = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                prefix = "/v1/tools/"

                if not self.path.startswith(prefix):
                    self._send_json(
                        {
                            "schema_version": "0.1",
                            "accepted": False,
                        },
                        status=404,
                    )
                    return

                expected_authorization = (
                    f"Bearer {gateway.token}"
                )

                if (
                    self.headers.get("Authorization")
                    != expected_authorization
                ):
                    self._send_json(
                        {
                            "schema_version": "0.1",
                            "accepted": False,
                        },
                        status=401,
                    )
                    return

                tool_name = unquote(
                    self.path[len(prefix):]
                )

                if not tool_name:
                    self._send_json(
                        {
                            "schema_version": "0.1",
                            "accepted": False,
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

                    payload = json.loads(
                        self.rfile.read(length).decode(
                            "utf-8"
                        )
                    )
                except (
                    ValueError,
                    UnicodeDecodeError,
                    json.JSONDecodeError,
                ):
                    self._send_json(
                        {
                            "schema_version": "0.1",
                            "accepted": False,
                        },
                        status=400,
                    )
                    return

                if not isinstance(payload, dict):
                    self._send_json(
                        {
                            "schema_version": "0.1",
                            "accepted": False,
                        },
                        status=400,
                    )
                    return

                call = ObservedActionCall(
                    tool_name=tool_name,
                    arguments=dict(payload),
                )

                with gateway._lock:
                    gateway._calls.append(call)

                response_payload: dict[str, object] = {
                    "schema_version": "0.1",
                    "accepted": True,
                }

                tool_result = gateway._tool_results.get(
                    tool_name
                )

                if tool_result is not None:
                    response_payload["result"] = dict(
                        tool_result
                    )

                self._send_json(
                    response_payload,
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

        self._server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            Handler,
        )

        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address

        return f"http://{host}:{port}"

    @property
    def calls(self) -> tuple[ObservedActionCall, ...]:
        with self._lock:
            return tuple(self._calls)

    def tool_url(
        self,
        tool_name: str,
    ) -> str:
        if not tool_name:
            raise ValueError(
                "tool_name cannot be empty."
            )

        encoded = quote(
            tool_name,
            safe="",
        )

        return (
            f"{self.base_url}/v1/tools/{encoded}"
        )

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError(
                "ActionGateway is already running."
            )

        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
        )
        self._thread.start()

    def close(self) -> None:
        if self._thread is None:
            return

        self._server.shutdown()
        self._server.server_close()
        self._thread.join()

        self._thread = None

    def __enter__(self) -> ActionGateway:
        self.start()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
