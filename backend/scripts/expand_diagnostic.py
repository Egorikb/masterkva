#!/usr/bin/env python3
"""Generate the full diagnostic pool for grades 1-9 from curriculum topics."""

from pathlib import Path
import json, re

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "diagnostic_pool.json"

MANUAL_1_6 = [
  [
    1,
    "ПОДГОТОВКА",
    "Посмотри на 3 красных и 2 синих кружка. Сколько всего кружков?",
    "5",
    [
      "5",
      "пять"
    ],
    1,
    "Concrete",
    "кружки",
    "counting"
  ],
  [
    1,
    "ПОЗИЦИИ",
    "Если мяч лежит под столом, где он находится относительно стола?",
    "под столом",
    [
      "снизу",
      "под"
    ],
    1,
    "Concrete",
    "мяч и стол",
    "position"
  ],
  [
    1,
    "СЛОЖЕНИЕ/ВЫЧИТАНИЕ ДО 5",
    "2 + 3 = ?",
    "5",
    [
      "5",
      "пять"
    ],
    1,
    "Abstract",
    "числа",
    "addition"
  ],
  [
    1,
    "ФИГУРЫ",
    "Какая фигура имеет 4 равные стороны?",
    "квадрат",
    [
      "квадрат"
    ],
    1,
    "Concrete",
    "фигуры",
    "shapes"
  ],
  [
    1,
    "СЛОЖЕНИЕ/ВЫЧИТАНИЕ ДО 10",
    "7 - 4 = ?",
    "3",
    [
      "3",
      "три"
    ],
    1,
    "Abstract",
    "числа",
    "number_line"
  ],
  [
    1,
    "ЧАСЫ",
    "Если на часах 6:00, сколько это часов?",
    "6",
    [
      "6",
      "шесть"
    ],
    1,
    "Concrete",
    "часы",
    "clock"
  ],
  [
    1,
    "СЛОЖЕНИЕ С ПЕРЕХОДОМ",
    "8 + 5 = ?",
    "13",
    [
      "13",
      "тринадцать"
    ],
    1,
    "Abstract",
    "числа",
    "carry"
  ],
  [
    2,
    "СЛОЖЕНИЕ/ВЫЧИТАНИЕ",
    "46 + 13 = ?",
    "59",
    [
      "59"
    ],
    1,
    "Abstract",
    "числа",
    "addition"
  ],
  [
    2,
    "УМНОЖЕНИЕ",
    "3 × 5 = ?",
    "15",
    [
      "15"
    ],
    1,
    "Pictorial",
    "группы",
    "array"
  ],
  [
    2,
    "ДЕЛЕНИЕ",
    "18 ÷ 6 = ?",
    "3",
    [
      "3"
    ],
    1,
    "Pictorial",
    "группы",
    "division"
  ],
  [
    2,
    "СМЕШАННЫЕ ОПЕРАЦИИ",
    "12 - 4 + 6 = ?",
    "14",
    [
      "14"
    ],
    2,
    "Abstract",
    "числа",
    "mixed_ops"
  ],
  [
    3,
    "СЛОЖЕНИЕ/ВЫЧИТАНИЕ",
    "83 - 27 = ?",
    "56",
    [
      "56"
    ],
    1,
    "Abstract",
    "числа",
    "column_subtraction"
  ],
  [
    3,
    "УМНОЖЕНИЕ",
    "6 × 8 = ?",
    "48",
    [
      "48"
    ],
    1,
    "Concrete",
    "фишки",
    "array"
  ],
  [
    3,
    "ДРОБИ",
    "Что больше: 1/2 или 1/4?",
    "1/2",
    [
      "половина",
      "1/2"
    ],
    2,
    "Pictorial",
    "полоса",
    "fraction_bar"
  ],
  [
    3,
    "ПЛОЩАДЬ",
    "Площадь прямоугольника 4 см × 3 см = ?",
    "12 см²",
    [
      "12",
      "12 см²"
    ],
    2,
    "Concrete",
    "клетки",
    "area"
  ],
  [
    4,
    "БОЛЬШИЕ ЧИСЛА",
    "4 305 + 270 = ?",
    "4 575",
    [
      "4575",
      "4 575"
    ],
    2,
    "Abstract",
    "числа",
    "place_value"
  ],
  [
    4,
    "УМНОЖЕНИЕ/ДЕЛЕНИЕ",
    "96 ÷ 8 = ?",
    "12",
    [
      "12"
    ],
    2,
    "Abstract",
    "числа",
    "division"
  ],
  [
    4,
    "ПЛОЩАДЬ",
    "Площадь прямоугольника 7 см × 8 см = ?",
    "56 см²",
    [
      "56",
      "56 см²"
    ],
    2,
    "Concrete",
    "плитки",
    "area"
  ],
  [
    4,
    "УРАВНЕНИЯ",
    "Реши: x + 9 = 17",
    "8",
    [
      "x = 8",
      "8"
    ],
    2,
    "Abstract",
    "буквы",
    "balance"
  ],
  [
    5,
    "ДРОБИ",
    "2/5 + 1/5 = ?",
    "3/5",
    [
      "3/5",
      "три пятых"
    ],
    2,
    "Pictorial",
    "полоса",
    "fraction_bar"
  ],
  [
    5,
    "УМНОЖЕНИЕ/ДЕЛЕНИЕ ДРОБЕЙ",
    "1/2 × 1/3 = ?",
    "1/6",
    [
      "1/6",
      "одна шестая"
    ],
    3,
    "Pictorial",
    "полоса",
    "fraction_multiplication"
  ],
  [
    5,
    "ПРОЦЕНТЫ",
    "15% от 200 = ?",
    "30",
    [
      "30"
    ],
    2,
    "Pictorial",
    "полоса",
    "percent_bar"
  ],
  [
    5,
    "ПЛОЩАДЬ",
    "Площадь треугольника с основанием 10 см и высотой 6 см = ?",
    "30 см²",
    [
      "30",
      "30 см²"
    ],
    3,
    "Concrete",
    "треугольник",
    "triangle_area"
  ],
  [
    6,
    "ОТРИЦАТЕЛЬНЫЕ ЧИСЛА",
    "-3 + 7 = ?",
    "4",
    [
      "4"
    ],
    2,
    "Pictorial",
    "числовая прямая",
    "number_line"
  ],
  [
    6,
    "СЛОЖЕНИЕ/ВЫЧИТАНИЕ",
    "45 - 18 = ?",
    "27",
    [
      "27"
    ],
    2,
    "Abstract",
    "числа",
    "column_subtraction"
  ],
  [
    6,
    "УМНОЖЕНИЕ/ДЕЛЕНИЕ",
    "56 ÷ 7 = ?",
    "8",
    [
      "8"
    ],
    2,
    "Abstract",
    "числа",
    "division"
  ],
  [
    6,
    "ПРОПОРЦИИ",
    "Если 3 тетради стоят 45 ₽, сколько стоит 1 тетрадь?",
    "15 ₽",
    [
      "15",
      "15 ₽"
    ],
    3,
    "Pictorial",
    "тетради",
    "ratio"
  ]
]


