from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from deeptutor.services.diagnostic_engine import DiagnosticEngine, diagnostic_engine
from deeptutor.services.error_taxonomy import error_taxonomy
from deeptutor.services.learning_rag import learning_rag
from deeptutor.services.mastery_evaluator import mastery_evaluator
from deeptutor.services.practice_engine import PracticeEngine
from deeptutor.services.report_service import ReportService
from deeptutor.services.skill_runtime import skill_resolver
from deeptutor.services.teacher_llm import generate_teacher_reply
from deeptutor.services.visual_template_service import decorate_question_visual

generate_teacher_explanation = generate_teacher_reply

router = APIRouter()
STATE_FILE = Path(__file__).resolve().parents[3] / "data" / "user_states.json"

practice_engine = PracticeEngine()
report_service = ReportService()


class ChatRequest(BaseModel):
    user_id: str
    message: str
    name: str | None = None
    grade: int | None = Field(default=None, ge=0)
    mode: str | None = None


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
    "learning_context": None,
    "teacher_explanation": None,
    "current_practice": None,
    "practice_feedback": None,
    "report": None,
    "current_skill_id": None,
    "current_skill_version": None,
    "current_skill_mode": None,
    "current_topic_id": None,
    "current_lesson_id": None,
    "diagnosis_result_id": None,
    "diagnosis_confidence": None,
    "detected_gaps": [],
    "explanation_ack_pending": False,
    "explanation_shown_for_skill_id": None,
    "learning_mode_active": False,
    "board_mode": "off",
    "mastery_status_by_skill": {},
    "mastery_check_pending": False,
    "mastery_check_result": None,
    "promotion_eligible": False,
    "registry_resolution": {"source": "fallback", "resolved_at": None, "warnings": []},
    "runtime_audit_log": [],
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


def _refresh_stale_diagnostic_state(user_id: str, state: dict[str, Any]) -> dict[str, Any]:
    if not state:
        return state
    if state.get("phase") != "diagnostic":
        return state

    progress = dict(state.get("diagnostic_progress") or {})
    questions_answered = int(progress.get("questions_answered", 0) or 0)
    if questions_answered != 0:
        return state

    claimed_grade = int(progress.get("claimed_grade") or state.get("grade") or 1)
    fresh_sequence = diagnostic_engine.build_diagnostic_sequence(claimed_grade)
    if not fresh_sequence:
        return state

    current_sequence = list(state.get("diag_sequence") or [])
    current_first = str((current_sequence[0] or {}).get("id") or (current_sequence[0] or {}).get("topic_id") or "") if current_sequence else ""
    fresh_first = str((fresh_sequence[0] or {}).get("id") or (fresh_sequence[0] or {}).get("topic_id") or "")
    if current_first == fresh_first:
        return state

    refreshed_state = dict(state)
    refreshed_state["diag_sequence"] = fresh_sequence
    refreshed_state["diag_answers"] = []
    refreshed_progress = dict(progress)
    refreshed_progress["questions_answered"] = 0
    refreshed_progress["correct_in_row"] = 0
    refreshed_progress["in_diagnostic"] = True
    refreshed_progress["claimed_grade"] = claimed_grade
    refreshed_state["diagnostic_progress"] = refreshed_progress

    states = _read_states()
    states[user_id] = refreshed_state
    save_user_states(states)
    return refreshed_state


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
    return _refresh_stale_diagnostic_state(user_id, merged)


