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


def test_golden_chain_release_gate_acceptance_suite(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"golden-chain-release-gate-{uuid.uuid4()}"
    seed_history_g1 = [
        {"question_id": f"g1-seed-{idx}", "is_correct": True, "confidence": 1.0}
        for idx in range(1, 5)
    ]
    seed_history_g2 = [
        {"question_id": f"g2-seed-{idx}", "is_correct": True, "confidence": 1.0}
        for idx in range(1, 5)
    ]
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 1,
                "phase": "chat",
                "practice_feedback": None,
                "report": None,
                "mastery_status_by_skill": {
                    "g1_early_arithmetic_core": {
                        "status": "learning",
                        "attempt_history": seed_history_g1,
                    },
                    "g2_addition_core": {
                        "status": "learning",
                        "attempt_history": seed_history_g2,
                    },
                    "g2_subtraction_core": {
                        "status": "learning",
                        "attempt_history": seed_history_g2,
                    },
                },
            }
        }
    )

    with TestClient(_build_app()) as client:
        start = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "диагностика", "name": "Алиса", "grade": 1},
        )
        assert start.status_code == 200
        assert start.json()["state"]["phase"] == "diagnostic"

        response = start
        for _ in range(7):
            response = client.post(
                "/api/v1/plugins/panda/chat",
                json={"user_id": user_id, "message": "999"},
            )
            assert response.status_code == 200

        diag_payload = response.json()
        diag_state = diag_payload["state"]
        assert diag_state["phase"] == "explanation"
        assert diag_state["diagnostic_gap_status"] == "diagnosed_gap"
        assert diag_state["blocked_skill_ids"] == ["g2_addition_core", "g2_subtraction_core"]
        assert diag_state["remediation_targets"]["number_bond_missing_part"] == "number_bond"

        continue_response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "давай"},
        )
        assert continue_response.status_code == 200
        continue_payload = continue_response.json()
        continue_state = continue_payload["state"]
        assert continue_state["phase"] == "practice"
        assert continue_state["current_skill_id"] == "g1_early_arithmetic_core"
        assert continue_state["blocked_skill_ids"] == ["g2_addition_core", "g2_subtraction_core"]
        assert continue_state["current_practice"] is not None
        assert continue_state["student_profile"]["active_scope"]["chain_id"] == "g1_to_g2_addition"

        practice_answer = str(continue_state["current_practice"]["answer"])
        mastery_result = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": practice_answer},
        )
        assert mastery_result.status_code == 200
        mastery_payload = mastery_result.json()
        mastery_state = mastery_payload["state"]
        assert mastery_state["phase"] == "mastery_check"
        assert mastery_state["mastery_gate_status"] == "mastered"
        assert mastery_state["promotion_eligible"] is True
        assert mastery_state["blocked_skill_ids"] == []
        assert mastery_state["mastery_check_result"]["decision"] == "mastered"

        promote_response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "давай"},
        )
        assert promote_response.status_code == 200
        promote_payload = promote_response.json()
        promote_state = promote_payload["state"]
        assert promote_state["phase"] == "practice"
        assert promote_state["current_skill_id"] == "g2_addition_core"
        assert promote_state["current_practice"]["question"] == "12 + 5 = ?"
        assert promote_state["student_profile"]["active_scope"]["current_skill_id"] == "g2_addition_core"
        assert promote_state["student_profile"]["promotion_history"][-1]["from_skill_id"] == "g1_early_arithmetic_core"
        assert promote_state["student_profile"]["promotion_history"][-1]["to_skill_id"] == "g2_addition_core"
        assert promote_state["blocked_skill_ids"] == []

        g2_answer = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "17"},
        )
        assert g2_answer.status_code == 200
        g2_payload = g2_answer.json()
        g2_state = g2_payload["state"]
        assert g2_state["phase"] == "mastery_check"
        assert g2_state["current_skill_id"] == "g2_addition_core"
        assert g2_state["mastery_gate_status"] == "mastered"
        assert g2_state["promotion_eligible"] is True
        assert g2_state["blocked_skill_ids"] == []
        assert g2_state["student_profile"]["mastery_history"]
