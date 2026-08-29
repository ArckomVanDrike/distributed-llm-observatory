import pytest
from pydantic import ValidationError

from schemas.execution_environment import (
    ExecutionAccessStatus,
    ExecutionEnvironment,
    ExecutionInterface,
    ExecutionPlatform,
)


def test_native_android_environment_records_explicit_runtimes():
    environment = ExecutionEnvironment(
        platform=ExecutionPlatform.ANDROID,
        interface=ExecutionInterface.NATIVE,
        available_runtimes=[
            "llama.cpp",
        ],
        accelerator_access=ExecutionAccessStatus.LIMITED,
        filesystem_access=ExecutionAccessStatus.AVAILABLE,
        limitations=[
            "Sustained inference may be thermally constrained.",
        ],
    )

    assert environment.schema_version == "0.1"
    assert environment.platform is ExecutionPlatform.ANDROID
    assert environment.interface is ExecutionInterface.NATIVE
    assert environment.available_runtimes == [
        "llama.cpp",
    ]
    assert (
        environment.accelerator_access
        is ExecutionAccessStatus.LIMITED
    )
    assert (
        environment.filesystem_access
        is ExecutionAccessStatus.AVAILABLE
    )


def test_mobile_browser_can_preserve_unknown_runtime_inventory():
    environment = ExecutionEnvironment(
        platform=ExecutionPlatform.IOS,
        interface=ExecutionInterface.BROWSER,
        available_runtimes=None,
        accelerator_access=ExecutionAccessStatus.UNKNOWN,
        filesystem_access=ExecutionAccessStatus.LIMITED,
        limitations=[
            "The browser cannot establish native runtime availability.",
        ],
    )

    assert environment.platform is ExecutionPlatform.IOS
    assert environment.interface is ExecutionInterface.BROWSER

    # None means unknown, not an observed empty runtime inventory.
    assert environment.available_runtimes is None
    assert (
        environment.accelerator_access
        is ExecutionAccessStatus.UNKNOWN
    )


def test_known_empty_runtime_inventory_is_distinct_from_unknown():
    environment = ExecutionEnvironment(
        platform=ExecutionPlatform.LINUX,
        interface=ExecutionInterface.NATIVE,
        available_runtimes=[],
    )

    assert environment.available_runtimes == []
    assert environment.available_runtimes is not None


def test_execution_environment_rejects_duplicate_runtime_names():
    with pytest.raises(
        ValidationError,
        match="runtime",
    ):
        ExecutionEnvironment(
            platform=ExecutionPlatform.ANDROID,
            interface=ExecutionInterface.NATIVE,
            available_runtimes=[
                "llama.cpp",
                "llama.cpp",
            ],
        )
