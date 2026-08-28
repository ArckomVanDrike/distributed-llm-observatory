from observer.core.agent_starter_catalog_query_builder import (
    build_agent_starter_catalog_queries,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    CandidateArchitectureAssessment,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
)


def test_catalog_query_builder_maps_coding_assessment_to_llm_query():
    assessment = CandidateArchitectureAssessment(
        architecture_id="local-coding-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The coding architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The coding architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The coding-agent architecture uses an LLM "
                    "for coding assistance."
                ),
            ),
            AgentStarterEvidence(
                key="source_code_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Source code remains inside the "
                    "user-controlled environment."
                ),
            ),
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.CODING,
        assessment=assessment,
    )

    assert len(queries) == 1

    query = queries[0]

    assert (
        query.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert query.required_capabilities == ["coding"]

    # Local processing evidence is not equivalent to
    # a concrete on-device deployment mode.
    assert query.required_deployment_modes == []

    # These properties have not been established by evidence.
    assert query.required_runtime is None
    assert query.required_pricing_class is None


def test_catalog_query_builder_returns_no_llm_query_for_deterministic_automation():
    assessment = CandidateArchitectureAssessment(
        architecture_id="traditional-deterministic-automation",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The deterministic architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "Deterministic automation satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "The deterministic automation architecture "
                    "does not use an LLM."
                ),
            ),
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.AUTOMATION,
        assessment=assessment,
    )

    assert queries == []


def test_catalog_query_builder_returns_llm_query_for_llm_automation():
    assessment = CandidateArchitectureAssessment(
        architecture_id="supervised-automation-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The automation architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The automation architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The automation architecture uses an LLM."
                ),
            ),
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.AUTOMATION,
        assessment=assessment,
    )

    assert len(queries) == 1

    query = queries[0]

    assert (
        query.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert query.required_capabilities == []
    assert query.required_deployment_modes == []
    assert query.required_runtime is None
    assert query.required_pricing_class is None


def test_catalog_query_builder_rejects_automation_without_llm_usage_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="unknown-automation",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "LLM usage is not established.",
        ],
        recommendation_reasons=[
            "The architecture cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="unrelated_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="Unrelated evidence.",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Automation stack mapping requires exactly one "
            "candidate_uses_llm boolean evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.AUTOMATION,
            assessment=assessment,
        )


def test_catalog_query_builder_rejects_conflicting_automation_llm_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="conflicting-automation",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "The automation LLM usage evidence conflicts.",
        ],
        recommendation_reasons=[
            "The architecture cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=False,
                reason="The candidate does not use an LLM.",
            ),
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="The candidate uses an LLM.",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Automation stack mapping requires exactly one "
            "candidate_uses_llm boolean evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.AUTOMATION,
            assessment=assessment,
        )


def test_catalog_query_builder_maps_direct_context_rag_to_llm_query():
    assessment = CandidateArchitectureAssessment(
        architecture_id="direct-context-knowledge-assistant",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The direct-context architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "Direct context satisfies the knowledge requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The knowledge-assistant architecture uses an LLM "
                    "for generation."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_retrieval_pipeline",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "The architecture supplies knowledge "
                    "without a retrieval stage."
                ),
            ),
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        assessment=assessment,
    )

    assert len(queries) == 1

    query = queries[0]

    assert (
        query.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert query.required_capabilities == []
    assert query.required_deployment_modes == []
    assert query.required_runtime is None
    assert query.required_pricing_class is None


def test_catalog_query_builder_maps_full_rag_to_llm_query():
    assessment = CandidateArchitectureAssessment(
        architecture_id="full-rag-pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The retrieval architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The retrieval architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The knowledge-assistant architecture uses an LLM "
                    "for generation."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_retrieval_pipeline",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The architecture retrieves relevant knowledge "
                    "before generation."
                ),
            ),
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        assessment=assessment,
    )

    assert len(queries) == 1

    query = queries[0]

    assert (
        query.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert query.required_capabilities == []
    assert query.required_deployment_modes == []
    assert query.required_runtime is None
    assert query.required_pricing_class is None


def test_catalog_query_builder_rejects_rag_without_retrieval_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="unknown-knowledge-architecture",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "Retrieval behavior is not established.",
        ],
        recommendation_reasons=[
            "The architecture cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The knowledge-assistant architecture uses an LLM "
                    "for generation."
                ),
            ),
            AgentStarterEvidence(
                key="unrelated_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="Unrelated evidence.",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Knowledge stack mapping requires exactly one "
            "candidate_uses_retrieval_pipeline boolean evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.KNOWLEDGE_RAG,
            assessment=assessment,
        )


