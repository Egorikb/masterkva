from __future__ import annotations

from deeptutor.services.practice_engine import PracticeEngine


def test_build_practice_item_from_weak_topic() -> None:
    engine = PracticeEngine()
    weak_topic = {
        "grade": 1,
        "topic_id": "g1_t03",
        "topic": "СЛОЖЕНИЕ С ПЕРЕХОДОМ",
        "source_question_id": "g1_t03_q01",
    }

    item = engine.build_practice_item(weak_topic)

    assert item["id"] == "g1_t03_p01"
    assert item["topic_id"] == "g1_t03"
    assert item["attempts"] == 0
    assert item["question"]
    assert item["answer"]


def test_create_practice_uses_topic_specific_task_not_hardcoded_42() -> None:
    engine = PracticeEngine()
    weak_topic = {
        "grade": 1,
        "topic_id": "g1_t03",
        "topic": "СЛОЖЕНИЕ/ВЫЧИТАНИЕ",
        "source_question_id": "g1_t03_q01",
    }

    practice = engine.create_practice(weak_topic)

    assert practice["topic_id"] == "g1_t03"
    assert practice["id"] == "g1_t03_p01"
    assert practice["question"]
    assert practice["answer"] != "42"
    assert practice["attempts"] == 0


def test_check_practice_answer_increments_attempts_and_returns_feedback() -> None:
    engine = PracticeEngine()
    practice = {
        "id": "g1_t03_p01",
        "topic_id": "g1_t03",
        "question": "4 + 3 = ?",
        "answer": "7",
        "attempts": 0,
    }

    feedback = engine.check_practice_answer(practice, "7")

    assert feedback["is_correct"] is True
    assert feedback["topic_id"] == "g1_t03"
    assert feedback["attempts"] == 1
    assert practice["attempts"] == 1


def test_check_practice_answer_rejects_wrong_numeric_answer() -> None:
    engine = PracticeEngine()
    practice = {
        "id": "g1_t03_p01",
        "topic_id": "g1_t03",
        "question": "4 + 3 = ?",
        "answer": "7",
        "attempts": 0,
    }

    feedback = engine.check_practice_answer(practice, "8")

    assert feedback["is_correct"] is False
    assert feedback["attempts"] == 1
