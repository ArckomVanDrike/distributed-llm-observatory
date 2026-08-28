from dataclasses import dataclass

from observer.core.agent_starter_decision_engine import (
    assess_agent_starter_candidate,
)
from observer.core.agent_starter_plan_builder import (
    build_agent_starter_plan,
)
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


@dataclass(frozen=True)
class GoldenCandidate:
    architecture_id: str
    technical_feasibility: TechnicalFeasibility
    evidence: tuple[AgentStarterEvidence, ...]
    expected_recommendation: RecommendationVerdict
    expected_confidence: RecommendationConfidence
    expected_blocking_requirement_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentStarterGoldenFixture:
    fixture_id: str
    goal: AgentStarterGoal
    requirements: tuple[AgentStarterRequirement, ...]
    candidates: tuple[GoldenCandidate, ...]
    expected_constraint_conflict: bool = False


def _run_golden_fixture(fixture: AgentStarterGoldenFixture):
    requirements = list(fixture.requirements)

    assessments = [
        assess_agent_starter_candidate(
            goal=fixture.goal,
            architecture_id=candidate.architecture_id,
            technical_feasibility=candidate.technical_feasibility,
            requirements=requirements,
            candidate_evidence=list(candidate.evidence),
        )
        for candidate in fixture.candidates
    ]

    plan = build_agent_starter_plan(
        goal=fixture.goal,
        requirements=requirements,
        candidate_assessments=assessments,
    )

    return plan


LOCAL_CODE_REQUIREMENT = AgentStarterRequirement(
    key="source_code_must_stay_local",
    value=True,
    strength=ConstraintStrength.HARD,
    evidence=[
        AgentStarterEvidence(
            key="source_code_local_only",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
    ],
)


GOLDEN_01_LOCAL_PRIVATE_CODING = AgentStarterGoldenFixture(
    fixture_id="golden-01-local-private-coding",
    goal=AgentStarterGoal.CODING,
    requirements=(LOCAL_CODE_REQUIREMENT,),
    candidates=(
        GoldenCandidate(
            architecture_id="local-coding-agent",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=(
                AgentStarterEvidence(
                    key="source_code_remote_processing",
                    source=EvidenceSource.DERIVED,
                    value=False,
                    reason=(
                        "The local architecture processes source "
                        "code on the observed device."
                    ),
                ),
            ),
            expected_recommendation=RecommendationVerdict.POSSIBLE,
            expected_confidence=RecommendationConfidence.MEDIUM,
        ),
        GoldenCandidate(
            architecture_id="remote-coding-agent",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=(
                AgentStarterEvidence(
                    key="source_code_remote_processing",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The remote architecture sends source code "
                        "outside the observed device."
                    ),
                ),
            ),
            expected_recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            expected_confidence=RecommendationConfidence.HIGH,
            expected_blocking_requirement_keys=(
                "source_code_must_stay_local",
            ),
        ),
    ),
)


def test_golden_01_local_private_coding():
    fixture = GOLDEN_01_LOCAL_PRIVATE_CODING

    plan = _run_golden_fixture(fixture)

    assert plan.goal is fixture.goal
    assert plan.constraint_conflict is None

    assert [
        assessment.architecture_id
        for assessment in plan.candidate_assessments
    ] == [
        candidate.architecture_id
        for candidate in fixture.candidates
    ]

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert {
            requirement.key
            for requirement in assessment.blocking_requirements
        } == set(candidate.expected_blocking_requirement_keys)


