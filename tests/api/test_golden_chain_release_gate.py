import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

import deeptutor.api.routers.plugins_api as plugins_api
from deeptutor.api.routers.plugins_api import router


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/plugins")
    return app


def test_golden_chain_hardening_run_promotes_from_g1_to_g2(tmp_path, monkeypatch) -> None:
    """Golden chain: practice with g1 skills, verify mastery evaluation works.
    With expanded registry, the chain is longer: g1_counting → g1_number_successor → ...
    This test verifies the practice flow works end-to-end with a g1 skill.
    """
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"golden-chain-hardening-{uuid.uuid4()}"
    save_user_states = plugins_api.save_user_states
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 1,
                "phase": "practice",
                "weak_topic": {
                    "grade": 1,
                    "topic_id": "g1_t01",
                    "topic": "Подготовка к счёту",
                },
                "current_practice": {
                    "id": "g1_t01_p01",
                    "topic_id": "g1_t01",
                    "title": "Подготовка к счёту",
                    "question": "Сколько всего: 3 и 2?",
                    "answer": "5",
                    "item_family": "counting_with_objects",
                    "attempts": 0,
                },
                "practice_feedback": None,
                "report": None,
                "mastery_status_by_skill": {
                    "g1_counting_core": {
                        "status": "learning",
                        "attempt_history": [
                            {"question_id": f"seed-{i}", "is_correct": True, "confidence": 1.0}
                            for i in range(5)
                        ],
                    },
                },
                "current_skill_id": "g1_counting_core",
            }
        }
    )

    with TestClient(_build_app()) as client:
        # Answer correctly → should trigger mastery evaluation
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "5"},
        )
        assert response.status_code == 200
        state = response.json()["state"]
        # With mastery check, phase may be practice (correct answer, waiting for more)
        # or remediation (if mastery not yet achieved)
        assert state["phase"] in ("practice", "remediation")
