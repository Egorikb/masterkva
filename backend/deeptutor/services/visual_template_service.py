from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CANONICAL_VISUAL_TYPES: list[dict[str, Any]] = [
    {
        "visual_type": "ten_frame",
        "purpose": "Показывать числа до 10 и разложение части/целое",
        "best_for": ["addition_subtraction", "early_number_sense"],
    },
    {
        "visual_type": "number_line",
        "purpose": "Показывать движение по числовой прямой и сравнение чисел",
        "best_for": ["addition_subtraction", "place_value"],
    },
    {
        "visual_type": "base_ten_blocks",
        "purpose": "Делать видимыми десятки и единицы, перенос и разрядный состав",
        "best_for": ["place_value", "addition_subtraction"],
    },
    {
        "visual_type": "place_value_chart",
        "purpose": "Показывать разряды числа и обмен единиц на десяток",
        "best_for": ["place_value", "addition_subtraction"],
    },
    {
        "visual_type": "part_part_whole_bar",
        "purpose": "Показывать части, которые складываются в целое",
        "best_for": ["addition_subtraction", "fractions_decimals_percents"],
    },
    {
        "visual_type": "area_model_grid",
        "purpose": "Показывать площадь, умножение, дроби и разложение по частям",
        "best_for": ["multiplication_division", "fractions_decimals_percents", "geometry_measurement"],
    },
    {
        "visual_type": "array_matrix",
        "purpose": "Показывать группы, массивы и таблицу умножения",
        "best_for": ["multiplication_division"],
    },
    {
        "visual_type": "bar_model_strip_diagram",
        "purpose": "Показывать отношение частей, дробей и задач в полосовой модели",
        "best_for": ["addition_subtraction", "fractions_decimals_percents", "ratio_proportions"],
    },
    {
        "visual_type": "ratio_table",
        "purpose": "Показывать пропорции, отношения и соответствия величин",
        "best_for": ["ratios_proportions"],
    },
    {
        "visual_type": "double_number_line",
        "purpose": "Показывать пропорциональный рост и сравнение двух шкал",
        "best_for": ["ratios_proportions", "functions_graphs"],
    },
    {
        "visual_type": "double_number_line_dynamic",
        "purpose": "Показывать привязку двух шкал к общей единице и динамику масштабирования",
        "best_for": ["ratios_proportions"],
    },
    {
        "visual_type": "fraction_circle_region",
        "purpose": "Показывать доли целого на круге или на равных частях",
        "best_for": ["fractions_decimals_percents"],
    },
    {
        "visual_type": "percent_grid_10x10",
        "purpose": "Показывать проценты через сетку 10×10 и точный счёт сотых",
        "best_for": ["fractions_decimals_percents"],
    },
    {
        "visual_type": "coordinate_plane_plot",
        "purpose": "Показывать точки на координатной плоскости и геометрию графиков",
        "best_for": ["functions_graphs", "geometry_measurement"],
    },
    {
        "visual_type": "algebra_tiles",
        "purpose": "Показывать алгебраические выражения и уравнения через плитки",
        "best_for": ["expressions_equations_inequalities"],
    },
    {
        "visual_type": "balance_scale_equation",
        "purpose": "Показывать равенство и уравнение как баланс",
        "best_for": ["expressions_equations_inequalities"],
    },
    {
        "visual_type": "function_table",
        "purpose": "Показывать вход/выход и правило функции в таблице",
        "best_for": ["functions_graphs"],
    },
    {
        "visual_type": "cartesian_graph",
        "purpose": "Показывать графики функций и зависимости",
        "best_for": ["functions_graphs"],
    },
    {
        "visual_type": "net_of_solid",
        "purpose": "Показывать развёртки тел и переход к объёмным фигурам",
        "best_for": ["geometry_measurement"],
    },
    {
        "visual_type": "geoboard_dynamic",
        "purpose": "Показывать фигуры, углы, площади и построения на сетке",
        "best_for": ["geometry_measurement"],
    },
    {
        "visual_type": "spatial_relations",
        "purpose": "Показывать относительное положение объектов: выше/ниже, слева/справа, перед/за",
        "best_for": ["geometry_measurement", "early_number_sense"],
    },
    {
        "visual_type": "shape_recognition",
        "purpose": "Показывать и распознавать базовые плоские фигуры и их признаки",
        "best_for": ["geometry_measurement"],
    },
    {
        "visual_type": "clock_face",
        "purpose": "Показывать время на циферблате, час и полчаса",
        "best_for": ["geometry_measurement", "measurement"],
    },
    {
        "visual_type": "number_bond",
        "purpose": "Показывать целое и части, связку числа",
        "best_for": ["addition_subtraction", "early_number_sense"],
    },
    {
        "visual_type": "cartesian_graph_slider",
        "purpose": "Показывать графики функций со слайдерами параметров",
        "best_for": ["functions_graphs"],
    },
    {
        "visual_type": "balance_scale_linear",
        "purpose": "Показывать линейные уравнения как баланс",
        "best_for": ["expressions_equations_inequalities"],
    },
    {
        "visual_type": "fraction_bars",
        "purpose": "Показывать дроби как части полосы",
        "best_for": ["fractions_decimals_percents"],
    },
    {
        "visual_type": "cut_and_drag_parallelogram",
        "purpose": "Показывать преобразование фигур и площади",
        "best_for": ["geometry_measurement"],
    },
    {
        "visual_type": "division_groups",
        "purpose": "Показывать деление на группы и  sharing",
        "best_for": ["multiplication_division"],
    },
]

