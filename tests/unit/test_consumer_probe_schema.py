from datetime import datetime, timezone

from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeEnvelope,
    ConsumerProbeRecord,
    ProbeInputMode,
)


def make_record(**overrides) -> ConsumerProbeRecord:
    data = {
        "observer_id": "observer-test",
        "region_code": "CL-Los-Lagos",
        "platform": ConsumerPlatform.CHATGPT,
        "account_tier": "plus",
        "model_label": "user-visible-model",
        "benchmark_version": "0.1",
        "prompt_id": "reasoning-001",
        "input_mode": ProbeInputMode.MANUAL,
        "started_at_utc": datetime.now(timezone.utc),
    }

    data.update(overrides)

    return ConsumerProbeRecord(**data)


def test_consumer_probe_record_defaults_to_private():
    record = make_record()

    assert record.response_capture_enabled is False
    assert record.sharing_allowed is False
    assert record.response_text is None


def test_consumer_probe_supports_visible_account_metadata():
    record = make_record(
        platform=ConsumerPlatform.CLAUDE,
        account_tier="pro",
        model_label="visible-model-name",
    )

    assert record.platform == ConsumerPlatform.CLAUDE
    assert record.account_tier == "pro"
    assert record.model_label == "visible-model-name"


def test_shareable_record_removes_response_without_consent():
    record = make_record(
        response_text="Sensitive local response",
        response_capture_enabled=True,
        sharing_allowed=False,
    )

    envelope = ConsumerProbeEnvelope(record=record)
    shared = envelope.shareable_record()

    assert shared["response_text"] is None


def test_shareable_record_includes_response_with_explicit_consent():
    record = make_record(
        response_text="Benchmark response",
        response_capture_enabled=True,
        sharing_allowed=True,
    )

    envelope = ConsumerProbeEnvelope(record=record)
    shared = envelope.shareable_record()

    assert shared["response_text"] == "Benchmark response"


def test_probe_can_record_browser_side_timings():
    record = make_record(
        time_to_first_output_ms=850.5,
        total_latency_ms=4320.2,
    )

    assert record.time_to_first_output_ms == 850.5
    assert record.total_latency_ms == 4320.2
