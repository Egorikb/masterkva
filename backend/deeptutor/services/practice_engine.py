from __future__ import annotations

import re
from dataclasses import dataclass

PRACTICE_BY_TOPIC: dict[str, dict[str, str]] = {
    "g1_t01": {"question": "Сколько всего: 3 и 2?", "answer": "5"},
    "g1_t02": {"question": "Какое число идёт после 6?", "answer": "7"},
    "g1_t03": {"question": "4 + 3 = ?", "answer": "7"},
    "g1_t04": {"question": "7 - 4 = ?", "answer": "3"},
    "g2_t01": {"question": "12 + 5 = ?", "answer": "17"},
}


def _single_number(value: str) -> str | None:
    nums = re.findall(r"-?\d+", str(value).strip())
    return nums[0] if len(nums) == 1 else None


def _check_answer(user_answer: str, correct_answer: str) -> tuple[bool, float]:
    user = str(user_answer).strip().lower()
    correct = str(correct_answer).strip().lower()
    if user == correct:
        return True, 1.0

    user_num = _single_number(user)
    correct_num = _single_number(correct)
    if user_num is not None and correct_num is not None:
        is_correct = user_num == correct_num
        return is_correct, 0.95 if is_correct else 0.0

    return False, 0.0


@dataclass(slots=True)
class PracticeEngine:
    def create_practice(self, weak_topic: dict) -> dict:
        topic_id = str(weak_topic.get("topic_id") or "unknown_topic")
        title = weak_topic.get("topic") or "Тема"
        template = PRACTICE_BY_TOPIC.get(
            topic_id,
            {"question": f"Реши короткое задание по теме: {title}", "answer": "1"},
        )
        return {
            "id": f"{topic_id}_p01",
            "topic_id": topic_id,
            "title": title,
            "question": template["question"],
            "answer": template["answer"],
            "attempts": 0,
        }

    def build_practice_item(self, weak_topic: dict) -> dict:
        return self.create_practice(weak_topic)

    def check_practice_answer(self, practice: dict, user_answer: str) -> dict:
        practice["attempts"] = int(practice.get("attempts", 0)) + 1
        is_correct, confidence = _check_answer(user_answer, practice.get("answer", ""))
        return {
            "is_correct": is_correct,
            "confidence": confidence,
            "user_answer": user_answer,
            "correct_answer": str(practice.get("answer", "")),
            "topic_id": practice.get("topic_id"),
            "attempts": practice["attempts"],
        }
