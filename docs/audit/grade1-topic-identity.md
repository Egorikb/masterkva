# D1 — карта идентификаторов 1 класса

Дата: 2026-09-10. Исходный commit: `e53d18c1d10519aae218c044ab6898253b104e0b`. Статус: **кандидат для проверки Sol перед B1**.

## Итог

- Учтены 26 canonical topics и 78 `lesson_id`; каждый урок присутствует ровно один раз.
- Найдены 7 диагностических `topic_id`, 6 grade-1 `skill_id` и 6 уникальных `item_family`.
- Контентно подтверждены **9** строк; **23** требуют проверки; **46** не имеют безопасной grade-1 runtime-связи.
- Карта не меняет уроки, runtime и пользовательское состояние. `backend/data/user_states.json` не читался и не изменялся.

## Главный вывод

Суффиксы чисел не являются связью. Canonical topic 2 — пространственные позиции, а runtime `g1_t02` — следующее число. Canonical topic 3 — числа до 5, а runtime `g1_t03` фактически содержит сложение с переходом через 10. Поэтому автоматическое соединение по номеру небезопасно.

## Карта по 26 темам

| Canonical | Уроки | Подтверждено | Review | Unmapped | Runtime-кандидаты |
|---:|---|---:|---:|---:|---|
| 1 — Подготовка | g1-t01-l01, g1-t01-l02, g1-t01-l03 | 1 | 2 | 0 | g1_t01 → g1_counting_core → counting_with_objects |
| 2 — Позиции | g1-t02-l01, g1-t02-l02, g1-t02-l03 | 0 | 0 | 3 | — |
| 3 — Числа до 5 | g1-t03-l01, g1-t03-l02, g1-t03-l03 | 1 | 2 | 0 | g1_t05 → g1_number_bond → number_bond_missing_part |
| 4 — Сложение и вычитание до 5 | g1-t04-l01, g1-t04-l02, g1-t04-l03 | 0 | 3 | 0 | g1_t05 → g1_number_bond → number_bond_missing_part |
| 5 — Объёмные тела | g1-t05-l01, g1-t05-l02, g1-t05-l03 | 0 | 0 | 3 | — |
| 6 — Числа 6-7 | g1-t06-l01, g1-t06-l02, g1-t06-l03 | 0 | 3 | 0 | g1_t05 → g1_number_bond → number_bond_missing_part<br>g1_t03 → g1_addition_within_10 → addition_within_10_part_whole<br>g1_t02 → g1_number_successor → number_successor |
| 7 — Числа 8-9 | g1-t07-l01, g1-t07-l02, g1-t07-l03 | 0 | 3 | 0 | g1_t05 → g1_number_bond → number_bond_missing_part<br>g1_t03 → g1_addition_within_10 → addition_within_10_part_whole<br>g1_t02 → g1_number_successor → number_successor |
| 8 — Число 10 | g1-t08-l01, g1-t08-l02, g1-t08-l03 | 0 | 2 | 1 | g1_t06 → g1_compose_decompose_10 → compose_decompose_10 |
| 9 — Смешанные задачи до 10 | g1-t09-l01, g1-t09-l02, g1-t09-l03 | 1 | 2 | 0 | g1_t03 → g1_addition_within_10 → addition_within_10_part_whole<br>g1_t04 → g1_subtraction_within_10 → subtraction_within_10_part_whole |
| 10 — Числа 11-20 | g1-t10-l01, g1-t10-l02, g1-t10-l03 | 0 | 0 | 3 | — |
| 11 — Часы | g1-t11-l01, g1-t11-l02, g1-t11-l03 | 0 | 0 | 3 | — |
| 12 — Сложение с переходом через 10 | g1-t12-l01, g1-t12-l02, g1-t12-l03 | 3 | 0 | 0 | g1_t07 → g1_compose_decompose_10 → addition_within_10_part_whole |
| 13 — Сложение в пределах 20: закрепление | g1-t13-l01, g1-t13-l02, g1-t13-l03 | 3 | 0 | 0 | g1_t07 → g1_compose_decompose_10 → addition_within_10_part_whole |
| 14 — Повторение 1 семестра | g1-t14-l01, g1-t14-l02, g1-t14-l03 | 0 | 3 | 0 | g1_t05 → g1_number_bond → number_bond_missing_part<br>g1_t02 → g1_number_successor → number_successor<br>g1_t04 → g1_subtraction_within_10 → subtraction_within_10_part_whole<br>g1_t03 → g1_addition_within_10 → addition_within_10_part_whole |
| 15 — Фигуры (плоские) | g1-t15-l01, g1-t15-l02, g1-t15-l03 | 0 | 0 | 3 | — |
| 16 — Вычитание через 10 | g1-t16-l01, g1-t16-l02, g1-t16-l03 | 0 | 0 | 3 | — |
| 17 — Вычитание в пределах 20: закрепление | g1-t17-l01, g1-t17-l02, g1-t17-l03 | 0 | 0 | 3 | — |
| 18 — Классификация | g1-t18-l01, g1-t18-l02, g1-t18-l03 | 0 | 0 | 3 | — |
| 19 — Числа до 100 | g1-t19-l01, g1-t19-l02, g1-t19-l03 | 0 | 0 | 3 | — |
| 20 — Сложение до 100 (без перехода) | g1-t20-l01, g1-t20-l02, g1-t20-l03 | 0 | 3 | 0 | g1_t06 → g1_compose_decompose_10 → compose_decompose_10 |
| 21 — Деньги (рубли) | g1-t21-l01, g1-t21-l02, g1-t21-l03 | 0 | 0 | 3 | — |
| 22 — Вычитание до 100 (без перехода) | g1-t22-l01, g1-t22-l02, g1-t22-l03 | 0 | 0 | 3 | — |
| 23 — Сложение до 100 (с переходом) | g1-t23-l01, g1-t23-l02, g1-t23-l03 | 0 | 0 | 3 | — |
| 24 — Вычитание до 100 (с переходом) | g1-t24-l01, g1-t24-l02, g1-t24-l03 | 0 | 0 | 3 | — |
| 25 — Закономерности | g1-t25-l01, g1-t25-l02, g1-t25-l03 | 0 | 0 | 3 | — |
| 26 — Повторение 2 семестра | g1-t26-l01, g1-t26-l02, g1-t26-l03 | 0 | 0 | 3 | — |