_BASE_DIR = Path(__file__).resolve().parents[2]
_TOPIC_MAP_PATH = _BASE_DIR / "data" / "visual_topic_map.json"


def _normalize_topic_key(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().upper())


def _load_topic_blueprints() -> dict[tuple[int, str], dict[str, Any]]:
    try:
        raw = json.loads(_TOPIC_MAP_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

    overrides: dict[tuple[int, str], dict[str, Any]] = {}
    for entry in raw:
        try:
            grade = int(entry.get("grade", 0))
            topic = _normalize_topic_key(entry.get("topic", ""))
            if grade <= 0 or not topic:
                continue
            overrides[(grade, topic)] = entry
        except Exception:
            continue
    return overrides


TOPIC_BLUEPRINT_OVERRIDES = _load_topic_blueprints()


def _template_blueprint_from_visual(
    *,
    visual_type: str,
    title: str,
    prompt: str,
    family: str | None = None,
    grade: int | None = None,
) -> dict[str, Any] | None:
    template = _TEMPLATE_LIBRARY.get(visual_type)
    if not template:
        return None

    sections = [
        {
            "label": section["label"],
            "kind": section["kind"],
            "bullets": list(section["bullets"]),
        }
        for section in template["sections"]
    ]
    resolved_family = family or str(template.get("family") or "")
    return {
        "templateType": visual_type,
        "templateFamily": resolved_family,
        "templateLabel": template["label"],
        "templateStage": template["stage"],
        "templateGlyph": template["glyph"],
        "templateSections": sections,
        "templateHide": template["hide"],
        "templateWhy": template["why"],
        "templateNotes": template["notes"],
        "templateTitle": title,
        "templatePrompt": prompt,
        "templatePreview": {
            "grade": grade,
            "topic": title,
            "family": resolved_family,
            "visual_type": visual_type,
        },
    }


_TEMPLATE_LIBRARY: dict[str, dict[str, Any]] = {
    "number_bond": {
        "label": "Числовая связка",
        "family": "addition_subtraction",
        "stage": "concrete_pictorial_abstract",
        "glyph": "🧩",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи целое и части как отдельные предметы или фишки.",
                    "Сначала собери части в целое, потом назови число.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Отобрази две части и одно целое в компактной схеме.",
                    "Подпиши части так, чтобы ученик видел, как они складываются.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Только после модели покажи запись примера.",
                    "Спрячь ответ до того, как ученик увидит связь между частями и целым.",
                ],
            },
        ],
        "hide": "Не показывать результат раньше, чем ученик увидит части и целое.",
        "why": "Для ранней арифметики важно увидеть структуру числа как связку частей и целого.",
        "notes": "Базовый шаблон для grade 1 и ранней арифметики.",
    },
    "ten_frame": {
        "label": "Десятичная рамка",
        "family": "addition_subtraction",
        "stage": "concrete_pictorial_abstract",
        "glyph": "🔟",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи предметы по одному и сгруппируй их в десяток.",
                    "Пусть ученик считает руками или фишками.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Заполни рамку из 10 клеток, оставляя пустые клетки видимыми.",
                    "Покажи, какие клетки надо дополнить до полного десятка.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Только после картинки покажи запись примера.",
                    "Спрячь ответ до шага переноса/дополнения.",
                ],
            },
        ],
        "hide": "Спрятать итоговый ответ до момента, когда десяток собран на предметах и в рамке.",
        "why": "Рамка делает переход от предметов к записи наглядным и помогает видеть десяток как единицу счёта.",
        "notes": "Лучше всего работает для 1 класса и задач на состав числа 10.",
    },
    "number_line": {
        "label": "Числовая прямая",
        "family": "addition_subtraction",
        "stage": "pictorial_abstract",
        "glyph": "➖➕",
        "sections": [
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи стартовую точку и дуги шага по числовой прямой.",
                    "Разбей длинный шаг на короткие видимые переходы.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Покажи запись суммы или разности только после движения по прямой.",
                    "Укажи промежуточный переход через десяток или через удобную точку.",
                ],
            },
        ],
        "hide": "Не показывать ответ раньше, чем ученик увидит весь маршрут по прямой.",
        "why": "Числовая прямая связывает движение глазами с символической записью и делает шаги вычисления прозрачными.",
        "notes": "Хороша для сравнения, перехода через десяток и сложения/вычитания в 2–4 классах.",
    },
    "base_ten_blocks": {
        "label": "Блоки десятков и единиц",
        "family": "place_value",
        "stage": "concrete_pictorial_abstract",
        "glyph": "🧱",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи десятки палочками и единицы кубиками.",
                    "Разложи число на разрядные части.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи обмен 10 единиц на 1 десяток.",
                    "Сделай перенос видимым стрелкой или анимацией.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Запиши разложение числа по разрядам.",
                    "Покажи итоговый пример только после обмена.",
                ],
            },
        ],
        "hide": "Спрятать сокращённую запись до того, как ученик увидит обмен десятка и единиц.",
        "why": "Блоки делают разрядный состав видимым и помогают понять перенос через десяток без магии.",
        "notes": "Подходит для чисел 11–100 и сложения/вычитания с переходом.",
    },
    "place_value_chart": {
        "label": "Таблица разрядов",
        "family": "place_value",
        "stage": "pictorial_abstract",
        "glyph": "📊",
        "sections": [
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи таблицу десятков, единиц и, если нужно, сотен.",
                    "Заполни клетки числами и подчеркни разрядный переход.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Покажи запись числа с подписями разрядов.",
                    "Сделай ответ видимым только после разрядного разбора.",
                ],
            },
        ],
        "hide": "Не показывать краткую запись числа до заполнения таблицы.",
        "why": "Таблица разрядов помогает удерживать место каждой цифры и делает сложение/вычитание структурным.",
        "notes": "Сильный шаблон для 1–4 классов и повторения перед 5–6 классом.",
    },
    "part_part_whole_bar": {
        "label": "Часть–часть–целое",
        "family": "addition_subtraction",
        "stage": "concrete_pictorial_abstract",
        "glyph": "🧩",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи две части предметами разных цветов.",
                    "Собери их в одно целое на доске.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи полосовую модель с двумя сегментами и одной общей длиной.",
                    "Подпиши части отдельно и целое отдельно.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Запиши выражение только после того, как части и целое понятны.",
                ],
            },
        ],
        "hide": "Спрятать целое, пока ученик не увидит обе части.",
        "why": "Полосовая модель связывает части и целое и хорошо подходит для текстовых задач и дробей.",
        "notes": "Универсальный шаблон для ранней арифметики и word problems.",
    },
    "array_matrix": {
        "label": "Массив / таблица умножения",
        "family": "multiplication_division",
        "stage": "concrete_pictorial_abstract",
        "glyph": "⬛",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Собери группы одинаковых предметов в ряды и столбцы.",
                    "Пусть ученик видит повторяющиеся группы как один массив.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи сетку с рядами и столбцами.",
                    "Подпиши количество в каждом измерении.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Спрячь формулу умножения до момента, когда массив уже понятен.",
                    "Покажи перестановку множителей как тот же рисунок, но повёрнутый.",
                ],
            },
        ],
        "hide": "Спрятать результат и формулу, пока не видно сетки и повторяющихся групп.",
        "why": "Массив визуализирует умножение как повторяющееся сложение и готовит к таблице умножения.",
        "notes": "Опора для 2–4 классов и перехода к делению через группировку.",
    },
    "division_groups": {
        "label": "Группы деления",
        "family": "multiplication_division",
        "stage": "concrete_pictorial_abstract",
        "glyph": "➗",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Разложи предметы на равные группы.",
                    "Покажи, сколько предметов в каждой группе и сколько групп получилось.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Нарисуй одинаковые корзины, коробки или кружки-группы.",
                    "Сделай пустые места и недостающие группы видимыми.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Только потом покажи деление в записи.",
                    "Проверь остаток или делимость через рисунок.",
                ],
            },
        ],
        "hide": "Не показывать частное до завершения группировки предметов.",
        "why": "Равные группы убирают абстрактность деления и делают операцию наблюдаемой.",
        "notes": "Особенно полезно для начальной школы и остатка.",
    },
    "fraction_bars": {
        "label": "Полосы дробей",
        "family": "fractions_decimals_percents",
        "stage": "pictorial_abstract",
        "glyph": "◫",
        "sections": [
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Раздели полосу на равные части.",
                    "Подсвети долю, а не только запись дроби.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Покажи числитель и знаменатель как запись увиденной доли.",
                    "Спрячь итоговую дробь, пока не видно равные части.",
                ],
            },
        ],
        "hide": "Спрятать дробную запись до того, как ученик увидит равные части.",
        "why": "Полоса дробей удерживает идею равных частей и хорошо переносится на проценты и десятичные дроби.",
        "notes": "Универсальный шаблон для 3–6 классов.",
    },
    "fraction_circle_region": {
        "label": "Доля круга",
        "family": "fractions_decimals_percents",
        "stage": "concrete_pictorial_abstract",
        "glyph": "◔",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи предмет или пирог, разделённый на равные части.",
                    "Выдели нужную долю цветом.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи круг с секторами одинакового размера.",
                    "Подпиши, какая часть закрашена.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Свяжи рисунок с записью дроби.",
                ],
            },
        ],
        "hide": "Спрятать дробь до того, как видны равные части круга.",
        "why": "Круговая модель помогает увидеть часть целого и сравнивать доли.",
        "notes": "Хорошо работает для младших классов и бытовых задач.",
    },
    "percent_grid_10x10": {
        "label": "Сетка процентов 10×10",
        "family": "fractions_decimals_percents",
        "stage": "concrete_pictorial_abstract",
        "glyph": "%",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи квадрат 10×10 как 100 одинаковых клеток.",
                    "Закрашивай клетки по одной, чтобы видеть каждый процент как 1 из 100.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Нарисуй заполненную сетку и выдели нужное количество клеток.",
                    "Подпиши, сколько клеток уже закрашено и сколько осталось.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Покажи запись процента и формулу только после клеточной модели.",
                ],
            },
        ],
        "hide": "Спрятать формулу процента до того, как видно 100-клеточную сетку.",
        "why": "Сетка 10×10 даёт точный счёт процентов и делает 1 % визуально равным одной клетке.",
        "notes": "Лучший базовый шаблон для задач на проценты и доли от числа.",
    },
    "ratio_table": {
        "label": "Таблица отношений",
        "family": "ratios_proportions",
        "stage": "pictorial_abstract",
        "glyph": "↔",
        "sections": [
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи две связанные величины в строках или столбцах.",
                    "Сделай закономерность между ними видимой.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Покажи отношение и пропорцию в краткой записи только после таблицы.",
                ],
            },
        ],
        "hide": "Спрятать пропорциональную запись, пока отношения не собраны в таблице.",
        "why": "Таблица упорядочивает связанные величины и помогает искать масштабирование.",
        "notes": "Базовый шаблон для 5–8 классов.",
    },
    "double_number_line": {
        "label": "Две числовые прямые",
        "family": "ratios_proportions",
        "stage": "pictorial_abstract",
        "glyph": "〰️",
        "sections": [
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи две шкалы с одинаковыми шагами разной длины.",
                    "Отметь соответствующие значения дугами или стрелками.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Покажи соотношение только после визуального соответствия.",
                ],
            },
        ],
        "hide": "Спрятать числовую пропорцию до момента, когда шкалы совпали визуально.",
        "why": "Двойная прямая помогает увидеть масштабирование и связь двух величин.",
        "notes": "Подходит для процентов, пропорций и масштабов.",
    },
    "double_number_line_dynamic": {
        "label": "Две числовые прямые с привязкой",
        "family": "ratios_proportions",
        "stage": "pictorial_abstract",
        "glyph": "〰️↔️",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи опорную единицу и две величины, связанные одной ценой или масштабом.",
                    "Пусть ученик сначала видит, что одна шкала задаёт шаг другой.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Сделай привязку шкал к общей единице и покажи повторяющиеся шаги.",
                    "Подсвети, как меняется длина отрезка при изменении коэффициента.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Покажи формулу пропорции только после визуального совпадения шагов.",
                ],
            },
        ],
        "hide": "Спрятать запись пропорции, пока обе шкалы не выровнены по общей единице.",
        "why": "Динамическая двойная прямая делает коэффициент масштабирования видимым и удобным для пропорций и процентов.",
        "notes": "Лучше всего работает для 6–7 классов, масштабов и сравнения величин.",
    },
    "balance_scale_equation": {
        "label": "Весы равенства",
        "family": "expressions_equations_inequalities",
        "stage": "concrete_pictorial_abstract",
        "glyph": "⚖️",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи две стороны баланса с одинаковой массой.",
                    "Добавляй и убирай блоки одинаково с обеих сторон.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Изобрази левую и правую части уравнения как чаши весов.",
                    "Покажи, что баланс сохраняется при одинаковых действиях.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Покажи уравнение только после видимого уравнивания сторон.",
                ],
            },
        ],
        "hide": "Спрятать x или ответ, пока не выполнено уравновешивание шагов на весах.",
        "why": "Весы переводят уравнение в понятный принцип равновесия и снимают страх перед неизвестной.",
        "notes": "Лучший базовый шаблон для линейных уравнений и неравенств.",
    },
    "balance_scale_linear": {
        "label": "Весы линейного уравнения",
        "family": "expressions_equations_inequalities",
        "stage": "concrete_pictorial_abstract",
        "glyph": "⚖️➖",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи неизвестное как один одинаковый блок на весах.",
                    "Убери или добавь одинаковые куски с обеих сторон по одному шагу.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Разбей линейное выражение на шаги переноса и упрощения.",
                    "Сделай видимым, как коэффициент и свободный член меняют баланс.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Запиши линейное уравнение только после равного упрощения обеих сторон.",
                ],
            },
        ],
        "hide": "Спрятать сокращённую форму и ответ, пока не завершён поэтапный перенос.",
        "why": "Линейные уравнения лучше понимаются как последовательность равных преобразований баланса.",
        "notes": "Особенно полезно для 7–8 классов и задач с коэффициентом перед x.",
    },
    "algebra_tiles": {
        "label": "Алгебраические плитки",
        "family": "expressions_equations_inequalities",
        "stage": "concrete_pictorial_abstract",
        "glyph": "🧩",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи x-плитки и единичные плитки разных цветов.",
                    "Собери выражение как физический набор деталей.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Нарисуй плитки на сетке, чтобы было видно сборку и сокращение.",
                    "Сделай исчезновение парных элементов очевидным.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Переведи плитки в символы и уравнение.",
                ],
            },
        ],
        "hide": "Спрятать символическую запись до завершения сборки плиток.",
        "why": "Плитки дают физический аналог алгебры и помогают увидеть сборку/разбор выражений.",
        "notes": "Очень полезно для 5–9 классов.",
    },
    "function_table": {
        "label": "Таблица функции",
        "family": "functions_graphs",
        "stage": "pictorial_abstract",
        "glyph": "📋",
        "sections": [
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи входы и выходы в таблице.",
                    "Подсвети правило преобразования между строками.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Переведи таблицу в формулу или правило только после анализа данных.",
                ],
            },
        ],
        "hide": "Спрятать формулу до того, как закономерность в таблице станет явной.",
        "why": "Таблица связывает набор значений с правилом и готовит к графику.",
        "notes": "Хорошо для линейных и нелинейных функций.",
    },
    "cartesian_graph": {
        "label": "Координатный график",
        "family": "functions_graphs",
        "stage": "pictorial_abstract",
        "glyph": "📈",
        "sections": [
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Отметь точки на координатной плоскости.",
                    "Покажи, как точки формируют линию или кривую.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Сделай правило функции видимым по положению точек.",
                ],
            },
        ],
        "hide": "Спрятать уравнение графика до того, как ученик увидит точки и форму.",
        "why": "График связывает таблицу, формулу и поведение функции в пространстве.",
        "notes": "Подходит для 7–9 классов и аналитической геометрии.",
    },
    "cartesian_graph_slider": {
        "label": "График со слайдерами",
        "family": "functions_graphs",
        "stage": "pictorial_abstract",
        "glyph": "🎚️📈",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи, как ползунки меняют коэффициенты на экране.",
                    "Пусть ученик сначала двигает один параметр и смотрит на результат.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи, как линия или парабола меняется при движении слайдера.",
                    "Подсвети влияние наклона, сдвига и вершины отдельно.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Запиши формулу только после того, как виден эффект каждого параметра.",
                ],
            },
        ],
        "hide": "Спрятать коэффициенты и формулу, пока изменение графика не стало заметным.",
        "why": "Слайдеры превращают абстрактные параметры в наглядное изменение формы графика.",
        "notes": "Особенно полезно для линейных и квадратичных функций в 8–9 классах.",
    },
    "coordinate_plane_plot": {
        "label": "Координатная плоскость",
        "family": "geometry_measurement",
        "stage": "pictorial_abstract",
        "glyph": "✳️",
        "sections": [
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи оси и точку(и) на плоскости.",
                    "Подсвети координаты как шаги по горизонтали и вертикали.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Переведи точки в координаты только после визуального размещения.",
                ],
            },
        ],
        "hide": "Спрятать координаты до того, как точка найдена на сетке.",
        "why": "Координатная плоскость даёт видимый переход от шага на сетке к записи пары чисел.",
        "notes": "Полезно для геометрии и графиков.",
    },
    "net_of_solid": {
        "label": "Развёртка тела",
        "family": "geometry_measurement",
        "stage": "concrete_pictorial_abstract",
        "glyph": "🧊",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи физическую коробку или модель тела.",
                    "Разверни её в плоскую схему.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Нарисуй развёртку с подписанными гранями.",
                    "Покажи, как из неё складывается объёмная фигура.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Покажи формулу площади или объёма только после развёртки.",
                ],
            },
        ],
        "hide": "Спрятать формулу, пока не видна развёртка и связь с телом.",
        "why": "Развёртка помогает понять форму тела и перейти к площади и объёму.",
        "notes": "Опора для стереометрии и начальной геометрии.",
    },
    "geoboard_dynamic": {
        "label": "Геопланшет",
        "family": "geometry_measurement",
        "stage": "concrete_pictorial_abstract",
        "glyph": "📐",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи натяжение резинок между гвоздиками или точками.",
                    "Меняй фигуру и наблюдай, что сохраняется.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Покажи сетку, отрезки, углы и подпиши измерения.",
                    "Сделай форму фигуры видимой как набор связей.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Покажи вычисление периметра, площади или углов после построения.",
                ],
            },
        ],
        "hide": "Спрятать числовой ответ до построения фигуры на сетке.",
        "why": "Геопланшет помогает строить и менять фигуры, а не только читать готовые чертежи.",
        "notes": "Подходит для построений, симметрии и площади.",
    },
    "cut_and_drag_parallelogram": {
        "label": "Разрежь и перетащи параллелограмм",
        "family": "geometry_measurement",
        "stage": "concrete_pictorial_abstract",
        "glyph": "✂️🟩",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи параллелограмм как фигуру, которую можно мысленно разрезать по высоте.",
                    "Перетащи срезанный треугольник к другой стороне, чтобы получить прямоугольник.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Подпиши основание и высоту до и после разрезания.",
                    "Покажи, что площадь не меняется при переносе куска.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Запиши формулу площади только после преобразования в прямоугольник.",
                ],
            },
        ],
        "hide": "Спрятать формулу площади, пока ученик не увидит преобразование фигуры.",
        "why": "Разрезание и перенос делают площадь параллелограмма доказуемой через площадь прямоугольника.",
        "notes": "Лучший шаблон для площади параллелограмма и похожих фигур в 5–8 классах.",
    },
    "spatial_relations": {
        "label": "Пространственные отношения",
        "family": "geometry_measurement",
        "stage": "concrete_pictorial_abstract",
        "glyph": "⬆️⬇️",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи реальные предметы и отношения между ними: выше, ниже, слева, справа, спереди, сзади.",
                    "Пусть ученик сначала укажет предметы руками или взглядом.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Нарисуй два-три предмета на простой сцене и подпиши направление стрелками.",
                    "Сделай видимым один и тот же сюжет в другом положении.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Свяжи расположение с краткой словесной записью: слева от, справа от, выше, ниже.",
                ],
            },
        ],
        "hide": "Не показывать словесный ответ, пока ребёнок не проверит расположение на сцене.",
        "why": "Пространственные отношения проще понять через предметную сцену и повторить в рисунке.",
        "notes": "Нужен для тем 1 класса про позиции и для дальнейшей геометрии.",
    },
    "shape_recognition": {
        "label": "Распознавание фигур",
        "family": "geometry_measurement",
        "stage": "concrete_pictorial_abstract",
        "glyph": "◻️",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи предметы из жизни, похожие на круг, квадрат, треугольник и прямоугольник.",
                    "Пусть ученик находит фигуры в окружении, а не только на картинке.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Нарисуй контуры фигур и подсвети их признаки: стороны, углы, кривую линию.",
                    "Покажи одинаковые и разные фигуры рядом.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Свяжи фигуру с названием и краткими признаками.",
                ],
            },
        ],
        "hide": "Не показывать название фигуры сразу, если задача на узнавание.",
        "why": "Фигуры легче запоминать через реальные объекты и контуры, а не через сухой список названий.",
        "notes": "Подходит для тем первого и второго классов о фигурах.",
    },
    "clock_face": {
        "label": "Часы и время",
        "family": "geometry_measurement",
        "stage": "concrete_pictorial_abstract",
        "glyph": "🕒",
        "sections": [
            {
                "label": "Concrete",
                "kind": "concrete",
                "bullets": [
                    "Покажи реальные часы или макет циферблата.",
                    "Пусть ученик двигает стрелки сам и называет время.",
                ],
            },
            {
                "label": "Pictorial",
                "kind": "pictorial",
                "bullets": [
                    "Нарисуй циферблат с крупными делениями и разными стрелками.",
                    "Подсвети час и полчаса как два разных устойчивых случая.",
                ],
            },
            {
                "label": "Abstract",
                "kind": "abstract",
                "bullets": [
                    "Свяжи положение стрелок с цифровой записью времени.",
                ],
            },
        ],
        "hide": "Спрятать цифровую запись времени до того, как ребёнок увидит стрелки.",
        "why": "Часы проще понять через макет, чем через одну только цифровую запись.",
        "notes": "Закрывает тему часов в 1–2 классах.",
    },
}


