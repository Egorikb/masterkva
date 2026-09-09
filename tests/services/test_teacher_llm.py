from __future__ import annotations

import json

import deeptutor.services.teacher_llm as teacher_llm
from deeptutor.services.config import get_llm_config
from deeptutor.services.teacher_llm import (
    build_teacher_prompt,
    generate_teacher_explanation,
    generate_teacher_reply,
    generate_teacher_response,
)


class _FakeChatCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)

        class _Choice:
            class _Message:
                content = json.dumps({
                    "schema_version": "v1",
                    "teacher_text": "Объясни правило сложения через 10 и начни с простого примера.",
                    "pedagogical_move": "explain",
                    "hint_level": 0,
                    "visual_request": {"needed": False, "type": None, "focus": None, "values": [], "labels": []},
                    "safety_flags": [],
                    "needs_human_review": False,
                    "source": "llm",
                }, ensure_ascii=False)

            message = _Message()

        class _Response:
            choices = [_Choice()]

        return _Response()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = type("Chat", (), {"completions": _FakeChatCompletions()})()


def test_generate_teacher_reply_without_key_uses_teacher_voice(monkeypatch) -> None:
    monkeypatch.setattr(
        teacher_llm,
        "get_llm_config",
        lambda: type("Cfg", (), {"provider": "openai", "model": "gpt-4o-mini", "api_key": "", "base_url": "https://api.openai.com/v1"})(),
    )

    text = generate_teacher_reply(
        stage="practice_result",
        grade=1,
        weak_topic={"topic": "Вычитание", "topic_id": "g1_t04"},
        learning_context=[],
        user_message="5",
        practice_question="7 - 4 = ?",
        practice_feedback={"is_correct": True},
        report={"summary": "Эта попытка верная, но по одной задаче ещё нельзя делать вывод о всём уровне знаний.", "practice_result": "success"},
    )

    assert "LLM-ключ" not in text
    assert "попытка" in text
    assert "Хочешь" not in text
    assert "давай" not in text.lower()
    assert not text.endswith("?")


def test_generate_teacher_reply_strips_terminal_followup_from_llm(monkeypatch) -> None:
    monkeypatch.setattr(
        teacher_llm,
        "get_llm_config",
        lambda: type("Cfg", (), {"provider": "openai", "model": "gpt-4o-mini", "api_key": "unit-test-key", "base_url": "https://api.openai.com/v1"})(),
    )

    fake_client = _FakeClient()
    fake_client.chat.completions.create = lambda **kwargs: type(
        "Response",
        (),
        {
            "choices": [
                type(
                    "Choice",
                    (),
                    {"message": type("Message", (), {"content": json.dumps({
                        "schema_version": "v1",
                        "teacher_text": "Верно, эта попытка получилась. Хочешь ещё?",
                        "pedagogical_move": "praise",
                        "hint_level": 0,
                        "visual_request": {"needed": False},
                        "safety_flags": [],
                        "needs_human_review": False,
                        "source": "llm",
                    }, ensure_ascii=False)})()},
                )()
            ]
        },
    )()

    text = generate_teacher_reply(
        stage="practice_result",
        grade=1,
        weak_topic={"topic": "Сложение", "topic_id": "g1_t03"},
        learning_context=[],
        user_message="7",
        practice_question="4 + 3 = ?",
        practice_feedback={"is_correct": True},
        report={"summary": "success"},
        client=fake_client,
    )

    assert text == "Верно, эта попытка получилась."


def test_get_llm_config_loads_dotenv_defaults(monkeypatch, tmp_path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "LLM_BINDING=openai\nLLM_MODEL=gpt-4o-mini\nLLM_API_KEY=test-key\nLLM_HOST=https://api.example.com/v1\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("LLM_BINDING", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_HOST", raising=False)
    monkeypatch.setattr("deeptutor.services.config._candidate_env_files", lambda: [dotenv])
    monkeypatch.setattr("deeptutor.services.config._DOTENV_LOADED", False)

    cfg = get_llm_config()

    assert cfg.provider == "openai"
    assert cfg.model == "gpt-4o-mini"
    assert cfg.api_key == "test-key"
    assert cfg.base_url == "https://api.example.com/v1"


