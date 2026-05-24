from __future__ import annotations

from deeptutor.services.diagnostic_engine import DiagnosticEngine
from deeptutor.services.visual_template_service import decorate_question_visual


def test_grade_one_sequence_uses_all_grade_one_questions() -> None:
    engine = DiagnosticEngine()

    sequence = engine.build_diagnostic_sequence(1)

    # Grade 1 has 11 questions (5 addition_with_transition + 6 other topics)
    assert len(sequence) == 11
    assert {item["grade"] for item in sequence} == {1}
    assert sequence[0]["topic_id"] == "g1_t07"
    assert sequence[0]["skill_id"] == "g1_early_arithmetic_core"
    assert sequence[0]["skill_mode"] == "shadow"
    assert sequence[0]["coverage_status"] == "partial"
    assert sequence[0]["board_policy"] == "off"
    assert sequence[0]["contract_validation"]["required"] is True
    assert sequence[0]["contract_validation"]["board_policy_locked"] is True


def test_grade_two_pilot_skill_is_marked_active() -> None:
    engine = DiagnosticEngine()

    sequence = engine.get_questions_for_grade(2)

    pilot = sequence[0]
    assert pilot["skill_id"] == "g2_addition_core"
    assert pilot["skill_mode"] == "active"
    assert pilot["coverage_status"] == "partial"
    assert pilot["board_policy"] == "off"


def test_grade_nine_sequence_covers_all_grades_and_board_visuals() -> None:
    engine = DiagnosticEngine()

    sequence = engine.build_diagnostic_sequence(9)
    visuals = [decorate_question_visual(question) for question in sequence]

    assert len(sequence) == 20
    assert [item["grade"] for item in sequence] == [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9]
    assert {item["grade"] for item in sequence} == set(range(1, 10))
    assert all(item.get("skill_id") for item in sequence)
    assert all(item.get("coverage_status") == "partial" for item in sequence)
    assert sequence[-1]["topic"] == "Квадратные функции"
    assert sequence[-1]["question"] == "Как называется график квадратичной функции?"

    visuals_by_topic = {item["topic"]: visual for item, visual in zip(sequence, visuals)}

    assert visuals_by_topic["ПОДГОТОВКА"]["type"] == "number_bond"
    assert visuals_by_topic["ПОДГОТОВКА"]["parts"] == [2, 1]
    assert visuals_by_topic["ПОДГОТОВКА"]["operation"] == "add"
    assert visuals_by_topic["СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5"]["type"] == "question"
    assert visuals_by_topic["СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5"]["templateType"] == "number_bond"
    assert visuals_by_topic["СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5"]["templateFamily"] == "addition_subtraction"
    assert visuals_by_topic["СЛОЖЕНИЕ ДО 100 (БЕЗ ПЕРЕХОДА)"]["type"] == "number_bond"
    assert visuals_by_topic["Следующее число"]["templateType"] == "number_line"
    assert visuals_by_topic["СЛОЖЕНИЕ С ПЕРЕХОДОМ ЧЕРЕЗ 10"]["type"] == "number_bond"
    # Last question with this topic is 9+5, so parts are [9, 5]
    assert visuals_by_topic["СЛОЖЕНИЕ С ПЕРЕХОДОМ ЧЕРЕЗ 10"]["parts"] == [9, 5]
    assert visuals_by_topic["СЛОЖЕНИЕ С ПЕРЕХОДОМ ЧЕРЕЗ 10"]["operation"] == "add"
    assert visuals_by_topic["Сложение с переходом"]["type"] == "number_bond"
    assert visuals_by_topic["Сложение с переходом"]["parts"] == [4, 3]
    assert visuals_by_topic["Сложение с переходом"]["operation"] == "add"
    assert visuals_by_topic["Вычитание"]["type"] == "number_bond"
    assert visuals_by_topic["Вычитание"]["parts"] == [7, 4]
    assert visuals_by_topic["Вычитание"]["operation"] == "subtract"
    assert visuals_by_topic["Время (часы, минуты, секунды)"]["templateType"] == "clock_face"
    assert visuals_by_topic["Большие числа (до 100 млн)"]["templateType"] == "place_value_chart"
    assert visuals_by_topic["Простые уравнения"]["templateType"] == "balance_scale_equation"
    # g5_simple_equations_core is at index 15 (after 11 grade-1 + 2 grade-2 + 1 grade-3 + 1 grade-4)
    assert sequence[15]["skill_id"] == "g5_simple_equations_core"
    assert sequence[15]["coverage_status"] == "partial"
    assert sequence[15]["board_policy"] == "limited"
    assert visuals_by_topic["Проценты"]["templateType"] == "percent_grid_10x10"
    assert visuals_by_topic["Рациональные числа"]["type"] == "number_bond"
    assert visuals_by_topic["Рациональные числа"]["parts"] == [3, 5]
    assert visuals_by_topic["Рациональные числа"]["operation"] == "add"
    assert visuals_by_topic["Линейные уравнения"]["templateType"] == "balance_scale_linear"
    assert visuals_by_topic["Квадратные функции"]["templateType"] == "cartesian_graph_slider"

    for visual in visuals:
        assert visual["title"]
        assert visual["prompt"]
        if visual["type"] == "number_bond":
            assert visual["parts"]
            assert visual["operation"] in {"add", "subtract"}
        else:
            assert visual["type"] == "question"
            if visual.get("templateType"):
                assert visual.get("templateSections")
                assert visual.get("templateLabel")
                assert visual.get("templateFamily")
            else:
                assert visual["cpaVisual"] in {"counting", "position", "carry", "number_line", "addition", "shapes", "clock", "division", "mixed_ops", "unknown"}



def test_run_diagnostic_collects_weak_topic_and_grade_stats() -> None:
    engine = DiagnosticEngine()
    answers = [
        {"question_id": "g1_t01_q01", "grade": 1, "topic_id": "g1_t01", "topic": "Счёт до 10", "is_correct": True},
        {"question_id": "g1_t02_q01", "grade": 1, "topic_id": "g1_t02", "topic": "Следующее число", "is_correct": False},
        {"question_id": "g1_t03_q01", "grade": 1, "topic_id": "g1_t03", "topic": "Сложение с переходом", "is_correct": False},
    ]

    result = engine.run_diagnostic(1, answers)

    assert result.claimed_grade == 1
    assert result.actual_grade == 1
    assert result.total_questions == 3
    assert result.correct_count == 1
    assert result.needs_review is True
    assert result.weak_topics[0]["topic_id"] == "g1_t02"
    assert result.grade_stats[1]["wrong"] == 2
    learning_path = result.get_learning_path()
    assert learning_path["start_grade"] == 1
    assert learning_path["start_topic_id"] == "g1_t02"
