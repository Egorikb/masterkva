from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from deeptutor.services.student_profile_store import (
    get_student_profile,
    update_student_profile,
)


# XP constants
XP_CORRECT_ANSWER = 10
XP_WRONG_ANSWER = 2  # partial credit for trying
XP_STREAK_BONUS = 5  # per streak level
XP_MASTERY_BONUS = 50
XP_DAILY_LOGIN = 5

# Level thresholds (cumulative XP)
LEVEL_THRESHOLDS = [
    0,    # Level 1
    50,   # Level 2
    150,  # Level 3
    300,  # Level 4
    500,  # Level 5
    750,  # Level 6
    1050, # Level 7
    1400, # Level 8
    1800, # Level 9
    2300, # Level 10
]

# Badge definitions
BADGES: dict[str, dict[str, Any]] = {
    "first_answer": {
        "id": "first_answer",
        "name": "Первый шаг",
        "description": "Ответить на первый вопрос",
        "icon": "🎯",
        "condition": "total_attempts >= 1",
    },
    "streak_5": {
        "id": "streak_5",
        "name": "Серия 5",
        "description": "5 правильных ответов подряд",
        "icon": "🔥",
        "condition": "max_streak >= 5",
    },
    "streak_10": {
        "id": "streak_10",
        "name": "Серия 10",
        "description": "10 правильных ответов подряд",
        "icon": "💥",
        "condition": "max_streak >= 10",
    },
    "first_mastery": {
        "id": "first_mastery",
        "name": "Первая тема",
        "description": "Освоить первую тему",
        "icon": "⭐",
        "condition": "mastered_count >= 1",
    },
    "five_mastered": {
        "id": "five_mastered",
        "name": "Знаток",
        "description": "Освоить 5 тем",
        "icon": "🏆",
        "condition": "mastered_count >= 5",
    },
    "ten_mastered": {
        "id": "ten_mastered",
        "name": "Эксперт",
        "description": "Освоить 10 тем",
        "icon": "👑",
        "condition": "mastered_count >= 10",
    },
    "perfect_session": {
        "id": "perfect_session",
        "name": "Без ошибок",
        "description": "100% точность в сессии (минимум 5 вопросов)",
        "icon": "💎",
        "condition": "session_accuracy == 1.0 and session_total >= 5",
    },
    "speed_demon": {
        "id": "speed_demon",
        "name": "Молниеносный",
        "description": "Ответить на 5 вопросов подряд быстро",
        "icon": "⚡",
        "condition": "fast_streak >= 5",
    },
}


@dataclass
class GamificationState:
    """Gamification state for a user."""
    xp: int = 0
    level: int = 1
    current_streak: int = 0
    max_streak: int = 0
    total_correct: int = 0
    total_wrong: int = 0
    badges: list[str] = field(default_factory=list)
    last_answer_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "xp": self.xp,
            "level": self.level,
            "current_streak": self.current_streak,
            "max_streak": self.max_streak,
            "total_correct": self.total_correct,
            "total_wrong": self.total_wrong,
            "badges": list(self.badges),
            "last_answer_at": self.last_answer_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> GamificationState:
        if not data:
            return cls()
        return cls(
            xp=int(data.get("xp", 0)),
            level=int(data.get("level", 1)),
            current_streak=int(data.get("current_streak", 0)),
            max_streak=int(data.get("max_streak", 0)),
            total_correct=int(data.get("total_correct", 0)),
            total_wrong=int(data.get("total_wrong", 0)),
            badges=list(data.get("badges", [])),
            last_answer_at=data.get("last_answer_at"),
        )


def get_gamification_state(user_id: str) -> GamificationState:
    """Get gamification state for a user."""
    profile = get_student_profile(user_id)
    gamification = profile.get("gamification", {})
    return GamificationState.from_dict(gamification)


def save_gamification_state(user_id: str, state: GamificationState) -> None:
    """Save gamification state to user profile."""
    update_student_profile(user_id, {"gamification": state.to_dict()})


def calculate_level(xp: int) -> int:
    """Calculate level from XP."""
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if xp >= threshold:
            level = i + 1
        else:
            break
    return level


