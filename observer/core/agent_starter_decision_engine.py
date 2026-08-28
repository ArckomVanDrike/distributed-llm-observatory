from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
    ConstraintStrength,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
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


def assess_coding_candidate(
    *,
    architecture_id: str,
    technical_feasibility: TechnicalFeasibility,
    requirements: list[AgentStarterRequirement],
    candidate_evidence: list[AgentStarterEvidence],
) -> CandidateArchitectureAssessment:
    supporting_evidence = [
        evidence
        for requirement in requirements
        for evidence in requirement.evidence
    ]
    supporting_evidence.extend(candidate_evidence)

    local_only_requirements = [
        requirement
        for requirement in requirements
        if requirement.key == "source_code_must_stay_local"
        and requirement.value is True
        and requirement.strength is ConstraintStrength.HARD
    ]
    local_only_required = bool(local_only_requirements)

    processing_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "source_code_remote_processing"
    ]

    remote_processing = any(
        evidence.value is True
        for evidence in processing_evidence
    )

    processing_boundary_unknown = (
        not processing_evidence
        or any(
            evidence.source is EvidenceSource.UNKNOWN
            or evidence.value is None
            for evidence in processing_evidence
        )
    )

    if technical_feasibility is TechnicalFeasibility.FEASIBLE:
        technical_reason = (
            "The candidate is technically feasible."
        )
    elif technical_feasibility is TechnicalFeasibility.LIMITED:
        technical_reason = (
            "The candidate has limited technical feasibility."
        )
    elif technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        technical_reason = (
            "The candidate is not feasible under the evaluated "
            "technical constraints."
        )
    else:
        technical_reason = (
            "Technical feasibility is unknown and has not "
            "been established."
        )

    if local_only_required and remote_processing:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate violates the hard requirement "
                "that source code must stay local."
            ],
            supporting_evidence=supporting_evidence,
            blocking_requirements=local_only_requirements,
        )

    if technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate is not technically feasible "
                "under the evaluated constraints."
            ],
            supporting_evidence=supporting_evidence,
        )

    if local_only_required and processing_boundary_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Compliance with the hard local-only source-code "
                "requirement cannot be verified from the available "
                "evidence."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.LIMITED:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.MEDIUM,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Limited technical feasibility makes this "
                "candidate a possible but currently "
                "not recommended choice."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.UNKNOWN:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Available evidence is insufficient to "
                "recommend this candidate."
            ],
            supporting_evidence=supporting_evidence,
        )

    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=technical_feasibility,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[technical_reason],
        recommendation_reasons=[
            "No evaluated hard coding constraint excludes "
            "the candidate."
        ],
        supporting_evidence=supporting_evidence,
    )


