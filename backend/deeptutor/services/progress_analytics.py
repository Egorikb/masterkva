from __future__ import annotations

from typing import Any

from deeptutor.services.student_profile_store import (
    ensure_student_profile,
    get_student_profile,
)
from deeptutor.services.skill_runtime import skill_resolver


def get_progress_summary(user_id: str) -> dict[str, Any]:
    """Read-only progress summary for parents/teachers.

    Returns skill status, recent mastery decisions, gaps, and recommended next actions.
    Does NOT modify any state or affect learning flow.
    """
    profile = get_student_profile(user_id)
    if not profile:
        profile = ensure_student_profile(user_id)

    active_scope = profile.get("active_scope", {})
    skill_mastery = profile.get("skill_mastery", {})
    diagnostic_history = profile.get("diagnostic_history", [])
    mastery_history = profile.get("mastery_history", [])
    promotion_history = profile.get("promotion_history", [])
    activity_counters = profile.get("activity_counters", {})

    current_skill_id = active_scope.get("current_skill_id")
    blocked_skill_ids = active_scope.get("blocked_skill_ids", [])
    chain_id = active_scope.get("chain_id")

    # Build per-skill summary
    skills_summary: list[dict[str, Any]] = []
    for skill_id, mastery_entry in skill_mastery.items():
        resolution = skill_resolver.resolve(topic_id=skill_id)
        summary: dict[str, Any] = {
            "skill_id": skill_id,
            "grade": _grade_from_skill_id(skill_id),
            "status": mastery_entry.get("status", "unknown"),
            "mode": resolution.mode,
            "last_practiced_at": mastery_entry.get("last_practiced_at"),
            "last_attempt_correct": mastery_entry.get("last_attempt_correct"),
            "last_attempt_confidence": mastery_entry.get("last_attempt_confidence"),
            "last_mastered_at": mastery_entry.get("last_mastered_at"),
            "blocked_by": mastery_entry.get("blocked_by"),
            "blocked_reason": mastery_entry.get("blocked_reason"),
            "error_code": mastery_entry.get("error_code"),
            "error_family": mastery_entry.get("error_family"),
            "last_mastery_decision": mastery_entry.get("last_mastery_decision"),
        }
        skills_summary.append(summary)

    # Recommend next action (deterministic, backend-owned)
    recommended_action = _recommend_next_action(
        current_skill_id=current_skill_id,
        blocked_skill_ids=blocked_skill_ids,
        skill_mastery=skill_mastery,
    )

    return {
        "user_id": user_id,
        "profile_schema_version": profile.get("profile_schema_version", "v1"),
        "chain_id": chain_id,
        "current_skill_id": current_skill_id,
        "blocked_skill_ids": blocked_skill_ids,
        "activity_counters": activity_counters,
        "skills": skills_summary,
        "last_diagnostic_at": diagnostic_history[-1]["at"] if diagnostic_history else None,
        "last_mastery_at": mastery_history[-1]["at"] if mastery_history else None,
        "last_promotion_at": promotion_history[-1]["at"] if promotion_history else None,
        "recommended_next_action": recommended_action,
    }


def _grade_from_skill_id(skill_id: str) -> int | None:
    """Extract grade from skill_id like 'g1_...' -> 1."""
    try:
        if skill_id and skill_id.startswith("g") and "_" in skill_id:
            return int(skill_id[1:].split("_")[0])
    except (ValueError, IndexError):
        pass
    return None


def _recommend_next_action(
    current_skill_id: str | None,
    blocked_skill_ids: list[str],
    skill_mastery: dict[str, Any],
) -> str:
    """Deterministic next-action recommendation."""
    if blocked_skill_ids:
        return f"continue_current_skill:{current_skill_id}"

    if current_skill_id:
        mastery_entry = skill_mastery.get(current_skill_id, {})
        status = mastery_entry.get("status", "")
        if status == "mastered":
            next_skills = skill_resolver.resolve(topic_id=current_skill_id).next_skills
            if next_skills:
                return f"ready_for_promotion:{next_skills[0]}"
            return "chain_complete"
        elif status == "learning":
            return f"continue_practice:{current_skill_id}"
        elif status == "practicing":
            return f"needs_more_practice:{current_skill_id}"

    else:
        return f"start_g1_early_arithmetic_core"

    return "diagnose"
