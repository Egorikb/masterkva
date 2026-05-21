from __future__ import annotations

from deeptutor.services.teacher_llm import build_teacher_prompt, generate_teacher_explanation


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
