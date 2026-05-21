from __future__ import annotations

from deeptutor.services.diagnostic_engine import DiagnosticEngine


def test_grade_one_sequence_uses_all_grade_one_questions() -> None:
    engine = DiagnosticEngine()

    sequence = engine.build_diagnostic_sequence(1)

    assert len(sequence) == 4
    assert {item["grade"] for item in sequence} == {1}
    assert sequence[0]["topic_id"] == "g1_t01"


def test_run_diagnostic_collects_weak_topic_and_grade_stats() -> None:
    engine = DiagnosticEngine()
    answers = [
        {"question_id": "g1_t01_q01", "grade": 1, "topic_id": "g1_t01", "topic": "Счёт до 10", "is_correct": True},
        {"question_id": "g1_t02_q01", "grade": 1, "topic_id": "g1_t02", "topic": "Следующее число", "is_correct": False},
        {"question_id": "g1_t03_q01", "grade": 1, "topic_id": "g1_t03", "topic": "Сложение с переходом", "is_correct": False},
    ]

    result = engine.run_diagnostic(1, answers)

    assert result.claimed_grade == 1
    assert result.actual_grade == 1
    assert result.total_questions == 3
    assert result.correct_count == 1
    assert result.needs_review is True
    assert result.weak_topics[0]["topic_id"] == "g1_t02"
    assert result.grade_stats[1]["wrong"] == 2
    learning_path = result.get_learning_path()
    assert learning_path["start_grade"] == 1
    assert learning_path["start_topic_id"] == "g1_t02"
