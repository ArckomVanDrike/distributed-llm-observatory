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
