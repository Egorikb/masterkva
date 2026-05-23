from __future__ import annotations

from deeptutor.services.error_taxonomy import error_taxonomy


class ReportService:
    def build_report(self, weak_topic: dict | None, practice_feedback: dict | None = None) -> dict:
        return build_report(weak_topic, practice_feedback)



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
