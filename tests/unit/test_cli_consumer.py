from datetime import datetime, timezone
from pathlib import Path

import pytest

from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
)
from consumer_probe.storage.sqlite import (
    ConsumerProbeSQLiteStore,
)
from observer.cli import (
    build_parser,
    consumer_detect,
    consumer_summary,
    parse_candidate_start,
)


def make_record(
    *,
    hour: int = 21,
    ttfo: float = 1200,
    latency: float = 3000,
) -> ConsumerProbeRecord:
    timestamp = datetime(
        2026,
        8,
        19,
        hour,
        0,
        tzinfo=timezone.utc,
    )

    return ConsumerProbeRecord(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        platform=ConsumerPlatform.CHATGPT,
        page_hostname="chatgpt.com",
        benchmark_version="0.1",
        prompt_id="reasoning-001",
        started_at_utc=timestamp,
        first_output_at_utc=timestamp,
        completed_at_utc=timestamp,
        time_to_first_output_ms=ttfo,
        total_latency_ms=latency,
    )


def test_parser_exposes_consumer_commands():
    parser = build_parser()

    for command in (
        "consumer-import",
        "consumer-summary",
        "consumer-detect",
    ):
        args = parser.parse_args(
            
                [command]
                if command == "consumer-summary"
                else (
                    [
                        command,
                        "sample.json",
                    ]
                    if command == "consumer-import"
                    else [
                        command,
                        "--candidate-start",
                        "2026-08-19T20:00:00Z",
                        "--platform",
                        "chatgpt",
                        "--region-code",
                        "CL-Los-Lagos",
                        "--prompt-id",
                        "reasoning-001",
                    ]
                )
            
        )

        assert args.command == command


def test_parse_candidate_start_accepts_z():
    value = parse_candidate_start(
        "2026-08-19T20:00:00Z"
    )

    assert value == datetime(
        2026,
        8,
        19,
        20,
        0,
        tzinfo=timezone.utc,
    )


def test_parse_candidate_start_rejects_naive_datetime():
    with pytest.raises(
        ValueError,
        match="include UTC timezone",
    ):
        parse_candidate_start(
            "2026-08-19T20:00:00"
        )


def test_consumer_summary_reads_sqlite(
    tmp_path: Path,
    capsys,
):
    path = tmp_path / "consumer.db"

    store = ConsumerProbeSQLiteStore(path)
    store.append(make_record())

    parser = build_parser()
    args = parser.parse_args(
        [
            "consumer-summary",
            "--storage",
            str(path),
        ]
    )

    result = consumer_summary(args)

    output = capsys.readouterr().out

    assert result == 0
    assert "Samples:          1" in output
    assert "Median TTFO:" in output
    assert "1200.00 ms" in output
    assert "3000.00 ms" in output


def test_consumer_detect_reports_insufficient_data(
    tmp_path: Path,
    capsys,
):
    path = tmp_path / "consumer.db"

    store = ConsumerProbeSQLiteStore(path)
    store.append(make_record())

    parser = build_parser()
    args = parser.parse_args(
        [
            "consumer-detect",
            "--candidate-start",
            "2026-08-19T20:00:00Z",
            "--platform",
            "chatgpt",
            "--region-code",
            "CL-Los-Lagos",
            "--prompt-id",
            "reasoning-001",
            "--storage",
            str(path),
        ]
    )

    result = consumer_detect(args)

    output = capsys.readouterr().out

    assert result == 0
    assert "Candidate samples: 1" in output
    assert "Baseline samples:  0" in output
    assert "insufficient_data" in output
