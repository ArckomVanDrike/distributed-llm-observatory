from observer.core.task_evidence import (
    TaskCriterionEvidence,
)


def test_task_criterion_evidence_is_observatory_owned():
    evidence = TaskCriterionEvidence(
        criterion_id="tests-pass",
        passed=True,
        evidence="pytest: 42 passed",
    )

    assert evidence.criterion_id == "tests-pass"
    assert evidence.passed is True
    assert evidence.evidence == "pytest: 42 passed"


def test_task_criterion_evidence_is_immutable():
    evidence = TaskCriterionEvidence(
        criterion_id="tests-pass",
        passed=True,
    )

    try:
        evidence.passed = False
    except AttributeError:
        pass
    else:
        raise AssertionError(
            "TaskCriterionEvidence must be immutable."
        )
