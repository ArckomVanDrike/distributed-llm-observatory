import json
import shlex
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import observer.cli as cli_module
from observer.cli import (
    agent_compare,
    agent_history,
    agent_test,
    build_parser,
)


def test_parser_exposes_agent_test_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-test",
            "http://127.0.0.1:8000",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
            "--suite-bank",
            "custom/suites",
            "--task-bank",
            "custom/tasks",
            "--output",
            "reports/agent-run.json",
        ]
    )

    assert args.command == "agent-test"
    assert args.base_url == "http://127.0.0.1:8000"
    assert args.observer_id == "observer-test"
    assert args.region_code == "CL-Los-Lagos"
    assert args.suite_bank == Path("custom/suites")
    assert args.task_bank == Path("custom/tasks")
    assert args.output == Path("reports/agent-run.json")



def test_agent_test_runs_protocol_runner_and_prints_summary(
    monkeypatch,
    capsys,
):
    captured = {}
    artifact = SimpleNamespace(
        session=SimpleNamespace(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        ),
    )

    class FakeProtocolRunner:
        def __init__(
            self,
            *,
            observer_id,
            region_code,
            suite_root,
            task_root,
        ):
            captured["observer_id"] = observer_id
            captured["region_code"] = region_code
            captured["suite_root"] = suite_root
            captured["task_root"] = task_root

        def run(
            self,
            *,
            base_url,
            generated_at_utc,
        ):
            captured["base_url"] = base_url
            captured["generated_at_utc"] = generated_at_utc

            return SimpleNamespace(
                session=SimpleNamespace(
                    observer_id="observer-test",
                    region_code="CL-Los-Lagos",
                    target=SimpleNamespace(
                        target_id="example-agent",
                    ),
                ),
                report=SimpleNamespace(
                    suite_id="agent-protocol-core",
                    suite_version="0.1",
                    total_tasks=1,
                    passed_tasks=1,
                    pass_rate=1.0,
                    median_latency_ms=4.5,
                ),
                to_artifact=lambda: artifact,
            )

    monkeypatch.setattr(
        cli_module,
        "AgentLabProtocolRunner",
        FakeProtocolRunner,
    )

    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-test",
            "http://127.0.0.1:8000",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
            "--suite-bank",
            "custom/suites",
            "--task-bank",
            "custom/tasks",
        ]
    )

    result = agent_test(args)
    output = capsys.readouterr().out

    assert result == 0

    assert captured["observer_id"] == "observer-test"
    assert captured["region_code"] == "CL-Los-Lagos"
    assert captured["suite_root"] == Path("custom/suites")
    assert captured["task_root"] == Path("custom/tasks")
    assert (
        captured["base_url"]
        == "http://127.0.0.1:8000"
    )
    assert (
        captured["generated_at_utc"].tzinfo
        is not None
    )

    assert "=== DLLO AGENT LAB ===" in output
    assert "Target:            example-agent" in output
    assert (
        "Suite:             agent-protocol-core v0.1"
        in output
    )
    assert "Observer:          observer-test" in output
    assert "Observed from:     CL-Los-Lagos" in output
    assert (
        "Observatory:       temporal=yes geographic=yes"
        in output
    )
    assert "Tasks:             1" in output
    assert "Passed:            1" in output
    assert "Pass rate:         100.00%" in output
    assert "Median latency:    4.50 ms" in output


def test_agent_test_returns_zero_when_benchmark_fails(
    monkeypatch,
    capsys,
):
    artifact = SimpleNamespace(
        session=SimpleNamespace(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        ),
    )

    class FakeProtocolRunner:
        def __init__(
            self,
            *,
            observer_id,
            region_code,
            suite_root,
            task_root,
        ):
            pass

        def run(
            self,
            *,
            base_url,
            generated_at_utc,
        ):
            return SimpleNamespace(
                session=SimpleNamespace(
                    observer_id="observer-test",
                    region_code="CL-Los-Lagos",
                    target=SimpleNamespace(
                        target_id="failing-agent",
                    ),
                ),
                report=SimpleNamespace(
                    suite_id="agent-protocol-core",
                    suite_version="0.1",
                    total_tasks=1,
                    passed_tasks=0,
                    pass_rate=0.0,
                    median_latency_ms=7.25,
                ),
                to_artifact=lambda: artifact,
            )

    monkeypatch.setattr(
        cli_module,
        "AgentLabProtocolRunner",
        FakeProtocolRunner,
    )

    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-test",
            "http://127.0.0.1:8000",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
        ]
    )

    result = agent_test(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "Target:            failing-agent" in output
    assert "Tasks:             1" in output
    assert "Passed:            0" in output
    assert "Pass rate:         0.00%" in output
    assert "Median latency:    7.25 ms" in output


def test_agent_test_returns_two_on_operational_error(
    monkeypatch,
    capsys,
):
    class FailingProtocolRunner:
        def __init__(
            self,
            *,
            observer_id,
            region_code,
            suite_root,
            task_root,
        ):
            pass

        def run(
            self,
            *,
            base_url,
            generated_at_utc,
        ):
            raise cli_module.AgentLabProtocolRunnerError(
                "Local SUT endpoint is unavailable."
            )

    monkeypatch.setattr(
        cli_module,
        "AgentLabProtocolRunner",
        FailingProtocolRunner,
    )

    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-test",
            "http://127.0.0.1:8000",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
        ]
    )

    result = agent_test(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert (
        "Error: Local SUT endpoint is unavailable."
        in captured.err
    )


def test_main_dispatches_agent_test(
    monkeypatch,
):
    captured = {}

    def fake_agent_test(args):
        captured["command"] = args.command
        captured["base_url"] = args.base_url
        return 17

    monkeypatch.setattr(
        cli_module,
        "agent_test",
        fake_agent_test,
    )

    monkeypatch.setattr(
        cli_module.sys,
        "argv",
        [
            "dllo",
            "agent-test",
            "http://127.0.0.1:8000",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
        ],
    )

    result = cli_module.main()

    assert result == 17
    assert captured["command"] == "agent-test"
    assert (
        captured["base_url"]
        == "http://127.0.0.1:8000"
    )


def test_agent_test_output_defaults_to_none():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-test",
            "http://127.0.0.1:8000",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
        ]
    )

    assert args.output is None


def test_agent_test_writes_artifact_when_output_is_requested(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    captured = {}
    artifact = SimpleNamespace(
        session=SimpleNamespace(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        ),
    )
    output_path = tmp_path / "agent-run.json"

    class FakeProtocolRunner:
        def __init__(
            self,
            *,
            observer_id,
            region_code,
            suite_root,
            task_root,
        ):
            pass

        def run(
            self,
            *,
            base_url,
            generated_at_utc,
        ):
            return SimpleNamespace(
                session=SimpleNamespace(
                    observer_id="observer-test",
                    region_code="CL-Los-Lagos",
                    target=SimpleNamespace(
                        target_id="export-agent",
                    ),
                ),
                report=SimpleNamespace(
                    suite_id="agent-protocol-core",
                    suite_version="0.1",
                    total_tasks=1,
                    passed_tasks=1,
                    pass_rate=1.0,
                    median_latency_ms=5.0,
                ),
                to_artifact=lambda: artifact,
            )

    def fake_write_agent_lab_run_artifact(
        received_artifact,
        received_path,
    ):
        captured["artifact"] = received_artifact
        captured["path"] = received_path

    monkeypatch.setattr(
        cli_module,
        "AgentLabProtocolRunner",
        FakeProtocolRunner,
    )
    monkeypatch.setattr(
        cli_module,
        "write_agent_lab_run_artifact",
        fake_write_agent_lab_run_artifact,
        raising=False,
    )

    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-test",
            "http://127.0.0.1:8000",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
            "--output",
            str(output_path),
        ]
    )

    result = agent_test(args)
    capsys.readouterr()

    assert result == 0
    assert captured["artifact"] is artifact
    assert captured["path"] == output_path


def test_agent_test_does_not_write_artifact_without_output(
    monkeypatch,
    capsys,
):
    artifact = SimpleNamespace(
        session=SimpleNamespace(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        ),
    )

    class FakeProtocolRunner:
        def __init__(
            self,
            *,
            observer_id,
            region_code,
            suite_root,
            task_root,
        ):
            pass

        def run(
            self,
            *,
            base_url,
            generated_at_utc,
        ):
            return SimpleNamespace(
                session=SimpleNamespace(
                    observer_id="observer-test",
                    region_code="CL-Los-Lagos",
                    target=SimpleNamespace(
                        target_id="no-export-agent",
                    ),
                ),
                report=SimpleNamespace(
                    suite_id="agent-protocol-core",
                    suite_version="0.1",
                    total_tasks=1,
                    passed_tasks=1,
                    pass_rate=1.0,
                    median_latency_ms=5.0,
                ),
                to_artifact=lambda: artifact,
            )

    def fail_if_writer_is_called(*args, **kwargs):
        raise AssertionError(
            "Artifact writer must not be called "
            "without --output."
        )

    monkeypatch.setattr(
        cli_module,
        "AgentLabProtocolRunner",
        FakeProtocolRunner,
    )
    monkeypatch.setattr(
        cli_module,
        "write_agent_lab_run_artifact",
        fail_if_writer_is_called,
    )

    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-test",
            "http://127.0.0.1:8000",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
        ]
    )

    result = agent_test(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "Target:            no-export-agent" in output


def test_agent_test_returns_two_when_artifact_write_fails(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    artifact = SimpleNamespace(
        session=SimpleNamespace(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        ),
    )

    class FakeProtocolRunner:
        def __init__(
            self,
            *,
            observer_id,
            region_code,
            suite_root,
            task_root,
        ):
            pass

        def run(
            self,
            *,
            base_url,
            generated_at_utc,
        ):
            return SimpleNamespace(
                session=SimpleNamespace(
                    observer_id="observer-test",
                    region_code="CL-Los-Lagos",
                    target=SimpleNamespace(
                        target_id="export-agent",
                    ),
                ),
                report=SimpleNamespace(
                    suite_id="agent-protocol-core",
                    suite_version="0.1",
                    total_tasks=1,
                    passed_tasks=1,
                    pass_rate=1.0,
                    median_latency_ms=5.0,
                ),
                to_artifact=lambda: artifact,
            )

    def failing_writer(
        artifact,
        path,
    ):
        raise OSError("Cannot write artifact.")

    monkeypatch.setattr(
        cli_module,
        "AgentLabProtocolRunner",
        FakeProtocolRunner,
    )
    monkeypatch.setattr(
        cli_module,
        "write_agent_lab_run_artifact",
        failing_writer,
    )

    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-test",
            "http://127.0.0.1:8000",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
            "--output",
            str(tmp_path / "agent-run.json"),
        ]
    )

    result = agent_test(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert "Error: Cannot write artifact." in captured.err


def test_parser_exposes_agent_compare_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-compare",
            "runs/baseline.json",
            "runs/candidate.json",
        ]
    )

    assert args.command == "agent-compare"
    assert args.baseline == Path(
        "runs/baseline.json"
    )
    assert args.candidate == Path(
        "runs/candidate.json"
    )


def test_main_dispatches_agent_compare(
    monkeypatch,
):
    captured = {}

    def fake_agent_compare(args):
        captured["command"] = args.command
        captured["baseline"] = args.baseline
        captured["candidate"] = args.candidate
        return 19

    monkeypatch.setattr(
        cli_module,
        "agent_compare",
        fake_agent_compare,
        raising=False,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "dllo",
            "agent-compare",
            "baseline.json",
            "candidate.json",
        ],
    )

    result = cli_module.main()

    assert result == 19
    assert captured["command"] == "agent-compare"
    assert captured["baseline"] == Path(
        "baseline.json"
    )
    assert captured["candidate"] == Path(
        "candidate.json"
    )


