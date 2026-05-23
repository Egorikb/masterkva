from __future__ import annotations

import deeptutor.services.teacher_llm as teacher_llm
from deeptutor.services.config import get_llm_config
from deeptutor.services.teacher_llm import build_teacher_prompt, generate_teacher_explanation, generate_teacher_reply


class _FakeChatCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)

        class _Choice:
            class _Message:
                content = "Объясни правило сложения через 10 и начни с простого примера."

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
    assert "Хочешь ещё один похожий пример" in text


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