def get_level_progress(xp: int) -> dict[str, Any]:
    """Get progress towards next level."""
    current_level = calculate_level(xp)
    if current_level >= len(LEVEL_THRESHOLDS):
        return {
            "current_level": current_level,
            "next_level": current_level,
            "xp_current": xp,
            "xp_next": xp,
            "progress_pct": 100,
        }

    xp_current_level = LEVEL_THRESHOLDS[current_level - 1]
    xp_next_level = LEVEL_THRESHOLDS[current_level]
    progress = xp - xp_current_level
    needed = xp_next_level - xp_current_level

    return {
        "current_level": current_level,
        "next_level": current_level + 1,
        "xp_current": xp,
        "xp_next": xp_next_level,
        "progress_pct": min(round(progress / needed * 100) if needed > 0 else 100, 100),
    }


def check_badges(state: GamificationState, profile: dict[str, Any]) -> list[str]:
    """Check which new badges should be awarded."""
    skill_mastery = profile.get("skill_mastery", {})
    mastered_count = sum(1 for s in skill_mastery.values() if s.get("status") == "mastered")

    context = {
        "total_attempts": state.total_correct + state.total_wrong,
        "max_streak": state.max_streak,
        "mastered_count": mastered_count,
        "session_accuracy": 0,  # set by caller if needed
        "session_total": 0,
        "fast_streak": 0,
    }

    new_badges: list[str] = []
    for badge_id, badge_def in BADGES.items():
        if badge_id in state.badges:
            continue
        condition = badge_def["condition"]
        try:
            if _evaluate_condition(condition, context):
                new_badges.append(badge_id)
        except Exception:
            pass

    return new_badges


def _evaluate_condition(condition: str, context: dict[str, Any]) -> bool:
    """Safely evaluate a badge condition."""
    parts = condition.split(" and ")
    for part in parts:
        part = part.strip()
        if "==" in part:
            key, value = part.split("==", 1)
            key = key.strip()
            value = value.strip()
            if context.get(key) != _parse_value(value):
                return False
        elif ">=" in part:
            key, value = part.split(">=", 1)
            key = key.strip()
            value = value.strip()
            if (context.get(key) or 0) < _parse_value(value):
                return False
        elif "<=" in part:
            key, value = part.split("<=", 1)
            key = key.strip()
            value = value.strip()
            if (context.get(key) or 0) > _parse_value(value):
                return False
    return True


def _parse_value(value: str) -> Any:
    """Parse a value from condition string."""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def record_answer(user_id: str, is_correct: bool, confidence: float | None = None) -> dict[str, Any]:
    """Record an answer and update gamification state.

    Returns dict with xp_earned, new_level, new_badges, streak.
    """
    state = get_gamification_state(user_id)
    profile = get_student_profile(user_id)

    now = datetime.now(timezone.utc).isoformat()

    # Calculate XP
    xp_earned = XP_CORRECT_ANSWER if is_correct else XP_WRONG_ANSWER

    # Streak bonus
    if is_correct:
        state.current_streak += 1
        state.total_correct += 1
        if state.current_streak > state.max_streak:
            state.max_streak = state.current_streak
        if state.current_streak >= 3:
            xp_earned += XP_STREAK_BONUS * (state.current_streak - 2)
    else:
        state.current_streak = 0
        state.total_wrong += 1

    state.xp += xp_earned
    state.last_answer_at = now

    # Check level up
    old_level = state.level
    state.level = calculate_level(state.xp)
    level_up = state.level > old_level

    # Check badges
    new_badges = check_badges(state, profile)
    for badge_id in new_badges:
        state.badges.append(badge_id)

    # Save
    save_gamification_state(user_id, state)

    return {
        "xp_earned": xp_earned,
        "total_xp": state.xp,
        "level": state.level,
        "level_up": level_up,
        "old_level": old_level,
        "current_streak": state.current_streak,
        "max_streak": state.max_streak,
        "new_badges": new_badges,
        "all_badges": list(state.badges),
        "level_progress": get_level_progress(state.xp),
    }


def record_mastery(user_id: str, skill_id: str) -> dict[str, Any]:
    """Record a mastery achievement and award bonus XP."""
    state = get_gamification_state(user_id)

    state.xp += XP_MASTERY_BONUS
    old_level = state.level
    state.level = calculate_level(state.xp)
    level_up = state.level > old_level

    # Check badges
    profile = get_student_profile(user_id)
    new_badges = check_badges(state, profile)
    for badge_id in new_badges:
        state.badges.append(badge_id)

    save_gamification_state(user_id, state)

    return {
        "xp_earned": XP_MASTERY_BONUS,
        "total_xp": state.xp,
        "level": state.level,
        "level_up": level_up,
        "new_badges": new_badges,
    }