def test_catalog_query_builder_rejects_conflicting_rag_retrieval_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="conflicting-knowledge-architecture",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "Retrieval evidence conflicts.",
        ],
        recommendation_reasons=[
            "The architecture cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The knowledge-assistant architecture uses an LLM "
                    "for generation."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_retrieval_pipeline",
                source=EvidenceSource.DERIVED,
                value=False,
                reason="The candidate does not use retrieval.",
            ),
            AgentStarterEvidence(
                key="candidate_uses_retrieval_pipeline",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="The candidate uses retrieval.",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Knowledge stack mapping requires exactly one "
            "candidate_uses_retrieval_pipeline boolean evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.KNOWLEDGE_RAG,
            assessment=assessment,
        )


def test_catalog_query_builder_maps_voice_pipeline_to_stt_and_tts_queries():
    assessment = CandidateArchitectureAssessment(
        architecture_id="local-voice-pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The voice architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The voice architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_stt",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The voice-pipeline architecture uses speech-to-text "
                    "for speech input processing."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_tts",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The voice-pipeline architecture uses text-to-speech "
                    "for speech output generation."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_raw_audio_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Raw audio remains inside the "
                    "user-controlled environment."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_transcript_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Transcripts remain inside the "
                    "user-controlled environment."
                ),
            ),
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.VOICE,
        assessment=assessment,
    )

    assert [
        query.component_type
        for query in queries
    ] == [
        AgentStarterCatalogComponentType.STT,
        AgentStarterCatalogComponentType.TTS,
    ]

    for query in queries:
        assert query.required_capabilities == []
        assert query.required_deployment_modes == []
        assert query.required_runtime is None
        assert query.required_pricing_class is None


def test_catalog_query_builder_does_not_infer_deployment_for_hybrid_voice():
    assessment = CandidateArchitectureAssessment(
        architecture_id="hybrid-voice-pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The hybrid voice architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The hybrid voice architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_stt",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The voice-pipeline architecture uses speech-to-text "
                    "for speech input processing."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_tts",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The voice-pipeline architecture uses text-to-speech "
                    "for speech output generation."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_raw_audio_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Raw audio remains inside the "
                    "user-controlled environment."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_transcript_remote_processing",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "Transcript processing may occur outside the "
                    "user-controlled environment."
                ),
            ),
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.VOICE,
        assessment=assessment,
    )

    assert [
        query.component_type
        for query in queries
    ] == [
        AgentStarterCatalogComponentType.STT,
        AgentStarterCatalogComponentType.TTS,
    ]

    assert all(
        query.required_deployment_modes == []
        for query in queries
    )


def test_catalog_query_builder_rejects_voice_without_transcript_boundary_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="incomplete-voice-pipeline",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "Transcript processing boundary is unknown.",
        ],
        recommendation_reasons=[
            "The voice architecture cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_stt",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The voice-pipeline architecture uses speech-to-text "
                    "for speech input processing."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_tts",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The voice-pipeline architecture uses text-to-speech "
                    "for speech output generation."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_raw_audio_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Raw audio remains inside the "
                    "user-controlled environment."
                ),
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Voice stack mapping requires exactly one "
            "candidate_transcript_remote_processing boolean evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.VOICE,
            assessment=assessment,
        )


