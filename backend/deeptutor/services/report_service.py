from __future__ import annotations


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
        summary = (
            f"В этой попытке по теме '{topic_name}' есть ошибка. "
            "Одна ошибка не означает, что тема не понята."
        )
        recommendations = [
            "Повтори объяснение и попробуй ещё раз",
            "Одна ошибка не даёт повода делать вывод о знании всей темы",
        ]

    return {
        "summary": summary,
        "weak_topic": weak_topic,
        "practice_result": practice_result,
        "recommendations": recommendations,
    }
