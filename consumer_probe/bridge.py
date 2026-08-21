from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from consumer_probe.due import (
    find_due_probe,
    find_next_probe,
)
from consumer_probe.local_telemetry import (
    LocalTelemetryUnavailableError,
)
from consumer_probe.sampling import SamplingPolicy
from consumer_probe.schemas import ConsumerPlatform
from consumer_probe.storage.sqlite import ConsumerProbeSQLiteStore
from consumer_probe.telemetry_registry import (
    TelemetrySessionConflictError,
    TelemetrySessionNotFoundError,
    TelemetrySessionRegistry,
)
from observer.core.consumer_schedule import build_prompt_bank_schedule


@dataclass(frozen=True)
class BridgeConfig:
    observer_id: str
    platform: ConsumerPlatform
    benchmark_version: str = "0.1"
    prompt_bank_path: Path = Path("benchmark/prompts")
    storage_path: Path = Path("data/consumer-probes.db")
    bucket_hours: int = 4
    samples_per_bucket: int = 1
    edge_guard_minutes: int = 15
    grace_minutes: int = 60


def completed_prompt_ids_for_day(
    config: BridgeConfig,
    sampling_date,
) -> set[str]:
    store = ConsumerProbeSQLiteStore(
        config.storage_path
    )

    completed: set[str] = set()

    for record in store.load_all():
        if record.observer_id != config.observer_id:
            continue

        if record.platform != config.platform:
            continue

        if (
            record.benchmark_version
            != config.benchmark_version
        ):
            continue

        if (
            record.started_at_utc
            .astimezone(timezone.utc)
            .date()
            != sampling_date
        ):
            continue

        if record.generation_failed:
            continue

        if record.interrupted:
            continue

        if record.completed_at_utc is None:
            continue

        completed.add(record.prompt_id)

    return completed


def build_next_payload(
    config: BridgeConfig,
    *,
    now_utc: datetime,
) -> dict:
    if now_utc.tzinfo is None:
        raise ValueError(
            "now_utc must be timezone-aware."
        )

    now = now_utc.astimezone(timezone.utc)
    sampling_date = now.date()

    policy = SamplingPolicy(
        bucket_hours=config.bucket_hours,
        samples_per_bucket=config.samples_per_bucket,
        edge_guard_minutes=config.edge_guard_minutes,
    )

    schedule = build_prompt_bank_schedule(
        sampling_date,
        observer_id=config.observer_id,
        benchmark_version=config.benchmark_version,
        prompt_bank_path=config.prompt_bank_path,
        sampling_policy=policy,
    )

    completed = completed_prompt_ids_for_day(
        config,
        sampling_date,
    )

    due = find_due_probe(
        schedule,
        now_utc=now,
        completed_prompt_ids=completed,
        grace_minutes=config.grace_minutes,
    )

    upcoming = None

    if due is None:
        upcoming = find_next_probe(
            schedule,
            now_utc=now,
            completed_prompt_ids=completed,
        )

    if due is not None:
        item = due.item

        status = "due"
        item_payload = {
            "scheduled_at_utc": (
                item.scheduled_at_utc.isoformat()
            ),
            "prompt_id": item.benchmark.prompt_id,
            "category": item.benchmark.category.value,
            "prompt": item.benchmark.prompt,
            "overdue_by_ms": round(
                due.overdue_by.total_seconds()
                * 1000
            ),
        }

    elif upcoming is not None:
        status = "upcoming"

        starts_in = (
            upcoming.scheduled_at_utc
            - now
        )

        item_payload = {
            "scheduled_at_utc": (
                upcoming.scheduled_at_utc.isoformat()
            ),
            "prompt_id": upcoming.benchmark.prompt_id,
            "category": (
                upcoming.benchmark.category.value
            ),
            "prompt": upcoming.benchmark.prompt,
            "starts_in_ms": round(
                starts_in.total_seconds()
                * 1000
            ),
        }

    else:
        status = "none"
        item_payload = None

    return {
        "schema_version": "0.1",
        "status": status,
        "now_utc": now.isoformat(),
        "schedule_date": sampling_date.isoformat(),
        "observer_id": config.observer_id,
        "platform": config.platform.value,
        "benchmark_version": (
            config.benchmark_version
        ),
        "completed_today": len(completed),
        "item": item_payload,
    }


