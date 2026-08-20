from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PROC_ROOT = Path("/proc")

DEFAULT_BROWSER_PROCESS_NAMES = frozenset(
    {
        "firefox",
        "firefox-bin",
    }
)


@dataclass(frozen=True)
class LocalTelemetrySnapshot:
    captured_at_utc: datetime
    monotonic_ns: int

    browser_process_count: int
    browser_rss_bytes: int
    browser_cpu_ticks: int

    system_memory_available_bytes: int
    system_cpu_total_ticks: int
    system_cpu_idle_ticks: int


@dataclass(frozen=True)
class LocalTelemetrySample:
    captured_at_utc: datetime
    interval_ms: float

    browser_process_count: int
    browser_rss_bytes: int
    browser_cpu_percent: float | None

    system_memory_available_bytes: int
    system_cpu_percent: float | None


class LocalTelemetryUnavailableError(RuntimeError):
    """Raised when host telemetry cannot be collected."""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(
            encoding="utf-8"
        )
    except (
        OSError,
        UnicodeDecodeError,
    ) as exc:
        raise LocalTelemetryUnavailableError(
            f"Unable to read local telemetry source: {path}"
        ) from exc


def _read_system_cpu(
    proc_root: Path,
) -> tuple[int, int]:
    first_line = _read_text(
        proc_root / "stat"
    ).splitlines()[0]

    parts = first_line.split()

    if not parts or parts[0] != "cpu":
        raise LocalTelemetryUnavailableError(
            "Invalid /proc/stat CPU data."
        )

    try:
        counters = [
            int(value)
            for value in parts[1:]
        ]
    except ValueError as exc:
        raise LocalTelemetryUnavailableError(
            "Invalid /proc/stat CPU counters."
        ) from exc

    if len(counters) < 4:
        raise LocalTelemetryUnavailableError(
            "Incomplete /proc/stat CPU data."
        )

    total_ticks = sum(counters)

    idle_ticks = counters[3]

    if len(counters) >= 5:
        idle_ticks += counters[4]

    return total_ticks, idle_ticks


def _read_available_memory(
    proc_root: Path,
) -> int:
    for line in _read_text(
        proc_root / "meminfo"
    ).splitlines():
        if not line.startswith(
            "MemAvailable:"
        ):
            continue

        parts = line.split()

        if len(parts) < 2:
            break

        try:
            return int(parts[1]) * 1024
        except ValueError as exc:
            raise LocalTelemetryUnavailableError(
                "Invalid MemAvailable value."
            ) from exc

    raise LocalTelemetryUnavailableError(
        "MemAvailable not found in /proc/meminfo."
    )


def _read_process_name(
    process_root: Path,
) -> str | None:
    try:
        return (
            process_root
            .joinpath("comm")
            .read_text(
                encoding="utf-8"
            )
            .strip()
        )
    except (
        OSError,
        UnicodeDecodeError,
    ):
        return None


def _read_process_rss_bytes(
    process_root: Path,
) -> int | None:
    try:
        lines = (
            process_root
            .joinpath("status")
            .read_text(
                encoding="utf-8"
            )
            .splitlines()
        )
    except (
        OSError,
        UnicodeDecodeError,
    ):
        return None

    for line in lines:
        if not line.startswith("VmRSS:"):
            continue

        parts = line.split()

        if len(parts) < 2:
            return None

        try:
            return int(parts[1]) * 1024
        except ValueError:
            return None

    return None


def _read_process_stat_fields(
    process_root: Path,
) -> list[str] | None:
    try:
        raw = (
            process_root
            .joinpath("stat")
            .read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        UnicodeDecodeError,
    ):
        return None

    closing_parenthesis = raw.rfind(")")

    if closing_parenthesis < 0:
        return None

    return raw[
        closing_parenthesis + 1:
    ].split()


def _read_process_ppid(
    process_root: Path,
) -> int | None:
    fields = _read_process_stat_fields(
        process_root
    )

    # After removing pid and "(comm)",
    # fields[0] is /proc stat field 3 (state)
    # fields[1] is field 4 (ppid).
    if fields is None or len(fields) <= 1:
        return None

    try:
        return int(fields[1])
    except ValueError:
        return None


def _read_process_cpu_ticks(
    process_root: Path,
) -> int | None:
    fields = _read_process_stat_fields(
        process_root
    )

    if fields is None:
        return None

    # After removing pid and "(comm)",
    # fields[0] is Linux /proc stat field 3.
    #
    # utime = field 14 -> index 11
    # stime = field 15 -> index 12
    if len(fields) <= 12:
        return None

    try:
        user_ticks = int(fields[11])
        system_ticks = int(fields[12])
    except ValueError:
        return None

    return user_ticks + system_ticks


