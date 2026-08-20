from pathlib import Path

EXTENSION_ROOT = Path(
    "consumer_probe/extension"
)

POPUP = (
    EXTENSION_ROOT
    / "popup"
    / "popup.js"
)

BACKGROUND = (
    EXTENSION_ROOT
    / "background"
    / "background.js"
)

SERVICE_WORKER = (
    EXTENSION_ROOT
    / "background"
    / "service_worker.js"
)


def test_probe_uuid_is_created_before_completion():
    source = POPUP.read_text(
        encoding="utf-8"
    )

    assert source.count(
        "crypto.randomUUID()"
    ) == 1

    assert (
        "probeId = crypto.randomUUID();"
        in source
    )

    assert "probe_id: probeId" in source


def test_overlay_requests_telemetry_lifecycle():
    source = POPUP.read_text(
        encoding="utf-8"
    )

    for message_type in (
        "dllo-telemetry-start",
        "dllo-telemetry-stop",
        "dllo-telemetry-cancel",
    ):
        assert message_type in source


def test_browser_record_contains_local_telemetry():
    source = POPUP.read_text(
        encoding="utf-8"
    )

    assert "local_telemetry:" in source
    assert "local_telemetry_error:" in source


def test_backgrounds_expose_same_telemetry_contract():
    background = BACKGROUND.read_text(
        encoding="utf-8"
    )

    service_worker = (
        SERVICE_WORKER.read_text(
            encoding="utf-8"
        )
    )

    assert background == service_worker

    for route in (
        "/v1/telemetry/start",
        "/v1/telemetry/stop",
        "/v1/telemetry/cancel",
    ):
        assert route in background


def test_browser_record_marks_human_first_output_measurement():
    source = POPUP.read_text(
        encoding="utf-8"
    )

    assert (
        "first_output_measurement_mode:"
        in source
    )
    assert (
        '"human-observed-click-v0.1"'
        in source
    )
    assert (
        'makeButton("Mark First Output (Human)")'
        in source
    )
