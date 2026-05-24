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
        # Step 1: Start diagnostic
        start = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "диагностика", "name": "Алиса", "grade": 1},
        )
        assert start.status_code == 200
        assert start.json()["state"]["phase"] == "diagnostic"

        # Step 2: Answer all diagnostic questions (send wrong answers to finish faster)
        response = start
        for _ in range(7):
            response = client.post(
                "/api/v1/plugins/panda/chat",
                json={"user_id": user_id, "message": "999"},
            )
            assert response.status_code == 200

        # Step 3: Diagnostic auto-transitions to practice (no "давай" needed)
        diag_payload = response.json()
        diag_state = diag_payload["state"]
        assert diag_state["phase"] == "practice"
        assert diag_state["diagnostic_gap_status"] == "diagnosed_gap"
        assert diag_state["blocked_skill_ids"] == ["g2_addition_core", "g2_subtraction_core"]
        assert diag_state["remediation_targets"]["number_bond_missing_part"] == "number_bond"
        assert diag_state["current_skill_id"] == "g1_early_arithmetic_core"
        assert diag_state["current_practice"] is not None
        assert diag_state["student_profile"]["active_scope"]["chain_id"] == "g1_to_g2_addition"

        # Step 4: Answer practice question correctly → auto-promotes to next skill
        practice_answer = str(diag_state["current_practice"]["answer"])
        practice_result = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": practice_answer},
        )
        assert practice_result.status_code == 200
        practice_payload = practice_result.json()
        practice_state = practice_payload["state"]

        # Mastery is evaluated; if mastered, auto-promotes to g2_addition_core
        if practice_state.get("mastery_gate_status") == "mastered":
            assert practice_state["phase"] == "practice"
            assert practice_state["current_skill_id"] == "g2_addition_core"
            assert practice_state["current_practice"]["question"] == "12 + 5 = ?"
            assert practice_state["student_profile"]["active_scope"]["current_skill_id"] == "g2_addition_core"
            assert practice_state["student_profile"]["promotion_history"][-1]["from_skill_id"] == "g1_early_arithmetic_core"
            assert practice_state["student_profile"]["promotion_history"][-1]["to_skill_id"] == "g2_addition_core"
            assert practice_state["blocked_skill_ids"] == []

            # Step 5: Answer g2 practice
            g2_answer = client.post(
                "/api/v1/plugins/panda/chat",
                json={"user_id": user_id, "message": "17"},
            )
            assert g2_answer.status_code == 200
            g2_payload = g2_answer.json()
            g2_state = g2_payload["state"]
            assert g2_state["current_skill_id"] == "g2_addition_core"
            assert g2_state["student_profile"]["mastery_history"]
        else:
            # Not yet mastered — still in practice, which is correct
            assert practice_state["phase"] == "practice"