def test_agent_starter_dispatches_all_supported_goals(monkeypatch):
    import observer.core.agent_starter_decision_engine as engine

    calls = []

    def make_assessor(expected_goal):
        def assessor(
            *,
            architecture_id,
            technical_feasibility,
            requirements,
            candidate_evidence,
        ):
            calls.append(expected_goal)
            return CandidateArchitectureAssessment(
                architecture_id=architecture_id,
                technical_feasibility=technical_feasibility,
                recommendation=RecommendationVerdict.POSSIBLE,
                confidence=RecommendationConfidence.MEDIUM,
                technical_reasons=["Dispatch test."],
                recommendation_reasons=["Dispatch test."],
                supporting_evidence=[
                    AgentStarterEvidence(
                        key="dispatch_test_evidence",
                        source=EvidenceSource.DERIVED,
                        value=True,
                        reason=(
                            "Synthetic evidence used only to verify "
                            "goal dispatch."
                        ),
                    ),
                ],
            )

        return assessor

    routes = {
        AgentStarterGoal.CODING: "assess_coding_candidate",
        AgentStarterGoal.AUTOMATION: "assess_automation_candidate",
        AgentStarterGoal.KNOWLEDGE_RAG: "assess_rag_candidate",
        AgentStarterGoal.VOICE: "assess_voice_candidate",
        AgentStarterGoal.PERSONAL: "assess_personal_candidate",
    }

    for goal, attribute in routes.items():
        monkeypatch.setattr(
            engine,
            attribute,
            make_assessor(goal),
        )

    for goal in routes:
        result = engine.assess_agent_starter_candidate(
            goal=goal,
            architecture_id=f"{goal.value}-candidate",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            requirements=[],
            candidate_evidence=[],
        )

        assert result.architecture_id == f"{goal.value}-candidate"

    assert calls == list(routes)


GOLDEN_02_CPU_ONLY_CODING_CLOUD_ALLOWED = AgentStarterGoldenFixture(
    fixture_id="golden-02-cpu-only-coding-cloud-allowed",
    goal=AgentStarterGoal.CODING,
    requirements=(),
    candidates=(
        GoldenCandidate(
            architecture_id="local-cpu-coding-agent",
            technical_feasibility=TechnicalFeasibility.LIMITED,
            evidence=(
                AgentStarterEvidence(
                    key="source_code_remote_processing",
                    source=EvidenceSource.DERIVED,
                    value=False,
                    reason=(
                        "The local architecture keeps source code "
                        "on the observed CPU-only device."
                    ),
                ),
            ),
            expected_recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            expected_confidence=RecommendationConfidence.MEDIUM,
        ),
        GoldenCandidate(
            architecture_id="cloud-coding-agent",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=(
                AgentStarterEvidence(
                    key="source_code_remote_processing",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The cloud architecture processes source code "
                        "remotely, which is allowed in this scenario."
                    ),
                ),
            ),
            expected_recommendation=RecommendationVerdict.POSSIBLE,
            expected_confidence=RecommendationConfidence.MEDIUM,
        ),
    ),
)


def test_golden_02_cpu_only_coding_cloud_allowed():
    fixture = GOLDEN_02_CPU_ONLY_CODING_CLOUD_ALLOWED

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.CODING
    assert plan.constraint_conflict is None

    assert [
        assessment.architecture_id
        for assessment in plan.candidate_assessments
    ] == [
        "local-cpu-coding-agent",
        "cloud-coding-agent",
    ]

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert assessment.blocking_requirements == []


GOLDEN_03_CPU_ONLY_CODING_LOCAL_ONLY = AgentStarterGoldenFixture(
    fixture_id="golden-03-cpu-only-coding-local-only",
    goal=AgentStarterGoal.CODING,
    requirements=(LOCAL_CODE_REQUIREMENT,),
    candidates=(
        GoldenCandidate(
            architecture_id="local-cpu-coding-agent",
            technical_feasibility=TechnicalFeasibility.LIMITED,
            evidence=(
                AgentStarterEvidence(
                    key="source_code_remote_processing",
                    source=EvidenceSource.DERIVED,
                    value=False,
                    reason=(
                        "The local architecture keeps source code "
                        "on the observed CPU-only device."
                    ),
                ),
            ),
            expected_recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            expected_confidence=RecommendationConfidence.MEDIUM,
        ),
        GoldenCandidate(
            architecture_id="cloud-coding-agent",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=(
                AgentStarterEvidence(
                    key="source_code_remote_processing",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The cloud architecture would send source "
                        "code outside the observed device."
                    ),
                ),
            ),
            expected_recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            expected_confidence=RecommendationConfidence.HIGH,
            expected_blocking_requirement_keys=(
                "source_code_must_stay_local",
            ),
        ),
    ),
)


def test_golden_03_cpu_only_coding_local_only():
    fixture = GOLDEN_03_CPU_ONLY_CODING_LOCAL_ONLY

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.CODING
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert {
            requirement.key
            for requirement in assessment.blocking_requirements
        } == set(candidate.expected_blocking_requirement_keys)


