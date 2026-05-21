from __future__ import annotations

from typing import Any

from openai import OpenAI

from deeptutor.services.config import get_llm_config

SYSTEM_PROMPT = (
    "Ты преподаватель начальной/средней школы. "
    "Объясняй только по учебному контексту, кратко и ясно, "
    "используя материалы программы 1–9 класса. "
    "Если контекст неполный, честно скажи, что опираешься на базовую программу класса."
)


def _format_learning_context(learning_context: list[dict[str, Any]]) -> str:
    if not learning_context:
        return "Учебный контекст не найден."
    lines: list[str] = []
    for item in learning_context:
        title = str(item.get("title") or item.get("source_file") or "материал")
        topic = str(item.get("topic_id") or "без topic_id")
        snippet = str(item.get("snippet") or "").strip()
        lines.append(f"- {title} [{topic}]: {snippet}")
    return "\n".join(lines)


def build_teacher_prompt(
    *,
    grade: int,
    weak_topic: dict[str, Any] | None,
    learning_context: list[dict[str, Any]],
    user_message: str = "",
) -> str:
    topic_name = str((weak_topic or {}).get("topic") or "тема")
    topic_id = str((weak_topic or {}).get("topic_id") or "")
    context_text = _format_learning_context(learning_context)
    return (
        f"Класс: {grade}\n"
        f"Тема: {topic_name}\n"
        f"Topic ID: {topic_id}\n"
        f"Последнее сообщение ученика: {user_message or 'нет'}\n\n"
        f"Учебный контекст:\n{context_text}\n\n"
        "Дай 2-4 предложения объяснения по теме и один очень простой шаг для старта практики."
    )


def generate_teacher_explanation(
    *,
    grade: int,
    weak_topic: dict[str, Any] | None,
    learning_context: list[dict[str, Any]],
    user_message: str = "",
    client: Any | None = None,
) -> str:
    cfg = get_llm_config()
    prompt = build_teacher_prompt(
        grade=grade,
        weak_topic=weak_topic,
        learning_context=learning_context,
        user_message=user_message,
    )

    if not cfg.api_key:
        return (
            f"Объяснение по теме '{(weak_topic or {}).get('topic', 'тема')}' готово, "
            "но LLM-ключ не настроен."
        )

    llm_client = client or OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    response = llm_client.chat.completions.create(
        model=cfg.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    content = response.choices[0].message.content if getattr(response, "choices", None) else None
    text = str(content or "").strip()
    if text:
        return text
    return f"Объяснение по теме '{(weak_topic or {}).get('topic', 'тема')}' не удалось сгенерировать."
