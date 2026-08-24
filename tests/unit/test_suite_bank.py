import json
from pathlib import Path

import pytest

from observer.core.suite_bank import (
    SuiteBank,
    SuiteBankError,
)
from schemas.benchmark import BenchmarkFamily


def test_loads_canonical_agent_suite():
    suites = SuiteBank(
        Path("benchmark/suites"),
    ).load_enabled()

    suite = next(
        suite
        for suite in suites
        if (
            suite.suite_id == "agent-core"
            and suite.suite_version == "0.1"
        )
    )

    assert suite.family is BenchmarkFamily.AGENT
    assert suite.task_ids == [
        "agent-filesystem-001",
    ]


def test_suite_bank_loads_valid_suite(tmp_path: Path):
    path = tmp_path / "suite.json"

    path.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "suite_id": "agent-test",
                "suite_version": "0.1",
                "family": "agent",
                "task_ids": [
                    "agent-task-001",
                ],
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    suite = SuiteBank(tmp_path).load_suite(path)

    assert suite.suite_id == "agent-test"
    assert suite.suite_version == "0.1"


def test_suite_bank_rejects_invalid_json(tmp_path: Path):
    path = tmp_path / "suite.json"
    path.write_text(
        "{invalid",
        encoding="utf-8",
    )

    with pytest.raises(
        SuiteBankError,
        match="Invalid JSON",
    ):
        SuiteBank(tmp_path).load_suite(path)


def test_suite_bank_rejects_invalid_suite(tmp_path: Path):
    path = tmp_path / "suite.json"

    path.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "suite_id": "agent-test",
                "suite_version": "0.1",
                "family": "agent",
                "task_ids": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        SuiteBankError,
        match="Invalid benchmark suite",
    ):
        SuiteBank(tmp_path).load_suite(path)


def test_suite_bank_rejects_missing_root(tmp_path: Path):
    missing = tmp_path / "missing"

    with pytest.raises(
        SuiteBankError,
        match="does not exist",
    ):
        SuiteBank(missing).load_all()


def test_suite_bank_rejects_duplicate_suite_identity(
    tmp_path: Path,
):
    payload = {
        "schema_version": "0.1",
        "suite_id": "agent-test",
        "suite_version": "0.1",
        "family": "agent",
        "task_ids": [
            "agent-task-001",
        ],
    }

    (tmp_path / "first.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    (tmp_path / "second.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        SuiteBankError,
        match="Duplicate benchmark suite",
    ):
        SuiteBank(tmp_path).load_all()


def test_load_enabled_excludes_disabled_suites(
    tmp_path: Path,
):
    enabled = {
        "schema_version": "0.1",
        "suite_id": "agent-enabled",
        "suite_version": "0.1",
        "family": "agent",
        "task_ids": [
            "agent-task-001",
        ],
        "enabled": True,
    }

    disabled = {
        "schema_version": "0.1",
        "suite_id": "agent-disabled",
        "suite_version": "0.1",
        "family": "agent",
        "task_ids": [
            "agent-task-002",
        ],
        "enabled": False,
    }

    (tmp_path / "enabled.json").write_text(
        json.dumps(enabled),
        encoding="utf-8",
    )
    (tmp_path / "disabled.json").write_text(
        json.dumps(disabled),
        encoding="utf-8",
    )

    suites = SuiteBank(tmp_path).load_enabled()

    assert [
        suite.suite_id
        for suite in suites
    ] == [
        "agent-enabled",
    ]
