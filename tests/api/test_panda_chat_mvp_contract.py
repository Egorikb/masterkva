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


def test_diagnostic_start_uses_backend_text_no_llm(tmp_path, monkeypatch) -> None:
    """Diagnostic start uses backend-owned text, not LLM. No 'давай' needed."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "LLM_TEXT_SHOULD_NOT_APPEAR")
    user_id = f"mvp-start-backend-text-{uuid.uuid4()}"

    with TestClient(_build_app()) as client:
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "диагностика", "name": "Яна", "grade": 3},
        )

    payload = response.json()
    assert payload["state"]["phase"] == "diagnostic"
    assert "Начнём диагностику" in payload["text"]
    assert "LLM_TEXT_SHOULD_NOT_APPEAR" not in payload["text"]
    assert payload["visual"] is not None


def test_diagnostic_auto_transitions_to_practice_no_davay(tmp_path, monkeypatch) -> None:
    """After diagnostic completes, teacher auto-transitions to practice — no 'давай' needed."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"mvp-auto-practice-{uuid.uuid4()}"

    with TestClient(_build_app()) as client:
        start = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "диагностика", "name": "Алиса", "grade": 1},
        )
        assert start.status_code == 200
        assert start.json()["state"]["phase"] == "diagnostic"

        # Answer questions (wrong answers trigger early termination at 3)
        # Diagnostic auto-transitions to practice after 3 wrong answers
        for _ in range(3):
            response = client.post(
                "/api/v1/plugins/panda/chat",
                json={"user_id": user_id, "message": "999"},
            )
            assert response.status_code == 200

        # After diagnostic completes, phase should be practice (not waiting for "давай")
        payload = response.json()
        state = payload["state"]
        # Auto-transitioned to practice (not explanation, not waiting for "давай")
        assert state["phase"] == "practice"
    assert isinstance(state["weak_topic"], dict)
    assert state["current_practice"] is not None
    assert state["diagnostic_gap_status"] == "diagnosed_gap"
    assert state["blocked_skill_ids"] == ["g2_addition_core", "g2_subtraction_core"]
    assert state["remediation_targets"]["number_bond_missing_part"] == "number_bond"
    # No "Скажи «давай»" in text
    assert "Скажи" not in payload["text"] or "давай" not in payload["text"].lower()


def test_start_from_explanation_creates_practice_from_weak_topic(tmp_path, monkeypatch) -> None:
    """If state is in explanation (old saved state), push forward to practice automatically."""
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


def test_practice_answer_auto_advances_to_next_question(tmp_path, monkeypatch) -> None:
    """After correct practice answer, teacher auto-gives next question (no 'want more?')."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "Верно!")
    user_id = f"mvp-practice-auto-advance-{uuid.uuid4()}"
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
    # Still in practice (auto-advanced to next question)
    assert state["phase"] == "practice"
    assert state["current_practice"]["attempts"] == 0  # new practice object
    assert state["practice_feedback"]["is_correct"] is True
    # The text should contain the next question, not "want more?"
    text = response.json()["text"]
    assert "Хочешь" not in text
    assert "ещё" not in text.lower() or "Смотри" in text


def test_wrong_practice_answer_enters_remediation_flow(tmp_path, monkeypatch) -> None:
    """After wrong answer, system enters remediation flow (not raw practice)."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "Почти.")
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
        "item_family": "counting_with_objects",
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
    # Wrong answer → remediation phase
    assert payload["state"]["phase"] == "remediation"
    assert payload["state"]["practice_feedback"]["is_correct"] is False
    # Text should contain the correct answer
    text = payload["text"]
    assert "5" in text  # correct answer shown
    # And a clarifying question (remediation step)
    assert "?" in text


def test_mastery_gate_marks_g2_mastered_after_full_window(tmp_path, monkeypatch) -> None:
    """Mastery gate still works — after enough correct answers, skill is mastered."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"mvp-mastery-gate-mastered-{uuid.uuid4()}"
    weak_topic = {
        "grade": 2,
        "topic_id": "g2_t01",
        "topic": "Сложение двузначных чисел",
        "source_question_id": "g2_t01_q01",
    }
    current_practice = {
        "id": "g2_t01_p01",
        "topic_id": "g2_t01",
        "title": "Сложение двузначных чисел",
        "question": "12 + 5 = ?",
        "answer": "17",
        "attempts": 0,
    }
    seed_history = [
        {"question_id": f"seed-{idx}", "is_correct": True, "confidence": 1.0}
        for idx in range(1, 5)
    ]
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 2,
                "phase": "practice",
                "weak_topic": weak_topic,
                "current_practice": current_practice,
                "practice_feedback": None,
                "report": None,
                "mastery_status_by_skill": {
                    "g2_addition_core": {
                        "status": "learning",
                        "attempt_history": seed_history,
                    }
                },
            }
        }
    )

    with TestClient(_build_app()) as client:
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "17"},
        )

    payload = response.json()
    state = payload["state"]
    # Mastered — auto-promoted to next skill's practice
    assert state["mastery_gate_status"] == "mastered"
    assert state["promotion_eligible"] is True
    assert state["mastery_check_result"]["decision"] == "mastered"
    assert state["mastery_status_by_skill"]["g2_addition_core"]["last_mastery_decision"] == "mastered"


def test_mastery_gate_stays_closed_on_insufficient_evidence(tmp_path, monkeypatch) -> None:
    """Not enough evidence — stays in practice."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"mvp-mastery-gate-insufficient-{uuid.uuid4()}"
    weak_topic = {
        "grade": 2,
        "topic_id": "g2_t01",
        "topic": "Сложение двузначных чисел",
        "source_question_id": "g2_t01_q01",
    }
    current_practice = {
        "id": "g2_t01_p01",
        "topic_id": "g2_t01",
        "title": "Сложение двузначных чисел",
        "question": "12 + 5 = ?",
        "answer": "17",
        "attempts": 0,
    }
    seed_history = [
        {"question_id": f"seed-{idx}", "is_correct": True, "confidence": 1.0}
        for idx in range(1, 3)
    ]
    save_user_states(
        {
            user_id: {
                "name": "Алиса",
                "grade": 2,
                "phase": "practice",
                "weak_topic": weak_topic,
                "current_practice": current_practice,
                "practice_feedback": None,
                "report": None,
                "mastery_status_by_skill": {
                    "g2_addition_core": {
                        "status": "learning",
                        "attempt_history": seed_history,
                    }
                },
            }
        }
    )

    with TestClient(_build_app()) as client:
        response = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "17"},
        )

    payload = response.json()
    state = payload["state"]
    assert state["mastery_gate_status"] == "insufficient_evidence"
    assert state["promotion_eligible"] is False
    assert state["mastery_check_result"]["decision"] == "insufficient_evidence"
    assert state["mastery_check_result"]["evidence"]["history_length"] == 3
    assert state["mastery_status_by_skill"]["g2_addition_core"]["last_mastery_decision"] == "insufficient_evidence"
    # Still in practice — teacher continues
    assert state["phase"] == "practice"


