from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_FILE = Path(__file__).resolve().parents[2] / "data" / "user_states.json"
DEFAULT_CHAIN_ID = "g1_to_g2_addition"
DEFAULT_ALLOWED_SKILLS = ["g1_early_arithmetic_core", "g2_addition_core"]
PROFILE_SCHEMA_VERSION = "v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_states() -> dict[str, dict[str, Any]]:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_states(states: dict[str, dict[str, Any]]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(states, ensure_ascii=False, indent=2), encoding="utf-8")


def _fresh_profile(user_id: str | None = None) -> dict[str, Any]:
    return {
        "profile_schema_version": PROFILE_SCHEMA_VERSION,
        "user_id": user_id,
        "active_scope": {
            "chain_id": DEFAULT_CHAIN_ID,
            "allowed_skill_ids": list(DEFAULT_ALLOWED_SKILLS),
            "current_skill_id": None,
            "current_topic_id": None,
            "current_grade": None,
            "updated_at": None,
        },
        "skill_mastery": {},
        "diagnostic_history": [],
        "mastery_history": [],
        "promotion_history": [],
        "activity_counters": {
            "diagnostic_sessions": 0,
            "practice_sessions": 0,
            "mastery_checks": 0,
            "promotions": 0,
        },
        "last_updated_at": None,
    }


def _merge_profile(base: dict[str, Any], profile: dict[str, Any] | None, user_id: str | None = None) -> dict[str, Any]:
    merged = deepcopy(base)
    if isinstance(profile, dict):
        merged.update({k: v for k, v in profile.items() if k != "active_scope" and k != "activity_counters"})
        merged["active_scope"].update(profile.get("active_scope") or {})
        merged["activity_counters"].update(profile.get("activity_counters") or {})
        merged["skill_mastery"] = dict(profile.get("skill_mastery") or {})
        merged["diagnostic_history"] = list(profile.get("diagnostic_history") or [])
        merged["mastery_history"] = list(profile.get("mastery_history") or [])
        merged["promotion_history"] = list(profile.get("promotion_history") or [])
    if user_id is not None:
        merged["user_id"] = user_id
    return merged


def ensure_student_profile(user_id: str) -> dict[str, Any]:
    states = _read_states()
    state = dict(states.get(user_id) or {})
    profile = _merge_profile(_fresh_profile(user_id), state.get("student_profile"), user_id)
    state["student_profile"] = profile
    states[user_id] = state
    _write_states(states)
    return profile


def get_student_profile(user_id: str) -> dict[str, Any]:
    states = _read_states()
    state = dict(states.get(user_id) or {})
    profile = state.get("student_profile")
    if not isinstance(profile, dict):
        return ensure_student_profile(user_id)
    return _merge_profile(_fresh_profile(user_id), profile, user_id)