def make_handler(
    config: BridgeConfig,
    telemetry_registry: TelemetrySessionRegistry | None = None,
    *,
    collector_static_root: Path | None = None,
):
    registry = (
        telemetry_registry
        if telemetry_registry is not None
        else TelemetrySessionRegistry()
    )

    collector_root = (
        collector_static_root.resolve()
        if collector_static_root is not None
        else None
    )

    class BridgeHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)

            if parsed.path == "/health":
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "service": "dllo-consumer-bridge",
                    },
                )
                return

            if parsed.path == "/v1/next":
                self._handle_next(parsed.query)
                return

            if (
                parsed.path == "/"
                and collector_root is not None
            ):
                self._send_collector_index()
                return

            if (
                parsed.path.startswith("/assets/")
                and collector_root is not None
            ):
                self._send_collector_asset(
                    parsed.path,
                )
                return

            self._send_json(
                404,
                {
                    "error": "not_found",
                },
            )

        def do_POST(self) -> None:
            parsed = urlparse(self.path)

            if parsed.path == "/v1/telemetry/start":
                self._handle_telemetry_action(
                    "start"
                )
                return

            if parsed.path == "/v1/telemetry/stop":
                self._handle_telemetry_action(
                    "stop"
                )
                return

            if parsed.path == "/v1/telemetry/cancel":
                self._handle_telemetry_action(
                    "cancel"
                )
                return

            self._send_json(
                404,
                {
                    "error": "not_found",
                },
            )

        def _read_json_body(
            self,
        ) -> dict:
            raw_length = self.headers.get(
                "Content-Length"
            )

            if raw_length is None:
                raise ValueError(
                    "Content-Length is required."
                )

            try:
                length = int(raw_length)
            except ValueError as exc:
                raise ValueError(
                    "Invalid Content-Length."
                ) from exc

            if length <= 0:
                raise ValueError(
                    "Request body is required."
                )

            if length > 4096:
                raise ValueError(
                    "Request body is too large."
                )

            raw_body = self.rfile.read(
                length
            )

            try:
                payload = json.loads(
                    raw_body.decode("utf-8")
                )
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
            ) as exc:
                raise ValueError(
                    "Invalid JSON request body."
                ) from exc

            if not isinstance(
                payload,
                dict,
            ):
                raise ValueError(
                    "JSON request body must be an object."
                )

            return payload

        def _handle_telemetry_action(
            self,
            action: str,
        ) -> None:
            try:
                payload = (
                    self._read_json_body()
                )

                probe_id = payload.get(
                    "probe_id"
                )

                if not isinstance(
                    probe_id,
                    str,
                ):
                    raise ValueError(
                        "probe_id is required."
                    )

                if action == "start":
                    response = registry.start(
                        probe_id
                    )
                    status = 201

                elif action == "stop":
                    response = registry.stop(
                        probe_id
                    )
                    status = 200

                elif action == "cancel":
                    response = registry.cancel(
                        probe_id
                    )
                    status = 200

                else:
                    raise ValueError(
                        "Unknown telemetry action."
                    )

                self._send_json(
                    status,
                    response,
                )

            except ValueError as exc:
                self._send_json(
                    400,
                    {
                        "error": "bad_request",
                        "message": str(exc),
                    },
                )

            except TelemetrySessionConflictError as exc:
                self._send_json(
                    409,
                    {
                        "error": "session_conflict",
                        "message": str(exc),
                    },
                )

            except TelemetrySessionNotFoundError as exc:
                self._send_json(
                    404,
                    {
                        "error": "session_not_found",
                        "message": str(exc),
                    },
                )

            except LocalTelemetryUnavailableError as exc:
                self._send_json(
                    503,
                    {
                        "error": "telemetry_unavailable",
                        "message": str(exc),
                    },
                )

        def _handle_next(
            self,
            raw_query: str,
        ) -> None:
            try:
                query = parse_qs(raw_query)
                raw_now = query.get("now", [None])[0]

                if raw_now is None:
                    now = datetime.now(
                        timezone.utc
                    )
                else:
                    normalized = raw_now

                    if normalized.endswith("Z"):
                        normalized = (
                            normalized[:-1]
                            + "+00:00"
                        )

                    now = datetime.fromisoformat(
                        normalized
                    )

                payload = build_next_payload(
                    config,
                    now_utc=now,
                )

                self._send_json(
                    200,
                    payload,
                )

            except (
                ValueError,
                OSError,
            ) as exc:
                self._send_json(
                    400,
                    {
                        "error": "bad_request",
                        "message": str(exc),
                    },
                )

        def _send_collector_asset(
            self,
            request_path: str,
        ) -> None:
            assert collector_root is not None

            relative_path = request_path.lstrip("/")
            asset_path = (
                collector_root
                / relative_path
            ).resolve()

            if not asset_path.is_relative_to(
                collector_root
            ):
                self._send_json(
                    404,
                    {
                        "error": "not_found",
                    },
                )
                return

            if not asset_path.is_file():
                self._send_json(
                    404,
                    {
                        "error": "not_found",
                    },
                )
                return

            try:
                body = asset_path.read_bytes()
            except OSError:
                self._send_json(
                    404,
                    {
                        "error": "not_found",
                    },
                )
                return

            content_type, _ = mimetypes.guess_type(
                asset_path.name
            )

            self.send_response(200)
            self.send_header(
                "Content-Type",
                content_type
                or "application/octet-stream",
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

        def _send_collector_index(self) -> None:
            assert collector_root is not None

            index_path = collector_root / "index.html"

            try:
                body = index_path.read_bytes()
            except OSError:
                self._send_json(
                    404,
                    {
                        "error": "collector_not_found",
                    },
                )
                return

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
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

    return BridgeHandler


def serve(
    config: BridgeConfig,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    collector_static_root: Path | None = None,
) -> None:
    if host not in {
        "127.0.0.1",
        "::1",
        "localhost",
    }:
        raise ValueError(
            "Consumer bridge may only bind to localhost."
        )

    server = ThreadingHTTPServer(
        (host, port),
        make_handler(
            config,
            collector_static_root=collector_static_root,
        ),
    )

    print(
        f"DLLO Consumer Bridge listening on "
        f"http://{host}:{port}"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
