from abc import ABC

from observer.core.task_evidence import (
    TaskEvidenceCollector,
)


def test_task_evidence_collector_is_abstract_contract():
    assert issubclass(
        TaskEvidenceCollector,
        ABC,
    )

    assert TaskEvidenceCollector.__abstractmethods__ == {
        "collect",
    }
