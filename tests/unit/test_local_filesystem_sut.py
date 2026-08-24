from pathlib import Path

import pytest

from observer.sut.local_filesystem import LocalFilesystemSUTAdapter


def test_local_filesystem_sut_requires_existing_workspace(
    tmp_path: Path,
):
    with pytest.raises(
        ValueError,
        match="workspace",
    ):
        LocalFilesystemSUTAdapter(
            tmp_path / "missing",
        )


def test_local_filesystem_sut_requires_directory(
    tmp_path: Path,
):
    file_path = tmp_path / "not-a-directory"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="directory",
    ):
        LocalFilesystemSUTAdapter(
            file_path,
        )


def test_local_filesystem_sut_resolves_workspace(
    tmp_path: Path,
):
    adapter = LocalFilesystemSUTAdapter(
        tmp_path,
    )

    assert adapter.workspace == tmp_path.resolve()


def test_local_filesystem_sut_writes_file_inside_workspace(
    tmp_path: Path,
):
    from observer.sut.base import (
        SUTExecutionContext,
        SUTRequest,
    )

    adapter = LocalFilesystemSUTAdapter(tmp_path)

    context = SUTExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="agent-filesystem-001",
        target_id="local-filesystem-sut",
    )

    result = adapter.execute(
        context,
        SUTRequest(
            task="Create the requested probe file.",
            metadata={
                "operation": "write_file",
                "path": "dllo-probe.txt",
                "content": "DLLO-AGENT-SMOKE-001",
            },
        ),
    )

    probe = tmp_path / "dllo-probe.txt"

    assert probe.read_text(encoding="utf-8") == "DLLO-AGENT-SMOKE-001"
    assert result.task_completed is True

    assert not hasattr(result, "criterion_evidence")


def test_local_filesystem_sut_rejects_absolute_path(
    tmp_path: Path,
):
    from observer.sut.base import (
        SUTExecutionContext,
        SUTRequest,
    )

    adapter = LocalFilesystemSUTAdapter(tmp_path)

    context = SUTExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="agent-filesystem-001",
        target_id="local-filesystem-sut",
    )

    with pytest.raises(
        ValueError,
        match="relative",
    ):
        adapter.execute(
            context,
            SUTRequest(
                task="Write a file.",
                metadata={
                    "operation": "write_file",
                    "path": "/tmp/escape.txt",
                    "content": "x",
                },
            ),
        )


def test_local_filesystem_sut_rejects_parent_escape(
    tmp_path: Path,
):
    from observer.sut.base import (
        SUTExecutionContext,
        SUTRequest,
    )

    adapter = LocalFilesystemSUTAdapter(tmp_path)

    context = SUTExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="agent-filesystem-001",
        target_id="local-filesystem-sut",
    )

    with pytest.raises(
        ValueError,
        match="escapes the workspace",
    ):
        adapter.execute(
            context,
            SUTRequest(
                task="Write a file.",
                metadata={
                    "operation": "write_file",
                    "path": "../escape.txt",
                    "content": "x",
                },
            ),
        )
