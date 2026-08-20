from __future__ import annotations

import threading
from collections.abc import Callable
from uuid import UUID

from consumer_probe.telemetry_session import (
    TelemetrySession,
    TelemetrySessionResult,
)


class TelemetrySessionConflictError(RuntimeError):
    """Raised when a probe already has an active telemetry session."""


class TelemetrySessionNotFoundError(RuntimeError):
    """Raised when no active telemetry session exists for a probe."""


def normalize_probe_id(probe_id: str) -> str:
    try:
        return str(UUID(probe_id))
    except ValueError as exc:
        raise ValueError(
            "probe_id must be a valid UUID."
        ) from exc


def telemetry_result_payload(
    probe_id: str,
    result: TelemetrySessionResult,
) -> dict:
    summary = result.summary
    provenance = result.provenance

    return {
        "telemetry_schema_version": "0.2",
        "probe_id": probe_id,
        "started_at_utc": (
            result.started_at_utc.isoformat()
        ),
        "stopped_at_utc": (
            result.stopped_at_utc.isoformat()
        ),
        "sample_count": summary.sample_count,
        "duration_ms": summary.duration_ms,
        "collector_version": (
            provenance.collector_version
        ),
        "browser_scope": (
            provenance.browser_scope
        ),
        "memory_method": (
            provenance.memory_method
        ),
        "fast_interval_target_ms": (
            provenance.fast_interval_target_ms
        ),
        "pss_interval_target_ms": (
            provenance.pss_interval_target_ms
        ),
        "peak_browser_process_count": (
            summary.peak_browser_process_count
        ),
        "peak_browser_rss_bytes": (
            summary.peak_browser_rss_bytes
        ),
        "peak_browser_pss_bytes": (
            summary.peak_browser_pss_bytes
        ),
        "pss_sample_count": (
            summary.pss_sample_count
        ),
        "peak_browser_cpu_percent": (
            summary.peak_browser_cpu_percent
        ),
        "min_system_memory_available_bytes": (
            summary.min_system_memory_available_bytes
        ),
        "peak_system_cpu_percent": (
            summary.peak_system_cpu_percent
        ),
    }


class TelemetrySessionRegistry:
    """
    Manage active local telemetry sessions keyed by browser probe UUID.
    """

    def __init__(
        self,
        *,
        session_factory: Callable[
            [],
            TelemetrySession,
        ] = TelemetrySession,
    ) -> None:
        self._session_factory = session_factory
        self._sessions: dict[
            str,
            TelemetrySession,
        ] = {}
        self._lock = threading.Lock()

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def start(
        self,
        probe_id: str,
    ) -> dict:
        normalized = normalize_probe_id(
            probe_id
        )

        with self._lock:
            if normalized in self._sessions:
                raise TelemetrySessionConflictError(
                    "Telemetry session already active "
                    f"for probe {normalized}."
                )

            session = self._session_factory()
            session.start()

            self._sessions[
                normalized
            ] = session

        return {
            "telemetry_schema_version": "0.2",
            "probe_id": normalized,
            "status": "running",
        }

    def stop(
        self,
        probe_id: str,
    ) -> dict:
        normalized = normalize_probe_id(
            probe_id
        )

        with self._lock:
            session = self._sessions.pop(
                normalized,
                None,
            )

        if session is None:
            raise TelemetrySessionNotFoundError(
                "No active telemetry session "
                f"for probe {normalized}."
            )

        result = session.stop()

        return telemetry_result_payload(
            normalized,
            result,
        )

    def cancel(
        self,
        probe_id: str,
    ) -> dict:
        normalized = normalize_probe_id(
            probe_id
        )

        with self._lock:
            session = self._sessions.pop(
                normalized,
                None,
            )

        if session is None:
            raise TelemetrySessionNotFoundError(
                "No active telemetry session "
                f"for probe {normalized}."
            )

        # Stop the sampling thread cleanly, but intentionally
        # discard the resulting metrics.
        session.stop()

        return {
            "telemetry_schema_version": "0.2",
            "probe_id": normalized,
            "status": "cancelled",
        }