GOLDEN_04_TINY_DOCUMENTS_RAG_UNNECESSARY = AgentStarterGoldenFixture(
    fixture_id="golden-04-tiny-documents-rag-unnecessary",
    goal=AgentStarterGoal.KNOWLEDGE_RAG,
    requirements=(),
    candidates=(
        GoldenCandidate(
            architecture_id="direct-context-knowledge-assistant",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=(
                AgentStarterEvidence(
                    key="corpus_fits_direct_context",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The document collection is small enough "
                        "to fit directly in the working context."
                    ),
                ),
                AgentStarterEvidence(
                    key="retrieval_required",
                    source=EvidenceSource.DERIVED,
                    value=False,
                    reason=(
                        "A retrieval layer is not required for "
                        "this small document collection."
                    ),
                ),
                AgentStarterEvidence(
                    key="candidate_uses_retrieval_pipeline",
                    source=EvidenceSource.DERIVED,
                    value=False,
                    reason=(
                        "The candidate uses direct context instead "
                        "of a retrieval pipeline."
                    ),
                ),
            ),
            expected_recommendation=RecommendationVerdict.RECOMMENDED,
            expected_confidence=RecommendationConfidence.HIGH,
        ),
        GoldenCandidate(
            architecture_id="full-rag-pipeline",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=(
                AgentStarterEvidence(
                    key="corpus_fits_direct_context",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The document collection is small enough "
                        "to fit directly in the working context."
                    ),
                ),
                AgentStarterEvidence(
                    key="retrieval_required",
                    source=EvidenceSource.DERIVED,
                    value=False,
                    reason=(
                        "A retrieval layer is not required for "
                        "this small document collection."
                    ),
                ),
                AgentStarterEvidence(
                    key="candidate_uses_retrieval_pipeline",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The candidate introduces a full retrieval "
                        "pipeline despite the corpus fitting context."
                    ),
                ),
            ),
            expected_recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            expected_confidence=RecommendationConfidence.HIGH,
        ),
    ),
)


def test_golden_04_tiny_documents_rag_unnecessary():
    fixture = GOLDEN_04_TINY_DOCUMENTS_RAG_UNNECESSARY

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.KNOWLEDGE_RAG
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert assessment.blocking_requirements == []


PRIVATE_KNOWLEDGE_LOCAL_ONLY_REQUIREMENT = AgentStarterRequirement(
    key="knowledge_data_must_stay_local",
    value=True,
    strength=ConstraintStrength.HARD,
    evidence=[
        AgentStarterEvidence(
            key="knowledge_data_local_only",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
    ],
)


def _private_medium_rag_evidence(
    *,
    candidate_knowledge_data_remote_processing: bool,
) -> tuple[AgentStarterEvidence, ...]:
    return (
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The medium knowledge corpus does not fit "
                "reliably in direct working context."
            ),
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "Retrieval is required for the medium "
                "knowledge corpus."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_uses_retrieval_pipeline",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The candidate uses a retrieval pipeline."
            ),
        ),
        AgentStarterEvidence(
            key="citations_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_provides_source_provenance",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "Retrieved evidence retains source provenance "
                "for citation."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_knowledge_data_remote_processing",
            source=EvidenceSource.DERIVED,
            value=candidate_knowledge_data_remote_processing,
            reason=(
                "The candidate architecture explicitly defines "
                "whether private knowledge data is processed "
                "outside the observed device."
            ),
        ),
    )


GOLDEN_05_PRIVATE_MEDIUM_RAG = AgentStarterGoldenFixture(
    fixture_id="golden-05-private-medium-rag",
    goal=AgentStarterGoal.KNOWLEDGE_RAG,
    requirements=(PRIVATE_KNOWLEDGE_LOCAL_ONLY_REQUIREMENT,),
    candidates=(
        GoldenCandidate(
            architecture_id="local-private-rag",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=_private_medium_rag_evidence(
                candidate_knowledge_data_remote_processing=False,
            ),
            expected_recommendation=RecommendationVerdict.POSSIBLE,
            expected_confidence=RecommendationConfidence.MEDIUM,
        ),
        GoldenCandidate(
            architecture_id="remote-private-rag",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=_private_medium_rag_evidence(
                candidate_knowledge_data_remote_processing=True,
            ),
            expected_recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            expected_confidence=RecommendationConfidence.HIGH,
            expected_blocking_requirement_keys=(
                "knowledge_data_must_stay_local",
            ),
        ),
    ),
)


