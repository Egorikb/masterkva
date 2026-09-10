from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from deeptutor.api.routers import plugins_api


PILOT = {
    "user_id": "b1-child",
    "message": "начать",
    "mode": "curricular",
    "action": "start",
    "lesson_id": "g1-t12-l01",
    "content_version": "2.0",
}
FORBIDDEN_KEYS = {
    "answer",
    "answers",
    "expected",
    "expected_answers",
    "solution_steps",
    "teacher_note",
    "diagnostic_topic_id",
    "skill_id",
    "item_family",
    "evidence",
}


def _client(tmp_path, monkeypatch) -> TestClient:
    state_file = tmp_path / "user_states.json"
    monkeypatch.setattr(plugins_api, "STATE_FILE", state_file)
    app = FastAPI()
    app.include_router(plugins_api.router, prefix="/api/v1/plugins")
    return TestClient(app)


def _start(client: TestClient) -> dict:
    response = client.post("/api/v1/plugins/panda/chat", json=PILOT)
    assert response.status_code == 200
    return response.json()


def _all_keys(value) -> set[str]:
    if isinstance(value, dict):
        result = set(value)
        for child in value.values():
            result.update(_all_keys(child))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for child in value:
            result.update(_all_keys(child))
        return result
    return set()


def test_real_panda_chat_starts_exact_pilot_lesson(tmp_path, monkeypatch) -> None:
    with _client(tmp_path, monkeypatch) as client:
        payload = _start(client)
    assert payload["text"] == "Вычисли 8 + 5."
    assert payload["state"]["phase"] == "curricular"
    assert payload["state"]["curricular"]["lesson_id"] == "g1-t12-l01"
    assert payload["state"]["curricular"]["content_version"] == "2.0"


def test_initial_child_response_has_no_answer_solution_or_mapping_evidence(tmp_path, monkeypatch) -> None:
    with _client(tmp_path, monkeypatch) as client:
        payload = _start(client)
    assert FORBIDDEN_KEYS.isdisjoint(_all_keys(payload))
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "13" not in encoded
    assert "разлож" not in encoded.casefold()


def test_wrong_answer_stays_on_server_owned_part_without_revealing_answer(tmp_path, monkeypatch) -> None:
    with _client(tmp_path, monkeypatch) as client:
        _start(client)
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": PILOT["user_id"], "message": "12", "action": "answer"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"]["curricular"]["part_index"] == 0
    assert payload["state"]["curricular"]["part_complete"] is False
    assert payload["state"]["curricular"]["lesson_complete"] is False
    assert payload["state"]["practice_feedback"]["status"] == "incorrect"
    assert "13" not in json.dumps(payload, ensure_ascii=False)


def test_correct_answer_completes_lesson_but_never_awards_mastery(tmp_path, monkeypatch) -> None:
    with _client(tmp_path, monkeypatch) as client:
        _start(client)
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": PILOT["user_id"], "message": "13", "action": "answer"},
        )
    payload = response.json()
    assert payload["state"]["curricular"]["part_complete"] is True
    assert payload["state"]["curricular"]["lesson_complete"] is True
    assert payload["state"]["curricular"]["mastery_awarded"] is False
    assert payload["state"]["practice_feedback"]["mastery_awarded"] is False


def test_hint_is_separate_and_does_not_record_an_attempt(tmp_path, monkeypatch) -> None:
    with _client(tmp_path, monkeypatch) as client:
        _start(client)
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": PILOT["user_id"], "message": "", "action": "hint"},
        )
    payload = response.json()
    assert response.status_code == 200
    assert payload["text"] == "Как разделить 5, чтобы сначала получить 10?"
    assert payload["state"]["current_practice"]["attempts"] == 0
    assert payload["state"]["practice_feedback"] is None
    assert payload["state"]["curricular"]["mastery_awarded"] is False


def test_advance_before_server_marks_current_part_complete_is_blocked(tmp_path, monkeypatch) -> None:
    with _client(tmp_path, monkeypatch) as client:
        _start(client)
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": PILOT["user_id"], "message": "", "action": "advance"},
        )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "current_part_not_complete"


def test_client_part_index_and_part_complete_are_ignored(tmp_path, monkeypatch) -> None:
    with _client(tmp_path, monkeypatch) as client:
        _start(client)
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={
                "user_id": PILOT["user_id"],
                "message": "12",
                "action": "answer",
                "part_index": 999,
                "part_complete": True,
            },
        )
    payload = response.json()
    assert payload["state"]["curricular"]["part_index"] == 0
    assert payload["state"]["curricular"]["part_complete"] is False


def test_unknown_or_wrong_version_never_falls_back_to_legacy_practice(tmp_path, monkeypatch) -> None:
    with _client(tmp_path, monkeypatch) as client:
        unknown = client.post(
            "/api/v1/plugins/panda/chat",
            json={**PILOT, "lesson_id": "g1-t12-l02"},
        )
        wrong_version = client.post(
            "/api/v1/plugins/panda/chat",
            json={**PILOT, "content_version": "1.0"},
        )
    assert unknown.status_code == 422
    assert wrong_version.status_code == 422
    assert unknown.json()["detail"]["code"] == "lesson_not_allowlisted"
    assert wrong_version.json()["detail"]["code"] == "lesson_not_allowlisted"
