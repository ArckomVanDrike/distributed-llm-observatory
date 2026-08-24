from pathlib import Path

from observer.core.fixture_bank import FixtureBank
from observer.core.task_bank import TaskBank


def test_repository_task_fixture_references_resolve():
    tasks = TaskBank(
        Path("benchmark/tasks"),
    ).load_all()

    fixtures = FixtureBank(
        Path("benchmark/fixtures"),
    ).load_all()

    fixtures_by_id = {
        fixture.fixture_id: fixture
        for fixture in fixtures
    }

    referenced_fixture_ids = {
        task.fixture_id
        for task in tasks
        if task.fixture_id is not None
    }

    assert referenced_fixture_ids

    for fixture_id in referenced_fixture_ids:
        assert fixture_id in fixtures_by_id


def test_canonical_filesystem_task_uses_empty_workspace_fixture():
    tasks = TaskBank(
        Path("benchmark/tasks"),
    ).load_all()

    fixtures = FixtureBank(
        Path("benchmark/fixtures"),
    ).load_all()

    task = next(
        task
        for task in tasks
        if task.task_id == "agent-filesystem-001"
    )

    fixture = next(
        fixture
        for fixture in fixtures
        if fixture.fixture_id == task.fixture_id
    )

    assert task.fixture_id == "filesystem-empty-v0-1"
    assert fixture.files == []
