from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import json
import socket
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from fastapi import FastAPI
import uvicorn

from deeptutor.api.routers import plugins_api


PILOT_START = {
    "user_id": "b2a-curricular-child",
    "message": "начать",
    "mode": "curricular",
    "action": "start",
    "lesson_id": "g1-t12-l01",
    "content_version": "2.0",
}


@dataclass(frozen=True)
class _Response:
    status_code: int
    payload: dict

    def json(self) -> dict:
        return self.payload


class _HttpClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def post(self, path: str, *, json_payload: dict) -> _Response:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(json_payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as exc:
            return _Response(exc.code, json.loads(exc.read().decode("utf-8")))
        with response:
            return _Response(response.status, json.loads(response.read().decode("utf-8")))


@contextmanager
def _client():
    app = FastAPI()
    app.include_router(plugins_api.router, prefix="/api/v1/plugins")
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.01)
    if not server.started:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()
        raise RuntimeError("HTTP acceptance server did not start")
    try:
        yield _HttpClient(f"http://127.0.0.1:{port}")
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()
        if thread.is_alive():
            raise RuntimeError("HTTP acceptance server did not stop")


def _post(client: _HttpClient, payload: dict) -> _Response:
    return client.post("/api/v1/plugins/panda/chat", json_payload=payload)


def _legacy_state(user_id: str) -> dict:
    return {
        "name": "Аня",
        "grade": 1,
        "onboarding_complete": True,
        "phase": "practice",
        "path_choice": "kungfu",
        "in_learning": True,
        "learning_mode_active": True,
        "weak_topic": {
            "grade": 1,
            "topic_id": "g1_t03",
            "topic": "Сложение до 10",
            "source_question_id": "g1_t03_q01",
        },
        "current_practice": {
            "id": "g1_t03_p01",
            "topic_id": "g1_t03",
            "title": "Сложение до 10",
            "question": "4 + 3 = ?",
            "answer": "7",
            "attempts": 0,
        },
        "practice_feedback": None,
        "report": None,
        "student_profile": {"user_id": user_id},
    }


def test_curricular_actions_keep_attempts_and_part_under_server_control() -> None:
    with _client() as client:
        started = _post(client, PILOT_START)
        wrong = _post(
            client,
            {"user_id": PILOT_START["user_id"], "message": "12", "action": "answer"},
        )
        hint = _post(
            client,
            {"user_id": PILOT_START["user_id"], "message": "13", "action": "hint"},
        )
        rephrased = _post(
            client,
            {"user_id": PILOT_START["user_id"], "message": "13", "action": "rephrase"},
        )
        paused = _post(
            client,
            {"user_id": PILOT_START["user_id"], "message": "13", "action": "pause"},
        )
        rejected_answer = _post(
            client,
            {"user_id": PILOT_START["user_id"], "message": "13", "action": "answer"},
        )
        resumed = _post(
            client,
            {"user_id": PILOT_START["user_id"], "message": "13", "action": "resume"},
        )
        correct = _post(
            client,
            {"user_id": PILOT_START["user_id"], "message": "13", "action": "answer"},
        )
        help_after_completion = _post(
            client,
            {"user_id": PILOT_START["user_id"], "message": "", "action": "hint"},
        )

    assert started.status_code == 200
    assert wrong.json()["state"]["curricular"]["part_index"] == 0
    assert wrong.json()["state"]["current_practice"]["attempts"] == 1
    assert wrong.json()["state"]["practice_feedback"]["status"] == "incorrect"

    for response in (hint, rephrased):
        assert response.status_code == 200
        assert response.json()["state"]["current_practice"]["attempts"] == 1
        assert response.json()["state"]["curricular"]["part_index"] == 0
        assert "13" not in response.json()["text"]
    assert hint.json()["text"] == "Как разделить 5, чтобы сначала получить 10?"
    assert "8 + 5" in rephrased.json()["text"]

    assert paused.status_code == 200
    assert paused.json()["state"]["phase"] == "paused"
    assert paused.json()["state"]["current_practice"]["attempts"] == 1
    assert paused.json()["state"]["curricular"] == started.json()["state"]["curricular"]

    assert rejected_answer.status_code == 409
    assert rejected_answer.json()["detail"]["code"] == "resume_required"

    assert resumed.status_code == 200
    assert resumed.json()["state"]["phase"] == "curricular"
    assert resumed.json()["state"]["current_practice"]["attempts"] == 1
    assert resumed.json()["state"]["curricular"] == started.json()["state"]["curricular"]

    assert correct.status_code == 200
    assert correct.json()["state"]["current_practice"]["attempts"] == 2
    assert correct.json()["state"]["curricular"]["lesson_complete"] is True
    assert help_after_completion.status_code == 200
    assert help_after_completion.json()["text"] == "Урок уже завершён."
    assert help_after_completion.json()["state"]["current_practice"]["attempts"] == 2