def _read_browser_totals(
    proc_root: Path,
    process_names: frozenset[str],
) -> tuple[int, int, int]:
    """
    Aggregate the complete process tree rooted at the browser.

    Firefox uses multiple child processes whose ``comm`` value may
    differ from ``firefox``. Root processes are identified by name,
    then all descendants are followed through /proc PPID relations.
    """
    try:
        entries = list(
            proc_root.iterdir()
        )
    except OSError as exc:
        raise LocalTelemetryUnavailableError(
            f"Unable to enumerate {proc_root}."
        ) from exc

    process_table: dict[
        int,
        tuple[
            int | None,
            str | None,
            int,
            int,
        ],
    ] = {}

    root_pids: set[int] = set()

    for process_root in entries:
        if not process_root.name.isdigit():
            continue

        pid = int(process_root.name)

        name = _read_process_name(
            process_root
        )

        ppid = _read_process_ppid(
            process_root
        )

        rss = (
            _read_process_rss_bytes(
                process_root
            )
            or 0
        )

        cpu_ticks = (
            _read_process_cpu_ticks(
                process_root
            )
            or 0
        )

        process_table[pid] = (
            ppid,
            name,
            rss,
            cpu_ticks,
        )

        if name in process_names:
            root_pids.add(pid)

    if not root_pids:
        return (0, 0, 0)

    browser_pids = set(
        root_pids
    )

    changed = True

    while changed:
        changed = False

        for pid, process in process_table.items():
            ppid = process[0]

            if (
                pid in browser_pids
                or ppid not in browser_pids
            ):
                continue

            browser_pids.add(pid)
            changed = True

    rss_bytes = 0
    cpu_ticks = 0

    for pid in browser_pids:
        process = process_table.get(
            pid
        )

        if process is None:
            continue

        rss_bytes += process[2]
        cpu_ticks += process[3]

    return (
        len(browser_pids),
        rss_bytes,
        cpu_ticks,
    )


def capture_local_telemetry(
    *,
    proc_root: Path = DEFAULT_PROC_ROOT,
    process_names: frozenset[str] = (
        DEFAULT_BROWSER_PROCESS_NAMES
    ),
) -> LocalTelemetrySnapshot:
    if not proc_root.exists():
        raise LocalTelemetryUnavailableError(
            f"Linux proc filesystem unavailable: {proc_root}"
        )

    (
        browser_process_count,
        browser_rss_bytes,
        browser_cpu_ticks,
    ) = _read_browser_totals(
        proc_root,
        process_names,
    )

    (
        system_cpu_total_ticks,
        system_cpu_idle_ticks,
    ) = _read_system_cpu(
        proc_root
    )

    return LocalTelemetrySnapshot(
        captured_at_utc=datetime.now(
            timezone.utc
        ),
        monotonic_ns=time.monotonic_ns(),
        browser_process_count=(
            browser_process_count
        ),
        browser_rss_bytes=browser_rss_bytes,
        browser_cpu_ticks=browser_cpu_ticks,
        system_memory_available_bytes=(
            _read_available_memory(
                proc_root
            )
        ),
        system_cpu_total_ticks=(
            system_cpu_total_ticks
        ),
        system_cpu_idle_ticks=(
            system_cpu_idle_ticks
        ),
    )


def derive_local_telemetry_sample(
    previous: LocalTelemetrySnapshot,
    current: LocalTelemetrySnapshot,
    *,
    clock_ticks_per_second: int | None = None,
) -> LocalTelemetrySample:
    elapsed_ns = (
        current.monotonic_ns
        - previous.monotonic_ns
    )

    if elapsed_ns <= 0:
        raise ValueError(
            "Telemetry snapshots must be "
            "monotonically ordered."
        )

    elapsed_seconds = (
        elapsed_ns / 1_000_000_000
    )

    ticks_per_second = (
        clock_ticks_per_second
        if clock_ticks_per_second is not None
        else int(
            os.sysconf(
                "SC_CLK_TCK"
            )
        )
    )

    browser_tick_delta = (
        current.browser_cpu_ticks
        - previous.browser_cpu_ticks
    )

    browser_cpu_percent = None

    if browser_tick_delta >= 0:
        browser_cpu_percent = (
            browser_tick_delta
            / ticks_per_second
            / elapsed_seconds
            * 100
        )

    system_total_delta = (
        current.system_cpu_total_ticks
        - previous.system_cpu_total_ticks
    )

    system_idle_delta = (
        current.system_cpu_idle_ticks
        - previous.system_cpu_idle_ticks
    )

    system_cpu_percent = None

    if (
        system_total_delta > 0
        and 0 <= system_idle_delta
        <= system_total_delta
    ):
        system_cpu_percent = (
            (
                system_total_delta
                - system_idle_delta
            )
            / system_total_delta
            * 100
        )

    return LocalTelemetrySample(
        captured_at_utc=current.captured_at_utc,
        interval_ms=(
            elapsed_seconds * 1000
        ),
        browser_process_count=(
            current.browser_process_count
        ),
        browser_rss_bytes=(
            current.browser_rss_bytes
        ),
        browser_cpu_percent=(
            browser_cpu_percent
        ),
        system_memory_available_bytes=(
            current.system_memory_available_bytes
        ),
        system_cpu_percent=(
            system_cpu_percent
        ),
    )
