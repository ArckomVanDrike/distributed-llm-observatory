from observer.core.agent_starter_decision_engine import (
    assess_automation_candidate,
    assess_coding_candidate,
    assess_rag_candidate,
    assess_voice_candidate,
    technical_feasibility_from_compatibility,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterRequirement,
    ConstraintStrength,
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


def _assessment(
    verdict: CompatibilityVerdict,
) -> CompatibilityAssessment:
    return CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=verdict,
        summary="Compatibility result.",
    )


def _local_only_requirement() -> AgentStarterRequirement:
    evidence = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    return AgentStarterRequirement(
        key="source_code_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
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


def test_remote_coding_candidate_can_be_feasible_but_not_recommended():
    requirement = _local_only_requirement()

    remote_processing = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The candidate architecture sends repository context "
            "to remote inference."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="cloud_coding",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[remote_processing],
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.HIGH
    assert requirement.evidence[0] in result.supporting_evidence
    assert remote_processing in result.supporting_evidence


def test_local_coding_candidate_is_possible_not_automatically_recommended():
    requirement = _local_only_requirement()

    local_processing = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.DERIVED,
        value=False,
        reason=(
            "The candidate architecture keeps repository context "
            "inside the local execution boundary."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="local_coding",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[local_processing],
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.MEDIUM
    assert requirement.evidence[0] in result.supporting_evidence
    assert local_processing in result.supporting_evidence


def test_limited_coding_candidate_is_possible_but_not_recommended():
    evidence = AgentStarterEvidence(
        key="local_execution_headroom",
        source=EvidenceSource.DERIVED,
        value="limited",
        reason=(
            "Compatibility evidence indicates limited "
            "execution headroom."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="local_coding",
        technical_feasibility=TechnicalFeasibility.LIMITED,
        requirements=[],
        candidate_evidence=[evidence],
    )

    assert result.technical_feasibility is TechnicalFeasibility.LIMITED
    assert (
        result.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.MEDIUM
    assert any(
        "limited" in reason.lower()
        for reason in result.technical_reasons
    )


def test_unknown_coding_feasibility_is_not_treated_as_feasible():
    evidence = AgentStarterEvidence(
        key="local_execution_headroom",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason=(
            "Available evidence is insufficient to establish "
            "local execution feasibility."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="local_coding",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        requirements=[],
        candidate_evidence=[evidence],
    )

    assert result.technical_feasibility is TechnicalFeasibility.UNKNOWN
    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "unknown" in reason.lower()
        or "not established" in reason.lower()
        for reason in result.technical_reasons
    )


def test_not_feasible_coding_candidate_is_not_recommended():
    evidence = AgentStarterEvidence(
        key="local_execution_feasibility",
        source=EvidenceSource.DERIVED,
        value="not_feasible",
        reason=(
            "Observed constraints establish that the candidate "
            "cannot support the required local execution."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="local_coding",
        technical_feasibility=TechnicalFeasibility.NOT_FEASIBLE,
        requirements=[],
        candidate_evidence=[evidence],
    )

    assert (
        result.technical_feasibility
        is TechnicalFeasibility.NOT_FEASIBLE
    )
    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "not feasible" in reason.lower()
        for reason in result.technical_reasons
    )


def test_local_only_requirement_with_unknown_processing_is_not_recommended():
    requirement = _local_only_requirement()

    unknown_processing = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason=(
            "It is not known whether the candidate sends "
            "repository context to remote inference."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="coding_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[unknown_processing],
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "cannot be verified" in reason.lower()
        or "insufficient" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_local_only_requirement_without_processing_evidence_is_not_recommended():
    requirement = _local_only_requirement()

    result = assess_coding_candidate(
        architecture_id="coding_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[],
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "cannot be verified" in reason.lower()
        or "insufficient" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_proven_local_only_violation_records_blocking_requirement():
    requirement = _local_only_requirement()

    remote_processing = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The candidate architecture sends repository context "
            "to remote inference."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="cloud_coding",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[remote_processing],
    )

    assert result.blocking_requirements == [requirement]


def test_unknown_local_only_compliance_is_not_recorded_as_proven_blocker():
    requirement = _local_only_requirement()

    unknown_processing = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason=(
            "It is not known whether the candidate sends "
            "repository context to remote inference."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="coding_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[unknown_processing],
    )

    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.blocking_requirements == []


def _deterministic_automation_evidence(
    *,
    candidate_uses_llm: bool,
) -> list[AgentStarterEvidence]:
    return [
        AgentStarterEvidence(
            key="workflow_deterministic",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="semantic_interpretation_required",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The declared workflow consists of fixed "
                "deterministic steps."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_uses_llm",
            source=EvidenceSource.DERIVED,
            value=candidate_uses_llm,
            reason=(
                "The candidate architecture explicitly "
                "defines whether LLM inference is used."
            ),
        ),
    ]


def test_deterministic_workflow_recommends_traditional_automation():
    result = assess_automation_candidate(
        architecture_id="traditional_automation",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_deterministic_automation_evidence(
            candidate_uses_llm=False,
        ),
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert result.recommendation is RecommendationVerdict.RECOMMENDED
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "deterministic" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_deterministic_workflow_does_not_recommend_unnecessary_llm_agent():
    result = assess_automation_candidate(
        architecture_id="llm_automation_agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_deterministic_automation_evidence(
            candidate_uses_llm=True,
        ),
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert (
        result.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "unnecessary" in reason.lower()
        or "not required" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_unknown_llm_usage_limits_automation_recommendation_confidence():
    evidence = [
        AgentStarterEvidence(
            key="workflow_deterministic",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="semantic_interpretation_required",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The declared workflow consists of fixed "
                "deterministic steps."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_uses_llm",
            source=EvidenceSource.UNKNOWN,
            value=None,
            reason=(
                "The candidate architecture does not provide "
                "enough evidence to establish LLM usage."
            ),
        ),
    ]

    result = assess_automation_candidate(
        architecture_id="automation_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "insufficient" in reason.lower()
        or "unknown" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_missing_semantic_need_does_not_make_ai_unnecessary():
    evidence = [
        AgentStarterEvidence(
            key="workflow_deterministic",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_llm",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The candidate architecture uses LLM inference."
            ),
        ),
    ]

    result = assess_automation_candidate(
        architecture_id="llm_automation_agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "insufficient" in reason.lower()
        or "unknown" in reason.lower()
        for reason in result.recommendation_reasons
    )


def _high_impact_automation_evidence(
    *,
    human_approval_required: bool,
) -> list[AgentStarterEvidence]:
    return [
        AgentStarterEvidence(
            key="workflow_deterministic",
            source=EvidenceSource.DECLARED,
            value=False,
        ),
        AgentStarterEvidence(
            key="semantic_interpretation_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_llm",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses LLM inference.",
        ),
        AgentStarterEvidence(
            key="destructive_or_high_impact_actions",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_executes_autonomously",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The candidate can execute external write actions "
                "without waiting for a user command."
            ),
        ),
        AgentStarterEvidence(
            key="human_approval_required",
            source=EvidenceSource.DECLARED,
            value=human_approval_required,
        ),
    ]


def test_autonomous_high_impact_automation_without_approval_is_not_recommended():
    result = assess_automation_candidate(
        architecture_id="autonomous_workflow_agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_high_impact_automation_evidence(
            human_approval_required=False,
        ),
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "approval" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_high_impact_automation_with_human_approval_can_proceed():
    result = assess_automation_candidate(
        architecture_id="supervised_workflow_agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_high_impact_automation_evidence(
            human_approval_required=True,
        ),
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.MEDIUM


def test_24_7_requirement_downgrades_non_always_available_automation():
    evidence = _deterministic_automation_evidence(
        candidate_uses_llm=False,
    )
    evidence.extend(
        [
            AgentStarterEvidence(
                key="availability_24_7_required",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="candidate_always_available",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "The candidate runs on a device that is not "
                    "expected to remain continuously available."
                ),
            ),
        ]
    )

    result = assess_automation_candidate(
        architecture_id="personal_device_automation",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert (
        result.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "24/7" in reason
        or "availability" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_24_7_requirement_allows_always_available_traditional_automation():
    evidence = _deterministic_automation_evidence(
        candidate_uses_llm=False,
    )
    evidence.extend(
        [
            AgentStarterEvidence(
                key="availability_24_7_required",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="candidate_always_available",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The candidate deployment is designed for "
                    "continuous availability."
                ),
            ),
        ]
    )

    result = assess_automation_candidate(
        architecture_id="always_on_automation",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.RECOMMENDED
    assert result.confidence is RecommendationConfidence.HIGH


def _small_direct_context_evidence(
    *,
    candidate_uses_retrieval: bool,
) -> list[AgentStarterEvidence]:
    return [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The corpus is small enough to fit the intended "
                "direct-context workflow."
            ),
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The requested workflow does not require "
                "retrieval over a larger knowledge collection."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=candidate_uses_retrieval,
            reason=(
                "The candidate architecture explicitly defines "
                "whether a retrieval pipeline is used."
            ),
        ),
    ]


def test_small_corpus_recommends_direct_context():
    result = assess_rag_candidate(
        architecture_id="direct_context",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_small_direct_context_evidence(
            candidate_uses_retrieval=False,
        ),
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert result.recommendation is RecommendationVerdict.RECOMMENDED
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "direct context" in reason.lower()
        or "direct-context" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_small_corpus_does_not_recommend_unnecessary_full_rag():
    result = assess_rag_candidate(
        architecture_id="full_rag",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_small_direct_context_evidence(
            candidate_uses_retrieval=True,
        ),
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert (
        result.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "unnecessary" in reason.lower()
        or "not required" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_unknown_retrieval_usage_limits_rag_recommendation_confidence():
    evidence = [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The corpus fits the intended direct context.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="Retrieval is not required for the workflow.",
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.UNKNOWN,
            value=None,
            reason=(
                "The candidate does not provide enough evidence "
                "to establish whether retrieval is used."
            ),
        ),
    ]

    result = assess_rag_candidate(
        architecture_id="knowledge_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "insufficient" in reason.lower()
        or "unknown" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_missing_retrieval_requirement_does_not_assume_rag_is_unnecessary():
    evidence = [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The corpus fits the intended direct context.",
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
    ]

    result = assess_rag_candidate(
        architecture_id="full_rag",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "insufficient" in reason.lower()
        or "unknown" in reason.lower()
        for reason in result.recommendation_reasons
    )


def _citation_rag_evidence(
    *,
    candidate_provides_source_provenance: bool,
) -> list[AgentStarterEvidence]:
    return [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The knowledge workflow is not treated as a "
                "direct-context-only case."
            ),
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="citations_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_provides_source_provenance",
            source=EvidenceSource.DERIVED,
            value=candidate_provides_source_provenance,
            reason=(
                "The candidate architecture explicitly defines "
                "whether retrieved evidence retains source provenance."
            ),
        ),
    ]


def test_rag_with_required_citations_and_source_provenance_can_proceed():
    result = assess_rag_candidate(
        architecture_id="provenance_aware_rag",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_citation_rag_evidence(
            candidate_provides_source_provenance=True,
        ),
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.MEDIUM


def test_rag_without_source_provenance_is_not_recommended_when_citations_required():
    result = assess_rag_candidate(
        architecture_id="rag_without_provenance",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_citation_rag_evidence(
            candidate_provides_source_provenance=False,
        ),
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "provenance" in reason.lower()
        or "citation" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_unknown_source_provenance_limits_citation_rag_confidence():
    evidence = [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="citations_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_provides_source_provenance",
            source=EvidenceSource.UNKNOWN,
            value=None,
            reason=(
                "Available evidence does not establish whether "
                "retrieved content retains source provenance."
            ),
        ),
    ]

    result = assess_rag_candidate(
        architecture_id="rag_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "provenance" in reason.lower()
        and (
            "insufficient" in reason.lower()
            or "unknown" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def test_missing_source_provenance_does_not_assume_citation_compliance():
    evidence = [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="citations_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
    ]

    result = assess_rag_candidate(
        architecture_id="rag_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "provenance" in reason.lower()
        and (
            "insufficient" in reason.lower()
            or "unknown" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def _scanned_document_rag_evidence(
    *,
    candidate_supports_ocr: bool,
) -> list[AgentStarterEvidence]:
    return [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="documents_include_scans",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_ocr",
            source=EvidenceSource.DERIVED,
            value=candidate_supports_ocr,
            reason=(
                "The candidate architecture explicitly defines "
                "whether scanned documents can be processed with OCR."
            ),
        ),
    ]


def test_rag_with_scanned_documents_and_ocr_can_proceed():
    result = assess_rag_candidate(
        architecture_id="rag_with_ocr",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_scanned_document_rag_evidence(
            candidate_supports_ocr=True,
        ),
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.MEDIUM


def test_rag_without_ocr_is_not_recommended_for_scanned_documents():
    result = assess_rag_candidate(
        architecture_id="rag_without_ocr",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_scanned_document_rag_evidence(
            candidate_supports_ocr=False,
        ),
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "ocr" in reason.lower()
        or "scanned" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_unknown_ocr_support_limits_scanned_document_rag_confidence():
    evidence = [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="documents_include_scans",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_ocr",
            source=EvidenceSource.UNKNOWN,
            value=None,
            reason=(
                "Available evidence does not establish whether "
                "the candidate supports OCR."
            ),
        ),
    ]

    result = assess_rag_candidate(
        architecture_id="rag_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "ocr" in reason.lower()
        and (
            "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def test_missing_ocr_support_does_not_assume_scanned_document_compatibility():
    evidence = [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="documents_include_scans",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
    ]

    result = assess_rag_candidate(
        architecture_id="rag_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "ocr" in reason.lower()
        and (
            "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def _frequently_updated_rag_evidence(
    *,
    candidate_supports_incremental_indexing: bool,
) -> list[AgentStarterEvidence]:
    return [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="corpus_updates_frequent",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_incremental_indexing",
            source=EvidenceSource.DERIVED,
            value=candidate_supports_incremental_indexing,
            reason=(
                "The candidate architecture explicitly defines "
                "whether corpus updates can be indexed incrementally."
            ),
        ),
    ]


def test_frequently_updated_rag_with_incremental_indexing_can_proceed():
    result = assess_rag_candidate(
        architecture_id="incremental_rag",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_frequently_updated_rag_evidence(
            candidate_supports_incremental_indexing=True,
        ),
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.MEDIUM


def test_frequently_updated_rag_without_incremental_indexing_is_not_preferred():
    result = assess_rag_candidate(
        architecture_id="static_reindex_rag",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_frequently_updated_rag_evidence(
            candidate_supports_incremental_indexing=False,
        ),
    )

    assert (
        result.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "incremental" in reason.lower()
        or "frequent" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_unknown_incremental_indexing_limits_frequent_update_rag_confidence():
    evidence = [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="corpus_updates_frequent",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_incremental_indexing",
            source=EvidenceSource.UNKNOWN,
            value=None,
            reason=(
                "Available evidence does not establish whether "
                "the candidate supports incremental indexing."
            ),
        ),
    ]

    result = assess_rag_candidate(
        architecture_id="rag_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "incremental" in reason.lower()
        and (
            "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def test_missing_incremental_indexing_does_not_assume_frequent_update_fit():
    evidence = [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="corpus_updates_frequent",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
    ]

    result = assess_rag_candidate(
        architecture_id="rag_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "incremental" in reason.lower()
        and (
            "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def test_rag_not_feasible_cannot_be_recommended_by_architecture_fit():
    result = assess_rag_candidate(
        architecture_id="direct_context",
        technical_feasibility=TechnicalFeasibility.NOT_FEASIBLE,
        requirements=[],
        candidate_evidence=_small_direct_context_evidence(
            candidate_uses_retrieval=False,
        ),
    )

    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "not technically feasible" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_rag_limited_feasibility_cannot_be_strongly_recommended():
    result = assess_rag_candidate(
        architecture_id="direct_context",
        technical_feasibility=TechnicalFeasibility.LIMITED,
        requirements=[],
        candidate_evidence=_small_direct_context_evidence(
            candidate_uses_retrieval=False,
        ),
    )

    assert (
        result.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.MEDIUM
    assert any(
        "limited" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_rag_unknown_feasibility_cannot_be_recommended_from_feature_fit():
    result = assess_rag_candidate(
        architecture_id="direct_context",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        requirements=[],
        candidate_evidence=_small_direct_context_evidence(
            candidate_uses_retrieval=False,
        ),
    )

    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "insufficient" in reason.lower()
        or "unknown" in reason.lower()
        for reason in result.recommendation_reasons
    )


def _exact_identifier_rag_evidence(
    *,
    candidate_supports_lexical_or_hybrid_retrieval: bool,
) -> list[AgentStarterEvidence]:
    return [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="exact_identifier_lookup_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_lexical_or_hybrid_retrieval",
            source=EvidenceSource.DERIVED,
            value=candidate_supports_lexical_or_hybrid_retrieval,
            reason=(
                "The candidate architecture explicitly defines "
                "whether exact-match-friendly lexical or hybrid "
                "retrieval is available."
            ),
        ),
    ]


def test_exact_identifier_rag_with_lexical_or_hybrid_retrieval_can_proceed():
    result = assess_rag_candidate(
        architecture_id="hybrid_rag",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_exact_identifier_rag_evidence(
            candidate_supports_lexical_or_hybrid_retrieval=True,
        ),
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.MEDIUM


def test_exact_identifier_rag_without_lexical_or_hybrid_retrieval_is_not_preferred():
    result = assess_rag_candidate(
        architecture_id="semantic_only_rag",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_exact_identifier_rag_evidence(
            candidate_supports_lexical_or_hybrid_retrieval=False,
        ),
    )

    assert (
        result.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "lexical" in reason.lower()
        or "hybrid" in reason.lower()
        or "exact" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_unknown_lexical_or_hybrid_support_limits_exact_identifier_rag_confidence():
    evidence = [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="exact_identifier_lookup_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_lexical_or_hybrid_retrieval",
            source=EvidenceSource.UNKNOWN,
            value=None,
            reason=(
                "Available evidence does not establish whether "
                "the candidate supports lexical or hybrid retrieval."
            ),
        ),
    ]

    result = assess_rag_candidate(
        architecture_id="rag_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        (
            "lexical" in reason.lower()
            or "hybrid" in reason.lower()
        )
        and (
            "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def test_missing_lexical_or_hybrid_support_does_not_assume_exact_identifier_fit():
    evidence = [
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="The corpus requires a retrieval workflow.",
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses a retrieval pipeline.",
        ),
        AgentStarterEvidence(
            key="exact_identifier_lookup_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
    ]

    result = assess_rag_candidate(
        architecture_id="rag_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        (
            "lexical" in reason.lower()
            or "hybrid" in reason.lower()
        )
        and (
            "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def test_automation_not_feasible_cannot_be_recommended_by_workflow_fit():
    result = assess_automation_candidate(
        architecture_id="traditional_automation",
        technical_feasibility=TechnicalFeasibility.NOT_FEASIBLE,
        requirements=[],
        candidate_evidence=_deterministic_automation_evidence(
            candidate_uses_llm=False,
        ),
    )

    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "not technically feasible" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_automation_limited_feasibility_cannot_be_strongly_recommended():
    result = assess_automation_candidate(
        architecture_id="traditional_automation",
        technical_feasibility=TechnicalFeasibility.LIMITED,
        requirements=[],
        candidate_evidence=_deterministic_automation_evidence(
            candidate_uses_llm=False,
        ),
    )

    assert (
        result.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.MEDIUM
    assert any(
        "limited" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_automation_unknown_feasibility_cannot_be_recommended_from_workflow_fit():
    result = assess_automation_candidate(
        architecture_id="traditional_automation",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        requirements=[],
        candidate_evidence=_deterministic_automation_evidence(
            candidate_uses_llm=False,
        ),
    )

    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "insufficient" in reason.lower()
        or "unknown" in reason.lower()
        for reason in result.recommendation_reasons
    )


def _realtime_voice_evidence(
    *,
    candidate_supports_streaming: bool,
) -> list[AgentStarterEvidence]:
    return [
        AgentStarterEvidence(
            key="realtime_voice_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_streaming",
            source=EvidenceSource.DERIVED,
            value=candidate_supports_streaming,
            reason=(
                "The candidate architecture explicitly defines "
                "whether streaming voice processing is supported."
            ),
        ),
    ]


def test_realtime_voice_with_streaming_can_proceed():
    result = assess_voice_candidate(
        architecture_id="streaming_voice_pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_realtime_voice_evidence(
            candidate_supports_streaming=True,
        ),
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.MEDIUM


def test_realtime_voice_without_streaming_is_not_preferred():
    result = assess_voice_candidate(
        architecture_id="non_streaming_voice_pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=_realtime_voice_evidence(
            candidate_supports_streaming=False,
        ),
    )

    assert (
        result.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "streaming" in reason.lower()
        or "realtime" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_unknown_streaming_support_limits_realtime_voice_confidence():
    evidence = [
        AgentStarterEvidence(
            key="realtime_voice_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_streaming",
            source=EvidenceSource.UNKNOWN,
            value=None,
            reason=(
                "Available evidence does not establish whether "
                "the candidate supports streaming voice processing."
            ),
        ),
    ]

    result = assess_voice_candidate(
        architecture_id="voice_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "streaming" in reason.lower()
        and (
            "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def test_missing_streaming_support_does_not_assume_realtime_voice_fit():
    evidence = [
        AgentStarterEvidence(
            key="realtime_voice_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
    ]

    result = assess_voice_candidate(
        architecture_id="voice_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "streaming" in reason.lower()
        and (
            "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def _raw_audio_local_only_requirement() -> AgentStarterRequirement:
    return AgentStarterRequirement(
        key="raw_audio_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[
            AgentStarterEvidence(
                key="raw_audio_local_only",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )


def test_remote_raw_audio_processing_violates_local_only_voice_requirement():
    requirement = _raw_audio_local_only_requirement()

    evidence = [
        AgentStarterEvidence(
            key="candidate_raw_audio_remote_processing",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The candidate sends raw audio to a remote STT "
                "component for transcription."
            ),
        ),
    ]

    result = assess_voice_candidate(
        architecture_id="remote_stt_voice_pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.HIGH
    assert result.blocking_requirements == [requirement]
    assert any(
        "raw audio" in reason.lower()
        or "local" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_local_raw_audio_processing_satisfies_local_only_boundary():
    requirement = _raw_audio_local_only_requirement()

    evidence = [
        AgentStarterEvidence(
            key="candidate_raw_audio_remote_processing",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "Raw audio is processed locally before any "
                "downstream remote processing."
            ),
        ),
    ]

    result = assess_voice_candidate(
        architecture_id="local_stt_voice_pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.MEDIUM
    assert result.blocking_requirements == []


def test_unknown_raw_audio_processing_cannot_verify_local_only_compliance():
    requirement = _raw_audio_local_only_requirement()

    evidence = [
        AgentStarterEvidence(
            key="candidate_raw_audio_remote_processing",
            source=EvidenceSource.UNKNOWN,
            value=None,
            reason=(
                "Available evidence does not establish whether "
                "raw audio is sent to remote processing."
            ),
        ),
    ]

    result = assess_voice_candidate(
        architecture_id="voice_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.LIMITED
    assert result.blocking_requirements == []
    assert any(
        "raw audio" in reason.lower()
        and (
            "cannot" in reason.lower()
            or "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def test_missing_raw_audio_processing_does_not_assume_local_only_compliance():
    requirement = _raw_audio_local_only_requirement()

    result = assess_voice_candidate(
        architecture_id="voice_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[],
    )

    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.LIMITED
    assert result.blocking_requirements == []
    assert any(
        "raw audio" in reason.lower()
        and (
            "cannot" in reason.lower()
            or "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def _transcript_local_only_requirement() -> AgentStarterRequirement:
    return AgentStarterRequirement(
        key="transcript_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[
            AgentStarterEvidence(
                key="transcript_local_only",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )


def test_hybrid_voice_allows_remote_transcript_when_raw_audio_stays_local():
    raw_audio_requirement = _raw_audio_local_only_requirement()

    evidence = [
        AgentStarterEvidence(
            key="candidate_raw_audio_remote_processing",
            source=EvidenceSource.DERIVED,
            value=False,
            reason="Raw audio is transcribed locally.",
        ),
        AgentStarterEvidence(
            key="transcript_remote_processing_allowed",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_transcript_remote_processing",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "Only the locally produced transcript is sent "
                "to a remote downstream component."
            ),
        ),
    ]

    result = assess_voice_candidate(
        architecture_id="hybrid_voice_pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[raw_audio_requirement],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.MEDIUM
    assert result.blocking_requirements == []


def test_remote_transcript_processing_violates_local_only_transcript_requirement():
    requirement = _transcript_local_only_requirement()

    evidence = [
        AgentStarterEvidence(
            key="candidate_transcript_remote_processing",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The candidate sends the transcript to a remote "
                "component for downstream processing."
            ),
        ),
    ]

    result = assess_voice_candidate(
        architecture_id="remote_transcript_pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.HIGH
    assert result.blocking_requirements == [requirement]
    assert any(
        "transcript" in reason.lower()
        and "local" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_unknown_transcript_processing_cannot_verify_local_only_compliance():
    requirement = _transcript_local_only_requirement()

    evidence = [
        AgentStarterEvidence(
            key="candidate_transcript_remote_processing",
            source=EvidenceSource.UNKNOWN,
            value=None,
            reason=(
                "Available evidence does not establish whether "
                "the transcript is sent to remote processing."
            ),
        ),
    ]

    result = assess_voice_candidate(
        architecture_id="voice_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=evidence,
    )

    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.LIMITED
    assert result.blocking_requirements == []
    assert any(
        "transcript" in reason.lower()
        and (
            "cannot" in reason.lower()
            or "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )


def test_missing_transcript_processing_does_not_assume_local_only_compliance():
    requirement = _transcript_local_only_requirement()

    result = assess_voice_candidate(
        architecture_id="voice_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[],
    )

    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.LIMITED
    assert result.blocking_requirements == []
    assert any(
        "transcript" in reason.lower()
        and (
            "cannot" in reason.lower()
            or "unknown" in reason.lower()
            or "insufficient" in reason.lower()
        )
        for reason in result.recommendation_reasons
    )