def test_agent_compare_loads_runs_and_prints_changes(
    monkeypatch,
    capsys,
):
    baseline = SimpleNamespace(
        session=SimpleNamespace(
            session_id="baseline-session",
            target=SimpleNamespace(
                target_id="comparison-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        ),
    )
    candidate = SimpleNamespace(
        session=SimpleNamespace(
            session_id="candidate-session",
            target=SimpleNamespace(
                target_id="comparison-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        ),
    )

    def fake_load(path):
        if path == Path("baseline.json"):
            return baseline

        if path == Path("candidate.json"):
            return candidate

        raise AssertionError(f"Unexpected path: {path}")

    def fake_compare(
        received_candidate,
        received_baseline,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline

        return SimpleNamespace(
            baseline_session_id="baseline-session",
            candidate_session_id="candidate-session",
            total_tasks=4,
            improvements=1,
            regressions=1,
            unchanged=2,
            pass_rate_delta=0.25,
            median_latency_ms_delta=150.0,
            retry_delta=-1,
            human_intervention_delta=2,
            task_changes=(
                SimpleNamespace(
                    task_id="task-fail-to-pass",
                    transition=SimpleNamespace(
                        value="fail-to-pass",
                    ),
                ),
                SimpleNamespace(
                    task_id="task-pass-to-fail",
                    transition=SimpleNamespace(
                        value="pass-to-fail",
                    ),
                ),
                SimpleNamespace(
                    task_id="task-unchanged-pass",
                    transition=SimpleNamespace(
                        value="unchanged-pass",
                    ),
                ),
            ),
        )

    monkeypatch.setattr(
        cli_module,
        "load_agent_lab_run_artifact",
        fake_load,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_agent_lab_runs",
        fake_compare,
        raising=False,
    )

    args = SimpleNamespace(
        baseline=Path("baseline.json"),
        candidate=Path("candidate.json"),
    )

    result = agent_compare(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "=== DLLO AGENT COMPARISON ===" in output
    assert "Target:             comparison-agent" in output
    assert "Suite:              agent-protocol-core v1.0" in output
    assert "Tasks compared:     4" in output
    assert "Improved:           1" in output
    assert "Regressed:          1" in output
    assert "Unchanged:          2" in output
    assert "Pass rate delta:    +25.0%" in output
    assert "Median latency:     +150.0 ms" in output
    assert "Retries:            -1" in output
    assert "Human interventions:+2" in output
    assert "task-fail-to-pass: FAIL -> PASS" in output
    assert "task-pass-to-fail: PASS -> FAIL" in output
    assert "task-unchanged-pass" not in output


def test_agent_compare_returns_two_on_invalid_artifact(
    monkeypatch,
    capsys,
):
    def failing_load(path):
        raise ValueError(
            f"Invalid Agent Lab run artifact: {path}"
        )

    monkeypatch.setattr(
        cli_module,
        "load_agent_lab_run_artifact",
        failing_load,
        raising=False,
    )

    args = SimpleNamespace(
        baseline=Path("baseline.json"),
        candidate=Path("candidate.json"),
    )

    result = agent_compare(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert (
        "Error: Invalid Agent Lab run artifact"
        in captured.err
    )


def test_parser_exposes_agent_history_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-history",
            "runs",
            "--target",
            "comparison-agent",
        ]
    )

    assert args.command == "agent-history"
    assert args.history_root == Path("runs")
    assert args.target == "comparison-agent"


def test_agent_history_target_defaults_to_none():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-history",
            "runs",
        ]
    )

    assert args.target is None


def test_main_dispatches_agent_history(
    monkeypatch,
):
    captured = {}

    def fake_agent_history(args):
        captured["command"] = args.command
        captured["history_root"] = args.history_root
        captured["target"] = args.target
        return 23

    monkeypatch.setattr(
        cli_module,
        "agent_history",
        fake_agent_history,
        raising=False,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "dllo",
            "agent-history",
            "runs",
            "--target",
            "comparison-agent",
        ],
    )

    result = cli_module.main()

    assert result == 23
    assert captured["command"] == "agent-history"
    assert captured["history_root"] == Path("runs")
    assert captured["target"] == "comparison-agent"



def test_agent_history_prints_persisted_runs(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="session-001",
                observer_id=None,
                region_code=None,
                started_at_utc=datetime(
                    2026,
                    8,
                    24,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
                target=SimpleNamespace(
                    target_id="history-agent",
                ),
                suite_id="agent-protocol-core",
                suite_version="1.0",
            ),
            technical_report=SimpleNamespace(
                total_tasks=11,
                pass_rate=0.5,
            ),
        ),
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="session-002",
                observer_id=None,
                region_code=None,
                started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
                target=SimpleNamespace(
                    target_id="history-agent",
                ),
                suite_id="agent-protocol-core",
                suite_version="1.0",
            ),
            technical_report=SimpleNamespace(
                total_tasks=11,
                pass_rate=1.0,
            ),
        ),
    ]

    captured = {}

    class FakeHistory:
        def __init__(self, root):
            captured["root"] = root

        def load_all(self):
            captured["mode"] = "all"
            return artifacts

        def for_target(self, target_id):
            raise AssertionError(
                "Target filter must not be used."
            )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
    )

    result = agent_history(args)
    output = capsys.readouterr().out

    assert result == 0
    assert captured["root"] == Path("runs")
    assert captured["mode"] == "all"
    assert "=== DLLO AGENT RUN HISTORY ===" in output
    assert "Runs:               2" in output
    assert "session-001" in output
    assert "session-002" in output
    assert "history-agent" in output
    assert "agent-protocol-core v1.0" in output
    assert "Pass rate:          50.00%" in output
    assert "Pass rate:          100.00%" in output


def test_agent_history_uses_explicit_target_filter(
    monkeypatch,
    capsys,
):
    captured = {}

    artifact = SimpleNamespace(
        session=SimpleNamespace(
            session_id="filtered-session",
            observer_id=None,
            region_code=None,
            started_at_utc=datetime(
                2026,
                8,
                25,
                18,
                0,
                tzinfo=timezone.utc,
            ),
            target=SimpleNamespace(
                target_id="filtered-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        ),
        technical_report=SimpleNamespace(
            total_tasks=11,
            pass_rate=0.75,
        ),
    )

    class FakeHistory:
        def __init__(self, root):
            captured["root"] = root

        def load_all(self):
            raise AssertionError(
                "Unfiltered history must not be loaded."
            )

        def for_target(self, target_id):
            captured["target"] = target_id
            return [artifact]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target="filtered-agent",
    )

    result = agent_history(args)
    output = capsys.readouterr().out

    assert result == 0
    assert captured["target"] == "filtered-agent"
    assert "Target filter:      filtered-agent" in output
    assert "filtered-session" in output


def test_agent_history_returns_two_on_invalid_artifact(
    monkeypatch,
    capsys,
):
    class FakeHistory:
        def __init__(self, root):
            pass

        def load_all(self):
            raise cli_module.AgentLabArtifactIOError(
                "Invalid Agent Lab run artifact"
            )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
    )

    result = agent_history(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert (
        "Error: Invalid Agent Lab run artifact"
        in captured.err
    )


def test_parser_exposes_agent_compare_temporal_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-compare-temporal",
            "baseline.json",
            "candidate.json",
        ]
    )

    assert args.command == "agent-compare-temporal"
    assert args.baseline == Path("baseline.json")
    assert args.candidate == Path("candidate.json")