def test_golden_05_private_medium_rag():
    fixture = GOLDEN_05_PRIVATE_MEDIUM_RAG

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.KNOWLEDGE_RAG
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert {
            requirement.key
            for requirement in assessment.blocking_requirements
        } == set(candidate.expected_blocking_requirement_keys)


def _large_multi_user_rag_evidence() -> tuple[AgentStarterEvidence, ...]:
    return (
        AgentStarterEvidence(
            key="corpus_fits_direct_context",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The large shared corpus does not fit reliably "
                "in direct working context."
            ),
        ),
        AgentStarterEvidence(
            key="retrieval_required",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "Retrieval is required for the large multi-user corpus."
            ),
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
            value=True,
            reason=(
                "Retrieved evidence preserves source provenance "
                "for citations."
            ),
        ),
        AgentStarterEvidence(
            key="corpus_updates_frequent",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_incremental_indexing",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The candidate supports incremental indexing "
                "for frequently updated shared content."
            ),
        ),
    )


GOLDEN_06_LARGE_MULTI_USER_RAG_CLOUD_ALLOWED = AgentStarterGoldenFixture(
    fixture_id="golden-06-large-multi-user-rag-cloud-allowed",
    goal=AgentStarterGoal.KNOWLEDGE_RAG,
    requirements=(),
    candidates=(
        GoldenCandidate(
            architecture_id="local-large-rag",
            technical_feasibility=TechnicalFeasibility.LIMITED,
            evidence=_large_multi_user_rag_evidence(),
            expected_recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            expected_confidence=RecommendationConfidence.MEDIUM,
        ),
        GoldenCandidate(
            architecture_id="cloud-large-rag",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=_large_multi_user_rag_evidence(),
            expected_recommendation=RecommendationVerdict.POSSIBLE,
            expected_confidence=RecommendationConfidence.MEDIUM,
        ),
    ),
)


def test_golden_06_large_multi_user_rag_cloud_allowed():
    fixture = GOLDEN_06_LARGE_MULTI_USER_RAG_CLOUD_ALLOWED

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.KNOWLEDGE_RAG
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert assessment.blocking_requirements == []