## Проверенные расхождения пространств идентификаторов

1. `curriculum_detailed/` — отдельная legacy-таксономия из восьми файлов. Её номера нельзя приравнивать к canonical v2: detailed topic 4 «ФИГУРЫ» соответствует canonical topic 15, а не 4; detailed topic 5 объединяет canonical 6–9; detailed topic 7 разделён на canonical 12–13.
2. Файлы `grade_1_topic_9.json`…`grade_1_topic_26.json` отсутствуют в исследованном commit. Это отсутствие legacy-detail, а не отсутствие canonical тем или уроков.
3. В registry только шесть навыков первого класса. `g1_compose_decompose_10` одновременно владеет runtime topic `g1_t06` («сложение до 100 без перехода») и `g1_t07` («сложение с переходом через 10»).
4. `g1_t03` и `g1_t07` используют один `item_family` и фактически дублируют набор примеров с переходом через 10, хотя относятся к разным skill.
5. Название skill `g1_addition_within_10` противоречит его диагностическим примерам `8+5`, `9+3`, `7+6` с ответами больше 10.
6. `SkillResolver.resolve(..., lesson_id=...)` не умеет разрешать lesson_id: индекс строится только по skill_id, diagnostic topic_id и topic_names. Без этой карты один lesson_id приводит к `fallback_used`.
7. `DiagnosticEngine.get_questions_for_grade` не переносит исходный `item_family` в нормализованный вопрос. Практика восстанавливает family из отдельного статического словаря или по topic id, что усиливает риск рассинхронизации.

## Подтверждённые строки (`mapped`)