def assess_automation_candidate(
    *,
    architecture_id: str,
    technical_feasibility: TechnicalFeasibility,
    requirements: list[AgentStarterRequirement],
    candidate_evidence: list[AgentStarterEvidence],
) -> CandidateArchitectureAssessment:
    supporting_evidence = [
        evidence
        for requirement in requirements
        for evidence in requirement.evidence
    ]
    supporting_evidence.extend(candidate_evidence)

    workflow_deterministic = any(
        evidence.key == "workflow_deterministic"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    semantic_interpretation_not_required = any(
        evidence.key == "semantic_interpretation_required"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    candidate_uses_llm = any(
        evidence.key == "candidate_uses_llm"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_does_not_use_llm = any(
        evidence.key == "candidate_uses_llm"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    required_decision_keys = {
        "workflow_deterministic",
        "semantic_interpretation_required",
        "candidate_uses_llm",
    }
    decision_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key in required_decision_keys
    ]
    observed_decision_keys = {
        evidence.key
        for evidence in decision_evidence
    }

    decision_evidence_incomplete = (
        observed_decision_keys != required_decision_keys
        or any(
            evidence.source is EvidenceSource.UNKNOWN
            or evidence.value is None
            for evidence in decision_evidence
        )
    )

    availability_24_7_required = any(
        evidence.key == "availability_24_7_required"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_not_always_available = any(
        evidence.key == "candidate_always_available"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    high_impact_actions = any(
        evidence.key == "destructive_or_high_impact_actions"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    autonomous_execution = any(
        evidence.key == "candidate_executes_autonomously"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    approval_explicitly_not_required = any(
        evidence.key == "human_approval_required"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    if technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        technical_reason = (
            "The candidate is not technically feasible."
        )
    elif technical_feasibility is TechnicalFeasibility.LIMITED:
        technical_reason = (
            "The candidate has limited technical feasibility."
        )
    elif technical_feasibility is TechnicalFeasibility.UNKNOWN:
        technical_reason = (
            "The candidate's technical feasibility is unknown."
        )
    else:
        technical_reason = (
            "The candidate is technically feasible."
        )

    if technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate is not technically feasible "
                "under the evaluated constraints."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.LIMITED:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.MEDIUM,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Limited technical feasibility makes this "
                "candidate a possible but currently "
                "not recommended choice."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.UNKNOWN:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Available evidence is insufficient to establish "
                "technical feasibility for this candidate."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        high_impact_actions
        and autonomous_execution
        and approval_explicitly_not_required
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Autonomous destructive or high-impact actions "
                "without human approval are not recommended."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        availability_24_7_required
        and candidate_explicitly_not_always_available
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate cannot satisfy the requested 24/7 "
                "availability because its deployment is not "
                "continuously available."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        workflow_deterministic
        and semantic_interpretation_not_required
        and candidate_explicitly_does_not_use_llm
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The workflow is deterministic and does not "
                "require semantic interpretation, so traditional "
                "automation is the simpler recommended architecture."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        workflow_deterministic
        and semantic_interpretation_not_required
        and candidate_uses_llm
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "LLM inference is not required for this deterministic "
                "workflow and would add unnecessary complexity."
            ],
            supporting_evidence=supporting_evidence,
        )

    if decision_evidence_incomplete:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Available evidence is insufficient to establish "
                "whether AI is necessary for this automation."
            ],
            supporting_evidence=supporting_evidence,
        )

    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=technical_feasibility,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[technical_reason],
        recommendation_reasons=[
            "The available automation evidence does not yet justify "
            "a stronger architecture recommendation."
        ],
        supporting_evidence=supporting_evidence,
    )


def assess_rag_candidate(
    *,
    architecture_id: str,
    technical_feasibility: TechnicalFeasibility,
    requirements: list[AgentStarterRequirement],
    candidate_evidence: list[AgentStarterEvidence],
) -> CandidateArchitectureAssessment:
    supporting_evidence = [
        evidence
        for requirement in requirements
        for evidence in requirement.evidence
    ]
    supporting_evidence.extend(candidate_evidence)

    corpus_fits_direct_context = any(
        evidence.key == "corpus_fits_direct_context"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    retrieval_explicitly_not_required = any(
        evidence.key == "retrieval_required"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    candidate_uses_retrieval = any(
        evidence.key == "candidate_uses_retrieval_pipeline"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_does_not_use_retrieval = any(
        evidence.key == "candidate_uses_retrieval_pipeline"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    required_rag_decision_keys = {
        "corpus_fits_direct_context",
        "retrieval_required",
        "candidate_uses_retrieval_pipeline",
    }
    rag_decision_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key in required_rag_decision_keys
    ]
    observed_rag_decision_keys = {
        evidence.key
        for evidence in rag_decision_evidence
    }

    rag_decision_evidence_incomplete = (
        observed_rag_decision_keys != required_rag_decision_keys
        or any(
            evidence.source is EvidenceSource.UNKNOWN
            or evidence.value is None
            for evidence in rag_decision_evidence
        )
    )

    citations_required = any(
        evidence.key == "citations_required"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_lacks_source_provenance = any(
        evidence.key == "candidate_provides_source_provenance"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    source_provenance_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_provides_source_provenance"
    ]

    source_provenance_unknown = (
        citations_required
        and (
            not source_provenance_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in source_provenance_evidence
            )
        )
    )

    documents_include_scans = any(
        evidence.key == "documents_include_scans"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_lacks_ocr = any(
        evidence.key == "candidate_supports_ocr"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    ocr_support_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_supports_ocr"
    ]

    ocr_support_unknown = (
        documents_include_scans
        and (
            not ocr_support_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in ocr_support_evidence
            )
        )
    )

    corpus_updates_frequent = any(
        evidence.key == "corpus_updates_frequent"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_lacks_incremental_indexing = any(
        evidence.key == "candidate_supports_incremental_indexing"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    incremental_indexing_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_supports_incremental_indexing"
    ]

    incremental_indexing_unknown = (
        corpus_updates_frequent
        and (
            not incremental_indexing_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in incremental_indexing_evidence
            )
        )
    )

    exact_identifier_lookup_required = any(
        evidence.key == "exact_identifier_lookup_required"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_lacks_lexical_or_hybrid_retrieval = any(
        evidence.key == "candidate_supports_lexical_or_hybrid_retrieval"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    lexical_or_hybrid_retrieval_evidence = [
        evidence
        for evidence in candidate_evidence
        if (
            evidence.key
            == "candidate_supports_lexical_or_hybrid_retrieval"
        )
    ]

    lexical_or_hybrid_retrieval_unknown = (
        exact_identifier_lookup_required
        and (
            not lexical_or_hybrid_retrieval_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in lexical_or_hybrid_retrieval_evidence
            )
        )
    )

    if technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        technical_reason = (
            "The candidate is not technically feasible."
        )
    elif technical_feasibility is TechnicalFeasibility.LIMITED:
        technical_reason = (
            "The candidate has limited technical feasibility."
        )
    elif technical_feasibility is TechnicalFeasibility.UNKNOWN:
        technical_reason = (
            "The candidate's technical feasibility is unknown."
        )
    else:
        technical_reason = (
            "The candidate is technically feasible."
        )

    if technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate is not technically feasible "
                "under the evaluated constraints."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.LIMITED:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.MEDIUM,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Limited technical feasibility makes this "
                "candidate a possible but currently "
                "not recommended choice."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.UNKNOWN:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Available evidence is insufficient to establish "
                "technical feasibility for this candidate."
            ],
            supporting_evidence=supporting_evidence,
        )

    knowledge_local_only_requirements = [
        requirement
        for requirement in requirements
        if (
            requirement.key == "knowledge_data_must_stay_local"
            and requirement.value is True
            and requirement.strength is ConstraintStrength.HARD
        )
    ]

    candidate_knowledge_data_remote_processing = any(
        evidence.key == "candidate_knowledge_data_remote_processing"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    knowledge_processing_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_knowledge_data_remote_processing"
    ]

    knowledge_processing_unknown = (
        bool(knowledge_local_only_requirements)
        and (
            not knowledge_processing_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in knowledge_processing_evidence
            )
        )
    )

    if (
        knowledge_local_only_requirements
        and candidate_knowledge_data_remote_processing
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate violates the hard requirement "
                "that private knowledge data must stay local."
            ],
            supporting_evidence=supporting_evidence,
            blocking_requirements=knowledge_local_only_requirements,
        )

    if (
        citations_required
        and candidate_explicitly_lacks_source_provenance
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Citations are required, but the candidate does not "
                "retain source provenance for retrieved evidence."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        documents_include_scans
        and candidate_explicitly_lacks_ocr
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The document corpus includes scanned content, "
                "but the candidate does not support OCR."
            ],
            supporting_evidence=supporting_evidence,
        )

    if knowledge_processing_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Compliance with the hard requirement that private "
                "knowledge data must stay local cannot be verified "
                "from the available evidence."
            ],
            supporting_evidence=supporting_evidence,
            blocking_requirements=[],
        )

    if (
        corpus_updates_frequent
        and candidate_explicitly_lacks_incremental_indexing
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The corpus changes frequently, but the candidate "
                "does not support incremental indexing, making it "
                "a poor operational fit."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        exact_identifier_lookup_required
        and candidate_explicitly_lacks_lexical_or_hybrid_retrieval
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Exact identifier lookup is required, but the "
                "candidate lacks lexical or hybrid retrieval, "
                "making it a poor retrieval fit."
            ],
            supporting_evidence=supporting_evidence,
        )

    if ocr_support_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "OCR support is unknown or insufficiently "
                "established for the scanned document corpus."
            ],
            supporting_evidence=supporting_evidence,
        )

    if source_provenance_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Source provenance is unknown or insufficiently "
                "established for the requested citations."
            ],
            supporting_evidence=supporting_evidence,
        )

    if incremental_indexing_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Incremental indexing support is unknown or "
                "insufficiently established for the frequently "
                "updated corpus."
            ],
            supporting_evidence=supporting_evidence,
        )

    if lexical_or_hybrid_retrieval_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Lexical or hybrid retrieval support is unknown "
                "or insufficiently established for the requested "
                "exact identifier lookup."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        corpus_fits_direct_context
        and retrieval_explicitly_not_required
        and candidate_explicitly_does_not_use_retrieval
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The corpus fits direct context and retrieval is "
                "not required, so a direct-context architecture "
                "is recommended."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        corpus_fits_direct_context
        and retrieval_explicitly_not_required
        and candidate_uses_retrieval
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "A retrieval pipeline is unnecessary for this "
                "small direct-context corpus."
            ],
            supporting_evidence=supporting_evidence,
        )

    if rag_decision_evidence_incomplete:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Available evidence is insufficient to establish "
                "whether retrieval is necessary for this knowledge "
                "workflow."
            ],
            supporting_evidence=supporting_evidence,
        )

    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=technical_feasibility,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[technical_reason],
        recommendation_reasons=[
            "The available RAG evidence does not yet justify "
            "a stronger architecture recommendation."
        ],
        supporting_evidence=supporting_evidence,
    )


