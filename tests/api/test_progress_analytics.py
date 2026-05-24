from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from deeptutor.api.routers.plugins_api import router
from deeptutor.services.progress_analytics import (
    get_progress_summary,
    _build_error_history,
    _build_daily_progress,
    _build_topic_heatmap,
    _calculate_overall_score,
    _calculate_response_stats,
)
from deeptutor.services.report_service import (
    ReportService,
    build_report,
    generated_report,
    _export_progress_csv,
    _recommendation_text,
)
from deeptutor.services.notification_service import (
    check_and_notify,
    get_notification_log,
    clear_notification_log,
    _build_notification,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/plugins")
    return app


# === progress_analytics tests ===

def test_analytics_structure_in_summary() -> None:
    """Progress summary should include analytics section."""
    user_id = f"analytics-struct-{uuid.uuid4()}"
    summary = get_progress_summary(user_id)
    assert "analytics" in summary
    analytics = summary["analytics"]
    assert "overall_score" in analytics
    assert "error_history" in analytics
    assert "daily_progress" in analytics
    assert "topic_heatmap" in analytics
    assert "response_stats" in analytics


def test_overall_score_empty_profile() -> None:
    """Overall score should be 0 for empty profile."""
    score = _calculate_overall_score({}, {})
    assert score["score"] == 0
    assert score["mastered"] == 0
    assert score["total"] == 0


def test_overall_score_with_mastered_skills() -> None:
    """Overall score should reflect mastered skills."""
    skill_mastery = {
        "skill_a": {"status": "mastered"},
        "skill_b": {"status": "mastered"},
        "skill_c": {"status": "learning"},
    }
    counters = {"practice_sessions": 10, "diagnostic_sessions": 2}
    score = _calculate_overall_score(skill_mastery, counters)
    assert score["mastered"] == 2
    assert score["learning"] == 1
    assert score["total"] == 3
    # (2*100 + 1*50) / 3 = 83
    assert score["score"] == 83


def test_error_history_empty() -> None:
    """Error history should be empty for no attempts."""
    errors = _build_error_history([])
    assert errors == []


def test_error_history_filters_correct() -> None:
    """Error history should only include wrong answers."""
    history = [
        {"event": "practice_attempt", "is_correct": True, "at": "2026-01-01T00:00:00Z"},
        {"event": "practice_attempt", "is_correct": False, "at": "2026-01-01T00:01:00Z", "error_code": "E001"},
        {"event": "mastery_evaluation", "is_correct": False},
    ]
    errors = _build_error_history(history)
    assert len(errors) == 1
    assert errors[0]["error_code"] == "E001"


def test_daily_progress_aggregation() -> None:
    """Daily progress should aggregate by date."""
    history = [
        {"event": "practice_attempt", "is_correct": True, "at": "2026-01-15T10:00:00Z", "skill_id": "s1"},
        {"event": "practice_attempt", "is_correct": False, "at": "2026-01-15T11:00:00Z", "skill_id": "s2"},
        {"event": "practice_attempt", "is_correct": True, "at": "2026-01-16T10:00:00Z", "skill_id": "s1"},
    ]
    daily = _build_daily_progress(history)
    assert len(daily) == 2
    assert daily[0]["date"] == "2026-01-15"
    assert daily[0]["total"] == 2
    assert daily[0]["correct"] == 1
    assert daily[0]["accuracy"] == 0.5
    assert daily[0]["skills_practiced"] == 2


def test_topic_heatmap_sorted_by_accuracy() -> None:
    """Topic heatmap should be sorted by accuracy ascending (weakest first)."""
    history = [
        {"event": "practice_attempt", "is_correct": True, "at": "T1", "topic_id": "strong"},
        {"event": "practice_attempt", "is_correct": True, "at": "T2", "topic_id": "strong"},
        {"event": "practice_attempt", "is_correct": False, "at": "T3", "topic_id": "weak"},
        {"event": "practice_attempt", "is_correct": False, "at": "T4", "topic_id": "weak"},
    ]
    heatmap = _build_topic_heatmap(history)
    assert len(heatmap) == 2
    assert heatmap[0]["topic_id"] == "weak"
    assert heatmap[0]["accuracy"] == 0.0
    assert heatmap[1]["topic_id"] == "strong"
    assert heatmap[1]["accuracy"] == 1.0


def test_response_stats_empty() -> None:
    """Response stats should handle empty history."""
    stats = _calculate_response_stats([])
    assert stats["total_attempts"] == 0
    assert stats["correct_rate"] == 0


def test_response_stats_with_data() -> None:
    """Response stats should calculate correct rate and confidence."""
    history = [
        {"event": "practice_attempt", "is_correct": True, "confidence": 0.9},
        {"event": "practice_attempt", "is_correct": True, "confidence": 0.8},
        {"event": "practice_attempt", "is_correct": False, "confidence": 0.3, "error_family": "calculation"},
    ]
    stats = _calculate_response_stats(history)
    assert stats["total_attempts"] == 3
    assert stats["correct_rate"] == 0.67
    assert stats["avg_confidence"] == 0.67
    assert stats["error_family_distribution"]["calculation"] == 1


# === report_service tests ===

def test_report_service_build_full_report() -> None:
    """Full report should have sections and raw summary."""
    service = ReportService()
    user_id = f"report-full-{uuid.uuid4()}"
    report = service.build_full_report(user_id)
    assert report["user_id"] == user_id
    assert "generated_at" in report
    assert "sections" in report
    assert "raw_summary" in report
    assert isinstance(report["sections"], list)


def test_report_service_export_csv() -> None:
    """CSV export should return string with CSV content."""
    service = ReportService()
    user_id = f"report-csv-{uuid.uuid4()}"
    csv_content = service.export_csv(user_id)
    assert isinstance(csv_content, str)
    assert "User ID" in csv_content
    assert user_id in csv_content


def test_build_report_correct_answer() -> None:
    """Report for correct answer should have success result."""
    report = build_report({"topic": "сложение"}, {"is_correct": True})
    assert report["practice_result"] == "success"
    assert "верная" in report["summary"]


def test_build_report_wrong_answer() -> None:
    """Report for wrong answer should have needs_review result."""
    report = build_report({"topic": "сложение"}, {"is_correct": False})
    assert report["practice_result"] == "needs_review"
    assert "ошибка" in report["summary"]


def test_recommendation_text_known_actions() -> None:
    """Recommendation text should be human-readable."""
    assert "следующую" in _recommendation_text("ready_for_promotion:g2")
    assert "практику" in _recommendation_text("continue_practice:g1")
    assert "больше" in _recommendation_text("needs_more_practice:g1")
    assert "завершена" in _recommendation_text("chain_complete")
    assert "диагностику" in _recommendation_text("diagnose")


# === notification_service tests ===

def test_build_notification_mastery() -> None:
    """Mastery notification should have correct structure."""
    notif = _build_notification("user1", "mastery_achieved", {"skill_id": "g1_counting"})
    assert notif["event_type"] == "mastery_achieved"
    assert notif["user_id"] == "user1"
    assert "освоил" in notif["message"]
    assert "skill_id" in notif


def test_build_notification_streak() -> None:
    """Streak notification should include streak count."""
    notif = _build_notification("user1", "streak_milestone", {"streak": 5})
    assert notif["event_type"] == "streak_milestone"
    assert notif["streak"] == 5
    assert "5" in notif["message"]


def test_notification_log_append_and_retrieve() -> None:
    """Notification log should store and retrieve notifications."""
    clear_notification_log()
    notif = _build_notification("user1", "mastery_achieved", {"skill_id": "s1"})
    from deeptutor.services.notification_service import _log_notification
    _log_notification(notif)

    log = get_notification_log("user1")
    assert len(log) >= 1
    assert log[-1]["event_type"] == "mastery_achieved"


def test_notification_log_clear() -> None:
    """Clear should empty the notification log."""
    clear_notification_log()
    log = get_notification_log()
    assert log == []


# === API endpoint tests ===

def test_dashboard_endpoint() -> None:
    """Dashboard endpoint should return 200 with summary and report."""
    from deeptutor.api.routers.plugins_api import save_user_states

    user_id = f"dash-api-{uuid.uuid4()}"
    save_user_states({
        user_id: {
            "name": "Тест",
            "grade": 1,
            "phase": "chat",
            "student_profile": {
                "active_scope": {"current_skill_id": None, "blocked_skill_ids": []},
                "skill_mastery": {},
                "promotion_history": [],
            },
        }
    })

    with TestClient(_build_app()) as client:
        response = client.get(f"/api/v1/plugins/panda/dashboard/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert "summary" in data
        assert "report" in data


def test_csv_export_endpoint() -> None:
    """CSV export endpoint should return 200 with CSV content."""
    from deeptutor.api.routers.plugins_api import save_user_states

    user_id = f"csv-api-{uuid.uuid4()}"
    save_user_states({
        user_id: {
            "name": "Тест",
            "grade": 1,
            "phase": "chat",
            "student_profile": {
                "active_scope": {"current_skill_id": None, "blocked_skill_ids": []},
                "skill_mastery": {},
                "promotion_history": [],
            },
        }
    })

    with TestClient(_build_app()) as client:
        response = client.get(f"/api/v1/plugins/panda/reports/{user_id}/csv")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "csv"
        assert "content" in data


def test_notifications_subscribe_endpoint() -> None:
    """Notification subscribe endpoint should return 200."""
    user_id = f"notif-api-{uuid.uuid4()}"

    with TestClient(_build_app()) as client:
        response = client.post(
            "/api/v1/plugins/panda/notifications/subscribe",
            params={"user_id": user_id, "webhook_url": "https://example.com/webhook"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subscribed"] is True
        assert "mastery_achieved" in data["events"]
