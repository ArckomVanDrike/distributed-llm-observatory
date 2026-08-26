from __future__ import annotations

from pathlib import Path
from threading import Thread
from urllib.request import urlopen

import pytest

from observer.agent_lab_bridge import (
    AgentLabBridgeConfig,
    make_handler,
    serve,
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