def assess_voice_candidate(
    *,
    architecture_id: str,
    technical_feasibility: TechnicalFeasibility,
    requirements: list[AgentStarterRequirement],
    candidate_evidence: list[AgentStarterEvidence],
) -> CandidateArchitectureAssessment:
    supporting_evidence = [
        evidence
        for requirement in requirements
        for evidence in requirement.evidence
    ]
    supporting_evidence.extend(candidate_evidence)

    if technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        technical_reason = (
            "The candidate is not technically feasible."
        )
    elif technical_feasibility is TechnicalFeasibility.LIMITED:
        technical_reason = (
            "The candidate has limited technical feasibility."
        )
    elif technical_feasibility is TechnicalFeasibility.UNKNOWN:
        technical_reason = (
            "The candidate's technical feasibility is unknown."
        )
    else:
        technical_reason = (
            "The candidate is technically feasible."
        )

    if technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate is not technically feasible "
                "under the evaluated constraints."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.LIMITED:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.MEDIUM,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Limited technical feasibility makes this "
                "candidate a possible but currently "
                "not recommended choice."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.UNKNOWN:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Available evidence is insufficient to establish "
                "technical feasibility for this candidate."
            ],
            supporting_evidence=supporting_evidence,
        )

    raw_audio_local_only_requirements = [
        requirement
        for requirement in requirements
        if (
            requirement.key == "raw_audio_must_stay_local"
            and requirement.value is True
            and requirement.strength is ConstraintStrength.HARD
        )
    ]

    candidate_raw_audio_remote_processing = any(
        evidence.key == "candidate_raw_audio_remote_processing"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    raw_audio_processing_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_raw_audio_remote_processing"
    ]

    raw_audio_processing_unknown = (
        bool(raw_audio_local_only_requirements)
        and (
            not raw_audio_processing_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in raw_audio_processing_evidence
            )
        )
    )

    if (
        raw_audio_local_only_requirements
        and candidate_raw_audio_remote_processing
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate violates the hard requirement "
                "that raw audio must stay local."
            ],
            supporting_evidence=supporting_evidence,
            blocking_requirements=raw_audio_local_only_requirements,
        )

    if raw_audio_processing_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Compliance with the hard requirement that raw "
                "audio must stay local cannot be verified from "
                "the available evidence."
            ],
            supporting_evidence=supporting_evidence,
            blocking_requirements=[],
        )

    transcript_local_only_requirements = [
        requirement
        for requirement in requirements
        if (
            requirement.key == "transcript_must_stay_local"
            and requirement.value is True
            and requirement.strength is ConstraintStrength.HARD
        )
    ]

    candidate_transcript_remote_processing = any(
        evidence.key == "candidate_transcript_remote_processing"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    transcript_processing_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_transcript_remote_processing"
    ]

    transcript_processing_unknown = (
        bool(transcript_local_only_requirements)
        and (
            not transcript_processing_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in transcript_processing_evidence
            )
        )
    )

    if (
        transcript_local_only_requirements
        and candidate_transcript_remote_processing
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate violates the hard requirement "
                "that the transcript must stay local."
            ],
            supporting_evidence=supporting_evidence,
            blocking_requirements=transcript_local_only_requirements,
        )

    if transcript_processing_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Compliance with the hard requirement that the "
                "transcript must stay local cannot be verified "
                "from the available evidence."
            ],
            supporting_evidence=supporting_evidence,
            blocking_requirements=[],
        )

    interruptions_required = any(
        evidence.key == "interruptions_required"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_lacks_barge_in_turn_management = any(
        evidence.key == "candidate_supports_barge_in_turn_management"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    turn_management_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_supports_barge_in_turn_management"
    ]

    turn_management_unknown = (
        interruptions_required
        and (
            not turn_management_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in turn_management_evidence
            )
        )
    )

    if (
        interruptions_required
        and candidate_explicitly_lacks_barge_in_turn_management
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Interruptions are required, but the candidate "
                "does not support barge-in or conversational "
                "turn management."
            ],
            supporting_evidence=supporting_evidence,
        )

    if turn_management_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Barge-in or conversational turn management "
                "support is unknown or insufficiently established "
                "for the requested interruptions."
            ],
            supporting_evidence=supporting_evidence,
        )

    realtime_voice_required = any(
        evidence.key == "realtime_voice_required"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_supports_streaming = any(
        evidence.key == "candidate_supports_streaming"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_lacks_streaming = any(
        evidence.key == "candidate_supports_streaming"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    streaming_support_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_supports_streaming"
    ]

    streaming_support_unknown = (
        realtime_voice_required
        and (
            not streaming_support_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in streaming_support_evidence
            )
        )
    )

    candidate_explicitly_misses_realtime_latency_requirement = any(
        evidence.key == "candidate_meets_realtime_latency_requirement"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    realtime_latency_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_meets_realtime_latency_requirement"
    ]

    realtime_latency_unknown = (
        realtime_voice_required
        and (
            not realtime_latency_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in realtime_latency_evidence
            )
        )
    )

    if (
        realtime_voice_required
        and candidate_explicitly_lacks_streaming
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Realtime voice interaction is required, but the "
                "candidate does not support streaming processing."
            ],
            supporting_evidence=supporting_evidence,
        )

    if streaming_support_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Streaming support is unknown or insufficiently "
                "established for the requested realtime voice workflow."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        realtime_voice_required
        and candidate_explicitly_misses_realtime_latency_requirement
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate does not meet the requested "
                "end-to-end realtime voice latency requirement."
            ],
            supporting_evidence=supporting_evidence,
        )

    if realtime_latency_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "End-to-end realtime voice latency suitability "
                "is unknown or insufficiently established."
            ],
            supporting_evidence=supporting_evidence,
        )

    if realtime_voice_required and candidate_supports_streaming:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.MEDIUM,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate supports streaming processing "
                "required by the realtime voice workflow."
            ],
            supporting_evidence=supporting_evidence,
        )

    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=technical_feasibility,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[technical_reason],
        recommendation_reasons=[
            "The available voice evidence does not yet justify "
            "a stronger architecture recommendation."
        ],
        supporting_evidence=supporting_evidence,
    )