def test_golden_chain_hardening_run_promotes_from_g1_to_g2(tmp_path, monkeypatch) -> None:
    """Full chain: practice → mastery → auto-promote to next skill → practice."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"mvp-golden-chain-promotion-{uuid.uuid4()}"
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
                "phase": "practice",
                "weak_topic": {
                    "grade": 1,
                    "topic_id": "g1_t05",
                    "topic": "СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5",
                    "source_question_id": "g1_t05_q01",
                },
                "current_practice": {
                    "id": "g1_t05_p01",
                    "topic_id": "g1_t05",
                    "title": "СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5",
                    "question": "2 + 1 = ?",
                    "answer": "3",
                    "item_family": "number_bond_missing_part",
                    "attempts": 0,
                },
                "practice_feedback": None,
                "report": None,
                "blocked_skill_ids": ["g2_addition_core"],
                "remediation_targets": {"number_bond_missing_part": "number_bond"},
                "mastery_status_by_skill": {
                    "g1_early_arithmetic_core": {
                        "status": "learning",
                        "attempt_history": seed_history_g1,
                    },
                    "g2_addition_core": {
                        "status": "learning",
                        "attempt_history": seed_history_g2,
                    },
                },
                "current_skill_id": "g1_early_arithmetic_core",
                "current_skill_version": "v1",
                "current_skill_mode": "shadow",
                "current_topic_id": "g1_t05",
                "learning_mode_active": True,
                "mastery_check_pending": False,
                "promotion_eligible": False,
            }
        }
    )

    with TestClient(_build_app()) as client:
        g1_mastery = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "3"},
        )
        assert g1_mastery.status_code == 200
        g1_payload = g1_mastery.json()
        # Auto-promoted to g2 practice (no "давай" needed)
        assert g1_payload["state"]["phase"] == "practice"
        assert g1_payload["state"]["current_skill_id"] == "g2_addition_core"
        assert g1_payload["state"]["current_practice"]["topic_id"] == "g2_t01"
        assert g1_payload["state"]["current_practice"]["question"] == "12 + 5 = ?"
        assert g1_payload["state"]["student_profile"]["promotion_history"][-1]["from_skill_id"] == "g1_early_arithmetic_core"
        assert g1_payload["state"]["student_profile"]["promotion_history"][-1]["to_skill_id"] == "g2_addition_core"
        assert g1_payload["state"]["blocked_skill_ids"] == []

        g2_mastery = client.post(
            "/api/v1/plugins/panda/chat",
            json={"user_id": user_id, "message": "17"},
        )
        assert g2_mastery.status_code == 200
        g2_payload = g2_mastery.json()
        # g2 is also mastered (had 4 seed correct + 1 current = 5), auto-promotes to g3
        assert g2_payload["state"]["current_skill_id"] == "g3_time_measurement_core"
        assert g2_payload["state"]["promotion_eligible"] is True
        assert g2_payload["state"]["mastery_gate_status"] == "mastered"


def test_report_phase_redirects_to_practice(tmp_path, monkeypatch) -> None:
    """If state is in report (old saved state), push forward to practice."""
    monkeypatch.setattr(plugins_api, "STATE_FILE", tmp_path / "user_states.json")
    monkeypatch.setattr(plugins_api, "generate_teacher_reply", lambda **kwargs: "TEACHER_OK")
    user_id = f"mvp-report-redirect-{uuid.uuid4()}"
    weak_topic = {
        "grade": 1,
        "topic_id": "g1_t02",
        "topic": "Следующее число",
        "source_question_id": "g1_t02_q01",
    }
    report = {
        "summary": "В этой попытке по теме 'Следующее число' есть ошибка.",
        "weak_topic": weak_topic,
        "practice_result": "needs_review",
        "recommendations": ["Повтори объяснение и попробуй ещё раз"],
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
    assert payload["state"]["practice_feedback"] is None
    assert payload["state"]["report"] is None
