import json
from pathlib import Path

import pytest

from observer.core.fixture_bank import (
    FixtureBank,
    FixtureBankError,
)


def write_fixture(
    path: Path,
    *,
    fixture_id: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "fixture_id": fixture_id,
                "files": [],
            }
        ),
        encoding="utf-8",
    )


def test_fixture_bank_loads_sorted_fixtures(
    tmp_path: Path,
):
    write_fixture(
        tmp_path / "b.json",
        fixture_id="fixture-b",
    )
    write_fixture(
        tmp_path / "a.json",
        fixture_id="fixture-a",
    )

    fixtures = FixtureBank(
        tmp_path
    ).load_all()

    assert [
        fixture.fixture_id
        for fixture in fixtures
    ] == [
        "fixture-a",
        "fixture-b",
    ]


def test_fixture_bank_rejects_missing_directory(
    tmp_path: Path,
):
    with pytest.raises(
        FixtureBankError,
        match="does not exist",
    ):
        FixtureBank(
            tmp_path / "missing"
        ).load_all()


def test_fixture_bank_rejects_invalid_json(
    tmp_path: Path,
):
    path = tmp_path / "invalid.json"
    path.write_text(
        "{",
        encoding="utf-8",
    )

    with pytest.raises(
        FixtureBankError,
        match="Invalid JSON",
    ):
        FixtureBank(
            tmp_path
        ).load_all()


def test_fixture_bank_rejects_invalid_fixture(
    tmp_path: Path,
):
    path = tmp_path / "invalid.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "fixture_id": "INVALID",
                "files": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        FixtureBankError,
        match="Invalid fixture",
    ):
        FixtureBank(
            tmp_path
        ).load_all()


def test_fixture_bank_rejects_duplicate_ids(
    tmp_path: Path,
):
    write_fixture(
        tmp_path / "one.json",
        fixture_id="same-fixture",
    )
    write_fixture(
        tmp_path / "two.json",
        fixture_id="same-fixture",
    )

    with pytest.raises(
        FixtureBankError,
        match="Duplicate fixture_id",
    ):
        FixtureBank(
            tmp_path
        ).load_all()
