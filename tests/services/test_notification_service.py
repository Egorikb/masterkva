from __future__ import annotations

from deeptutor.services.notification_service import (
    _build_notification,
    _log_notification,
    get_notification_log,
    clear_notification_log,
)


def test_build_notification_mastery():
    notif = _build_notification("u1", "mastery_achieved", {"skill_id": "s1"})
    assert notif["event_type"] == "mastery_achieved"
    assert notif["title"] == "Тема освоена!"
    assert "s1" in notif["message"]


def test_build_notification_streak():
    notif = _build_notification("u1", "streak_milestone", {"streak": 7})
    assert notif["event_type"] == "streak_milestone"
    assert notif["streak"] == 7
    assert "7" in notif["message"]


def test_build_notification_daily_summary():
    notif = _build_notification("u1", "daily_summary", {})
    assert notif["event_type"] == "daily_summary"
    assert "title" in notif


def test_notification_log_append():
    clear_notification_log()
    notif = _build_notification("u1", "mastery_achieved", {"skill_id": "s1"})
    _log_notification(notif)
    log = get_notification_log("u1")
    assert len(log) >= 1


def test_notification_log_filter_by_user():
    clear_notification_log()
    _log_notification(_build_notification("u1", "mastery_achieved", {}))
    _log_notification(_build_notification("u2", "streak_milestone", {}))
    log = get_notification_log("u1")
    assert all(n["user_id"] == "u1" for n in log)


def test_notification_log_clear():
    _log_notification(_build_notification("u1", "mastery_achieved", {}))
    clear_notification_log()
    assert get_notification_log() == []
