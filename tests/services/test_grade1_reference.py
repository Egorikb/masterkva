from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.validate_grade1_reference import validate_reference


ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def reference_data(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    lessons = json.loads((ROOT / "backend/data/lessons/grade_1_ru_adapted.json").read_text(encoding="utf-8"))
    curriculum = json.loads((ROOT / "backend/data/curriculum/grade_1_full.json").read_text(encoding="utf-8"))
    mappings = {
        str(topic["id"]): {
            "book_id": "upper" if topic["semester"] == 1 else "lower",
            "printed_pages": str(topic.get("pages") or "") if topic["semester"] == 1 else "",
            "verification": "unit_verified" if topic["semester"] == 1 else "unverified",
        }
        for topic in curriculum["topics"]
    }
    manifest = {
        "books": {
            "upper": {"id": "upper", "local_path": "sources/upper.pdf", "sha256": "0" * 64, "verification": "local_verified", "pdf_pages": 118, "printed_to_pdf_1based_offset": 5},
            "lower": {"id": "lower", "local_path": None, "verification": "missing"},
        },
        "topic_mapping": mappings,
    }
    for semester in ("semester_1", "semester_2"):
        for topic in lessons[semester]["topics"]:
            topic["source"] = mappings[str(topic["id"])]
            for lesson in topic["lessons"]:
                lesson["source"] = {**mappings[str(topic["id"])], "kind": "authored_adaptation"}
    for topic in curriculum["topics"]:
        mapping = mappings[str(topic["id"])]
        topic["pages"] = mapping["printed_pages"]
        topic["source_status"] = mapping["verification"]
    _write(data / "lessons/grade_1_ru_adapted.json", lessons)
    _write(data / "curriculum/grade_1_full.json", curriculum)
    _write(data / "curriculum/grade_1_sources.json", manifest)
    return data


def _payload(data: Path) -> dict:
    return json.loads((data / "lessons/grade_1_ru_adapted.json").read_text(encoding="utf-8"))


def _first_lesson(payload: dict) -> dict:
    return payload["semester_1"]["topics"][0]["lessons"][0]


def test_current_reference_passes_structural_and_arithmetic_gate(reference_data: Path) -> None:
    assert validate_reference(reference_data) == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda lesson: lesson.update(lesson_id="g1-t01-l02"), "duplicate lesson_id"),
        (lambda lesson: lesson.update(student_prompt="устаревший текст"), "joined presentation prompts"),
        (lambda lesson: lesson.pop("source"), "source does not exactly match"),
    ],
)
def test_gate_catches_identity_prompt_and_source_drift(reference_data: Path, mutation, message: str) -> None:
    payload = _payload(reference_data)
    mutation(_first_lesson(payload))
    _write(reference_data / "lessons/grade_1_ru_adapted.json", payload)
    assert any(message in error for error in validate_reference(reference_data))


def test_gate_catches_wrong_arithmetic(reference_data: Path) -> None:
    payload = _payload(reference_data)
    lesson = payload["semester_1"]["topics"][2]["lessons"][1]
    lesson["assessment"]["parts"][0]["expected"][0] = "5"
    lesson["expected_answers"][0] = "5"
    _write(reference_data / "lessons/grade_1_ru_adapted.json", payload)
    assert any("arithmetic mismatch" in error for error in validate_reference(reference_data))


def test_gate_catches_assessment_prompt_and_mode_drift(reference_data: Path) -> None:
    payload = _payload(reference_data)
    exact_lesson = payload["semester_1"]["topics"][0]["lessons"][1]
    exact_lesson["assessment"]["parts"][0]["prompt"] = "Другой вопрос"
    exact_lesson["answer_mode"] = "open"
    rubric_lesson = _first_lesson(payload)
    rubric_lesson["acceptance_criteria"] = ["Другая рубрика"]
    _write(reference_data / "lessons/grade_1_ru_adapted.json", payload)
    errors = validate_reference(reference_data)
    assert any("part prompts" in error for error in errors)
    assert any("answer_mode" in error for error in errors)
    assert any("rubric acceptance_criteria" in error for error in errors)


def test_gate_rejects_verified_claim_against_missing_book_and_bad_ranges(reference_data: Path) -> None:
    manifest_path = reference_data / "curriculum/grade_1_sources.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["topic_mapping"]["1"].update(book_id="lower", printed_pages="120-119")
    _write(manifest_path, manifest)
    assert any("unit_verified requires a local_verified book" in error for error in validate_reference(reference_data))

    manifest["topic_mapping"]["1"].update(book_id="upper", printed_pages="120-121")
    _write(manifest_path, manifest)
    errors = validate_reference(reference_data)
    assert any("exceed local book bounds" in error for error in errors)


def test_ordered_needs_multiple_parts_but_comparison_prompt_need_not_parse(reference_data: Path) -> None:
    payload = _payload(reference_data)
    lesson = payload["semester_1"]["topics"][0]["lessons"][1]
    lesson["assessment"] = {
        "kind": "ordered",
        "parts": [{"prompt": "Что больше: 5 или 3?", "expected": ["5"]}],
    }
    lesson["expected_answers"] = ["5"]
    _write(reference_data / "lessons/grade_1_ru_adapted.json", payload)
    errors = validate_reference(reference_data)
    assert any("ordered assessment requires more than one part" in error for error in errors)
    assert not any("bad arithmetic" in error for error in errors)


def test_optional_source_verification_checks_hash(reference_data: Path) -> None:
    source = reference_data / "sources/upper.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"reference")
    manifest_path = reference_data / "curriculum/grade_1_sources.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["books"]["upper"]["sha256"] = hashlib.sha256(b"reference").hexdigest()
    _write(manifest_path, manifest)
    assert validate_reference(reference_data, verify_sources=True) == []
    source.write_bytes(b"changed")
    assert any("sha256 mismatch" in error for error in validate_reference(reference_data, verify_sources=True))


def test_mechanical_migrations_skip_versioned_grade_one(tmp_path: Path, monkeypatch) -> None:
    from scripts import complete_primary_lessons, enrich_adapted_lessons

    data = tmp_path / "data"
    original = ROOT / "backend/data/lessons/grade_1_ru_adapted.json"
    target = data / "lessons/grade_1_ru_adapted.json"
    target.parent.mkdir(parents=True)
    shutil.copyfile(original, target)
    before = target.read_bytes()

    for grade in range(2, 10):
        _write(data / f"curriculum/grade_{grade}_full.json", {"topics": []})
        _write(data / f"lessons/grade_{grade}_ru_adapted.json", {"reference_version": "test"})
    _write(data / "curriculum/grade_1_full.json", {"topics": []})

    monkeypatch.setattr(complete_primary_lessons, "DATA", data)
    complete_primary_lessons.main()
    assert target.read_bytes() == before

    monkeypatch.setattr(enrich_adapted_lessons, "DATA", data)
    enrich_adapted_lessons.main()
    assert target.read_bytes() == before
