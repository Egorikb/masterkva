from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from deeptutor.services.diagnostic_engine import DiagnosticEngine, diagnostic_engine
from deeptutor.services.practice_engine import PracticeEngine
from deeptutor.services.report_service import ReportService

router = APIRouter()
STATE_FILE = Path(__file__).resolve().parents[3] / "data" / "user_states.json"

practice_engine = PracticeEngine()
report_service = ReportService()


class ChatRequest(BaseModel):
    user_id: str
    message: str
    name: str | None = None
    grade: int | None = Field(default=None, ge=0)


DEFAULT_STATE: dict[str, Any] = {
    "name": None,
    "grade": 0,
    "last_topic": None,
    "onboarding_complete": False,
    "phase": "chat",
    "path_choice": None,
    "in_learning": False,
    "diagnostic_progress": {},
    "diag_answers": [],
    "diag_sequence": [],
    "weak_topic": None,
    "current_practice": None,
    "practice_feedback": None,
    "report": None,
}


def _fresh_state() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_STATE, ensure_ascii=False))


def _read_states() -> dict[str, dict[str, Any]]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_user_states(states: dict[str, dict[str, Any]]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(states, ensure_ascii=False, indent=2), encoding="utf-8")


def get_user_state(user_id: str) -> dict[str, Any]:
    states = _read_states()
    state = states.get(user_id)
    if state is None:
        state = _fresh_state()
        states[user_id] = state
        save_user_states(states)
        return state

    merged = _fresh_state()
    merged.update(state)
    return merged


