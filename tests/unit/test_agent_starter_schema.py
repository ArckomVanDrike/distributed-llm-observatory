import pytest
from pydantic import ValidationError

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    ConstraintStrength,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)


def test_agent_starter_goal_vocabulary():
    assert AgentStarterGoal.PERSONAL.value == "personal"
    assert AgentStarterGoal.KNOWLEDGE_RAG.value == "knowledge_rag"
    assert AgentStarterGoal.CODING.value == "coding"
    assert AgentStarterGoal.AUTOMATION.value == "automation"
    assert AgentStarterGoal.VOICE.value == "voice"


def test_agent_starter_evidence_source_vocabulary():
    assert EvidenceSource.OBSERVED.value == "observed"
    assert EvidenceSource.DECLARED.value == "declared"
    assert EvidenceSource.DERIVED.value == "derived"
    assert EvidenceSource.UNKNOWN.value == "unknown"


def test_agent_starter_constraint_strength_vocabulary():
    assert ConstraintStrength.HARD.value == "hard"
    assert ConstraintStrength.SOFT.value == "soft"


def test_agent_starter_technical_feasibility_vocabulary():
    assert TechnicalFeasibility.FEASIBLE.value == "feasible"
    assert TechnicalFeasibility.LIMITED.value == "limited"
    assert (
        TechnicalFeasibility.NOT_FEASIBLE.value
        == "not_feasible"
    )
    assert TechnicalFeasibility.UNKNOWN.value == "unknown"


def test_agent_starter_recommendation_vocabulary():
    assert (
        RecommendationVerdict.RECOMMENDED.value
        == "recommended"
    )
    assert (
        RecommendationVerdict.POSSIBLE.value
        == "possible"
    )
    assert (
        RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED.value
        == "possible_but_not_recommended"
    )
    assert (
        RecommendationVerdict.NOT_RECOMMENDED.value
        == "not_recommended"
    )


def test_agent_starter_recommendation_confidence_vocabulary():
    assert RecommendationConfidence.HIGH.value == "high"
    assert RecommendationConfidence.MEDIUM.value == "medium"
    assert RecommendationConfidence.LIMITED.value == "limited"


def test_agent_starter_evidence_records_observed_value():
    evidence = AgentStarterEvidence(
        key="total_memory_bytes",
        source=EvidenceSource.OBSERVED,
        value=16 * 1024**3,
    )

    assert evidence.schema_version == "0.1"
    assert evidence.key == "total_memory_bytes"
    assert evidence.source is EvidenceSource.OBSERVED
    assert evidence.value == 16 * 1024**3
    assert evidence.reason is None


def test_agent_starter_derived_evidence_requires_reason():
    evidence = AgentStarterEvidence(
        key="filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "User selected modify files and run tests."
        ),
    )

    assert evidence.value is True
    assert evidence.reason is not None


def test_agent_starter_unknown_evidence_has_no_claimed_value():
    evidence = AgentStarterEvidence(
        key="accelerator_memory_bytes",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason=(
            "Accelerator memory could not be observed."
        ),
    )

    assert evidence.value is None
    assert evidence.source is EvidenceSource.UNKNOWN


def test_agent_starter_unknown_evidence_rejects_claimed_value():
    with pytest.raises(
        ValidationError,
        match="Unknown evidence cannot record a value",
    ):
        AgentStarterEvidence(
            key="accelerator_memory_bytes",
            source=EvidenceSource.UNKNOWN,
            value=8 * 1024**3,
            reason="Accelerator memory is unknown.",
        )


def test_agent_starter_unknown_evidence_requires_reason():
    with pytest.raises(
        ValidationError,
        match="Unknown evidence must explain what is unknown",
    ):
        AgentStarterEvidence(
            key="accelerator_memory_bytes",
            source=EvidenceSource.UNKNOWN,
            value=None,
        )


def test_agent_starter_derived_evidence_requires_reason_text():
    with pytest.raises(
        ValidationError,
        match="Derived evidence must record its reason",
    ):
        AgentStarterEvidence(
            key="filesystem_write",
            source=EvidenceSource.DERIVED,
            value=True,
        )


@pytest.mark.parametrize(
    "source",
    [
        EvidenceSource.OBSERVED,
        EvidenceSource.DECLARED,
        EvidenceSource.DERIVED,
    ],
)
def test_known_agent_starter_evidence_requires_value(
    source: EvidenceSource,
):
    kwargs = {
        "key": "example",
        "source": source,
        "value": None,
    }

    if source is EvidenceSource.DERIVED:
        kwargs["reason"] = "Derived from user choice."

    with pytest.raises(
        ValidationError,
        match="Known evidence must record a value",
    ):
        AgentStarterEvidence(**kwargs)
