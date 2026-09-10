"""Complete the lesson contract for grades 1-3 without inventing answers."""

from __future__ import annotations

import json
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data"

NOTE_BY_TYPE = {
    "concrete": "Попроси ребёнка сначала выполнить действие с предметами или представить его, затем назвать ответ.",
    "comparison": "Попроси ребёнка назвать, что он сравнивает, и объяснить ответ словами.",
    "practice": "Попроси ребёнка решить самостоятельно, затем коротко объяснить способ проверки.",
    "recognition": "Попроси ребёнка назвать признак и привести один пример из окружающей жизни.",
    "counting": "Попроси ребёнка проговаривать счёт вслух и проверить результат повторным пересчётом.",
    "word_problem": "Попроси ребёнка назвать известные данные, действие и ответ с единицами.",
    "strategy": "Попроси ребёнка сначала объяснить выбранный способ, затем выполнить вычисление и проверить его.",
    "number_composition": "Попроси ребёнка показать состав числа предметами или рисунком, затем записать числа.",
    "place_value": "Попроси ребёнка отделить десятки от единиц и объяснить значение каждой цифры.",
    "time": "Попроси ребёнка опереться на циферблат или ленту времени и проговорить ход рассуждения.",
    "sorting": "Попроси ребёнка назвать признак группировки и проверить, что каждый предмет попал в нужную группу.",
    "pattern": "Попроси ребёнка назвать правило узора и проверить его на следующем элементе.",
    "ten_frame": "Попроси ребёнка показать заполненные и свободные места, затем назвать состав числа.",
    "problem": "Попроси ребёнка назвать данные задачи, действие и полный ответ.",
    "exchange": "Попроси ребёнка показать обмен десятка или рубля предметами, затем записать действие.",
}


def main() -> None:
    for grade in (1, 2, 3):
        path = DATA / "lessons" / f"grade_{grade}_ru_adapted.json"
        data = json.loads(path.read_text())
        if data.get("reference_version"):
            continue
        for semester_key in ("semester_1", "semester_2"):
            for topic in data[semester_key]["topics"]:
                for lesson in topic["lessons"]:
                    # Keep one canonical answer field. The aliases were identical
                    # in the audited corpus and were not consumed by the runtime.
                    if "expected_answers" not in lesson:
                        if "answer" in lesson:
                            lesson["expected_answers"] = [str(lesson.pop("answer"))]
                        elif "answers" in lesson:
                            lesson["expected_answers"] = [str(x) for x in lesson.pop("answers")]
                    lesson.pop("answer", None)
                    lesson.pop("answers", None)
                    lesson["answer_mode"] = (
                        "exact" if "expected_answers" in lesson else "open"
                    )

                    if "teacher_note" not in lesson:
                        lesson["teacher_note"] = NOTE_BY_TYPE.get(
                            lesson.get("type"),
                            "Попроси ребёнка объяснить ход решения и проверить ответ.",
                        )

                    for field in ("task", "student_prompt"):
                        text = lesson[field].rstrip()
                        if text and text[-1] not in ".!?)]»\"":
                            text += "."
                        lesson[field] = text

        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
