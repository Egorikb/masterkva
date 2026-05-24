from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from deeptutor.api.routers.plugins_api import router
from deeptutor.services.progress_analytics import get_progress_summary


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/plugins")
    return app


def test_progress_summary_returns_structure() -> None:
    """Progress summary should return expected structure."""
    user_id = f"progress-test-{uuid.uuid4()}"
    summary = get_progress_summary(user_id)

    assert summary["user_id"] == user_id
    assert "current_skill_id" in summary
    assert "blocked_skill_ids" in summary
    assert "skills" in summary
    assert "activity_counters" in summary
    assert "recommended_next_action" in summary


def test_progress_summary_after_practice(tmp_path, monkeypatch) -> None:
    """Progress summary should reflect practice activity."""
    from deeptutor.api.routers.plugins_api import save_user_states

    user_id = f"progress-practice-{uuid.uuid4()}"
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 1,
                "phase": "chat",
                "mastery_status_by_skill": {
                    "g1_counting_core": {
                        "status": "learning",
                    },
                },
                "student_profile": {
                    "active_scope": {
                        "current_skill_id": "g1_counting_core",
                        "chain_id": "g1_to_g2_addition",
                        "blocked_skill_ids": [],
                    },
                    "skill_mastery": {
                        "g1_counting_core": {
                            "status": "learning",
                        },
                    },
                    "promotion_history": [],
                },
            }
        }
    )

    summary = get_progress_summary(user_id)
    assert summary["user_id"] == user_id
    assert len(summary["skills"]) > 0

    g1_skill = next((s for s in summary["skills"] if s["skill_id"] == "g1_counting_core"), None)
    assert g1_skill is not None
    assert g1_skill["status"] == "learning"


def test_progress_api_endpoint(tmp_path, monkeypatch) -> None:
    """Progress API endpoint should return 200 with valid structure."""
    from deeptutor.api.routers.plugins_api import STATE_FILE, save_user_states

    monkeypatch.setattr("deeptutor.api.routers.plugins_api.STATE_FILE", tmp_path / "user_states.json")

    user_id = f"progress-api-{uuid.uuid4()}"
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 2,
                "phase": "practice",
                "mastery_status_by_skill": {
                    "g2_addition_core": {
                        "status": "mastered",
                    },
                },
                "student_profile": {
                    "active_scope": {
                        "current_skill_id": "g2_addition_core",
                        "blocked_skill_ids": [],
                    },
                    "skill_mastery": {
                        "g2_addition_core": {
                            "status": "mastered",
                        },
                    },
                    "promotion_history": [],
                },
            }
        }
    )

    with TestClient(_build_app()) as client:
        response = client.get(f"/api/v1/plugins/panda/progress/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert "recommended_next_action" in data
        assert "skills" in data