def test_agent_compare_temporal_reports_observation_context(
    monkeypatch,
    capsys,
):
    baseline = SimpleNamespace(
        session=SimpleNamespace(
            target=SimpleNamespace(
                target_id="temporal-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        )
    )
    candidate = SimpleNamespace(
        session=SimpleNamespace()
    )

    def fake_load(path):
        if path == Path("baseline.json"):
            return baseline
        if path == Path("candidate.json"):
            return candidate
        raise AssertionError(f"Unexpected path: {path}")

    def fake_compare(
        received_candidate,
        received_baseline,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline

        return SimpleNamespace(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
            baseline_started_at_utc=datetime(
                2026,
                8,
                24,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            candidate_started_at_utc=datetime(
                2026,
                8,
                25,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            run_comparison=SimpleNamespace(
                baseline_session_id="baseline-session",
                candidate_session_id="candidate-session",
                total_tasks=4,
                improvements=1,
                regressions=1,
                unchanged=2,
                pass_rate_delta=0.25,
                median_latency_ms_delta=150.0,
                retry_delta=-1,
                human_intervention_delta=2,
                task_changes=(),
            ),
        )

    monkeypatch.setattr(
        cli_module,
        "load_agent_lab_run_artifact",
        fake_load,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_temporal_agent_observations",
        fake_compare,
        raising=False,
    )

    args = SimpleNamespace(
        baseline=Path("baseline.json"),
        candidate=Path("candidate.json"),
    )

    result = cli_module.agent_compare_temporal(args)
    output = capsys.readouterr().out

    assert result == 0
    assert (
        "=== DLLO AGENT TEMPORAL COMPARISON ==="
        in output
    )
    assert "Target:             temporal-agent" in output
    assert (
        "Suite:              "
        "agent-protocol-core v1.0"
        in output
    )
    assert "Observer:           observer-test" in output
    assert "Observed from:      CL-Los-Lagos" in output
    assert (
        "Baseline observed:  "
        "2026-08-24T20:00:00+00:00"
        in output
    )
    assert (
        "Candidate observed: "
        "2026-08-25T20:00:00+00:00"
        in output
    )
    assert "Tasks compared:     4" in output
    assert "Improved:           1" in output
    assert "Regressed:          1" in output
    assert "Pass rate delta:    +25.0%" in output
    assert "Median latency:     +150.0 ms" in output


def test_agent_compare_temporal_returns_two_on_invalid_comparison(
    monkeypatch,
    capsys,
):
    baseline = SimpleNamespace()
    candidate = SimpleNamespace()

    def fake_load(path):
        if path == Path("baseline.json"):
            return baseline
        if path == Path("candidate.json"):
            return candidate
        raise AssertionError(f"Unexpected path: {path}")

    def failing_compare(
        received_candidate,
        received_baseline,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline

        raise ValueError(
            "Temporal comparison requires the same region_code."
        )

    monkeypatch.setattr(
        cli_module,
        "load_agent_lab_run_artifact",
        fake_load,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_temporal_agent_observations",
        failing_compare,
        raising=False,
    )

    args = SimpleNamespace(
        baseline=Path("baseline.json"),
        candidate=Path("candidate.json"),
    )

    result = cli_module.agent_compare_temporal(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert (
        "Error: Temporal comparison requires "
        "the same region_code."
        in captured.err
    )


def test_main_dispatches_agent_compare_temporal(
    monkeypatch,
):
    sentinel = object()

    def fake_agent_compare_temporal(args):
        assert args.command == "agent-compare-temporal"
        assert args.baseline == Path("baseline.json")
        assert args.candidate == Path("candidate.json")
        return sentinel

    monkeypatch.setattr(
        cli_module,
        "agent_compare_temporal",
        fake_agent_compare_temporal,
        raising=False,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dllo",
            "agent-compare-temporal",
            "baseline.json",
            "candidate.json",
        ],
    )

    result = cli_module.main()

    assert result is sentinel


def test_parser_exposes_agent_compare_geographic_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-compare-geographic",
            "baseline.json",
            "candidate.json",
            "--max-observation-skew-seconds",
            "600",
        ]
    )

    assert args.command == "agent-compare-geographic"
    assert args.baseline == Path("baseline.json")
    assert args.candidate == Path("candidate.json")
    assert args.max_observation_skew_seconds == 600.0


def test_agent_compare_geographic_reports_observation_context(
    monkeypatch,
    capsys,
):
    baseline = SimpleNamespace(
        session=SimpleNamespace(
            target=SimpleNamespace(
                target_id="geographic-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        )
    )
    candidate = SimpleNamespace(
        session=SimpleNamespace()
    )

    def fake_load(path):
        if path == Path("baseline.json"):
            return baseline
        if path == Path("candidate.json"):
            return candidate
        raise AssertionError(f"Unexpected path: {path}")

    def fake_compare(
        received_candidate,
        received_baseline,
        *,
        max_observation_skew,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline
        assert max_observation_skew == timedelta(
            seconds=600.0,
        )

        return SimpleNamespace(
            baseline_observer_id="observer-los-lagos",
            candidate_observer_id="observer-aysen",
            baseline_region_code="CL-Los-Lagos",
            candidate_region_code="CL-Aysen",
            baseline_started_at_utc=datetime(
                2026,
                8,
                25,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            candidate_started_at_utc=datetime(
                2026,
                8,
                25,
                20,
                5,
                tzinfo=timezone.utc,
            ),
            observation_skew=timedelta(
                minutes=5,
            ),
            max_observation_skew=timedelta(
                minutes=10,
            ),
            run_comparison=SimpleNamespace(
                baseline_session_id="baseline-session",
                candidate_session_id="candidate-session",
                total_tasks=4,
                improvements=1,
                regressions=1,
                unchanged=2,
                pass_rate_delta=0.25,
                median_latency_ms_delta=150.0,
                retry_delta=-1,
                human_intervention_delta=2,
                task_changes=(),
            ),
        )

    monkeypatch.setattr(
        cli_module,
        "load_agent_lab_run_artifact",
        fake_load,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_geographic_agent_observations",
        fake_compare,
        raising=False,
    )

    args = SimpleNamespace(
        baseline=Path("baseline.json"),
        candidate=Path("candidate.json"),
        max_observation_skew_seconds=600.0,
    )

    result = cli_module.agent_compare_geographic(args)
    output = capsys.readouterr().out

    assert result == 0
    assert (
        "=== DLLO AGENT GEOGRAPHIC COMPARISON ==="
        in output
    )
    assert "geographic-agent" in output
    assert "agent-protocol-core v1.0" in output

    assert "observer-los-lagos" in output
    assert "observer-aysen" in output

    assert "Observed from baseline:  CL-Los-Lagos" in output
    assert "Observed from candidate: CL-Aysen" in output

    assert "Observation skew:      300.00 s" in output
    assert "Maximum allowed skew: 600.00 s" in output

    assert "Tasks compared:        4" in output
    assert "Improved:              1" in output
    assert "Regressed:             1" in output
    assert "Pass rate delta:       +25.0%" in output
    assert "Median latency:        +150.0 ms" in output


def test_agent_compare_geographic_returns_two_on_invalid_comparison(
    monkeypatch,
    capsys,
):
    baseline = SimpleNamespace()
    candidate = SimpleNamespace()

    def fake_load(path):
        if path == Path("baseline.json"):
            return baseline
        if path == Path("candidate.json"):
            return candidate
        raise AssertionError(f"Unexpected path: {path}")

    def failing_compare(
        received_candidate,
        received_baseline,
        *,
        max_observation_skew,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline
        assert max_observation_skew == timedelta(
            seconds=600.0,
        )

        raise ValueError(
            "Geographic comparison requires "
            "different region_code values."
        )

    monkeypatch.setattr(
        cli_module,
        "load_agent_lab_run_artifact",
        fake_load,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_geographic_agent_observations",
        failing_compare,
        raising=False,
    )

    args = SimpleNamespace(
        baseline=Path("baseline.json"),
        candidate=Path("candidate.json"),
        max_observation_skew_seconds=600.0,
    )

    result = cli_module.agent_compare_geographic(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert (
        "Error: Geographic comparison requires "
        "different region_code values."
        in captured.err
    )


def test_main_dispatches_agent_compare_geographic(
    monkeypatch,
):
    sentinel = object()

    def fake_agent_compare_geographic(args):
        assert args.command == "agent-compare-geographic"
        assert args.baseline == Path("baseline.json")
        assert args.candidate == Path("candidate.json")
        assert args.max_observation_skew_seconds == 600.0
        return sentinel

    monkeypatch.setattr(
        cli_module,
        "agent_compare_geographic",
        fake_agent_compare_geographic,
        raising=False,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dllo",
            "agent-compare-geographic",
            "baseline.json",
            "candidate.json",
            "--max-observation-skew-seconds",
            "600",
        ],
    )

    result = cli_module.main()

    assert result is sentinel


def test_agent_history_reports_observatory_qualification(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="modern-session",
                started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                observer_id="observer-castro",
                region_code="CL-Los-Lagos",
                target=SimpleNamespace(
                    target_id="history-agent",
                ),
                suite_id="agent-protocol-core",
                suite_version="1.0",
            ),
            technical_report=SimpleNamespace(
                total_tasks=11,
                pass_rate=1.0,
            ),
        ),
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="legacy-session",
                started_at_utc=datetime(
                    2026,
                    8,
                    24,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                observer_id=None,
                region_code=None,
                target=SimpleNamespace(
                    target_id="history-agent",
                ),
                suite_id="agent-protocol-core",
                suite_version="1.0",
            ),
            technical_report=SimpleNamespace(
                total_tasks=11,
                pass_rate=0.5,
            ),
        ),
    ]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return artifacts

        def for_target(self, target_id):
            raise AssertionError(
                "Target filter must not be used."
            )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
    )

    result = agent_history(args)
    output = capsys.readouterr().out

    assert result == 0

    assert "Observer:            observer-castro" in output
    assert "Observed from:       CL-Los-Lagos" in output
    assert (
        "Observatory:         "
        "temporal=yes geographic=yes"
        in output
    )

    assert "Observer:            n/a" in output
    assert "Observed from:       n/a" in output
    assert (
        "Observatory:         "
        "temporal=no geographic=no"
        in output
    )


def test_agent_history_reports_observatory_qualification_reasons(
    monkeypatch,
    capsys,
):
    artifact = SimpleNamespace(
        session=SimpleNamespace(
            session_id="legacy-session",
            started_at_utc=datetime(
                2026,
                8,
                24,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            observer_id=None,
            region_code=None,
            target=SimpleNamespace(
                target_id="history-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        ),
        technical_report=SimpleNamespace(
            total_tasks=11,
            pass_rate=0.5,
        ),
    )

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return [artifact]

        def for_target(self, target_id):
            raise AssertionError(
                "Target filter must not be used."
            )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
    )

    result = agent_history(args)
    output = capsys.readouterr().out

    assert result == 0
    assert (
        "Observatory reasons: missing observer_id, "
        "missing region_code"
        in output
    )


def test_parser_exposes_agent_pairs_temporal_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-pairs-temporal",
            "runs",
            "--target",
            "pair-agent",
        ]
    )

    assert args.command == "agent-pairs-temporal"
    assert args.history_root == Path("runs")
    assert args.target == "pair-agent"


def test_main_dispatches_agent_pairs_temporal(
    monkeypatch,
):
    captured = {}

    def fake_agent_pairs_temporal(args):
        captured["command"] = args.command
        captured["history_root"] = args.history_root
        captured["target"] = args.target
        return 31

    monkeypatch.setattr(
        cli_module,
        "agent_pairs_temporal",
        fake_agent_pairs_temporal,
        raising=False,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dllo",
            "agent-pairs-temporal",
            "runs",
            "--target",
            "pair-agent",
        ],
    )

    result = cli_module.main()

    assert result == 31
    assert captured["command"] == "agent-pairs-temporal"
    assert captured["history_root"] == Path("runs")
    assert captured["target"] == "pair-agent"


def test_agent_pairs_temporal_reports_discovered_pairs(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="session-a",
            ),
        ),
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="session-b",
            ),
        ),
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="session-c",
            ),
        ),
    ]
    captured = {}

    class FakeHistory:
        def __init__(self, root):
            captured["root"] = root

        def for_target(self, target_id):
            captured["target"] = target_id
            return artifacts

    def fake_discover(received_artifacts):
        assert received_artifacts is artifacts

        return [
            SimpleNamespace(
                baseline_session_id="session-a",
                candidate_session_id="session-b",
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    24,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id="observer-test",
                candidate_observer_id="observer-test",
                baseline_region_code="CL-Los-Lagos",
                candidate_region_code="CL-Los-Lagos",
                comparable=True,
                reasons=(),
            ),
            SimpleNamespace(
                baseline_session_id="session-a",
                candidate_session_id="session-c",
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    24,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    26,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id="observer-test",
                candidate_observer_id="observer-test",
                baseline_region_code="CL-Los-Lagos",
                candidate_region_code="CL-Aysen",
                comparable=False,
                reasons=(
                    "Temporal comparison requires "
                    "the same region_code.",
                ),
            ),
        ]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_temporal_agent_observation_pairs",
        fake_discover,
        raising=False,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target="pair-agent",
    )

    result = cli_module.agent_pairs_temporal(args)
    output = capsys.readouterr().out

    assert result == 0
    assert captured["root"] == Path("runs")
    assert captured["target"] == "pair-agent"

    assert "=== DLLO AGENT TEMPORAL PAIRS ===" in output
    assert "Runs:               3" in output
    assert "Pairs:              2" in output
    assert "Target filter:      pair-agent" in output

    assert "Baseline session:   session-a" in output
    assert (
        "Baseline observed:  2026-08-24T20:00:00+00:00"
        in output
    )
    assert "Baseline observer:  observer-test" in output
    assert "Observed from baseline:  CL-Los-Lagos" in output

    assert "Candidate session:  session-b" in output
    assert (
        "Candidate observed: 2026-08-25T20:00:00+00:00"
        in output
    )
    assert "Candidate observer: observer-test" in output
    assert "Observed from candidate: CL-Los-Lagos" in output

    assert "Comparable:         yes" in output
    assert (
        "Compare command:    "
        "dllo agent-compare-temporal-history "
        "runs session-a session-b"
        in output
    )

    assert "Candidate session:  session-c" in output
    assert "Comparable:         no" in output
    assert (
        "Reason:             Temporal comparison requires "
        "the same region_code."
        in output
    )
    assert output.count("Compare command:") == 1


def test_parser_exposes_agent_pairs_geographic_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-pairs-geographic",
            "runs",
            "--target",
            "pair-agent",
            "--max-observation-skew-seconds",
            "600",
        ]
    )

    assert args.command == "agent-pairs-geographic"
    assert args.history_root == Path("runs")
    assert args.target == "pair-agent"
    assert args.max_observation_skew_seconds == 600.0


def test_main_dispatches_agent_pairs_geographic(
    monkeypatch,
):
    captured = {}

    def fake_agent_pairs_geographic(args):
        captured["command"] = args.command
        captured["history_root"] = args.history_root
        captured["target"] = args.target
        captured["max_skew"] = (
            args.max_observation_skew_seconds
        )
        return 37

    monkeypatch.setattr(
        cli_module,
        "agent_pairs_geographic",
        fake_agent_pairs_geographic,
        raising=False,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dllo",
            "agent-pairs-geographic",
            "runs",
            "--target",
            "pair-agent",
            "--max-observation-skew-seconds",
            "600",
        ],
    )

    result = cli_module.main()

    assert result == 37
    assert captured["command"] == "agent-pairs-geographic"
    assert captured["history_root"] == Path("runs")
    assert captured["target"] == "pair-agent"
    assert captured["max_skew"] == 600.0


def test_agent_pairs_geographic_reports_discovered_pairs(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="session-a",
            ),
        ),
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="session-b",
            ),
        ),
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="session-c",
            ),
        ),
    ]
    captured = {}

    class FakeHistory:
        def __init__(self, root):
            captured["root"] = root

        def for_target(self, target_id):
            captured["target"] = target_id
            return artifacts

    def fake_discover(
        received_artifacts,
        *,
        max_observation_skew,
    ):
        assert received_artifacts is artifacts
        assert max_observation_skew == timedelta(
            seconds=600.0,
        )

        return [
            SimpleNamespace(
                baseline_session_id="session-a",
                candidate_session_id="session-b",
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    5,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id="observer-los-lagos",
                candidate_observer_id="observer-aysen",
                baseline_region_code="CL-Los-Lagos",
                candidate_region_code="CL-Aysen",
                comparable=True,
                reasons=(),
            ),
            SimpleNamespace(
                baseline_session_id="session-a",
                candidate_session_id="session-c",
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    30,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id="observer-los-lagos",
                candidate_observer_id="observer-aysen-two",
                baseline_region_code="CL-Los-Lagos",
                candidate_region_code="CL-Aysen",
                comparable=False,
                reasons=(
                    "Geographic comparison observation skew "
                    "exceeds max_observation_skew.",
                ),
            ),
        ]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_geographic_agent_observation_pairs",
        fake_discover,
        raising=False,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target="pair-agent",
        max_observation_skew_seconds=600.0,
    )

    result = cli_module.agent_pairs_geographic(args)
    output = capsys.readouterr().out

    assert result == 0
    assert captured["root"] == Path("runs")
    assert captured["target"] == "pair-agent"

    assert "=== DLLO AGENT GEOGRAPHIC PAIRS ===" in output
    assert "Runs:               3" in output
    assert "Pairs:              2" in output
    assert "Target filter:      pair-agent" in output
    assert "Maximum skew:       600.00 s" in output

    assert "Baseline session:   session-a" in output
    assert (
        "Baseline observed:  2026-08-25T20:00:00+00:00"
        in output
    )
    assert "Baseline observer:  observer-los-lagos" in output
    assert "Observed from baseline:  CL-Los-Lagos" in output

    assert "Candidate session:  session-b" in output
    assert (
        "Candidate observed: 2026-08-25T20:05:00+00:00"
        in output
    )
    assert "Candidate observer: observer-aysen" in output
    assert "Observed from candidate: CL-Aysen" in output

    assert "Comparable:         yes" in output
    assert (
        "Compare command:    "
        "dllo agent-compare-geographic-history "
        "runs session-a session-b "
        "--max-observation-skew-seconds 600.0"
        in output
    )

    assert "Candidate session:  session-c" in output
    assert "Comparable:         no" in output
    assert output.count("Compare command:") == 1
    assert (
        "Reason:             Geographic comparison "
        "observation skew exceeds max_observation_skew."
        in output
    )


