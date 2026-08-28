from observer.core.agent_starter_stack_requirement_builder import (
    build_agent_starter_stack_requirements,
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


def test_stack_requirement_builder_maps_coding_llm_requirement():
    llm_evidence = AgentStarterEvidence(
        key="candidate_uses_llm",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The coding-agent architecture uses an LLM "
            "for coding assistance."
        ),
    )

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
            llm_evidence,
        ],
    )

    requirements = build_agent_starter_stack_requirements(
        goal=AgentStarterGoal.CODING,
        assessment=assessment,
    )

    assert len(requirements) == 1

    requirement = requirements[0]

    assert (
        requirement.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert requirement.required_capabilities == [
        "coding",
    ]
    assert requirement.required_deployment_modes == []
    assert requirement.required_runtime is None
    assert requirement.required_pricing_class is None
    assert requirement.supporting_evidence == [
        llm_evidence,
    ]


def test_stack_requirement_builder_rejects_coding_without_llm_evidence():
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
        build_agent_starter_stack_requirements(
            goal=AgentStarterGoal.CODING,
            assessment=assessment,
        )


def test_stack_requirement_builder_rejects_coding_without_llm_usage():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="coding-without-llm",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "The candidate does not use an LLM.",
        ],
        recommendation_reasons=[
            "The coding LLM stack requirement does not apply.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "The candidate explicitly does not use an LLM."
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
        build_agent_starter_stack_requirements(
            goal=AgentStarterGoal.CODING,
            assessment=assessment,
        )


def test_stack_requirement_builder_returns_no_components_for_deterministic_automation():
    llm_evidence = AgentStarterEvidence(
        key="candidate_uses_llm",
        source=EvidenceSource.DERIVED,
        value=False,
        reason=(
            "The deterministic automation architecture "
            "does not use an LLM."
        ),
    )

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
            llm_evidence,
        ],
    )

    requirements = build_agent_starter_stack_requirements(
        goal=AgentStarterGoal.AUTOMATION,
        assessment=assessment,
    )

    assert requirements == []


def test_stack_requirement_builder_maps_llm_automation_requirement():
    llm_evidence = AgentStarterEvidence(
        key="candidate_uses_llm",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The supervised automation architecture uses an LLM "
            "for agent behavior."
        ),
    )

    assessment = CandidateArchitectureAssessment(
        architecture_id="supervised-automation-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The automation architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The LLM architecture is a possible alternative.",
        ],
        supporting_evidence=[
            llm_evidence,
        ],
    )

    requirements = build_agent_starter_stack_requirements(
        goal=AgentStarterGoal.AUTOMATION,
        assessment=assessment,
    )

    assert len(requirements) == 1

    requirement = requirements[0]

    assert (
        requirement.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert requirement.required_capabilities == []
    assert requirement.required_deployment_modes == []
    assert requirement.required_runtime is None
    assert requirement.required_pricing_class is None
    assert requirement.supporting_evidence == [
        llm_evidence,
    ]


def test_stack_requirement_builder_rejects_automation_without_llm_evidence():
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
        build_agent_starter_stack_requirements(
            goal=AgentStarterGoal.AUTOMATION,
            assessment=assessment,
        )


def test_stack_requirement_builder_maps_direct_context_rag_to_llm():
    llm_evidence = AgentStarterEvidence(
        key="candidate_uses_llm",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The knowledge-assistant architecture uses an LLM "
            "for generation."
        ),
    )

    retrieval_evidence = AgentStarterEvidence(
        key="candidate_uses_retrieval_pipeline",
        source=EvidenceSource.DERIVED,
        value=False,
        reason=(
            "The direct-context architecture supplies knowledge "
            "without a retrieval stage."
        ),
    )

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
            llm_evidence,
            retrieval_evidence,
        ],
    )

    requirements = build_agent_starter_stack_requirements(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        assessment=assessment,
    )

    assert len(requirements) == 1

    requirement = requirements[0]

    assert (
        requirement.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert requirement.required_capabilities == []
    assert requirement.required_deployment_modes == []
    assert requirement.required_runtime is None
    assert requirement.required_pricing_class is None
    assert requirement.supporting_evidence == [
        llm_evidence,
    ]


def test_stack_requirement_builder_maps_full_rag_to_llm_without_inferred_retrieval_components():
    llm_evidence = AgentStarterEvidence(
        key="candidate_uses_llm",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The knowledge-assistant architecture uses an LLM "
            "for generation."
        ),
    )

    retrieval_evidence = AgentStarterEvidence(
        key="candidate_uses_retrieval_pipeline",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The full RAG architecture retrieves relevant knowledge "
            "before generation."
        ),
    )

    assessment = CandidateArchitectureAssessment(
        architecture_id="full-rag-pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The RAG architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "Retrieval satisfies the knowledge requirements.",
        ],
        supporting_evidence=[
            llm_evidence,
            retrieval_evidence,
        ],
    )

    requirements = build_agent_starter_stack_requirements(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        assessment=assessment,
    )

    assert [
        requirement.component_type
        for requirement in requirements
    ] == [
        AgentStarterCatalogComponentType.LLM,
    ]

    assert requirements[0].supporting_evidence == [
        llm_evidence,
    ]


def test_stack_requirement_builder_rejects_rag_without_retrieval_evidence():
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
        build_agent_starter_stack_requirements(
            goal=AgentStarterGoal.KNOWLEDGE_RAG,
            assessment=assessment,
        )


def test_stack_requirement_builder_maps_voice_to_stt_and_tts():
    stt_evidence = AgentStarterEvidence(
        key="candidate_uses_stt",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The voice-pipeline architecture uses speech-to-text "
            "for speech input processing."
        ),
    )

    tts_evidence = AgentStarterEvidence(
        key="candidate_uses_tts",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The voice-pipeline architecture uses text-to-speech "
            "for speech output generation."
        ),
    )

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
            stt_evidence,
            tts_evidence,
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

    requirements = build_agent_starter_stack_requirements(
        goal=AgentStarterGoal.VOICE,
        assessment=assessment,
    )

    assert [
        requirement.component_type
        for requirement in requirements
    ] == [
        AgentStarterCatalogComponentType.STT,
        AgentStarterCatalogComponentType.TTS,
    ]

    assert all(
        requirement.required_deployment_modes == []
        for requirement in requirements
    )

    assert requirements[0].supporting_evidence == [
        stt_evidence,
    ]
    assert requirements[1].supporting_evidence == [
        tts_evidence,
    ]


def test_stack_requirement_builder_rejects_voice_without_stt_usage_evidence():
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
        build_agent_starter_stack_requirements(
            goal=AgentStarterGoal.VOICE,
            assessment=assessment,
        )


def test_stack_requirement_builder_rejects_voice_without_transcript_boundary_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="incomplete-voice-pipeline",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "Transcript boundary is not established.",
        ],
        recommendation_reasons=[
            "The voice stack cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_stt",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="The candidate uses speech-to-text.",
            ),
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
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Voice stack mapping requires exactly one "
            "candidate_transcript_remote_processing "
            "boolean evidence value"
        ),
    ):
        build_agent_starter_stack_requirements(
            goal=AgentStarterGoal.VOICE,
            assessment=assessment,
        )