- `g1-t01-l01` → `g1_t01` → `g1_counting_core` → `counting_with_objects`: Пересчёт реальных предметов напрямую совпадает со счётом объектов.
- `g1-t03-l01` → `g1_t05` → `g1_number_bond` → `number_bond_missing_part`: Пропущенные части состава 5 совпадают с number_bond_missing_part; ноль остаётся дополнительным содержанием урока.
- `g1-t09-l02` → `g1_t04` → `g1_subtraction_within_10` → `subtraction_within_10_part_whole`: Вычитание 8−2 находится в пределах 10 и совпадает с семейством subtraction_within_10_part_whole.
- `g1-t12-l01` → `g1_t07` → `g1_compose_decompose_10` → `addition_within_10_part_whole`: 8+5 буквально присутствует в диагностическом g1_t07; стратегия — переход через 10.
- `g1-t12-l02` → `g1_t07` → `g1_compose_decompose_10` → `addition_within_10_part_whole`: 7+6 и 9+5 буквально присутствуют в g1_t07; весь урок про переход через 10.
- `g1-t12-l03` → `g1_t07` → `g1_compose_decompose_10` → `addition_within_10_part_whole`: Объяснение 9+6 проверяет ту же стратегию дополнения до 10; item_family совпадает по смыслу.
- `g1-t13-l01` → `g1_t07` → `g1_compose_decompose_10` → `addition_within_10_part_whole`: 6+8 требует перехода через 10 и соответствует диагностической теме g1_t07.
- `g1-t13-l02` → `g1_t07` → `g1_compose_decompose_10` → `addition_within_10_part_whole`: 8+7 буквально присутствует в g1_t07; другие примеры также переходят через 10.
- `g1-t13-l03` → `g1_t07` → `g1_compose_decompose_10` → `addition_within_10_part_whole`: Оба способа 7+8 используют дополнение до 10; это содержание g1_t07.

## Спорные строки (`review_required`)

