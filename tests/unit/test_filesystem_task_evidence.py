from pathlib import Path

from observer.core.filesystem_task_evidence import (
    FilesystemTaskEvidenceCollector,
)


def test_filesystem_evidence_reports_matching_file(
    tmp_path: Path,
):
    path = tmp_path / "dllo-probe.txt"
    path.write_text(
        "DLLO-AGENT-SMOKE-001",
        encoding="utf-8",
    )

    collector = FilesystemTaskEvidenceCollector(
        workspace=tmp_path,
        relative_path="dllo-probe.txt",
        expected_content="DLLO-AGENT-SMOKE-001",
    )

    evidence = {
        item.criterion_id: item
        for item in collector.collect()
    }

    assert evidence["file-created"].passed is True
    assert evidence["file-contents-match"].passed is True


def test_filesystem_evidence_reports_missing_file(
    tmp_path: Path,
):
    collector = FilesystemTaskEvidenceCollector(
        workspace=tmp_path,
        relative_path="dllo-probe.txt",
        expected_content="DLLO-AGENT-SMOKE-001",
    )

    evidence = {
        item.criterion_id: item
        for item in collector.collect()
    }

    assert evidence["file-created"].passed is False
    assert evidence["file-contents-match"].passed is False


def test_filesystem_evidence_reports_wrong_contents(
    tmp_path: Path,
):
    path = tmp_path / "dllo-probe.txt"
    path.write_text(
        "wrong",
        encoding="utf-8",
    )

    collector = FilesystemTaskEvidenceCollector(
        workspace=tmp_path,
        relative_path="dllo-probe.txt",
        expected_content="DLLO-AGENT-SMOKE-001",
    )

    evidence = {
        item.criterion_id: item
        for item in collector.collect()
    }

    assert evidence["file-created"].passed is True
    assert evidence["file-contents-match"].passed is False
