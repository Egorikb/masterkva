from __future__ import annotations

from deeptutor.services.mastery_evaluator import MasteryEvaluator, mastery_evaluator


def test_mastery_evaluator_marks_g2_addition_core_mastered_on_full_window() -> None:
    evaluator = MasteryEvaluator()
    mastery_state = {
        "status": "learning",
        "attempt_history": [
            {"question_id": f"seed-{i}", "is_correct": True, "confidence": 1.0}
            for i in range(5)
        ],
    }
    contract = {
        "mastery_gate": {"type": "streak", "correct": 3, "window": 5},
        "validation": {"mastery_owned_by_backend": True},
    }
    decision = evaluator.evaluate(skill_id="g2_addition_core", contract=contract, mastery_state=mastery_state)
    assert decision.decision == "mastered"


def test_mastery_evaluator_routes_recent_errors_to_remediation() -> None:
    evaluator = MasteryEvaluator()
    mastery_state = {
        "status": "learning",
        "attempt_history": [
            {"question_id": f"seed-{i}", "is_correct": i < 2, "confidence": 1.0}
            for i in range(5)
        ],
    }
    contract = {
        "mastery_gate": {"type": "streak", "correct": 3, "window": 5},
        "validation": {"mastery_owned_by_backend": True},
    }
    decision = evaluator.evaluate(skill_id="g2_addition_core", contract=contract, mastery_state=mastery_state)
    assert decision.decision in ("not_mastered", "needs_remediation", "insufficient_evidence")
