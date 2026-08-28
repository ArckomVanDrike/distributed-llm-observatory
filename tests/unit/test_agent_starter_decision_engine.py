from observer.core.agent_starter_decision_engine import (
    technical_feasibility_from_compatibility,
)
from schemas.agent_starter import TechnicalFeasibility
from schemas.compatibility import (
    AssessmentBasis,
    CompatibilityAssessment,
    CompatibilityVerdict,
)


def _assessment(
    verdict: CompatibilityVerdict,
) -> CompatibilityAssessment:
    return CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=verdict,
        summary="Compatibility result.",
    )


def test_compatible_maps_to_feasible():
    result = technical_feasibility_from_compatibility(
        _assessment(CompatibilityVerdict.COMPATIBLE)
    )

    assert result is TechnicalFeasibility.FEASIBLE


def test_constrained_maps_to_limited():
    result = technical_feasibility_from_compatibility(
        _assessment(CompatibilityVerdict.CONSTRAINED)
    )

    assert result is TechnicalFeasibility.LIMITED


def test_unknown_maps_to_unknown():
    result = technical_feasibility_from_compatibility(
        _assessment(CompatibilityVerdict.UNKNOWN)
    )

    assert result is TechnicalFeasibility.UNKNOWN


def test_hardware_not_recommended_does_not_become_agent_recommendation():
    result = technical_feasibility_from_compatibility(
        _assessment(
            CompatibilityVerdict.NOT_RECOMMENDED
        )
    )

    assert result is TechnicalFeasibility.LIMITED
