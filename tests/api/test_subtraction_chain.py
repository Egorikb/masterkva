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


def test_subtraction_chain_hardening_run(tmp_path, monkeypatch) -> None:
    """Full hardening run for g1 -> g2_subtraction chain."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"subtraction-chain-hardening-{uuid.uuid4()}"
    seed_history_g1 = [
        {"question_id": f"g1-seed-{idx}", "is_correct": True, "confidence": 1.0}
        for idx in range(1, 5)
    ]
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
                    "question": "15 - 7 = ?",
                    "answer": "8",
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
        # Step 1: answer g2 subtraction practice correctly -> mastery_check
        g2_mastery = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "8"},
        )
        assert g2_mastery.status_code == 200
        g2_payload = g2_mastery.json()
        assert g2_payload["state"]["phase"] == "mastery_check"
        assert g2_payload["state"]["current_skill_id"] == "g2_subtraction_core"
        assert g2_payload["state"]["mastery_gate_status"] == "mastered"
        assert g2_payload["state"]["promotion_eligible"] is True
        assert g2_payload["state"]["blocked_skill_ids"] == []
        assert g2_payload["state"]["mastery_check_result"]["decision"] == "mastered"


def test_subtraction_chain_coverage_passes() -> None:
    """Coverage-run should pass for g2_subtraction_core."""
    from deeptutor.services.coverage_runner import run_coverage

    report = run_coverage()
    skills = {s["skill_id"]: s for s in report["skills"]}

    assert "g2_subtraction_core" in skills
    sub = skills["g2_subtraction_core"]

    # Should not have blocking gaps
    assert not sub["blocking_gaps"], f"Blocking gaps: {sub['blocking_gaps']}"

    # Visual policy should be valid
    assert sub["coverage"].get("visual_policy") == "present"
    assert sub["coverage"].get("visual_type") == "number_bond"

    # Should have diagnostic pool
    assert sub["coverage"].get("diagnostic_pool") == "present"

    # Should have remediation targets
    assert sub["coverage"].get("remediation") == "present"
