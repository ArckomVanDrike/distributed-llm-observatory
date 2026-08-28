from __future__ import annotations

from schemas.agent_starter import TechnicalFeasibility
from schemas.compatibility import (
    CompatibilityAssessment,
    CompatibilityVerdict,
)


def technical_feasibility_from_compatibility(
    assessment: CompatibilityAssessment,
) -> TechnicalFeasibility:
    if assessment.verdict is CompatibilityVerdict.COMPATIBLE:
        return TechnicalFeasibility.FEASIBLE

    if assessment.verdict is CompatibilityVerdict.CONSTRAINED:
        return TechnicalFeasibility.LIMITED

    if assessment.verdict is CompatibilityVerdict.NOT_RECOMMENDED:
        return TechnicalFeasibility.LIMITED

    return TechnicalFeasibility.UNKNOWN
