import pytest
from pydantic import ValidationError

from schemas.model_profile import (
    ExecutionLocation,
    ModelProfile,
)


def test_model_profile_describes_local_quantized_model():
    profile = ModelProfile(
        model_id="example-7b",
        parameter_count=7_000_000_000,
        quantization="q4_k_m",
        context_window_tokens=8192,
        runtime="llama.cpp",
        execution_location=ExecutionLocation.ON_DEVICE,
    )

    assert profile.schema_version == "0.1"
    assert profile.model_id == "example-7b"
    assert profile.parameter_count == 7_000_000_000
    assert profile.quantization == "q4_k_m"
    assert profile.context_window_tokens == 8192
    assert profile.runtime == "llama.cpp"
    assert profile.execution_location is ExecutionLocation.ON_DEVICE


def test_model_profile_supports_partial_information():
    profile = ModelProfile(
        model_id="custom-agent-model",
        execution_location=ExecutionLocation.REMOTE,
    )

    assert profile.parameter_count is None
    assert profile.quantization is None
    assert profile.runtime is None


def test_model_profile_supports_hybrid_execution():
    profile = ModelProfile(
        model_id="hybrid-system",
        execution_location=ExecutionLocation.HYBRID,
    )

    assert profile.execution_location is ExecutionLocation.HYBRID


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("parameter_count", 0),
        ("parameter_count", -1),
        ("context_window_tokens", 0),
        ("context_window_tokens", -1),
    ],
)
def test_model_profile_rejects_non_positive_numeric_values(
    field: str,
    value: int,
):
    values = {
        "model_id": "example-model",
        "execution_location": ExecutionLocation.ON_DEVICE,
        field: value,
    }

    with pytest.raises(ValidationError):
        ModelProfile(**values)
