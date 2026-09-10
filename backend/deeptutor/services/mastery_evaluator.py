from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MasteryDecision:
    skill_id: str | None
    decision: str
    confidence: float
    reasons: list[str]
    failed_criteria: list[str]
    evidence: dict[str, Any]


class MasteryEvaluator:
    """Deterministic backend-owned mastery evaluator.

    The evaluator is intentionally small and rule-based. It reads skill contract
    metadata and the per-skill evidence accumulated in state, then returns one
    of the finite decisions:

    - mastered
    - not_mastered
    - needs_remediation
    - insufficient_evidence
    """

    def evaluate(
        self,
        *,
        skill_id: str | None,
        contract: dict[str, Any],
        mastery_state: dict[str, Any],
    ) -> MasteryDecision:
        if not skill_id:
            return self._decision(
                skill_id=None,
                decision="insufficient_evidence",
                confidence=0.0,
                reasons=["missing_skill_id"],
                failed_criteria=["missing_skill_id"],
                evidence={"history_length": 0},
            )

        if not contract:
            return self._decision(
                skill_id=skill_id,
                decision="insufficient_evidence",
                confidence=0.0,
                reasons=["missing_contract"],
                failed_criteria=["missing_contract"],
                evidence={"history_length": len(list(mastery_state.get("attempt_history") or []))},
            )

        validation = contract.get("validation") or {}
        gate = dict(contract.get("mastery_gate") or {})
        if not validation.get("mastery_owned_by_backend") or not gate:
            return self._decision(
                skill_id=skill_id,
                decision="insufficient_evidence",
                confidence=0.0,
                reasons=["contract_not_mastery_owned", "missing_mastery_gate"],
                failed_criteria=["contract_not_mastery_owned", "missing_mastery_gate"],
                evidence={"history_length": len(list(mastery_state.get("attempt_history") or []))},
            )

        history = list(mastery_state.get("attempt_history") or [])
        window = max(1, int(gate.get("window") or 5))
        required_correct = max(1, int(gate.get("correct") or 4))
        if len(history) < window:
            return self._decision(
                skill_id=skill_id,
                decision="insufficient_evidence",
                confidence=0.0,
                reasons=["not_enough_attempts"],
                failed_criteria=["min_window_not_reached"],
                evidence={"history_length": len(history), "required_window": window},
            )

        window_history = history[-window:]
        correct_count = sum(1 for attempt in window_history if bool(attempt.get("is_correct")))
        wrong_count = len(window_history) - correct_count
        consecutive_correct = self._consecutive_correct(history)

        evidence = {
            "history_length": len(history),
            "window": window,
            "required_correct": required_correct,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "consecutive_correct": consecutive_correct,
            "gate_type": gate.get("type") or "accuracy_over_n",
        }

        gate_type = str(gate.get("type") or "accuracy_over_n").strip().lower()
        if gate_type == "streak":
            if consecutive_correct >= required_correct:
                return self._decision(
                    skill_id=skill_id,
                    decision="mastered",
                    confidence=self._confidence(correct_count, window),
                    reasons=["correct_streak_met", "required_window_met"],
                    failed_criteria=[],
                    evidence=evidence,
                )
            if wrong_count >= max(2, window - required_correct + 1):
                return self._decision(
                    skill_id=skill_id,
                    decision="needs_remediation",
                    confidence=self._confidence(correct_count, window),
                    reasons=["streak_not_met", "too_many_recent_errors"],
                    failed_criteria=["correct_streak"],
                    evidence=evidence,
                )
            return self._decision(
                skill_id=skill_id,
                decision="not_mastered",
                confidence=self._confidence(correct_count, window),
                reasons=["streak_not_met"],
                failed_criteria=["correct_streak"],
                evidence=evidence,
            )

        # Default: accuracy_over_n
        if correct_count >= required_correct:
            return self._decision(
                skill_id=skill_id,
                decision="mastered",
                confidence=self._confidence(correct_count, window),
                reasons=["correct_threshold_met", "required_window_met"],
                failed_criteria=[],
                evidence=evidence,
            )
        if wrong_count >= 2:
            return self._decision(
                skill_id=skill_id,
                decision="needs_remediation",
                confidence=self._confidence(correct_count, window),
                reasons=["accuracy_threshold_not_met", "too_many_recent_errors"],
                failed_criteria=["correct_over_window"],
                evidence=evidence,
            )
        return self._decision(
            skill_id=skill_id,
            decision="not_mastered",
            confidence=self._confidence(correct_count, window),
            reasons=["accuracy_threshold_not_met"],
            failed_criteria=["correct_over_window"],
            evidence=evidence,
        )

    @staticmethod
    def _consecutive_correct(history: list[dict[str, Any]]) -> int:
        streak = 0
        for attempt in reversed(history):
            if bool(attempt.get("is_correct")):
                streak += 1
            else:
                break
        return streak

    @staticmethod
    def _confidence(correct_count: int, window: int) -> float:
        if window <= 0:
            return 0.0
        return round(min(1.0, max(0.0, correct_count / window)), 3)

    @staticmethod
    def _decision(
        *,
        skill_id: str | None,
        decision: str,
        confidence: float,
        reasons: list[str],
        failed_criteria: list[str],
        evidence: dict[str, Any],
    ) -> MasteryDecision:
        return MasteryDecision(
            skill_id=skill_id,
            decision=decision,
            confidence=confidence,
            reasons=reasons,
            failed_criteria=failed_criteria,
            evidence=evidence,
        )


mastery_evaluator = MasteryEvaluator()
