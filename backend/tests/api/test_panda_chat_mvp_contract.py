from __future__ import annotations

import importlib
import uuid

import pytest

FastAPI = pytest.importorskip("fastapi").FastAPI
TestClient = pytest.importorskip("fastapi.testclient").TestClient

plugins_api_module = importlib.import_module("deeptutor.api.routers.plugins_api")
plugins_router = plugins_api_module.router


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(plugins_router, prefix="/api/v1/plugins")
    return app


def test_diagnostic_failure_routes_to_explanation_phase_with_weak_topic() -> None:
    user_id = f"mvp-explanation-phase-{uuid.uuid4()}"

    with TestClient(_build_app()) as client:
        start = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "диагностика", "name": "Алиса", "grade": 1},
        )
        assert start.status_code == 200

        response = None
        for _ in range(7):
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


def test_start_from_explanation_creates_practice_from_weak_topic() -> None:
    user_id = f"mvp-start-practice-{uuid.uuid4()}"
    weak_topic = {
        "grade": 1,
        "topic_id": "g1_t03",
        "topic": "СЛОЖЕНИЕ/ВЫЧИТАНИЕ",
        "source_question_id": "g1_t03_q01",
    }
    plugins_api_module.update_user_state(
        user_id,
        {
            "name": "Алиса",
            "grade": 1,
            "path_choice": "course",
            "in_learning": True,
            "actual_grade": 1,
            "phase": "explanation",
            "weak_topic": weak_topic,
            "current_practice": None,
            "report": None,
        },
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


def test_panda_chat_response_always_contains_visual_field() -> None:
    user_id = f"mvp-visual-contract-{uuid.uuid4()}"

    with TestClient(_build_app()) as client:
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={
                "user_id": user_id,
                "message": "курс",
                "name": "Алиса",
                "grade": 1,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert "text" in body
    assert "state" in body
    assert "visual" in body
    assert body["visual"] is None or isinstance(body["visual"], dict)


def test_practice_answer_moves_to_report_without_regenerating_practice() -> None:
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
    plugins_api_module.update_user_state(
        user_id,
        {
            "name": "Алиса",
            "grade": 1,
            "path_choice": "course",
            "in_learning": True,
            "actual_grade": 1,
            "phase": "practice",
            "weak_topic": weak_topic,
            "current_practice": current_practice,
            "report": None,
        },
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