def test_agent_pairs_geographic_returns_two_on_invalid_skew(
    monkeypatch,
    capsys,
):
    artifacts = []

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return artifacts

    def failing_discover(
        received_artifacts,
        *,
        max_observation_skew,
    ):
        assert received_artifacts is artifacts
        assert max_observation_skew == timedelta(
            seconds=-1.0,
        )

        raise ValueError(
            "max_observation_skew cannot be negative."
        )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_geographic_agent_observation_pairs",
        failing_discover,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
        max_observation_skew_seconds=-1.0,
    )

    result = cli_module.agent_pairs_geographic(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert (
        "Error: max_observation_skew cannot be negative."
        in captured.err
    )


def test_agent_pairs_temporal_uses_all_runs_without_target(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="session-a",
            ),
        ),
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="session-b",
            ),
        ),
    ]
    captured = {}

    class FakeHistory:
        def __init__(self, root):
            captured["root"] = root

        def load_all(self):
            captured["load_all"] = True
            return artifacts

        def for_target(self, target_id):
            raise AssertionError(
                f"Unexpected target filter: {target_id}"
            )

    def fake_discover(received_artifacts):
        assert received_artifacts is artifacts
        return []

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_temporal_agent_observation_pairs",
        fake_discover,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
    )

    result = cli_module.agent_pairs_temporal(args)
    output = capsys.readouterr().out

    assert result == 0
    assert captured["root"] == Path("runs")
    assert captured["load_all"] is True

    assert "Runs:               2" in output
    assert "Pairs:              0" in output
    assert "Target filter:" not in output


def test_agent_pairs_temporal_reports_missing_provenance_as_na(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="legacy-session",
            ),
        ),
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="modern-session",
            ),
        ),
    ]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return artifacts

    def fake_discover(received_artifacts):
        assert received_artifacts is artifacts

        return [
            SimpleNamespace(
                baseline_session_id="legacy-session",
                candidate_session_id="modern-session",
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    24,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id=None,
                candidate_observer_id="observer-test",
                baseline_region_code=None,
                candidate_region_code="CL-Los-Lagos",
                comparable=False,
                reasons=(
                    "Baseline observation is not eligible "
                    "for temporal comparison.",
                ),
            ),
        ]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_temporal_agent_observation_pairs",
        fake_discover,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
    )

    result = cli_module.agent_pairs_temporal(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "Baseline observer:  n/a" in output
    assert "Observed from baseline:  n/a" in output
    assert "Candidate observer: observer-test" in output
    assert "Observed from candidate: CL-Los-Lagos" in output
    assert "None" not in output


def test_agent_pairs_geographic_reports_missing_provenance_as_na(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="legacy-session",
            ),
        ),
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="modern-session",
            ),
        ),
    ]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return artifacts

    def fake_discover(
        received_artifacts,
        *,
        max_observation_skew,
    ):
        assert received_artifacts is artifacts
        assert max_observation_skew == timedelta(
            seconds=600.0,
        )

        return [
            SimpleNamespace(
                baseline_session_id="legacy-session",
                candidate_session_id="modern-session",
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    5,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id=None,
                candidate_observer_id="observer-test",
                baseline_region_code=None,
                candidate_region_code="CL-Aysen",
                comparable=False,
                reasons=(
                    "Baseline observation is not eligible "
                    "for geographic comparison.",
                ),
            ),
        ]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_geographic_agent_observation_pairs",
        fake_discover,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
        max_observation_skew_seconds=600.0,
    )

    result = cli_module.agent_pairs_geographic(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "Baseline observer:  n/a" in output
    assert "Observed from baseline:  n/a" in output
    assert "Candidate observer: observer-test" in output
    assert "Observed from candidate: CL-Aysen" in output
    assert "None" not in output


def test_parser_exposes_agent_compare_temporal_history_command():
    parser = build_parser()

    baseline_session_id = (
        "00000000-0000-0000-0000-000000000301"
    )
    candidate_session_id = (
        "00000000-0000-0000-0000-000000000302"
    )

    args = parser.parse_args(
        [
            "agent-compare-temporal-history",
            "runs",
            baseline_session_id,
            candidate_session_id,
        ]
    )

    assert args.command == "agent-compare-temporal-history"
    assert args.history_root == Path("runs")
    assert args.baseline_session_id == UUID(
        baseline_session_id
    )
    assert args.candidate_session_id == UUID(
        candidate_session_id
    )


def test_main_dispatches_agent_compare_temporal_history(
    monkeypatch,
):
    captured = {}

    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000301"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000302"
    )

    def fake_agent_compare_temporal_history(args):
        captured["command"] = args.command
        captured["history_root"] = args.history_root
        captured["baseline_session_id"] = (
            args.baseline_session_id
        )
        captured["candidate_session_id"] = (
            args.candidate_session_id
        )
        return 41

    monkeypatch.setattr(
        cli_module,
        "agent_compare_temporal_history",
        fake_agent_compare_temporal_history,
        raising=False,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dllo",
            "agent-compare-temporal-history",
            "runs",
            str(baseline_session_id),
            str(candidate_session_id),
        ],
    )

    result = cli_module.main()

    assert result == 41
    assert (
        captured["command"]
        == "agent-compare-temporal-history"
    )
    assert captured["history_root"] == Path("runs")
    assert (
        captured["baseline_session_id"]
        == baseline_session_id
    )
    assert (
        captured["candidate_session_id"]
        == candidate_session_id
    )


def test_agent_compare_temporal_history_resolves_sessions_and_reports(
    monkeypatch,
    capsys,
):
    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000311"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000312"
    )

    baseline = SimpleNamespace(
        session=SimpleNamespace(
            target=SimpleNamespace(
                target_id="history-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        ),
    )
    candidate = SimpleNamespace(
        session=SimpleNamespace(),
    )

    captured = {}

    class FakeHistory:
        def __init__(self, root):
            captured["root"] = root

        def get_by_session_id(self, session_id):
            captured.setdefault(
                "session_ids",
                [],
            ).append(session_id)

            if session_id == baseline_session_id:
                return baseline

            if session_id == candidate_session_id:
                return candidate

            raise AssertionError(
                f"Unexpected session_id: {session_id}"
            )

    def fake_compare(
        received_candidate,
        received_baseline,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline

        return SimpleNamespace(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
            baseline_started_at_utc=datetime(
                2026,
                8,
                24,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            candidate_started_at_utc=datetime(
                2026,
                8,
                25,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            run_comparison=SimpleNamespace(
                total_tasks=4,
                improvements=1,
                regressions=1,
                unchanged=2,
                pass_rate_delta=0.25,
                median_latency_ms_delta=150.0,
                retry_delta=-1,
                human_intervention_delta=2,
            ),
        )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_temporal_agent_observations",
        fake_compare,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        baseline_session_id=baseline_session_id,
        candidate_session_id=candidate_session_id,
    )

    result = cli_module.agent_compare_temporal_history(args)
    output = capsys.readouterr().out

    assert result == 0
    assert captured["root"] == Path("runs")
    assert captured["session_ids"] == [
        baseline_session_id,
        candidate_session_id,
    ]

    assert (
        "=== DLLO AGENT TEMPORAL COMPARISON ==="
        in output
    )
    assert "Target:             history-agent" in output
    assert (
        "Suite:              "
        "agent-protocol-core v1.0"
        in output
    )
    assert "Observer:           observer-test" in output
    assert "Observed from:      CL-Los-Lagos" in output
    assert (
        "Baseline observed:  "
        "2026-08-24T20:00:00+00:00"
        in output
    )
    assert (
        "Candidate observed: "
        "2026-08-25T20:00:00+00:00"
        in output
    )
    assert "Tasks compared:     4" in output
    assert "Pass rate delta:    +25.0%" in output
    assert "Median latency:     +150.0 ms" in output


def test_agent_compare_temporal_history_returns_two_on_unknown_session(
    monkeypatch,
    capsys,
):
    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000321"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000399"
    )

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def get_by_session_id(self, session_id):
            if session_id == baseline_session_id:
                return SimpleNamespace()

            if session_id == candidate_session_id:
                raise ValueError(
                    "Agent Lab run history does not contain "
                    f"session_id: {session_id}"
                )

            raise AssertionError(
                f"Unexpected session_id: {session_id}"
            )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        baseline_session_id=baseline_session_id,
        candidate_session_id=candidate_session_id,
    )

    result = cli_module.agent_compare_temporal_history(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert (
        "Error: Agent Lab run history does not contain "
        f"session_id: {candidate_session_id}"
        in captured.err
    )


def test_parser_exposes_agent_compare_geographic_history_command():
    parser = build_parser()

    baseline_session_id = (
        "00000000-0000-0000-0000-000000000401"
    )
    candidate_session_id = (
        "00000000-0000-0000-0000-000000000402"
    )

    args = parser.parse_args(
        [
            "agent-compare-geographic-history",
            "runs",
            baseline_session_id,
            candidate_session_id,
            "--max-observation-skew-seconds",
            "600",
        ]
    )

    assert args.command == "agent-compare-geographic-history"
    assert args.history_root == Path("runs")
    assert args.baseline_session_id == UUID(
        baseline_session_id
    )
    assert args.candidate_session_id == UUID(
        candidate_session_id
    )
    assert args.max_observation_skew_seconds == 600.0


def test_main_dispatches_agent_compare_geographic_history(
    monkeypatch,
):
    captured = {}

    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000401"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000402"
    )

    def fake_agent_compare_geographic_history(args):
        captured["command"] = args.command
        captured["history_root"] = args.history_root
        captured["baseline_session_id"] = (
            args.baseline_session_id
        )
        captured["candidate_session_id"] = (
            args.candidate_session_id
        )
        captured["max_skew"] = (
            args.max_observation_skew_seconds
        )
        return 43

    monkeypatch.setattr(
        cli_module,
        "agent_compare_geographic_history",
        fake_agent_compare_geographic_history,
        raising=False,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dllo",
            "agent-compare-geographic-history",
            "runs",
            str(baseline_session_id),
            str(candidate_session_id),
            "--max-observation-skew-seconds",
            "600",
        ],
    )

    result = cli_module.main()

    assert result == 43
    assert (
        captured["command"]
        == "agent-compare-geographic-history"
    )
    assert captured["history_root"] == Path("runs")
    assert (
        captured["baseline_session_id"]
        == baseline_session_id
    )
    assert (
        captured["candidate_session_id"]
        == candidate_session_id
    )
    assert captured["max_skew"] == 600.0


def test_agent_compare_geographic_history_resolves_sessions_and_reports(
    monkeypatch,
    capsys,
):
    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000411"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000412"
    )

    baseline = SimpleNamespace(
        session=SimpleNamespace(
            target=SimpleNamespace(
                target_id="history-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        ),
    )
    candidate = SimpleNamespace(
        session=SimpleNamespace(),
    )

    captured = {}

    class FakeHistory:
        def __init__(self, root):
            captured["root"] = root

        def get_by_session_id(self, session_id):
            captured.setdefault(
                "session_ids",
                [],
            ).append(session_id)

            if session_id == baseline_session_id:
                return baseline

            if session_id == candidate_session_id:
                return candidate

            raise AssertionError(
                f"Unexpected session_id: {session_id}"
            )

    def fake_compare(
        received_candidate,
        received_baseline,
        *,
        max_observation_skew,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline
        assert max_observation_skew == timedelta(
            seconds=600.0,
        )

        return SimpleNamespace(
            baseline_observer_id="observer-los-lagos",
            candidate_observer_id="observer-aysen",
            baseline_region_code="CL-Los-Lagos",
            candidate_region_code="CL-Aysen",
            baseline_started_at_utc=datetime(
                2026,
                8,
                25,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            candidate_started_at_utc=datetime(
                2026,
                8,
                25,
                20,
                5,
                tzinfo=timezone.utc,
            ),
            observation_skew=timedelta(
                minutes=5,
            ),
            max_observation_skew=timedelta(
                minutes=10,
            ),
            run_comparison=SimpleNamespace(
                total_tasks=4,
                improvements=1,
                regressions=1,
                unchanged=2,
                pass_rate_delta=0.25,
                median_latency_ms_delta=150.0,
                retry_delta=-1,
                human_intervention_delta=2,
            ),
        )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_geographic_agent_observations",
        fake_compare,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        baseline_session_id=baseline_session_id,
        candidate_session_id=candidate_session_id,
        max_observation_skew_seconds=600.0,
    )

    result = cli_module.agent_compare_geographic_history(
        args
    )
    output = capsys.readouterr().out

    assert result == 0
    assert captured["root"] == Path("runs")
    assert captured["session_ids"] == [
        baseline_session_id,
        candidate_session_id,
    ]

    assert (
        "=== DLLO AGENT GEOGRAPHIC COMPARISON ==="
        in output
    )
    assert "Target:                history-agent" in output
    assert (
        "Suite:                 "
        "agent-protocol-core v1.0"
        in output
    )
    assert "Baseline observer:     observer-los-lagos" in output
    assert "Candidate observer:    observer-aysen" in output
    assert "Observed from baseline:  CL-Los-Lagos" in output
    assert "Observed from candidate: CL-Aysen" in output
    assert "Observation skew:      300.00 s" in output
    assert "Maximum allowed skew: 600.00 s" in output
    assert "Tasks compared:        4" in output
    assert "Pass rate delta:       +25.0%" in output
    assert "Median latency:        +150.0 ms" in output


def test_agent_compare_geographic_history_returns_two_on_unknown_session(
    monkeypatch,
    capsys,
):
    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000421"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000499"
    )

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def get_by_session_id(self, session_id):
            if session_id == baseline_session_id:
                return SimpleNamespace()

            if session_id == candidate_session_id:
                raise ValueError(
                    "Agent Lab run history does not contain "
                    f"session_id: {session_id}"
                )

            raise AssertionError(
                f"Unexpected session_id: {session_id}"
            )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        baseline_session_id=baseline_session_id,
        candidate_session_id=candidate_session_id,
        max_observation_skew_seconds=600.0,
    )

    result = cli_module.agent_compare_geographic_history(
        args
    )
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert (
        "Error: Agent Lab run history does not contain "
        f"session_id: {candidate_session_id}"
        in captured.err
    )


def test_agent_pairs_temporal_quotes_history_root_in_compare_command(
    monkeypatch,
    capsys,
):
    artifacts = [SimpleNamespace()]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("run history")

        def load_all(self):
            return artifacts

    def fake_discover(received_artifacts):
        assert received_artifacts is artifacts

        return [
            SimpleNamespace(
                baseline_session_id="session-a",
                candidate_session_id="session-b",
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    24,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id="observer-test",
                candidate_observer_id="observer-test",
                baseline_region_code="CL-Los-Lagos",
                candidate_region_code="CL-Los-Lagos",
                comparable=True,
                reasons=(),
            )
        ]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_temporal_agent_observation_pairs",
        fake_discover,
    )

    args = SimpleNamespace(
        history_root=Path("run history"),
        target=None,
    )

    result = cli_module.agent_pairs_temporal(args)
    output = capsys.readouterr().out

    assert result == 0
    assert (
        "dllo agent-compare-temporal-history "
        "'run history' session-a session-b"
        in output
    )