def _normalize_text(*parts: Any) -> str:
    values = [str(part) for part in parts if part is not None and str(part).strip()]
    return " ".join(values).lower()


def _extract_grade(question: dict[str, Any]) -> int:
    try:
        return int(question.get("grade") or 0)
    except Exception:
        return 0


def _looks_like_equation(text: str) -> bool:
    return any(token in text for token in (" уравнен", "= x", "найди x", "реши урав", "баланс", "неизвестн"))


def _looks_like_fraction(text: str) -> bool:
    return any(token in text for token in ("дроб", "1/", "/2", "/3", "/4", "процент", "процен"))


def _looks_like_ratio(text: str) -> bool:
    return any(token in text for token in ("отношен", "пропорц", "масшт", "ratio", "scale", "unit rate"))


def _looks_like_function(text: str) -> bool:
    return any(token in text for token in ("функц", "график", "координат", "таблиц знач", "вход", "выход"))


def _looks_like_geometry(text: str) -> bool:
    return any(token in text for token in ("геометр", "угол", "периметр", "площад", "объём", "объем", "тело", "многогран", "параллелепипед"))


def _looks_like_multiplication(text: str) -> bool:
    return any(token in text for token in ("умнож", "таблиц умнож", "произвед", "times", "factor", "групп по", "повторяющ"))


