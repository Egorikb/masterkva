from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from deeptutor.services.curricular_lesson_runtime import (
    CurriculumResolutionError,
    ResolvedCurricularLesson,
    curricular_lesson_runtime,
)
from deeptutor.services.diagnostic_engine import DiagnosticEngine, diagnostic_engine
from deeptutor.services.error_taxonomy import error_taxonomy
from deeptutor.services.learning_rag import learning_rag
from deeptutor.services.mastery_evaluator import mastery_evaluator
from deeptutor.services.practice_engine import PracticeEngine
from deeptutor.services.report_service import ReportService
from deeptutor.services.skill_runtime import skill_resolver
from deeptutor.services.student_profile_store import (
    ensure_student_profile,
    get_student_profile,
    record_diagnostic_result,
    record_learning_pause,
    record_mastery_evaluation,
    record_practice_attempt,
    record_promotion,
)
from deeptutor.services.state_storage import read_states, write_states
from deeptutor.services.progress_analytics import get_progress_summary
from deeptutor.services.remediation_engine import remediation_engine
from deeptutor.services.teacher_llm import generate_teacher_explanation, generate_teacher_reply
from deeptutor.services.visual_template_service import decorate_question_visual

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
    lesson_id: str | None = None
    content_version: str | None = None
    action: Literal["start", "answer", "hint", "advance"] | None = None


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
    "current_content_version": None,
    "curricular_session": None,
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
    "mastery_gate_status": "idle",
    "promotion_eligible": False,
    "registry_resolution": {"source": "fallback", "resolved_at": None, "warnings": []},
    "runtime_audit_log": [],
    "phase_before_pause": None,
    "paused_context": None,
    "student_profile": {
        "profile_schema_version": "v1",
        "user_id": None,
        "active_scope": {
            "chain_id": "g1_to_g2_addition",
            "allowed_skill_ids": ["g1_counting_core", "g2_addition_core"],
            "current_skill_id": None,
            "current_topic_id": None,
            "current_grade": None,
            "updated_at": None,
        },
        "skill_mastery": {},
        "diagnostic_history": [],
        "mastery_history": [],
        "promotion_history": [],
        "learning_memory": {
            "last_topics": [],
            "weak_topic_queue": [],
            "mastered_weak_topics": [],
            "misconceptions": {},
            "teaching_actions": [],
        },
        "session_status": {
            "status": "active",
            "reason": None,
            "paused_at": None,
            "resumed_at": None,
            "resume_phase": None,
            "resume_topic_id": None,
            "resume_topic": None,
            "resume_skill_id": None,
        },
        "activity_counters": {
            "diagnostic_sessions": 0,
            "practice_sessions": 0,
            "mastery_checks": 0,
            "promotions": 0,
        },
        "last_updated_at": None,
    },
}


def _fresh_state() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_STATE, ensure_ascii=False))


def _read_states() -> dict[str, dict[str, Any]]:
    return read_states(STATE_FILE)


def save_user_states(states: dict[str, dict[str, Any]]) -> None:
    write_states(STATE_FILE, states)


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


def _skill_entry_by_id(skill_id: str | None) -> dict[str, Any] | None:
    normalized_skill_id = str(skill_id or "").strip()
    if not normalized_skill_id:
        return None
    for skill in skill_resolver.registry.get("skills", []):
        if str(skill.get("skill_id") or "").strip() == normalized_skill_id:
            return dict(skill)
    return None


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


def _record_mastery_gate_result(
    state: dict[str, Any],
    *,
    skill_id: str | None,
    decision: str,
    confidence: float,
    reasons: list[str],
    failed_criteria: list[str],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    if not skill_id:
        return state
    mastery_status_by_skill = dict(state.get("mastery_status_by_skill") or {})
    current = dict(mastery_status_by_skill.get(skill_id) or {})
    current["last_mastery_decision"] = decision
    current["last_mastery_confidence"] = confidence
    current["last_mastery_reasons"] = list(reasons)
    current["last_mastery_failed_criteria"] = list(failed_criteria)
    current["last_mastery_evidence"] = dict(evidence)
    current["last_mastery_at"] = "now"
    mastery_status_by_skill[skill_id] = current
    state["mastery_status_by_skill"] = mastery_status_by_skill
    state["mastery_gate_status"] = decision
    state["mastery_check_result"] = {
        "skill_id": skill_id,
        "decision": decision,
        "confidence": confidence,
        "reasons": list(reasons),
        "failed_criteria": list(failed_criteria),
        "evidence": dict(evidence),
    }
    state["promotion_eligible"] = decision == "mastered"
    state["mastery_check_pending"] = decision == "mastered"
    if decision == "mastered":
        state["phase"] = "mastery_check"
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


def _is_stop_intent(message: str) -> bool:
    text = f" {message.lower().strip()} "
    stop_tokens = (
        " хватит ",
        " стоп ",
        " остановись ",
        " пауза ",
        " устал ",
        " устала ",
        " не хочу ",
        " закончили ",
        " на сегодня всё ",
        " на сегодня все ",
        " достаточно ",
    )
    return any(token in text for token in stop_tokens)


def _is_answer_correct(answer: str, question: dict[str, Any]) -> bool:
    user = str(answer).strip().lower()
    correct = str(question.get("answer", "")).strip().lower()
    if user == correct:
        return True
    alternatives = {str(item).strip().lower() for item in question.get("alternatives", [])}
    if user in alternatives:
        return True

    number_pattern = r"[+-]?\d+(?:[.,]\d+)?"
    measurement_pattern = rf"^\s*({number_pattern})\s*([^\W\d_]+)?\s*$"
    user_match = re.fullmatch(measurement_pattern, user, re.IGNORECASE)
    correct_match = re.fullmatch(measurement_pattern, correct, re.IGNORECASE)
    if user_match and correct_match:
        user_number, user_unit = user_match.groups()
        correct_number, correct_unit = correct_match.groups()
        # Do not accept a different unit merely because its digits match.
        if correct_unit is not None and user_unit != correct_unit:
            return False
        return user_number.replace(",", ".") == correct_number.replace(",", ".")
    return False


def _strip_followup_question(text: str) -> str:
    """Remove trailing 'want more?' type questions from LLM output."""
    import re
    # Only remove specific follow-up patterns, don't cut mid-sentence
    patterns = [
        r"(?:\n\n|\s)Хочешь[^\n.!?]*\??$",
        r"(?:\n\n|\s)Готов[^\n.!?]*\??$",
        r"(?:\n\n|\s)Продолж[^\n.!?]*\??$",
        r"(?:\n\n|\s)Ещё[^\n.!?]*\??$",
        r"(?:\n\n|\s)Еще[^\n.!?]*\??$",
        r"(?:\n\n|\s)Давай[^\n.!?]*\??$",
        r"(?:\n\n|\s)Скажи[^\n.!?]*(?:давай|продолж)[^\n.!?]*\??$",
        r"(?:\n\n|\s)Если хочешь[^\n.!?]*$",
    ]
    result = text
    for pattern in patterns:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.MULTILINE)
    return result.strip()