def update_user_state(user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    states = _read_states()
    state = _fresh_state()
    state.update(states.get(user_id, {}))
    for key, value in updates.items():
        if value is None:
            state.pop(key, None)
        else:
            state[key] = value
    states[user_id] = state
    save_user_states(states)
    return state


def _ensure_state_defaults(state: dict[str, Any]) -> dict[str, Any]:
    merged = _fresh_state()
    merged.update(state or {})
    return merged


def _append_runtime_audit_log(user_id: str, event_type: str, payload: dict[str, Any]) -> None:
    state = get_user_state(user_id)
    runtime_audit_log = list(state.get("runtime_audit_log") or [])
    runtime_audit_log.append({"event_type": event_type, **payload})
    if len(runtime_audit_log) > 200:
        runtime_audit_log = runtime_audit_log[-200:]
    update_user_state(user_id, {"runtime_audit_log": runtime_audit_log})


def _update_mastery_status(
    state: dict[str, Any],
    skill_id: str | None,
    *,
    status: str,
    confidence: float | None = None,
    attempts_delta: int = 0,
    correct: bool | None = None,
    attempt_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not skill_id:
        return state
    mastery_status_by_skill = dict(state.get("mastery_status_by_skill") or {})
    current = dict(mastery_status_by_skill.get(skill_id) or {})
    current["status"] = status
    current["last_seen_at"] = current.get("last_seen_at") or "now"
    current["attempts_count"] = int(current.get("attempts_count") or 0) + attempts_delta
    if confidence is not None:
        current["confidence"] = confidence

    if correct is not None:
        current["correct_count"] = int(current.get("correct_count") or 0) + (1 if correct else 0)
        current["wrong_count"] = int(current.get("wrong_count") or 0) + (0 if correct else 1)
        current["correct_streak"] = int(current.get("correct_streak") or 0) + (1 if correct else 0)
        current["wrong_streak"] = 0 if correct else int(current.get("wrong_streak") or 0) + 1
        current["last_correct"] = bool(correct)

    attempt_history = list(current.get("attempt_history") or [])
    if attempt_record is not None:
        attempt_history.append(dict(attempt_record))
        current["attempt_history"] = attempt_history[-10:]

    mastery_status_by_skill[skill_id] = current
    state["mastery_status_by_skill"] = mastery_status_by_skill
    return state


def _is_diagnostic_start(message: str) -> bool:
    text = message.lower()
    return "диагност" in text or "провер" in text or "старт" in text


def _is_explanation_start(message: str) -> bool:
    text = message.lower()
    return "начать" in text or "практик" in text or "давай" in text


def _is_followup_request(message: str) -> bool:
    text = message.lower()
    return any(token in text for token in ("что дальше", "дальше", "продолж", "ещё", "еще", "следующ", "потом"))


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



def _learning_context_for_topic(grade: int, topic: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not topic:
        return []
    query_parts = [str(topic.get("topic") or ""), str(topic.get("topic_id") or "")]
    query = " ".join(part for part in query_parts if part).strip()
    return learning_rag.retrieve(
        grade=grade,
        query=query or str(topic.get("topic") or "тема"),
        topic_id=str(topic.get("topic_id")) if topic.get("topic_id") is not None else None,
        top_k=3,
    )


def _panda_response(text: str, state: dict[str, Any], visual: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized_state = _ensure_state_defaults(state)
    normalized_state.setdefault("phase", "chat")
    normalized_state.setdefault("weak_topic", None)
    normalized_state.setdefault("learning_context", None)
    normalized_state.setdefault("teacher_explanation", None)
    normalized_state.setdefault("current_practice", None)
    normalized_state.setdefault("practice_feedback", None)
    normalized_state.setdefault("report", None)
    return {"text": text, "visual": visual, "state": normalized_state}


def _question_visual(question: dict[str, Any]) -> dict[str, Any]:
    return decorate_question_visual(question)


def _start_diagnostic(user_id: str, state: dict[str, Any]) -> dict[str, Any]:
    claimed_grade = int(state.get("grade") or 1)
    sequence = diagnostic_engine.build_diagnostic_sequence(claimed_grade)
    if not sequence:
        sequence = [diagnostic_engine.get_questions_for_grade(1)[0]] if diagnostic_engine.get_questions_for_grade(1) else []
    diag_state = {
        "phase": "diagnostic",
        "path_choice": "diagnostic",
        "in_learning": False,
        "learning_mode_active": False,
        "board_mode": "off",
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
        "current_skill_id": None,
        "current_skill_version": None,
        "current_skill_mode": None,
        "current_topic_id": None,
        "current_lesson_id": None,
        "diagnosis_result_id": None,
        "diagnosis_confidence": None,
        "detected_gaps": [],
        "explanation_ack_pending": False,
        "explanation_shown_for_skill_id": None,
        "runtime_audit_log": list(state.get("runtime_audit_log") or []),
        "registry_resolution": {"source": "shadow", "resolved_at": None, "warnings": []},
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
    start_topic = weak_topic or diagnostic_engine.get_starting_topic(result.actual_grade)
    resolution = skill_resolver.resolve(
        topic_id=str(start_topic.get("topic_id") or ""),
        topic_name=str(start_topic.get("topic") or ""),
        lesson_id=str(start_topic.get("lesson_id") or "") or None,
    )
    contract_summary = skill_resolver.skill_summary(resolution)["contract_summary"]
    learning_context = _learning_context_for_topic(result.actual_grade, start_topic)

    summary_line = result.get_learning_path()["message"].splitlines()[0]
    topic_name = str(start_topic.get("topic") or "тема")
    if result.weak_topics:
        text = (
            f"Видна слабая тема — {topic_name}.\n\n"
            f"{summary_line}\n\n"
            "Скажи «давай», и я начну объяснение."
        )
    else:
        text = (
            "База выглядит крепкой.\n\n"
            f"{summary_line}\n\n"
            "Скажи «давай», и я дам следующий шаг."
        )

    next_state = {
        "phase": "explanation",
        "in_learning": True,
        "learning_mode_active": True,
        "board_mode": skill_resolver.apply_board_policy(resolution, default="off"),
        "diagnostic_progress": {},
        "weak_topic": start_topic,
        "learning_context": learning_context,
        "teacher_explanation": None,
        "current_practice": None,
        "practice_feedback": None,
        "report": None,
        "diag_answers": [],
        "diag_sequence": [],
        "current_skill_id": resolution.skill_id,
        "current_skill_version": resolution.skill_version,
        "current_skill_mode": resolution.mode,
        "current_topic_id": resolution.topic_id,
        "current_lesson_id": resolution.lesson_id,
        "diagnosis_result_id": f"diag_{result.actual_grade}_{len(answers)}_{len(result.weak_topics)}",
        "diagnosis_confidence": result.success_rate,
        "detected_gaps": [topic.get("skill_id") or topic.get("topic_id") for topic in result.weak_topics],
        "explanation_ack_pending": True,
        "explanation_shown_for_skill_id": resolution.skill_id,
        "registry_resolution": {
            "source": resolution.source,
            "resolved_at": "now",
            "warnings": list(resolution.warnings),
            "contract_summary": contract_summary,
        },
    }
    state = update_user_state(user_id, next_state)
    _append_runtime_audit_log(
        user_id,
        "skill_resolved",
        {
            "mode": resolution.mode,
            "topic_id": resolution.topic_id,
            "skill_id": resolution.skill_id,
            "skill_version": resolution.skill_version,
            "decision": "diagnostic_finish_to_explanation",
            "reason": "diagnostic_completed",
            "active": resolution.mode == "active",
        },
    )
    return _panda_response(text, state)


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

    if state.get("phase") == "chat" and not state.get("onboarding_complete"):
        if request.mode == "kungfu":
            state = _start_diagnostic(user_id, state)
            state = update_user_state(user_id, {"onboarding_complete": True, "path_choice": "kungfu"})
            first_question = _current_question(state)
            if first_question is None:
                return _panda_response("Диагностика недоступна: нет вопросов.", state)
            teacher_intro = generate_teacher_reply(
                stage="diagnostic_start",
                grade=int(state.get("grade") or 1),
                weak_topic=None,
                learning_context=list(state.get("learning_context") or []),
                user_message=message,
            )
            text = (
                f"{teacher_intro}\n\n"
                f"{first_question['question']}"
            )
            return _panda_response(text, state, visual=_question_visual(first_question))

        if request.mode == "homework":
            state = update_user_state(user_id, {"onboarding_complete": True, "path_choice": "homework"})
            text = (
                f"Привет, {state['name']}! Я помогу с математикой.\n\n"
                "Какую тему или задачу разбираем прямо сейчас?"
            )
            return _panda_response(text, state)

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
                "skill_id": question.get("skill_id"),
                "coverage_status": question.get("coverage_status"),
                "board_policy": question.get("board_policy"),
                "skill_contract_id": question.get("skill_contract_id"),
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
        return _panda_response(text, state, visual=_question_visual(next_question))

    if _is_diagnostic_start(message):
        state = _start_diagnostic(user_id, state)
        first_question = _current_question(state)
        if first_question is None:
            return _panda_response("Диагностика недоступна: нет вопросов.", state)
        teacher_intro = generate_teacher_reply(
            stage="diagnostic_start",
            grade=int(state.get("grade") or 1),
            weak_topic=None,
            learning_context=list(state.get("learning_context") or []),
            user_message=message,
        )
        text = (
            f"{teacher_intro}\n\n"
            f"{first_question['question']}"
        )
        return _panda_response(text, state, visual=_question_visual(first_question))

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
                    "learning_mode_active": True,
                    "explanation_ack_pending": False,
                    "explanation_shown_for_skill_id": state.get("current_skill_id"),
                    "board_mode": skill_resolver.apply_board_policy(
                        skill_resolver.resolve(topic_id=str(weak_topic.get("topic_id") or ""), topic_name=str(weak_topic.get("topic") or "")),
                        default=str(state.get("board_mode") or "off"),
                    ),
                },
            )
            _append_runtime_audit_log(
                user_id,
                "contract_applied",
                {
                    "mode": state.get("current_skill_mode") or "shadow",
                    "topic_id": weak_topic.get("topic_id"),
                    "skill_id": state.get("current_skill_id"),
                    "skill_version": state.get("current_skill_version"),
                    "decision": "explanation_to_practice",
                    "reason": "student_acknowledged_explanation",
                    "active": (state.get("current_skill_mode") or "shadow") == "active",
                },
            )
            text = generate_teacher_reply(
                stage="practice_intro",
                grade=int(state.get("grade") or 1),
                weak_topic=weak_topic,
                learning_context=list(state.get("learning_context") or []),
                user_message=message,
                practice_question=practice["question"],
            )
            return _panda_response(text, state, visual=_question_visual(practice))

        text = generate_teacher_reply(
            stage="explanation",
            grade=int(state.get("grade") or 1),
            weak_topic=weak_topic,
            learning_context=list(state.get("learning_context") or []),
            user_message=message,
        )
        return _panda_response(text, state, visual={"type": "explanation", "topic_id": weak_topic.get("topic_id")})

    if state.get("phase") == "practice":
        practice = state.get("current_practice")
        if not practice:
            weak_topic = state.get("weak_topic") or diagnostic_engine.get_starting_topic(int(state.get("grade") or 1))
            practice = practice_engine.create_practice(weak_topic)
            state = update_user_state(user_id, {"current_practice": practice})

        feedback = practice_engine.check_practice_answer(practice, message)
        skill_resolution = skill_resolver.resolve(
            topic_id=str(practice.get("topic_id") or ""),
            topic_name=str((state.get("weak_topic") or {}).get("topic") or ""),
        )
        error_details = error_taxonomy.classify_practice_error(practice, feedback, skill_resolution.contract)
        feedback = {**feedback, **error_details}
        report = report_service.build_report(state.get("weak_topic") or practice, feedback)
        state = update_user_state(
            user_id,
            {
                "phase": "report" if feedback["is_correct"] else "practice",
                "practice_feedback": feedback,
                "report": report,
                "current_practice": practice,
                "mastery_check_pending": False,
                "promotion_eligible": False,
            },
        )
        state = _update_mastery_status(
            state,
            skill_resolution.skill_id or state.get("current_skill_id"),
            status="practicing" if not feedback["is_correct"] else "learning",
            confidence=feedback.get("confidence"),
            attempts_delta=1,
            correct=bool(feedback["is_correct"]),
            attempt_record={
                "question_id": practice.get("id"),
                "topic_id": practice.get("topic_id"),
                "is_correct": bool(feedback["is_correct"]),
                "confidence": feedback.get("confidence"),
                "user_answer": feedback.get("user_answer"),
                "correct_answer": feedback.get("correct_answer"),
                "error_code": feedback.get("error_code"),
                "error_family": feedback.get("error_family"),
                "remediation_path": feedback.get("remediation_path"),
            },
        )
        mastery_state = (state.get("mastery_status_by_skill") or {}).get(skill_resolution.skill_id or state.get("current_skill_id") or "", {})
        mastery_decision = mastery_evaluator.evaluate(
            skill_id=skill_resolution.skill_id or state.get("current_skill_id"),
            contract=skill_resolution.contract,
            mastery_state=mastery_state,
        )
        mastery_result = {
            "skill_id": mastery_decision.skill_id,
            "decision": mastery_decision.decision,
            "confidence": mastery_decision.confidence,
            "reasons": list(mastery_decision.reasons),
            "failed_criteria": list(mastery_decision.failed_criteria),
            "evidence": dict(mastery_decision.evidence),
        }
        state = update_user_state(
            user_id,
            {
                "mastery_check_result": mastery_result,
                "promotion_eligible": mastery_decision.decision == "mastered",
                "mastery_check_pending": mastery_decision.decision == "mastered",
            },
        )
        if mastery_decision.decision == "mastered":
            state = update_user_state(user_id, {"phase": "mastery_check"})
        state = update_user_state(user_id, {"mastery_status_by_skill": state.get("mastery_status_by_skill") or {}})
        _append_runtime_audit_log(
            user_id,
            "mastery_evaluated",
            {
                "skill_id": mastery_result["skill_id"],
                "decision": mastery_result["decision"],
                "confidence": mastery_result["confidence"],
                "passed_criteria": [reason for reason in mastery_result["reasons"] if reason not in {"accuracy_threshold_not_met", "streak_not_met", "not_enough_attempts"}],
                "failed_criteria": mastery_result["failed_criteria"],
                "source": "backend_mastery_evaluator",
            },
        )
        text = generate_teacher_reply(
            stage="practice_result",
            grade=int(state.get("grade") or 1),
            weak_topic=state.get("weak_topic") or practice,
            learning_context=list(state.get("learning_context") or []),
            user_message=message,
            practice_question=practice.get("question", ""),
            practice_feedback=feedback,
            report=report,
        )
        if mastery_decision.decision == "mastered":
            text = f"{text}\n\n🎯 Навык этой цепочки пока закрыт по backend-оценке."
        visual = {"type": "report", "practice_result": report["practice_result"]} if feedback["is_correct"] else _question_visual(practice)
        return _panda_response(text, state, visual=visual)

    if state.get("phase") == "mastery_check":
        mastery_result = state.get("mastery_check_result") or {}
        skill_id = mastery_result.get("skill_id") or state.get("current_skill_id")
        text = (
            "🎯 Навык подтверждён backend-оценкой.\n\n"
            f"skill_id: {skill_id}\n"
            "Сейчас цепочка остаётся в контролируемом hardening-режиме, без расширения ширины."
        )
        visual = {"type": "report", "mastery_result": mastery_result}
        return _panda_response(text, state, visual=visual)

    if state.get("phase") == "report":
        report = state.get("report") or report_service.build_report(state.get("weak_topic"), state.get("practice_feedback"))
        topic = report.get("weak_topic") or state.get("weak_topic") or state.get("current_practice") or {}
        practice_round = int(state.get("practice_round") or 0) + 1
        next_practice = practice_engine.create_practice(topic, variant=practice_round)
        state = update_user_state(
            user_id,
            {
                "phase": "practice",
                "practice_round": practice_round,
                "current_practice": next_practice,
                "practice_feedback": None,
                "report": None,
            },
        )
        text = generate_teacher_reply(
            stage="practice_intro",
            grade=int(state.get("grade") or 1),
            weak_topic=topic,
            learning_context=list(state.get("learning_context") or []),
            user_message=message,
            practice_question=next_practice.get("question", ""),
        )
        return _panda_response(text, state, visual=_question_visual(next_practice))

    return _panda_response(
        f"Привет, {state['name']}! Напиши 'диагностика', чтобы начать учёбу.",
        state,
    )
