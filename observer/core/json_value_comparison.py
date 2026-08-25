from __future__ import annotations

from typing import Any


def json_scalar_equal(
    observed: Any,
    expected: Any,
) -> bool:
    if isinstance(observed, bool) or isinstance(expected, bool):
        return (
            isinstance(observed, bool)
            and isinstance(expected, bool)
            and observed == expected
        )

    observed_is_number = isinstance(
        observed,
        (int, float),
    )
    expected_is_number = isinstance(
        expected,
        (int, float),
    )

    if observed_is_number or expected_is_number:
        return (
            observed_is_number
            and expected_is_number
            and observed == expected
        )

    return (
        type(observed) is type(expected)
        and observed == expected
    )


def json_flat_object_equal(
    observed: dict[str, Any],
    expected: dict[str, Any],
) -> bool:
    if observed.keys() != expected.keys():
        return False

    return all(
        json_scalar_equal(
            observed[key],
            expected[key],
        )
        for key in expected
    )
