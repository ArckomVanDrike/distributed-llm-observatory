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