- `g1-t01-l02`: Сравнение количеств связано со счётом, но диагностическая семья проверяет сумму двух чисел, а не сравнение. Кандидат: `g1_t01`/`g1_counting_core`/`counting_with_objects`.
- `g1-t01-l03`: Количество связано со счётом, но порядковое место диагностикой g1_t01 не покрывается. Кандидат: `g1_t01`/`g1_counting_core`/`counting_with_objects`.
- `g1-t03-l02`: Обычное сложение до 5 относится к skill g1_number_bond, но не имеет пропущенной части, которую проверяет item_family. Кандидат: `g1_t05`/`g1_number_bond`/`number_bond_missing_part`.
- `g1-t03-l03`: Вычитание до 5 относится к теме skill, но диагностическая семья сформулирована только как пропущенная часть суммы. Кандидат: `g1_t05`/`g1_number_bond`/`number_bond_missing_part`.
- `g1-t04-l01`: Сложение до 5 совпадает с названием runtime-темы, но формат не совпадает с number_bond_missing_part. Кандидат: `g1_t05`/`g1_number_bond`/`number_bond_missing_part`.
- `g1-t04-l02`: Урок сравнивает результаты сложения и вычитания; runtime-семья проверяет только одну пропущенную часть. Кандидат: `g1_t05`/`g1_number_bond`/`number_bond_missing_part`.
- `g1-t04-l03`: Диапазон до 5 совпадает, но урок содержит набор прямых действий, а не один number bond. Кандидат: `g1_t05`/`g1_number_bond`/`number_bond_missing_part`.
- `g1-t06-l01`: Состав 6 близок числовым связкам, но runtime g1_t05 назван «до 5» и один его вопрос уже выходит до 6. Кандидат: `g1_t05`/`g1_number_bond`/`number_bond_missing_part`.
- `g1-t06-l02`: Сложение 4+3 не переходит через 10, тогда как все диагностические g1_t03 переходят через 10. Кандидат: `g1_t03`/`g1_addition_within_10`/`addition_within_10_part_whole`.
- `g1-t06-l03`: Соседство 6 и 7 связано со следующим числом, но урок также требует сравнения и разности. Кандидат: `g1_t02`/`g1_number_successor`/`number_successor`.
- `g1-t07-l01`: Состав 8 близок числовым связкам, но runtime g1_t05 заявлен для действий до 5. Кандидат: `g1_t05`/`g1_number_bond`/`number_bond_missing_part`.
- `g1-t07-l02`: Сложение 6+2 не переходит через 10, а диагностический g1_t03 проверяет суммы 11–15. Кандидат: `g1_t03`/`g1_addition_within_10`/`addition_within_10_part_whole`.
- `g1-t07-l03`: Порядок 8 и 9 близок successor, но урок спрашивает раньше/позже, а не только следующее число. Кандидат: `g1_t02`/`g1_number_successor`/`number_successor`.
- `g1-t08-l01`: Дополнение 7 до 10 совпадает с названием skill «Состав десятка», но диагностика g1_t06 фактически складывает десятки до 100. Кандидат: `g1_t06`/`g1_compose_decompose_10`/`compose_decompose_10`.
- `g1-t08-l02`: Состав 10 совпадает с названием skill, но не с фактическими вопросами diagnostic g1_t06. Кандидат: `g1_t06`/`g1_compose_decompose_10`/`compose_decompose_10`.
- `g1-t09-l01`: Задача 4+3 — сложение до 10 без перехода; g1_t03 фактически проверяет переход через 10. Кандидат: `g1_t03`/`g1_addition_within_10`/`addition_within_10_part_whole`.
- `g1-t09-l03`: Урок объединяет несколько разных runtime-смыслов; один идентификатор исказит оценку. Кандидаты: `g1_t03`/`g1_addition_within_10`, `g1_t04`/`g1_subtraction_within_10`.
- `g1-t14-l01`: Урок объединяет несколько разных runtime-смыслов; один идентификатор исказит оценку. Кандидаты: `g1_t02`/`g1_number_successor`, `g1_t04`/`g1_subtraction_within_10`.
- `g1-t14-l02`: Сложение 3+2 относится к действиям до 5, но урок дополнительно требует проверку обратным действием. Кандидат: `g1_t05`/`g1_number_bond`/`number_bond_missing_part`.
- `g1-t14-l03`: Урок объединяет несколько разных runtime-смыслов; один идентификатор исказит оценку. Кандидаты: `g1_t03`/`g1_addition_within_10`, `g1_t04`/`g1_subtraction_within_10`, `g1_t05`/`g1_number_bond`.
- `g1-t20-l01`: Сложение без перехода совпадает с названием g1_t06, но диагностика проверяет только круглые десятки, а урок — 24+35. Кандидат: `g1_t06`/`g1_compose_decompose_10`/`compose_decompose_10`.
- `g1-t20-l02`: Сложение двузначных без перехода шире диагностических примеров с одними десятками. Кандидат: `g1_t06`/`g1_compose_decompose_10`/`compose_decompose_10`.
- `g1-t20-l03`: 20+13 — сложение без перехода, но диагностическое покрытие g1_t06 ограничено круглыми десятками. Кандидат: `g1_t06`/`g1_compose_decompose_10`/`compose_decompose_10`.

## Непокрытые строки (`unmapped`)

