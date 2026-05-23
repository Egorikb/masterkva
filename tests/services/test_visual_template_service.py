from deeptutor.services.visual_template_service import build_template_blueprint, decorate_question_visual


def test_decorate_question_visual_keeps_simple_addition_as_number_bond() -> None:
    visual = decorate_question_visual({
        "topic": "Сложение с переходом",
        "question": "3 + 2 = ?",
        "answer": "5",
        "grade": 1,
    })

    assert visual["type"] == "number_bond"
    assert visual["parts"] == [3, 2]
    assert visual["operation"] == "add"
    assert visual["prompt"] == "3 + 2 = ?"
    assert visual["total"] == 5



def test_decorate_question_visual_uses_number_bond_for_real_carry() -> None:
    visual = decorate_question_visual({
        "topic": "Сложение с переходом",
        "question": "8 + 5 = ?",
        "answer": "13",
        "grade": 1,
    })

    assert visual["type"] == "number_bond"
    assert visual["parts"] == [8, 5]
    assert visual["operation"] == "add"
    assert visual["total"] == 13



def test_decorate_question_visual_adds_blueprint_for_equation() -> None:
    visual = decorate_question_visual({
        "topic": "Реши уравнение",
        "question": "x + 3 = 7",
        "answer": "x = 4",
        "grade": 5,
    })

    assert visual["type"] == "question"
    assert visual["templateType"] == "balance_scale_equation"
    assert visual["templateFamily"] == "expressions_equations_inequalities"
    assert len(visual["templateSections"]) == 3
    assert "balance" in visual["templateWhy"].lower() or "равновес" in visual["templateWhy"].lower()



def test_build_template_blueprint_handles_fraction_topics() -> None:
    blueprint = build_template_blueprint({
        "topic": "Доли и дроби",
        "question": "Найди 1/2 от круга",
        "grade": 4,
    })

    assert blueprint is not None
    assert blueprint["templateType"] == "fraction_bars"
    assert blueprint["templateFamily"] == "fractions_decimals_percents"
    assert any(section["label"] == "Pictorial" for section in blueprint["templateSections"])



def test_build_template_blueprint_uses_topic_override_for_positions() -> None:
    blueprint = build_template_blueprint({
        "topic": "ПОЗИЦИИ",
        "question": "Что выше: карандаш или тетрадь?",
        "grade": 1,
    })

    assert blueprint is not None
    assert blueprint["templateType"] == "spatial_relations"
    assert blueprint["templateFamily"] == "geometry_measurement"
    assert blueprint["templateSkills"] == ["верх/низ", "лево/право", "перед/сзади"]



def test_build_template_blueprint_uses_topic_override_for_clock() -> None:
    blueprint = build_template_blueprint({
        "topic": "ЧАСЫ",
        "question": "Покажи 3 часа на часах",
        "grade": 1,
    })

    assert blueprint is not None
    assert blueprint["templateType"] == "clock_face"
    assert blueprint["templateFamily"] == "geometry_measurement"
    assert blueprint["templatePreview"]["visual_type"] == "clock_face"



def test_build_template_blueprint_uses_percent_grid_for_percent_topics() -> None:
    blueprint = build_template_blueprint({
        "topic": "ПРОЦЕНТЫ",
        "question": "Найди 20% от числа 50",
        "grade": 6,
    })

    assert blueprint is not None
    assert blueprint["templateType"] == "percent_grid_10x10"
    assert blueprint["templateFamily"] == "fractions_decimals_percents"
    assert blueprint["templateNotes"]


def test_build_template_blueprint_uses_dynamic_double_number_line_for_proportions() -> None:
    blueprint = build_template_blueprint({
        "topic": "ПРОПОРЦИИ",
        "question": "Если 2 тетради стоят 20 рублей, сколько стоят 5 тетрадей?",
        "grade": 6,
    })

    assert blueprint is not None
    assert blueprint["templateType"] == "double_number_line_dynamic"
    assert blueprint["templateFamily"] == "ratios_proportions"
    assert "масшта" in blueprint["templateWhy"].lower() or "привяз" in blueprint["templateWhy"].lower()


def test_build_template_blueprint_uses_linear_balance_for_linear_equations() -> None:
    blueprint = build_template_blueprint({
        "topic": "ЛИНЕЙНЫЕ УРАВНЕНИЯ",
        "question": "2x + 3 = 11",
        "grade": 7,
    })

    assert blueprint is not None
    assert blueprint["templateType"] == "balance_scale_linear"
    assert blueprint["templateFamily"] == "expressions_equations_inequalities"


def test_build_template_blueprint_uses_slider_graph_for_linear_functions() -> None:
    blueprint = build_template_blueprint({
        "topic": "ЛИНЕЙНЫЕ ФУНКЦИИ",
        "question": "Построй y = 2x + 1",
        "grade": 8,
    })

    assert blueprint is not None
    assert blueprint["templateType"] == "cartesian_graph_slider"
    assert blueprint["templateFamily"] == "functions_graphs"


def test_build_template_blueprint_uses_cut_and_drag_for_parallelogram_topics() -> None:
    blueprint = build_template_blueprint({
        "topic": "ПАРАЛЛЕЛОГРАММЫ",
        "question": "Найди площадь параллелограмма",
        "grade": 8,
    })

    assert blueprint is not None
    assert blueprint["templateType"] == "cut_and_drag_parallelogram"
    assert blueprint["templateFamily"] == "geometry_measurement"
    assert blueprint["templatePreview"]["visual_type"] == "cut_and_drag_parallelogram"
