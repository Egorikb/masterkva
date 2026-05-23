from __future__ import annotations

from deeptutor.services.report_service import build_report


def test_report_practice_result_is_status_string() -> None:
    weak_topic = {
        "grade": 1,
        "topic_id": "g1_t03",
        "topic": "СЛОЖЕНИЕ С ПЕРЕХОДОМ",
        "source_question_id": "g1_t03_q01",
    }
    practice_feedback = {
        "is_correct": True,
        "confidence": 0.96,
        "user_answer": "13",
        "correct_answer": "13",
        "topic_id": "g1_t03",
        "attempts": 1,
    }

    report = build_report(weak_topic, practice_feedback)

    assert report["summary"]
    assert "по одной задаче" in report["summary"]
    assert report["weak_topic"] == weak_topic
    assert report["practice_result"] == "success"
    assert isinstance(report["recommendations"], list) and report["recommendations"]


def test_report_wrong_practice_result_needs_review() -> None:
    report = build_report({"topic": "Сложение"}, {"is_correct": False})
    assert report["practice_result"] == "needs_review"
    assert "Одна ошибка" in report["summary"]
    assert "о знании всей темы" in report["recommendations"][1]
