"""
MasterKva — Remediation Engine

Отдельный "лечебный" цикл для работы с ошибками:
  Ошибка → классификация → уточняющее задание (проще) → объяснение → 2-3 аналога → mastery check

Scaffolding (градуированные подсказки):
  1-я ошибка: визуальная подсказка (remediation_visual из item_family)
  2-я ошибка: пошаговый алгоритм (step_by_step)
  3-я ошибка: объяснение + возврат к объяснению темы (escalate to explanation)

State flow:
  PRACTICE --[PRACTICE_WRONG]--> REMEDIATION
  REMEDIATION --[REMEDIATION_CORRECT x2]--> REMEDIATION (next analog)
  REMEDIATION --[REMEDIATION_COMPLETE]--> PRACTICE (return to normal)
  REMEDIATION --[REMEDIATION_ESCALATE]--> EXPLANATION (full re-teach)
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from deeptutor.services.error_taxonomy import (
    REMEDIATION_BY_ITEM_FAMILY,
    ErrorTaxonomy,
    error_taxonomy,
)


# === Scaffolding levels ===
# Each level maps to a specific action type in the remediation flow
SCAFFOLDING_VISUAL = "visual_hint"           # Level 1: show visual hint
SCAFFOLDING_STEP_BY_STEP = "step_by_step"     # Level 2: show algorithm
SCAFFOLDING_ESCALATE = "escalate"             # Level 3: full re-teach

# How many consecutive errors trigger escalation
ESCALATION_THRESHOLD = 3


@dataclass
class RemediationStep:
    """Single step within the remediation flow."""
    step_type: str  # "clarify" | "explain" | "analog" | "mastery_check"
    question: str
    answer: str
    item_family: str
    visual_hint: str | None = None
    step_by_step_hint: str | None = None
    error_code: str | None = None
    is_correct: bool | None = None


@dataclass
class RemediationState:
    """Tracks the full remediation cycle for a single error."""
    original_question: dict[str, Any]
    error_code: str
    error_family: str
    item_family: str
    remediation_path: str
    scaffolding_level: int = 1  # 1=visual, 2=step_by_step, 3=escalate
    steps: list[RemediationStep] = field(default_factory=list)
    current_step_index: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    analogs_total: int = 2  # how many analogous questions to solve
    is_complete: bool = False
    escalate: bool = False

    @property
    def current_step(self) -> RemediationStep | None:
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def needed_analogs(self) -> int:
        """How many more correct analogs needed to complete."""
        return max(0, self.analogs_total - self.correct_count)


class RemediationEngine:
    """Generates and tracks remediation flow."""

    def __init__(self) -> None:
        self._active: dict[str, RemediationState] = {}

    # ---- Public API ----

    def start_remediation(
        self,
        user_id: str,
        original_question: dict[str, Any],
        error_details: dict[str, Any],
    ) -> RemediationState:
        """Start a new remediation cycle after a practice error."""
        error_code = error_details.get("error_code", "procedural_slip")
        error_family = error_details.get("error_family", "procedural_slip")
        item_family = error_details.get("item_family", "")
        remediation_path = error_details.get("remediation_path", "")

        state = RemediationState(
            original_question=original_question,
            error_code=error_code,
            error_family=error_family,
            item_family=item_family,
            remediation_path=remediation_path,
        )

        # Build the remediation sequence
        self._build_steps(state)
        self._active[user_id] = state
        return state

    def get_state(self, user_id: str) -> RemediationState | None:
        return self._active.get(user_id)

    def remove_state(self, user_id: str) -> None:
        self._active.pop(user_id, None)

    def check_answer(
        self,
        user_id: str,
        user_answer: str,
    ) -> tuple[bool, RemediationStep | None, bool, bool]:
        """
        Check answer within remediation flow.

        Returns:
            (is_correct, next_step_or_none, is_complete, should_escalate)
        """
        state = self._active.get(user_id)
        if not state:
            return False, None, True, True

        step = state.current_step
        if not step:
            return False, None, True, True

        # Check correctness
        correct_answer = step.answer
        is_correct = self._check_value(user_answer, correct_answer)
        step.is_correct = is_correct

        if is_correct:
            state.correct_count += 1
        else:
            state.wrong_count += 1

        # Advance to next step
        state.current_step_index += 1

        # Check if remediation is complete (enough correct analogs)
        if state.correct_count >= state.analogs_total:
            state.is_complete = True
            return is_correct, None, True, False

        # Check escalation (too many consecutive errors in remediation)
        if state.wrong_count >= ESCALATION_THRESHOLD:
            state.escalate = True
            return is_correct, None, True, True

        # Get next step
        next_step = state.current_step
        return is_correct, next_step, False, False

    def get_scaffolding_level(self, user_id: str) -> int:
        """Get current scaffolding level (1-3) for the user."""
        state = self._active.get(user_id)
        if not state:
            return 1
        return min(1 + state.wrong_count, 3)

    # ---- Step generation ----

    def _build_steps(self, state: RemediationState) -> None:
        """Build the full remediation sequence."""
        original = state.original_question
        parts = original.get("parts", [])
        item_family = state.item_family

        # Step 1: Clarifying question (simpler version of original)
        clarify = self._make_clarifying_question(original, parts, item_family)
        state.steps.append(RemediationStep(
            step_type="clarify",
            question=clarify["question"],
            answer=str(clarify["answer"]),
            item_family=item_family,
            visual_hint=self._get_visual_hint(item_family),
            error_code=state.error_code,
        ))

        # Step 2: Analogous question 1
        analog1 = self._make_analog(original, parts, item_family, variant=1)
        state.steps.append(RemediationStep(
            step_type="analog",
            question=analog1["question"],
            answer=str(analog1["answer"]),
            item_family=item_family,
            visual_hint=self._get_visual_hint(item_family),
            error_code=state.error_code,
        ))

        # Step 3: Analogous question 2
        analog2 = self._make_analog(original, parts, item_family, variant=2)
        state.steps.append(RemediationStep(
            step_type="analog",
            question=analog2["question"],
            answer=str(analog2["answer"]),
            item_family=item_family,
            visual_hint=self._get_visual_hint(item_family),
            error_code=state.error_code,
        ))

    def _make_clarifying_question(
        self,
        original: dict[str, Any],
        parts: list,
        item_family: str,
    ) -> dict[str, str]:
        """Generate a simpler version of the original question for clarification."""
        num_fam = self._numeric_family(item_family)

        if num_fam == "addition":
            # Simpler addition: smaller numbers, same pattern
            a = random.randint(2, 5)
            b = random.randint(1, 4)
            return {
                "question": f"Сколько будет {a} + {b}?",
                "answer": str(a + b),
            }
        elif num_fam == "subtraction":
            a = random.randint(5, 9)
            b = random.randint(1, a - 1)
            return {
                "question": f"Сколько будет {a} − {b}?",
                "answer": str(a - b),
            }
        elif item_family == "number_successor":
            n = random.randint(3, 8)
            return {"question": f"Какое число идёт после {n}?", "answer": str(n + 1)}
        elif item_family == "counting_with_objects":
            a = random.randint(1, 4)
            b = random.randint(1, 4)
            return {"question": f"Сколько всего: {a} и {b}?", "answer": str(a + b)}
        elif item_family == "time_unit_conversion":
            hours = random.randint(1, 3)
            return {
                "question": f"Сколько минут в {hours} часах?",
                "answer": str(hours * 60),
            }
        else:
            # Generic: use original but with smaller numbers
            if len(parts) >= 2:
                a = max(1, int(parts[0]) // 2) if str(parts[0]).isdigit() else 3
                b = max(1, int(parts[1]) // 2) if str(parts[1]).isdigit() else 2
                return {"question": f"Сколько будет {a} + {b}?", "answer": str(a + b)}
            return {"question": "Сколько будет 2 + 3?", "answer": "5"}

    def _make_analog(
        self,
        original: dict[str, Any],
        parts: list,
        item_family: str,
        variant: int,
    ) -> dict[str, str]:
        """Generate an analogous question (same pattern, different numbers)."""
        rng = random.Random(variant * 17 + hash(item_family) % 1000)
        num_fam = self._numeric_family(item_family)

        if num_fam == "addition":
            # Keep the "cross 10" pattern if original crossed 10
            if len(parts) >= 2:
                try:
                    orig_a, orig_b = int(parts[0]), int(parts[1])
                    crosses_10 = (orig_a + orig_b) > 10
                except (ValueError, TypeError):
                    crosses_10 = True
            else:
                crosses_10 = True

            if crosses_10:
                a = rng.randint(6, 9)
                b = rng.randint(1, 9)
                while a + b <= 10:
                    b = rng.randint(1, 9)
            else:
                a = rng.randint(2, 7)
                b = rng.randint(1, 9 - a)
            return {"question": f"Сколько будет {a} + {b}?", "answer": str(a + b)}

        elif num_fam == "subtraction":
            a = rng.randint(7, 15)
            b = rng.randint(1, min(a - 1, 9))
            return {"question": f"Сколько будет {a} − {b}?", "answer": str(a - b)}

        elif item_family == "number_successor":
            n = rng.randint(2, 15)
            return {"question": f"Какое число идёт после {n}?", "answer": str(n + 1)}

        elif item_family == "counting_with_objects":
            a = rng.randint(1, 5)
            b = rng.randint(1, 5)
            return {"question": f"Сколько всего: {a} и {b}?", "answer": str(a + b)}

        elif item_family == "time_unit_conversion":
            hours = rng.randint(1, 5)
            return {
                "question": f"Сколько минут в {hours} часах?",
                "answer": str(hours * 60),
            }

        else:
            a = rng.randint(2, 8)
            b = rng.randint(1, 9 - a)
            return {"question": f"Сколько будет {a} + {b}?", "answer": str(a + b)}

    def _get_visual_hint(self, item_family: str) -> str | None:
        """Get the visual hint type for this item family."""
        return REMEDIATION_BY_ITEM_FAMILY.get(item_family)

    @staticmethod
    def _numeric_family(item_family: str) -> str:
        """Map item_family to numeric operation family."""
        if not item_family:
            return "other"
        if "addition" in item_family or "compose" in item_family or "carry" in item_family:
            return "addition"
        if "subtraction" in item_family:
            return "subtraction"
        return "other"

    @staticmethod
    def _check_value(user_answer: str, correct_answer: str) -> bool:
        user = str(user_answer).strip().lower()
        correct = str(correct_answer).strip().lower()
        if user == correct:
            return True
        # Extract numbers and compare
        import re
        user_nums = re.findall(r"-?\d+", user)
        correct_nums = re.findall(r"-?\d+", correct)
        if len(user_nums) == 1 and len(correct_nums) == 1:
            return user_nums[0] == correct_nums[0]
        return False


remediation_engine = RemediationEngine()
