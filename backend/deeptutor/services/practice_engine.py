from __future__ import annotations

import re
from dataclasses import dataclass

PRACTICE_BY_TOPIC: dict[str, list[dict[str, str]]] = {
    "g1_t01": [
        {"question": "Сколько всего: 3 и 2?", "answer": "5", "item_family": "counting_with_objects"},
        {"question": "Сколько всего: 4 и 1?", "answer": "5", "item_family": "counting_with_objects"},
    ],
    "g1_t02": [
        {"question": "Какое число идёт после 6?", "answer": "7", "item_family": "number_successor"},
        {"question": "Какое число идёт после 8?", "answer": "9", "item_family": "number_successor"},
    ],
    "g1_t03": [
        {"question": "4 + 3 = ?", "answer": "7", "item_family": "addition_within_10_part_whole"},
        {"question": "2 + 5 = ?", "answer": "7", "item_family": "addition_within_10_part_whole"},
    ],
    "g1_t04": [
        {"question": "7 - 4 = ?", "answer": "3", "item_family": "subtraction_within_10_part_whole"},
        {"question": "8 - 5 = ?", "answer": "3", "item_family": "subtraction_within_10_part_whole"},
    ],
    "g1_t05": [
        {"question": "2 + 1 = ?", "answer": "3", "item_family": "number_bond_missing_part"},
        {"question": "1 + 2 = ?", "answer": "3", "item_family": "number_bond_missing_part"},
    ],
    "g1_t06": [
        {"question": "20 + 30 = ?", "answer": "50", "item_family": "compose_decompose_10"},
        {"question": "40 + 10 = ?", "answer": "50", "item_family": "compose_decompose_10"},
    ],
    "g1_t07": [
        {"question": "8 + 5 = ?", "answer": "13", "item_family": "addition_within_10_part_whole"},
        {"question": "9 + 3 = ?", "answer": "12", "item_family": "addition_within_10_part_whole"},
    ],
    "g2_t01": [
        {"question": "12 + 5 = ?", "answer": "17", "item_family": "addition_carry"},
        {"question": "14 + 3 = ?", "answer": "17", "item_family": "addition_carry"},
    ],
}

ITEM_FAMILY_BY_TOPIC = {
    "g1_t01": "counting_with_objects",
    "g1_t02": "number_successor",
    "g1_t03": "addition_within_10_part_whole",
    "g1_t04": "subtraction_within_10_part_whole",
    "g1_t05": "number_bond_missing_part",
    "g1_t06": "compose_decompose_10",
    "g1_t07": "addition_within_10_part_whole",
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
    def create_practice(self, weak_topic: dict, variant: int = 0) -> dict:
        topic_id = str(weak_topic.get("topic_id") or "unknown_topic")
        title = weak_topic.get("topic") or "Тема"
        templates = PRACTICE_BY_TOPIC.get(topic_id) or [
            {"question": f"Реши короткое задание по теме: {title}", "answer": "1"},
        ]
        template = templates[variant % len(templates)]
        item_family = str(template.get("item_family") or weak_topic.get("item_family") or ITEM_FAMILY_BY_TOPIC.get(topic_id) or "").strip() or None
        return {
            "id": f"{topic_id}_p{variant + 1:02d}",
            "topic_id": topic_id,
            "title": title,
            "question": template["question"],
            "answer": template["answer"],
            "item_family": item_family,
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
            "item_family": practice.get("item_family"),
            "attempts": practice["attempts"],
        }
