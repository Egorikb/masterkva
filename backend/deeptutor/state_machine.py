"""
MasterKva — State Machine Module

Отвечает за переходы между фазами:
  chat → diagnostic → practice → mastery_check → promotion → practice (next skill)

НЕ содержит:
  - API-роутинг (это в plugins_api.py)
  - Вызовы LLM (это в llm_router.py)
  - Формирование HTTP-ответов (это в plugins_api.py)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Phase(str, Enum):
    CHAT = "chat"
    DIAGNOSTIC = "diagnostic"
    EXPLANATION = "explanation"
    PRACTICE = "practice"
    MASTERY_CHECK = "mastery_check"
    REPORT = "report"


class Transition(str, Enum):
    START_DIAGNOSTIC = "start_diagnostic"
    ANSWER_CORRECT = "answer_correct"
    ANSWER_WRONG = "answer_wrong"
    DIAGNOSTIC_COMPLETE = "diagnostic_complete"
    EXPLANATION_DONE = "explanation_done"
    PRACTICE_CORRECT = "practice_correct"
    PRACTICE_WRONG = "practice_wractice"
    MASTERY_ACHIEVED = "mastery_achieved"
    MASTERY_FAILED = "mastery_failed"
    PROMOTE = "promote"


# === State transition table ===
# Maps (current_phase, transition) -> next_phase
TRANSITIONS: dict[tuple[Phase, Transition], Phase] = {
    (Phase.CHAT, Transition.START_DIAGNOSTIC): Phase.DIAGNOSTIC,
    (Phase.DIAGNOSTIC, Transition.ANSWER_CORRECT): Phase.DIAGNOSTIC,
    (Phase.DIAGNOSTIC, Transition.ANSWER_WRONG): Phase.DIAGNOSTIC,
    (Phase.DIAGNOSTIC, Transition.DIAGNOSTIC_COMPLETE): Phase.PRACTICE,
    (Phase.EXPLANATION, Transition.EXPLANATION_DONE): Phase.PRACTICE,
    (Phase.PRACTICE, Transition.PRACTICE_CORRECT): Phase.PRACTICE,
    (Phase.PRACTICE, Transition.PRACTICE_WRONG): Phase.PRACTICE,
    (Phase.PRACTICE, Transition.MASTERY_ACHIEVED): Phase.MASTERY_CHECK,
    (Phase.PRACTICE, Transition.MASTERY_FAILED): Phase.PRACTICE,
    (Phase.MASTERY_CHECK, Transition.PROMOTE): Phase.PRACTICE,
}


@dataclass
class StateTransition:
    user_id: str
    from_phase: Phase
    to_phase: Phase
    transition: Transition
    context: dict[str, Any] = field(default_factory=dict)


class StateMachine:
    """Pure state machine — no I/O, no LLM, no database."""

    @staticmethod
    def next_phase(current: Phase, transition: Transition) -> Phase | None:
        """Get next phase for given transition. Returns None if invalid."""
        return TRANSITIONS.get((current, transition))

    @staticmethod
    def is_valid_transition(current: Phase, transition: Transition) -> bool:
        return (current, transition) in TRANSITIONS

    @staticmethod
    def is_terminal(phase: Phase) -> bool:
        """Check if phase is terminal (no outgoing transitions)."""
        return not any(
            t[0] == phase for t in TRANSITIONS
        )