def update_student_profile(user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    states = _read_states()
    state = dict(states.get(user_id) or {})
    profile = _merge_profile(_fresh_profile(user_id), state.get("student_profile"), user_id)
    for key, value in patch.items():
        if value is None:
            profile.pop(key, None)
        else:
            profile[key] = value
    profile["last_updated_at"] = _utc_now()
    state["student_profile"] = profile
    states[user_id] = state
    _write_states(states)
    return profile


def _upsert_skill_entry(profile: dict[str, Any], skill_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    skill_mastery = dict(profile.get("skill_mastery") or {})
    entry = dict(skill_mastery.get(skill_id) or {})
    entry.update(patch)
    skill_mastery[skill_id] = entry
    profile["skill_mastery"] = skill_mastery
    return profile


def record_diagnostic_result(
    user_id: str,
    *,
    chain_id: str,
    current_skill_id: str | None,
    current_topic_id: str | None,
    current_grade: int | None,
    diagnosis_result_id: str | None,
    diagnosis_confidence: float | None,
    weak_topic: dict[str, Any] | None,
    detected_gaps: list[str] | None,
) -> dict[str, Any]:
    profile = ensure_student_profile(user_id)
    profile["activity_counters"]["diagnostic_sessions"] = int(profile["activity_counters"].get("diagnostic_sessions") or 0) + 1
    profile["active_scope"] = {
        **profile.get("active_scope", {}),
        "chain_id": chain_id,
        "allowed_skill_ids": list(DEFAULT_ALLOWED_SKILLS),
        "current_skill_id": current_skill_id,
        "current_topic_id": current_topic_id,
        "current_grade": current_grade,
        "updated_at": _utc_now(),
    }
    profile.setdefault("diagnostic_history", []).append(
        {
            "at": _utc_now(),
            "diagnosis_result_id": diagnosis_result_id,
            "diagnosis_confidence": diagnosis_confidence,
            "current_skill_id": current_skill_id,
            "current_topic_id": current_topic_id,
            "current_grade": current_grade,
            "weak_topic_id": (weak_topic or {}).get("topic_id"),
            "weak_topic": (weak_topic or {}).get("topic"),
            "detected_gaps": list(detected_gaps or []),
        }
    )
    profile["last_updated_at"] = _utc_now()
    return update_student_profile(user_id, profile)


def record_practice_attempt(
    user_id: str,
    *,
    skill_id: str | None,
    skill_version: str | None,
    question_id: str | None,
    topic_id: str | None,
    is_correct: bool,
    confidence: float | None,
    error_code: str | None,
    error_family: str | None,
    remediation_path: str | None,
) -> dict[str, Any]:
    profile = ensure_student_profile(user_id)
    profile["activity_counters"]["practice_sessions"] = int(profile["activity_counters"].get("practice_sessions") or 0) + 1
    if skill_id:
        profile = _upsert_skill_entry(
            profile,
            skill_id,
            {
                "skill_id": skill_id,
                "skill_version": skill_version,
                "last_practiced_at": _utc_now(),
                "last_attempt_at": _utc_now(),
                "last_attempt_correct": bool(is_correct),
                "last_attempt_confidence": confidence,
                "last_practice_question_id": question_id,
                "last_practice_topic_id": topic_id,
                "error_code": error_code,
                "error_family": error_family,
                "remediation_path": remediation_path,
            },
        )
    profile.setdefault("mastery_history", []).append(
        {
            "at": _utc_now(),
            "event": "practice_attempt",
            "skill_id": skill_id,
            "skill_version": skill_version,
            "question_id": question_id,
            "topic_id": topic_id,
            "is_correct": bool(is_correct),
            "confidence": confidence,
            "error_code": error_code,
            "error_family": error_family,
            "remediation_path": remediation_path,
        }
    )
    profile["last_updated_at"] = _utc_now()
    return update_student_profile(user_id, profile)


def record_mastery_evaluation(
    user_id: str,
    *,
    skill_id: str | None,
    skill_version: str | None,
    decision: str,
    confidence: float | None,
    evidence: dict[str, Any] | None,
    reasons: list[str] | None,
    failed_criteria: list[str] | None,
    remediation_path: str | None,
    error_code: str | None = None,
    error_family: str | None = None,
) -> dict[str, Any]:
    profile = ensure_student_profile(user_id)
    profile["activity_counters"]["mastery_checks"] = int(profile["activity_counters"].get("mastery_checks") or 0) + 1
    profile.setdefault("mastery_history", []).append(
        {
            "at": _utc_now(),
            "skill_id": skill_id,
            "skill_version": skill_version,
            "decision": decision,
            "confidence": confidence,
            "evidence": dict(evidence or {}),
            "reasons": list(reasons or []),
            "failed_criteria": list(failed_criteria or []),
            "remediation_path": remediation_path,
            "error_code": error_code,
            "error_family": error_family,
        }
    )
    if skill_id:
        profile = _upsert_skill_entry(
            profile,
            skill_id,
            {
                "skill_id": skill_id,
                "skill_version": skill_version,
                "status": decision,
                "mastery_level": "mastered" if decision == "mastered" else ("remediation" if decision == "needs_remediation" else "learning"),
                "last_evaluated_at": _utc_now(),
                "mastery_confidence": confidence,
                "decision": decision,
                "evidence": dict(evidence or {}),
                "reasons": list(reasons or []),
                "failed_criteria": list(failed_criteria or []),
                "error_code": error_code,
                "error_family": error_family,
                "remediation_path": remediation_path,
            },
        )
        if decision == "mastered":
            profile["skill_mastery"][skill_id]["last_mastered_at"] = _utc_now()
    profile["last_updated_at"] = _utc_now()
    return update_student_profile(user_id, profile)


def record_promotion(
    user_id: str,
    *,
    from_skill_id: str | None,
    to_skill_id: str | None,
    from_skill_version: str | None = None,
    to_skill_version: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    profile = ensure_student_profile(user_id)
    profile["activity_counters"]["promotions"] = int(profile["activity_counters"].get("promotions") or 0) + 1
    profile.setdefault("promotion_history", []).append(
        {
            "at": _utc_now(),
            "from_skill_id": from_skill_id,
            "to_skill_id": to_skill_id,
            "from_skill_version": from_skill_version,
            "to_skill_version": to_skill_version,
            "reason": reason or "backend_promotion",
        }
    )
    profile["active_scope"] = {
        **profile.get("active_scope", {}),
        "current_skill_id": to_skill_id,
        "updated_at": _utc_now(),
    }
    profile["last_updated_at"] = _utc_now()
    return update_student_profile(user_id, profile)
