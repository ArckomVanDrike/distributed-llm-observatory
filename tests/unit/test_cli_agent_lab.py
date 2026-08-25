from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

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
    assert "Tasks:             1" in output
    assert "Passed:            1" in output
    assert "Pass rate:         100.00%" in output
    assert "Median latency:    4.50 ms" in output


def test_agent_test_returns_zero_when_benchmark_fails(
    monkeypatch,
    capsys,
):
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
    artifact = object()
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
                to_artifact=lambda: object(),
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
