from __future__ import annotations

import json
from pathlib import Path

import pytest

import deeptutor.services.curricular_lesson_runtime as runtime_module
from deeptutor.services.curricular_lesson_runtime import (
    CurriculumResolutionError,
    CurricularLessonRuntime,
)


SOURCE_BY_ATTR = {
    "LESSONS_FILE": runtime_module.LESSONS_FILE,
    "RUNTIME_MAP_FILE": runtime_module.RUNTIME_MAP_FILE,
    "DIAGNOSTIC_POOL_FILE": runtime_module.DIAGNOSTIC_POOL_FILE,
    "SKILL_REGISTRY_FILE": runtime_module.SKILL_REGISTRY_FILE,
    "SKILL_CONTRACTS_FILE": runtime_module.SKILL_CONTRACTS_FILE,
}


def _runtime_with_copied_sources(tmp_path: Path, monkeypatch) -> CurricularLessonRuntime:
    for attr, source in SOURCE_BY_ATTR.items():
        target = tmp_path / source.name
        target.write_bytes(source.read_bytes())
        monkeypatch.setattr(runtime_module, attr, target)
    return CurricularLessonRuntime()


def _json_for(attr: str) -> dict:
    return json.loads(getattr(runtime_module, attr).read_text(encoding="utf-8"))


def _replace_json(attr: str, value: dict) -> None:
    getattr(runtime_module, attr).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _assert_code(exc: pytest.ExceptionInfo[CurriculumResolutionError], code: str) -> None:
    assert exc.value.code == code


def test_resolves_only_the_reviewed_pilot_pair(tmp_path: Path, monkeypatch) -> None:
    resolved = _runtime_with_copied_sources(tmp_path, monkeypatch).resolve("g1-t12-l01", "2.0")
    assert resolved.lesson_id == "g1-t12-l01"
    assert resolved.content_version == "2.0"
    assert resolved.mapping["status"] == "mapped"


def test_child_part_exposes_prompt_but_no_answer_or_mapping_evidence(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    part = runtime.child_part(runtime.resolve("g1-t12-l01", "2.0"), 0)
    assert part["question"] == "Вычисли 8 + 5."
    assert {"answer", "expected", "expected_answers", "solution_steps", "teacher_note", "hint"}.isdisjoint(part)
    assert {"diagnostic_topic_id", "skill_id", "item_family", "evidence"}.isdisjoint(part)


def test_exact_answer_is_assessed_by_server_contract(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    resolved = runtime.resolve("g1-t12-l01", "2.0")
    assert runtime.assess_part(resolved, 0, "13")["status"] == "correct"
    assert runtime.assess_part(resolved, 0, "12")["status"] == "incorrect"


def test_hint_is_separate_from_assessment(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    resolved = runtime.resolve("g1-t12-l01", "2.0")
    assert runtime.hint(resolved, 0) == "Как разделить 5, чтобы сначала получить 10?"
    assert runtime.assess_part(resolved, 0, "Как разделить 5?")["status"] == "incorrect"


def test_missing_identity_fails_closed(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    with pytest.raises(CurriculumResolutionError) as exc:
        runtime.resolve("", "2.0")
    _assert_code(exc, "lesson_identity_required")


def test_wrong_version_fails_closed(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    with pytest.raises(CurriculumResolutionError) as exc:
        runtime.resolve("g1-t12-l01", "1.0")
    _assert_code(exc, "lesson_not_allowlisted")


def test_unknown_lesson_fails_closed_without_fallback(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    with pytest.raises(CurriculumResolutionError) as exc:
        runtime.resolve("g1-t12-l02", "2.0")
    _assert_code(exc, "lesson_not_allowlisted")


def test_review_required_mapping_fails_closed(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    data = _json_for("RUNTIME_MAP_FILE")
    row = next(item for item in data["mappings"] if item["lesson_id"] == "g1-t12-l01")
    row["status"] = "review_required"
    _replace_json("RUNTIME_MAP_FILE", data)
    with pytest.raises(CurriculumResolutionError) as exc:
        runtime.resolve("g1-t12-l01", "2.0")
    _assert_code(exc, "mapping_not_approved")


def test_unmapped_mapping_fails_closed(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    data = _json_for("RUNTIME_MAP_FILE")
    row = next(item for item in data["mappings"] if item["lesson_id"] == "g1-t12-l01")
    row["status"] = "unmapped"
    _replace_json("RUNTIME_MAP_FILE", data)
    with pytest.raises(CurriculumResolutionError) as exc:
        runtime.resolve("g1-t12-l01", "2.0")
    _assert_code(exc, "mapping_not_approved")


def test_family_only_diagnostic_match_is_rejected(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    data = _json_for("DIAGNOSTIC_POOL_FILE")
    for item in data["questions"]:
        if item.get("topic_id") == "g1_t07" and item.get("item_family") == "addition_within_10_part_whole":
            item["topic_id"] = "g1_t03"
    _replace_json("DIAGNOSTIC_POOL_FILE", data)
    with pytest.raises(CurriculumResolutionError) as exc:
        runtime.resolve("g1-t12-l01", "2.0")
    _assert_code(exc, "diagnostic_binding_missing")


def test_topic_only_diagnostic_match_is_rejected(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    data = _json_for("DIAGNOSTIC_POOL_FILE")
    for item in data["questions"]:
        if item.get("topic_id") == "g1_t07":
            item["item_family"] = "compose_decompose_10"
    _replace_json("DIAGNOSTIC_POOL_FILE", data)
    with pytest.raises(CurriculumResolutionError) as exc:
        runtime.resolve("g1-t12-l01", "2.0")
    _assert_code(exc, "diagnostic_binding_missing")


def test_skill_topic_mismatch_is_rejected(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    data = _json_for("SKILL_REGISTRY_FILE")
    skill = next(item for item in data["skills"] if item["skill_id"] == "g1_compose_decompose_10")
    skill["topic_ids"] = ["g1_t06"]
    _replace_json("SKILL_REGISTRY_FILE", data)
    with pytest.raises(CurriculumResolutionError) as exc:
        runtime.resolve("g1-t12-l01", "2.0")
    _assert_code(exc, "skill_topic_mismatch")


def test_skill_family_mismatch_is_rejected(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    data = _json_for("SKILL_CONTRACTS_FILE")
    contract = next(item for item in data["contracts"] if item["skill_id"] == "g1_compose_decompose_10")
    contract["diagnostic"]["item_families"] = ["compose_decompose_10"]
    _replace_json("SKILL_CONTRACTS_FILE", data)
    with pytest.raises(CurriculumResolutionError) as exc:
        runtime.resolve("g1-t12-l01", "2.0")
    _assert_code(exc, "skill_family_mismatch")


def test_invalid_part_index_never_falls_back(tmp_path: Path, monkeypatch) -> None:
    runtime = _runtime_with_copied_sources(tmp_path, monkeypatch)
    resolved = runtime.resolve("g1-t12-l01", "2.0")
    with pytest.raises(CurriculumResolutionError) as exc:
        runtime.child_part(resolved, 1)
    _assert_code(exc, "part_out_of_range")
