"""Tests for visual_template_service.py"""
from __future__ import annotations

import pytest

from deeptutor.services.visual_template_service import decorate_question_visual


class TestDecorateQuestionVisual:
    """Test that visual templates are correctly assigned based on topic/CPA."""

    def test_addition_within_10_returns_number_bond(self):
        q = {
            "topic": "Сложение с переходом",
            "item_family": "addition_within_10_part_whole",
            "question": "8 + 5 = ?",
            "CPA": {"visual": "number_bond", "objects": "счёт"},
        }
        visual = decorate_question_visual(q)
        assert visual["type"] == "number_bond"
        assert visual["operation"] == "add"

    def test_subtraction_returns_number_bond_with_subtract(self):
        q = {
            "topic": "Вычитание",
            "item_family": "subtraction_within_10_part_whole",
            "question": "7 - 4 = ?",
        }
        visual = decorate_question_visual(q)
        assert visual["type"] == "number_bond"
        assert visual["operation"] == "subtract"

    def test_time_returns_question_with_cpa_visual(self):
        q = {
            "topic": "Время (часы, минуты, секунды)",
            "item_family": "time_unit_conversion",
            "question": "Сколько минут в 2 часах?",
            "CPA": {"visual": "clock", "objects": "часы"},
        }
        visual = decorate_question_visual(q)
        assert visual["type"] == "question"
        assert visual["cpaVisual"] == "clock"
        assert visual["objects"] == "часы"

    def test_equations_returns_balance_scale(self):
        q = {
            "topic": "Простые уравнения",
            "item_family": "inverse_operation_error",
            "question": "x + 4 = 9",
            "CPA": {"visual": "balance_scale_equation", "objects": "уравнение"},
        }
        visual = decorate_question_visual(q)
        assert visual["templateType"] == "balance_scale_equation"

    def test_percent_returns_percent_grid(self):
        q = {
            "topic": "Проценты",
            "item_family": "percent_calculation_error",
            "question": "25% от 200",
            "CPA": {"visual": "percent_grid_10x10", "objects": "проценты"},
        }
        visual = decorate_question_visual(q)
        assert visual["templateType"] == "percent_grid_10x10"

    def test_returns_question_type_for_unknown(self):
        q = {
            "topic": "Неизвестная тема",
            "item_family": "unknown_family",
            "question": "???",
        }
        visual = decorate_question_visual(q)
        assert visual["type"] == "question"

    def test_visual_has_required_fields(self):
        q = {
            "topic": "Сложение",
            "item_family": "addition_within_10_part_whole",
            "question": "2 + 3 = ?",
        }
        visual = decorate_question_visual(q)
        assert "title" in visual
        assert "prompt" in visual
        assert "type" in visual
