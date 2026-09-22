from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from deeptutor.api.routers import plugins_api
import deeptutor.services.curricular_lesson_runtime as runtime_module
from deeptutor.services.curricular_lesson_runtime import ResolvedCurricularLesson


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


def _synthetic_resolved(assessment: dict, prompts: list[str]) -> ResolvedCurricularLesson:
    return ResolvedCurricularLesson(
        lesson_id="synthetic",
        content_version="test",
        lesson={"assessment": assessment, "presentation": {"prompts": prompts}},
        mapping={},
    )


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


def test_every_other_mapped_review_or_unmapped_lesson_is_closed(tmp_path, monkeypatch) -> None:
    runtime_map = json.loads(runtime_module.RUNTIME_MAP_FILE.read_text(encoding="utf-8"))
    other_rows = [row for row in runtime_map["mappings"] if row["lesson_id"] != PILOT["lesson_id"]]
    assert len(other_rows) == 77
    assert sum(row["status"] == "review_required" for row in other_rows) == 10
    assert sum(row["status"] == "unmapped" for row in other_rows) == 59

    with _client(tmp_path, monkeypatch) as client:
        responses = [
            client.post(
                "/api/v1/plugins/panda/chat",
                json={
                    **PILOT,
                    "lesson_id": row["lesson_id"],
                    "content_version": row["content_version"],
                },
            )
            for row in other_rows
        ]
    assert all(response.status_code == 422 for response in responses)
    assert {response.json()["detail"]["code"] for response in responses} == {"lesson_not_allowlisted"}


def test_changed_expected_in_test_copy_changes_api_assessment(tmp_path: Path, monkeypatch) -> None:
    lessons_file = tmp_path / runtime_module.LESSONS_FILE.name
    lessons = json.loads(runtime_module.LESSONS_FILE.read_text(encoding="utf-8"))
    lesson = next(
        lesson
        for semester in (lessons["semester_1"], lessons["semester_2"])
        for topic in semester["topics"]
        for lesson in topic["lessons"]
        if lesson["lesson_id"] == PILOT["lesson_id"]
    )
    lesson["assessment"]["parts"][0]["expected"] = ["99"]
    lessons_file.write_text(json.dumps(lessons, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(runtime_module, "LESSONS_FILE", lessons_file)

    with _client(tmp_path, monkeypatch) as client:
        _start(client)
        old_answer = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": PILOT["user_id"], "message": "13", "action": "answer"},
        )
        new_answer = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": PILOT["user_id"], "message": "99", "action": "answer"},
        )
    assert old_answer.json()["state"]["practice_feedback"]["status"] == "incorrect"
    assert new_answer.json()["state"]["practice_feedback"]["status"] == "correct"


def test_child_safe_serializer_drops_stale_internal_fields(tmp_path, monkeypatch) -> None:
    with _client(tmp_path, monkeypatch) as client:
        _start(client)
        state = plugins_api.get_user_state(PILOT["user_id"])
        practice = dict(state["current_practice"])
        practice.update({"answer": "SERVER-ANSWER", "teacher_note": "SERVER-NOTE"})
        feedback = {"status": "incorrect", "attempts": 1, "correct_answer": "SERVER-ANSWER"}
        plugins_api.update_user_state(
            PILOT["user_id"],
            {"current_practice": practice, "practice_feedback": feedback},
        )
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": PILOT["user_id"], "message": "", "action": "hint"},
        )
    payload = response.json()
    assert FORBIDDEN_KEYS.isdisjoint(_all_keys(payload))
    assert "SERVER-" not in json.dumps(payload, ensure_ascii=False)


def test_curricular_pause_and_resume_keep_child_safe_shape(tmp_path, monkeypatch) -> None:
    with _client(tmp_path, monkeypatch) as client:
        _start(client)
        state = plugins_api.get_user_state(PILOT["user_id"])
        state["curricular_session"]["legacy_state"]["current_practice"] = {
            "question": "Legacy question",
            "answer": "SERVER-ANSWER",
        }
        plugins_api.update_user_state(PILOT["user_id"], {"curricular_session": state["curricular_session"]})
        paused = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": PILOT["user_id"], "message": "стоп", "mode": "curricular"},
        )
        resumed = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": PILOT["user_id"], "message": "продолжить", "mode": "curricular"},
        )
    assert paused.json()["state"]["phase"] == "paused"
    assert resumed.json()["state"]["phase"] == "curricular"
    assert FORBIDDEN_KEYS.isdisjoint(_all_keys(paused.json()))
    assert FORBIDDEN_KEYS.isdisjoint(_all_keys(resumed.json()))
    assert "SERVER-ANSWER" not in json.dumps([paused.json(), resumed.json()], ensure_ascii=False)


