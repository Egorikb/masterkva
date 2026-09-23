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
from deeptutor.services.curricular_lesson_runtime import ResolvedCurricularLesson


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
    for key in ("session_id", "lesson_id", "content_version", "part_index", "part_revision"):
        assert paused.json()["state"]["curricular"][key] == started.json()["state"]["curricular"][key]

    assert rejected_answer.status_code == 409
    assert rejected_answer.json()["detail"]["code"] == "resume_required"

    assert resumed.status_code == 200
    assert resumed.json()["state"]["phase"] == "curricular"
    assert resumed.json()["state"]["current_practice"]["attempts"] == 1
    for key in ("session_id", "lesson_id", "content_version", "part_index", "part_revision"):
        assert resumed.json()["state"]["curricular"][key] == started.json()["state"]["curricular"][key]

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


def test_curricular_request_ids_deduplicate_conflict_and_offer_reviewed_support() -> None:
    start_request = {**PILOT_START, "request_id": "b2b-start-1"}

    with _client() as client:
        started = _post(client, start_request)
        repeated_start = _post(client, start_request)
        session_id = started.json()["state"]["session_id"]
        part_revision = started.json()["state"]["curricular"]["part_revision"]
        answer = {
            "user_id": PILOT_START["user_id"],
            "message": "12",
            "action": "answer",
            "request_id": "b2b-answer-1",
            "session_id": session_id,
            "part_revision": part_revision,
        }
        first_wrong = _post(client, answer)
        repeated_wrong = _post(client, answer)
        conflict = _post(client, {**answer, "message": "11"})
        second_wrong = _post(client, {**answer, "request_id": "b2b-answer-2"})
        third_wrong = _post(client, {**answer, "request_id": "b2b-answer-3"})
        unparsed = _post(
            client,
            {**answer, "message": "", "request_id": "b2b-empty-1"},
        )
        hint = _post(
            client,
            {**answer, "message": "", "action": "hint", "request_id": "b2b-hint-1"},
        )
        paused = _post(
            client,
            {**answer, "message": "", "action": "pause", "request_id": "b2b-pause-1"},
        )
        resumed = _post(
            client,
            {**answer, "message": "", "action": "resume", "request_id": "b2b-resume-1"},
        )

    assert started.status_code == 200
    assert started.json()["replayed"] is False
    assert repeated_start.status_code == 200
    assert repeated_start.json()["replayed"] is True
    assert repeated_start.json()["state"]["session_id"] == session_id

    assert first_wrong.json()["state"]["current_practice"]["attempts"] == 1
    assert first_wrong.json()["state"]["curricular"]["incorrect_attempts"] == 1
    assert repeated_wrong.json()["replayed"] is True
    assert repeated_wrong.json()["state"]["current_practice"]["attempts"] == 1
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "request_id_conflict"
    assert second_wrong.json()["state"]["current_practice"]["attempts"] == 2

    third_payload = third_wrong.json()
    assert third_payload["state"]["current_practice"]["attempts"] == 3
    assert third_payload["state"]["curricular"]["incorrect_attempts"] == 3
    assert third_payload["state"]["practice_feedback"]["support_offered"] is True
    assert "разберём текущий пример" in third_payload["text"]
    assert "взрослого" in third_payload["text"]
    assert "Пауза" in third_payload["text"]
    assert "13" not in third_payload["text"]
    assert third_payload["state"]["curricular"]["mastery_awarded"] is False

    assert unparsed.json()["event_kind"] == "unparsed_input"
    assert unparsed.json()["state"]["practice_feedback"]["status"] == "invalid_input"
    assert unparsed.json()["state"]["current_practice"]["attempts"] == 3
    assert unparsed.json()["state"]["curricular"]["incorrect_attempts"] == 3
    assert hint.json()["event_kind"] == "help_request"
    assert hint.json()["state"]["current_practice"]["attempts"] == 3
    assert paused.json()["state"]["phase"] == "paused"
    assert resumed.json()["state"]["phase"] == "curricular"
    assert resumed.json()["state"]["current_practice"]["attempts"] == 3
    assert "request_journal" not in json.dumps(
        [started.json(), third_payload, hint.json(), resumed.json()],
        ensure_ascii=False,
    )


