from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from deeptutor.api.routers.plugins_api import router, save_user_states
import deeptutor.api.routers.plugins_api as plugins_api


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/plugins")
    return app


def test_diagnostic_failure_routes_to_explanation_phase_with_weak_topic(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    user_id = f"mvp-explanation-phase-{uuid.uuid4()}"

    with TestClient(_build_app()) as client:
        start = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "диагностика", "name": "Алиса", "grade": 1},
        )
        assert start.status_code == 200
        assert start.json()["state"]["phase"] == "diagnostic"

        response = start
        for _ in range(4):
            response = client.post(
                "/api/v1/plugins/panda/chat",
                json={"user_id": user_id, "message": "999"},
            )
            assert response.status_code == 200

    state = response.json()["state"]
    assert state["phase"] == "explanation"
    assert isinstance(state["weak_topic"], dict)
    assert state["current_practice"] is None
    assert state["report"] is None


def test_explanation_phase_uses_grade_specific_learning_context(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_explanation", lambda **kwargs: "TEACHER_OK")
    user_id = f"mvp-rag-context-{uuid.uuid4()}"

    with TestClient(_build_app()) as client:
        start = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "диагностика", "name": "Алиса", "grade": 1},
        )
        assert start.status_code == 200

        response = start
        for _ in range(4):
            response = client.post(
                "/api/v1/plugins/panda/chat",
                json={"user_id": user_id, "message": "999"},
            )
            assert response.status_code == 200

    payload = response.json()
    state = payload["state"]
    assert state["phase"] == "explanation"
    assert state["learning_context"]
    assert all(item["grade"] == 1 for item in state["learning_context"])
    assert any(item["source_file"].startswith("grade_1") for item in state["learning_context"])
    assert state["teacher_explanation"] == "TEACHER_OK"
    assert "TEACHER_OK" in payload["text"]



def test_start_from_explanation_creates_practice_from_weak_topic(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    user_id = f"mvp-start-practice-{uuid.uuid4()}"
    weak_topic = {
        "grade": 1,
        "topic_id": "g1_t03",
        "topic": "СЛОЖЕНИЕ/ВЫЧИТАНИЕ",
        "source_question_id": "g1_t03_q01",
    }
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 1,
                "phase": "explanation",
                "weak_topic": weak_topic,
                "current_practice": None,
                "report": None,
            }
        }
    )

    with TestClient(_build_app()) as client:
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "начать"},
        )

    state = response.json()["state"]
    assert state["phase"] == "practice"
    assert state["current_practice"]["topic_id"] == "g1_t03"
    assert state["current_practice"]["answer"] != "42"


def test_practice_answer_moves_to_report_without_regenerating_practice(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    user_id = f"mvp-practice-to-report-{uuid.uuid4()}"
    weak_topic = {
        "grade": 1,
        "topic_id": "g1_t03",
        "topic": "СЛОЖЕНИЕ/ВЫЧИТАНИЕ",
        "source_question_id": "g1_t03_q01",
    }
    current_practice = {
        "id": "g1_t03_p01",
        "topic_id": "g1_t03",
        "title": "СЛОЖЕНИЕ/ВЫЧИТАНИЕ",
        "question": "4 + 3 = ?",
        "answer": "7",
        "attempts": 0,
    }
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 1,
                "phase": "practice",
                "weak_topic": weak_topic,
                "current_practice": current_practice,
                "report": None,
            }
        }
    )

    with TestClient(_build_app()) as client:
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "7"},
        )

    state = response.json()["state"]
    assert state["phase"] == "report"
    assert state["current_practice"]["id"] == "g1_t03_p01"
    assert state["current_practice"]["attempts"] == 1
    assert state["practice_feedback"]["is_correct"] is True
    assert state["report"]["practice_result"] == "success"
