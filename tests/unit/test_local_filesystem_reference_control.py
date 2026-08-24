from pathlib import Path

from observer.sut.base import (
    SUTExecutionContext,
    SUTRequest,
)
from observer.sut.local_filesystem import (
    LocalFilesystemSUTAdapter,
    LocalFilesystemWriteControl,
)


def test_reference_sut_uses_explicit_control_not_request_metadata(
    tmp_path: Path,
):
    adapter = LocalFilesystemSUTAdapter(
        tmp_path,
        control=LocalFilesystemWriteControl(
            path="dllo-probe.txt",
            content="DLLO-AGENT-SMOKE-001",
        ),
    )

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
                "path": "wrong.txt",
                "content": "WRONG",
            },
        ),
    )

    assert result.task_completed is True

    assert (
        tmp_path / "dllo-probe.txt"
    ).read_text(encoding="utf-8") == "DLLO-AGENT-SMOKE-001"

    assert not (
        tmp_path / "wrong.txt"
    ).exists()


def test_reference_sut_requires_explicit_control(
    tmp_path: Path,
):
    adapter = LocalFilesystemSUTAdapter(
        tmp_path,
    )

    context = SUTExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="agent-filesystem-001",
        target_id="local-filesystem-sut",
    )

    import pytest

    with pytest.raises(
        ValueError,
        match="explicit control",
    ):
        adapter.execute(
            context,
            SUTRequest(
                task="Create the requested probe file.",
                metadata={
                    "operation": "write_file",
                    "path": "should-not-exist.txt",
                    "content": "WRONG",
                },
            ),
        )

    assert not (
        tmp_path / "should-not-exist.txt"
    ).exists()