def assess_personal_candidate(
    *,
    architecture_id: str,
    technical_feasibility: TechnicalFeasibility,
    requirements: list[AgentStarterRequirement],
    candidate_evidence: list[AgentStarterEvidence],
) -> CandidateArchitectureAssessment:
    supporting_evidence = [
        evidence
        for requirement in requirements
        for evidence in requirement.evidence
    ]
    supporting_evidence.extend(candidate_evidence)

    if technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        technical_reason = (
            "The candidate is not technically feasible."
        )
    elif technical_feasibility is TechnicalFeasibility.LIMITED:
        technical_reason = (
            "The candidate has limited technical feasibility."
        )
    elif technical_feasibility is TechnicalFeasibility.UNKNOWN:
        technical_reason = (
            "The candidate's technical feasibility is unknown."
        )
    else:
        technical_reason = (
            "The candidate is technically feasible."
        )

    if technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate is not technically feasible "
                "under the evaluated constraints."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.LIMITED:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.MEDIUM,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Limited technical feasibility makes this "
                "candidate a possible but currently "
                "not recommended choice."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.UNKNOWN:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Available evidence is insufficient to establish "
                "technical feasibility for this candidate."
            ],
            supporting_evidence=supporting_evidence,
        )

    proactive_behavior_required = any(
        evidence.key == "proactive_behavior_required"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_lacks_background_scheduling = any(
        evidence.key == "candidate_supports_background_scheduling"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    background_scheduling_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_supports_background_scheduling"
    ]

    background_scheduling_unknown = (
        proactive_behavior_required
        and (
            not background_scheduling_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in background_scheduling_evidence
            )
        )
    )

    if (
        proactive_behavior_required
        and candidate_lacks_background_scheduling
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Proactive behavior is required, but the candidate "
                "does not support scheduled or background execution."
            ],
            supporting_evidence=supporting_evidence,
        )


    indefinite_all_conversation_retention_not_required = any(
        evidence.key == "indefinite_all_conversation_retention_required"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    candidate_retains_all_conversations_indefinitely = any(
        evidence.key == "candidate_retains_all_conversations_indefinitely"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    indefinite_retention_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_retains_all_conversations_indefinitely"
    ]

    indefinite_retention_unknown = (
        indefinite_all_conversation_retention_not_required
        and (
            not indefinite_retention_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in indefinite_retention_evidence
            )
        )
    )

    if (
        indefinite_all_conversation_retention_not_required
        and candidate_retains_all_conversations_indefinitely
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Indefinite retention of all conversations is not "
                "required, so retaining everything without a bounded "
                "retention policy is not recommended."
            ],
            supporting_evidence=supporting_evidence,
        )


    selective_memory_required = any(
        evidence.key == "selective_memory_required"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_lacks_memory_controls = any(
        evidence.key == "candidate_supports_memory_inspect_edit_delete"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    memory_controls_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_supports_memory_inspect_edit_delete"
    ]

    memory_controls_unknown = (
        selective_memory_required
        and (
            not memory_controls_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in memory_controls_evidence
            )
        )
    )

    if (
        selective_memory_required
        and candidate_explicitly_lacks_memory_controls
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Selective memory is required, but the candidate "
                "does not support inspection, editing, and deletion "
                "of stored memory."
            ],
            supporting_evidence=supporting_evidence,
        )


    cross_session_memory_required = any(
        evidence.key == "cross_session_memory_required"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_supports_persistent_memory = any(
        evidence.key == "candidate_supports_persistent_memory"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_lacks_persistent_memory = any(
        evidence.key == "candidate_supports_persistent_memory"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    persistent_memory_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "candidate_supports_persistent_memory"
    ]

    persistent_memory_unknown = (
        cross_session_memory_required
        and (
            not persistent_memory_evidence
            or any(
                evidence.source is EvidenceSource.UNKNOWN
                or evidence.value is None
                for evidence in persistent_memory_evidence
            )
        )
    )

    if (
        cross_session_memory_required
        and candidate_explicitly_lacks_persistent_memory
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Cross-session memory is required, but the "
                "candidate does not support persistent memory."
            ],
            supporting_evidence=supporting_evidence,
        )

    if background_scheduling_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Scheduled or background execution support is "
                "unknown or insufficiently established for the "
                "requested proactive workflow."
            ],
            supporting_evidence=supporting_evidence,
        )

    if indefinite_retention_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Conversation retention behavior is unknown or "
                "insufficiently established where indefinite "
                "retention is not required."
            ],
            supporting_evidence=supporting_evidence,
        )

    if memory_controls_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Memory inspection, editing, and deletion support "
                "is unknown or insufficiently established for the "
                "requested selective memory workflow."
            ],
            supporting_evidence=supporting_evidence,
        )

    if persistent_memory_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Persistent memory support is unknown or "
                "insufficiently established for the requested "
                "cross-session workflow."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        cross_session_memory_required
        and candidate_supports_persistent_memory
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.MEDIUM,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate supports persistent memory "
                "for the requested cross-session workflow."
            ],
            supporting_evidence=supporting_evidence,
        )

    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=technical_feasibility,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[technical_reason],
        recommendation_reasons=[
            "The available personal-assistant evidence does not "
            "yet justify a stronger architecture recommendation."
        ],
        supporting_evidence=supporting_evidence,
    )


def assess_agent_starter_candidate(
    *,
    goal: AgentStarterGoal,
    architecture_id: str,
    technical_feasibility: TechnicalFeasibility,
    requirements: list[AgentStarterRequirement],
    candidate_evidence: list[AgentStarterEvidence],
) -> CandidateArchitectureAssessment:
    if goal is AgentStarterGoal.CODING:
        assessor = assess_coding_candidate
    elif goal is AgentStarterGoal.AUTOMATION:
        assessor = assess_automation_candidate
    elif goal is AgentStarterGoal.KNOWLEDGE_RAG:
        assessor = assess_rag_candidate
    elif goal is AgentStarterGoal.VOICE:
        assessor = assess_voice_candidate
    elif goal is AgentStarterGoal.PERSONAL:
        assessor = assess_personal_candidate
    else:
        raise ValueError(
            f"Unsupported Agent Starter goal: {goal!r}"
        )

    return assessor(
        architecture_id=architecture_id,
        technical_feasibility=technical_feasibility,
        requirements=requirements,
        candidate_evidence=candidate_evidence,
    )