def update_user_state(user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    states = _read_states()
    state = _fresh_state()
    state.update(states.get(user_id, {}))
    for key, value in updates.items():
        if value is not None:
            state[key] = value
    states[user_id] = state
    save_user_states(states)
    return state


def _ensure_state_defaults(state: dict[str, Any]) -> dict[str, Any]:
    merged = _fresh_state()
    merged.update(state or {})
    return merged


def _is_diagnostic_start(message: str) -> bool:
    text = message.lower()
    return "диагност" in text or "провер" in text or "старт" in text


def _is_explanation_start(message: str) -> bool:
    text = message.lower()
    return "начать" in text or "практик" in text or "давай" in text


def _is_answer_correct(answer: str, question: dict[str, Any]) -> bool:
    user = str(answer).strip().lower()
    correct = str(question.get("answer", "")).strip().lower()
    if user == correct:
        return True
    alternatives = {str(item).strip().lower() for item in question.get("alternatives", [])}
    if user in alternatives:
        return True

    def _digits(value: str) -> str | None:
        digits = "".join(ch for ch in value if ch.isdigit() or ch == "-")
        return digits if digits and digits not in {"-", "--"} else None

    user_digits = _digits(user)
    correct_digits = _digits(correct)
    if user_digits is not None and correct_digits is not None:
        return user_digits == correct_digits
    return False


def _panda_response(text: str, state: dict[str, Any], visual: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized_state = _ensure_state_defaults(state)
    normalized_state.setdefault("phase", "chat")
    normalized_state.setdefault("weak_topic", None)
    normalized_state.setdefault("current_practice", None)
    normalized_state.setdefault("practice_feedback", None)
    normalized_state.setdefault("report", None)
    return {"text": text, "visual": visual, "state": normalized_state}


def _start_diagnostic(user_id: str, state: dict[str, Any]) -> dict[str, Any]:
    claimed_grade = int(state.get("grade") or 1)
    sequence = diagnostic_engine.build_diagnostic_sequence(claimed_grade)
    if not sequence:
        sequence = [diagnostic_engine.get_questions_for_grade(1)[0]] if diagnostic_engine.get_questions_for_grade(1) else []
    diag_state = {
        "phase": "diagnostic",
        "path_choice": "diagnostic",
        "in_learning": False,
        "diagnostic_progress": {
            "in_diagnostic": True,
            "claimed_grade": claimed_grade,
            "questions_answered": 0,
            "correct_in_row": 0,
        },
        "diag_answers": [],
        "diag_sequence": sequence,
        "weak_topic": None,
        "current_practice": None,
        "practice_feedback": None,
        "report": None,
    }
    update_user_state(user_id, diag_state)
    return get_user_state(user_id)


def _current_question(state: dict[str, Any]) -> dict[str, Any] | None:
    sequence = list(state.get("diag_sequence", []))
    progress = dict(state.get("diagnostic_progress", {}))
    index = int(progress.get("questions_answered", 0))
    if not sequence:
        return None
    if index >= len(sequence):
        index = len(sequence) - 1
    return sequence[index]


def _finish_diagnostic(user_id: str, state: dict[str, Any]) -> dict[str, Any]:
    claimed_grade = int(state.get("diagnostic_progress", {}).get("claimed_grade") or state.get("grade") or 1)
    answers = list(state.get("diag_answers", []))
    result = diagnostic_engine.run_diagnostic(claimed_grade, answers)
    weak_topic = diagnostic_engine.select_weak_topic(result)

    if result.weak_topics:
        explanation_state = {
            "phase": "explanation",
            "in_learning": True,
            "diagnostic_progress": {},
            "weak_topic": weak_topic,
            "current_practice": None,
            "practice_feedback": None,
            "report": None,
            "diag_answers": [],
            "diag_sequence": [],
        }
        update_user_state(user_id, explanation_state)
        state = get_user_state(user_id)
        topic_name = weak_topic["topic"] if weak_topic else "тема"
        text = (
            "🎯 Диагностика завершена.\n\n"
            f"Слабая тема: {topic_name}.\n"
            "Сейчас коротко объясню, потом начнём практику.\n"
            "Напиши 'начать'."
        )
        return _panda_response(text, state, visual={"type": "weak_topic", "topic": weak_topic})

    starting_topic = diagnostic_engine.get_starting_topic(result.actual_grade)
    practice = practice_engine.create_practice(starting_topic)
    practice_state = {
        "phase": "practice",
        "in_learning": True,
        "diagnostic_progress": {},
        "weak_topic": starting_topic,
        "current_practice": practice,
        "practice_feedback": None,
        "report": None,
        "diag_answers": [],
        "diag_sequence": [],
    }
    update_user_state(user_id, practice_state)
    state = get_user_state(user_id)
    text = (
        "🎉 Диагностика завершена.\n\n"
        f"Начинаем с темы: {starting_topic['topic']}.\n"
        "Давай сразу к практике."
    )
    return _panda_response(text, state, visual={"type": "practice", "practice": practice})


@router.post("/panda/chat")
async def panda_chat(request: ChatRequest) -> dict[str, Any]:
    user_id = request.user_id
    message = request.message.strip()

    if request.name:
        update_user_state(user_id, {"name": request.name})
    if request.grade and request.grade > 0:
        update_user_state(user_id, {"grade": request.grade})

    state = get_user_state(user_id)
    state = _ensure_state_defaults(state)

    if request.name and not state.get("name"):
        state = update_user_state(user_id, {"name": request.name})
    if request.grade and request.grade > 0 and not state.get("grade"):
        state = update_user_state(user_id, {"grade": request.grade})

    if not state.get("name"):
        return _panda_response(
            "Привет! Как тебя зовут?",
            state,
        )

    if not state.get("grade"):
        return _panda_response(
            f"Отлично, {state['name']}! В каком ты классе?",
            state,
        )

    if state.get("phase") == "diagnostic":
        question = _current_question(state)
        if question is None:
            state = _finish_diagnostic(user_id, state)
            return state

        is_correct = _is_answer_correct(message, question)
        answers = list(state.get("diag_answers", []))
        answers.append(
            {
                "question_id": question.get("id"),
                "grade": question.get("grade", state.get("grade", 1)),
                "topic_id": question.get("topic_id"),
                "topic": question.get("topic"),
                "user_answer": message,
                "is_correct": is_correct,
            }
        )
        progress = dict(state.get("diagnostic_progress", {}))
        progress["questions_answered"] = int(progress.get("questions_answered", 0)) + 1
        progress["correct_in_row"] = int(progress.get("correct_in_row", 0)) + (1 if is_correct else 0)
        update_user_state(
            user_id,
            {
                "diagnostic_progress": progress,
                "diag_answers": answers,
            },
        )
        state = get_user_state(user_id)

        sequence = list(state.get("diag_sequence", []))
        if progress["questions_answered"] >= len(sequence):
            state = _finish_diagnostic(user_id, state)
            return state

        next_question = sequence[progress["questions_answered"]]
        text = (
            "Верно!" if is_correct else f"Почти. Правильный ответ: {question['answer']}"
        )
        text += f"\n\nСледующий вопрос: {next_question['question']}"
        return _panda_response(text, state, visual={"type": "question", "topic_id": next_question.get("topic_id")})

    if _is_diagnostic_start(message):
        state = _start_diagnostic(user_id, state)
        first_question = _current_question(state)
        if first_question is None:
            return _panda_response("Диагностика недоступна: нет вопросов.", state)
        text = (
            "Начинаем диагностику.\n\n"
            f"{first_question['question']}"
        )
        return _panda_response(text, state, visual={"type": "question", "topic_id": first_question.get("topic_id")})

    if state.get("phase") == "explanation":
        weak_topic = state.get("weak_topic") or diagnostic_engine.get_starting_topic(int(state.get("grade") or 1))
        if _is_explanation_start(message):
            practice = practice_engine.create_practice(weak_topic)
            state = update_user_state(
                user_id,
                {
                    "phase": "practice",
                    "current_practice": practice,
                    "practice_feedback": None,
                    "report": None,
                },
            )
            text = (
                f"Отлично. Практика по теме '{weak_topic['topic']}'.\n\n"
                f"{practice['question']}"
            )
            return _panda_response(text, state, visual={"type": "practice", "topic_id": practice.get("topic_id")})

        text = (
            f"Разберём тему '{weak_topic['topic']}'.\n"
            "Напиши 'начать', когда будешь готов к практике."
        )
        return _panda_response(text, state, visual={"type": "explanation", "topic_id": weak_topic.get("topic_id")})

    if state.get("phase") == "practice":
        practice = state.get("current_practice")
        if not practice:
            weak_topic = state.get("weak_topic") or diagnostic_engine.get_starting_topic(int(state.get("grade") or 1))
            practice = practice_engine.create_practice(weak_topic)
            state = update_user_state(user_id, {"current_practice": practice})

        feedback = practice_engine.check_practice_answer(practice, message)
        report = report_service.build_report({"weak_topic": state.get("weak_topic") or practice}, feedback)
        state = update_user_state(
            user_id,
            {
                "phase": "report",
                "practice_feedback": feedback,
                "report": report,
                "current_practice": practice,
            },
        )
        text = (
            "Отлично! " if feedback["is_correct"] else "Почти. "
        ) + report["summary"]
        return _panda_response(text, state, visual={"type": "report", "practice_result": report["practice_result"]})

    if state.get("phase") == "report":
        report = state.get("report") or report_service.build_report(state.get("weak_topic"), state.get("practice_feedback"))
        text = report["summary"]
        return _panda_response(text, state, visual={"type": "report", "practice_result": report["practice_result"]})

    return _panda_response(
        f"Привет, {state['name']}! Напиши 'диагностика', чтобы начать учёбу.",
        state,
    )