def _looks_like_division(text: str) -> bool:
    return any(token in text for token in ("делен", "подели", "раздел", "частн", "остат", "group", "divide"))


def _looks_like_place_value(text: str) -> bool:
    return any(token in text for token in ("десят", "единиц", "разряд", "двузнач", "трёхзнач", "трехзнач", "разложи число", "число до 100", "число до 1000"))


def _looks_like_next_number(text: str) -> bool:
    return any(token in text for token in ("следующ", "идёт после", "идет после", "число после", "какое число идёт", "какое число идет"))

def _looks_like_addition_subtraction(text: str) -> bool:
    return any(token in text for token in ("слож", "вычит", "+", "-", "сумм", "разность", "добав", "убав"))



def _needs_carry_or_borrow(text: str, numbers: list[int]) -> bool:
    if len(numbers) < 2:
        return False

    first, second = numbers[0], numbers[1]

    if any(token in text for token in ("через 10", "через десят", "regroup", "carry")):
        return True

    if "+" in text or any(token in text for token in ("слож", "плюс", "прибав", "добав")):
        return first + second >= 10

    if "-" in text or any(token in text for token in ("вычит", "убер", "отня", "минус")):
        return first < second

    return False



def _select_visual_type(question: dict[str, Any]) -> tuple[str | None, str | None]:
    grade = _extract_grade(question)
    text = _normalize_text(question.get("topic"), question.get("title"), question.get("question"), question.get("answer"))
    prompt_text = _normalize_text(question.get("question"), question.get("answer"))
    numbers = [int(value) for value in re.findall(r"\d+", prompt_text)]

    if _looks_like_equation(text):
        if any(token in text for token in ("линейн", "коэффициент", "ax", "bx", "перенос")):
            return "expressions_equations_inequalities", "balance_scale_linear"
        return "expressions_equations_inequalities", "balance_scale_equation"
    if _looks_like_function(text):
        if any(token in text for token in ("линейн", "квадрат", "парабол", "y=", "слайдер", "коэффиц")):
            return "functions_graphs", "cartesian_graph_slider"
        return "functions_graphs", "function_table"
    if _looks_like_ratio(text):
        if any(token in text for token in ("пропорц", "масшт", "scale", "отношен")):
            return "ratios_proportions", "double_number_line_dynamic"
        return "ratios_proportions", "ratio_table"
    if _looks_like_fraction(text):
        if "процент" in text or "процен" in text:
            return "fractions_decimals_percents", "percent_grid_10x10"
        return "fractions_decimals_percents", "fraction_bars"
    if _looks_like_multiplication(text):
        return "multiplication_division", "array_matrix"
    if _looks_like_division(text):
        return "multiplication_division", "division_groups"
    if _looks_like_geometry(text):
        if "параллелограмм" in text:
            return "geometry_measurement", "cut_and_drag_parallelogram"
        if any(token in text for token in ("площад", "высот", "основан")):
            return "geometry_measurement", "cut_and_drag_parallelogram"
        return "geometry_measurement", "geoboard_dynamic"
    if _looks_like_place_value(text):
        return "place_value", "base_ten_blocks" if grade <= 4 else "place_value_chart"
    if _looks_like_next_number(text):
        return "addition_subtraction", "number_line"
    if _looks_like_addition_subtraction(text):
        if _needs_carry_or_borrow(text, numbers):
            return "addition_subtraction", "number_line"
        return "addition_subtraction", "part_part_whole_bar"
    return None, None


