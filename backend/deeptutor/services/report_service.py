from __future__ import annotations


class ReportService:
    def build_report(self, weak_topic: dict | None, practice_feedback: dict | None = None) -> dict:
        return build_report(weak_topic, practice_feedback)



def build_report(weak_topic: dict | None, practice_feedback: dict | None) -> dict:
    weak_topic = weak_topic or None
    practice_feedback = practice_feedback or {}
    is_correct = bool(practice_feedback.get("is_correct", False))
    topic_name = (weak_topic or {}).get("topic", "тема")
    practice_result = "success" if is_correct else "needs_review"

    summary = (
        f"Практика по теме '{topic_name}' успешна"
        if is_correct
        else f"Практика по теме '{topic_name}' требует повторения"
    )

    return {
        "summary": summary,
        "weak_topic": weak_topic,
        "practice_result": practice_result,
        "recommendations": [
            "Переходи к следующему шагу" if is_correct else "Повтори объяснение и попробуй ещё раз"
        ],
    }