RAW_AUDIO_LOCAL_ONLY_REQUIREMENT = AgentStarterRequirement(
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


TRANSCRIPT_LOCAL_ONLY_REQUIREMENT = AgentStarterRequirement(
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


def _realtime_voice_evidence(
    *,
    raw_audio_remote: bool,
    transcript_remote: bool,
) -> tuple[AgentStarterEvidence, ...]:
    return (
        AgentStarterEvidence(
            key="realtime_voice_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_streaming",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate supports streaming voice interaction.",
        ),
        AgentStarterEvidence(
            key="candidate_meets_realtime_latency_requirement",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The candidate meets the explicit realtime latency "
                "requirement for this fixture."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_raw_audio_remote_processing",
            source=EvidenceSource.DERIVED,
            value=raw_audio_remote,
            reason=(
                "The candidate architecture explicitly defines "
                "whether raw audio is processed remotely."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_transcript_remote_processing",
            source=EvidenceSource.DERIVED,
            value=transcript_remote,
            reason=(
                "The candidate architecture explicitly defines "
                "whether transcript data is processed remotely."
            ),
        ),
    )


GOLDEN_07_REALTIME_OFFLINE_VOICE_CONSTRAINED = AgentStarterGoldenFixture(
    fixture_id="golden-07-realtime-offline-voice-constrained",
    goal=AgentStarterGoal.VOICE,
    requirements=(
        RAW_AUDIO_LOCAL_ONLY_REQUIREMENT,
        TRANSCRIPT_LOCAL_ONLY_REQUIREMENT,
    ),
    candidates=(
        GoldenCandidate(
            architecture_id="local-offline-voice",
            technical_feasibility=TechnicalFeasibility.LIMITED,
            evidence=_realtime_voice_evidence(
                raw_audio_remote=False,
                transcript_remote=False,
            ),
            expected_recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            expected_confidence=RecommendationConfidence.MEDIUM,
        ),
        GoldenCandidate(
            architecture_id="remote-realtime-voice",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=_realtime_voice_evidence(
                raw_audio_remote=True,
                transcript_remote=True,
            ),
            expected_recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            expected_confidence=RecommendationConfidence.HIGH,
            expected_blocking_requirement_keys=(
                "raw_audio_must_stay_local",
            ),
        ),
    ),
)


def test_golden_07_realtime_offline_voice_constrained():
    fixture = GOLDEN_07_REALTIME_OFFLINE_VOICE_CONSTRAINED

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.VOICE
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert {
            requirement.key
            for requirement in assessment.blocking_requirements
        } == set(candidate.expected_blocking_requirement_keys)


GOLDEN_08_HYBRID_VOICE_LOCAL_AUDIO_REMOTE_TRANSCRIPT = (
    AgentStarterGoldenFixture(
        fixture_id=(
            "golden-08-hybrid-voice-local-audio-remote-transcript"
        ),
        goal=AgentStarterGoal.VOICE,
        requirements=(RAW_AUDIO_LOCAL_ONLY_REQUIREMENT,),
        candidates=(
            GoldenCandidate(
                architecture_id="local-stt-remote-llm-voice",
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                evidence=_realtime_voice_evidence(
                    raw_audio_remote=False,
                    transcript_remote=True,
                ),
                expected_recommendation=RecommendationVerdict.POSSIBLE,
                expected_confidence=RecommendationConfidence.MEDIUM,
            ),
            GoldenCandidate(
                architecture_id="remote-stt-remote-llm-voice",
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                evidence=_realtime_voice_evidence(
                    raw_audio_remote=True,
                    transcript_remote=True,
                ),
                expected_recommendation=(
                    RecommendationVerdict.NOT_RECOMMENDED
                ),
                expected_confidence=RecommendationConfidence.HIGH,
                expected_blocking_requirement_keys=(
                    "raw_audio_must_stay_local",
                ),
            ),
        ),
    )
)


def test_golden_08_hybrid_voice_local_audio_remote_transcript():
    fixture = (
        GOLDEN_08_HYBRID_VOICE_LOCAL_AUDIO_REMOTE_TRANSCRIPT
    )

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.VOICE
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert {
            requirement.key
            for requirement in assessment.blocking_requirements
        } == set(candidate.expected_blocking_requirement_keys)


def _deterministic_automation_evidence(
    *,
    candidate_uses_llm: bool,
) -> tuple[AgentStarterEvidence, ...]:
    return (
        AgentStarterEvidence(
            key="workflow_deterministic",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The workflow follows deterministic rules "
                "with explicit inputs and actions."
            ),
        ),
        AgentStarterEvidence(
            key="semantic_interpretation_required",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "The workflow does not require semantic "
                "interpretation."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_uses_llm",
            source=EvidenceSource.DERIVED,
            value=candidate_uses_llm,
            reason=(
                "The candidate architecture explicitly defines "
                "whether an LLM participates in execution."
            ),
        ),
    )


GOLDEN_09_DETERMINISTIC_WORKFLOW_AI_UNNECESSARY = (
    AgentStarterGoldenFixture(
        fixture_id="golden-09-deterministic-workflow-ai-unnecessary",
        goal=AgentStarterGoal.AUTOMATION,
        requirements=(),
        candidates=(
            GoldenCandidate(
                architecture_id="traditional-deterministic-automation",
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                evidence=_deterministic_automation_evidence(
                    candidate_uses_llm=False,
                ),
                expected_recommendation=(
                    RecommendationVerdict.RECOMMENDED
                ),
                expected_confidence=RecommendationConfidence.HIGH,
            ),
            GoldenCandidate(
                architecture_id="llm-agent-deterministic-automation",
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                evidence=_deterministic_automation_evidence(
                    candidate_uses_llm=True,
                ),
                expected_recommendation=(
                    RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
                ),
                expected_confidence=RecommendationConfidence.HIGH,
            ),
        ),
    )
)


def test_golden_09_deterministic_workflow_ai_unnecessary():
    fixture = GOLDEN_09_DETERMINISTIC_WORKFLOW_AI_UNNECESSARY

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.AUTOMATION
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert assessment.blocking_requirements == []


def _email_automation_evidence(
    *,
    autonomous_execution: bool,
    human_approval_required: bool,
) -> tuple[AgentStarterEvidence, ...]:
    return (
        AgentStarterEvidence(
            key="workflow_deterministic",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "Email handling is not fully deterministic because "
                "message content requires interpretation."
            ),
        ),
        AgentStarterEvidence(
            key="semantic_interpretation_required",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "Email content requires semantic interpretation "
                "before a response can be prepared."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_uses_llm",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The candidate uses an LLM to interpret and draft "
                "email content."
            ),
        ),
        AgentStarterEvidence(
            key="destructive_or_high_impact_actions",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "Sending email externally is treated as a "
                "high-impact write action in this fixture."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_executes_autonomously",
            source=EvidenceSource.DERIVED,
            value=autonomous_execution,
            reason=(
                "The candidate architecture explicitly defines "
                "whether outbound email can be sent autonomously."
            ),
        ),
        AgentStarterEvidence(
            key="human_approval_required",
            source=EvidenceSource.DECLARED,
            value=human_approval_required,
        ),
    )


