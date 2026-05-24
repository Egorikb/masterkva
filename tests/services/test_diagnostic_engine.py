from __future__ import annotations

from deeptutor.services.diagnostic_engine import DiagnosticEngine
from deeptutor.services.visual_template_service import decorate_question_visual


def test_grade_one_sequence_uses_all_grade_one_questions() -> None:
    engine = DiagnosticEngine()

    sequence = engine.build_diagnostic_sequence(1)

    # Grade 1 has 23 questions (7 topics x 3-5 questions each)
    assert len(sequence) == 23
    assert {item["grade"] for item in sequence} == {1}
    assert sequence[0]["topic_id"] == "g1_t01"
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

    assert len(sequence) == 59
    assert [item["grade"] for item in sequence] == [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9]
    assert {item["grade"] for item in sequence} == set(range(1, 10))
    assert all(item.get("skill_id") for item in sequence)
    assert all(item.get("coverage_status") == "partial" for item in sequence)
    assert sequence[-1]["topic"] == "Квадратные функции"
    assert "Квадратные" in sequence[-1]["topic"]

    visuals_by_topic = {item["topic"]: visual for item, visual in zip(sequence, visuals)}

    # Check that preparation questions have valid visuals
    prep_visuals = [decorate_question_visual(q) for q in sequence if "Подготовка" in q.get("topic", "")]
    assert any(v["type"] == "number_bond" for v in prep_visuals)
    assert visuals_by_topic["Сложение и вычитание до 5"]["type"] == "question"
    assert visuals_by_topic["Сложение и вычитание до 5"]["templateType"] == "number_bond"
    assert visuals_by_topic["Сложение и вычитание до 5"]["templateFamily"] == "addition_subtraction"
    assert visuals_by_topic["Сложение до 100 без перехода"]["type"] == "number_bond"
    assert visuals_by_topic["Следующее число"]["templateType"] == "number_line"
    assert visuals_by_topic["Сложение с переходом через 10"]["type"] == "number_bond"
    # Last question with this topic
    assert visuals_by_topic["Сложение с переходом через 10"]["operation"] == "add"
    assert visuals_by_topic["Сложение с переходом"]["type"] == "number_bond"
    assert visuals_by_topic["Сложение с переходом"]["operation"] == "add"
    assert visuals_by_topic["Вычитание в пределах 10"]["type"] == "number_bond"
    assert visuals_by_topic["Вычитание в пределах 10"]["operation"] == "subtract"
    assert visuals_by_topic["Время (часы, минуты, секунды)"]["templateType"] == "clock_face"
    assert visuals_by_topic["Большие числа (до 100 млн)"]["templateType"] == "place_value_chart"
    assert visuals_by_topic["Простые уравнения"]["templateType"] == "balance_scale_equation"
    # g5_simple_equations_core is at index 39
    assert sequence[39]["skill_id"] == "g5_simple_equations_core"
    assert sequence[39]["coverage_status"] == "partial"
    assert sequence[39]["board_policy"] == "limited"
    assert visuals_by_topic["Проценты"]["templateType"] == "percent_grid_10x10"
    assert visuals_by_topic["Рациональные числа"]["type"] == "number_bond"
    assert len(visuals_by_topic["Рациональные числа"]["parts"]) == 2
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
                    assert visual["cpaVisual"] in {"counting", "position", "carry", "number_line", "addition", "shapes", "clock", "division", "mixed_ops", "unknown", "ten_frame", "number_bond", "place_value_chart", "balance_scale_equation", "percent_grid_10x10", "cartesian_graph_slider", "part_part_whole_bar"}



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
