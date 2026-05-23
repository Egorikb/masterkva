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


def test_diagnostic_start_uses_teacher_voice(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "Я твой преподаватель. Давай начнём диагностику спокойно и шаг за шагом.")
    user_id = f"mvp-start-teacher-voice-{uuid.uuid4()}"

    with TestClient(_build_app()) as client:
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "диагностика", "name": "Яна", "grade": 3},
        )

    payload = response.json()
    assert payload["state"]["phase"] == "diagnostic"
    assert "я твой преподаватель" in payload["text"].lower()
    assert "Начинаем диагностику" not in payload["text"]
    assert payload["visual"]["type"] == "number_bond"
    assert payload["visual"]["parts"] == [8, 5]
    assert payload["visual"]["operation"] == "add"




def test_diagnostic_completion_waits_for_manual_continue(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
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

    payload = response.json()
    state = payload["state"]
    assert state["phase"] == "explanation"
    assert isinstance(state["weak_topic"], dict)
    assert state["current_practice"] is None
    assert state["report"] is None
    assert "Скажи «давай»" in payload["text"]
    assert "Начнём с темы" not in payload["text"]
    assert "Вот первый пример" not in payload["text"]


def test_start_from_explanation_creates_practice_from_weak_topic(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
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
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
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
    assert "TEACHER_OK" in response.json()["text"]


def test_wrong_practice_answer_stays_in_live_practice(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"mvp-practice-retry-{uuid.uuid4()}"
    weak_topic = {
        "grade": 1,
        "topic_id": "g1_t01",
        "topic": "Счёт до 10",
        "source_question_id": "g1_t01_q01",
    }
    current_practice = {
        "id": "g1_t01_p01",
        "topic_id": "g1_t01",
        "title": "Счёт до 10",
        "question": "Сколько всего: 3 и 2?",
        "answer": "5",
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
            json={"user_id": user_id, "message": "9"},
        )

    payload = response.json()
    assert payload["state"]["phase"] == "practice"
    assert payload["state"]["current_practice"]["attempts"] == 1
    assert payload["state"]["practice_feedback"]["is_correct"] is False
    assert payload["state"]["report"]["practice_result"] == "needs_review"
    assert payload["visual"]["type"] == "number_bond"
    assert payload["visual"]["parts"] == [3, 2]
    assert payload["visual"]["operation"] == "add"
    assert "TEACHER_OK" in payload["text"]


def test_report_followup_continues_to_next_practice(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"mvp-report-followup-{uuid.uuid4()}"
    weak_topic = {
        "grade": 1,
        "topic_id": "g1_t02",
        "topic": "Следующее число",
        "source_question_id": "g1_t02_q01",
    }
    report = {
        "summary": "В этой попытке по теме 'Следующее число' есть ошибка. Одна ошибка не означает, что тема не понята.",
        "weak_topic": weak_topic,
        "practice_result": "needs_review",
        "recommendations": [
            "Повтори объяснение и попробуй ещё раз",
            "Одна ошибка не даёт повода делать вывод о знании всей темы",
        ],
    }
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 1,
                "phase": "report",
                "weak_topic": weak_topic,
                "current_practice": {
                    "id": "g1_t02_p01",
                    "topic_id": "g1_t02",
                    "title": "Следующее число",
                    "question": "Какое число идёт после 6?",
                    "answer": "7",
                    "attempts": 1,
                },
                "practice_feedback": {"is_correct": False},
                "report": report,
            }
        }
    )

    with TestClient(_build_app()) as client:
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "давай"},
        )

    payload = response.json()
    assert payload["state"]["phase"] == "practice"
    assert payload["state"]["current_practice"]["topic_id"] == "g1_t02"
    assert payload["state"]["current_practice"]["question"] != "Какое число идёт после 6?"
    assert payload["state"]["practice_feedback"] is None
    assert payload["state"]["report"] is None
    assert payload["visual"]["type"] == "question"
    assert "TEACHER_OK" in payload["text"]