def make_question(grade, topic, question, answer, alternatives=None, difficulty=1, cpa_type='Abstract', objects='числа', visual='formula'):
    return {
        'grade': grade,
        'topic': topic,
        'question': question,
        'answer': answer,
        'alternatives': alternatives or [],
        'difficulty': difficulty,
        'CPA': {'type': cpa_type, 'objects': objects, 'visual': visual},
    }


def clean_question(q: str) -> str:
    q = q.strip()
    q = re.split(r'\s+Сначала\b', q, maxsplit=1)[0].strip()
    q = re.split(r'\s+Пусть\b', q, maxsplit=1)[0].strip()
    q = re.split(r'\s+Дай\b', q, maxsplit=1)[0].strip()
    return q.rstrip(' .')


def main() -> None:
    questions = [make_question(*row) for row in MANUAL_1_6]
    base = ROOT / 'data' / 'curriculum_detailed'
    for grade in (7, 8, 9):
        files = sorted(base.glob(f'grade_{grade}_topic_*.json'), key=lambda p: int(p.stem.split('_')[-1]))
        for p in files:
            obj = json.loads(p.read_text(encoding='utf-8'))
            topic = obj.get('title') or obj.get('topic') or p.stem
            if str(topic).startswith('ПОВТОРЕНИЕ'):
                continue
            source = obj.get('exercises', [None])[0] if obj.get('exercises') else (obj.get('problems', [None])[0] if obj.get('problems') else None)
            if not source:
                continue
            q = clean_question(source.get('question', ''))
            answer = source.get('answer') or source.get('solution') or ''
            if not q or not answer:
                continue
            title_upper = topic.upper()
            cpa_type = 'Abstract'
            objects = 'числа'
            visual = 'formula'
            if any(k in title_upper for k in ['ГЕОМЕТР', 'ТРЕУГОЛЬНИК', 'ПАРАЛЛЕЛОГРАМ', 'ОКРУЖНОСТ', 'ПОВОРОТ', 'СИММЕТРИ', 'ЛУЧ', 'ОТРЕЗОК', 'УГЛ']):
                cpa_type = 'Pictorial'; objects = 'геометрия'; visual = 'geometry'
            elif any(k in title_upper for k in ['ДАННЫ', 'ВЕРОЯТНОСТ', 'ОБРАТНАЯ ПРОПОРЦИ', 'ПРОЕКЦ']):
                cpa_type = 'Pictorial'; objects = 'таблица'; visual = 'data'
            elif any(k in title_upper for k in ['ЧИСЛ', 'УРАВН', 'ВЫРАЖ', 'ФУНКЦ', 'КВАДРАТ', 'КОРН', 'ПОДОБ', 'НЕРАВЕН', 'ПРОПОРЦ', 'ТРИГОНОМ']):
                cpa_type = 'Abstract'; objects = 'числа'; visual = 'algebra'
            questions.append(make_question(grade, topic, q, str(answer), [str(answer)], 4 if grade == 7 else 5, cpa_type, objects, visual))

    questions = sorted(questions, key=lambda x: (x['grade'], x['topic'], x['question']))
    counts = {}
    for q in questions:
        counts[str(q['grade'])] = counts.get(str(q['grade']), 0) + 1
    pool = {
        'version': 2,
        'description': 'Full diagnostic pool by curriculum topic coverage (review topics excluded).',
        'questions_per_grade': counts,
        'total_questions': len(questions),
        'questions': questions,
    }
    OUT.write_text(json.dumps(pool, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'wrote {OUT}')
    print(f'total {len(questions)}')
    print(f'counts {counts}')


if __name__ == '__main__':
    main()
