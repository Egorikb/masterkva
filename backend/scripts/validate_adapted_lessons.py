"""Small quality gate for grades 1-9 adapted lesson data."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LEAK_MARKERS = (
    "Пусть ученик",
    "Дай несколько однотипных примеров",
    "Повтори главный приём темы",
    "Сначала разбей число на разряды",
    "Сначала объясни ход рассуждений",
    "Сначала перебери варианты",
    "Попроси решить 2–3 очень похожих",
    "Попроси сначала назвать",
    "Сначала найди общий признак",
    "Сначала сравни вслух",
    "Сначала покажи самый простой",
    "Сначала покажи базовый вариант",
    "Сначала покажи короткий приём",
    "Сначала покажи приём на одном",
    "Сначала отработай один образец",
    "Начни с простого случая",
    "Сначала реши быстро",
    "Сначала выбери самый удобный",
)


def validate_grade(grade: int) -> list[str]:
    errors: list[str] = []
    curriculum = json.loads(
        (DATA / "curriculum" / f"grade_{grade}_full.json").read_text()
    )
    adapted = json.loads(
        (DATA / "lessons" / f"grade_{grade}_ru_adapted.json").read_text()
    )
    source_topics = {topic["id"]: topic for topic in curriculum["topics"]}
    seen: set[int] = set()

    for semester_key in ("semester_1", "semester_2"):
        for topic in adapted.get(semester_key, {}).get("topics", []):
            topic_id = topic.get("id")
            seen.add(topic_id)
            if topic_id not in source_topics:
                errors.append(f"grade {grade}: unknown topic {topic_id}")
            for index, lesson in enumerate(topic.get("lessons", []), 1):
                location = f"grade {grade}, topic {topic_id}, lesson {index}"
                for field in ("task", "student_prompt"):
                    text = lesson.get(field, "")
                    if not text:
                        errors.append(f"{location}: missing {field}")
                    if any(marker in text for marker in LEAK_MARKERS):
                        errors.append(f"{location}: teacher text leaked into {field}")
                if lesson.get("source_topic_id") != topic_id:
                    errors.append(f"{location}: source_topic_id mismatch")
                if lesson.get("skills") != source_topics.get(topic_id, {}).get("skills", []):
                    errors.append(f"{location}: skills do not match source topic")
                if grade <= 3:
                    if "answer" in lesson or "answers" in lesson:
                        errors.append(f"{location}: non-canonical answer field")
                    if lesson.get("answer_mode") not in {"exact", "open"}:
                        errors.append(f"{location}: invalid answer_mode")
                    if "teacher_note" not in lesson:
                        errors.append(f"{location}: missing teacher_note")

    missing = set(source_topics) - seen
    errors.extend(f"grade {grade}: missing topic {topic_id}" for topic_id in sorted(missing))
    return errors


def main() -> int:
    errors = [error for grade in range(1, 10) for error in validate_grade(grade)]
    if errors:
        print("\n".join(errors))
        return 1
    print("grades 1-9 adapted lessons: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
