from pathlib import Path

from observer.cli import (
    build_parser,
    task_list,
    task_show,
)


def test_parser_exposes_task_commands():
    parser = build_parser()

    list_args = parser.parse_args(
        ["task-list"]
    )
    show_args = parser.parse_args(
        [
            "task-show",
            "agent-filesystem-001",
        ]
    )

    assert list_args.command == "task-list"
    assert show_args.command == "task-show"
    assert (
        show_args.task_id
        == "agent-filesystem-001"
    )


def test_task_list_reports_enabled_repository_tasks(
    capsys,
):
    parser = build_parser()
    args = parser.parse_args(
        ["task-list"]
    )

    result = task_list(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "=== DLLO BENCHMARK TASKS ===" in output
    assert "Tasks:             6" in output
    assert "agent-filesystem-001" in output
    assert "agent-protocol-smoke-001" in output
    assert "agent-protocol-instruction-001" in output
    assert "agent-protocol-structured-output-001" in output
    assert "agent-protocol-action-001" in output
    assert "agent-protocol-tool-selection-001" in output
    assert "agent" in output
    assert "technical" in output
    assert "easy" in output


def test_task_show_reports_canonical_task(
    capsys,
):
    parser = build_parser()
    args = parser.parse_args(
        [
            "task-show",
            "agent-filesystem-001",
        ]
    )

    result = task_show(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "=== DLLO BENCHMARK TASK ===" in output
    assert (
        "Task ID:           agent-filesystem-001"
        in output
    )
    assert "Family:            agent" in output
    assert "Category:          technical" in output
    assert "Difficulty:        easy" in output
    assert (
        "Evaluator:         "
        "deterministic-evidence-v0-1"
        in output
    )
    assert "filesystem" in output
    assert "text" in output
    assert "file-created" in output
    assert "file-contents-match" in output
    assert (
        "DLLO-AGENT-SMOKE-001"
        in output
    )


def test_task_show_returns_not_found(
    tmp_path: Path,
    capsys,
):
    task_bank = tmp_path / "tasks"
    task_bank.mkdir()

    parser = build_parser()
    args = parser.parse_args(
        [
            "task-show",
            "missing-task",
            "--task-bank",
            str(task_bank),
        ]
    )

    result = task_show(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert (
        "Task not found: missing-task"
        in captured.err
    )


def test_task_list_reports_invalid_task_bank(
    tmp_path: Path,
    capsys,
):
    parser = build_parser()
    args = parser.parse_args(
        [
            "task-list",
            "--task-bank",
            str(tmp_path / "missing"),
        ]
    )

    result = task_list(args)
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert (
        "Task bank directory does not exist"
        in captured.err
    )
