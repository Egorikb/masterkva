"""Regression tests for diagnostic weak-topic extraction."""

from __future__ import annotations

from deeptutor.services.diagnostic_engine import DiagnosticEngine


def test_run_diagnostic_extracts_weak_topic_without_stable_question_id() -> None:
    """Wrong answers should still produce weak topics even if pool questions have no stable id."""
    engine = DiagnosticEngine()
    grade_1_questions = engine.get_questions_for_grade(1)
    failed_question = grade_1_questions[2]

    answers = [
        {
            "question_id": "g1-q3",
            "grade": 1,
            "user_answer": "0",
            "is_correct": False,
        }
    ]

    result = engine.run_diagnostic(claimed_grade=1, answers=answers)

    assert result.weak_topics, "Expected at least one weak topic for a wrong answer"
    weak = result.weak_topics[0]
    assert weak["grade"] == 1
    assert weak["topic"] == failed_question["topic"]
    assert weak["topic_id"].startswith("g1_t")
    assert weak["source_question_id"].startswith("g1_t")
    assert weak["question"] == failed_question["question"]


def test_select_weak_topic_returns_first_real_weak_topic() -> None:
    engine = DiagnosticEngine()
    result = engine.run_diagnostic(
        claimed_grade=1,
        answers=[
            {
                "question_id": "g1-q1",
                "grade": 1,
                "user_answer": "0",
                "is_correct": False,
            },
            {
                "question_id": "g1-q2",
                "grade": 1,
                "user_answer": "1",
                "is_correct": False,
            },
        ],
    )

    weak_topic = engine.select_weak_topic(result)

    assert weak_topic is not None
    assert weak_topic["grade"] == 1
    assert weak_topic["topic_id"].startswith("g1_t")
    assert weak_topic["source_question_id"].startswith("g1_t")
    assert isinstance(weak_topic["topic"], str) and weak_topic["topic"]