def test_agent_pairs_geographic_quotes_history_root_in_compare_command(
    monkeypatch,
    capsys,
):
    artifacts = [SimpleNamespace()]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("run history")

        def load_all(self):
            return artifacts

    def fake_discover(
        received_artifacts,
        *,
        max_observation_skew,
    ):
        assert received_artifacts is artifacts
        assert max_observation_skew == timedelta(
            seconds=600.0,
        )

        return [
            SimpleNamespace(
                baseline_session_id="session-a",
                candidate_session_id="session-b",
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    5,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id="observer-los-lagos",
                candidate_observer_id="observer-aysen",
                baseline_region_code="CL-Los-Lagos",
                candidate_region_code="CL-Aysen",
                comparable=True,
                reasons=(),
            )
        ]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_geographic_agent_observation_pairs",
        fake_discover,
    )

    args = SimpleNamespace(
        history_root=Path("run history"),
        target=None,
        max_observation_skew_seconds=600.0,
    )

    result = cli_module.agent_pairs_geographic(args)
    output = capsys.readouterr().out

    assert result == 0
    assert (
        "dllo agent-compare-geographic-history "
        "'run history' session-a session-b "
        "--max-observation-skew-seconds 600.0"
        in output
    )


def build_pair_roundtrip_artifact(
    *,
    session_id: UUID,
    observed_at: datetime,
    observer_id: str,
    region_code: str,
):
    from observer.core.agent_technical_report import (
        build_agent_technical_report,
    )
    from schemas.agent_lab import (
        AgentLabRunArtifact,
        AgentTestSession,
        AgentTestSessionStatus,
    )
    from schemas.target import (
        TargetCapability,
        TargetManifest,
        TargetType,
    )

    session = AgentTestSession(
        session_id=session_id,
        observer_id=observer_id,
        region_code=region_code,
        target=TargetManifest(
            target_id="roundtrip-agent",
            display_name="Roundtrip Agent",
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        ),
        suite_id="agent-protocol-core",
        suite_version="1.0",
        status=AgentTestSessionStatus.COMPLETED,
        started_at_utc=observed_at,
        completed_at_utc=observed_at,
    )

    return AgentLabRunArtifact(
        session=session,
        technical_report=build_agent_technical_report(
            session,
            generated_at_utc=observed_at,
        ),
    )


def test_agent_pairs_temporal_compare_command_round_trips_through_parser(
    tmp_path,
    capsys,
):
    from observer.core.agent_lab_artifact_io import (
        write_agent_lab_run_artifact,
    )

    history_root = tmp_path / "run history"
    history_root.mkdir()

    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000501"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000502"
    )

    baseline = build_pair_roundtrip_artifact(
        session_id=baseline_session_id,
        observed_at=datetime(
            2026,
            8,
            25,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )
    candidate = build_pair_roundtrip_artifact(
        session_id=candidate_session_id,
        observed_at=datetime(
            2026,
            8,
            25,
            21,
            0,
            tzinfo=timezone.utc,
        ),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    write_agent_lab_run_artifact(
        baseline,
        history_root / "baseline.json",
    )
    write_agent_lab_run_artifact(
        candidate,
        history_root / "candidate.json",
    )

    args = SimpleNamespace(
        history_root=history_root,
        target=None,
    )

    result = cli_module.agent_pairs_temporal(args)
    output = capsys.readouterr().out

    assert result == 0

    command_line = next(
        line.removeprefix("Compare command:    ")
        for line in output.splitlines()
        if line.startswith("Compare command:    ")
    )

    command_parts = shlex.split(command_line)

    assert command_parts[0] == "dllo"

    parsed = build_parser().parse_args(
        command_parts[1:]
    )

    assert parsed.command == "agent-compare-temporal-history"
    assert parsed.history_root == history_root
    assert parsed.baseline_session_id == baseline_session_id
    assert parsed.candidate_session_id == candidate_session_id


def test_agent_pairs_geographic_compare_command_round_trips_through_parser(
    tmp_path,
    capsys,
):
    from observer.core.agent_lab_artifact_io import (
        write_agent_lab_run_artifact,
    )

    history_root = tmp_path / "run history"
    history_root.mkdir()

    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000511"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000512"
    )

    baseline = build_pair_roundtrip_artifact(
        session_id=baseline_session_id,
        observed_at=datetime(
            2026,
            8,
            25,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        observer_id="observer-los-lagos",
        region_code="CL-Los-Lagos",
    )
    candidate = build_pair_roundtrip_artifact(
        session_id=candidate_session_id,
        observed_at=datetime(
            2026,
            8,
            25,
            20,
            5,
            tzinfo=timezone.utc,
        ),
        observer_id="observer-aysen",
        region_code="CL-Aysen",
    )

    write_agent_lab_run_artifact(
        baseline,
        history_root / "baseline.json",
    )
    write_agent_lab_run_artifact(
        candidate,
        history_root / "candidate.json",
    )

    args = SimpleNamespace(
        history_root=history_root,
        target=None,
        max_observation_skew_seconds=600.0,
    )

    result = cli_module.agent_pairs_geographic(args)
    output = capsys.readouterr().out

    assert result == 0

    command_line = next(
        line.removeprefix("Compare command:    ")
        for line in output.splitlines()
        if line.startswith("Compare command:    ")
    )

    command_parts = shlex.split(command_line)

    assert command_parts[0] == "dllo"

    parsed = build_parser().parse_args(
        command_parts[1:]
    )

    assert parsed.command == "agent-compare-geographic-history"
    assert parsed.history_root == history_root
    assert parsed.baseline_session_id == baseline_session_id
    assert parsed.candidate_session_id == candidate_session_id
    assert parsed.max_observation_skew_seconds == 600.0


def test_parser_exposes_agent_history_json_output():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-history",
            "runs",
            "--json",
        ]
    )

    assert args.command == "agent-history"
    assert args.history_root == Path("runs")
    assert args.json_output is True


def test_agent_history_emits_machine_readable_json(
    monkeypatch,
    capsys,
):
    session_id = UUID(
        "00000000-0000-0000-0000-000000000601"
    )
    artifact = SimpleNamespace(
        session=SimpleNamespace(
            session_id=session_id,
            started_at_utc=datetime(
                2026,
                8,
                26,
                1,
                0,
                tzinfo=timezone.utc,
            ),
            target=SimpleNamespace(
                target_id="json-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        ),
        technical_report=SimpleNamespace(
            total_tasks=11,
            pass_rate=0.75,
        ),
    )

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return [artifact]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "qualify_agent_observation",
        lambda received: SimpleNamespace(
            provenance_complete=True,
            temporal_eligible=True,
            geographic_eligible=True,
            reasons=(),
        ),
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
        json_output=True,
    )

    result = cli_module.agent_history(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload == {
        "count": 1,
        "target_filter": None,
        "runs": [
            {
                "started_at_utc": (
                    "2026-08-26T01:00:00+00:00"
                ),
                "session_id": str(session_id),
                "target_id": "json-agent",
                "suite_id": "agent-protocol-core",
                "suite_version": "1.0",
                "observer_id": "observer-test",
                "region_code": "CL-Los-Lagos",
                "observatory": {
                    "provenance_complete": True,
                    "temporal_eligible": True,
                    "geographic_eligible": True,
                    "reasons": [],
                },
                "total_tasks": 11,
                "pass_rate": 0.75,
            }
        ],
    }


def test_agent_history_json_keeps_legacy_run_with_qualification_reasons(
    monkeypatch,
    capsys,
):
    session_id = UUID(
        "00000000-0000-0000-0000-000000000611"
    )
    artifact = SimpleNamespace(
        session=SimpleNamespace(
            session_id=session_id,
            started_at_utc=datetime(
                2026,
                8,
                25,
                22,
                0,
                tzinfo=timezone.utc,
            ),
            target=SimpleNamespace(
                target_id="legacy-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
            observer_id=None,
            region_code=None,
        ),
        technical_report=SimpleNamespace(
            total_tasks=11,
            pass_rate=0.5,
        ),
    )

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return [artifact]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "qualify_agent_observation",
        lambda received: SimpleNamespace(
            provenance_complete=False,
            temporal_eligible=False,
            geographic_eligible=False,
            reasons=(
                "Observation is missing observer provenance.",
            ),
        ),
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
        json_output=True,
    )

    result = cli_module.agent_history(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload["count"] == 1
    assert len(payload["runs"]) == 1

    run = payload["runs"][0]

    assert run["session_id"] == str(session_id)
    assert run["target_id"] == "legacy-agent"
    assert run["observer_id"] is None
    assert run["region_code"] is None
    assert run["observatory"] == {
        "provenance_complete": False,
        "temporal_eligible": False,
        "geographic_eligible": False,
        "reasons": [
            "Observation is missing observer provenance.",
        ],
    }


def test_agent_history_json_reports_explicit_target_filter(
    monkeypatch,
    capsys,
):
    artifact = SimpleNamespace(
        session=SimpleNamespace(
            session_id=UUID(
                "00000000-0000-0000-0000-000000000621"
            ),
            started_at_utc=datetime(
                2026,
                8,
                26,
                2,
                0,
                tzinfo=timezone.utc,
            ),
            target=SimpleNamespace(
                target_id="filtered-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
        ),
        technical_report=SimpleNamespace(
            total_tasks=11,
            pass_rate=1.0,
        ),
    )

    captured = {}

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            raise AssertionError(
                "load_all must not be used with target filter"
            )

        def for_target(self, target_id):
            captured["target"] = target_id
            return [artifact]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "qualify_agent_observation",
        lambda received: SimpleNamespace(
            provenance_complete=True,
            temporal_eligible=True,
            geographic_eligible=True,
            reasons=(),
        ),
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target="filtered-agent",
        json_output=True,
    )

    result = cli_module.agent_history(args)
    output = capsys.readouterr().out

    assert result == 0
    assert captured["target"] == "filtered-agent"

    payload = json.loads(output)

    assert payload["count"] == 1
    assert payload["target_filter"] == "filtered-agent"
    assert [
        run["target_id"]
        for run in payload["runs"]
    ] == ["filtered-agent"]


def test_parser_exposes_agent_pairs_temporal_json_output():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-pairs-temporal",
            "runs",
            "--json",
        ]
    )

    assert args.command == "agent-pairs-temporal"
    assert args.history_root == Path("runs")
    assert args.target is None
    assert args.json_output is True


def test_agent_pairs_temporal_emits_machine_readable_json(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
    ]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def for_target(self, target_id):
            assert target_id == "pair-agent"
            return artifacts

    def fake_discover(received_artifacts):
        assert received_artifacts is artifacts

        return [
            SimpleNamespace(
                baseline_session_id=UUID(
                    "00000000-0000-0000-0000-000000000701"
                ),
                candidate_session_id=UUID(
                    "00000000-0000-0000-0000-000000000702"
                ),
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    21,
                    0,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id="observer-test",
                candidate_observer_id="observer-test",
                baseline_region_code="CL-Los-Lagos",
                candidate_region_code="CL-Los-Lagos",
                comparable=True,
                reasons=(),
            ),
            SimpleNamespace(
                baseline_session_id=UUID(
                    "00000000-0000-0000-0000-000000000701"
                ),
                candidate_session_id=UUID(
                    "00000000-0000-0000-0000-000000000703"
                ),
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    22,
                    0,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id="observer-test",
                candidate_observer_id="observer-test",
                baseline_region_code="CL-Los-Lagos",
                candidate_region_code="CL-Aysen",
                comparable=False,
                reasons=(
                    "Temporal comparison requires "
                    "the same region_code.",
                ),
            ),
        ]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_temporal_agent_observation_pairs",
        fake_discover,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target="pair-agent",
        json_output=True,
    )

    result = cli_module.agent_pairs_temporal(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload == {
        "count": 2,
        "target_filter": "pair-agent",
        "pairs": [
            {
                "baseline": {
                    "session_id": (
                        "00000000-0000-0000-0000-000000000701"
                    ),
                    "started_at_utc": (
                        "2026-08-25T20:00:00+00:00"
                    ),
                    "observer_id": "observer-test",
                    "region_code": "CL-Los-Lagos",
                },
                "candidate": {
                    "session_id": (
                        "00000000-0000-0000-0000-000000000702"
                    ),
                    "started_at_utc": (
                        "2026-08-25T21:00:00+00:00"
                    ),
                    "observer_id": "observer-test",
                    "region_code": "CL-Los-Lagos",
                },
                "comparable": True,
                "reasons": [],
            },
            {
                "baseline": {
                    "session_id": (
                        "00000000-0000-0000-0000-000000000701"
                    ),
                    "started_at_utc": (
                        "2026-08-25T20:00:00+00:00"
                    ),
                    "observer_id": "observer-test",
                    "region_code": "CL-Los-Lagos",
                },
                "candidate": {
                    "session_id": (
                        "00000000-0000-0000-0000-000000000703"
                    ),
                    "started_at_utc": (
                        "2026-08-25T22:00:00+00:00"
                    ),
                    "observer_id": "observer-test",
                    "region_code": "CL-Aysen",
                },
                "comparable": False,
                "reasons": [
                    "Temporal comparison requires "
                    "the same region_code.",
                ],
            },
        ],
    }


def test_parser_exposes_agent_pairs_geographic_json_output():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-pairs-geographic",
            "runs",
            "--max-observation-skew-seconds",
            "600",
            "--json",
        ]
    )

    assert args.command == "agent-pairs-geographic"
    assert args.history_root == Path("runs")
    assert args.target is None
    assert args.max_observation_skew_seconds == 600.0
    assert args.json_output is True