def test_invalid_explicit_action_does_not_change_state() -> None:
    user_id = "b2a-invalid-action-child"
    plugins_api.save_user_states({user_id: _legacy_state(user_id)})
    before = deepcopy(plugins_api.get_user_state(user_id))

    with _client() as client:
        resume = _post(
            client,
            {"user_id": user_id, "message": "", "action": "resume"},
        )
        response = _post(
            client,
            {"user_id": user_id, "message": "", "action": "advance"},
        )

    assert resume.status_code == 409
    assert resume.json()["detail"]["code"] == "not_paused"
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "action_not_available_in_current_phase"
    assert plugins_api.get_user_state(user_id) == before


def test_legacy_explicit_help_pause_resume_and_answer_are_distinct(monkeypatch) -> None:
    user_id = "b2a-legacy-actions-child"
    plugins_api.save_user_states({user_id: _legacy_state(user_id)})
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "Верно!")

    with _client() as client:
        hint = _post(client, {"user_id": user_id, "message": "7", "action": "hint"})
        rephrased = _post(client, {"user_id": user_id, "message": "7", "action": "rephrase"})
        paused = _post(client, {"user_id": user_id, "message": "7", "action": "pause"})
        blocked = _post(client, {"user_id": user_id, "message": "7", "action": "answer"})
        resumed = _post(client, {"user_id": user_id, "message": "7", "action": "resume"})
        answered = _post(client, {"user_id": user_id, "message": "7", "action": "answer"})

    for response in (hint, rephrased):
        assert response.status_code == 200
        assert response.json()["state"]["current_practice"]["attempts"] == 0
        assert "answer" not in response.json()["state"]["current_practice"]
        assert response.json()["visual"] is None
    assert "7" not in hint.json()["text"]
    assert "4 + 3" in rephrased.json()["text"]
    assert "7" not in rephrased.json()["text"]

    assert paused.status_code == 200
    assert paused.json()["state"]["phase"] == "paused"
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "resume_required"
    assert resumed.status_code == 200
    assert resumed.json()["state"]["phase"] == "practice"
    assert resumed.json()["state"]["current_practice"]["attempts"] == 0
    assert resumed.json()["state"]["practice_feedback"] is None
    assert answered.status_code == 200
    assert answered.json()["state"]["practice_feedback"]["is_correct"] is True


def test_legacy_text_pause_and_unlabelled_resume_stay_compatible() -> None:
    user_id = "b2a-legacy-text-child"
    plugins_api.save_user_states({user_id: _legacy_state(user_id)})

    with _client() as client:
        paused = _post(client, {"user_id": user_id, "message": "стоп"})
        resumed = _post(client, {"user_id": user_id, "message": "7"})

    assert paused.status_code == 200
    assert paused.json()["state"]["phase"] == "paused"
    assert resumed.status_code == 200
    assert resumed.json()["state"]["phase"] == "practice"
    assert resumed.json()["state"]["current_practice"]["attempts"] == 0
    assert resumed.json()["state"]["practice_feedback"] is None


def test_switch_from_curricular_restores_legacy_without_assessing_message() -> None:
    user_id = PILOT_START["user_id"]
    legacy = _legacy_state(user_id)
    plugins_api.save_user_states({user_id: legacy})

    with _client() as client:
        started = _post(client, PILOT_START)
        switched = _post(
            client,
            {
                "user_id": user_id,
                "message": "7",
                "mode": "kungfu",
                "action": "answer",
            },
        )

    assert started.status_code == 200
    assert switched.status_code == 200
    assert switched.json()["state"]["phase"] == "practice"
    assert switched.json()["state"]["current_practice"]["id"] == "g1_t03_p01"
    assert switched.json()["state"]["current_practice"]["attempts"] == 0
    assert switched.json()["state"]["practice_feedback"] is None
    assert plugins_api.get_user_state(user_id).get("curricular_session") is None