def test_ordered_parts_advance_one_at_a_time_under_server_control(tmp_path, monkeypatch) -> None:
    _client(tmp_path, monkeypatch)
    resolved = _synthetic_resolved(
        {
            "kind": "ordered",
            "parts": [
                {"prompt": "Первая часть", "expected": ["1"]},
                {"prompt": "Вторая часть", "expected": ["2"]},
            ],
        },
        ["Первая часть", "Вторая часть"],
    )
    session = {
        "lesson_id": "synthetic",
        "content_version": "test",
        "part_index": 0,
        "part_count": 2,
        "attempts": 0,
        "part_complete": False,
        "awaiting_advance": False,
        "lesson_complete": False,
    }
    plugins_api.save_user_states(
        {
            "ordered-child": {
                "phase": "curricular",
                "curricular_session": session,
                "current_practice": plugins_api.curricular_lesson_runtime.child_part(resolved, 0),
            }
        }
    )

    first = plugins_api._answer_curricular_part(
        "ordered-child",
        plugins_api.ChatRequest(user_id="ordered-child", message="1", action="answer"),
        resolved,
        session,
    )
    assert first["state"]["curricular"]["part_complete"] is True
    assert first["state"]["curricular"]["lesson_complete"] is False
    advanced = plugins_api._advance_curricular_part(
        "ordered-child",
        resolved,
        plugins_api.get_user_state("ordered-child")["curricular_session"],
    )
    assert advanced["state"]["curricular"]["part_index"] == 1
    second = plugins_api._answer_curricular_part(
        "ordered-child",
        plugins_api.ChatRequest(user_id="ordered-child", message="2", action="answer"),
        resolved,
        plugins_api.get_user_state("ordered-child")["curricular_session"],
    )
    assert second["state"]["curricular"]["lesson_complete"] is True
    assert second["state"]["curricular"]["mastery_awarded"] is False


def test_rubric_needs_adult_review_and_never_changes_mastery(tmp_path, monkeypatch) -> None:
    _client(tmp_path, monkeypatch)
    resolved = _synthetic_resolved(
        {"kind": "rubric", "criteria": ["Объясняет ход решения"]},
        ["Объясни решение"],
    )
    mastery = {"legacy-skill": {"status": "learning", "attempts_count": 4}}
    session = {
        "lesson_id": "synthetic",
        "content_version": "test",
        "part_index": 0,
        "part_count": 1,
        "attempts": 0,
        "part_complete": False,
        "awaiting_advance": False,
        "lesson_complete": False,
    }
    plugins_api.save_user_states(
        {
            "rubric-child": {
                "phase": "curricular",
                "curricular_session": session,
                "current_practice": plugins_api.curricular_lesson_runtime.child_part(resolved, 0),
                "mastery_status_by_skill": mastery,
                "promotion_eligible": False,
            }
        }
    )
    payload = plugins_api._answer_curricular_part(
        "rubric-child",
        plugins_api.ChatRequest(user_id="rubric-child", message="Моё объяснение", action="answer"),
        resolved,
        session,
    )
    stored = plugins_api.get_user_state("rubric-child")
    assert payload["state"]["practice_feedback"]["status"] == "needs_review"
    assert "взрослому" in payload["text"]
    assert payload["state"]["curricular"]["part_complete"] is False
    assert stored["mastery_status_by_skill"] == mastery
    assert stored["promotion_eligible"] is False


def test_switch_back_to_legacy_restores_context_without_assessing_switch_message(tmp_path, monkeypatch) -> None:
    legacy_practice = {
        "id": "legacy-question",
        "topic_id": "g1_t02",
        "question": "Какое число идёт после 8?",
        "answer": "9",
        "attempts": 0,
    }
    mastery = {"g1_number_successor": {"status": "learning", "attempts_count": 4}}
    plugins_api.STATE_FILE = tmp_path / "user_states.json"
    plugins_api.save_user_states(
        {
            PILOT["user_id"]: {
                "name": "Аня",
                "grade": 1,
                "phase": "practice",
                "path_choice": "kungfu",
                "current_practice": legacy_practice,
                "current_skill_id": "g1_number_successor",
                "current_topic_id": "g1_t02",
                "mastery_status_by_skill": mastery,
                "promotion_eligible": False,
            }
        }
    )
    with _client(tmp_path, monkeypatch) as client:
        _start(client)
        client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": PILOT["user_id"], "message": "13", "action": "answer"},
        )
        switched = client.post(
            "/api/v1/plugins/panda/chat",
            json={
                "user_id": PILOT["user_id"],
                "message": "9",
                "mode": "kungfu",
                "action": "answer",
            },
        )
    payload = switched.json()
    stored = plugins_api.get_user_state(PILOT["user_id"])
    assert payload["state"]["phase"] == "practice"
    assert payload["state"]["current_practice"]["id"] == "legacy-question"
    assert stored["current_practice"]["attempts"] == 0
    assert stored["mastery_status_by_skill"] == mastery
    assert stored["promotion_eligible"] is False
    assert stored.get("curricular_session") is None
