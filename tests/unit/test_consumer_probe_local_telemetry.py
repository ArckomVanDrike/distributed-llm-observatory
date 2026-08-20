from datetime import datetime, timezone
from pathlib import Path

import pytest

from consumer_probe.local_telemetry import (
    LocalTelemetrySnapshot,
    capture_local_telemetry,
    derive_local_telemetry_sample,
)


def make_process(
    proc_root: Path,
    *,
    pid: int,
    name: str,
    rss_kb: int,
    user_ticks: int,
    system_ticks: int,
    pss_kb: int | None = None,
) -> None:
    root = proc_root / str(pid)
    root.mkdir()

    (root / "comm").write_text(
        f"{name}\n",
        encoding="utf-8",
    )

    (root / "status").write_text(
        f"Name:\t{name}\n"
        f"VmRSS:\t{rss_kb} kB\n",
        encoding="utf-8",
    )

    if pss_kb is not None:
        (root / "smaps_rollup").write_text(
            f"Rss:\t{rss_kb} kB\n"
            f"Pss:\t{pss_kb} kB\n",
            encoding="utf-8",
        )

    fields = [
        str(pid),
        f"({name})",
        "S",
        *["0"] * 49,
    ]

    fields[13] = str(user_ticks)
    fields[14] = str(system_ticks)

    (root / "stat").write_text(
        " ".join(fields),
        encoding="utf-8",
    )


def make_proc_root(
    tmp_path: Path,
) -> Path:
    proc_root = tmp_path / "proc"
    proc_root.mkdir()

    (proc_root / "stat").write_text(
        "cpu 100 10 50 800 40 0 0 0 0 0\n",
        encoding="utf-8",
    )

    (proc_root / "meminfo").write_text(
        "MemTotal:       8000000 kB\n"
        "MemAvailable:   3000000 kB\n",
        encoding="utf-8",
    )

    return proc_root


def test_capture_aggregates_firefox_processes(
    tmp_path: Path,
):
    proc_root = make_proc_root(
        tmp_path
    )

    make_process(
        proc_root,
        pid=100,
        name="firefox",
        rss_kb=1000,
        user_ticks=100,
        system_ticks=20,
    )

    make_process(
        proc_root,
        pid=101,
        name="firefox",
        rss_kb=2000,
        user_ticks=50,
        system_ticks=10,
    )

    make_process(
        proc_root,
        pid=200,
        name="python",
        rss_kb=9000,
        user_ticks=900,
        system_ticks=900,
    )

    snapshot = capture_local_telemetry(
        proc_root=proc_root
    )

    assert (
        snapshot.browser_process_count
        == 2
    )

    assert (
        snapshot.browser_rss_bytes
        == 3000 * 1024
    )

    assert (
        snapshot.browser_cpu_ticks
        == 180
    )

    assert (
        snapshot.system_memory_available_bytes
        == 3000000 * 1024
    )


def test_capture_reads_system_cpu_counters(
    tmp_path: Path,
):
    proc_root = make_proc_root(
        tmp_path
    )

    snapshot = capture_local_telemetry(
        proc_root=proc_root
    )

    assert (
        snapshot.system_cpu_total_ticks
        == 1000
    )

    assert (
        snapshot.system_cpu_idle_ticks
        == 840
    )


def test_derive_calculates_browser_cpu():
    now = datetime(
        2026,
        8,
        20,
        tzinfo=timezone.utc,
    )

    previous = LocalTelemetrySnapshot(
        captured_at_utc=now,
        monotonic_ns=1_000_000_000,
        browser_process_count=5,
        browser_rss_bytes=100,
        browser_pss_bytes=None,
        browser_cpu_ticks=100,
        system_memory_available_bytes=1000,
        system_cpu_total_ticks=1000,
        system_cpu_idle_ticks=800,
    )

    current = LocalTelemetrySnapshot(
        captured_at_utc=now,
        monotonic_ns=2_000_000_000,
        browser_process_count=5,
        browser_rss_bytes=200,
        browser_pss_bytes=None,
        browser_cpu_ticks=150,
        system_memory_available_bytes=900,
        system_cpu_total_ticks=1100,
        system_cpu_idle_ticks=850,
    )

    sample = derive_local_telemetry_sample(
        previous,
        current,
        clock_ticks_per_second=100,
    )

    assert (
        sample.browser_cpu_percent
        == pytest.approx(50.0)
    )

    assert (
        sample.system_cpu_percent
        == pytest.approx(50.0)
    )

    assert sample.interval_ms == 1000
    assert sample.browser_rss_bytes == 200


def test_browser_cpu_can_exceed_100_percent():
    now = datetime(
        2026,
        8,
        20,
        tzinfo=timezone.utc,
    )

    previous = LocalTelemetrySnapshot(
        captured_at_utc=now,
        monotonic_ns=0,
        browser_process_count=4,
        browser_rss_bytes=0,
        browser_pss_bytes=None,
        browser_cpu_ticks=0,
        system_memory_available_bytes=0,
        system_cpu_total_ticks=0,
        system_cpu_idle_ticks=0,
    )

    current = LocalTelemetrySnapshot(
        captured_at_utc=now,
        monotonic_ns=1_000_000_000,
        browser_process_count=4,
        browser_rss_bytes=0,
        browser_pss_bytes=None,
        browser_cpu_ticks=250,
        system_memory_available_bytes=0,
        system_cpu_total_ticks=100,
        system_cpu_idle_ticks=50,
    )

    sample = derive_local_telemetry_sample(
        previous,
        current,
        clock_ticks_per_second=100,
    )

    assert (
        sample.browser_cpu_percent
        == pytest.approx(250.0)
    )