def _select_age_based_visual(grade: int, skill_contract: dict[str, Any] | None) -> str | None:
    """D1: Select visual type based on student age/grade and skill_contract.

    Grade bands (CPA model):
      1-4 (младшая школа):   concrete-pictorial visuals
      5-6 (средняя школа):   pictorial-abstract visuals
      7-9 (старшая школа):   abstract-representational visuals
    """
    visual_policy = (skill_contract or {}).get("visual_policy") or {}
    age_band = visual_policy.get("age_band")

    if age_band == "junior":
        grade = min(grade, 4)
    elif age_band == "middle":
        grade = max(min(grade, 6), 5)
    elif age_band == "senior":
        grade = max(grade, 7)

    if grade <= 4:
        return "number_bond"
    elif grade <= 6:
        return "place_value_chart"
    else:
        return "coordinate_plane_plot"


def build_template_blueprint(
    question: dict[str, Any],
    skill_contract: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    grade = _extract_grade(question)
    title = str(question.get("topic") or question.get("title") or "Задание")
    prompt = str(question.get("question") or "")
    topic_key = _normalize_topic_key(title)

    # D1: Check skill_contract visual_policy first (highest priority)
    if skill_contract:
        visual_policy = skill_contract.get("visual_policy") or {}
        contract_visual = str(visual_policy.get("template") or "").strip()
        if contract_visual and contract_visual in _TEMPLATE_LIBRARY:
            family = str(visual_policy.get("family") or _TEMPLATE_LIBRARY[contract_visual].get("family") or "")
            blueprint = _template_blueprint_from_visual(
                visual_type=contract_visual,
                title=title,
                prompt=prompt,
                family=family,
                grade=grade,
            )
            if blueprint:
                blueprint["templateReason"] = f"Визуал из skill_contract: {contract_visual}"
                blueprint["templateSource"] = "skill_contract"
                return blueprint

        # D1: Age-based visual selection from contract
        age_visual = _select_age_based_visual(grade, skill_contract)
        if age_visual and age_visual in _TEMPLATE_LIBRARY:
            family = _TEMPLATE_LIBRARY[age_visual].get("family") or ""
            blueprint = _template_blueprint_from_visual(
                visual_type=age_visual,
                title=title,
                prompt=prompt,
                family=family,
                grade=grade,
            )
            if blueprint:
                blueprint["templateReason"] = f"Возрастной визуал для grade {grade}: {age_visual}"
                blueprint["templateSource"] = "age_based"
                return blueprint

    # Fallback: topic blueprint overrides
    override = TOPIC_BLUEPRINT_OVERRIDES.get((grade, topic_key))
    if override:
        visual_type = str(override.get("visual_type") or "")
        family = str(override.get("family") or "") or None
        blueprint = _template_blueprint_from_visual(
            visual_type=visual_type,
            title=title,
            prompt=prompt,
            family=family,
            grade=grade,
        )
        if blueprint:
            blueprint["templateReason"] = str(override.get("reason") or "")
            blueprint["templateSkills"] = list(override.get("skills") or [])
            return blueprint

    family, visual_type = _select_visual_type(question)
    if not visual_type:
        return None

    blueprint = _template_blueprint_from_visual(
        visual_type=visual_type,
        title=title,
        prompt=prompt,
        family=family,
        grade=grade,
    )
    if blueprint:
        blueprint["templateReason"] = f"Эвристический выбор для темы {title!r}."
    return blueprint


def decorate_question_visual(
    question: dict[str, Any],
    skill_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prompt = str(question.get("question") or "")
    prompt_lower = prompt.lower()
    numbers = [int(value) for value in re.findall(r"\d+", prompt)]
    title = str(question.get("topic") or "Задание")
    cpa = dict(question.get("CPA") or {})
    template_blueprint = build_template_blueprint(question, skill_contract=skill_contract)

    def _looks_like_simple_arithmetic() -> bool:
        if len(numbers) < 2:
            return False
        return bool(
            re.search(r"[+−-]", prompt)
            or any(
                token in prompt_lower
                for token in (
                    "сколько всего",
                    "плюс",
                    "прибав",
                    "слож",
                    "выч",
                    "убер",
                    "останет",
                    "минус",
                    "отня",
                )
            )
        )

    if template_blueprint and template_blueprint.get("templateSections"):
        template_family = str(template_blueprint.get("templateFamily") or "")
        template_type = str(template_blueprint.get("templateType") or "")
        if not (
            template_family in {"addition_subtraction", "place_value"}
            and _looks_like_simple_arithmetic()
            and template_type != "number_bond"
        ):
            return {
                "type": "question",
                "title": title,
                "prompt": prompt,
                "cpaVisual": "unknown",
                "objects": str(cpa.get("objects") or ""),
                "parts": None,
                "colors": None,
                "answer": str(question.get("answer") or ""),
                "topic": str(question.get("topic") or ""),
                **template_blueprint,
            }

    def _number_bond(parts: list[int], *, operation: str = "add") -> dict[str, Any]:
        total = sum(parts) if operation != "subtract" else (parts[0] if parts else 0)
        return {
            "type": "number_bond",
            "total": total,
            "parts": parts,
            "title": title,
            "prompt": prompt,
            "topic": str(question.get("topic") or ""),
            "operation": operation,
        }

    def _ten_frame(filled: int, total: int = 10) -> dict[str, Any]:
        return {
            "type": "ten_frame",
            "filled": filled,
            "total": total,
            "title": title,
            "prompt": prompt,
            "topic": str(question.get("topic") or ""),
        }

    # Keep the existing lightweight visuals for early arithmetic; they work better than a blueprint.
    if any(token in prompt_lower for token in ("рамк", "клетк", "десят")) and len(numbers) >= 2:
        first, second = numbers[0], numbers[1]
        filled = second if first >= 10 else min(first, second)
        return {
            "type": "question",
            "title": title,
            "prompt": prompt,
            "cpaVisual": "number_line",
            "objects": str(cpa.get("objects") or ""),
            "parts": None,
            "colors": None,
            "answer": str(question.get("answer") or ""),
            "topic": str(question.get("topic") or ""),
            "templateType": "ten_frame",
            "templateFamily": "addition_subtraction",
            "templateLabel": _TEMPLATE_LIBRARY["ten_frame"]["label"],
            "templateStage": _TEMPLATE_LIBRARY["ten_frame"]["stage"],
            "templateGlyph": _TEMPLATE_LIBRARY["ten_frame"]["glyph"],
            "templateSections": _TEMPLATE_LIBRARY["ten_frame"]["sections"],
            "templateHide": _TEMPLATE_LIBRARY["ten_frame"]["hide"],
            "templateWhy": _TEMPLATE_LIBRARY["ten_frame"]["why"],
            "templateNotes": _TEMPLATE_LIBRARY["ten_frame"]["notes"],
            "templatePreview": _ten_frame(filled=filled, total=10 if first >= 10 else max(first, second)),
        }

    if "+" in prompt or any(token in prompt_lower for token in ("сколько всего", "плюс", "прибав")):
        if len(numbers) >= 2:
            return _number_bond(numbers[:2], operation="add")

    if "-" in prompt or any(token in prompt_lower for token in ("выч", "убер", "останет")):
        if len(numbers) >= 2:
            return _number_bond(numbers[:2], operation="subtract")

    cpa_visual = str(cpa.get("visual") or "")
    if not cpa_visual:
        if any(token in prompt_lower for token in ("кружк", "круг", "шар", "яблок", "предмет")) and len(numbers) >= 2:
            cpa_visual = "counting"
        elif any(token in prompt_lower for token in ("стол", "под", "над", "слева", "справа")):
            cpa_visual = "position"
        elif any(token in prompt_lower for token in ("час", "часы", "время")):
            cpa_visual = "clock"
        elif any(token in prompt_lower for token in ("фигур", "квадрат", "круг", "треуг")):
            cpa_visual = "shapes"
        else:
            cpa_visual = "unknown"

    parts: list[int] | None = numbers[:2] if cpa_visual == "counting" and len(numbers) >= 2 else None

    colors: list[str] | None = None
    if cpa_visual == "counting":
        color_map = [
            ("красн", "red"),
            ("син", "blue"),
            ("зелён", "emerald"),
            ("желт", "gold"),
            ("оранж", "gold"),
            ("фиолет", "purple"),
        ]
        found_colors = [color for token, color in color_map if token in prompt_lower]
        if found_colors:
            colors = found_colors[: len(parts or found_colors)]

    base = {
        "type": "question",
        "title": title,
        "prompt": prompt,
        "cpaVisual": cpa_visual,
        "objects": str(cpa.get("objects") or ""),
        "parts": parts,
        "colors": colors,
        "answer": str(question.get("answer") or ""),
        "topic": str(question.get("topic") or ""),
    }

    blueprint = build_template_blueprint(question)
    if blueprint and blueprint["templateFamily"] in {"multiplication_division", "fractions_decimals_percents", "ratios_proportions", "expressions_equations_inequalities", "functions_graphs", "geometry_measurement"}:
        base.update(blueprint)
    return base
