import pytest
from pydantic import ValidationError

from schemas.compatibility import (
    AssessmentBasis,
    CompatibilityAssessment,
    CompatibilityVerdict,
)


def test_estimated_compatible_assessment():
    assessment = CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=CompatibilityVerdict.COMPATIBLE,
        summary="Configuration appears suitable for local execution.",
        confidence=0.8,
        estimated_required_memory_bytes=6 * 1024**3,
        reasons=[
            "Estimated model footprint fits available memory.",
        ],
        recommendations=[
            "Validate with an Agent Lab measured run.",
        ],
    )

    assert assessment.schema_version == "0.1"
    assert assessment.basis is AssessmentBasis.ESTIMATED
    assert assessment.verdict is CompatibilityVerdict.COMPATIBLE
    assert assessment.confidence == 0.8


def test_measured_compatible_assessment():
    assessment = CompatibilityAssessment(
        basis=AssessmentBasis.MEASURED,
        verdict=CompatibilityVerdict.COMPATIBLE,
        summary="Configuration completed the measured workload.",
        measured_peak_memory_bytes=7 * 1024**3,
        reasons=[
            "The benchmark completed without memory exhaustion.",
        ],
    )

    assert assessment.basis is AssessmentBasis.MEASURED
    assert assessment.measured_peak_memory_bytes == 7 * 1024**3


def test_constrained_configuration():
    assessment = CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=CompatibilityVerdict.CONSTRAINED,
        summary="Configuration is likely to run with limited headroom.",
        recommendations=[
            "Reduce context size.",
            "Use a smaller or more aggressively quantized model.",
        ],
    )

    assert assessment.verdict is CompatibilityVerdict.CONSTRAINED
    assert len(assessment.recommendations) == 2


def test_unknown_when_information_is_insufficient():
    assessment = CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=CompatibilityVerdict.UNKNOWN,
        summary="Available device information is insufficient.",
    )

    assert assessment.verdict is CompatibilityVerdict.UNKNOWN


@pytest.mark.parametrize(
    "confidence",
    [
        -0.01,
        1.01,
    ],
)
def test_confidence_must_be_between_zero_and_one(
    confidence: float,
):
    with pytest.raises(ValidationError):
        CompatibilityAssessment(
            basis=AssessmentBasis.ESTIMATED,
            verdict=CompatibilityVerdict.COMPATIBLE,
            summary="Example.",
            confidence=confidence,
        )


@pytest.mark.parametrize(
    "field",
    [
        "estimated_required_memory_bytes",
        "measured_peak_memory_bytes",
    ],
)
def test_memory_measurements_must_be_positive(
    field: str,
):
    with pytest.raises(ValidationError):
        CompatibilityAssessment(
            basis=AssessmentBasis.ESTIMATED,
            verdict=CompatibilityVerdict.CONSTRAINED,
            summary="Example.",
            **{field: 0},
        )
