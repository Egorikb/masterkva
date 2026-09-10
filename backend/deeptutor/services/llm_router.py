"""
MasterKva — LLM Router Module

Отвечает за ВСЕ вызовы к LLM:
  - Генерация педагогических текстов
  - Обёртка над teacher_llm.generate_teacher_reply
  - Ограничение длины, фильтрация вопросов

Принцип: ВСЕ LLM-вызовы проходят через этот модуль.
Больше нигде в коде не вызывается generate_teacher_reply напрямую.
"""
from __future__ import annotations

import re
from typing import Any

from deeptutor.services.teacher_llm import generate_teacher_reply


# === System prompts for each stage ===

PRACTICE_RESULT_PROMPT_ADDON = (
    "Ты учитель. Скажи 1-2 короткие фразы. "
    "Хвали или мягко поправь. "
    "НЕ задавай вопросов — следующую задачу даёт система. "
    "НЕ предлагай «ещё» или «давай». "
    "Пиши очень коротко."
)

EXPLANATION_PROMPT_ADDON = (
    "Ты учитель. Объясни тему коротко и понятно ребёнку. "
    "Используй 1-2 абзаца. "
    "В конце можно задать один вопрос для проверки понимания."
)


def _strip_followup_question(text: str) -> str:
    """Remove trailing 'want more?' type questions from LLM output."""
    patterns = [
        r"\n\nХочешь[^\n]*\??$",
        r"\n\nПродолж[^\n]*\??$",
        r"\n\nЕщё[^\n]*\??$",
        r"\n\nДавай[^\n]*\??$",
    ]
    result = text
    for pattern in patterns:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.MULTILINE)
    return result.strip()


def _compact_text(text: str, max_chars: int = 140) -> str:
    """Compact LLM output to max_chars."""
    if len(text) <= max_chars:
        return text
    # Cut at last space before max_chars
    trimmed = text[:max_chars]
    last_space = trimmed.rfind(" ")
    if last_space > 0:
        trimmed = trimmed[:last_space]
    return trimmed.strip()


def generate_practice_feedback(
    *,
    grade: int,
    weak_topic: dict[str, Any] | None,
    learning_context: list[dict[str, Any]],
    user_message: str,
    practice_question: str,
    is_correct: bool,
    correct_answer: str,
    client: Any | None = None,
) -> str:
    """Generate short feedback for practice answer.

    Returns 1-2 short sentences. Never generates questions.
    """
    feedback = generate_teacher_reply(
        stage="practice_result" if is_correct else "practice_result",
        grade=grade,
        weak_topic=weak_topic,
        learning_context=learning_context,
        user_message=user_message,
        practice_question=practice_question,
        practice_feedback={"is_correct": is_correct, "correct_answer": correct_answer},
    )

    feedback = _strip_followup_question(feedback)
    feedback = _compact_text(feedback)
    return feedback


def generate_explanation(
    *,
    grade: int,
    weak_topic: dict[str, Any] | None,
    learning_context: list[dict[str, Any]],
    user_message: str = "",
    client: Any | None = None,
) -> str:
    """Generate explanation text for a topic.

    Returns 1-2 short paragraphs with optional check question.
    """
    return generate_teacher_reply(
        stage="explanation",
        grade=grade,
        weak_topic=weak_topic,
        learning_context=learning_context,
        user_message=user_message,
    )


def generate_diagnostic_intro(*, grade: int, client: Any | None = None) -> str:
    """Generate diagnostic introduction text."""
    return f"Начнём диагностику.\n\nЯ буду задавать вопросы по математике {grade} класса. Попробуй отвечать — это поможет мне понять, что тебе нужно подтянуть."


def generate_welcome(*, name: str, grade: int, client: Any | None = None) -> str:
    """Generate welcome text after onboarding."""
    return f"Привет, {name}! Я помогу тебе с математикой {grade} класса.\n\nНапиши 'диагностика', чтобы начать, или спроси меня о любой теме."
