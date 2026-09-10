"""Deterministic safety gate for child-facing teacher turns."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    blocked: bool
    flags: tuple[str, ...]
    safe_text: str | None = None
    needs_human_review: bool = False


_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?7|8)[\s()\-]*\d{3}[\s()\-]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}(?!\d)")
_SELF_HARM = ("не хочу жить", "убить себя", "покончить с собой", "сделать себе больно")
_ABUSE = ("меня бьют", "меня ударили", "боюсь дома", "ко мне пристают", "трогает меня")
_DANGEROUS = ("сделать бомбу", "взорвать", "отравить", "купить наркотики", "взломать")


def evaluate_child_safety(message: str) -> SafetyDecision:
    text = str(message or "").strip()
    lowered = text.casefold()
    flags: list[str] = []

    if _EMAIL_RE.search(text) or _PHONE_RE.search(text):
        flags.append("personal_data")
    if any(marker in lowered for marker in _SELF_HARM):
        flags.append("self_harm")
    if any(marker in lowered for marker in _ABUSE):
        flags.append("abuse")
    if any(marker in lowered for marker in _DANGEROUS):
        flags.append("dangerous_request")

    severe = any(flag in {"self_harm", "abuse", "dangerous_request"} for flag in flags)
    if severe:
        return SafetyDecision(
            blocked=True,
            flags=tuple(flags),
            safe_text=(
                "Я не буду помогать с опасными действиями. Если тебе сейчас страшно или небезопасно, "
                "обратись к взрослому, которому доверяешь, прямо сейчас."
            ),
            needs_human_review=True,
        )
    if "personal_data" in flags:
        return SafetyDecision(
            blocked=True,
            flags=tuple(flags),
            safe_text="Не отправляй в чат телефон, адрес или другие личные данные. Вернёмся к учебной задаче.",
        )
    return SafetyDecision(blocked=False, flags=tuple(flags))
