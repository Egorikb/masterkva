"""Normalize and annotate Russian adapted lessons for grades 1-9.

This is intentionally a small, deterministic migration: it removes teacher-only
boilerplate from child-facing text and carries source-topic metadata into each
lesson so the content can be audited without guessing its origin.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

LEAKS = (
    " Пусть ученик пройдёт путь от простого к сложному и сам назовёт, что меняется.",
    " Дай несколько однотипных примеров подряд, чтобы закрепить навык.",
    " Повтори главный приём темы, разложи решение на шаги и после каждого шага сверяйся с условием.",
    " Сначала объясни ход рассуждений своими словами, затем приведи пример из школьной жизни и сделай вывод.",
    " Сначала перебери варианты или разложи их по группам, затем сделай вывод без лишних предположений.",
    " Сначала разбей число на разряды или равные группы, затем вычисли и проверь ответ прикидкой.",
    " Сначала соотнеси время с уроком, переменой, тренировкой или календарём, затем переведи всё в нужные единицы.",
)


def main() -> None:
    for grade in range(1, 10):
        curriculum = json.loads(
            (DATA / "curriculum" / f"grade_{grade}_full.json").read_text()
        )
        topics = {topic["id"]: topic for topic in curriculum["topics"]}
        adapted_path = DATA / "lessons" / f"grade_{grade}_ru_adapted.json"
        adapted = json.loads(adapted_path.read_text())

        for semester_key in ("semester_1", "semester_2"):
            semester = int(semester_key.rsplit("_", 1)[1])
            for topic in adapted[semester_key]["topics"]:
                source = topics[topic["id"]]
                for lesson_index, lesson in enumerate(topic["lessons"], 1):
                    removed = []
                    for field in ("task", "student_prompt"):
                        text = lesson[field]
                        for leak in LEAKS:
                            if leak in text:
                                text = text.replace(leak, "")
                                removed.append(leak.strip())
                        lesson[field] = " ".join(text.split())

                    if removed:
                        note = lesson.get("teacher_note", "")
                        addition = " Дай ребёнку объяснить способ решения и проверить ответ."
                        if addition.strip() not in note:
                            lesson["teacher_note"] = (note.rstrip() + addition).strip()

                    lesson["source_topic_id"] = topic["id"]
                    lesson["source_pages"] = source.get("pages", "")
                    lesson["semester"] = semester
                    lesson["lesson_index"] = lesson_index
                    lesson["skills"] = source.get("skills", [])

        adapted_path.write_text(
            json.dumps(adapted, ensure_ascii=False, indent=2) + "\n"
        )


if __name__ == "__main__":
    main()
