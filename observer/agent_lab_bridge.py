from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class AgentLabBridgeConfig:
    observer_id: str
    region_code: str
    history_root: Path


def make_handler(
    config: AgentLabBridgeConfig,
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