def test_non_monotonic_snapshots_are_rejected():
    now = datetime(
        2026,
        8,
        20,
        tzinfo=timezone.utc,
    )

    snapshot = LocalTelemetrySnapshot(
        captured_at_utc=now,
        monotonic_ns=100,
        browser_process_count=0,
        browser_rss_bytes=0,
        browser_pss_bytes=None,
        browser_cpu_ticks=0,
        system_memory_available_bytes=0,
        system_cpu_total_ticks=0,
        system_cpu_idle_ticks=0,
    )

    with pytest.raises(
        ValueError,
        match="monotonically",
    ):
        derive_local_telemetry_sample(
            snapshot,
            snapshot,
        )


def test_capture_includes_firefox_descendants(
    tmp_path: Path,
):
    proc_root = make_proc_root(
        tmp_path
    )

    make_process(
        proc_root,
        pid=100,
        name="firefox",
        rss_kb=1000,
        user_ticks=100,
        system_ticks=20,
    )

    make_process(
        proc_root,
        pid=101,
        name="Web Content",
        rss_kb=2000,
        user_ticks=50,
        system_ticks=10,
    )

    make_process(
        proc_root,
        pid=102,
        name="Socket Process",
        rss_kb=500,
        user_ticks=25,
        system_ticks=5,
    )

    make_process(
        proc_root,
        pid=200,
        name="python",
        rss_kb=9000,
        user_ticks=900,
        system_ticks=900,
    )

    # Rewrite PPIDs in the synthetic stat files.
    def set_ppid(
        pid: int,
        ppid: int,
    ) -> None:
        path = (
            proc_root
            / str(pid)
            / "stat"
        )

        raw = path.read_text(
            encoding="utf-8"
        )

        closing = raw.rfind(")")
        prefix = raw[: closing + 1]
        fields = raw[
            closing + 1:
        ].split()

        # fields[0] = state
        # fields[1] = ppid
        fields[1] = str(ppid)

        path.write_text(
            prefix
            + " "
            + " ".join(fields),
            encoding="utf-8",
        )

    set_ppid(100, 1)
    set_ppid(101, 100)
    set_ppid(102, 101)
    set_ppid(200, 1)

    snapshot = capture_local_telemetry(
        proc_root=proc_root
    )

    assert (
        snapshot.browser_process_count
        == 3
    )

    assert (
        snapshot.browser_rss_bytes
        == 3500 * 1024
    )

    assert (
        snapshot.browser_cpu_ticks
        == 210
    )


def test_capture_excludes_unrelated_process_tree(
    tmp_path: Path,
):
    proc_root = make_proc_root(
        tmp_path
    )

    make_process(
        proc_root,
        pid=100,
        name="firefox",
        rss_kb=1000,
        user_ticks=10,
        system_ticks=5,
    )

    make_process(
        proc_root,
        pid=200,
        name="python",
        rss_kb=5000,
        user_ticks=100,
        system_ticks=100,
    )

    make_process(
        proc_root,
        pid=201,
        name="worker",
        rss_kb=7000,
        user_ticks=200,
        system_ticks=200,
    )

    def set_ppid(
        pid: int,
        ppid: int,
    ) -> None:
        path = (
            proc_root
            / str(pid)
            / "stat"
        )

        raw = path.read_text(
            encoding="utf-8"
        )

        closing = raw.rfind(")")
        prefix = raw[: closing + 1]
        fields = raw[
            closing + 1:
        ].split()

        fields[1] = str(ppid)

        path.write_text(
            prefix
            + " "
            + " ".join(fields),
            encoding="utf-8",
        )

    set_ppid(100, 1)
    set_ppid(200, 1)
    set_ppid(201, 200)

    snapshot = capture_local_telemetry(
        proc_root=proc_root
    )

    assert snapshot.browser_process_count == 1

    assert (
        snapshot.browser_rss_bytes
        == 1000 * 1024
    )


def test_capture_aggregates_complete_browser_pss(
    tmp_path: Path,
):
    proc_root = make_proc_root(
        tmp_path
    )

    make_process(
        proc_root,
        pid=100,
        name="firefox",
        rss_kb=1000,
        pss_kb=700,
        user_ticks=10,
        system_ticks=5,
    )

    make_process(
        proc_root,
        pid=101,
        name="firefox",
        rss_kb=2000,
        pss_kb=1300,
        user_ticks=20,
        system_ticks=10,
    )

    snapshot = capture_local_telemetry(
        proc_root=proc_root
    )

    assert (
        snapshot.browser_pss_bytes
        == 2000 * 1024
    )


def test_capture_rejects_partial_browser_pss(
    tmp_path: Path,
):
    proc_root = make_proc_root(
        tmp_path
    )

    make_process(
        proc_root,
        pid=100,
        name="firefox",
        rss_kb=1000,
        pss_kb=700,
        user_ticks=10,
        system_ticks=5,
    )

    # Deliberately has no smaps_rollup/PSS.
    make_process(
        proc_root,
        pid=101,
        name="firefox",
        rss_kb=2000,
        user_ticks=20,
        system_ticks=10,
    )

    snapshot = capture_local_telemetry(
        proc_root=proc_root
    )

    assert snapshot.browser_pss_bytes is None
