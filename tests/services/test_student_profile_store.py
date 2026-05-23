from __future__ import annotations

import json
from pathlib import Path

import pytest

import deeptutor.services.student_profile_store as store


@pytest.fixture()
def state_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    file_path = tmp_path / "user_states.json"
    monkeypatch.setattr(store, "STATE_FILE", file_path)
    return file_path


def test_ensure_student_profile_creates_default_profile(state_file: Path) -> None:
    profile = store.ensure_student_profile("user-1")

    assert profile["profile_schema_version"] == "v1"
    assert profile["user_id"] == "user-1"
    assert profile["active_scope"]["chain_id"] == "g1_to_g2_addition"
    assert profile["skill_mastery"] == {}
    assert state_file.exists()


def test_record_diagnostic_result_updates_profile_history(state_file: Path) -> None:
    store.ensure_student_profile("user-2")

    profile = store.record_diagnostic_result(
        "user-2",
        chain_id="g1_to_g2_addition",
        current_skill_id="g1_early_arithmetic_core",
        current_topic_id="g1_t05",
        current_grade=1,
        diagnosis_result_id="diag_1_4_1",
        diagnosis_confidence=0.8,
        weak_topic={"topic_id": "g1_t05", "topic": "СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5"},
        detected_gaps=["g1_t05"],
        blocked_skill_ids=["g2_addition_core"],
        remediation_targets={"number_bond_missing_part": "number_bond"},
    )

    assert profile["activity_counters"]["diagnostic_sessions"] == 1
    assert profile["active_scope"]["current_skill_id"] == "g1_early_arithmetic_core"
    assert profile["active_scope"]["blocked_skill_ids"] == ["g2_addition_core"]
    assert profile["active_scope"]["remediation_targets"]["number_bond_missing_part"] == "number_bond"
    assert profile["diagnostic_history"]
    assert profile["diagnostic_history"][0]["diagnosis_result_id"] == "diag_1_4_1"
    assert profile["skill_mastery"]["g2_addition_core"]["blocked_by"] == ["g1_early_arithmetic_core"]
    assert profile["skill_mastery"]["g2_addition_core"]["blocked_by_error_families"] == ["number_bond_missing_part"]


def test_record_practice_attempt_and_mastery_evaluation_update_skill_mastery(state_file: Path) -> None:
    store.ensure_student_profile("user-3")

    practice_profile = store.record_practice_attempt(
        "user-3",
        skill_id="g2_addition_core",
        skill_version="v1",
        question_id="g2_t01_p01",
        topic_id="g2_t01",
        is_correct=True,
        confidence=0.95,
        error_code=None,
        error_family=None,
        remediation_path=None,
    )
    mastery_profile = store.record_mastery_evaluation(
        "user-3",
        skill_id="g2_addition_core",
        skill_version="v1",
        decision="mastered",
        confidence=0.9,
        evidence={"history_length": 5},
        reasons=["correct_threshold_met"],
        failed_criteria=[],
        remediation_path=None,
        error_code=None,
        error_family=None,
    )

    assert practice_profile["activity_counters"]["practice_sessions"] == 1
    assert mastery_profile["activity_counters"]["mastery_checks"] == 1
    assert mastery_profile["skill_mastery"]["g2_addition_core"]["status"] == "mastered"
    assert mastery_profile["skill_mastery"]["g2_addition_core"]["last_mastered_at"]
    assert mastery_profile["mastery_history"]


def test_record_mastery_evaluation_clears_blocked_gates(state_file: Path) -> None:
    store.ensure_student_profile("user-4")
    store.record_diagnostic_result(
        "user-4",
        chain_id="g1_to_g2_addition",
        current_skill_id="g1_early_arithmetic_core",
        current_topic_id="g1_t05",
        current_grade=1,
        diagnosis_result_id="diag_1_4_1",
        diagnosis_confidence=0.8,
        weak_topic={"topic_id": "g1_t05", "topic": "СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5"},
        detected_gaps=["g1_t05"],
        blocked_skill_ids=["g2_addition_core"],
        remediation_targets={"number_bond_missing_part": "number_bond"},
    )

    profile = store.record_mastery_evaluation(
        "user-4",
        skill_id="g1_early_arithmetic_core",
        skill_version="v1",
        decision="mastered",
        confidence=0.95,
        evidence={"history_length": 5},
        reasons=["correct_threshold_met"],
        failed_criteria=[],
        remediation_path="number_bond",
        error_code=None,
        error_family=None,
        unblocked_skill_ids=["g2_addition_core"],
    )

    assert profile["active_scope"]["blocked_skill_ids"] == []
    assert "blocked_by" not in profile["skill_mastery"]["g2_addition_core"]
    assert "blocked_reason" not in profile["skill_mastery"]["g2_addition_core"]