- Topic 2 — Позиции: `g1-t02-l01`, `g1-t02-l02`, `g1-t02-l03`. Пространственные позиции отсутствуют среди grade-1 diagnostic topics и skills.
- Topic 5 — Объёмные тела: `g1-t05-l01`, `g1-t05-l02`, `g1-t05-l03`. Объёмные тела отсутствуют среди grade-1 diagnostic topics и skills.
- Topic 8 — Число 10: `g1-t08-l03`. Прямой и обратный счёт до 10 не совпадает с successor и не покрывается другим grade-1 runtime skill.
- Topic 10 — Числа 11-20: `g1-t10-l01`, `g1-t10-l02`, `g1-t10-l03`. Разрядный состав и запись чисел 11–20 отсутствуют среди grade-1 runtime skills.
- Topic 11 — Часы: `g1-t11-l01`, `g1-t11-l02`, `g1-t11-l03`. Чтение целых часов отсутствует среди grade-1 runtime skills; skill времени существует только для grade 3 и иной темы.
- Topic 15 — Фигуры (плоские): `g1-t15-l01`, `g1-t15-l02`, `g1-t15-l03`. Плоские фигуры отсутствуют среди grade-1 runtime skills; geometry_2d зарегистрирован для grade 3.
- Topic 16 — Вычитание через 10: `g1-t16-l01`, `g1-t16-l02`, `g1-t16-l03`. Вычитание через 10 в пределах 20 не покрывается g1_t04, чьи вопросы ограничены 10.
- Topic 17 — Вычитание в пределах 20: закрепление: `g1-t17-l01`, `g1-t17-l02`, `g1-t17-l03`. Закрепление вычитания в пределах 20 и обратная проверка не имеют grade-1 runtime skill.
- Topic 18 — Классификация: `g1-t18-l01`, `g1-t18-l02`, `g1-t18-l03`. Классификация по признаку отсутствует среди grade-1 runtime skills.
- Topic 19 — Числа до 100: `g1-t19-l01`, `g1-t19-l02`, `g1-t19-l03`. Разряды и чтение чисел до 100 отсутствуют среди grade-1 runtime skills.
- Topic 21 — Деньги (рубли): `g1-t21-l01`, `g1-t21-l02`, `g1-t21-l03`. Деньги и стоимость отсутствуют среди grade-1 runtime skills.
- Topic 22 — Вычитание до 100 (без перехода): `g1-t22-l01`, `g1-t22-l02`, `g1-t22-l03`. Вычитание двузначных без перехода отсутствует среди grade-1 runtime skills.
- Topic 23 — Сложение до 100 (с переходом): `g1-t23-l01`, `g1-t23-l02`, `g1-t23-l03`. Сложение двузначных с переходом шире g1_t07 (пределы 20); grade-1 skill разрядного переноса отсутствует.
- Topic 24 — Вычитание до 100 (с переходом): `g1-t24-l01`, `g1-t24-l02`, `g1-t24-l03`. Вычитание двузначных с переходом отсутствует среди grade-1 runtime skills.
- Topic 25 — Закономерности: `g1-t25-l01`, `g1-t25-l02`, `g1-t25-l03`. Закономерности отсутствуют среди grade-1 runtime skills.
- Topic 26 — Повторение 2 семестра: `g1-t26-l01`, `g1-t26-l02`, `g1-t26-l03`. Итоговый смешанный урок нельзя однозначно связать с одним grade-1 runtime skill.

## Legacy `curriculum_detailed` по содержанию

| Detailed | Соответствие canonical v2 | Статус |
|---|---|---|
| 1 — ПОДГОТОВКА | 1 | partial_match |
| 2 — ПОЗИЦИИ | 2 | content_match |
| 3 — СЛОЖЕНИЕ/ВЫЧИТАНИЕ ДО 5 | 3, 4 | split_in_reference_v2 |
| 4 — ФИГУРЫ | 15 | renumbered_by_content |
| 5 — СЛОЖЕНИЕ/ВЫЧИТАНИЕ ДО 10 | 6, 7, 8, 9 | split_in_reference_v2 |
| 6 — ЧАСЫ | 11 | partial_match |
| 7 — СЛОЖЕНИЕ С ПЕРЕХОДОМ | 12, 13 | split_in_reference_v2 |
| 8 — ПОВТОРЕНИЕ | 14 | content_match |

## Проверка

```bash
python3 backend/scripts/validate_grade1_topic_identity.py
git diff --check
```

Валидатор проверяет 26 тем, 78 уникальных уроков, ровно одну строку на урок, совпадение `content_version`, существование diagnostic topic/skill/contract/family и запрещает включать `backend/data/user_states.json` в Git diff.

## Ограничения и решение для B1

- B1 можно начинать только с девяти `mapped` строк; 23 строки требуют решения Sol, 46 нуждаются в новых grade-1 runtime contracts либо остаются вне маршрута.
- `review_required` не должен автоматически выбирать упражнение или повышать mastery.
- Карта — кандидат, а не миграция состояния и не разрешение перепривязать исторические попытки.
