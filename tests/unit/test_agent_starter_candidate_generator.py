from schemas.agent_starter import (
    AgentStarterGoal,
    AgentStarterPreparedInput,
    EvidenceSource,
)


def test_generates_base_coding_candidates_in_deterministic_order():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "local-coding-agent",
        "remote-coding-agent",
    ]

    assert all(
        candidate.goal is AgentStarterGoal.CODING
        for candidate in candidates
    )


def test_coding_candidates_record_locality_evidence():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    candidates = generate_agent_starter_candidates(prepared)

    local_candidate, remote_candidate = candidates

    assert [
        evidence.key
        for evidence in local_candidate.evidence
    ] == [
        "source_code_remote_processing",
    ]
    assert local_candidate.evidence[0].value is False

    assert [
        evidence.key
        for evidence in remote_candidate.evidence
    ] == [
        "source_code_remote_processing",
    ]
    assert remote_candidate.evidence[0].value is True

    assert all(
        evidence.source is EvidenceSource.DERIVED
        for candidate in candidates
        for evidence in candidate.evidence
    )

    assert all(
        evidence.reason
        for candidate in candidates
        for evidence in candidate.evidence
    )


def test_coding_candidate_generation_does_not_filter_hard_privacy_conflicts():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from schemas.agent_starter import (
        AgentStarterEvidence,
        AgentStarterRequirement,
        ConstraintStrength,
    )

    declared = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[declared],
        requirements=[
            AgentStarterRequirement(
                key="source_code_must_stay_local",
                value=True,
                strength=ConstraintStrength.HARD,
                evidence=[declared],
            ),
        ],
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "local-coding-agent",
        "remote-coding-agent",
    ]


def test_coding_candidate_generation_does_not_add_assessment_state():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    candidates = generate_agent_starter_candidates(prepared)

    for candidate in candidates:
        assert not hasattr(candidate, "technical_feasibility")
        assert not hasattr(candidate, "recommendation")
        assert not hasattr(candidate, "confidence")


def test_candidate_generation_returns_empty_for_unimplemented_goals():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    for goal in (
        AgentStarterGoal.PERSONAL,
        AgentStarterGoal.AUTOMATION,
        AgentStarterGoal.VOICE,
    ):
        prepared = AgentStarterPreparedInput(
            goal=goal,
        )

        assert generate_agent_starter_candidates(prepared) == []


def test_generates_base_rag_candidates_in_deterministic_order():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "direct-context-knowledge-assistant",
        "full-rag-pipeline",
    ]

    assert all(
        candidate.goal is AgentStarterGoal.KNOWLEDGE_RAG
        for candidate in candidates
    )


def test_rag_candidates_record_retrieval_architecture_evidence():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
    )

    candidates = generate_agent_starter_candidates(prepared)

    direct_context, full_rag = candidates

    assert [
        evidence.key
        for evidence in direct_context.evidence
    ] == [
        "candidate_uses_retrieval",
    ]
    assert direct_context.evidence[0].value is False

    assert [
        evidence.key
        for evidence in full_rag.evidence
    ] == [
        "candidate_uses_retrieval",
    ]
    assert full_rag.evidence[0].value is True

    assert all(
        evidence.source is EvidenceSource.DERIVED
        for candidate in candidates
        for evidence in candidate.evidence
    )

    assert all(
        evidence.reason
        for candidate in candidates
        for evidence in candidate.evidence
    )


def test_rag_candidate_generation_does_not_filter_unneeded_retrieval():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from schemas.agent_starter import AgentStarterEvidence

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="retrieval_required",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "The declared corpus is small enough "
                    "for direct context."
                ),
            ),
        ],
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "direct-context-knowledge-assistant",
        "full-rag-pipeline",
    ]
