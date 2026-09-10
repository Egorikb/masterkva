from __future__ import annotations

import json
from pathlib import Path

from deeptutor.services.lesson_assessment import assess_lesson, validate_assessment


def exact(expected: list[str]) -> dict:
    return {"assessment": {"kind": "exact", "parts": [{"prompt": "Ответ", "expected": expected}]}}


def test_exact_normalises_case_whitespace_and_bare_decimals_only() -> None:
    assert assess_lesson(exact(["4"]), " 4.0 ")["status"] == "correct"
    assert assess_lesson(exact(["4"]), "4,0")["status"] == "correct"
    assert assess_lesson(exact(["+4"]), "4")["status"] == "incorrect"
    assert assess_lesson(exact(["14"]), "1 4")["status"] == "incorrect"
    assert assess_lesson(exact(["4 яблока"]), "4.0 яблока")["status"] == "incorrect"
    assert assess_lesson(exact(["4 яблока"]), "4 яблока")["status"] == "correct"


def test_fraction_is_not_collapsed_into_digits_and_units_are_not_confused() -> None:
    assert assess_lesson(exact(["1/2"]), "12")["status"] == "incorrect"
    assert assess_lesson(exact(["3 см"]), "3 м")["status"] == "incorrect"


def test_full_equation_requires_an_explicit_variant() -> None:
    lesson = {"assessment": {"kind": "exact", "parts": [{"prompt": "8 + 5", "expected": ["13"], "expression": "8+5"}]}}
    assert assess_lesson(lesson, "8 + 5 = 13")["status"] == "incorrect"
    assert assess_lesson(lesson, "13")["status"] == "correct"


def test_ordered_requires_every_part_in_order_and_accepts_semicolon_input() -> None:
    lesson = {"assessment": {"kind": "ordered", "parts": [
        {"prompt": "Первое", "expected": ["2"]},
        {"prompt": "Второе", "expected": ["3"]},
    ]}}
    assert assess_lesson(lesson, ["2", "3"])["status"] == "correct"
    assert assess_lesson(lesson, "2;3")["status"] == "correct"
    assert assess_lesson(lesson, ["3", "2"])["status"] == "incorrect"
    assert assess_lesson(lesson, ["2"])["status"] == "invalid_input"
    assert assess_lesson(exact(["2"]), "2;3")["status"] == "invalid_input"
    assert assess_lesson(lesson, "2,3")["status"] == "invalid_input"


def test_rubric_never_fabricates_a_passing_grade() -> None:
    lesson = {"assessment": {"kind": "rubric", "criteria": ["Названа причина"], "mastery_policy": "do_not_infer_from_one_lesson"}}
    assert assess_lesson(lesson, "placeholder")["status"] == "needs_review"
    assert assess_lesson(lesson, "")["status"] == "invalid_input"
    assert assess_lesson(lesson, 1)["status"] == "invalid_input"


def test_schema_rejects_unsafe_expression_and_missing_rubric_criteria() -> None:
    assert validate_assessment({"kind": "exact", "parts": [{"prompt": "x", "expected": ["1"], "expression": "__import__('os')"}]})
    assert validate_assessment({"kind": "rubric"})


def test_all_grade_one_assessments_validate_and_follow_their_contract() -> None:
    data = json.loads((Path(__file__).resolve().parents[2] / "backend/data/lessons/grade_1_ru_adapted.json").read_text(encoding="utf-8"))
    lessons = [lesson for semester in (data["semester_1"], data["semester_2"]) for topic in semester["topics"] for lesson in topic["lessons"]]

    assert len(lessons) == 78
    for lesson in lessons:
        assessment = lesson["assessment"]
        assert validate_assessment(assessment) == [], lesson["lesson_id"]
        if assessment["kind"] == "rubric":
            assert assess_lesson(lesson, "Мой ответ")["status"] == "needs_review"
        else:
            answers = [part["expected"][0] for part in assessment["parts"]]
            response = answers[0] if assessment["kind"] == "exact" else answers
            assert assess_lesson(lesson, response)["status"] == "correct", lesson["lesson_id"]
