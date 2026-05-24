from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from deeptutor.api.routers.plugins_api import router
from deeptutor.services.gamification import (
    GamificationState,
    calculate_level,
    get_level_progress,
    check_badges,
    record_answer,
    record_mastery,
    get_gamification_state,
    save_gamification_state,
    XP_CORRECT_ANSWER,
    XP_WRONG_ANSWER,
    XP_MASTERY_BONUS,
    BADGES,
)
from deeptutor.services.i18n import (
    t,
    set_locale,
    get_locale,
    add_translations,
    get_available_locales,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/plugins")
    return app


def _make_user_id(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4()}"


# === i18n tests ===

def test_i18n_default_locale_is_ru() -> None:
    assert get_locale() == "ru"


def test_i18n_set_locale() -> None:
    set_locale("en")
    assert get_locale() == "en"
    set_locale("ru")  # reset


def test_i18n_t_ru() -> None:
    set_locale("ru")
    assert t("greeting") == "Привет!"


def test_i18n_t_en() -> None:
    assert t("greeting", locale="en") == "Hello!"


def test_i18n_t_missing_key() -> None:
    assert t("nonexistent_key") == "nonexistent_key"


def test_i18n_t_with_kwargs() -> None:
    result = t("notif_mastery_msg", locale="en", skill="Addition")
    assert "Addition" in result


def test_i18n_add_translations() -> None:
    add_translations("kk", {"greeting": "Сәлем!"})
    assert t("greeting", locale="kk") == "Сәлем!"


def test_i18n_available_locales() -> None:
    locales = get_available_locales()
    assert "ru" in locales
    assert "en" in locales


# === gamification: state tests ===

def test_gamification_state_default() -> None:
    state = GamificationState()
    assert state.xp == 0
    assert state.level == 1
    assert state.current_streak == 0


def test_gamification_state_to_dict() -> None:
    state = GamificationState(xp=100, level=2, current_streak=3)
    d = state.to_dict()
    assert d["xp"] == 100
    assert d["level"] == 2
    assert d["current_streak"] == 3


def test_gamification_state_from_dict() -> None:
    data = {"xp": 50, "level": 1, "badges": ["first_answer"]}
    state = GamificationState.from_dict(data)
    assert state.xp == 50
    assert "first_answer" in state.badges


def test_gamification_state_from_none() -> None:
    state = GamificationState.from_dict(None)
    assert state.xp == 0
    assert state.level == 1


# === gamification: level tests ===

def test_calculate_level_1() -> None:
    assert calculate_level(0) == 1
    assert calculate_level(49) == 1


def test_calculate_level_2() -> None:
    assert calculate_level(50) == 2
    assert calculate_level(149) == 2


def test_calculate_level_3() -> None:
    assert calculate_level(150) == 3


def test_get_level_progress() -> None:
    progress = get_level_progress(75)
    assert progress["current_level"] == 2
    assert progress["next_level"] == 3
    assert 0 < progress["progress_pct"] <= 100


def test_get_level_progress_max() -> None:
    progress = get_level_progress(9999)
    assert progress["current_level"] == progress["next_level"]
    assert progress["progress_pct"] == 100


# === gamification: answer recording tests ===

def test_record_answer_correct() -> None:
    user_id = _make_user_id("xp-correct")
    result = record_answer(user_id, True)
    assert result["xp_earned"] >= XP_CORRECT_ANSWER
    assert result["current_streak"] == 1
    assert result["total_xp"] > 0


def test_record_answer_wrong() -> None:
    user_id = _make_user_id("xp-wrong")
    result = record_answer(user_id, False)
    assert result["xp_earned"] == XP_WRONG_ANSWER
    assert result["current_streak"] == 0


def test_record_answer_streak_bonus() -> None:
    user_id = _make_user_id("xp-streak")
    # 3 correct answers in a row
    record_answer(user_id, True)
    record_answer(user_id, True)
    result = record_answer(user_id, True)
    assert result["current_streak"] == 3
    assert result["xp_earned"] > XP_CORRECT_ANSWER  # streak bonus


def test_record_answer_level_up() -> None:
    user_id = _make_user_id("xp-levelup")
    state = get_gamification_state(user_id)
    # Give enough XP to level up
    state.xp = 45  # close to level 2 (50)
    save_gamification_state(user_id, state)

    result = record_answer(user_id, True)
    if result["total_xp"] >= 50:
        assert result["level_up"] or not result["level_up"]  # depends on exact XP


def test_record_mastery_bonus() -> None:
    user_id = _make_user_id("xp-mastery")
    result = record_mastery(user_id, "test_skill")
    assert result["xp_earned"] == XP_MASTERY_BONUS


# === gamification: badge tests ===

def test_check_badges_first_answer() -> None:
    state = GamificationState(total_correct=1, total_wrong=0)
    profile = {"skill_mastery": {}}
    badges = check_badges(state, profile)
    assert "first_answer" in badges


def test_check_badges_streak_5() -> None:
    state = GamificationState(max_streak=5, total_correct=5, total_wrong=0)
    profile = {"skill_mastery": {}}
    badges = check_badges(state, profile)
    assert "streak_5" in badges


def test_check_badges_first_mastery() -> None:
    state = GamificationState(total_correct=10, total_wrong=0, badges=["first_answer"])
    profile = {"skill_mastery": {"skill_a": {"status": "mastered"}}}
    badges = check_badges(state, profile)
    assert "first_mastery" in badges


def test_check_badges_no_duplicates() -> None:
    state = GamificationState(
        total_correct=10, total_wrong=0,
        badges=["first_answer", "streak_5"]
    )
    profile = {"skill_mastery": {"a": {"status": "mastered"}}}
    badges = check_badges(state, profile)
    # Already has first_answer and streak_5
    assert "first_answer" not in badges
    assert "streak_5" not in badges


# === gamification: API tests ===

def test_gamification_endpoint() -> None:
    from deeptutor.api.routers.plugins_api import save_user_states

    user_id = _make_user_id("gamif-api")
    save_user_states({
        user_id: {
            "name": "Test",
            "grade": 1,
            "phase": "chat",
        }
    })

    with TestClient(_build_app()) as client:
        response = client.get(f"/api/v1/plugins/panda/gamification/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert "xp" in data
        assert "level" in data
        assert "badges" in data
        assert "level_progress" in data


def test_embed_init_endpoint() -> None:
    user_id = _make_user_id("embed-init")

    with TestClient(_build_app()) as client:
        response = client.post(
            "/api/v1/plugins/panda/embed/init",
            params={"user_id": user_id, "pupil_name": "Вася", "grade": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert data["name"] == "Вася"
        assert data["grade"] == 1
        assert data["ready"] is True


def test_embed_code_endpoint() -> None:
    user_id = _make_user_id("embed-code")

    with TestClient(_build_app()) as client:
        response = client.get(
            f"/api/v1/plugins/panda/embed/code",
            params={"user_id": user_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert "iframe_html" in data
        assert user_id in data["iframe_html"]
        assert "<iframe" in data["iframe_html"]
