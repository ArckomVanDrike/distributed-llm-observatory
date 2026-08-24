from __future__ import annotations

from schemas.compatibility import (
    AssessmentBasis,
    CompatibilityAssessment,
    CompatibilityVerdict,
)
from schemas.hardware import HardwareProfile
from schemas.model_profile import (
    ExecutionLocation,
    ModelProfile,
)

_QUANTIZATION_BITS: dict[str, float] = {
    "q2": 2.0,
    "q3": 3.0,
    "q4": 4.0,
    "q4_k_s": 4.0,
    "q4_k_m": 4.0,
    "q5": 5.0,
    "q5_k_s": 5.0,
    "q5_k_m": 5.0,
    "q6": 6.0,
    "q6_k": 6.0,
    "q8": 8.0,
    "q8_0": 8.0,
    "fp16": 16.0,
    "float16": 16.0,
    "bf16": 16.0,
    "fp32": 32.0,
    "float32": 32.0,
}

_WEIGHT_OVERHEAD_FACTOR = 1.35

_COMPATIBLE_HEADROOM_RATIO = 2.0
_CONSTRAINED_HEADROOM_RATIO = 1.25


def _unknown(
    summary: str,
    *,
    recommendations: list[str] | None = None,
) -> CompatibilityAssessment:
    return CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=CompatibilityVerdict.UNKNOWN,
        summary=summary,
        confidence=0.0,
        recommendations=recommendations or [],
    )


def _quantization_bits(
    quantization: str | None,
) -> float | None:
    if quantization is None:
        return None

    normalized = quantization.strip().lower()

    return _QUANTIZATION_BITS.get(normalized)


def estimate_local_compatibility(
    hardware: HardwareProfile,
    model: ModelProfile,
) -> CompatibilityAssessment:
    if model.execution_location is not ExecutionLocation.ON_DEVICE:
        return _unknown(
            "Local hardware compatibility cannot be estimated "
            "for a model that is not explicitly configured for "
            "on-device execution."
        )

    if hardware.total_memory_bytes is None:
        return _unknown(
            "Total device memory is unavailable.",
            recommendations=[
                "Collect or declare total device memory before "
                "estimating local compatibility.",
            ],
        )

    if model.parameter_count is None:
        return _unknown(
            "Model parameter count is unavailable.",
            recommendations=[
                "Provide the model parameter count before "
                "estimating its local memory footprint.",
            ],
        )

    bits_per_parameter = _quantization_bits(
        model.quantization
    )

    if bits_per_parameter is None:
        return _unknown(
            "Model quantization is unavailable or unsupported by "
            "the current estimator.",
            recommendations=[
                "Provide a recognized quantization format or "
                "validate the configuration with a measured run.",
            ],
        )

    raw_weight_bytes = (
        model.parameter_count
        * bits_per_parameter
        / 8
    )

    estimated_required_memory_bytes = int(
        raw_weight_bytes
        * _WEIGHT_OVERHEAD_FACTOR
    )

    headroom_ratio = (
        hardware.total_memory_bytes
        / estimated_required_memory_bytes
    )

    common_reason = (
        "Estimate includes model weights plus a conservative "
        "fixed overhead, but does not model KV cache, runtime "
        "behavior, agent components, or current system memory "
        "pressure."
    )

    if headroom_ratio >= _COMPATIBLE_HEADROOM_RATIO:
        return CompatibilityAssessment(
            basis=AssessmentBasis.ESTIMATED,
            verdict=CompatibilityVerdict.COMPATIBLE,
            summary=(
                "The configuration has substantial estimated "
                "memory headroom for local execution."
            ),
            confidence=0.6,
            estimated_required_memory_bytes=(
                estimated_required_memory_bytes
            ),
            reasons=[common_reason],
            recommendations=[
                "Validate the estimate with an Agent Lab "
                "measured run.",
            ],
        )

    if headroom_ratio >= _CONSTRAINED_HEADROOM_RATIO:
        return CompatibilityAssessment(
            basis=AssessmentBasis.ESTIMATED,
            verdict=CompatibilityVerdict.CONSTRAINED,
            summary=(
                "The configuration may run locally, but estimated "
                "memory headroom is limited."
            ),
            confidence=0.5,
            estimated_required_memory_bytes=(
                estimated_required_memory_bytes
            ),
            reasons=[common_reason],
            recommendations=[
                "Reduce context size if necessary.",
                "Consider a smaller or more aggressively "
                "quantized model.",
                "Validate with a measured run before treating "
                "the configuration as suitable.",
            ],
        )

    return CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=CompatibilityVerdict.NOT_RECOMMENDED,
        summary=(
            "Estimated model memory demand leaves insufficient "
            "device-memory headroom for this local configuration."
        ),
        confidence=0.6,
        estimated_required_memory_bytes=(
            estimated_required_memory_bytes
        ),
        reasons=[common_reason],
        recommendations=[
            "Use a smaller model or stronger quantization.",
            "Consider remote execution if local execution is not "
            "a requirement.",
        ],
    )
