from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from deeptutor.services.error_taxonomy import error_taxonomy
from deeptutor.services.progress_analytics import get_progress_summary


class ReportService:
    def build_report(self, weak_topic: dict | None, practice_feedback: dict | None = None) -> dict:
        return build_report(weak_topic, practice_feedback)

    def build_full_report(self, user_id: str) -> dict[str, Any]:
        """Build full student report for parents/teachers."""
        summary = get_progress_summary(user_id)
        return generated_report(summary)

    def export_csv(self, user_id: str) -> str:
        """Export student progress as CSV string."""
        summary = get_progress_summary(user_id)
        return _export_progress_csv(summary)


def _topic_name(weak_topic: dict | None) -> str:
    topic = weak_topic or {}
    return str(topic.get("topic") or topic.get("title") or "тема")



def build_report(weak_topic: dict | None, practice_feedback: dict | None) -> dict:
    weak_topic = weak_topic or None
    practice_feedback = practice_feedback or {}
    is_correct = bool(practice_feedback.get("is_correct", False))
    topic_name = _topic_name(weak_topic)
    classification = error_taxonomy.classify_practice_error(weak_topic or {}, practice_feedback, practice_feedback.get("contract") or None)
    practice_result = "success" if is_correct else "needs_review"

    if is_correct:
        summary = (
            f"Эта попытка по теме '{topic_name}' верная. "
            "Но по одной задаче ещё нельзя делать вывод о всём уровне знаний."
        )
        recommendations = [
            "Ещё один похожий пример покажет, насколько тема закрепилась",
            "Можно перейти к следующему шагу, если хочешь продолжить",
        ]
    else:
        error_label = classification.get("error_code") or "unknown_error"
        remediation_path = classification.get("remediation_path") or "slow_step_by_step"
        summary = (
            f"В этой попытке по теме '{topic_name}' есть ошибка типа {error_label}. "
            f"Для ремедиации выбран путь: {remediation_path}."
        )
        recommendations = [
            f"Сначала повторим через путь {remediation_path}",
            "Потом дадим ещё один аналогичный пример того же уровня",
        ]

    return {
        "summary": summary,
        "weak_topic": weak_topic,
        "practice_result": practice_result,
        "recommendations": recommendations,
        "error_code": classification.get("error_code"),
        "error_family": classification.get("error_family"),
        "remediation_path": classification.get("remediation_path"),
        "taxonomy_source": classification.get("taxonomy_source"),
    }


def generated_report(summary: dict[str, Any]) -> dict[str, Any]:
    """Generate a full human-readable report from progress summary."""
    analytics = summary.get("analytics", {})
    overall = analytics.get("overall_score", {})
    response_stats = analytics.get("response_stats", {})
    daily = analytics.get("daily_progress", [])
    heatmap = analytics.get("topic_heatmap", [])

    # Build text sections
    sections: list[dict[str, str]] = []

    # Overall score
    score = overall.get("score", 0)
    mastered = overall.get("mastered", 0)
    total = overall.get("total", 0)
    sections.append({
        "title": "Общий прогресс",
        "content": f"Общий балл: {score}/100. Освоено {mastered} из {total} тем.",
    })

    # Activity
    practice_sessions = overall.get("practice_sessions", 0)
    diagnostic_sessions = overall.get("diagnostic_sessions", 0)
    total_attempts = response_stats.get("total_attempts", 0)
    correct_rate = response_stats.get("correct_rate", 0)
    sections.append({
        "title": "Активность",
        "content": (
                f"Практических сессий: {practice_sessions}. "
            f"Диагностик: {diagnostic_sessions}. "
            f"Всего попыток: {total_attempts}. "
            f"Точность: {correct_rate * 100:.0f}%."
        ),
    })

    # Weak topics
    weak_topics = [h for h in heatmap if h.get("accuracy", 1) < 0.5]
    if weak_topics:
        weak_names = [h["topic_id"] for h in weak_topics[:5]]
        sections.append({
            "title": "Требуют внимания",
            "content": f"Темы с точностью ниже 50%: {', '.join(weak_names)}.",
        })

    # Recent daily progress
    if daily:
        last_7 = daily[-7:]
        daily_lines = [f"  {d['date']}: {d['correct']}/{d['total']} ({d['accuracy'] * 100:.0f}%)" for d in last_7]
        sections.append({
            "title": "Последние дни",
            "content": "\n".join(daily_lines),
        })

    # Error family distribution
    error_dist = response_stats.get("error_family_distribution", {})
    if error_dist:
        error_lines = [f"  {family}: {count}" for family, count in sorted(error_dist.items(), key=lambda x: -x[1])]
        sections.append({
            "title": "Типичные ошибки",
            "content": "\n".join(error_lines),
        })

    # Recommendations
    recommended = summary.get("recommended_next_action", "diagnose")
    sections.append({
        "title": "Рекомендация",
        "content": _recommendation_text(recommended),
    })

    return {
        "user_id": summary.get("user_id"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_score": score,
        "sections": sections,
        "raw_summary": summary,
    }


def _recommendation_text(recommended: str) -> str:
    """Convert recommendation code to human-readable text."""
    if recommended.startswith("ready_for_promotion:"):
        return f"Ученик готов к переходу на следующую тему."
    elif recommended.startswith("continue_practice:"):
        return "Рекомендуется продолжить практику по текущей теме."
    elif recommended.startswith("needs_more_practice:"):
        return "Нужно больше практики по текущей теме."
    elif recommended == "chain_complete":
        return "Цепочка обучения завершена!"
    elif recommended == "diagnose":
        return "Рекомендуется пройти диагностику."
    else:
        return recommended


def _export_progress_csv(summary: dict[str, Any]) -> str:
    """Export progress summary as CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header: overall info
    writer.writerow(["User ID", summary.get("user_id", "")])
    writer.writerow(["Generated At", datetime.now(timezone.utc).isoformat()])
    writer.writerow([])

    # Overall score
    analytics = summary.get("analytics", {})
    overall = analytics.get("overall_score", {})
    writer.writerow(["Overall Score", overall.get("score", 0)])
    writer.writerow(["Mastered Skills", overall.get("mastered", 0)])
    writer.writerow(["Learning Skills", overall.get("learning", 0)])
    writer.writerow(["Total Skills", overall.get("total", 0)])
    writer.writerow([])

    # Skills table
    writer.writerow(["Skill ID", "Grade", "Status", "Mode", "Last Practiced", "Correct"])
    for skill in summary.get("skills", []):
        writer.writerow([
            skill.get("skill_id", ""),
            skill.get("grade", ""),
            skill.get("status", ""),
            skill.get("mode", ""),
            skill.get("last_practiced_at", ""),
            skill.get("last_attempt_correct", ""),
        ])
    writer.writerow([])

    # Daily progress
    daily = analytics.get("daily_progress", [])
    if daily:
        writer.writerow(["Date", "Total", "Correct", "Accuracy", "Skills Practiced"])
        for day in daily:
            writer.writerow([
                day.get("date", ""),
                day.get("total", 0),
                day.get("correct", 0),
                day.get("accuracy", 0),
                day.get("skills_practiced", 0),
            ])
    writer.writerow([])

    # Topic heatmap
    heatmap = analytics.get("topic_heatmap", [])
    if heatmap:
        writer.writerow(["Topic ID", "Total", "Correct", "Accuracy"])
        for topic in heatmap:
            writer.writerow([
                topic.get("topic_id", ""),
                topic.get("total", 0),
                topic.get("correct", 0),
                topic.get("accuracy", 0),
            ])

    return output.getvalue()