def test_ordered_retries_and_stale_parts_are_decided_before_dispatch(monkeypatch) -> None:
    resolved = ResolvedCurricularLesson(
        lesson_id="synthetic-ordered",
        content_version="test",
        lesson={
            "assessment": {
                "kind": "ordered",
                "parts": [
                    {"prompt": "Первая часть", "expected": ["1"]},
                    {"prompt": "Вторая часть", "expected": ["2"]},
                ],
            },
            "presentation": {"prompts": ["Первая часть", "Вторая часть"]},
            "solution_steps": ["Выполни текущую часть."],
            "hint": "Работай по порядку.",
        },
        mapping={},
    )
    monkeypatch.setattr(plugins_api.curricular_lesson_runtime, "resolve", lambda *_: resolved)
    start = {
        "user_id": "b2b-ordered-child",
        "message": "начать",
        "mode": "curricular",
        "action": "start",
        "lesson_id": resolved.lesson_id,
        "content_version": resolved.content_version,
        "request_id": "ordered-start-1",
    }

    with _client() as client:
        started = _post(client, start)
        session_id = started.json()["state"]["session_id"]
        first_answer = {
            "user_id": start["user_id"],
            "message": "1",
            "action": "answer",
            "request_id": "ordered-answer-1",
            "session_id": session_id,
            "part_revision": 0,
        }
        answered = _post(client, first_answer)
        advance = {
            "user_id": start["user_id"],
            "message": "",
            "action": "advance",
            "request_id": "ordered-advance-1",
            "session_id": session_id,
            "part_revision": 0,
        }
        advanced = _post(client, advance)
        repeated_advance = _post(client, advance)
        repeated_answer = _post(client, first_answer)
        repeated_start = _post(client, start)
        current_part_after_replays = plugins_api.get_user_state(start["user_id"])[
            "curricular_session"
        ]["part_index"]
        stale = _post(
            client,
            {**first_answer, "message": "2", "request_id": "ordered-late-1"},
        )
        conflict = _post(client, {**advance, "message": "другое"})
        next_wrong = _post(
            client,
            {
                **first_answer,
                "request_id": "ordered-answer-2",
                "part_revision": 1,
            },
        )
        restarted = _post(client, {**start, "request_id": "ordered-start-2"})
        stale_session = _post(
            client,
            {
                **first_answer,
                "request_id": "ordered-old-session",
                "part_revision": 1,
            },
        )

    assert answered.json()["state"]["curricular"]["awaiting_advance"] is True
    assert advanced.json()["state"]["curricular"]["part_index"] == 1
    assert advanced.json()["state"]["curricular"]["part_revision"] == 1
    assert repeated_advance.json()["replayed"] is True
    assert repeated_advance.json()["state"]["curricular"]["part_index"] == 1
    assert repeated_answer.json()["replayed"] is True
    assert repeated_answer.json()["state"]["curricular"]["part_index"] == 0
    assert repeated_start.json()["replayed"] is True
    assert current_part_after_replays == 1
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "stale_part"
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "request_id_conflict"
    assert next_wrong.json()["state"]["current_practice"]["attempts"] == 1
    assert restarted.json()["state"]["session_id"] != session_id
    assert stale_session.status_code == 409
    assert stale_session.json()["detail"]["code"] == "stale_session"


def test_blank_legacy_answer_is_not_a_math_error_or_remediation_step() -> None:
    user_id = "b2b-legacy-empty-child"
    state = _legacy_state(user_id)
    state["session_id"] = "legacy-session-1"
    plugins_api.save_user_states({user_id: state})

    with _client() as client:
        response = _post(
            client,
            {
                "user_id": user_id,
                "message": "",
                "action": "answer",
                "request_id": "legacy-empty-1",
                "session_id": state["session_id"],
            },
        )
        repeated = _post(
            client,
            {
                "user_id": user_id,
                "message": "",
                "action": "answer",
                "request_id": "legacy-empty-1",
                "session_id": state["session_id"],
            },
        )

    assert response.status_code == 200
    assert response.json()["event_kind"] == "unparsed_input"
    assert response.json()["state"]["phase"] == "practice"
    assert response.json()["state"]["current_practice"]["attempts"] == 0
    assert response.json()["state"]["practice_feedback"] is None
    assert repeated.json()["replayed"] is True
    assert plugins_api.remediation_engine.get_state(user_id) is None
