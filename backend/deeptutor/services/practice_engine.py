from __future__ import annotations

import random
import re
from dataclasses import dataclass

# Static practice templates for topics that need specific wording
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
    "g2_t01": [
        {"question": "12 + 5 = ?", "answer": "17", "item_family": "addition_carry"},
        {"question": "14 + 3 = ?", "answer": "17", "item_family": "addition_carry"},
    ],
    "g2_t02": [
        {"question": "15 - 7 = ?", "answer": "8", "item_family": "subtraction_within_10_part_whole"},
        {"question": "13 - 6 = ?", "answer": "7", "item_family": "subtraction_within_10_part_whole"},
    ],
    "g3_t01": [
        {"question": "Сколько минут в 2 часах?", "answer": "120", "item_family": "time_unit_conversion"},
        {"question": "Сколько минут в 3 часах?", "answer": "180", "item_family": "time_unit_conversion"},
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
    "g2_t02": "subtraction_within_10_part_whole",
    "g3_t01": "time_unit_conversion",
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


def _generate_addition_within_20(variant: int) -> dict[str, str]:
    """Generate addition problems that cross 10 (the core 'переход через 10' pattern).
    First number is 6-9, second number is chosen so sum > 10."""
    rng = random.Random(variant * 31 + 17)
    a = rng.randint(6, 9)
    b = rng.randint(1, 9)
    while a + b <= 10:
        b = rng.randint(1, 9)
    answer = a + b
    return {
        "question": f"{a} + {b} = ?",
        "answer": str(answer),
        "item_family": "addition_within_10_part_whole",
    }


def _generate_addition_no_carry(variant: int) -> dict[str, str]:
    """Generate simple addition within 10 (no carry)."""
    rng = random.Random(variant * 31 + 17)
    a = rng.randint(1, 8)
    b = rng.randint(1, 9 - a)
    answer = a + b
    return {
        "question": f"{a} + {b} = ?",
        "answer": str(answer),
        "item_family": "addition_within_10_part_whole",
    }


def _generate_subtraction(variant: int) -> dict[str, str]:
    """Generate subtraction within 10."""
    rng = random.Random(variant * 31 + 17)
    a = rng.randint(3, 10)
    b = rng.randint(1, a - 1)
    answer = a - b
    return {
        "question": f"{a} - {b} = ?",
        "answer": str(answer),
        "item_family": "subtraction_within_10_part_whole",
    }


def _generate_successor(variant: int) -> dict[str, str]:
    """Generate 'what number comes after X' problems."""
    rng = random.Random(variant * 31 + 17)
    a = rng.randint(1, 10)
    return {
        "question": f"Какое число идёт после {a}?",
        "answer": str(a + 1),
        "item_family": "number_successor",
    }


def _generate_counting(variant: int) -> dict[str, str]:
    """Generate counting/part-whole problems."""
    rng = random.Random(variant * 31 + 17)
    a = rng.randint(1, 5)
    b = rng.randint(1, 5)
    answer = a + b
    return {
        "question": f"Сколько всего: {a} и {b}?",
        "answer": str(answer),
        "item_family": "counting_with_objects",
    }


def _generate_number_bond(variant: int) -> dict[str, str]:
    """Generate number bond / missing part problems."""
    rng = random.Random(variant * 31 + 17)
    whole = rng.randint(3, 8)
    part1 = rng.randint(1, whole - 1)
    part2 = whole - part1
    templates = [
        {"question": f"{part1} + ? = {whole}", "answer": str(part2)},
        {"question": f"? + {part1} = {whole}", "answer": str(part2)},
        {"question": f"{part1} + {part2} = ?", "answer": str(whole)},
    ]
    t = templates[rng.randint(0, len(templates) - 1)]
    t["item_family"] = "number_bond_missing_part"
    return t


def _generate_time_conversion(variant: int) -> dict[str, str]:
    """Generate time unit conversion problems."""
    rng = random.Random(variant * 31 + 17)
    hours = rng.randint(1, 5)
    templates = [
        {"question": f"Сколько минут в {hours} часах?", "answer": str(hours * 60)},
        {"question": f"Сколько минут в {hours + 5} часах?", "answer": str((hours + 5) * 60)},
    ]
    t = templates[rng.randint(0, len(templates) - 1)]
    t["item_family"] = "time_unit_conversion"
    return t


GENERATORS = {
    "addition_within_10_part_whole": _generate_addition_within_20,
    "subtraction_within_10_part_whole": _generate_subtraction,
    "number_successor": _generate_successor,
    "counting_with_objects": _generate_counting,
    "number_bond_missing_part": _generate_number_bond,
    "compose_decompose_10": _generate_addition_no_carry,
    "time_unit_conversion": _generate_time_conversion,
}


@dataclass(slots=True)
class PracticeEngine:
    def create_practice(self, weak_topic: dict, variant: int = 0) -> dict:
        topic_id = str(weak_topic.get("topic_id") or "unknown_topic")
        title = weak_topic.get("topic") or "Тема"

        # Try static templates first
        templates = PRACTICE_BY_TOPIC.get(topic_id)
        if templates:
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

        # Fall back to algorithmic generation
        item_family = str(weak_topic.get("item_family") or ITEM_FAMILY_BY_TOPIC.get(topic_id) or "").strip() or "addition_within_10_part_whole"
        generator = GENERATORS.get(item_family, _generate_addition_within_20)

        # Use variant to pick generator for variety
        family_generators = list(GENERATORS.keys())
        gen_idx = variant % max(len(family_generators), 1)
        for _ in range(gen_idx):
            generator = GENERATORS.get(family_generators[gen_idx % len(family_generators)], generator)
            break

        generated = generator(variant)

        return {
            "id": f"{topic_id}_g{variant + 1:02d}",
            "topic_id": topic_id,
            "title": title,
            "question": generated["question"],
            "answer": generated["answer"],
            "item_family": generated.get("item_family", item_family),
            "attempts": 0,
            "generated": True,
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
