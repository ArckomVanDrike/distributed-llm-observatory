from datetime import date, datetime, timedelta, timezone
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
    consumer_next,
    consumer_schedule,
    consumer_summary,
    parse_candidate_start,
    parse_now_utc,
    parse_sampling_date,
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


def test_consumer_import_is_idempotent(
    tmp_path: Path,
    capsys,
):
    export_path = tmp_path / "export.json"
    storage_path = tmp_path / "consumer.db"

    export_path.write_text(
        """
        {
          "export_schema_version": "0.1",
          "exported_at_utc": "2026-08-19T21:17:38.814Z",
          "sample_count": 1,
          "records": [
            {
              "schema_version": "0.1",
              "probe_id": "bd8813fb-26bc-42ea-b04c-c4a9d0a5367e",
              "prompt_id": "reasoning-001",
              "benchmark_version": "0.1",
              "platform": "chatgpt",
              "page_hostname": "chatgpt.com",
              "started_at_ms": 1755638224881,
              "started_at_utc": "2026-08-19T21:17:04.881Z",
              "first_output_at_ms": 1755638227769,
              "first_output_at_utc": "2026-08-19T21:17:07.769Z",
              "completed_at_ms": 1755638229123,
              "completed_at_utc": "2026-08-19T21:17:09.123Z",
              "time_to_first_output_ms": 2888,
              "total_latency_ms": 4242,
              "generation_failed": false,
              "interrupted": false,
              "retry_observed": false,
              "response_capture_enabled": false,
              "response_text": null,
              "measurement_mode": "consumer-ui-manual-v0.1"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    parser = build_parser()

    args = parser.parse_args(
        [
            "consumer-import",
            str(export_path),
            "--storage",
            str(storage_path),
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
            "--observer-timezone",
            "America/Santiago",
        ]
    )

    from observer.cli import consumer_import

    first_result = consumer_import(args)
    first_output = capsys.readouterr().out

    second_result = consumer_import(args)
    second_output = capsys.readouterr().out

    assert first_result == 0
    assert "Inserted:   1" in first_output
    assert "Duplicates: 0" in first_output
    assert "DB total:   1" in first_output

    assert second_result == 0
    assert "Inserted:   0" in second_output
    assert "Duplicates: 1" in second_output
    assert "DB total:   1" in second_output



def test_parser_exposes_consumer_schedule():
    parser = build_parser()

    args = parser.parse_args(
        [
            "consumer-schedule",
            "--date",
            "2026-08-19",
            "--observer-id",
            "observer-test",
        ]
    )

    assert args.command == "consumer-schedule"
    assert args.sampling_date == "2026-08-19"
    assert args.observer_id == "observer-test"


def test_parse_sampling_date_accepts_iso_date():
    value = parse_sampling_date(
        "2026-08-19"
    )

    assert value.isoformat() == "2026-08-19"


def test_parse_sampling_date_rejects_invalid_date():
    with pytest.raises(
        ValueError,
        match="YYYY-MM-DD",
    ):
        parse_sampling_date(
            "19-08-2026"
        )


def test_consumer_schedule_uses_prompt_bank(
    tmp_path: Path,
    capsys,
):
    prompt_path = (
        tmp_path
        / "reasoning"
        / "reasoning-001.json"
    )

    prompt_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    prompt_path.write_text(
        """
        {
          "prompt_id": "reasoning-001",
          "benchmark_version": "0.1",
          "category": "reasoning",
          "difficulty": "medium",
          "prompt": "Return the number nine.",
          "expected_characteristics": [
            "Returns 9."
          ],
          "scoring_method": "observatory_rubric_v0.1",
          "enabled": true
        }
        """,
        encoding="utf-8",
    )

    parser = build_parser()

    args = parser.parse_args(
        [
            "consumer-schedule",
            "--date",
            "2026-08-19",
            "--observer-id",
            "observer-test",
            "--benchmark-version",
            "0.1",
            "--prompt-bank",
            str(tmp_path),
        ]
    )

    result = consumer_schedule(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "2026-08-19" in output
    assert "observer-test" in output
    assert "Scheduled items:   1" in output
    assert "reasoning-001" in output
    assert "[reasoning]" in output


def write_single_prompt_bank(
    root: Path,
) -> None:
    prompt_path = (
        root
        / "reasoning"
        / "reasoning-001.json"
    )

    prompt_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    prompt_path.write_text(
        """
        {
          "prompt_id": "reasoning-001",
          "benchmark_version": "0.1",
          "category": "reasoning",
          "difficulty": "medium",
          "prompt": "Return the number nine.",
          "expected_characteristics": [
            "Returns 9."
          ],
          "scoring_method": "observatory_rubric_v0.1",
          "enabled": true
        }
        """,
        encoding="utf-8",
    )


def build_next_args(
    tmp_path: Path,
    *,
    now: str,
):
    prompt_bank = tmp_path / "prompts"
    write_single_prompt_bank(prompt_bank)

    parser = build_parser()

    return parser.parse_args(
        [
            "consumer-next",
            "--platform",
            "chatgpt",
            "--observer-id",
            "observer-test",
            "--date",
            "2026-08-19",
            "--now",
            now,
            "--prompt-bank",
            str(prompt_bank),
            "--storage",
            str(tmp_path / "consumer.db"),
        ]
    )


def test_parse_now_utc_accepts_z():
    value = parse_now_utc(
        "2026-08-19T10:00:00Z"
    )

    assert value == datetime(
        2026,
        8,
        19,
        10,
        0,
        tzinfo=timezone.utc,
    )


def test_parse_now_utc_rejects_naive_datetime():
    with pytest.raises(
        ValueError,
        match="include a UTC timezone",
    ):
        parse_now_utc(
            "2026-08-19T10:00:00"
        )


def test_consumer_next_reports_due(
    tmp_path: Path,
    capsys,
):
    from observer.core.consumer_schedule import (
        build_prompt_bank_schedule,
    )

    prompt_bank = tmp_path / "prompts"
    write_single_prompt_bank(prompt_bank)

    schedule = build_prompt_bank_schedule(
        date(2026, 8, 19),
        observer_id="observer-test",
        benchmark_version="0.1",
        prompt_bank_path=prompt_bank,
    )

    scheduled = schedule.items[0].scheduled_at_utc

    args = build_next_args(
        tmp_path,
        now=scheduled.isoformat(),
    )

    result = consumer_next(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "Status:            due" in output
    assert "reasoning-001" in output
    assert "Return the number nine." in output


def test_consumer_next_reports_upcoming(
    tmp_path: Path,
    capsys,
):
    from observer.core.consumer_schedule import (
        build_prompt_bank_schedule,
    )

    prompt_bank = tmp_path / "prompts"
    write_single_prompt_bank(prompt_bank)

    schedule = build_prompt_bank_schedule(
        date(2026, 8, 19),
        observer_id="observer-test",
        benchmark_version="0.1",
        prompt_bank_path=prompt_bank,
    )

    scheduled = schedule.items[0].scheduled_at_utc

    now = (
        scheduled
        - timedelta(minutes=30)
    )

    args = build_next_args(
        tmp_path,
        now=now.isoformat(),
    )

    result = consumer_next(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "Status:            upcoming" in output
    assert "reasoning-001" in output


def test_consumer_next_skips_completed_probe(
    tmp_path: Path,
    capsys,
):
    from observer.core.consumer_schedule import (
        build_prompt_bank_schedule,
    )

    prompt_bank = tmp_path / "prompts"
    write_single_prompt_bank(prompt_bank)

    schedule = build_prompt_bank_schedule(
        date(2026, 8, 19),
        observer_id="observer-test",
        benchmark_version="0.1",
        prompt_bank_path=prompt_bank,
    )

    scheduled = schedule.items[0].scheduled_at_utc
    storage = tmp_path / "consumer.db"

    store = ConsumerProbeSQLiteStore(storage)

    completed = ConsumerProbeRecord(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        platform=ConsumerPlatform.CHATGPT,
        page_hostname="chatgpt.com",
        benchmark_version="0.1",
        prompt_id="reasoning-001",
        started_at_utc=scheduled,
        first_output_at_utc=scheduled,
        completed_at_utc=scheduled,
        time_to_first_output_ms=1000,
        total_latency_ms=3000,
    )

    store.append(completed)

    parser = build_parser()

    args = parser.parse_args(
        [
            "consumer-next",
            "--platform",
            "chatgpt",
            "--observer-id",
            "observer-test",
            "--date",
            "2026-08-19",
            "--now",
            scheduled.isoformat(),
            "--prompt-bank",
            str(prompt_bank),
            "--storage",
            str(storage),
        ]
    )

    result = consumer_next(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "Completed today:   1" in output
    assert "Status:            none" in output
