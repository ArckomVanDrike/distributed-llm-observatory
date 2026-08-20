import json
from datetime import date, datetime
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import quote
from urllib.request import urlopen

import pytest

from consumer_probe.bridge import (
    BridgeConfig,
    build_next_payload,
    make_handler,
    serve,
)
from consumer_probe.schemas import ConsumerPlatform
from observer.core.consumer_schedule import (
    build_prompt_bank_schedule,
)


def write_prompt_bank(root: Path) -> None:
    path = (
        root
        / "mathematics"
        / "mathematics-001.json"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        """
        {
          "prompt_id": "mathematics-001",
          "benchmark_version": "0.1",
          "category": "mathematics",
          "difficulty": "medium",
          "prompt": "Solve x + 1 = 2.",
          "expected_characteristics": [
            "Concludes that x = 1."
          ],
          "scoring_method": "observatory_rubric_v0.1",
          "enabled": true
        }
        """,
        encoding="utf-8",
    )


def make_config(
    tmp_path: Path,
) -> BridgeConfig:
    prompt_bank = tmp_path / "prompts"
    write_prompt_bank(prompt_bank)

    return BridgeConfig(
        observer_id="observer-test",
        platform=ConsumerPlatform.CHATGPT,
        prompt_bank_path=prompt_bank,
        storage_path=tmp_path / "consumer.db",
    )


def scheduled_time(
    config: BridgeConfig,
) -> datetime:
    schedule = build_prompt_bank_schedule(
        date(2026, 8, 19),
        observer_id=config.observer_id,
        benchmark_version=config.benchmark_version,
        prompt_bank_path=config.prompt_bank_path,
    )

    return schedule.items[0].scheduled_at_utc


def test_build_next_payload_reports_due(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    now = scheduled_time(config)

    payload = build_next_payload(
        config,
        now_utc=now,
    )

    assert payload["schema_version"] == "0.1"
    assert payload["status"] == "due"
    assert payload["observer_id"] == "observer-test"
    assert payload["platform"] == "chatgpt"

    item = payload["item"]

    assert item is not None
    assert item["prompt_id"] == "mathematics-001"
    assert item["category"] == "mathematics"
    assert item["overdue_by_ms"] == 0


def test_build_next_payload_rejects_naive_time(
    tmp_path: Path,
):
    config = make_config(tmp_path)

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        build_next_payload(
            config,
            now_utc=datetime(
                2026,
                8,
                19,
                10,
                0,
            ),
        )


def run_test_server(
    config: BridgeConfig,
):
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


def test_health_endpoint(
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
            payload = json.load(response)

        assert response.status == 200
        assert payload == {
            "status": "ok",
            "service": "dllo-consumer-bridge",
        }

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_next_endpoint_returns_json_contract(
    tmp_path: Path,
):
    config = make_config(tmp_path)
    now = scheduled_time(config)

    server, thread = run_test_server(config)

    try:
        host, port = server.server_address

        encoded_now = quote(
            now.isoformat(),
            safe="",
        )

        url = (
            f"http://{host}:{port}"
            f"/v1/next?now={encoded_now}"
        )

        with urlopen(
            url,
            timeout=2,
        ) as response:
            payload = json.load(response)

        assert response.status == 200
        assert payload["status"] == "due"
        assert payload["item"]["prompt_id"] == (
            "mathematics-001"
        )

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_bridge_rejects_non_local_bind(
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
            port=8765,
        )


def post_json(
    url: str,
    payload: dict,
):
    from urllib.request import Request

    body = json.dumps(
        payload
    ).encode("utf-8")

    return urlopen(
        Request(
            url,
            data=body,
            headers={
                "Content-Type":
                    "application/json",
            },
            method="POST",
        ),
        timeout=2,
    )


def test_telemetry_start_and_cancel_endpoints(
    tmp_path: Path,
):
    config = make_config(tmp_path)

    server, thread = run_test_server(
        config
    )

    probe_id = (
        "19aa650b-76ea-4e8e-"
        "bf4e-10188989935b"
    )

    try:
        host, port = server.server_address
        base = f"http://{host}:{port}"

        with post_json(
            f"{base}/v1/telemetry/start",
            {
                "probe_id": probe_id,
            },
        ) as response:
            payload = json.load(
                response
            )

        assert response.status == 201
        assert payload["status"] == "running"
        assert payload["probe_id"] == probe_id

        with post_json(
            f"{base}/v1/telemetry/cancel",
            {
                "probe_id": probe_id,
            },
        ) as response:
            payload = json.load(
                response
            )

        assert response.status == 200
        assert payload["status"] == "cancelled"

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_telemetry_stop_returns_local_metrics(
    tmp_path: Path,
):
    config = make_config(tmp_path)

    server, thread = run_test_server(
        config
    )

    probe_id = (
        "a53ff6e7-3972-4287-"
        "86ab-72f438fe56bf"
    )

    try:
        host, port = server.server_address
        base = f"http://{host}:{port}"

        with post_json(
            f"{base}/v1/telemetry/start",
            {
                "probe_id": probe_id,
            },
        ):
            pass

        with post_json(
            f"{base}/v1/telemetry/stop",
            {
                "probe_id": probe_id,
            },
        ) as response:
            payload = json.load(
                response
            )

        assert response.status == 200
        assert payload["probe_id"] == probe_id

        assert (
            payload["telemetry_schema_version"]
            == "0.2"
        )

        assert (
            payload["collector_version"]
            == "linux-proc-firefox-tree-fastslow-v0.1"
        )
        assert (
            payload["browser_scope"]
            == "firefox-process-tree"
        )
        assert payload["memory_method"] == "rss+pss"
        assert payload["fast_interval_target_ms"] == 250
        assert payload["pss_interval_target_ms"] == 1500

        assert payload["sample_count"] >= 1

        assert (
            payload["peak_browser_rss_bytes"]
            is not None
        )

        assert (
            payload[
                "min_system_memory_available_bytes"
            ]
            is not None
        )

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
