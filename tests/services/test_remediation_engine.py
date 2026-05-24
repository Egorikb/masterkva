"""
Tests for Remediation Engine (Phase C).

Covers:
- RemediationState creation and step tracking
- Scaffolding levels (1=visual, 2=step_by_step, 3=escalate)
- Clarifying question generation per item_family
- Analog question generation
- Full remediation cycle: start → check answers → complete/escalate
"""
from __future__ import annotations

import pytest

from deeptutor.services.remediation_engine import (
    RemediationEngine,
    RemediationState,
    RemediationStep,
    SCAFFOLDING_VISUAL,
    SCAFFOLDING_STEP_BY_STEP,
    SCAFFOLDING_ESCALATE,
    ESCALATION_THRESHOLD,
)


@pytest.fixture
def engine() -> RemediationEngine:
    return RemediationEngine()


@pytest.fixture
def addition_question() -> dict:
    return {
        "id": "test_q01",
        "topic_id": "g1_t03",
        "question": "8 + 5 = ?",
        "answer": "13",
        "item_family": "addition_within_10_part_whole",
        "parts": ["8", "5"],
    }


@pytest.fixture
def subtraction_question() -> dict:
    return {
        "id": "test_q02",
        "topic_id": "g1_t04",
        "question": "15 - 7 = ?",
        "answer": "8",
        "item_family": "subtraction_within_10_part_whole",
        "parts": ["15", "7"],
    }


@pytest.fixture
def error_details_addition() -> dict:
    return {
        "error_code": "addition_within_10_part_whole_error",
        "error_family": "addition_within_10_part_whole",
        "item_family": "addition_within_10_part_whole",
        "remediation_path": "number_bond",
    }