def test_agent_pairs_geographic_emits_machine_readable_json(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
    ]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def for_target(self, target_id):
            assert target_id == "pair-agent"
            return artifacts

    def fake_discover(
        received_artifacts,
        *,
        max_observation_skew,
    ):
        assert received_artifacts is artifacts
        assert max_observation_skew == timedelta(
            seconds=600.0,
        )

        return [
            SimpleNamespace(
                baseline_session_id=UUID(
                    "00000000-0000-0000-0000-000000000711"
                ),
                candidate_session_id=UUID(
                    "00000000-0000-0000-0000-000000000712"
                ),
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    5,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id="observer-los-lagos",
                candidate_observer_id="observer-aysen",
                baseline_region_code="CL-Los-Lagos",
                candidate_region_code="CL-Aysen",
                comparable=True,
                reasons=(),
            ),
            SimpleNamespace(
                baseline_session_id=UUID(
                    "00000000-0000-0000-0000-000000000711"
                ),
                candidate_session_id=UUID(
                    "00000000-0000-0000-0000-000000000713"
                ),
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    30,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id="observer-los-lagos",
                candidate_observer_id="observer-aysen-two",
                baseline_region_code="CL-Los-Lagos",
                candidate_region_code="CL-Aysen",
                comparable=False,
                reasons=(
                    "Geographic comparison observation skew "
                    "exceeds max_observation_skew.",
                ),
            ),
        ]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_geographic_agent_observation_pairs",
        fake_discover,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target="pair-agent",
        max_observation_skew_seconds=600.0,
        json_output=True,
    )

    result = cli_module.agent_pairs_geographic(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload == {
        "count": 2,
        "target_filter": "pair-agent",
        "max_observation_skew_seconds": 600.0,
        "pairs": [
            {
                "baseline": {
                    "session_id": (
                        "00000000-0000-0000-0000-000000000711"
                    ),
                    "started_at_utc": (
                        "2026-08-25T20:00:00+00:00"
                    ),
                    "observer_id": "observer-los-lagos",
                    "region_code": "CL-Los-Lagos",
                },
                "candidate": {
                    "session_id": (
                        "00000000-0000-0000-0000-000000000712"
                    ),
                    "started_at_utc": (
                        "2026-08-25T20:05:00+00:00"
                    ),
                    "observer_id": "observer-aysen",
                    "region_code": "CL-Aysen",
                },
                "comparable": True,
                "reasons": [],
            },
            {
                "baseline": {
                    "session_id": (
                        "00000000-0000-0000-0000-000000000711"
                    ),
                    "started_at_utc": (
                        "2026-08-25T20:00:00+00:00"
                    ),
                    "observer_id": "observer-los-lagos",
                    "region_code": "CL-Los-Lagos",
                },
                "candidate": {
                    "session_id": (
                        "00000000-0000-0000-0000-000000000713"
                    ),
                    "started_at_utc": (
                        "2026-08-25T20:30:00+00:00"
                    ),
                    "observer_id": "observer-aysen-two",
                    "region_code": "CL-Aysen",
                },
                "comparable": False,
                "reasons": [
                    "Geographic comparison observation skew "
                    "exceeds max_observation_skew.",
                ],
            },
        ],
    }


def test_agent_pairs_temporal_json_preserves_missing_provenance_as_null(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(),
        SimpleNamespace(),
    ]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return artifacts

    def fake_discover(received_artifacts):
        assert received_artifacts is artifacts

        return [
            SimpleNamespace(
                baseline_session_id=UUID(
                    "00000000-0000-0000-0000-000000000721"
                ),
                candidate_session_id=UUID(
                    "00000000-0000-0000-0000-000000000722"
                ),
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    21,
                    0,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id=None,
                candidate_observer_id="observer-test",
                baseline_region_code=None,
                candidate_region_code="CL-Los-Lagos",
                comparable=False,
                reasons=(
                    "Temporal comparison requires complete "
                    "observer provenance.",
                ),
            )
        ]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_temporal_agent_observation_pairs",
        fake_discover,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
        json_output=True,
    )

    result = cli_module.agent_pairs_temporal(args)
    output = capsys.readouterr().out

    assert result == 0

    payload = json.loads(output)
    pair = payload["pairs"][0]

    assert pair["baseline"]["observer_id"] is None
    assert pair["baseline"]["region_code"] is None
    assert pair["candidate"]["observer_id"] == "observer-test"
    assert pair["candidate"]["region_code"] == "CL-Los-Lagos"
    assert pair["comparable"] is False
    assert "n/a" not in output


def test_agent_pairs_geographic_json_preserves_missing_provenance_as_null(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(),
        SimpleNamespace(),
    ]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return artifacts

    def fake_discover(
        received_artifacts,
        *,
        max_observation_skew,
    ):
        assert received_artifacts is artifacts
        assert max_observation_skew == timedelta(
            seconds=600.0,
        )

        return [
            SimpleNamespace(
                baseline_session_id=UUID(
                    "00000000-0000-0000-0000-000000000731"
                ),
                candidate_session_id=UUID(
                    "00000000-0000-0000-0000-000000000732"
                ),
                baseline_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                candidate_started_at_utc=datetime(
                    2026,
                    8,
                    25,
                    20,
                    5,
                    tzinfo=timezone.utc,
                ),
                baseline_observer_id=None,
                candidate_observer_id="observer-aysen",
                baseline_region_code=None,
                candidate_region_code="CL-Aysen",
                comparable=False,
                reasons=(
                    "Geographic comparison requires complete "
                    "observer provenance.",
                ),
            )
        ]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_geographic_agent_observation_pairs",
        fake_discover,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
        max_observation_skew_seconds=600.0,
        json_output=True,
    )

    result = cli_module.agent_pairs_geographic(args)
    output = capsys.readouterr().out

    assert result == 0

    payload = json.loads(output)
    pair = payload["pairs"][0]

    assert pair["baseline"]["observer_id"] is None
    assert pair["baseline"]["region_code"] is None
    assert pair["candidate"]["observer_id"] == "observer-aysen"
    assert pair["candidate"]["region_code"] == "CL-Aysen"
    assert pair["comparable"] is False
    assert "n/a" not in output


def test_parser_exposes_agent_compare_temporal_history_json_output():
    parser = build_parser()

    baseline_session_id = (
        "00000000-0000-0000-0000-000000000801"
    )
    candidate_session_id = (
        "00000000-0000-0000-0000-000000000802"
    )

    args = parser.parse_args(
        [
            "agent-compare-temporal-history",
            "runs",
            baseline_session_id,
            candidate_session_id,
            "--json",
        ]
    )

    assert args.command == "agent-compare-temporal-history"
    assert args.history_root == Path("runs")
    assert args.baseline_session_id == UUID(
        baseline_session_id
    )
    assert args.candidate_session_id == UUID(
        candidate_session_id
    )
    assert args.json_output is True