def _pause_learning(user_id: str, state: dict[str, Any], message: str) -> dict[str, Any]:
    weak_topic = state.get("weak_topic") or {}
    practice = state.get("current_practice") or {}
    topic_id = str(weak_topic.get("topic_id") or practice.get("topic_id") or state.get("current_topic_id") or "")
    topic_name = str(weak_topic.get("topic") or practice.get("title") or "текущая тема")
    resume_phase = str(state.get("phase") or "chat")
    if resume_phase == "paused":
        paused_context = dict(state.get("paused_context") or {})
        resume_phase = str(paused_context.get("phase") or state.get("phase_before_pause") or "chat")

    paused_context = {
        "phase": resume_phase,
        "topic_id": topic_id or None,
        "topic": topic_name,
        "skill_id": state.get("current_skill_id"),
        "practice_id": practice.get("id"),
        "paused_at": datetime.now(timezone.utc).isoformat(),
    }
    profile = record_learning_pause(
        user_id,
        status="paused",
        reason=message,
        resume_phase=resume_phase,
        resume_topic_id=topic_id or None,
        resume_topic=topic_name,
        resume_skill_id=state.get("current_skill_id"),
    )
    updated = update_user_state(
        user_id,
        {
            "phase": "paused",
            "phase_before_pause": resume_phase,
            "paused_context": paused_context,
            "learning_mode_active": False,
            "in_learning": False,
            "student_profile": profile,
        },
    )
    text = f"Хорошо, остановимся здесь. Я сохраню место: продолжим с темы «{topic_name}»."
    return _panda_response(text, updated)


def _resume_paused_learning(user_id: str, state: dict[str, Any]) -> dict[str, Any]:
    paused_context = dict(state.get("paused_context") or {})
    resume_phase = str(paused_context.get("phase") or state.get("phase_before_pause") or "chat")
    topic_name = str(paused_context.get("topic") or (state.get("weak_topic") or {}).get("topic") or "текущая тема")
    profile = record_learning_pause(
        user_id,
        status="active",
        reason="resume",
        resume_phase=resume_phase,
        resume_topic_id=paused_context.get("topic_id"),
        resume_topic=topic_name,
        resume_skill_id=paused_context.get("skill_id") or state.get("current_skill_id"),
    )
    state = update_user_state(
        user_id,
        {
            "phase": resume_phase,
            "learning_mode_active": resume_phase in {"diagnostic", "practice", "remediation", "explanation", "mastery_check"},
            "in_learning": resume_phase in {"practice", "remediation", "explanation", "mastery_check"},
            "student_profile": profile,
        },
    )

    if resume_phase == "diagnostic":
        question = _current_question(state)
        if question:
            return _panda_response(f"Продолжим диагностику.\n\n{question['question']}", state, visual=_question_visual(question))

    if resume_phase == "remediation":
        remediation = remediation_engine.get_state(user_id)
        if remediation and remediation.current_step:
            return _panda_response(
                f"Продолжим с маленького шага по теме «{topic_name}».\n\n{remediation.current_step.question}",
                state,
                visual=_question_visual({"question": remediation.current_step.question}),
            )

    practice = state.get("current_practice")
    if practice:
        return _panda_response(
            f"Продолжим с темы «{topic_name}».\n\n{practice['question']}",
            state,
            visual=_question_visual(practice),
        )

    return _panda_response(f"Продолжим с темы «{topic_name}».", state)


def _get_scaffolding_visual(remediation) -> str:
    """Get visual hint for scaffolding level 1."""
    visual_hint = remediation.remediation_path
    if not visual_hint:
        return ""
    visual_names = {
        "number_bond": "Посмотри на числовой домик:",
        "ten_frame": "Посчитай на десятирамке:",
        "number_line": "Посмотри на числовую прямую:",
        "base_ten_blocks": "Представь блоки десятков:",
        "clock_face": "Посмотри на часы:",
        "time_unit_table": "Вспомни: 1 час = 60 минут.",
    }
    return visual_names.get(visual_hint, f"Подсказка: {visual_hint}")