def test_catalog_query_builder_maps_session_only_personal_to_llm_query():
    assessment = CandidateArchitectureAssessment(
        architecture_id="session-only-personal-assistant",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The personal assistant architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The personal assistant satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_supports_persistent_memory",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "The session-only architecture does not retain "
                    "memory across sessions."
                ),
            ),
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.PERSONAL,
        assessment=assessment,
    )

    assert len(queries) == 1

    query = queries[0]

    assert (
        query.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert query.required_capabilities == []
    assert query.required_deployment_modes == []
    assert query.required_runtime is None
    assert query.required_pricing_class is None


def test_catalog_query_builder_maps_persistent_memory_personal_to_llm_query():
    assessment = CandidateArchitectureAssessment(
        architecture_id="controlled-persistent-memory-assistant",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The persistent-memory architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The persistent-memory architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_supports_persistent_memory",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The architecture retains memory across sessions."
                ),
            ),
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.PERSONAL,
        assessment=assessment,
    )

    assert len(queries) == 1
    assert (
        queries[0].component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert queries[0].required_capabilities == []
    assert queries[0].required_deployment_modes == []
    assert queries[0].required_runtime is None
    assert queries[0].required_pricing_class is None


def test_catalog_query_builder_rejects_personal_without_memory_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="unknown-personal-assistant",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "Persistent-memory behavior is unknown.",
        ],
        recommendation_reasons=[
            "The personal architecture cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="unrelated_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="Unrelated evidence.",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Personal catalog mapping requires exactly one "
            "candidate_supports_persistent_memory evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.PERSONAL,
            assessment=assessment,
        )


def test_catalog_query_builder_rejects_conflicting_personal_memory_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="conflicting-personal-assistant",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "Persistent-memory evidence conflicts.",
        ],
        recommendation_reasons=[
            "The personal architecture cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_supports_persistent_memory",
                source=EvidenceSource.DERIVED,
                value=False,
                reason="The candidate has no persistent memory.",
            ),
            AgentStarterEvidence(
                key="candidate_supports_persistent_memory",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="The candidate has persistent memory.",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Personal catalog mapping requires exactly one "
            "candidate_supports_persistent_memory evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.PERSONAL,
            assessment=assessment,
        )


def test_catalog_query_builder_rejects_coding_without_llm_usage_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="local-coding-agent",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "LLM usage is not established.",
        ],
        recommendation_reasons=[
            "The stack cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="unrelated_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The assessment contains evidence, "
                    "but not LLM-usage evidence."
                ),
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Coding stack mapping requires exactly one "
            "candidate_uses_llm evidence value equal to true"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.CODING,
            assessment=assessment,
        )


def test_catalog_query_builder_routes_automation_validation_through_stack_requirements():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="unknown-automation",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "LLM usage is not established.",
        ],
        recommendation_reasons=[
            "The stack cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="unrelated_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The assessment contains evidence, "
                    "but not LLM-usage evidence."
                ),
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Automation stack mapping requires exactly one "
            "candidate_uses_llm boolean evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.AUTOMATION,
            assessment=assessment,
        )


def test_catalog_query_builder_routes_rag_validation_through_stack_requirements():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="unknown-knowledge-architecture",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "Retrieval architecture is not established.",
        ],
        recommendation_reasons=[
            "The stack cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The architecture uses an LLM "
                    "for generation."
                ),
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Knowledge stack mapping requires exactly one "
            "candidate_uses_retrieval_pipeline boolean evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.KNOWLEDGE_RAG,
            assessment=assessment,
        )


def test_catalog_query_builder_routes_voice_validation_through_stack_requirements():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="incomplete-voice-pipeline",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "STT usage is not established.",
        ],
        recommendation_reasons=[
            "The voice stack cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_tts",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="The candidate uses text-to-speech.",
            ),
            AgentStarterEvidence(
                key="candidate_raw_audio_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason="Raw audio remains local.",
            ),
            AgentStarterEvidence(
                key="candidate_transcript_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason="Transcripts remain local.",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Voice stack mapping requires exactly one "
            "candidate_uses_stt evidence value equal to true"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.VOICE,
            assessment=assessment,
        )
