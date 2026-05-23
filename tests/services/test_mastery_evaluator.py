from __future__ import annotations

from deeptutor.services.mastery_evaluator import mastery_evaluator
from deeptutor.services.skill_runtime import skill_resolver


def test_mastery_evaluator_requires_window_for_g2_addition_core() -> None:
    resolution = skill_resolver.resolve(topic_id="g2_t01", topic_name="Сложение двузначных чисел")
    state = {
        "attempt_history": [
            {"is_correct": True, "confidence": 1.0},
            {"is_correct": True, "confidence": 1.0},
            {"is_correct": True, "confidence": 1.0},
        ]
    }

    decision = mastery_evaluator.evaluate(
        skill_id=resolution.skill_id,
        contract=resolution.contract,
        mastery_state=state,
    )

    assert decision.decision == "insufficient_evidence"
    assert decision.evidence["history_length"] == 3
    assert decision.evidence["required_window"] == 5


def test_mastery_evaluator_marks_g2_addition_core_mastered_on_full_window() -> None:
    resolution = skill_resolver.resolve(topic_id="g2_t01", topic_name="Сложение двузначных чисел")
    state = {
        "attempt_history": [
            {"is_correct": True, "confidence": 1.0},
            {"is_correct": True, "confidence": 1.0},
            {"is_correct": True, "confidence": 1.0},
            {"is_correct": True, "confidence": 1.0},
            {"is_correct": True, "confidence": 1.0},
        ]
    }

    decision = mastery_evaluator.evaluate(
        skill_id=resolution.skill_id,
        contract=resolution.contract,
        mastery_state=state,
    )

    assert decision.decision == "mastered"
    assert decision.confidence == 1.0
    assert "correct_threshold_met" in decision.reasons


def test_mastery_evaluator_routes_recent_errors_to_remediation() -> None:
    resolution = skill_resolver.resolve(topic_id="g2_t01", topic_name="Сложение двузначных чисел")
    state = {
        "attempt_history": [
            {"is_correct": True, "confidence": 1.0},
            {"is_correct": False, "confidence": 0.0},
            {"is_correct": False, "confidence": 0.0},
            {"is_correct": True, "confidence": 1.0},
            {"is_correct": True, "confidence": 1.0},
        ]
    }

    decision = mastery_evaluator.evaluate(
        skill_id=resolution.skill_id,
        contract=resolution.contract,
        mastery_state=state,
    )

    assert decision.decision == "needs_remediation"
    assert "too_many_recent_errors" in decision.reasons
