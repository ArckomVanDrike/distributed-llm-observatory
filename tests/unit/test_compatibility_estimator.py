from observer.core.compatibility_estimator import (
    estimate_local_compatibility,
)
from schemas.compatibility import (
    AssessmentBasis,
    CompatibilityVerdict,
)
from schemas.hardware import (
    DeviceClass,
    HardwareProfile,
    HardwareProfileSource,
)
from schemas.model_profile import (
    ExecutionLocation,
    ModelProfile,
)


def make_hardware(
    memory_gib: int | None,
) -> HardwareProfile:
    return HardwareProfile(
        device_class=DeviceClass.DESKTOP,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=(
            memory_gib * 1024**3
            if memory_gib is not None
            else None
        ),
    )


def test_remote_model_is_not_assessed_against_local_memory():
    result = estimate_local_compatibility(
        make_hardware(8),
        ModelProfile(
            model_id="remote-model",
            parameter_count=30_000_000_000,
            execution_location=ExecutionLocation.REMOTE,
        ),
    )

    assert result.basis is AssessmentBasis.ESTIMATED
    assert result.verdict is CompatibilityVerdict.UNKNOWN


def test_missing_memory_produces_unknown():
    result = estimate_local_compatibility(
        make_hardware(None),
        ModelProfile(
            model_id="example-7b",
            parameter_count=7_000_000_000,
            quantization="q4",
            execution_location=ExecutionLocation.ON_DEVICE,
        ),
    )

    assert result.verdict is CompatibilityVerdict.UNKNOWN


def test_missing_parameter_count_produces_unknown():
    result = estimate_local_compatibility(
        make_hardware(16),
        ModelProfile(
            model_id="unknown-size-model",
            quantization="q4",
            execution_location=ExecutionLocation.ON_DEVICE,
        ),
    )

    assert result.verdict is CompatibilityVerdict.UNKNOWN


def test_q4_7b_is_estimated_compatible_with_16_gib():
    result = estimate_local_compatibility(
        make_hardware(16),
        ModelProfile(
            model_id="example-7b",
            parameter_count=7_000_000_000,
            quantization="q4",
            execution_location=ExecutionLocation.ON_DEVICE,
        ),
    )

    assert result.verdict is CompatibilityVerdict.COMPATIBLE
    assert result.estimated_required_memory_bytes is not None


def test_q4_7b_is_constrained_with_8_gib():
    result = estimate_local_compatibility(
        make_hardware(8),
        ModelProfile(
            model_id="example-7b",
            parameter_count=7_000_000_000,
            quantization="q4",
            execution_location=ExecutionLocation.ON_DEVICE,
        ),
    )

    assert result.verdict is CompatibilityVerdict.CONSTRAINED


def test_q4_30b_is_not_recommended_with_8_gib():
    result = estimate_local_compatibility(
        make_hardware(8),
        ModelProfile(
            model_id="example-30b",
            parameter_count=30_000_000_000,
            quantization="q4",
            execution_location=ExecutionLocation.ON_DEVICE,
        ),
    )

    assert result.verdict is CompatibilityVerdict.NOT_RECOMMENDED


def test_unknown_quantization_does_not_guess():
    result = estimate_local_compatibility(
        make_hardware(16),
        ModelProfile(
            model_id="example-model",
            parameter_count=7_000_000_000,
            quantization="mystery-format",
            execution_location=ExecutionLocation.ON_DEVICE,
        ),
    )

    assert result.verdict is CompatibilityVerdict.UNKNOWN
