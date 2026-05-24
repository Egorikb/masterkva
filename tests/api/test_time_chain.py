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


def test_time_chain_hardening_run(tmp_path, monkeypatch) -> None:
    """Full hardening run for g2 -> g3_time chain: practice -> mastery -> auto-promotion."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"time-chain-hardening-{uuid.uuid4()}"
    seed_history_g3 = [
        {"question_id": f"g3-seed-{idx}", "is_correct": True, "confidence": 1.0}
        for idx in range(1, 5)
    ]
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 3,
                "phase": "practice",
                "weak_topic": {
                    "grade": 3,
                    "topic_id": "g3_t01",
                    "topic": "Время (часы, минуты, секунды)",
                    "source_question_id": "g3_t01_q01",
                },
                "current_practice": {
                    "id": "g3_t01_p01",
                    "topic_id": "g3_t01",
                    "title": "Время (часы, минуты, секунды)",
                    "question": "Сколько минут в 2 часах?",
                    "answer": "120",
                    "item_family": "time_unit_conversion",
                    "attempts": 0,
                },
                "practice_feedback": None,
                "report": None,
                "blocked_skill_ids": [],
                "remediation_targets": {"time_unit_conversion": "time_unit_table"},
                "mastery_status_by_skill": {
                    "g3_time_measurement_core": {
                        "status": "learning",
                        "attempt_history": seed_history_g3,
                    },
                },
                "current_skill_id": "g3_time_measurement_core",
                "current_skill_version": "v1",
                "current_skill_mode": "shadow",
                "current_topic_id": "g3_t01",
                "learning_mode_active": True,
                "mastery_check_pending": False,
                "promotion_eligible": False,
            }
        }
    )

    with TestClient(_build_app()) as client:
        # Step 1: answer practice correctly → mastery + auto-promotion to g4
        mastery = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "120"},
        )
        assert mastery.status_code == 200
        payload = mastery.json()
        state = payload["state"]
        assert state["mastery_gate_status"] == "mastered"
        assert state["promotion_eligible"] is True
        assert state["mastery_check_result"]["decision"] == "mastered"
        # Auto-promoted to g4_place_value_core (next_skill of g3)
        assert state["phase"] == "practice"
        assert state["current_skill_id"] == "g4_place_value_core"
        assert state["current_practice"]["topic_id"] == "g4_t01"
        assert state["student_profile"]["promotion_history"][-1]["from_skill_id"] == "g3_time_measurement_core"
        assert state["student_profile"]["promotion_history"][-1]["to_skill_id"] == "g4_place_value_core"


def test_time_chain_coverage_passes() -> None:
    """Coverage-run should pass for g3_time_measurement_core."""
    from deeptutor.services.coverage_runner import run_coverage

    report = run_coverage()
    skills = {s["skill_id"]: s for s in report["skills"]}

    assert "g3_time_measurement_core" in skills
    g3 = skills["g3_time_measurement_core"]

    # Should not have blocking gaps
    assert not g3["blocking_gaps"], f"Blocking gaps: {g3['blocking_gaps']}"

    # Visual policy should be valid
    assert g3["coverage"].get("visual_policy") == "present"
    assert g3["coverage"].get("visual_type") == "clock_face"

    # Should have diagnostic pool
    assert g3["coverage"].get("diagnostic_pool") == "present"

    # Should have remediation targets
    assert g3["coverage"].get("remediation") == "present"
