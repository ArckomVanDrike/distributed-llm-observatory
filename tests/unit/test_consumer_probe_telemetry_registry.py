from datetime import datetime, timezone
from uuid import uuid4

import pytest

from consumer_probe.local_telemetry import (
    LocalTelemetrySample,
)
from consumer_probe.telemetry_registry import (
    TelemetrySessionConflictError,
    TelemetrySessionNotFoundError,
    TelemetrySessionRegistry,
    normalize_probe_id,
)
from consumer_probe.telemetry_session import (
    LocalTelemetrySummary,
    TelemetrySessionResult,
)


class FakeTelemetrySession:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(
        self,
    ) -> TelemetrySessionResult:
        self.stopped = True

        now = datetime(
            2026,
            8,
            20,
            tzinfo=timezone.utc,
        )

        sample = LocalTelemetrySample(
            captured_at_utc=now,
            interval_ms=250,
            browser_process_count=5,
            browser_rss_bytes=1234,
            browser_pss_bytes=None,
            browser_cpu_percent=42,
            system_memory_available_bytes=5678,
            system_cpu_percent=21,
        )

        return TelemetrySessionResult(
            started_at_utc=now,
            stopped_at_utc=now,
            samples=(sample,),
            summary=LocalTelemetrySummary(
                sample_count=1,
                duration_ms=250,
                peak_browser_process_count=5,
                peak_browser_rss_bytes=1234,
                peak_browser_pss_bytes=900,
                peak_browser_cpu_percent=42,
                min_system_memory_available_bytes=5678,
                peak_system_cpu_percent=21,
            ),
        )


def make_registry() -> TelemetrySessionRegistry:
    return TelemetrySessionRegistry(
        session_factory=FakeTelemetrySession,
    )


def test_probe_id_is_normalized():
    probe_id = uuid4()

    assert normalize_probe_id(
        str(probe_id)
    ) == str(probe_id)


def test_invalid_probe_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="valid UUID",
    ):
        normalize_probe_id(
            "not-a-uuid"
        )


def test_registry_starts_session():
    registry = make_registry()
    probe_id = str(uuid4())

    result = registry.start(
        probe_id
    )

    assert result["status"] == "running"
    assert result["probe_id"] == probe_id
    assert registry.active_count == 1


def test_duplicate_session_is_rejected():
    registry = make_registry()
    probe_id = str(uuid4())

    registry.start(
        probe_id
    )

    with pytest.raises(
        TelemetrySessionConflictError,
    ):
        registry.start(
            probe_id
        )


def test_stop_returns_telemetry_summary():
    registry = make_registry()
    probe_id = str(uuid4())

    registry.start(
        probe_id
    )

    result = registry.stop(
        probe_id
    )

    assert result["probe_id"] == probe_id
    assert result["sample_count"] == 1

    assert (
        result["peak_browser_rss_bytes"]
        == 1234
    )

    assert (
        result["peak_browser_pss_bytes"]
        == 900
    )

    assert (
        result["peak_browser_cpu_percent"]
        == 42
    )

    assert registry.active_count == 0


def test_cancel_removes_session():
    registry = make_registry()
    probe_id = str(uuid4())

    registry.start(
        probe_id
    )

    result = registry.cancel(
        probe_id
    )

    assert result["status"] == "cancelled"
    assert registry.active_count == 0


def test_missing_session_is_rejected():
    registry = make_registry()

    with pytest.raises(
        TelemetrySessionNotFoundError,
    ):
        registry.stop(
            str(uuid4())
        )
