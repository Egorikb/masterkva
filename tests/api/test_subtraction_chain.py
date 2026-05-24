from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

import deeptutor.api.routers.plugins_api as plugins_api
from deeptutor.api.routers.plugins_api import router, save_user_states


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/plugins")
    return app


def test_subtraction_chain_release_gate(tmp_path, monkeypatch) -> None:
    """Full release gate: practice -> mastery (auto, no "давай") for subtraction chain.
    g2_subtraction_core has no next_skills, so after mastery we stay in practice."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"subtraction-release-gate-{uuid.uuid4()}"
    seed_history_g2 = [
        {"question_id": f"g2-sub-seed-{idx}", "is_correct": True, "confidence": 1.0}
        for idx in range(1, 5)
    ]
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 2,
                "phase": "practice",
                "weak_topic": {
                    "grade": 2,
                    "topic_id": "g2_t02",
                    "topic": "Сложение и вычитание до 100",
                    "source_question_id": "g2_t02_q01",
                },
                "current_practice": {
                    "id": "g2_t02_p01",
                    "topic_id": "g2_t02",
                    "title": "Сложение и вычитание до 100",
                    "question": "13 - 6 = ?",
                    "answer": "7",
                    "item_family": "subtraction_within_10_part_whole",
                    "attempts": 0,
                },
                "practice_feedback": None,
                "report": None,
                "blocked_skill_ids": [],
                "remediation_targets": {"subtraction_within_10_part_whole": "number_bond"},
                "mastery_status_by_skill": {
                    "g2_subtraction_core": {
                        "status": "learning",
                        "attempt_history": seed_history_g2,
                    },
                },
                "current_skill_id": "g2_subtraction_core",
                "current_skill_version": "v1",
                "current_skill_mode": "shadow",
                "current_topic_id": "g2_t02",
                "learning_mode_active": True,
                "mastery_check_pending": False,
                "promotion_eligible": False,
            }
        }
    )

    with TestClient(_build_app()) as client:
        # Step 1: answer practice correctly → mastery evaluated, auto-promoted or stays in practice
        mastery = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "7"},
        )
        assert mastery.status_code == 200
        payload = mastery.json()
        state = payload["state"]
        assert state["mastery_gate_status"] == "mastered"
        assert state["promotion_eligible"] is True
        assert state["mastery_check_result"]["decision"] == "mastered"
        assert state["current_skill_id"] == "g2_subtraction_core"
        # g2_subtraction_core has no next_skills, so stays in practice (teacher continues)
        assert state["phase"] == "practice"
