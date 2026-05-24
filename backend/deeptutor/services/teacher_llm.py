from __future__ import annotations

import re
from typing import Any

from openai import OpenAI

from deeptutor.services.config import get_llm_config

SYSTEM_PROMPT = (
    "Ты живой преподаватель начальной/средней школы и говоришь от первого лица. "
    "Обращайся к ребёнку как учитель, а не как система. "
    "Пиши очень коротко: обычно 1–2 коротких фразы. "
    "Если нужно больше, разбей ответ на 2–3 коротких абзаца с пустой строкой между ними. "
    "Основную наглядность отдавай доске, а не тексту. "
    "Используй только учебный контекст 1–9 класса. "
    "Если контекст неполный, честно скажи, что опираешься на базовую программу класса. "
    "Всегда удерживай фокус на одной теме."
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


def _topic_name(weak_topic: dict[str, Any] | None) -> str:
    return str((weak_topic or {}).get("topic") or (weak_topic or {}).get("title") or "тема")


def _compact_teacher_text(text: str, *, max_sentences: int = 2, max_chars: int = 140) -> str:
    normalized = " ".join(str(text or "").split()).strip()
    if not normalized:
        return ""

    if len(normalized) <= max_chars:
        return normalized

    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
    if parts:
        compact = " ".join(parts[:max_sentences]).strip()
    else:
        compact = normalized[:max_chars].rsplit(" ", 1)[0].strip() if " " in normalized[:max_chars] else normalized[:max_chars].strip()

    if len(compact) > max_chars:
        compact = compact[:max_chars].rsplit(" ", 1)[0].strip() if " " in compact[:max_chars] else compact[:max_chars].strip()
    if compact and compact[-1] not in ".!?":
        compact += "..."
    return compact


def build_teacher_prompt(
    *,
    grade: int,
    weak_topic: dict[str, Any] | None,
    learning_context: list[dict[str, Any]],
    user_message: str = "",
) -> str:
    topic_name = _topic_name(weak_topic)
    topic_id = str((weak_topic or {}).get("topic_id") or "")
    context_text = _format_learning_context(learning_context)
    return (
        f"Класс: {grade}\n"
        f"Тема: {topic_name}\n"
        f"Topic ID: {topic_id}\n"
        f"Последнее сообщение ученика: {user_message or 'нет'}\n\n"
        f"Учебный контекст:\n{context_text}\n\n"
        "Пиши как учитель: 1–2 коротких фразы на абзац. "
        "Если нужно больше, используй 2–3 коротких абзаца с пустой строкой между ними. "
        "Не перегружай объяснение — доска должна показывать смысл. "
        "Последняя фраза может быть коротким вопросом только если это нужно для продолжения урока."
    )


def build_teacher_turn_prompt(
    *,
    stage: str,
    grade: int,
    weak_topic: dict[str, Any] | None,
    learning_context: list[dict[str, Any]],
    user_message: str = "",
    practice_question: str = "",
    practice_feedback: dict[str, Any] | None = None,
    report: dict[str, Any] | None = None,
) -> str:
    topic_name = _topic_name(weak_topic)
    context_text = _format_learning_context(learning_context)
    feedback = practice_feedback or {}
    report_text = str((report or {}).get("summary") or "")
    return (
        f"Этап: {stage}\n"
        f"Класс: {grade}\n"
        f"Тема: {topic_name}\n"
        f"Последнее сообщение ученика: {user_message or 'нет'}\n"
        f"Задача: {practice_question or 'нет'}\n"
        f"Ответ верный: {bool(feedback.get('is_correct', False))}\n"
        f"Итог отчёта: {report_text or 'нет'}\n\n"
        f"Учебный контекст:\n{context_text}\n\n"
        "Ты преподаватель. Пиши как живой учитель: коротко, мягко и по делу. "
        "Не делай вывод о всём уровне знаний по одной задаче. "
        "Если этап связан с объяснением — помоги понять тему и закончи простым вопросом. "
        "Если этап связан с практикой — похвали или мягко поправь. "
        "НЕ задавай вопросов — следующую задачу даёт система. "
        "НЕ предлагай «ещё» или «давай» — система сама ведёт ребёнка. "
        "Пиши 1-2 короткие фразы. "
        "Если этап связан с отчётом — дай педагогический комментарий без технических слов."
    )


def _fallback_teacher_turn(
    *,
    stage: str,
    weak_topic: dict[str, Any] | None,
    practice_question: str = "",
    practice_feedback: dict[str, Any] | None = None,
    report: dict[str, Any] | None = None,
    user_message: str = "",
) -> str:
    topic_name = _topic_name(weak_topic)
    is_correct = bool((practice_feedback or {}).get("is_correct", False))
    report_text = str((report or {}).get("summary") or "")

    if stage == "diagnostic_start":
        return "Я твой преподаватель.\n\nНачнём диагностику."
    if stage == "diagnostic_complete":
        return (
            f"Вижу слабую тему — {topic_name}.\n\n"
            "Диагностика завершена.\n\n"
            "Скажи «давай», и я продолжу."
        )
    if stage == "explanation":
        return (
            f"Разберём тему '{topic_name}'.\n\n"
            "Сначала короткое правило.\n\n"
            "Готов?"
        )
    if stage == "practice_intro":
        return (
            f"Переходим к практике по теме '{topic_name}'.\n\n"
            f"Вот первый пример: {practice_question or 'сейчас дам пример'}."
        )
    if stage == "practice_result":
        if is_correct:
            return (
                "Верно.\n\n"
                f"{report_text or 'По одной задаче ещё рано делать вывод о всём уровне знаний.'}\n\n"
                "Хочешь ещё один похожий пример?"
            )
        return (
            "Почти.\n\n"
            f"{report_text or 'Одна ошибка не означает, что тема не понята.'}\n\n"
            f"Попробуем ещё раз: {practice_question or 'этот пример'}."
        )
    if stage == "report_followup":
        if report and report.get("practice_result") == "success":
            return (
                f"Эта попытка по теме '{topic_name}' получилась.\n\n"
                "Но по одной задаче нельзя делать вывод о всём уровне знаний.\n\n"
                "Хочешь ещё один похожий пример?"
            )
        return (
            f"В этой попытке по теме '{topic_name}' есть ошибка.\n\n"
            "Но по одной задаче тоже нельзя делать вывод о знании темы.\n\n"
            "Давай ещё один похожий пример?"
        )

    return report_text or f"Разберём тему '{topic_name}' шаг за шагом."


def generate_teacher_reply(
    *,
    stage: str,
    grade: int,
    weak_topic: dict[str, Any] | None,
    learning_context: list[dict[str, Any]],
    user_message: str = "",
    practice_question: str = "",
    practice_feedback: dict[str, Any] | None = None,
    report: dict[str, Any] | None = None,
    client: Any | None = None,
) -> str:
    cfg = get_llm_config()
    prompt = build_teacher_turn_prompt(
        stage=stage,
        grade=grade,
        weak_topic=weak_topic,
        learning_context=learning_context,
        user_message=user_message,
        practice_question=practice_question,
        practice_feedback=practice_feedback,
        report=report,
    )

    if not cfg.api_key:
        return _fallback_teacher_turn(
            stage=stage,
            weak_topic=weak_topic,
            practice_question=practice_question,
            practice_feedback=practice_feedback,
            report=report,
            user_message=user_message,
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
    text = _compact_teacher_text(str(content or "").strip())
    if text:
        if stage in {"practice_result", "report_followup"} and not text.endswith("?"):
            text += "?"
        return text
    return _fallback_teacher_turn(
        stage=stage,
        weak_topic=weak_topic,
        practice_question=practice_question,
        practice_feedback=practice_feedback,
        report=report,
        user_message=user_message,
    )


def generate_teacher_explanation(
    *,
    grade: int,
    weak_topic: dict[str, Any] | None,
    learning_context: list[dict[str, Any]],
    user_message: str = "",
    client: Any | None = None,
) -> str:
    return generate_teacher_reply(
        stage="explanation",
        grade=grade,
        weak_topic=weak_topic,
        learning_context=learning_context,
        user_message=user_message,
        client=client,
    )