def _get_scaffolding_step_by_step(remediation) -> str:
    """Get step-by-step hint for scaffolding level 2."""
    item_family = remediation.item_family
    if "addition" in item_family or "compose" in item_family:
        return "Давай по шагам: 1) Найди первое число. 2) Прибавь второе. 3) Если сумма больше 10 — запиши единицу и переноси десяток."
    if "subtraction" in item_family:
        return "Давай по шагам: 1) Найди первое число. 2) Вычти второе. 3) Если не хватает — займи десяток."
    if "time" in item_family:
        return "Вспомни: 1 час = 60 минут. Умножь часы на 60."
    return "Давай разберём по шагам. Сначала подумай, что нужно сделать."



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
    ensure_student_profile(user_id)
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
        "blocked_skill_ids": [],
        "remediation_targets": {},
        "diagnostic_gap_status": None,
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


def _should_end_diagnostic(state: dict[str, Any]) -> bool:
    """Check if diagnostic should end early based on wrong answers threshold.

    Ends early if:
    - 3 or more wrong answers in a row (consecutive failures)
    - All questions in the sequence have been answered
    """
    progress = dict(state.get("diagnostic_progress", {}))
    answers = list(state.get("diag_answers", []))
    sequence = list(state.get("diag_sequence", []))

    # End if all questions answered
    questions_answered = int(progress.get("questions_answered", 0))
    if questions_answered >= len(sequence):
        return True

    # End if 3 consecutive wrong answers
    if len(answers) >= 3:
        last_3 = answers[-3:]
        if all(not a.get("is_correct", False) for a in last_3):
            return True

    # End if 5 total wrong answers (across all answered questions)
    wrong_count = sum(1 for a in answers if not a.get("is_correct", False))
    if wrong_count >= 5:
        return True

    return False


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
    remediation_targets = dict(contract_summary.get("remediation_targets") or {})
    blocked_skill_ids = list(resolution.next_skills or [])
    diagnostic_gap_status = "diagnosed_gap" if result.weak_topics else "clear"

    # Build diagnostic summary text (backend-owned, no LLM)
    topic_name = str(start_topic.get("topic") or "тема")
    if result.weak_topics:
        text = (
            f"Диагностика завершена.\n\n"
            f"Вижу слабую тему — {topic_name}.\n\n"
            f"Начнём разбор. Слушай внимательно."
        )
    else:
        text = (
            "Диагностика завершена.\n\n"
            "База выглядит крепкой.\n\n"
            f"Начнём с темы «{topic_name}». Слушай внимательно."
        )

    # Generate explanation via LLM (pedagogical text only, not questions)
    explanation_text = generate_teacher_reply(
        stage="explanation",
        grade=result.actual_grade,
        weak_topic=start_topic,
        learning_context=learning_context,
        user_message="",
    )

    # Create first practice question
    practice = practice_engine.create_practice(start_topic)

    next_state = {
        "phase": "practice",
        "in_learning": True,
        "learning_mode_active": True,
        "board_mode": skill_resolver.apply_board_policy(resolution, default="off"),
        "diagnostic_progress": {},
        "weak_topic": start_topic,
        "learning_context": learning_context,
        "teacher_explanation": explanation_text,
        "current_practice": practice,
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
        "blocked_skill_ids": blocked_skill_ids,
        "remediation_targets": remediation_targets,
        "diagnostic_gap_status": diagnostic_gap_status,
        "explanation_ack_pending": False,
        "explanation_shown_for_skill_id": resolution.skill_id,
        "registry_resolution": {
            "source": resolution.source,
            "resolved_at": "now",
            "warnings": list(resolution.warnings),
            "contract_summary": contract_summary,
        },
    }
    state = update_user_state(user_id, next_state)
    record_diagnostic_result(
        user_id,
        chain_id="g1_to_g2_addition",
        current_skill_id=resolution.skill_id,
        current_topic_id=resolution.topic_id,
        current_grade=result.actual_grade,
        diagnosis_result_id=next_state["diagnosis_result_id"],
        diagnosis_confidence=result.success_rate,
        weak_topic=start_topic,
        detected_gaps=list(next_state["detected_gaps"]),
        blocked_skill_ids=blocked_skill_ids,
        remediation_targets=remediation_targets,
    )
    _append_runtime_audit_log(
        user_id,
        "skill_resolved",
        {
            "mode": resolution.mode,
            "topic_id": resolution.topic_id,
            "skill_id": resolution.skill_id,
            "skill_version": resolution.skill_version,
            "decision": "diagnostic_finish_to_practice",
            "reason": "diagnostic_completed_auto",
            "active": resolution.mode == "active",
        },
    )

    # Build the full teacher response: diagnostic summary + explanation + first practice question
    full_text = f"{text}\n\n{explanation_text}\n\n{practice['question']}"
    state["_teacher_text"] = full_text
    state["_teacher_visual"] = _question_visual(practice)
    return state