def test_build_teacher_prompt_includes_grade_topic_and_context() -> None:
    prompt = build_teacher_prompt(
        grade=1,
        weak_topic={"topic": "СЛОЖЕНИЕ/ВЫЧИТАНИЕ", "topic_id": "g1_t03"},
        learning_context=[{"title": "1 класс · СЛОЖЕНИЕ", "topic_id": "3", "snippet": "Складываем предметы"}],
        user_message="помоги с примером",
    )

    assert "Класс: 1" in prompt
    assert "СЛОЖЕНИЕ/ВЫЧИТАНИЕ" in prompt
    assert "g1_t03" in prompt
    assert "Складываем предметы" in prompt
    assert "помоги с примером" in prompt


def test_generate_teacher_explanation_uses_client_and_model_env(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BINDING", "openai")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_API_KEY", "unit-test-key")
    monkeypatch.setenv("LLM_HOST", "https://api.openai.com/v1")

    fake_client = _FakeClient()
    text = generate_teacher_explanation(
        grade=1,
        weak_topic={"topic": "СЛОЖЕНИЕ/ВЫЧИТАНИЕ", "topic_id": "g1_t03"},
        learning_context=[{"title": "1 класс · СЛОЖЕНИЕ", "topic_id": "3", "snippet": "Складываем предметы"}],
        user_message="начать",
        client=fake_client,
    )

    assert "Объясни правило" in text
    call = fake_client.chat.completions.calls[0]
    assert call["model"] == "gpt-4o-mini"
    assert call["temperature"] == 0.2
    assert any(msg["role"] == "system" for msg in call["messages"])
    assert any(msg["role"] == "user" and "Складываем предметы" in msg["content"] for msg in call["messages"])


def test_teacher_response_detects_rephrase_and_visual_intents(monkeypatch) -> None:
    monkeypatch.setattr(
        teacher_llm,
        "get_llm_config",
        lambda: type("Cfg", (), {"api_key": "", "model": "test", "base_url": ""})(),
    )

    rephrase = generate_teacher_response(
        stage="explanation", grade=2, weak_topic={"topic": "Деление"},
        learning_context=[], user_message="Я не понял, объясни иначе",
    )
    visual = generate_teacher_response(
        stage="explanation", grade=2, weak_topic={"topic": "Деление"},
        learning_context=[], user_message="Покажи на картинке",
    )

    assert rephrase.pedagogical_move.value == "rephrase"
    assert visual.pedagogical_move.value == "visualize"
    assert visual.visual_request.needed is True
    assert visual.visual_request.type == "bar_model"


def test_teacher_response_blocks_personal_data_before_llm(monkeypatch) -> None:
    monkeypatch.setattr(
        teacher_llm,
        "get_llm_config",
        lambda: type("Cfg", (), {"api_key": "unit-test-key", "model": "test", "base_url": ""})(),
    )
    fake_client = _FakeClient()

    response = generate_teacher_response(
        stage="explanation", grade=3, weak_topic={"topic": "Дроби"},
        learning_context=[], user_message="Мой телефон +7 999 123-45-67", client=fake_client,
    )

    assert response.source == "safety"
    assert "personal_data" in response.safety_flags
    assert fake_client.chat.completions.calls == []


def test_invalid_or_answer_leaking_llm_response_uses_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        teacher_llm,
        "get_llm_config",
        lambda: type("Cfg", (), {"api_key": "unit-test-key", "model": "test", "base_url": ""})(),
    )
    fake_client = _FakeClient()
    fake_client.chat.completions.create = lambda **kwargs: type(
        "Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {
            "content": json.dumps({
                "schema_version": "v1", "teacher_text": "Правильный ответ 13.",
                "pedagogical_move": "hint", "hint_level": 1,
                "visual_request": {"needed": False}, "safety_flags": [],
                "needs_human_review": False, "source": "llm",
            }, ensure_ascii=False)
        })()})()]}
    )()

    response = generate_teacher_response(
        stage="practice_result", grade=1, weak_topic={"topic": "Сложение"},
        learning_context=[], user_message="Подскажи", correct_answer="13", client=fake_client,
    )

    assert response.source == "fallback"
    assert "13" not in response.teacher_text