GOLDEN_10_SUPERVISED_EMAIL_AUTOMATION = AgentStarterGoldenFixture(
    fixture_id="golden-10-supervised-email-automation",
    goal=AgentStarterGoal.AUTOMATION,
    requirements=(),
    candidates=(
        GoldenCandidate(
            architecture_id="supervised-email-assistant",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=_email_automation_evidence(
                autonomous_execution=False,
                human_approval_required=True,
            ),
            expected_recommendation=RecommendationVerdict.POSSIBLE,
            expected_confidence=RecommendationConfidence.MEDIUM,
        ),
        GoldenCandidate(
            architecture_id="autonomous-email-sender",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=_email_automation_evidence(
                autonomous_execution=True,
                human_approval_required=False,
            ),
            expected_recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            expected_confidence=RecommendationConfidence.HIGH,
        ),
    ),
)


def test_golden_10_supervised_email_automation():
    fixture = GOLDEN_10_SUPERVISED_EMAIL_AUTOMATION

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.AUTOMATION
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert assessment.blocking_requirements == []


def _always_available_automation_evidence(
    *,
    candidate_always_available: bool,
) -> tuple[AgentStarterEvidence, ...]:
    return (
        AgentStarterEvidence(
            key="workflow_deterministic",
            source=EvidenceSource.DERIVED,
            value=False,
            reason=(
                "This fixture does not assume a purely "
                "deterministic workflow."
            ),
        ),
        AgentStarterEvidence(
            key="semantic_interpretation_required",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The automation requires semantic interpretation."
            ),
        ),
        AgentStarterEvidence(
            key="candidate_uses_llm",
            source=EvidenceSource.DERIVED,
            value=True,
            reason="The candidate uses an LLM.",
        ),
        AgentStarterEvidence(
            key="availability_24_7_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_always_available",
            source=EvidenceSource.DERIVED,
            value=candidate_always_available,
            reason=(
                "The candidate deployment explicitly defines "
                "whether it remains continuously available."
            ),
        ),
    )


GOLDEN_11_AUTOMATION_24_7_LAPTOP_NOT_ALWAYS_ON = (
    AgentStarterGoldenFixture(
        fixture_id="golden-11-automation-24-7-laptop-not-always-on",
        goal=AgentStarterGoal.AUTOMATION,
        requirements=(),
        candidates=(
            GoldenCandidate(
                architecture_id="always-on-automation-service",
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                evidence=_always_available_automation_evidence(
                    candidate_always_available=True,
                ),
                expected_recommendation=RecommendationVerdict.POSSIBLE,
                expected_confidence=RecommendationConfidence.MEDIUM,
            ),
            GoldenCandidate(
                architecture_id="laptop-hosted-automation",
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                evidence=_always_available_automation_evidence(
                    candidate_always_available=False,
                ),
                expected_recommendation=(
                    RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
                ),
                expected_confidence=RecommendationConfidence.HIGH,
            ),
        ),
    )
)


