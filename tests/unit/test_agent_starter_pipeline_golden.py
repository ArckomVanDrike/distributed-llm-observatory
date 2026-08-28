from observer.core.agent_starter_pipeline import (
    run_agent_starter_pipeline,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterIntake,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
from schemas.compatibility import (
    AssessmentBasis,
    CompatibilityAssessment,
    CompatibilityVerdict,
)


def _compatible(summary: str) -> CompatibilityAssessment:
    return CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=CompatibilityVerdict.COMPATIBLE,
        summary=summary,
        confidence=0.6,
    )


def test_pipeline_golden_01_local_private_coding():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="source_code_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    plan = run_agent_starter_pipeline(
        intake=intake,
        compatibility_by_architecture={
            "local-coding-agent": _compatible(
                "The local coding architecture has adequate "
                "technical headroom."
            ),
            "remote-coding-agent": _compatible(
                "The remote coding architecture is technically "
                "available."
            ),
        },
    )

    assert [
        requirement.key
        for requirement in plan.requirements
    ] == [
        "source_code_must_stay_local",
    ]

    assert [
        candidate.architecture_id
        for candidate in plan.candidate_assessments
    ] == [
        "local-coding-agent",
        "remote-coding-agent",
    ]

    local, remote = plan.candidate_assessments

    assert (
        local.technical_feasibility
        is TechnicalFeasibility.FEASIBLE
    )
    assert (
        local.recommendation
        is RecommendationVerdict.POSSIBLE
    )
    assert (
        local.confidence
        is RecommendationConfidence.MEDIUM
    )

    assert (
        remote.technical_feasibility
        is TechnicalFeasibility.FEASIBLE
    )
    assert (
        remote.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert (
        remote.confidence
        is RecommendationConfidence.HIGH
    )
    assert [
        requirement.key
        for requirement in remote.blocking_requirements
    ] == [
        "source_code_must_stay_local",
    ]

    assert plan.constraint_conflict is None


def test_pipeline_golden_04_tiny_documents_rag_unnecessary():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="corpus_is_very_small",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    plan = run_agent_starter_pipeline(
        intake=intake,
        compatibility_by_architecture={
            "direct-context-knowledge-assistant": _compatible(
                "The direct-context architecture is technically "
                "available."
            ),
            "full-rag-pipeline": _compatible(
                "The full RAG architecture is technically "
                "available."
            ),
        },
    )

    assert plan.requirements == []

    assert [
        candidate.architecture_id
        for candidate in plan.candidate_assessments
    ] == [
        "direct-context-knowledge-assistant",
        "full-rag-pipeline",
    ]

    direct_context, full_rag = plan.candidate_assessments

    assert (
        direct_context.technical_feasibility
        is TechnicalFeasibility.FEASIBLE
    )
    assert (
        direct_context.recommendation
        is RecommendationVerdict.RECOMMENDED
    )
    assert (
        direct_context.confidence
        is RecommendationConfidence.HIGH
    )

    assert (
        full_rag.technical_feasibility
        is TechnicalFeasibility.FEASIBLE
    )
    assert (
        full_rag.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert (
        full_rag.confidence
        is RecommendationConfidence.HIGH
    )

    direct_evidence = {
        evidence.key: evidence.value
        for evidence in direct_context.supporting_evidence
    }

    assert direct_evidence["corpus_fits_direct_context"] is True
    assert direct_evidence["retrieval_required"] is False
    assert (
        direct_evidence["candidate_uses_retrieval_pipeline"]
        is False
    )

    assert plan.constraint_conflict is None


def test_pipeline_golden_09_deterministic_workflow_needs_no_ai():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            AgentStarterEvidence(
                key="workflow_deterministic",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    plan = run_agent_starter_pipeline(
        intake=intake,
        compatibility_by_architecture={
            "traditional-deterministic-automation": _compatible(
                "Traditional automation is technically available."
            ),
            "supervised-automation-agent": _compatible(
                "The supervised automation agent is technically available."
            ),
            "autonomous-workflow-agent": _compatible(
                "The autonomous workflow agent is technically available."
            ),
        },
    )

    assert [
        candidate.architecture_id
        for candidate in plan.candidate_assessments
    ] == [
        "traditional-deterministic-automation",
        "supervised-automation-agent",
        "autonomous-workflow-agent",
    ]

    traditional, supervised, autonomous = (
        plan.candidate_assessments
    )

    assert (
        traditional.technical_feasibility
        is TechnicalFeasibility.FEASIBLE
    )
    assert (
        traditional.recommendation
        is RecommendationVerdict.RECOMMENDED
    )
    assert (
        traditional.confidence
        is RecommendationConfidence.HIGH
    )

    for candidate in [supervised, autonomous]:
        assert (
            candidate.technical_feasibility
            is TechnicalFeasibility.FEASIBLE
        )
        assert (
            candidate.recommendation
            is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
        )
        assert (
            candidate.confidence
            is RecommendationConfidence.HIGH
        )

    traditional_evidence = {
        evidence.key: evidence.value
        for evidence in traditional.supporting_evidence
    }

    assert traditional_evidence["workflow_deterministic"] is True
    assert (
        traditional_evidence["semantic_interpretation_required"]
        is False
    )
    assert traditional_evidence["candidate_uses_llm"] is False

    assert plan.constraint_conflict is None


def test_pipeline_golden_personal_cross_session_memory():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
        evidence=[
            AgentStarterEvidence(
                key="cross_session_memory_required",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    plan = run_agent_starter_pipeline(
        intake=intake,
        compatibility_by_architecture={
            "session-only-personal-assistant": _compatible(
                "The session-only assistant is technically available."
            ),
            "opaque-persistent-memory-assistant": _compatible(
                "The persistent-memory assistant is technically available."
            ),
            "controlled-persistent-memory-assistant": _compatible(
                "The controlled-memory assistant is technically available."
            ),
        },
    )

    assert [
        candidate.architecture_id
        for candidate in plan.candidate_assessments
    ] == [
        "session-only-personal-assistant",
        "opaque-persistent-memory-assistant",
        "controlled-persistent-memory-assistant",
    ]

    session_only, opaque, controlled = (
        plan.candidate_assessments
    )

    assert (
        session_only.technical_feasibility
        is TechnicalFeasibility.NOT_FEASIBLE
    )
    assert (
        session_only.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert (
        session_only.confidence
        is RecommendationConfidence.HIGH
    )

    for candidate in [opaque, controlled]:
        assert (
            candidate.technical_feasibility
            is TechnicalFeasibility.FEASIBLE
        )
        assert (
            candidate.recommendation
            is RecommendationVerdict.POSSIBLE
        )
        assert (
            candidate.confidence
            is RecommendationConfidence.MEDIUM
        )

    session_evidence = {
        evidence.key: evidence.value
        for evidence in session_only.supporting_evidence
    }

    assert session_evidence[
        "candidate_supports_persistent_memory"
    ] is False

    assert plan.constraint_conflict is None


def test_pipeline_golden_voice_interruptions_remain_unknown_without_turn_management_evidence():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="voice_interruptions_requested",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    plan = run_agent_starter_pipeline(
        intake=intake,
        compatibility_by_architecture={
            "local-voice-pipeline": _compatible(
                "The local voice pipeline is technically available."
            ),
            "hybrid-voice-pipeline": _compatible(
                "The hybrid voice pipeline is technically available."
            ),
            "cloud-voice-pipeline": _compatible(
                "The cloud voice pipeline is technically available."
            ),
        },
    )

    assert [
        candidate.architecture_id
        for candidate in plan.candidate_assessments
    ] == [
        "local-voice-pipeline",
        "hybrid-voice-pipeline",
        "cloud-voice-pipeline",
    ]

    for candidate in plan.candidate_assessments:
        assert (
            candidate.technical_feasibility
            is TechnicalFeasibility.UNKNOWN
        )
        assert (
            candidate.recommendation
            is RecommendationVerdict.NOT_RECOMMENDED
        )
        assert (
            candidate.confidence
            is RecommendationConfidence.LIMITED
        )
        assert candidate.blocking_requirements == []

        evidence = {
            item.key: item.value
            for item in candidate.supporting_evidence
        }

        assert evidence["voice_interruptions_requested"] is True
        assert evidence["interruptions_required"] is True

    assert plan.constraint_conflict is None
