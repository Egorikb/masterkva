"""Render the versioned Grade 1 corpus as a readable teacher guide."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    corpus = json.loads((ROOT / "backend/data/lessons/grade_1_ru_adapted.json").read_text())
    lines = [
        "# 1 класс — пособие преподавателя", "",
        f"Версия {corpus['reference_version']}. Создано из учебного JSON командой "
        "`python3 backend/scripts/export_grade1_guide.py`. Править исходный JSON, затем повторить экспорт.", "",
        "26 тем, 26 разобранных примеров, 78 самостоятельных заданий. "
        "Это образец содержания, а не полный годовой учебник. "
        "Привязки первого полугодия проверены по разделам китайского оригинала; "
        "для второго полугодия проверка оригинала остаётся открытой.", "",
        "Материал для взрослого: ответы и решения нельзя целиком передавать ребёнку. "
        "Сначала разбирается пример, затем задания выдаются по одному. "
        "При нескольких вопросах ответы проверяются по порядку. "
        "Для рисунков, действий и объяснений нужна проверка по критериям. "
        "Один правильный ответ не подтверждает освоение всей темы.", "",
    ]
    for semester in (1, 2):
        lines += [f"## Полугодие {semester}", ""]
        for topic in corpus[f"semester_{semester}"]["topics"]:
            teaching = topic["teaching"]
            source = topic["source"]
            reference = (
                f"Китайский оригинал: {source['unit']}, печатные страницы {source['printed_pages']}. "
                "Подтверждён раздел-основа, задания являются авторской адаптацией."
                if source["verification"] == "unit_verified" else
                "Источник второго полугодия не подтверждён: авторская адаптация унаследованной темы."
            )
            lines += [f"### {topic['id']}. {topic['title']}", "", reference, "",
                      f"**Цель:** {teaching['goal']}", "",
                      "**Предварительные темы:** " + (", ".join(map(str, teaching["prerequisite_topic_ids"])) or "нет") + ".", "",
                      f"**Типичная ошибка:** {teaching['common_mistake']}", "",
                      "**Разобранный пример**", "", teaching["worked_example"]["prompt"], ""]
            lines += [f"{i}. {step}" for i, step in enumerate(teaching["worked_example"]["solution_steps"], 1)] + [""]
            for lesson in topic["lessons"]:
                lines += [f"#### {lesson['lesson_id']}", "", lesson["student_prompt"], ""]
                if lesson.get("materials"):
                    lines += ["Материалы: " + ", ".join(lesson["materials"]) + ".", ""]
                lines += [f"Подсказка: {lesson['hint']}", "", "<details>", "<summary>Проверка и методическая заметка</summary>", ""]
                assessment = lesson["assessment"]
                if assessment["kind"] == "rubric":
                    lines += ["Требует проверки взрослым:", ""]
                    lines += [f"- {criterion}" for criterion in assessment["criteria"]]
                else:
                    lines += ["Ответы по порядку: " + "; ".join(lesson["expected_answers"]) + "."]
                lines += ["", "Ход решения:", ""]
                lines += [f"{i}. {step}" for i, step in enumerate(lesson["solution_steps"], 1)]
                lines += ["", lesson["teacher_note"], "", "</details>", ""]
    target = ROOT / "docs/grade1/TEACHER_GUIDE.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"Grade 1 teacher guide: {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
