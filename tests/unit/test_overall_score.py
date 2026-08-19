import pytest
from pydantic import ValidationError

from schemas.evaluation import QualityEvaluation


def make_evaluation(**overrides):
    data = {
        "fit": 5,
        "efficiency": 5,
        "clarity": 5,
        "style": 5,
        "structure": 5,
        "technical_accuracy": 5,
        "overall": 5,
        "judge_model": "test-judge",
        "judge_version": "0.1",
    }
    data.update(overrides)
    return QualityEvaluation(**data)


def test_valid_high_quality_evaluation():
    evaluation = make_evaluation()

    assert evaluation.overall == 5
    assert evaluation.fit == 5


def test_dimension_one_limits_overall_to_two():
    with pytest.raises(ValidationError):
        make_evaluation(fit=1, overall=3)


def test_dimension_one_allows_overall_two():
    evaluation = make_evaluation(fit=1, overall=2)

    assert evaluation.overall == 2


def test_dimension_two_limits_overall_to_three():
    with pytest.raises(ValidationError):
        make_evaluation(clarity=2, overall=4)


def test_dimension_two_allows_overall_three():
    evaluation = make_evaluation(clarity=2, overall=3)

    assert evaluation.overall == 3


def test_all_dimensions_four_or_more_require_overall_four():
    with pytest.raises(ValidationError):
        make_evaluation(
            fit=4,
            efficiency=4,
            clarity=4,
            style=4,
            structure=4,
            technical_accuracy=4,
            overall=3,
        )


def test_all_dimensions_four_or_more_allow_overall_four():
    evaluation = make_evaluation(
        fit=4,
        efficiency=4,
        clarity=4,
        style=4,
        structure=4,
        technical_accuracy=4,
        overall=4,
    )

    assert evaluation.overall == 4


def test_scores_must_be_between_one_and_six():
    with pytest.raises(ValidationError):
        make_evaluation(fit=7)

    with pytest.raises(ValidationError):
        make_evaluation(style=0)


def test_judge_agreement_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        make_evaluation(judge_agreement=1.1)

    with pytest.raises(ValidationError):
        make_evaluation(judge_agreement=-0.1)