def test_agent_compare_temporal_history_emits_machine_readable_json(
    monkeypatch,
    capsys,
):
    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000811"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000812"
    )

    baseline = SimpleNamespace(
        session=SimpleNamespace(
            session_id=baseline_session_id,
            target=SimpleNamespace(
                target_id="history-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        ),
    )
    candidate = SimpleNamespace(
        session=SimpleNamespace(
            session_id=candidate_session_id,
        ),
    )

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def get_by_session_id(self, session_id):
            if session_id == baseline_session_id:
                return baseline

            if session_id == candidate_session_id:
                return candidate

            raise AssertionError(
                f"Unexpected session_id: {session_id}"
            )

    def fake_compare(
        received_candidate,
        received_baseline,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline

        return SimpleNamespace(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
            baseline_started_at_utc=datetime(
                2026,
                8,
                25,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            candidate_started_at_utc=datetime(
                2026,
                8,
                26,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            run_comparison=SimpleNamespace(
                total_tasks=4,
                improvements=1,
                regressions=1,
                unchanged=2,
                pass_rate_delta=0.25,
                median_latency_ms_delta=150.0,
                retry_delta=-1,
                human_intervention_delta=2,
            ),
        )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_temporal_agent_observations",
        fake_compare,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        baseline_session_id=baseline_session_id,
        candidate_session_id=candidate_session_id,
        json_output=True,
    )

    result = cli_module.agent_compare_temporal_history(
        args
    )
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload == {
        "target_id": "history-agent",
        "suite_id": "agent-protocol-core",
        "suite_version": "1.0",
        "observer_id": "observer-test",
        "region_code": "CL-Los-Lagos",
        "baseline": {
            "session_id": str(baseline_session_id),
            "started_at_utc": (
                "2026-08-25T20:00:00+00:00"
            ),
        },
        "candidate": {
            "session_id": str(candidate_session_id),
            "started_at_utc": (
                "2026-08-26T20:00:00+00:00"
            ),
        },
        "comparison": {
            "total_tasks": 4,
            "improvements": 1,
            "regressions": 1,
            "unchanged": 2,
            "pass_rate_delta": 0.25,
            "median_latency_ms_delta": 150.0,
            "retry_delta": -1,
            "human_intervention_delta": 2,
        },
    }


def test_parser_exposes_agent_compare_temporal_json_output():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-compare-temporal",
            "baseline.json",
            "candidate.json",
            "--json",
        ]
    )

    assert args.command == "agent-compare-temporal"
    assert args.baseline == Path("baseline.json")
    assert args.candidate == Path("candidate.json")
    assert args.json_output is True


def test_agent_compare_temporal_emits_machine_readable_json(
    monkeypatch,
    capsys,
):
    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000821"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000822"
    )

    baseline = SimpleNamespace(
        session=SimpleNamespace(
            session_id=baseline_session_id,
            target=SimpleNamespace(
                target_id="path-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        ),
    )
    candidate = SimpleNamespace(
        session=SimpleNamespace(
            session_id=candidate_session_id,
        ),
    )

    def fake_load(path):
        if path == Path("baseline.json"):
            return baseline

        if path == Path("candidate.json"):
            return candidate

        raise AssertionError(
            f"Unexpected artifact path: {path}"
        )

    def fake_compare(
        received_candidate,
        received_baseline,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline

        return SimpleNamespace(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
            baseline_started_at_utc=datetime(
                2026,
                8,
                25,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            candidate_started_at_utc=datetime(
                2026,
                8,
                26,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            run_comparison=SimpleNamespace(
                total_tasks=4,
                improvements=1,
                regressions=1,
                unchanged=2,
                pass_rate_delta=0.25,
                median_latency_ms_delta=150.0,
                retry_delta=-1,
                human_intervention_delta=2,
            ),
        )

    monkeypatch.setattr(
        cli_module,
        "load_agent_lab_run_artifact",
        fake_load,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_temporal_agent_observations",
        fake_compare,
    )

    args = SimpleNamespace(
        baseline=Path("baseline.json"),
        candidate=Path("candidate.json"),
        json_output=True,
    )

    result = cli_module.agent_compare_temporal(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload == {
        "target_id": "path-agent",
        "suite_id": "agent-protocol-core",
        "suite_version": "1.0",
        "observer_id": "observer-test",
        "region_code": "CL-Los-Lagos",
        "baseline": {
            "session_id": str(baseline_session_id),
            "started_at_utc": (
                "2026-08-25T20:00:00+00:00"
            ),
        },
        "candidate": {
            "session_id": str(candidate_session_id),
            "started_at_utc": (
                "2026-08-26T20:00:00+00:00"
            ),
        },
        "comparison": {
            "total_tasks": 4,
            "improvements": 1,
            "regressions": 1,
            "unchanged": 2,
            "pass_rate_delta": 0.25,
            "median_latency_ms_delta": 150.0,
            "retry_delta": -1,
            "human_intervention_delta": 2,
        },
    }


def test_parser_exposes_agent_compare_geographic_history_json_output():
    parser = build_parser()

    baseline_session_id = (
        "00000000-0000-0000-0000-000000000831"
    )
    candidate_session_id = (
        "00000000-0000-0000-0000-000000000832"
    )

    args = parser.parse_args(
        [
            "agent-compare-geographic-history",
            "runs",
            baseline_session_id,
            candidate_session_id,
            "--max-observation-skew-seconds",
            "600",
            "--json",
        ]
    )

    assert args.command == "agent-compare-geographic-history"
    assert args.history_root == Path("runs")
    assert args.baseline_session_id == UUID(
        baseline_session_id
    )
    assert args.candidate_session_id == UUID(
        candidate_session_id
    )
    assert args.max_observation_skew_seconds == 600.0
    assert args.json_output is True


def test_agent_compare_geographic_history_emits_machine_readable_json(
    monkeypatch,
    capsys,
):
    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000841"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000842"
    )

    baseline = SimpleNamespace(
        session=SimpleNamespace(
            session_id=baseline_session_id,
            target=SimpleNamespace(
                target_id="history-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        ),
    )
    candidate = SimpleNamespace(
        session=SimpleNamespace(
            session_id=candidate_session_id,
        ),
    )

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def get_by_session_id(self, session_id):
            if session_id == baseline_session_id:
                return baseline

            if session_id == candidate_session_id:
                return candidate

            raise AssertionError(
                f"Unexpected session_id: {session_id}"
            )

    def fake_compare(
        received_candidate,
        received_baseline,
        *,
        max_observation_skew,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline
        assert max_observation_skew == timedelta(
            seconds=600.0,
        )

        return SimpleNamespace(
            baseline_observer_id="observer-los-lagos",
            candidate_observer_id="observer-aysen",
            baseline_region_code="CL-Los-Lagos",
            candidate_region_code="CL-Aysen",
            baseline_started_at_utc=datetime(
                2026,
                8,
                26,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            candidate_started_at_utc=datetime(
                2026,
                8,
                26,
                20,
                5,
                tzinfo=timezone.utc,
            ),
            observation_skew=timedelta(
                minutes=5,
            ),
            max_observation_skew=timedelta(
                minutes=10,
            ),
            run_comparison=SimpleNamespace(
                total_tasks=4,
                improvements=1,
                regressions=1,
                unchanged=2,
                pass_rate_delta=0.25,
                median_latency_ms_delta=150.0,
                retry_delta=-1,
                human_intervention_delta=2,
            ),
        )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_geographic_agent_observations",
        fake_compare,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        baseline_session_id=baseline_session_id,
        candidate_session_id=candidate_session_id,
        max_observation_skew_seconds=600.0,
        json_output=True,
    )

    result = cli_module.agent_compare_geographic_history(
        args
    )
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload == {
        "target_id": "history-agent",
        "suite_id": "agent-protocol-core",
        "suite_version": "1.0",
        "baseline": {
            "session_id": str(baseline_session_id),
            "observer_id": "observer-los-lagos",
            "region_code": "CL-Los-Lagos",
            "started_at_utc": (
                "2026-08-26T20:00:00+00:00"
            ),
        },
        "candidate": {
            "session_id": str(candidate_session_id),
            "observer_id": "observer-aysen",
            "region_code": "CL-Aysen",
            "started_at_utc": (
                "2026-08-26T20:05:00+00:00"
            ),
        },
        "observation_skew_seconds": 300.0,
        "max_observation_skew_seconds": 600.0,
        "comparison": {
            "total_tasks": 4,
            "improvements": 1,
            "regressions": 1,
            "unchanged": 2,
            "pass_rate_delta": 0.25,
            "median_latency_ms_delta": 150.0,
            "retry_delta": -1,
            "human_intervention_delta": 2,
        },
    }


def test_parser_exposes_agent_compare_geographic_json_output():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-compare-geographic",
            "baseline.json",
            "candidate.json",
            "--max-observation-skew-seconds",
            "600",
            "--json",
        ]
    )

    assert args.command == "agent-compare-geographic"
    assert args.baseline == Path("baseline.json")
    assert args.candidate == Path("candidate.json")
    assert args.max_observation_skew_seconds == 600.0
    assert args.json_output is True


def test_agent_compare_geographic_emits_machine_readable_json(
    monkeypatch,
    capsys,
):
    baseline_session_id = UUID(
        "00000000-0000-0000-0000-000000000851"
    )
    candidate_session_id = UUID(
        "00000000-0000-0000-0000-000000000852"
    )

    baseline = SimpleNamespace(
        session=SimpleNamespace(
            session_id=baseline_session_id,
            target=SimpleNamespace(
                target_id="path-agent",
            ),
            suite_id="agent-protocol-core",
            suite_version="1.0",
        ),
    )
    candidate = SimpleNamespace(
        session=SimpleNamespace(
            session_id=candidate_session_id,
        ),
    )

    def fake_load(path):
        if path == Path("baseline.json"):
            return baseline

        if path == Path("candidate.json"):
            return candidate

        raise AssertionError(
            f"Unexpected artifact path: {path}"
        )

    def fake_compare(
        received_candidate,
        received_baseline,
        *,
        max_observation_skew,
    ):
        assert received_candidate is candidate
        assert received_baseline is baseline
        assert max_observation_skew == timedelta(
            seconds=600.0,
        )

        return SimpleNamespace(
            baseline_observer_id="observer-los-lagos",
            candidate_observer_id="observer-aysen",
            baseline_region_code="CL-Los-Lagos",
            candidate_region_code="CL-Aysen",
            baseline_started_at_utc=datetime(
                2026,
                8,
                26,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            candidate_started_at_utc=datetime(
                2026,
                8,
                26,
                20,
                5,
                tzinfo=timezone.utc,
            ),
            observation_skew=timedelta(
                minutes=5,
            ),
            max_observation_skew=timedelta(
                minutes=10,
            ),
            run_comparison=SimpleNamespace(
                total_tasks=4,
                improvements=1,
                regressions=1,
                unchanged=2,
                pass_rate_delta=0.25,
                median_latency_ms_delta=150.0,
                retry_delta=-1,
                human_intervention_delta=2,
            ),
        )

    monkeypatch.setattr(
        cli_module,
        "load_agent_lab_run_artifact",
        fake_load,
    )
    monkeypatch.setattr(
        cli_module,
        "compare_geographic_agent_observations",
        fake_compare,
    )

    args = SimpleNamespace(
        baseline=Path("baseline.json"),
        candidate=Path("candidate.json"),
        max_observation_skew_seconds=600.0,
        json_output=True,
    )

    result = cli_module.agent_compare_geographic(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload == {
        "target_id": "path-agent",
        "suite_id": "agent-protocol-core",
        "suite_version": "1.0",
        "baseline": {
            "session_id": str(baseline_session_id),
            "observer_id": "observer-los-lagos",
            "region_code": "CL-Los-Lagos",
            "started_at_utc": (
                "2026-08-26T20:00:00+00:00"
            ),
        },
        "candidate": {
            "session_id": str(candidate_session_id),
            "observer_id": "observer-aysen",
            "region_code": "CL-Aysen",
            "started_at_utc": (
                "2026-08-26T20:05:00+00:00"
            ),
        },
        "observation_skew_seconds": 300.0,
        "max_observation_skew_seconds": 600.0,
        "comparison": {
            "total_tasks": 4,
            "improvements": 1,
            "regressions": 1,
            "unchanged": 2,
            "pass_rate_delta": 0.25,
            "median_latency_ms_delta": 150.0,
            "retry_delta": -1,
            "human_intervention_delta": 2,
        },
    }


def test_parser_exposes_agent_observatory_summary():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-observatory-summary",
            "runs",
        ]
    )

    assert args.command == "agent-observatory-summary"
    assert args.history_root == Path("runs")
    assert args.target is None


def test_agent_observatory_summary_reports_empty_history(
    monkeypatch,
    capsys,
):
    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return []

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
    )

    result = cli_module.agent_observatory_summary(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""
    assert captured.out == (
        "=== DLLO AGENT OBSERVATORY SUMMARY ===\n"
        "Runs:                 0\n"
        "Targets:              0\n"
        "Observers:            0\n"
        "Observed regions:     0\n"
        "Temporal eligible:    0\n"
        "Geographic eligible:  0\n"
        "Temporal pairs:\n"
        "  Comparable: 0\n"
        "  Rejected:   0\n"
        "Observation window:   n/a\n"
    )


def test_agent_observatory_summary_reports_observation_inventory(
    monkeypatch,
    capsys,
):
    first = SimpleNamespace(
        session=SimpleNamespace(
            session_id=UUID(
                "00000000-0000-0000-0000-000000000901"
            ),
            target=SimpleNamespace(
                target_id="agent-a",
            ),
            observer_id="observer-1",
            region_code="CL-Los-Lagos",
            started_at_utc=datetime(
                2026,
                8,
                20,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        ),
    )

    second = SimpleNamespace(
        session=SimpleNamespace(
            session_id=UUID(
                "00000000-0000-0000-0000-000000000902"
            ),
            target=SimpleNamespace(
                target_id="agent-a",
            ),
            observer_id="observer-2",
            region_code="CL-Aysen",
            started_at_utc=datetime(
                2026,
                8,
                22,
                15,
                30,
                tzinfo=timezone.utc,
            ),
        ),
    )

    legacy = SimpleNamespace(
        session=SimpleNamespace(
            session_id=UUID(
                "00000000-0000-0000-0000-000000000903"
            ),
            target=SimpleNamespace(
                target_id="agent-b",
            ),
            observer_id=None,
            region_code=None,
            started_at_utc=datetime(
                2026,
                8,
                26,
                9,
                45,
                tzinfo=timezone.utc,
            ),
        ),
    )

    artifacts = [first, second, legacy]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return artifacts

    def fake_qualify(artifact):
        if artifact is first:
            return SimpleNamespace(
                temporal_eligible=True,
                geographic_eligible=True,
            )

        if artifact is second:
            return SimpleNamespace(
                temporal_eligible=True,
                geographic_eligible=True,
            )

        if artifact is legacy:
            return SimpleNamespace(
                temporal_eligible=False,
                geographic_eligible=False,
            )

        raise AssertionError("Unexpected artifact")

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "discover_temporal_agent_observation_pairs",
        lambda artifacts: [
            SimpleNamespace(comparable=True),
            SimpleNamespace(comparable=True),
            SimpleNamespace(comparable=False),
        ],
    )

    monkeypatch.setattr(
        cli_module,
        "qualify_agent_observation",
        fake_qualify,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
    )

    result = cli_module.agent_observatory_summary(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""
    assert captured.out == (
        "=== DLLO AGENT OBSERVATORY SUMMARY ===\n"
        "Runs:                 3\n"
        "Targets:              2\n"
        "Observers:            2\n"
        "Observed regions:     2\n"
        "Temporal eligible:    2\n"
        "Geographic eligible:  2\n"
        "Temporal pairs:\n"
        "  Comparable: 2\n"
        "  Rejected:   1\n"
        "Observation window:\n"
        "  First: 2026-08-20T12:00:00+00:00\n"
        "  Last:  2026-08-26T09:45:00+00:00\n"
    )


def test_agent_observatory_summary_applies_target_filter(
    monkeypatch,
    capsys,
):
    first = SimpleNamespace(
        session=SimpleNamespace(
            session_id=UUID(
                "00000000-0000-0000-0000-000000000911"
            ),
            target=SimpleNamespace(
                target_id="agent-a",
            ),
            observer_id="observer-1",
            region_code="CL-Los-Lagos",
            started_at_utc=datetime(
                2026,
                8,
                20,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        ),
    )

    second = SimpleNamespace(
        session=SimpleNamespace(
            session_id=UUID(
                "00000000-0000-0000-0000-000000000912"
            ),
            target=SimpleNamespace(
                target_id="agent-a",
            ),
            observer_id="observer-1",
            region_code="CL-Los-Lagos",
            started_at_utc=datetime(
                2026,
                8,
                21,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        ),
    )

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            raise AssertionError(
                "load_all must not be used with target filter"
            )

        def for_target(self, target_id):
            assert target_id == "agent-a"
            return [first, second]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    monkeypatch.setattr(
        cli_module,
        "discover_temporal_agent_observation_pairs",
        lambda artifacts: [],
    )

    monkeypatch.setattr(
        cli_module,
        "qualify_agent_observation",
        lambda artifact: SimpleNamespace(
            temporal_eligible=True,
            geographic_eligible=True,
        ),
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target="agent-a",
    )

    result = cli_module.agent_observatory_summary(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""
    assert captured.out == (
        "=== DLLO AGENT OBSERVATORY SUMMARY ===\n"
        "Runs:                 2\n"
        "Targets:              1\n"
        "Observers:            1\n"
        "Observed regions:     1\n"
        "Temporal eligible:    2\n"
        "Geographic eligible:  2\n"
        "Temporal pairs:\n"
        "  Comparable: 0\n"
        "  Rejected:   0\n"
        "Observation window:\n"
        "  First: 2026-08-20T12:00:00+00:00\n"
        "  Last:  2026-08-21T12:00:00+00:00\n"
    )


def test_main_dispatches_agent_observatory_summary(
    monkeypatch,
):
    captured = {}

    def fake_agent_observatory_summary(args):
        captured["command"] = args.command
        captured["history_root"] = args.history_root
        captured["target"] = args.target
        return 29

    monkeypatch.setattr(
        cli_module,
        "agent_observatory_summary",
        fake_agent_observatory_summary,
        raising=False,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "dllo",
            "agent-observatory-summary",
            "runs",
            "--target",
            "agent-a",
        ],
    )

    result = cli_module.main()

    assert result == 29
    assert captured["command"] == "agent-observatory-summary"
    assert captured["history_root"] == Path("runs")
    assert captured["target"] == "agent-a"


def test_parser_exposes_agent_observatory_summary_json_output():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-observatory-summary",
            "runs",
            "--target",
            "agent-a",
            "--json",
        ]
    )

    assert args.command == "agent-observatory-summary"
    assert args.history_root == Path("runs")
    assert args.target == "agent-a"
    assert args.json_output is True


def test_agent_observatory_summary_emits_empty_machine_readable_json(
    monkeypatch,
    capsys,
):
    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return []

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
        json_output=True,
    )

    result = cli_module.agent_observatory_summary(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload == {
        "target_filter": None,
        "runs": 0,
        "targets": 0,
        "observers": 0,
        "observed_regions": 0,
        "temporal_eligible": 0,
        "geographic_eligible": 0,
        "temporal_pairs": {
            "comparable": 0,
            "rejected": 0,
        },
        "observation_window": None,
    }


def test_agent_observatory_summary_emits_machine_readable_inventory(
    monkeypatch,
    capsys,
):
    first = SimpleNamespace(
        session=SimpleNamespace(
            session_id=UUID(
                "00000000-0000-0000-0000-000000000921"
            ),
            target=SimpleNamespace(
                target_id="agent-a",
            ),
            observer_id="observer-1",
            region_code="CL-Los-Lagos",
            started_at_utc=datetime(
                2026,
                8,
                20,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        ),
    )

    second = SimpleNamespace(
        session=SimpleNamespace(
            session_id=UUID(
                "00000000-0000-0000-0000-000000000922"
            ),
            target=SimpleNamespace(
                target_id="agent-a",
            ),
            observer_id="observer-2",
            region_code="CL-Aysen",
            started_at_utc=datetime(
                2026,
                8,
                22,
                15,
                30,
                tzinfo=timezone.utc,
            ),
        ),
    )

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            raise AssertionError(
                "load_all must not be used with target filter"
            )

        def for_target(self, target_id):
            assert target_id == "agent-a"
            return [first, second]

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    monkeypatch.setattr(
        cli_module,
        "discover_temporal_agent_observation_pairs",
        lambda artifacts: [],
    )

    monkeypatch.setattr(
        cli_module,
        "qualify_agent_observation",
        lambda artifact: SimpleNamespace(
            temporal_eligible=True,
            geographic_eligible=True,
        ),
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target="agent-a",
        json_output=True,
    )

    result = cli_module.agent_observatory_summary(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload == {
        "target_filter": "agent-a",
        "runs": 2,
        "targets": 1,
        "observers": 2,
        "observed_regions": 2,
        "temporal_eligible": 2,
        "geographic_eligible": 2,
        "temporal_pairs": {
            "comparable": 0,
            "rejected": 0,
        },
        "observation_window": {
            "first_started_at_utc": (
                "2026-08-20T12:00:00+00:00"
            ),
            "last_started_at_utc": (
                "2026-08-22T15:30:00+00:00"
            ),
        },
    }


def test_agent_observatory_summary_counts_temporal_pairs(
    monkeypatch,
    capsys,
):
    artifacts = [
        SimpleNamespace(
            session=SimpleNamespace(
                session_id=UUID(
                    "00000000-0000-0000-0000-000000000931"
                ),
                target=SimpleNamespace(
                    target_id="agent-a",
                ),
                observer_id="observer-1",
                region_code="CL-Los-Lagos",
                started_at_utc=datetime(
                    2026,
                    8,
                    20,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
        ),
        SimpleNamespace(
            session=SimpleNamespace(
                session_id=UUID(
                    "00000000-0000-0000-0000-000000000932"
                ),
                target=SimpleNamespace(
                    target_id="agent-a",
                ),
                observer_id="observer-1",
                region_code="CL-Los-Lagos",
                started_at_utc=datetime(
                    2026,
                    8,
                    21,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
        ),
    ]

    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            return artifacts

    fake_pairs = [
        SimpleNamespace(
            comparable=True,
            reasons=(),
        ),
        SimpleNamespace(
            comparable=True,
            reasons=(),
        ),
        SimpleNamespace(
            comparable=False,
            reasons=("not comparable",),
        ),
    ]

    def fake_discover(received_artifacts):
        assert received_artifacts is artifacts
        return fake_pairs

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )
    monkeypatch.setattr(
        cli_module,
        "qualify_agent_observation",
        lambda artifact: SimpleNamespace(
            temporal_eligible=True,
            geographic_eligible=True,
        ),
    )
    monkeypatch.setattr(
        cli_module,
        "discover_temporal_agent_observation_pairs",
        fake_discover,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
        json_output=True,
    )

    result = cli_module.agent_observatory_summary(args)
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload["temporal_pairs"] == {
        "comparable": 2,
        "rejected": 1,
    }


def test_agent_observatory_summary_returns_two_on_invalid_artifact(
    monkeypatch,
    capsys,
):
    class FakeHistory:
        def __init__(self, root):
            assert root == Path("runs")

        def load_all(self):
            raise cli_module.AgentLabArtifactIOError(
                "Invalid Agent Lab run artifact"
            )

    monkeypatch.setattr(
        cli_module,
        "AgentLabRunHistory",
        FakeHistory,
    )

    args = SimpleNamespace(
        history_root=Path("runs"),
        target=None,
    )

    result = cli_module.agent_observatory_summary(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert captured.err == (
        "Error: Invalid Agent Lab run artifact\n"
    )


def test_parser_exposes_agent_lab_bridge_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-lab-bridge",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
            "--history-root",
            "data/test-agent-runs",
            "--host",
            "127.0.0.1",
            "--port",
            "9877",
        ]
    )

    assert args.command == "agent-lab-bridge"
    assert args.observer_id == "observer-test"
    assert args.region_code == "CL-Los-Lagos"
    assert args.history_root == Path(
        "data/test-agent-runs"
    )
    assert args.host == "127.0.0.1"
    assert args.port == 9877


def test_agent_lab_bridge_invokes_server(
    tmp_path: Path,
    monkeypatch,
):
    captured = {}

    def fake_serve_agent_lab_bridge(
        config,
        *,
        host,
        port,
        collector_static_root,
    ):
        captured["config"] = config
        captured["host"] = host
        captured["port"] = port
        captured["collector_static_root"] = (
            collector_static_root
        )

    monkeypatch.setattr(
        cli_module,
        "serve_agent_lab_bridge",
        fake_serve_agent_lab_bridge,
        raising=False,
    )

    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-lab-bridge",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
            "--history-root",
            str(tmp_path / "agent-runs"),
            "--host",
            "127.0.0.1",
            "--port",
            "9877",
        ]
    )

    result = cli_module.agent_lab_bridge(args)

    assert result == 0

    config = captured["config"]

    assert config.observer_id == "observer-test"
    assert config.region_code == "CL-Los-Lagos"
    assert config.history_root == (
        tmp_path / "agent-runs"
    )

    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 9877
    assert captured["collector_static_root"] is None


def test_main_dispatches_agent_lab_bridge(
    monkeypatch,
):
    captured = {}

    def fake_agent_lab_bridge(args):
        captured["command"] = args.command
        captured["history_root"] = args.history_root
        return 17

    monkeypatch.setattr(
        cli_module,
        "agent_lab_bridge",
        fake_agent_lab_bridge,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dllo",
            "agent-lab-bridge",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
            "--history-root",
            "data/agent-runs",
        ],
    )

    result = cli_module.main()

    assert result == 17
    assert captured["command"] == "agent-lab-bridge"
    assert captured["history_root"] == Path(
        "data/agent-runs"
    )


def test_agent_lab_bridge_passes_collector_static_root(
    tmp_path: Path,
    monkeypatch,
):
    captured = {}

    def fake_serve_agent_lab_bridge(
        config,
        *,
        host,
        port,
        collector_static_root,
    ):
        captured["config"] = config
        captured["host"] = host
        captured["port"] = port
        captured["collector_static_root"] = (
            collector_static_root
        )

    monkeypatch.setattr(
        cli_module,
        "serve_agent_lab_bridge",
        fake_serve_agent_lab_bridge,
        raising=False,
    )

    collector_root = tmp_path / "collector-dist"

    parser = build_parser()

    args = parser.parse_args(
        [
            "agent-lab-bridge",
            "--observer-id",
            "observer-test",
            "--region-code",
            "CL-Los-Lagos",
            "--history-root",
            str(tmp_path / "agent-runs"),
            "--collector-static-root",
            str(collector_root),
        ]
    )

    result = cli_module.agent_lab_bridge(args)

    assert result == 0
    assert (
        captured["collector_static_root"]
        == collector_root
    )