def test_golden_11_automation_24_7_laptop_not_always_on():
    fixture = GOLDEN_11_AUTOMATION_24_7_LAPTOP_NOT_ALWAYS_ON

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.AUTOMATION
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert assessment.blocking_requirements == []


def _selective_persistent_personal_evidence(
    *,
    memory_controls: bool,
) -> tuple[AgentStarterEvidence, ...]:
    return (
        AgentStarterEvidence(
            key="cross_session_memory_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_persistent_memory",
            source=EvidenceSource.DERIVED,
            value=True,
            reason=(
                "The candidate persists selected memory "
                "across sessions."
            ),
        ),
        AgentStarterEvidence(
            key="selective_memory_required",
            source=EvidenceSource.DECLARED,
            value=True,
        ),
        AgentStarterEvidence(
            key="candidate_supports_memory_inspect_edit_delete",
            source=EvidenceSource.DERIVED,
            value=memory_controls,
            reason=(
                "The candidate explicitly defines whether stored "
                "memory can be inspected, edited, and deleted."
            ),
        ),
    )


GOLDEN_12_PERSONAL_SELECTIVE_PERSISTENT_MEMORY = (
    AgentStarterGoldenFixture(
        fixture_id="golden-12-personal-selective-persistent-memory",
        goal=AgentStarterGoal.PERSONAL,
        requirements=(),
        candidates=(
            GoldenCandidate(
                architecture_id="controlled-persistent-memory-assistant",
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                evidence=_selective_persistent_personal_evidence(
                    memory_controls=True,
                ),
                expected_recommendation=RecommendationVerdict.POSSIBLE,
                expected_confidence=RecommendationConfidence.MEDIUM,
            ),
            GoldenCandidate(
                architecture_id="opaque-persistent-memory-assistant",
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                evidence=_selective_persistent_personal_evidence(
                    memory_controls=False,
                ),
                expected_recommendation=(
                    RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
                ),
                expected_confidence=RecommendationConfidence.HIGH,
            ),
        ),
    )
)


def test_golden_12_personal_selective_persistent_memory():
    fixture = GOLDEN_12_PERSONAL_SELECTIVE_PERSISTENT_MEMORY

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.PERSONAL
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert assessment.blocking_requirements == []


def _personal_retention_evidence(
    *,
    retains_all_conversations_indefinitely: bool,
) -> tuple[AgentStarterEvidence, ...]:
    return (
        AgentStarterEvidence(
            key="indefinite_all_conversation_retention_required",
            source=EvidenceSource.DECLARED,
            value=False,
        ),
        AgentStarterEvidence(
            key="candidate_retains_all_conversations_indefinitely",
            source=EvidenceSource.DERIVED,
            value=retains_all_conversations_indefinitely,
            reason=(
                "The candidate explicitly defines whether all "
                "conversation history is retained indefinitely."
            ),
        ),
    )


GOLDEN_13_PERSONAL_INDEFINITE_RETENTION_UNNECESSARY = (
    AgentStarterGoldenFixture(
        fixture_id=(
            "golden-13-personal-indefinite-retention-unnecessary"
        ),
        goal=AgentStarterGoal.PERSONAL,
        requirements=(),
        candidates=(
            GoldenCandidate(
                architecture_id="bounded-retention-personal-assistant",
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                evidence=_personal_retention_evidence(
                    retains_all_conversations_indefinitely=False,
                ),
                expected_recommendation=RecommendationVerdict.POSSIBLE,
                expected_confidence=RecommendationConfidence.MEDIUM,
            ),
            GoldenCandidate(
                architecture_id="retain-everything-personal-assistant",
                technical_feasibility=TechnicalFeasibility.FEASIBLE,
                evidence=_personal_retention_evidence(
                    retains_all_conversations_indefinitely=True,
                ),
                expected_recommendation=(
                    RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
                ),
                expected_confidence=RecommendationConfidence.HIGH,
            ),
        ),
    )
)


def test_golden_13_personal_indefinite_retention_unnecessary():
    fixture = GOLDEN_13_PERSONAL_INDEFINITE_RETENTION_UNNECESSARY

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.PERSONAL
    assert plan.constraint_conflict is None

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert assessment.blocking_requirements == []


