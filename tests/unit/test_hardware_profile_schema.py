import pytest
from pydantic import ValidationError

from schemas.hardware import (
    AcceleratorKind,
    AcceleratorProfile,
    DeviceClass,
    HardwareProfile,
    HardwareProfileSource,
)


def test_hardware_profile_describes_desktop():
    profile = HardwareProfile(
        device_class=DeviceClass.DESKTOP,
        source=HardwareProfileSource.NATIVE,
        os_name="Linux",
        architecture="x86_64",
        cpu_model="Intel Core i5",
        logical_cpu_count=8,
        total_memory_bytes=8 * 1024**3,
        accelerators=[],
    )

    assert profile.schema_version == "0.1"
    assert profile.device_class is DeviceClass.DESKTOP
    assert profile.total_memory_bytes == 8 * 1024**3
    assert profile.accelerators == []


def test_hardware_profile_supports_mobile_partial_scan():
    profile = HardwareProfile(
        device_class=DeviceClass.PHONE,
        source=HardwareProfileSource.BROWSER_LIMITED,
        os_name="Android",
        architecture="arm64",
        logical_cpu_count=8,
        total_memory_bytes=None,
        accelerators=[],
        limitations=[
            "Total memory is unavailable from this browser.",
            "GPU/NPU details are unavailable.",
        ],
    )

    assert profile.device_class is DeviceClass.PHONE
    assert profile.total_memory_bytes is None
    assert len(profile.limitations) == 2


def test_hardware_profile_can_describe_accelerator():
    profile = HardwareProfile(
        device_class=DeviceClass.LAPTOP,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=16 * 1024**3,
        accelerators=[
            AcceleratorProfile(
                kind=AcceleratorKind.GPU,
                name="Example GPU",
                memory_bytes=8 * 1024**3,
            ),
        ],
    )

    assert profile.accelerators[0].kind is AcceleratorKind.GPU
    assert profile.accelerators[0].memory_bytes == 8 * 1024**3


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
    ],
)
def test_hardware_profile_rejects_invalid_memory(value: int):
    with pytest.raises(ValidationError):
        HardwareProfile(
            device_class=DeviceClass.DESKTOP,
            source=HardwareProfileSource.NATIVE,
            total_memory_bytes=value,
        )


def test_hardware_profile_has_no_stable_device_identifier():
    fields = HardwareProfile.model_fields

    assert "serial_number" not in fields
    assert "mac_address" not in fields
    assert "device_uuid" not in fields
