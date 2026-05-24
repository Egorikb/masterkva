from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
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

    # Build analytics
    error_history = _build_error_history(mastery_history)
    daily_progress = _build_daily_progress(mastery_history)
    topic_heatmap = _build_topic_heatmap(mastery_history)
    overall_score = _calculate_overall_score(skill_mastery, activity_counters)
    response_stats = _calculate_response_stats(mastery_history)

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
        # Phase G analytics
        "analytics": {
            "overall_score": overall_score,
            "error_history": error_history,
            "daily_progress": daily_progress,
            "topic_heatmap": topic_heatmap,
            "response_stats": response_stats,
        },
    }


def _grade_from_skill_id(skill_id: str) -> int | None:
    """Extract grade from skill_id like 'g1_...' -> 1."""
    try:
        if skill_id and skill_id.startswith("g") and "_" in skill_id:
            return int(skill_id[1:].split("_")[0])
    except (ValueError, IndexError):
        pass
    return None


def _build_error_history(mastery_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build chronological error history from mastery history."""
    errors: list[dict[str, Any]] = []
    for entry in mastery_history:
        if entry.get("event") == "practice_attempt" and not entry.get("is_correct", True):
            errors.append({
                "at": entry.get("at"),
                "skill_id": entry.get("skill_id"),
                "topic_id": entry.get("topic_id"),
                "error_code": entry.get("error_code"),
                "error_family": entry.get("error_family"),
                "remediation_path": entry.get("remediation_path"),
            })
    return errors[-50:]  # last 50 errors


def _build_daily_progress(mastery_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate practice results by day."""
    daily: dict[str, dict[str, Any]] = {}
    for entry in mastery_history:
        if entry.get("event") != "practice_attempt":
            continue
        at = entry.get("at", "")
        day = at[:10] if len(at) >= 10 else "unknown"
        if day not in daily:
            daily[day] = {"date": day, "total": 0, "correct": 0, "skills": set()}
        daily[day]["total"] += 1
        if entry.get("is_correct"):
            daily[day]["correct"] += 1
        if entry.get("skill_id"):
            daily[day]["skills"].add(entry["skill_id"])

    result = []
    for day in sorted(daily.keys()):
        d = daily[day]
        result.append({
            "date": d["date"],
            "total": d["total"],
            "correct": d["correct"],
            "accuracy": round(d["correct"] / d["total"], 2) if d["total"] > 0 else 0,
            "skills_practiced": len(d["skills"]),
        })
    return result[-30:]  # last 30 days


def _build_topic_heatmap(mastery_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build per-topic accuracy heatmap."""
    topic_stats: dict[str, dict[str, Any]] = {}
    for entry in mastery_history:
        if entry.get("event") != "practice_attempt":
            continue
        topic_id = entry.get("topic_id") or entry.get("skill_id") or "unknown"
        if topic_id not in topic_stats:
            topic_stats[topic_id] = {"topic_id": topic_id, "total": 0, "correct": 0}
        topic_stats[topic_id]["total"] += 1
        if entry.get("is_correct"):
            topic_stats[topic_id]["correct"] += 1

    heatmap = []
    for topic_id, stats in topic_stats.items():
        heatmap.append({
            "topic_id": topic_id,
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(stats["correct"] / stats["total"], 2) if stats["total"] > 0 else 0,
        })
    # Sort by accuracy ascending (weakest first)
    heatmap.sort(key=lambda x: x["accuracy"])
    return heatmap


def _calculate_overall_score(
    skill_mastery: dict[str, Any], activity_counters: dict[str, Any]
) -> dict[str, Any]:
    """Calculate overall student score (0-100)."""
    total_skills = len(skill_mastery)
    if total_skills == 0:
        return {"score": 0, "mastered": 0, "learning": 0, "total": 0}

    mastered = sum(1 for s in skill_mastery.values() if s.get("status") == "mastered")
    learning = sum(1 for s in skill_mastery.values() if s.get("status") in ("learning", "practicing"))
    total = total_skills

    # Score: mastered = 100%, learning = 50%, unknown = 0%
    score = round((mastered * 100 + learning * 50) / total) if total > 0 else 0

    practice_sessions = int(activity_counters.get("practice_sessions") or 0)
    diagnostic_sessions = int(activity_counters.get("diagnostic_sessions") or 0)

    return {
        "score": min(score, 100),
        "mastered": mastered,
        "learning": learning,
        "total": total,
        "practice_sessions": practice_sessions,
        "diagnostic_sessions": diagnostic_sessions,
    }


def _calculate_response_stats(mastery_history: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate response statistics from mastery history."""
    attempts = [e for e in mastery_history if e.get("event") == "practice_attempt"]
    if not attempts:
        return {"total_attempts": 0, "correct_rate": 0, "avg_confidence": 0}

    total = len(attempts)
    correct = sum(1 for a in attempts if a.get("is_correct"))
    confidences = [a.get("confidence") for a in attempts if a.get("confidence") is not None]
    avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0

    # Error family distribution
    error_families: dict[str, int] = defaultdict(int)
    for a in attempts:
        if not a.get("is_correct") and a.get("error_family"):
            error_families[a["error_family"]] += 1

    return {
        "total_attempts": total,
        "correct_rate": round(correct / total, 2) if total > 0 else 0,
        "avg_confidence": avg_confidence,
        "error_family_distribution": dict(error_families),
    }


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