GOLDEN_14_MOBILE_BROWSER_HARDWARE_UNKNOWN = AgentStarterGoldenFixture(
    fixture_id="golden-14-mobile-browser-hardware-unknown",
    goal=AgentStarterGoal.CODING,
    requirements=(),
    candidates=(
        GoldenCandidate(
            architecture_id="mobile-browser-local-coding-agent",
            technical_feasibility=TechnicalFeasibility.UNKNOWN,
            evidence=(
                AgentStarterEvidence(
                    key="environment_is_mobile_browser",
                    source=EvidenceSource.DECLARED,
                    value=True,
                ),
                AgentStarterEvidence(
                    key="important_hardware_information_available",
                    source=EvidenceSource.UNKNOWN,
                    value=None,
                    reason=(
                        "The browser environment cannot expose enough "
                        "hardware information to establish local "
                        "technical feasibility."
                    ),
                ),
                AgentStarterEvidence(
                    key="source_code_remote_processing",
                    source=EvidenceSource.DERIVED,
                    value=False,
                    reason=(
                        "The candidate is intended to process source "
                        "code locally if the device proves capable."
                    ),
                ),
            ),
            expected_recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            expected_confidence=RecommendationConfidence.LIMITED,
        ),
    ),
)


def test_golden_14_mobile_browser_hardware_unknown():
    fixture = GOLDEN_14_MOBILE_BROWSER_HARDWARE_UNKNOWN

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.CODING
    assert plan.constraint_conflict is None

    assessment = plan.candidate_assessments[0]
    candidate = fixture.candidates[0]

    assert (
        assessment.technical_feasibility
        is TechnicalFeasibility.UNKNOWN
    )
    assert (
        assessment.technical_feasibility
        is not TechnicalFeasibility.NOT_FEASIBLE
    )
    assert (
        assessment.recommendation
        is candidate.expected_recommendation
    )
    assert assessment.confidence is candidate.expected_confidence
    assert assessment.blocking_requirements == []

    assert any(
        "insufficient" in reason.lower()
        or "unknown" in reason.lower()
        for reason in assessment.recommendation_reasons
    )


GOLDEN_15_HARD_CONSTRAINT_CONFLICT = AgentStarterGoldenFixture(
    fixture_id="golden-15-hard-constraint-conflict",
    goal=AgentStarterGoal.CODING,
    requirements=(LOCAL_CODE_REQUIREMENT,),
    candidates=(
        GoldenCandidate(
            architecture_id="remote-cloud-coding-agent-a",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=(
                AgentStarterEvidence(
                    key="source_code_remote_processing",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The candidate sends source code outside "
                        "the observed device."
                    ),
                ),
            ),
            expected_recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            expected_confidence=RecommendationConfidence.HIGH,
            expected_blocking_requirement_keys=(
                "source_code_must_stay_local",
            ),
        ),
        GoldenCandidate(
            architecture_id="remote-cloud-coding-agent-b",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            evidence=(
                AgentStarterEvidence(
                    key="source_code_remote_processing",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The alternative candidate also sends "
                        "source code outside the observed device."
                    ),
                ),
            ),
            expected_recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            expected_confidence=RecommendationConfidence.HIGH,
            expected_blocking_requirement_keys=(
                "source_code_must_stay_local",
            ),
        ),
    ),
    expected_constraint_conflict=True,
)


def test_golden_15_hard_constraint_conflict():
    fixture = GOLDEN_15_HARD_CONSTRAINT_CONFLICT

    plan = _run_golden_fixture(fixture)

    assert plan.goal is AgentStarterGoal.CODING

    for candidate, assessment in zip(
        fixture.candidates,
        plan.candidate_assessments,
        strict=True,
    ):
        assert (
            assessment.recommendation
            is candidate.expected_recommendation
        )
        assert assessment.confidence is candidate.expected_confidence
        assert {
            requirement.key
            for requirement in assessment.blocking_requirements
        } == set(candidate.expected_blocking_requirement_keys)

    assert fixture.expected_constraint_conflict is True
    assert plan.constraint_conflict is not None

    assert {
        requirement.key
        for requirement in plan.constraint_conflict.conflicting_requirements
    } == {
        "source_code_must_stay_local",
    }

    assert plan.constraint_conflict.summary
    assert plan.constraint_conflict.resolution_options