class TestRemediationEngineStart:
    def test_start_creates_state(self, engine, addition_question, error_details_addition):
        state = engine.start_remediation("user1", addition_question, error_details_addition)
        assert state is not None
        assert state.error_code == "addition_within_10_part_whole_error"
        assert state.item_family == "addition_within_10_part_whole"
        assert state.remediation_path == "number_bond"

    def test_start_builds_steps(self, engine, addition_question, error_details_addition):
        state = engine.start_remediation("user1", addition_question, error_details_addition)
        # Should have: clarify + 2 analogs = 3 steps
        assert len(state.steps) == 3
        assert state.steps[0].step_type == "clarify"
        assert state.steps[1].step_type == "analog"
        assert state.steps[2].step_type == "analog"

    def test_start_tracks_user(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        retrieved = engine.get_state("user1")
        assert retrieved is not None
        assert retrieved.error_family == "addition_within_10_part_whole"

    def test_remove_state(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        engine.remove_state("user1")
        assert engine.get_state("user1") is None


class TestRemediationScaffolding:
    def test_initial_scaffolding_level_is_1(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        assert engine.get_scaffolding_level("user1") == 1

    def test_scaffolding_increases_on_wrong(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        # First wrong answer
        engine.check_answer("user1", "999")
        assert engine.get_scaffolding_level("user1") == 2

    def test_scaffolding_caps_at_3(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        # Multiple wrong answers
        for _ in range(5):
            engine.check_answer("user1", "999")
        assert engine.get_scaffolding_level("user1") == 3


class TestRemediationCheckAnswer:
    def test_correct_answer_advances(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        step = engine.get_state("user1").current_step
        is_correct, next_step, is_complete, should_escalate = engine.check_answer(
            "user1", step.answer
        )
        assert is_correct is True
        assert is_complete is False
        assert should_escalate is False

    def test_wrong_answer_does_not_complete(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        is_correct, next_step, is_complete, should_escalate = engine.check_answer(
            "user1", "999"
        )
        assert is_correct is False
        assert is_complete is False

    def test_escalation_after_threshold(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        # Answer wrong ESCALATION_THRESHOLD times
        for _ in range(ESCALATION_THRESHOLD):
            is_correct, next_step, is_complete, should_escalate = engine.check_answer(
                "user1", "999"
            )
        assert should_escalate is True
        assert is_complete is True

    def test_completion_after_enough_correct(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        state = engine.get_state("user1")
        # Answer each step correctly
        for step in state.steps:
            is_correct, next_step, is_complete, should_escalate = engine.check_answer(
                "user1", step.answer
            )
        # After all correct, should be complete
        assert state.is_complete is True


class TestClarifyingQuestions:
    def test_addition_clarify(self, engine):
        q = {"question": "8 + 5 = ?", "answer": "13", "item_family": "addition_within_10_part_whole", "parts": ["8", "5"]}
        details = {"error_code": "err", "error_family": "add", "item_family": "addition_within_10_part_whole", "remediation_path": "number_bond"}
        engine.start_remediation("user1", q, details)
        clarify = engine.get_state("user1").steps[0]
        assert clarify.step_type == "clarify"
        assert "+" in clarify.question

    def test_subtraction_clarify(self, engine):
        q = {"question": "15 - 7 = ?", "answer": "8", "item_family": "subtraction_within_10_part_whole", "parts": ["15", "7"]}
        details = {"error_code": "err", "error_family": "sub", "item_family": "subtraction_within_10_part_whole", "remediation_path": "number_bond"}
        engine.start_remediation("user1", q, details)
        clarify = engine.get_state("user1").steps[0]
        assert clarify.step_type == "clarify"
        assert "−" in clarify.question or "-" in clarify.question


class TestAnalogQuestions:
    def test_analog_same_family(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        state = engine.get_state("user1")
        for step in state.steps[1:]:  # skip clarify
            assert step.step_type == "analog"
            assert step.item_family == "addition_within_10_part_whole"

    def test_analog_has_answer(self, engine, addition_question, error_details_addition):
        engine.start_remediation("user1", addition_question, error_details_addition)
        state = engine.get_state("user1")
        for step in state.steps[1:]:
            assert step.answer is not None
            assert step.answer != ""


class TestVisualHints:
    def test_number_bond_hint(self, engine):
        q = {"question": "3 + 2 = ?", "answer": "5", "item_family": "addition_within_10_part_whole", "parts": ["3", "2"]}
        details = {"error_code": "err", "error_family": "add", "item_family": "addition_within_10_part_whole", "remediation_path": "number_bond"}
        engine.start_remediation("user1", q, details)
        state = engine.get_state("user1")
        for step in state.steps:
            assert step.visual_hint == "number_bond"

    def test_ten_frame_hint(self, engine):
        q = {"question": "3 и 2", "answer": "5", "item_family": "counting_with_objects", "parts": ["3", "2"]}
        details = {"error_code": "err", "error_family": "count", "item_family": "counting_with_objects", "remediation_path": "ten_frame"}
        engine.start_remediation("user1", q, details)
        state = engine.get_state("user1")
        for step in state.steps:
            assert step.visual_hint == "ten_frame"


class TestEdgeCases:
    def test_unknown_item_family(self, engine):
        q = {"question": "???", "answer": "42", "item_family": "unknown_family", "parts": []}
        details = {"error_code": "err", "error_family": "unknown", "item_family": "unknown_family", "remediation_path": ""}
        state = engine.start_remediation("user1", q, details)
        assert state is not None
        assert len(state.steps) == 3

    def test_empty_item_family(self, engine):
        q = {"question": "2 + 3 = ?", "answer": "5", "parts": ["2", "3"]}
        details = {"error_code": "err", "error_family": "err", "item_family": "", "remediation_path": ""}
        state = engine.start_remediation("user1", q, details)
        assert state is not None

    def test_check_without_state(self, engine):
        is_correct, next_step, is_complete, should_escalate = engine.check_answer("nonexistent", "5")
        assert is_correct is False
        assert is_complete is True
        assert should_escalate is True
