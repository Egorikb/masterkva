from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from deeptutor.services.progress_analytics import get_progress_summary
from deeptutor.services.student_profile_store import get_student_profile

logger = logging.getLogger(__name__)

# In-memory notification log (persists only while backend runs)
_notification_log: list[dict[str, Any]] = []
MAX_NOTIFICATION_LOG = 500


def check_and_notify(user_id: str, event_type: str, event_data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Check if a notification should be sent and log it.

    Called by the main flow after key events (mastery, promotion, etc.).
    Returns notification payload if triggered, None otherwise.
    """
    profile = get_student_profile(user_id)
    subscription = _get_subscription(profile)

    if not subscription:
        return None

    events = subscription.get("events", [])
    if event_type not in events:
        return None

    notification = _build_notification(user_id, event_type, event_data or {})
    _log_notification(notification)

    # In production: POST to webhook_url
    webhook_url = subscription.get("webhook_url")
    if webhook_url:
        _send_webhook(webhook_url, notification)

    return notification


def _build_notification(user_id: str, event_type: str, event_data: dict[str, Any]) -> dict[str, Any]:
    """Build notification payload based on event type."""
    summary = get_progress_summary(user_id)
    analytics = summary.get("analytics", {})
    overall = analytics.get("overall_score", {})

    base = {
        "user_id": user_id,
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall.get("score", 0),
    }

    if event_type == "mastery_achieved":
        skill_id = event_data.get("skill_id", "unknown")
        return {
            **base,
            "title": "Тема освоена!",
            "message": f"Ученик успешно освоил тему «{skill_id}».",
            "skill_id": skill_id,
            "next_skill_id": event_data.get("next_skill_id"),
        }

    elif event_type == "daily_summary":
        daily = analytics.get("daily_progress", [])
        today = daily[-1] if daily else {}
        return {
            **base,
            "title": "Итоги дня",
            "message": (
                f"Сегодня: {today.get('correct', 0)}/{today.get('total', 0)} верных ответов. "
                f"Общий балл: {overall.get('score', 0)}/100."
            ),
            "daily_stats": today,
        }

    elif event_type == "streak_milestone":
        streak = event_data.get("streak", 0)
        return {
            **base,
            "title": "Серия успехов!",
            "message": f"Ученик ответил верно {streak} раз подряд!",
            "streak": streak,
        }

    else:
        return {
            **base,
            "title": event_type,
            "message": json.dumps(event_data, ensure_ascii=False),
        }


def _get_subscription(profile: dict[str, Any]) -> dict[str, Any] | None:
    """Get notification subscription from user state."""
    # Subscription is stored in user state, not profile
    # For now, check if user has any subscription configured
    state_data = profile.get("_notification_subscription")
    if state_data:
        return state_data
    return None


def _log_notification(notification: dict[str, Any]) -> None:
    """Log notification to in-memory log."""
    global _notification_log
    _notification_log.append(notification)
    if len(_notification_log) > MAX_NOTIFICATION_LOG:
        _notification_log = _notification_log[-MAX_NOTIFICATION_LOG:]


def _send_webhook(webhook_url: str, notification: dict[str, Any]) -> bool:
    """Send notification to webhook URL. Placeholder for production."""
    logger.info(f"Would send webhook to {webhook_url}: {notification['event_type']}")
    # In production: requests.post(webhook_url, json=notification, timeout=5)
    return True


def get_notification_log(user_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Get notification log, optionally filtered by user_id."""
    if user_id:
        filtered = [n for n in _notification_log if n.get("user_id") == user_id]
        return filtered[-limit:]
    return _notification_log[-limit:]


def clear_notification_log() -> None:
    """Clear notification log. For testing."""
    global _notification_log
    _notification_log = []
