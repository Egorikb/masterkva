#!/usr/bin/env python3
"""
Адаптация curriculum_detailed под российского школьника.
Заменяет общие задачи на задачи с российским контекстом.
"""

import json
from pathlib import Path

CURRICULUM_DIR = Path(__file__).parent.parent / "data" / "curriculum_detailed"

# Замены для российского контекста
REPLACEMENTS = {
    # Деньги
    "юань": "рубль",
    "юаней": "рублей",
    "юаня": "рубля",
    "¥": "₽",
    "元": "руб",
    
    # Имена (общие → русские)
    "Сяомин": "Петя",
    "Сяохуа": "Вася",
    "Сяоцян": "Коля",
    "Сяохун": "Маша",
    "Сяофан": "Света",
    "Линлин": "Оля",
    "Дундун": "Саша",
    
    # Предметы
    "баскетбольный мяч": "футбольный мяч",
    "волейбольный мяч": "волейбольный мяч",
    "пинг-понг": "настольный теннис",
    
    # Еда
    "пельмени": "пельмени",
    "блины": "блины",
    "борщ": "борщ",
    "каша": "каша",
    "окрошка": "окрошка",
    
    # Места
    "школьный двор": "школьный двор",
    "школьная столовая": "школьная столовая",
    "спортзал": "спортзал",
    "академия": "школа",
    
    # Праздники
    "Весенний фестиваль": "Новый год",
    "Праздник середины осени": "8 марта",
    "День учителя": "День учителя",
}

# Контекстные шаблоны для задач
RUSSIAN_CONTEXTS = {
    "магазин": [
        "Мама дала {name} {money}₽ на покупки. {name} купил {item} за {price}₽. Сколько сдачи?",
        "В школьной столовой {item} стоит {price}₽. У {name} {money}₽. Хватит ли на {count} {item}?",
        "{name} купил {item1} за {price1}₽ и {item2} за {price2}₽. Сколько всего потратил?",
    ],
    "школа": [
        "В классе {count1} мальчиков и {count2} девочек. Сколько всего учеников?",
        "{name} прочитал {count1} страниц учебника, осталось {count2}. Сколько страниц всего?",
        "На уроке математики {count1} учеников получили пятёрки, {count2} — четвёрки. Сколько всего?",
    ],
    "спорт": [
        "{name} пробежал {dist1} км, а {name2} — на {dist2} км больше. Сколько пробежал {name2}?",
        "Футбольное поле длиной {length} м и шириной {width} м. Периметр?",
        "{name} делает {count} отжиманий за подход. За {n} подходов — сколько?",
    ],
    "дом": [
        "{name} помогает маме готовить. Нужно {count1} картошки, а лука — в {times} раз меньше. Сколько лука?",
        "В комнате {name} {count1} книг, а в комнате {name2} — на {count2} больше. Сколько у {name2}?",
        "Бабушка испекла {count} пирогов. Съели {eaten}. Сколько осталось?",
    ],
}


def adapt_file(filepath):
    """Адаптирует один JSON файл"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Заменяем в теории
    if 'theory' in data:
        data['theory'] = replace_context(data['theory'])
    
    if 'theory_cpa' in data:
        for key in data['theory_cpa']:
            data['theory_cpa'][key] = replace_context(data['theory_cpa'][key])
    
    # Заменяем в упражнениях
    if 'exercises' in data:
        for ex in data['exercises']:
            if 'question' in ex:
                ex['question'] = replace_context(ex['question'])
    
    # Заменяем в задачах
    if 'problems' in data:
        for prob in data['problems']:
            if 'question' in prob:
                prob['question'] = replace_context(prob['question'])
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ {filepath.name}")


def replace_context(text):
    """Заменяет контекст на российский"""
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def main():
    files = sorted(CURRICULUM_DIR.glob("grade_7_topic_*.json")) + \
            sorted(CURRICULUM_DIR.glob("grade_8_topic_*.json")) + \
            sorted(CURRICULUM_DIR.glob("grade_9_topic_*.json"))
    
    print(f"Адаптация {len(files)} файлов...")
    for filepath in files:
        adapt_file(filepath)
    
    print("\nГотово! Все файлы адаптированы под российского школьника.")


if __name__ == "__main__":
    main()
