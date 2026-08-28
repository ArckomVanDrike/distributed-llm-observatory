import pytest
from pydantic import ValidationError

from schemas.agent_starter import (
    AgentStarterConstraintConflict,
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterPlan,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
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


def test_hard_requirement_records_declared_evidence():
    evidence = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    requirement = AgentStarterRequirement(
        key="source_code_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )

    assert requirement.schema_version == "0.1"
    assert requirement.key == "source_code_must_stay_local"
    assert requirement.value is True
    assert requirement.strength is ConstraintStrength.HARD
    assert requirement.evidence == [evidence]


def test_soft_requirement_records_declared_preference():
    evidence = AgentStarterEvidence(
        key="prefer_local_execution",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    requirement = AgentStarterRequirement(
        key="prefer_local_execution",
        value=True,
        strength=ConstraintStrength.SOFT,
        evidence=[evidence],
    )

    assert requirement.strength is ConstraintStrength.SOFT


def test_requirement_accepts_derived_evidence():
    evidence = AgentStarterEvidence(
        key="filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "User selected modify files and run tests."
        ),
    )

    requirement = AgentStarterRequirement(
        key="filesystem_write",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )

    assert (
        requirement.evidence[0].source
        is EvidenceSource.DERIVED
    )


def test_requirement_requires_supporting_evidence():
    with pytest.raises(
        ValidationError,
        match="Requirement must record supporting evidence",
    ):
        AgentStarterRequirement(
            key="offline_required",
            value=True,
            strength=ConstraintStrength.HARD,
            evidence=[],
        )


def test_requirement_rejects_unknown_only_evidence():
    unknown = AgentStarterEvidence(
        key="offline_required",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason="Offline requirement has not been established.",
    )

    with pytest.raises(
        ValidationError,
        match=(
            "Requirement cannot be supported only "
            "by unknown evidence"
        ),
    ):
        AgentStarterRequirement(
            key="offline_required",
            value=True,
            strength=ConstraintStrength.HARD,
            evidence=[unknown],
        )


def test_requirement_requires_value():
    evidence = AgentStarterEvidence(
        key="offline_required",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    with pytest.raises(
        ValidationError,
        match="Requirement must record a value",
    ):
        AgentStarterRequirement(
            key="offline_required",
            value=None,
            strength=ConstraintStrength.HARD,
            evidence=[evidence],
        )


def test_candidate_can_be_feasible_but_not_recommended():
    evidence = AgentStarterEvidence(
        key="local_cpu_execution",
        source=EvidenceSource.OBSERVED,
        value=True,
    )

    assessment = CandidateArchitectureAssessment(
        architecture_id="local_cpu_coding",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=(
            RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
        ),
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[
            "The workload can execute on the observed device.",
        ],
        recommendation_reasons=[
            (
                "Expected performance does not fit the requested "
                "autonomous coding workload."
            ),
        ],
        supporting_evidence=[evidence],
    )

    assert assessment.schema_version == "0.1"
    assert (
        assessment.technical_feasibility
        is TechnicalFeasibility.FEASIBLE
    )
    assert (
        assessment.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )


def test_candidate_recommendation_can_reflect_hard_requirement():
    evidence = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    assessment = CandidateArchitectureAssessment(
        architecture_id="cloud_coding",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "Remote inference is technically available.",
        ],
        recommendation_reasons=[
            "The architecture violates the local-only code boundary.",
        ],
        supporting_evidence=[evidence],
    )

    assert (
        assessment.technical_feasibility
        is TechnicalFeasibility.FEASIBLE
    )
    assert (
        assessment.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )


def test_candidate_requires_technical_reason():
    evidence = AgentStarterEvidence(
        key="total_memory_bytes",
        source=EvidenceSource.OBSERVED,
        value=16 * 1024**3,
    )

    with pytest.raises(
        ValidationError,
        match="Candidate assessment must explain technical feasibility",
    ):
        CandidateArchitectureAssessment(
            architecture_id="local_coding",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            recommendation=RecommendationVerdict.RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[],
            recommendation_reasons=[
                "The architecture fits the requested workload.",
            ],
            supporting_evidence=[evidence],
        )


def test_candidate_requires_recommendation_reason():
    evidence = AgentStarterEvidence(
        key="total_memory_bytes",
        source=EvidenceSource.OBSERVED,
        value=16 * 1024**3,
    )

    with pytest.raises(
        ValidationError,
        match="Candidate assessment must explain its recommendation",
    ):
        CandidateArchitectureAssessment(
            architecture_id="local_coding",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            recommendation=RecommendationVerdict.RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[
                "Observed resources satisfy the architecture.",
            ],
            recommendation_reasons=[],
            supporting_evidence=[evidence],
        )


def test_candidate_requires_supporting_evidence():
    with pytest.raises(
        ValidationError,
        match="Candidate assessment must record supporting evidence",
    ):
        CandidateArchitectureAssessment(
            architecture_id="local_coding",
            technical_feasibility=TechnicalFeasibility.UNKNOWN,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[
                "Available hardware evidence is incomplete.",
            ],
            recommendation_reasons=[
                "The architecture remains a possible option.",
            ],
            supporting_evidence=[],
        )


def test_constraint_conflict_records_hard_requirements_and_options():
    local_only_evidence = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    offline_evidence = AgentStarterEvidence(
        key="offline_required",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    local_only = AgentStarterRequirement(
        key="source_code_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[local_only_evidence],
    )
    offline = AgentStarterRequirement(
        key="offline_required",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[offline_evidence],
    )

    conflict = AgentStarterConstraintConflict(
        conflicting_requirements=[local_only, offline],
        summary=(
            "No evaluated architecture satisfies all hard requirements."
        ),
        resolution_options=[
            "Reduce the required capability.",
            "Upgrade the local hardware.",
            "Allow selected remote processing.",
        ],
    )

    assert conflict.schema_version == "0.1"
    assert conflict.conflicting_requirements == [
        local_only,
        offline,
    ]
    assert len(conflict.resolution_options) == 3


def test_constraint_conflict_accepts_single_hard_requirement():
    evidence = AgentStarterEvidence(
        key="offline_required",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    requirement = AgentStarterRequirement(
        key="offline_required",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )

    conflict = AgentStarterConstraintConflict(
        conflicting_requirements=[requirement],
        summary=(
            "The required capability cannot be satisfied "
            "under the offline boundary."
        ),
        resolution_options=[
            "Change the offline requirement.",
        ],
    )

    assert conflict.conflicting_requirements == [requirement]


def test_constraint_conflict_rejects_soft_requirement():
    evidence = AgentStarterEvidence(
        key="prefer_local_execution",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    preference = AgentStarterRequirement(
        key="prefer_local_execution",
        value=True,
        strength=ConstraintStrength.SOFT,
        evidence=[evidence],
    )

    with pytest.raises(
        ValidationError,
        match="Constraint conflict may contain only hard requirements",
    ):
        AgentStarterConstraintConflict(
            conflicting_requirements=[preference],
            summary="No candidate satisfies the preference.",
            resolution_options=[
                "Use another architecture.",
            ],
        )


def test_constraint_conflict_requires_requirement():
    with pytest.raises(
        ValidationError,
        match="Constraint conflict must identify a hard requirement",
    ):
        AgentStarterConstraintConflict(
            conflicting_requirements=[],
            summary="No evaluated architecture is suitable.",
            resolution_options=[
                "Change the requirements.",
            ],
        )


def test_constraint_conflict_requires_resolution_option():
    evidence = AgentStarterEvidence(
        key="offline_required",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    requirement = AgentStarterRequirement(
        key="offline_required",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )

    with pytest.raises(
        ValidationError,
        match="Constraint conflict must expose a resolution option",
    ):
        AgentStarterConstraintConflict(
            conflicting_requirements=[requirement],
            summary=(
                "No evaluated architecture satisfies the requirement."
            ),
            resolution_options=[],
        )


def test_agent_starter_plan_records_goal_requirements_and_candidates():
    evidence = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    requirement = AgentStarterRequirement(
        key="source_code_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )
    candidate = CandidateArchitectureAssessment(
        architecture_id="local_first_coding",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The observed environment supports local execution.",
        ],
        recommendation_reasons=[
            "The architecture respects the local-only code boundary.",
        ],
        supporting_evidence=[evidence],
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[requirement],
        candidate_assessments=[candidate],
    )

    assert plan.schema_version == "0.1"
    assert plan.goal is AgentStarterGoal.CODING
    assert plan.requirements == [requirement]
    assert plan.candidate_assessments == [candidate]
    assert plan.constraint_conflict is None


def test_agent_starter_plan_can_record_constraint_conflict():
    evidence = AgentStarterEvidence(
        key="offline_required",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    requirement = AgentStarterRequirement(
        key="offline_required",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )
    candidate = CandidateArchitectureAssessment(
        architecture_id="cloud_voice",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "Remote voice processing is technically available.",
        ],
        recommendation_reasons=[
            "The architecture violates the offline requirement.",
        ],
        supporting_evidence=[evidence],
    )
    conflict = AgentStarterConstraintConflict(
        conflicting_requirements=[requirement],
        summary=(
            "The requested capability cannot be satisfied "
            "under the offline boundary."
        ),
        resolution_options=[
            "Allow selected remote processing.",
            "Reduce the required capability.",
        ],
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.VOICE,
        requirements=[requirement],
        candidate_assessments=[candidate],
        constraint_conflict=conflict,
    )

    assert plan.constraint_conflict == conflict
    assert plan.candidate_assessments == [candidate]


def test_agent_starter_plan_requires_decision_state():
    with pytest.raises(
        ValidationError,
        match=(
            "Agent Starter plan must record candidate assessments "
            "or a constraint conflict"
        ),
    ):
        AgentStarterPlan(
            goal=AgentStarterGoal.PERSONAL,
            requirements=[],
            candidate_assessments=[],
        )


def test_agent_starter_plan_conflict_rejects_recommended_candidate():
    evidence = AgentStarterEvidence(
        key="offline_required",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    requirement = AgentStarterRequirement(
        key="offline_required",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )
    candidate = CandidateArchitectureAssessment(
        architecture_id="local_voice",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The architecture can execute locally.",
        ],
        recommendation_reasons=[
            "The architecture satisfies the requested workflow.",
        ],
        supporting_evidence=[evidence],
    )
    conflict = AgentStarterConstraintConflict(
        conflicting_requirements=[requirement],
        summary=(
            "No architecture satisfies the hard requirement."
        ),
        resolution_options=[
            "Change the hard requirement.",
        ],
    )

    with pytest.raises(
        ValidationError,
        match=(
            "Constraint conflict cannot coexist with "
            "a recommended candidate"
        ),
    ):
        AgentStarterPlan(
            goal=AgentStarterGoal.VOICE,
            requirements=[requirement],
            candidate_assessments=[candidate],
            constraint_conflict=conflict,
        )


def test_candidate_assessment_records_blocking_hard_requirement():
    evidence = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    requirement = AgentStarterRequirement(
        key="source_code_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )

    assessment = CandidateArchitectureAssessment(
        architecture_id="cloud_coding",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "Remote inference is technically available.",
        ],
        recommendation_reasons=[
            "The candidate violates the local-only boundary.",
        ],
        supporting_evidence=[evidence],
        blocking_requirements=[requirement],
    )

    assert assessment.blocking_requirements == [requirement]


def test_candidate_assessment_rejects_soft_blocking_requirement():
    evidence = AgentStarterEvidence(
        key="prefer_local_execution",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    preference = AgentStarterRequirement(
        key="prefer_local_execution",
        value=True,
        strength=ConstraintStrength.SOFT,
        evidence=[evidence],
    )

    with pytest.raises(
        ValidationError,
        match="Blocking requirements must be hard constraints",
    ):
        CandidateArchitectureAssessment(
            architecture_id="cloud_coding",
            technical_feasibility=TechnicalFeasibility.FEASIBLE,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.MEDIUM,
            technical_reasons=[
                "Remote inference is technically available.",
            ],
            recommendation_reasons=[
                "Local execution is preferred.",
            ],
            supporting_evidence=[evidence],
            blocking_requirements=[preference],
        )


def test_agent_starter_intake_records_goal_declared_evidence_and_hardware():
    from schemas.agent_starter import AgentStarterIntake
    from schemas.hardware import (
        DeviceClass,
        HardwareProfile,
        HardwareProfileSource,
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.LAPTOP,
        source=HardwareProfileSource.NATIVE,
        os_name="Linux",
        logical_cpu_count=8,
        total_memory_bytes=16 * 1024**3,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="source_code_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
        hardware_profile=hardware,
    )

    assert intake.goal is AgentStarterGoal.CODING
    assert intake.evidence[0].source is EvidenceSource.DECLARED
    assert intake.hardware_profile == hardware


def test_agent_starter_intake_allows_observed_and_unknown_evidence():
    from schemas.agent_starter import AgentStarterIntake

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="microphone_available",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
            AgentStarterEvidence(
                key="accelerator_details_available",
                source=EvidenceSource.UNKNOWN,
                value=None,
                reason=(
                    "The browser environment does not expose "
                    "accelerator details."
                ),
            ),
        ],
    )

    assert [
        evidence.source
        for evidence in intake.evidence
    ] == [
        EvidenceSource.OBSERVED,
        EvidenceSource.UNKNOWN,
    ]
    assert intake.hardware_profile is None


def test_agent_starter_intake_rejects_derived_evidence():
    import pytest
    from pydantic import ValidationError

    from schemas.agent_starter import AgentStarterIntake

    with pytest.raises(
        ValidationError,
        match="Derived evidence belongs to orchestration",
    ):
        AgentStarterIntake(
            goal=AgentStarterGoal.CODING,
            evidence=[
                AgentStarterEvidence(
                    key="shell_execution_required",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "Repository modification requires shell execution."
                    ),
                ),
            ],
        )


def test_agent_starter_intake_can_start_with_goal_only():
    from schemas.agent_starter import AgentStarterIntake

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
    )

    assert intake.goal is AgentStarterGoal.PERSONAL
    assert intake.evidence == []
    assert intake.hardware_profile is None


def test_agent_starter_prepared_input_records_normalized_decision_inputs():
    from schemas.agent_starter import AgentStarterPreparedInput
    from schemas.hardware import (
        DeviceClass,
        HardwareProfile,
        HardwareProfileSource,
    )

    declared = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    derived = AgentStarterEvidence(
        key="filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="The user requested repository modification.",
    )

    requirement = AgentStarterRequirement(
        key="source_code_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[declared],
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.LAPTOP,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=16 * 1024**3,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[
            declared,
            derived,
        ],
        requirements=[requirement],
        hardware_profile=hardware,
    )

    assert prepared.goal is AgentStarterGoal.CODING
    assert prepared.evidence == [
        declared,
        derived,
    ]
    assert prepared.requirements == [requirement]
    assert prepared.hardware_profile == hardware


def test_agent_starter_prepared_input_can_represent_incomplete_intake():
    from schemas.agent_starter import AgentStarterPreparedInput

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.PERSONAL,
    )

    assert prepared.evidence == []
    assert prepared.requirements == []
    assert prepared.hardware_profile is None


def test_agent_starter_prepared_input_allows_derived_evidence():
    from schemas.agent_starter import AgentStarterPreparedInput

    derived = AgentStarterEvidence(
        key="semantic_interpretation_required",
        source=EvidenceSource.DERIVED,
        value=False,
        reason=(
            "The declared workflow is deterministic."
        ),
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[derived],
    )

    assert prepared.evidence == [derived]
    assert prepared.evidence[0].source is EvidenceSource.DERIVED