def _curricular_public_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return only child-facing curricular state; mapping evidence stays server-side."""
    session = dict(state.get("curricular_session") or {})
    practice = dict(state.get("current_practice") or {})
    feedback = state.get("practice_feedback")
    return {
        "phase": "curricular",
        "weak_topic": None,
        "current_practice": practice or None,
        "practice_feedback": dict(feedback) if isinstance(feedback, dict) else None,
        "report": None,
        "curricular": {
            "lesson_id": session.get("lesson_id"),
            "content_version": session.get("content_version"),
            "part_index": session.get("part_index", 0),
            "part_count": session.get("part_count", 0),
            "part_complete": bool(session.get("part_complete", False)),
            "awaiting_advance": bool(session.get("awaiting_advance", False)),
            "lesson_complete": bool(session.get("lesson_complete", False)),
            "mastery_awarded": False,
        },
    }


def _curricular_response(text: str, state: dict[str, Any]) -> dict[str, Any]:
    practice = state.get("current_practice") or {}
    visual = _question_visual(practice) if practice and practice.get("requires_image") else None
    return {"text": text, "visual": visual, "state": _curricular_public_state(state)}


def _resolve_curricular_session(
    state: dict[str, Any],
    request: ChatRequest,
) -> tuple[ResolvedCurricularLesson, dict[str, Any]]:
    session = dict(state.get("curricular_session") or {})
    if not session:
        raise HTTPException(status_code=409, detail={"code": "curricular_session_not_started"})

    lesson_id = str(session.get("lesson_id") or "")
    content_version = str(session.get("content_version") or "")
    if request.lesson_id is not None and request.lesson_id.strip() != lesson_id:
        raise HTTPException(status_code=409, detail={"code": "lesson_session_mismatch"})
    if request.content_version is not None and request.content_version.strip() != content_version:
        raise HTTPException(status_code=409, detail={"code": "lesson_session_mismatch"})
    try:
        resolved = curricular_lesson_runtime.resolve(lesson_id, content_version)
    except CurriculumResolutionError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code}) from exc
    return resolved, session


def _start_curricular_lesson(user_id: str, request: ChatRequest) -> dict[str, Any]:
    try:
        resolved = curricular_lesson_runtime.resolve(
            str(request.lesson_id or ""),
            str(request.content_version or ""),
        )
        practice = curricular_lesson_runtime.child_part(resolved, 0)
    except CurriculumResolutionError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code}) from exc

    practice["attempts"] = 0
    session = {
        "lesson_id": resolved.lesson_id,
        "content_version": resolved.content_version,
        "assessment_kind": resolved.assessment_kind,
        "part_index": 0,
        "part_count": resolved.part_count,
        "attempts": 0,
        "part_complete": False,
        "awaiting_advance": False,
        "lesson_complete": False,
    }
    state = update_user_state(
        user_id,
        {
            "phase": "curricular",
            "path_choice": "curricular",
            "in_learning": True,
            "learning_mode_active": True,
            "current_lesson_id": resolved.lesson_id,
            "current_content_version": resolved.content_version,
            "curricular_session": session,
            "current_practice": practice,
            "practice_feedback": None,
            "weak_topic": None,
            "report": None,
            "current_skill_id": None,
            "current_skill_version": None,
            "current_skill_mode": None,
            "current_topic_id": None,
            "mastery_check_pending": False,
            "promotion_eligible": False,
        },
    )
    return _curricular_response(practice["question"], state)


def _answer_curricular_part(
    user_id: str,
    request: ChatRequest,
    resolved: ResolvedCurricularLesson,
    session: dict[str, Any],
) -> dict[str, Any]:
    if session.get("lesson_complete"):
        return _curricular_response("Урок уже завершён.", get_user_state(user_id))
    if session.get("part_complete"):
        raise HTTPException(status_code=409, detail={"code": "part_already_complete"})

    part_index = session.get("part_index", 0)
    try:
        result = curricular_lesson_runtime.assess_part(resolved, part_index, request.message)
    except CurriculumResolutionError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code}) from exc

    attempts = int(session.get("attempts") or 0) + 1
    status = str(result.get("status") or "invalid_input")
    part_complete = status == "correct"
    lesson_complete = part_complete and (
        resolved.assessment_kind == "exact" or int(part_index) == resolved.part_count - 1
    )
    awaiting_advance = part_complete and not lesson_complete
    session.update(
        {
            "attempts": attempts,
            "part_complete": part_complete,
            "awaiting_advance": awaiting_advance,
            "lesson_complete": lesson_complete,
        }
    )
    practice = curricular_lesson_runtime.child_part(resolved, int(part_index))
    practice["attempts"] = attempts
    feedback = {
        "status": status,
        "part_index": int(part_index),
        "attempts": attempts,
        "part_complete": part_complete,
        "lesson_complete": lesson_complete,
        "mastery_awarded": False,
    }
    state = update_user_state(
        user_id,
        {
            "curricular_session": session,
            "current_practice": practice,
            "practice_feedback": feedback,
            "mastery_check_pending": False,
            "promotion_eligible": False,
        },
    )
    if status == "correct":
        text = "Верно! Урок завершён." if lesson_complete else "Верно! Можно перейти к следующей части."
    elif status == "needs_review":
        text = "Ответ сохранён для проверки."
    elif status == "incorrect":
        text = "Пока не получилось. Попробуй ещё раз."
    else:
        text = "Нужен один ответ на текущую часть."
    return _curricular_response(text, state)


def _advance_curricular_part(
    user_id: str,
    resolved: ResolvedCurricularLesson,
    session: dict[str, Any],
) -> dict[str, Any]:
    if session.get("lesson_complete"):
        return _curricular_response("Урок уже завершён.", get_user_state(user_id))
    if not session.get("part_complete"):
        raise HTTPException(status_code=409, detail={"code": "current_part_not_complete"})

    current_index = int(session.get("part_index") or 0)
    next_index = current_index + 1
    if next_index >= resolved.part_count:
        session.update({"lesson_complete": True, "awaiting_advance": False})
        state = update_user_state(user_id, {"curricular_session": session})
        return _curricular_response("Урок завершён.", state)

    try:
        practice = curricular_lesson_runtime.child_part(resolved, next_index)
    except CurriculumResolutionError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code}) from exc
    practice["attempts"] = 0
    session.update(
        {
            "part_index": next_index,
            "attempts": 0,
            "part_complete": False,
            "awaiting_advance": False,
        }
    )
    state = update_user_state(
        user_id,
        {
            "curricular_session": session,
            "current_practice": practice,
            "practice_feedback": None,
        },
    )
    return _curricular_response(practice["question"], state)


def _handle_curricular_chat(user_id: str, request: ChatRequest, state: dict[str, Any]) -> dict[str, Any]:
    action = request.action
    if action == "start" or (
        action is None and request.mode == "curricular" and request.lesson_id
    ):
        return _start_curricular_lesson(user_id, request)

    resolved, session = _resolve_curricular_session(state, request)
    if action in (None, "answer"):
        return _answer_curricular_part(user_id, request, resolved, session)
    if action == "hint":
        try:
            hint = curricular_lesson_runtime.hint(resolved, session.get("part_index", 0))
        except CurriculumResolutionError as exc:
            raise HTTPException(status_code=422, detail={"code": exc.code}) from exc
        return _curricular_response(hint, state)
    if action == "advance":
        return _advance_curricular_part(user_id, resolved, session)
    raise HTTPException(status_code=422, detail={"code": "unsupported_curricular_action"})


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

    if _is_stop_intent(message):
        return _pause_learning(user_id, state, message)

    if state.get("phase") == "paused":
        return _resume_paused_learning(user_id, state)

    if (
        request.mode == "curricular"
        or request.action is not None
        or state.get("phase") == "curricular"
    ):
        return _handle_curricular_chat(user_id, request, state)

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
            text = (
                f"Начнём диагностику.\n\n"
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
            return _panda_response(state.get("_teacher_text", ""), state, visual=state.get("_teacher_visual"))

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
        if progress["questions_answered"] >= len(sequence) or _should_end_diagnostic(state):
            state = _finish_diagnostic(user_id, state)
            return _panda_response(state.get("_teacher_text", ""), state, visual=state.get("_teacher_visual"))

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
        text = (
            "Начнём диагностику.\n\n"
            f"{first_question['question']}"
        )
        return _panda_response(text, state, visual=_question_visual(first_question))

    # Explanation phase is no longer a separate step — diagnostic auto-transitions to practice.
    # If state somehow lands in "explanation" (e.g. old saved state), push forward to practice.
    if state.get("phase") == "explanation":
        weak_topic = state.get("weak_topic") or diagnostic_engine.get_starting_topic(int(state.get("grade") or 1))
        practice = practice_engine.create_practice(weak_topic)
        explanation_text = state.get("teacher_explanation") or generate_teacher_reply(
            stage="explanation",
            grade=int(state.get("grade") or 1),
            weak_topic=weak_topic,
            learning_context=list(state.get("learning_context") or []),
            user_message="",
        )
        state = update_user_state(
            user_id,
            {
                "phase": "practice",
                "current_practice": practice,
                "teacher_explanation": explanation_text,
                "explanation_ack_pending": False,
                "explanation_shown_for_skill_id": state.get("current_skill_id"),
                "board_mode": skill_resolver.apply_board_policy(
                    skill_resolver.resolve(topic_id=str(weak_topic.get("topic_id") or ""), topic_name=str(weak_topic.get("topic") or "")),
                    default=str(state.get("board_mode") or "off"),
                ),
            },
        )
        text = f"{explanation_text}\n\n{practice['question']}"
        return _panda_response(text, state, visual=_question_visual(practice))

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
        record_practice_attempt(
            user_id,
            skill_id=skill_resolution.skill_id or state.get("current_skill_id"),
            skill_version=skill_resolution.skill_version,
            question_id=practice.get("id"),
            topic_id=practice.get("topic_id"),
            is_correct=bool(feedback["is_correct"]),
            confidence=feedback.get("confidence"),
            error_code=feedback.get("error_code"),
            error_family=feedback.get("error_family"),
            remediation_path=feedback.get("remediation_path"),
        )

        # Determine next practice question
        practice_round = int(state.get("practice_round") or 0) + 1
        weak_topic = state.get("weak_topic") or practice
        next_practice = practice_engine.create_practice(weak_topic, variant=practice_round)

        # Build teacher text: feedback + next question (teacher drives, no "want more?")
        if feedback["is_correct"]:
            teacher_text = generate_teacher_reply(
                stage="practice_result",
                grade=int(state.get("grade") or 1),
                weak_topic=weak_topic,
                learning_context=list(state.get("learning_context") or []),
                user_message=message,
                practice_question=practice.get("question", ""),
                practice_feedback=feedback,
                report=report,
            )
            # Remove any "want more?" ending — teacher just gives next question
            teacher_text = _strip_followup_question(teacher_text)
            text = f"{teacher_text}\n\n{next_practice['question']}"
        else:
            # Practice wrong → start remediation flow
            remediation = remediation_engine.start_remediation(
                user_id,
                original_question=practice,
                error_details=feedback,
            )
            first_step = remediation.current_step

            scaffolding_level = remediation.scaffolding_level
            scaffolding_hint = ""
            if scaffolding_level == 1:
                scaffolding_hint = _get_scaffolding_visual(remediation)
            elif scaffolding_level == 2:
                scaffolding_hint = _get_scaffolding_step_by_step(remediation)

            teacher_text = generate_teacher_reply(
                stage="practice_result",
                grade=int(state.get("grade") or 1),
                weak_topic=weak_topic,
                learning_context=list(state.get("learning_context") or []),
                user_message=message,
                practice_question=practice.get("question", ""),
                practice_feedback=feedback,
                report=report,
            )
            teacher_text = _strip_followup_question(teacher_text)

            # Build remediation response
            correct_answer_text = f"Правильный ответ: {practice['answer']}."
            parts = [teacher_text, correct_answer_text]
            if scaffolding_hint:
                parts.append(scaffolding_hint)
            parts.append(first_step.question)
            text = "\n\n".join(parts)

        state = update_user_state(
            user_id,
            {
                "phase": "remediation" if not feedback["is_correct"] else "practice",
                "practice_round": practice_round,
                "practice_feedback": feedback,
                "report": report,
                "current_practice": next_practice if feedback["is_correct"] else practice,
                "remediation_step_type": first_step.step_type if not feedback["is_correct"] else None,
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
        state = _record_mastery_gate_result(
            state,
            skill_id=mastery_decision.skill_id or skill_resolution.skill_id or state.get("current_skill_id"),
            decision=mastery_decision.decision,
            confidence=mastery_decision.confidence,
            reasons=mastery_decision.reasons,
            failed_criteria=mastery_decision.failed_criteria,
            evidence=mastery_decision.evidence,
        )
        promotion_eligible = state.get("promotion_eligible", False)
        mastery_check_pending = state.get("mastery_check_pending", False)
        mastery_gate_status = state.get("mastery_gate_status") or "idle"
        mastery_check_result = state.get("mastery_check_result")
        state = update_user_state(
            user_id,
            {
                "mastery_status_by_skill": state.get("mastery_status_by_skill") or {},
                "mastery_gate_status": mastery_gate_status,
                "mastery_check_result": mastery_check_result,
                "promotion_eligible": bool(promotion_eligible),
                "mastery_check_pending": bool(mastery_check_pending),
                "blocked_skill_ids": [] if mastery_decision.decision == "mastered" else list(state.get("blocked_skill_ids") or []),
            },
        )
        state = get_user_state(user_id)
        record_mastery_evaluation(
            user_id,
            skill_id=mastery_decision.skill_id or state.get("current_skill_id"),
            skill_version=skill_resolution.skill_version,
            decision=mastery_decision.decision,
            confidence=mastery_decision.confidence,
            evidence=mastery_decision.evidence,
            reasons=mastery_decision.reasons,
            failed_criteria=mastery_decision.failed_criteria,
            remediation_path=feedback.get("remediation_path"),
            error_code=feedback.get("error_code"),
            error_family=feedback.get("error_family"),
            unblocked_skill_ids=list(skill_resolution.next_skills or []) if mastery_decision.decision == "mastered" else None,
        )
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

        # Handle mastery: auto-promote to next skill
        if mastery_decision.decision == "mastered":
            current_resolution = skill_resolver.resolve(topic_id=mastery_decision.skill_id or state.get("current_skill_id"))
            next_skill_id = (current_resolution.next_skills or [None])[0]
            next_skill_entry = _skill_entry_by_id(next_skill_id)
            next_resolution = skill_resolver.resolve(topic_id=next_skill_id)
            if next_skill_id and next_skill_entry:
                next_topic_id = str((next_skill_entry.get("topic_ids") or [next_resolution.topic_id or None])[0] or "")
                next_topic_name = str((next_skill_entry.get("topic_names") or [None])[0] or next_skill_id)
                next_weak_topic = {
                    "grade": int(next_skill_entry.get("grade") or state.get("grade") or 1),
                    "topic_id": next_topic_id or next_resolution.topic_id,
                    "topic": next_topic_name,
                    "skill_id": next_skill_id,
                }
                promoted_practice = practice_engine.create_practice(next_weak_topic)
                state = update_user_state(
                    user_id,
                    {
                        "phase": "practice",
                        "weak_topic": next_weak_topic,
                        "current_practice": promoted_practice,
                        "practice_feedback": None,
                        "report": None,
                        "current_skill_id": next_resolution.skill_id,
                        "current_skill_version": next_resolution.skill_version,
                        "current_skill_mode": next_resolution.mode,
                        "current_topic_id": next_weak_topic.get("topic_id"),
                        "learning_mode_active": True,
                        "mastery_check_pending": False,
                        "promotion_eligible": True,
                        "mastery_gate_status": "mastered",
                    },
                )
                student_profile = record_promotion(
                    user_id,
                    from_skill_id=mastery_decision.skill_id or state.get("current_skill_id"),
                    to_skill_id=next_skill_id,
                    from_skill_version=current_resolution.skill_version,
                    to_skill_version=next_resolution.skill_version,
                    reason="mastery_auto_promotion",
                )
                state = update_user_state(user_id, {"student_profile": student_profile})
                _append_runtime_audit_log(
                    user_id,
                    "auto_promotion",
                    {
                        "from_skill_id": mastery_decision.skill_id or state.get("current_skill_id"),
                        "to_skill_id": next_skill_id,
                        "reason": "mastery_auto_promotion",
                        "source": "backend_state_machine",
                    },
                )
                promo_text = f"🎯 Тема закреплена! Переходим к следующей.\n\n{promoted_practice['question']}"
                return _panda_response(promo_text, state, visual=_question_visual(promoted_practice))

        visual = {"type": "report", "practice_result": report["practice_result"]} if feedback["is_correct"] else _question_visual(next_practice)
        return _panda_response(text, state, visual=visual)

    # === REMEDIATION PHASE ===
    if state.get("phase") == "remediation":
        remediation = remediation_engine.get_state(user_id)
        if not remediation:
            # Lost state — restart practice
            weak_topic = state.get("weak_topic") or diagnostic_engine.get_starting_topic(int(state.get("grade") or 1))
            next_practice = practice_engine.create_practice(weak_topic)
            state = update_user_state(user_id, {"phase": "practice", "current_practice": next_practice})
            return _panda_response(next_practice["question"], state, visual=_question_visual(next_practice))

        answered_step = remediation.current_step
        is_correct, next_step, is_complete, should_escalate = remediation_engine.check_answer(
            user_id, message
        )

        if should_escalate:
            # 3 errors in remediation → escalate to full explanation
            remediation_engine.remove_state(user_id)
            weak_topic = state.get("weak_topic") or {}
            explanation_text = generate_teacher_explanation(
                grade=int(state.get("grade") or 1),
                weak_topic=weak_topic,
                learning_context=list(state.get("learning_context") or []),
                user_message=message,
            )
            explanation_text = _strip_followup_question(explanation_text)
            new_practice = practice_engine.create_practice(weak_topic)
            state = update_user_state(
                user_id,
                {
                    "phase": "explanation",
                    "teacher_explanation": explanation_text,
                    "explanation_ack_pending": True,
                    "explanation_shown_for_skill_id": state.get("current_skill_id"),
                    "board_mode": "on",
                },
            )
            text = f"{explanation_text}\n\nПопробуем ещё раз.\n\n{new_practice['question']}"
            return _panda_response(text, state, visual=_question_visual(new_practice))

        if is_complete:
            # Remediation done — return to practice
            remediation_engine.remove_state(user_id)
            weak_topic = state.get("weak_topic") or {}
            next_practice = practice_engine.create_practice(weak_topic)
            state = update_user_state(
                user_id,
                {
                    "phase": "practice",
                    "current_practice": next_practice,
                    "remediation_step_type": None,
                },
            )
            if is_correct:
                text = f"Верно! Отлично, продолжаем.\n\n{next_practice['question']}"
            else:
                text = f"Верно! Возвращаемся к практике.\n\n{next_practice['question']}"
            return _panda_response(text, state, visual=_question_visual(next_practice))

        # More steps in remediation
        scaffolding_hint = ""
        scaffolding_level = remediation.scaffolding_level
        if scaffolding_level == 1:
            scaffolding_hint = _get_scaffolding_visual(remediation)
        elif scaffolding_level == 2:
            scaffolding_hint = _get_scaffolding_step_by_step(remediation)

        if is_correct:
            text = f"Верно!\n\n{next_step.question}"
        else:
            answered_value = answered_step.answer if answered_step else ""
            text = f"Не совсем. Правильный ответ: {answered_value}.\n\n{next_step.question}"

        if scaffolding_hint:
            text = f"{text}\n\n{scaffolding_hint}"

        state = update_user_state(
            user_id,
            {"remediation_step_type": next_step.step_type},
        )
        return _panda_response(text, state, visual=_question_visual({"question": next_step.question}))

    # Report phase is no longer a separate step — practice auto-advances.
    # If state somehow lands in "report" (e.g. old saved state), push forward to practice.
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
        text = f"{next_practice['question']}"
        return _panda_response(text, state, visual=_question_visual(next_practice))

    # Mastery check phase is handled inside practice now.
    # If state somehow lands in "mastery_check", push forward.
    if state.get("phase") == "mastery_check":
        mastery_result = state.get("mastery_check_result") or {}
        skill_id = mastery_result.get("skill_id") or state.get("current_skill_id")
        decision = mastery_result.get("decision") or state.get("mastery_gate_status") or "unknown"
        if decision == "mastered":
            current_resolution = skill_resolver.resolve(topic_id=skill_id)
            next_skill_id = (current_resolution.next_skills or [None])[0]
            next_skill_entry = _skill_entry_by_id(next_skill_id)
            next_resolution = skill_resolver.resolve(topic_id=next_skill_id)
            if next_skill_id and next_skill_entry:
                next_topic_id = str((next_skill_entry.get("topic_ids") or [next_resolution.topic_id or None])[0] or "")
                next_topic_name = str((next_skill_entry.get("topic_names") or [None])[0] or next_skill_id)
                next_weak_topic = {
                    "grade": int(next_skill_entry.get("grade") or state.get("grade") or 1),
                    "topic_id": next_topic_id or next_resolution.topic_id,
                    "topic": next_topic_name,
                    "skill_id": next_skill_id,
                }
                promoted_practice = practice_engine.create_practice(next_weak_topic)
                state = update_user_state(
                    user_id,
                    {
                        "phase": "practice",
                        "weak_topic": next_weak_topic,
                        "current_practice": promoted_practice,
                        "practice_feedback": None,
                        "report": None,
                        "current_skill_id": next_resolution.skill_id,
                        "current_skill_version": next_resolution.skill_version,
                        "current_skill_mode": next_resolution.mode,
                        "current_topic_id": next_weak_topic.get("topic_id"),
                        "learning_mode_active": True,
                        "mastery_check_pending": False,
                        "promotion_eligible": True,
                        "mastery_gate_status": "mastered",
                    },
                )
                student_profile = record_promotion(
                    user_id,
                    from_skill_id=skill_id,
                    to_skill_id=next_skill_id,
                    from_skill_version=current_resolution.skill_version,
                    to_skill_version=next_resolution.skill_version,
                    reason="mastery_auto_promotion",
                )
                state = update_user_state(user_id, {"student_profile": student_profile})
                promo_text = f"🎯 Тема закреплена! Переходим к следующей.\n\n{promoted_practice['question']}"
                return _panda_response(promo_text, state, visual=_question_visual(promoted_practice))
        # Not mastered — go back to practice
        weak_topic = state.get("weak_topic") or diagnostic_engine.get_starting_topic(int(state.get("grade") or 1))
        retry_practice = practice_engine.create_practice(weak_topic)
        state = update_user_state(
            user_id,
            {
                "phase": "practice",
                "current_practice": retry_practice,
                "mastery_check_pending": False,
            },
        )
        text = f"Продолжаем практику.\n\n{retry_practice['question']}"
        return _panda_response(text, state, visual=_question_visual(retry_practice))

    return _panda_response(
        f"Привет, {state['name']}! Напиши 'диагностика', чтобы начать учёбу.",
        state,
    )


@router.get("/panda/progress/{user_id}")
def get_progress(user_id: str) -> dict[str, Any]:
    """Read-only progress summary for parents/teachers."""
    return get_progress_summary(user_id)


# === PHASE G: Analytics & Reports API ===

@router.get("/panda/dashboard/{user_id}")
def get_dashboard(user_id: str) -> dict[str, Any]:
    """Full dashboard data for parents/teachers."""
    summary = get_progress_summary(user_id)
    full_report = report_service.build_full_report(user_id)
    return {
        "user_id": user_id,
        "summary": summary,
        "report": full_report,
    }


@router.get("/panda/reports/{user_id}/csv")
def get_report_csv(user_id: str) -> dict[str, Any]:
    """Export student progress as CSV."""
    csv_content = report_service.export_csv(user_id)
    return {
        "user_id": user_id,
        "format": "csv",
        "content": csv_content,
    }


@router.post("/panda/notifications/subscribe")
def subscribe_notifications(
    user_id: str,
    webhook_url: str | None = None,
) -> dict[str, Any]:
    """Subscribe to progress notifications for a user.

    In production, webhook_url would be stored and called on events.
    For now, returns the subscription config.
    """
    # Store subscription in user state
    state = get_user_state(user_id)
    state = update_user_state(
        user_id,
        {
            "notification_subscription": {
                "webhook_url": webhook_url,
                "subscribed_at": datetime.now(timezone.utc).isoformat(),
                "events": ["mastery_achieved", "daily_summary", "streak_milestone"],
            }
        },
    )
    return {
        "user_id": user_id,
        "subscribed": True,
        "events": ["mastery_achieved", "daily_summary", "streak_milestone"],
    }


# === PHASE H: Integrations ===

from deeptutor.services.gamification import (
    get_gamification_state,
    record_answer,
    record_mastery,
    get_level_progress,
    BADGES,
)


@router.get("/panda/gamification/{user_id}")
def get_gamification(user_id: str) -> dict[str, Any]:
    """Get gamification state for a user (XP, level, badges)."""
    state = get_gamification_state(user_id)
    return {
        "user_id": user_id,
        **state.to_dict(),
        "level_progress": get_level_progress(state.xp),
        "available_badges": {k: {"name": v["name"], "description": v["description"], "icon": v["icon"]} for k, v in BADGES.items()},
    }


@router.post("/panda/embed/init")
def init_embed(
    user_id: str,
    pupil_name: str | None = None,
    grade: int | None = None,
) -> dict[str, Any]:
    """Initialize embedded session (for iframe/widget integration).

    Returns session config that the embed frontend can use.
    """
    state = get_user_state(user_id)
    if pupil_name:
        state = update_user_state(user_id, {"name": pupil_name})
    if grade:
        state = update_user_state(user_id, {"grade": grade})

    return {
        "user_id": user_id,
        "name": state.get("name"),
        "grade": state.get("grade"),
        "ready": bool(state.get("name") and state.get("grade")),
        "base_url": "/api/v1/plugins/panda",
    }


@router.get("/panda/embed/code")
def get_embed_code(
    user_id: str,
    height: str = "600",
    width: str = "100%",
) -> dict[str, Any]:
    """Get embeddable iframe HTML code."""
    iframe_html = (
        f'<iframe '
        f'src="/embed?user_id={user_id}" '
        f'width="{width}" '
        f'height="{height}" '
        f'frameborder="0" '
        f'allow="clipboard-write" '
        f'style="border: 1px solid #e5e7eb; border-radius: 12px;" '
        f'title="MasterKva Tutor">'
        f'</iframe>'
    )
    return {
        "user_id": user_id,
        "iframe_html": iframe_html,
    }
