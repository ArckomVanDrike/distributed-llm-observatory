from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from consumer_probe.local_telemetry import (
    LocalTelemetrySample,
    LocalTelemetrySnapshot,
    LocalTelemetryUnavailableError,
    capture_local_telemetry,
    derive_local_telemetry_sample,
)


@dataclass(frozen=True)
class LocalTelemetrySummary:
    sample_count: int
    duration_ms: float

    peak_browser_process_count: int | None
    peak_browser_rss_bytes: int | None
    peak_browser_cpu_percent: float | None

    min_system_memory_available_bytes: int | None
    peak_system_cpu_percent: float | None


@dataclass(frozen=True)
class TelemetrySessionResult:
    started_at_utc: datetime
    stopped_at_utc: datetime

    samples: tuple[LocalTelemetrySample, ...]
    summary: LocalTelemetrySummary


def summarize_local_telemetry(
    samples: list[LocalTelemetrySample],
    *,
    duration_ms: float,
) -> LocalTelemetrySummary:
    if duration_ms < 0:
        raise ValueError(
            "duration_ms cannot be negative."
        )

    if not samples:
        return LocalTelemetrySummary(
            sample_count=0,
            duration_ms=duration_ms,
            peak_browser_process_count=None,
            peak_browser_rss_bytes=None,
            peak_browser_cpu_percent=None,
            min_system_memory_available_bytes=None,
            peak_system_cpu_percent=None,
        )

    browser_cpu_values = [
        sample.browser_cpu_percent
        for sample in samples
        if sample.browser_cpu_percent is not None
    ]

    system_cpu_values = [
        sample.system_cpu_percent
        for sample in samples
        if sample.system_cpu_percent is not None
    ]

    return LocalTelemetrySummary(
        sample_count=len(samples),
        duration_ms=duration_ms,
        peak_browser_process_count=max(
            sample.browser_process_count
            for sample in samples
        ),
        peak_browser_rss_bytes=max(
            sample.browser_rss_bytes
            for sample in samples
        ),
        peak_browser_cpu_percent=(
            max(browser_cpu_values)
            if browser_cpu_values
            else None
        ),
        min_system_memory_available_bytes=min(
            sample.system_memory_available_bytes
            for sample in samples
        ),
        peak_system_cpu_percent=(
            max(system_cpu_values)
            if system_cpu_values
            else None
        ),
    )


class TelemetrySession:
    """
    Sample local host telemetry during one Consumer Probe.

    The session observes only local host/process metrics. It does not
    inspect browser DOM, response content, cookies, or network payloads.
    """

    def __init__(
        self,
        *,
        sample_interval_seconds: float = 0.25,
        capture: Callable[
            [],
            LocalTelemetrySnapshot,
        ] = capture_local_telemetry,
        clock_ticks_per_second: int | None = None,
    ) -> None:
        if sample_interval_seconds <= 0:
            raise ValueError(
                "sample_interval_seconds must be positive."
            )

        self.sample_interval_seconds = (
            sample_interval_seconds
        )
        self.capture = capture
        self.clock_ticks_per_second = (
            clock_ticks_per_second
        )

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self._started_at_utc: datetime | None = None
        self._initial_monotonic_ns: int | None = None
        self._previous_snapshot: (
            LocalTelemetrySnapshot | None
        ) = None

        self._samples: list[
            LocalTelemetrySample
        ] = []

        self._error: Exception | None = None

    @property
    def running(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
        )

    def start(self) -> None:
        if self.running:
            raise RuntimeError(
                "Telemetry session is already running."
            )

        self._stop_event.clear()
        self._samples = []
        self._error = None

        initial = self.capture()

        self._started_at_utc = (
            initial.captured_at_utc
        )
        self._initial_monotonic_ns = (
            initial.monotonic_ns
        )
        self._previous_snapshot = initial

        self._thread = threading.Thread(
            target=self._run,
            name="dllo-local-telemetry",
            daemon=True,
        )
        self._thread.start()

    def _capture_sample(self) -> None:
        previous = self._previous_snapshot

        if previous is None:
            raise RuntimeError(
                "Telemetry session has no initial snapshot."
            )

        current = self.capture()

        sample = derive_local_telemetry_sample(
            previous,
            current,
            clock_ticks_per_second=(
                self.clock_ticks_per_second
            ),
        )

        self._samples.append(sample)
        self._previous_snapshot = current

    def _run(self) -> None:
        try:
            while not self._stop_event.wait(
                self.sample_interval_seconds
            ):
                self._capture_sample()

        except Exception as exc:
            self._error = exc
            self._stop_event.set()

    def stop(self) -> TelemetrySessionResult:
        thread = self._thread

        if thread is None:
            raise RuntimeError(
                "Telemetry session has not been started."
            )

        self._stop_event.set()
        thread.join()

        if self._error is not None:
            raise LocalTelemetryUnavailableError(
                "Local telemetry session failed."
            ) from self._error

        # Capture the end of the probe even when it falls between
        # periodic sampling intervals.
        self._capture_sample()

        final_snapshot = self._previous_snapshot

        if (
            final_snapshot is None
            or self._started_at_utc is None
            or self._initial_monotonic_ns is None
        ):
            raise RuntimeError(
                "Telemetry session state is incomplete."
            )

        duration_ms = (
            final_snapshot.monotonic_ns
            - self._initial_monotonic_ns
        ) / 1_000_000

        stopped_at_utc = datetime.now(
            timezone.utc
        )

        samples = tuple(self._samples)

        self._thread = None

        return TelemetrySessionResult(
            started_at_utc=self._started_at_utc,
            stopped_at_utc=stopped_at_utc,
            samples=samples,
            summary=summarize_local_telemetry(
                list(samples),
                duration_ms=duration_ms,
            ),
        )
