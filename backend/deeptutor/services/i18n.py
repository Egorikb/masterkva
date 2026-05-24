from __future__ import annotations

from typing import Any

_DEFAULT_LOCALE = "ru"

_translations: dict[str, dict[str, str]] = {
    "ru": {
        # General
        "greeting": "Привет!",
        "what_is_your_name": "Как тебя зовут?",
        "what_grade": "В каком ты классе?",
        "start_learning": "Напиши 'диагностика', чтобы начать учёбу.",

        # Diagnostic
        "diagnostic_start": "Начнём диагностику.",
        "diagnostic_complete_weak": "Диагностика завершена.\n\nВижу слабую тему — {topic}.\n\nНачнём разбор. Слушай внимательно.",
        "diagnostic_complete_strong": "Диагностика завершена.\n\nБаза выглядит крепкой.\n\nНачнём с темы «{topic}». Слушай внимательно.",
        "correct": "Верно!",
        "almost_correct": "Почти. правильный ответ: {answer}",
        "next_question": "Следующий вопрос:",

        # Practice
        "practice_correct": "Верно! Отлично.",
        "practice_wrong": "Не совсем. Правильный ответ: {answer}.",
        "keep_practicing": "Продолжаем практику.",
        "more_practice_needed": "Нужно больше практики.",

        # Mastery
        "topic_mastered": "🎯 Тема закреплена! Переходим к следующей.",
        "mastery_check": "Проверяем знания...",
        "continue_current_skill": "Рекомендуется продолжить практику по текущей теме.",

        # Remediation
        "remediation_continue": "Верно! Продолжаем.",
        "remediation_return": "Верно! Возвращаемся к практике.",
        "remediation_escalation_1": "Посмотри на числовой домик:",
        "remediation_escalation_2": "Давай по шагам: 1) Найди первое число. 2) Прибавь второе.",
        "remediation_explanation": "Давай разберёмся.",

        # Dashboard / Reports
        "overall_progress": "Общий прогресс",
        "activity": "Активность",
        "weak_topics": "Требуют внимания",
        "recent_days": "Последние дни",
        "common_errors": "Типичные ошибки",
        "recommendation": "Рекомендация",

        # Notifications
        "notif_mastery_title": "Тема освоена!",
        "notif_mastery_msg": "Ученик успешно освоил тему «{skill}».",
        "notif_streak_title": "Серия успехов!",
        "notif_streak_msg": "Ученик ответил верно {streak} раз подряд!",
        "notif_daily_title": "Итоги дня",

        # Gamification
        "level_up": "Уровень {level}!",
        "xp_earned": " +{xp} опыта",
        "badge_earned": "🏅 Получен бейдж: {badge}",
        "streak_message": "Серия: {count} подряд!",
    },
    "en": {
        # General
        "greeting": "Hello!",
        "what_is_your_name": "What is your name?",
        "what_grade": "What grade are you in?",
        "start_learning": "Type 'diagnostic' to start learning.",

        # Diagnostic
        "diagnostic_start": "Let's start the diagnostic.",
        "diagnostic_complete_weak": "Diagnostic complete.\n\nI see a weak topic — {topic}.\n\nLet's start working on it. Listen carefully.",
        "diagnostic_complete_strong": "Diagnostic complete.\n\nYour foundation looks strong.\n\nLet's start with '{topic}'. Listen carefully.",
        "correct": "Correct!",
        "almost_correct": "Almost. Correct answer: {answer}",
        "next_question": "Next question:",

        # Practice
        "practice_correct": "Correct! Great job.",
        "practice_wrong": "Not quite. Correct answer: {answer}.",
        "keep_practicing": "Keep practicing.",
        "more_practice_needed": "More practice needed.",

        # Mastery
        "topic_mastered": "🎯 Topic mastered! Moving to the next one.",
        "mastery_check": "Checking knowledge...",
        "continue_current_skill": "Recommended to continue practicing the current topic.",

        # Remediation
        "remediation_continue": "Correct! Continuing.",
        "remediation_return": "Correct! Returning to practice.",
        "remediation_escalation_1": "Look at the number bond:",
        "remediation_escalation_2": "Let's do it step by step: 1) Find the first number. 2) Add the second.",
        "remediation_explanation": "Let's work through this.",

        # Dashboard / Reports
        "overall_progress": "Overall Progress",
        "activity": "Activity",
        "weak_topics": "Needs Attention",
        "recent_days": "Recent Days",
        "common_errors": "Common Errors",
        "recommendation": "Recommendation",

        # Notifications
        "notif_mastery_title": "Topic Mastered!",
        "notif_mastery_msg": "Student has successfully mastered «{skill}».",
        "notif_streak_title": "Success Streak!",
        "notif_streak_msg": "Student answered correctly {streak} times in a row!",
        "notif_daily_title": "Daily Summary",

        # Gamification
        "level_up": "Level {level}!",
        "xp_earned": " +{xp} XP",
        "badge_earned": "🏅 Badge earned: {badge}",
        "streak_message": "Streak: {count} in a row!",
    },
}


def set_locale(locale: str) -> None:
    """Set default locale."""
    global _DEFAULT_LOCALE
    if locale in _translations:
        _DEFAULT_LOCALE = locale


def get_locale() -> str:
    """Get current default locale."""
    return _DEFAULT_LOCALE


def t(key: str, locale: str | None = None, **kwargs: Any) -> str:
    """Translate a key to the specified or default locale."""
    loc = locale or _DEFAULT_LOCALE
    translations = _translations.get(loc, _translations["ru"])
    text = translations.get(key, _translations["ru"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def add_translations(locale: str, translations: dict[str, str]) -> None:
    """Add or update translations for a locale."""
    if locale not in _translations:
        _translations[locale] = {}
    _translations[locale].update(translations)


def get_available_locales() -> list[str]:
    """Get list of available locales."""
    return list(_translations.keys())
