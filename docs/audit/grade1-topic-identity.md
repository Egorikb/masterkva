# D1 — техническая и смысловая приёмка карты 1 класса

Дата: 2026-09-10. Исходный проверенный HEAD: `23b44e7df7f93f910274beaed3dee5b163816692`. Техническую проверку выполнил основной агент в полной копии `ACTIVE`; независимую смысловую проверку всех 32 строк — GPT-5.6 Sol.

**Статус:** приёмка D1 завершена, разработку узкого B1 можно начинать с `g1-t12-l01` версии `2.0`. Реализация B1 и автоматическое повышение mastery ещё не включены. Карта охватывает 26 тем / 78 уроков / 7 diagnostic topics / 6 grade-1 skills; `mapped` подтверждает смысл связи, а не освоение навыка ребёнком.

## Итог

Среди 32 рассмотренных строк: **9 `mapped`, 10 `review_required`, 13 `unmapped`**. Решения перенесены в JSON; исходные 46 `unmapped` сохранены без изменения. Итог всей карты: **9 / 10 / 59**.

Из исходных девяти `mapped` подтверждены семь: `g1-t09-l02`, все три урока темы 12 и все три урока темы 13. `g1-t01-l01` понижен до `unmapped`, потому что реальная диагностика и практика складывают два заданных числа и не проверяют пересчёт наблюдаемых предметов. `g1-t03-l01` понижен до `review_required`, потому что только две из трёх частей являются `number_bond_missing_part`, а первая отдельно проверяет вычитание до нуля.

Из исходных 23 `review_required` подтверждены две новые связи:

- `g1-t03-l03` → `g1_t04` → `g1_subtraction_within_10` → `subtraction_within_10_part_whole`;
- `g1-t07-l03` → `g1_t02` → `g1_number_successor` → `number_successor`.

В таблице `review_required` означает: содержательно близкая часть существует, но одна тройка не покрывает весь урок либо текущий diagnostic/practice contract внутренне противоречив; строка должна быть закрыта для автоматического выбора и mastery до разделения урока или исправления контракта. `unmapped` означает отсутствие целостной действующей тройки.

## Карта по 26 темам после Sol

| Тема | Mapped | Review | Unmapped | Текущие runtime topics / кандидаты |
|---|---:|---:|---:|---|
| 1 — Подготовка | 0 | 0 | 3 | — |
| 2 — Позиции | 0 | 0 | 3 | — |
| 3 — Числа до 5 | 1 | 1 | 1 | g1_t05, g1_t04 |
| 4 — Сложение и вычитание до 5 | 0 | 2 | 1 | g1_t05 |
| 5 — Объёмные тела | 0 | 0 | 3 | — |
| 6 — Числа 6-7 | 0 | 2 | 1 | g1_t05, g1_t02 |
| 7 — Числа 8-9 | 1 | 1 | 1 | g1_t05, g1_t02 |
| 8 — Число 10 | 0 | 0 | 3 | — |
| 9 — Смешанные задачи до 10 | 1 | 1 | 1 | g1_t04, g1_t03 |
| 10 — Числа 11-20 | 0 | 0 | 3 | — |
| 11 — Часы | 0 | 0 | 3 | — |
| 12 — Сложение с переходом через 10 | 3 | 0 | 0 | g1_t07 |
| 13 — Сложение в пределах 20: закрепление | 3 | 0 | 0 | g1_t07 |
| 14 — Повторение 1 семестра | 0 | 3 | 0 | g1_t02, g1_t04, g1_t05, g1_t03 |
| 15 — Фигуры (плоские) | 0 | 0 | 3 | — |
| 16 — Вычитание через 10 | 0 | 0 | 3 | — |
| 17 — Вычитание в пределах 20: закрепление | 0 | 0 | 3 | — |
| 18 — Классификация | 0 | 0 | 3 | — |
| 19 — Числа до 100 | 0 | 0 | 3 | — |
| 20 — Сложение до 100 (без перехода) | 0 | 0 | 3 | — |
| 21 — Деньги (рубли) | 0 | 0 | 3 | — |
| 22 — Вычитание до 100 (без перехода) | 0 | 0 | 3 | — |
| 23 — Сложение до 100 (с переходом) | 0 | 0 | 3 | — |
| 24 — Вычитание до 100 (с переходом) | 0 | 0 | 3 | — |
| 25 — Закономерности | 0 | 0 | 3 | — |
| 26 — Повторение 2 семестра | 0 | 0 | 3 | — |

## Решения по 32 строкам

Общие runtime-доказательства: реальные вопросы grade 1 начинаются в [`diagnostic_pool.json`](../../backend/data/diagnostic_pool.json#L5); шесть навыков — в [`skill_registry.json`](../../backend/data/skill_registry.json#L6); их контракты — в [`skill_contracts.json`](../../backend/data/skill_contracts.json#L5); статические упражнения и таблица family — в [`practice_engine.py`](../../backend/deeptutor/services/practice_engine.py#L13).

| Урок | Решение | Тройка при `mapped` | Предметная причина и доказательство |
|---|---|---|---|
| [`g1-t01-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L53) | `unmapped` | — | Урок проверяет физический пересчёт до 5 по одному предмету. `g1_t01` фактически спрашивает сумму двух уже заданных чисел, а практика делает то же; название `counting_with_objects` не компенсирует смену действия. |
| [`g1-t01-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L129) | `unmapped` | — | Сравнение 3 и 5 и разностное сравнение `5−3`; `g1_t01/g1_counting_core/counting_with_objects` не проверяет ни знак сравнения, ни «на сколько». |
| [`g1-t01-l03`](../../backend/data/lessons/grade_1_ru_adapted.json#L208) | `unmapped` | — | Две цели: количественный и порядковый счёт. В grade-1 runtime нет ordinal family; `g1_t01` проверяет сумму, не место в ряду. |
| [`g1-t03-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L572) | `review_required` | — | Две части `5=2+□`, `5=0+□` совпадают с `g1_t05/g1_number_bond/number_bond_missing_part`, но первая часть `3−3=0` проверяет иной результат. Одна тройка не представляет весь ordered assessment. |
| [`g1-t03-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L647) | `unmapped` | — | Прямая сумма `2+2` до 5 не является missing part. Альтернатива `g1_t03` тоже не годится: его диагностика состоит из сумм с переходом через 10 ([`g1_t03_q01`](../../backend/data/diagnostic_pool.json#L185)). |
| [`g1-t03-l03`](../../backend/data/lessons/grade_1_ru_adapted.json#L717) | `mapped` | `g1_t04` / `g1_subtraction_within_10` / `subtraction_within_10_part_whole` | Задача `4−1=3` — однозначное уменьшение в диапазоне до 10; diagnostic и practice `g1_t04` проверяют то же действие и диапазон ([`g1_t04_q01`](../../backend/data/diagnostic_pool.json#L263)). |
| [`g1-t04-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L821) | `unmapped` | — | `3+1` — прямая сумма без перехода. `g1_t05` проверяет missing part, а `g1_t03` диагностирует переход через 10, хотя его статическая практика противоречиво выдаёт суммы без перехода. Целостной тройки нет. |
| [`g1-t04-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L902) | `review_required` | — | Ordered assessment объединяет сложение, вычитание и сравнение результатов. Нужны как минимум две arithmetic family и отдельное сравнение; один `number_bond_missing_part` и один skill искажают урок. |
| [`g1-t04-l03`](../../backend/data/lessons/grade_1_ru_adapted.json#L1004) | `review_required` | — | Четыре прямых действия чередуют сложение и вычитание. Их можно сопоставлять только по частям после разделения; `g1_t05/number_bond_missing_part` не соответствует форме заданий. |
| [`g1-t06-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L1359) | `review_required` | — | Состав 6 тематически близок number bond и одно диагностическое задание действительно доходит до 6, но урок требует два наблюдаемых разбиения на непустые группы, а family проверяет одну пропущенную часть числового равенства. Нужен отдельный rubric/family либо разбиение. |
| [`g1-t06-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L1430) | `unmapped` | — | `4+3=7` — сложение без перехода; все diagnostic items `g1_t03` переходят через 10. Совпадение со статическим practice при противоположной диагностике не образует надёжного контракта. |
| [`g1-t06-l03`](../../backend/data/lessons/grade_1_ru_adapted.json#L1503) | `review_required` | — | Урок использует соседство 6→7, но оценивает и большее число, и разность `7−6`. `number_successor` покрывает лишь основание рассуждения, не полный ordered assessment. |
| [`g1-t07-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L1610) | `review_required` | — | Состав 8 связан с number bond, но требует двух физических разбиений. Diagnostic `g1_t05` проверяет одну пропущенную часть и фактически ограничен целыми 3–6; покрытие диапазона 8 и rubric отсутствует. |
| [`g1-t07-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L1681) | `unmapped` | — | `6+2=8` не переходит через 10. Diagnostic `g1_t03` проверяет только суммы 11–15, поэтому topic и диапазон кандидата не совпадают с уроком. |
| [`g1-t07-l03`](../../backend/data/lessons/grade_1_ru_adapted.json#L1753) | `mapped` | `g1_t02` / `g1_number_successor` / `number_successor` | Оба вопроса фиксируют одну и ту же смежную пару 8→9: 8 раньше, 9 позже. Runtime `g1_t02` прямо содержит «какое число идёт после 8?» ([`practice_engine.py`](../../backend/deeptutor/services/practice_engine.py#L18)). |
| [`g1-t08-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L1861) | `unmapped` | — | Дополнение 7 до 10 является составом числа 10, но фактический `g1_t06` складывает круглые десятки до 100 ([`g1_t06_q01`](../../backend/data/diagnostic_pool.json#L443)). `compose_decompose_10` здесь имеет иное реальное значение. |
| [`g1-t08-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L1944) | `unmapped` | — | Три missing-part равенства с целым 10 не покрываются ни `g1_t06` с круглыми десятками, ни `g1_t05` с фактическим диапазоном до 6. Название skill «Состав десятка» недостаточно. |
| [`g1-t09-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L2117) | `unmapped` | — | Сюжетная сумма `4+3=7` без перехода. `g1_t03` диагностирует переход через 10; отдельного согласованного grade-1 topic для сложения без перехода нет. |
| [`g1-t09-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L2185) | `mapped` | `g1_t04` / `g1_subtraction_within_10` / `subtraction_within_10_part_whole` | Однозначная задача на уменьшение `8−2=6` в диапазоне до 10; topic, skill, family, diagnostic и practice согласованы по действию и диапазону. |
| [`g1-t09-l03`](../../backend/data/lessons/grade_1_ru_adapted.json#L2262) | `review_required` | — | Один урок объединяет `5+1` и `9−4`. Вычитание имеет рабочую тройку `g1_t04`, сложение без перехода — нет; одной тройкой урок описать нельзя. |
| [`g1-t12-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L2884) | `mapped` | `g1_t07` / `g1_compose_decompose_10` / `addition_within_10_part_whole` | Урок и решение — `8+5`, разложение 5 на 2 и 3, дополнение 8 до 10. `g1_t07_q01` задаёт ровно `8+5=13` ([диагностика](../../backend/data/diagnostic_pool.json#L545)); контракт skill включает это family ([контракт](../../backend/data/skill_contracts.json#L395)). |
| [`g1-t12-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L2974) | `mapped` | `g1_t07` / `g1_compose_decompose_10` / `addition_within_10_part_whole` | Все три суммы переходят через 10; `7+6` и `9+5` буквально присутствуют в `g1_t07`, а `5+7` имеет тот же диапазон и стратегию. |
| [`g1-t12-l03`](../../backend/data/lessons/grade_1_ru_adapted.json#L3035) | `mapped` | `g1_t07` / `g1_compose_decompose_10` / `addition_within_10_part_whole` | Рубрика требует именно разложение 6 на 1+5 и переход `9+1=10`, `10+5=15`. Это тот же предметный паттерн carry-addition. Статус не делает rubric автоматически оцениваемой и не разрешает mastery. |
| [`g1-t13-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L3139) | `mapped` | `g1_t07` / `g1_compose_decompose_10` / `addition_within_10_part_whole` | `6+8=14` находится в том же диапазоне 11–17 и требует дополнения до 10; topic и family совпадают по действию и стратегии. |
| [`g1-t13-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L3230) | `mapped` | `g1_t07` / `g1_compose_decompose_10` / `addition_within_10_part_whole` | Все три суммы — однозначное сложение с переходом в пределах 20; `8+7` буквально есть в diagnostic `g1_t07`, остальные сохраняют тот же паттерн. |
| [`g1-t13-l03`](../../backend/data/lessons/grade_1_ru_adapted.json#L3293) | `mapped` | `g1_t07` / `g1_compose_decompose_10` / `addition_within_10_part_whole` | Оба требуемых способа для `7+8` — дополнение одного слагаемого до 10; число и стратегия лежат в точном runtime topic. Рубрика остаётся только наблюдаемым lesson assessment. |
| [`g1-t14-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L3408) | `review_required` | — | Ordered assessment объединяет predecessor 10, successor 10 и `5−5=0`. `number_successor` покрывает только одну часть, а single-family mapping исказит повторение. |
| [`g1-t14-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L3472) | `review_required` | — | Цель — не только `3+2=5`, а обязательная проверка пересчётом или обратным `5−2=3`. Ни `number_bond_missing_part`, ни numeric addition family не оценивают способ проверки; нужен rubric/composite contract. |
| [`g1-t14-l03`](../../backend/data/lessons/grade_1_ru_adapted.json#L3559) | `review_required` | — | Три части принадлежат разным семействам: сложение без перехода, вычитание до 10, сложение с переходом. Допустима только part-level карта после разделения. |
| [`g1-t20-l01`](../../backend/data/lessons/grade_1_ru_adapted.json#L4944) | `unmapped` | — | `24+35` требует сложения десятков и единиц. `g1_t06/compose_decompose_10` проверяет лишь суммы круглых десятков, поэтому не покрывает единицы и полный алгоритм. |
| [`g1-t20-l02`](../../backend/data/lessons/grade_1_ru_adapted.json#L5034) | `unmapped` | — | Все три примера складывают двузначные числа по двум разрядам; диагностические и practice items `g1_t06` содержат только круглые десятки. Диапазон ответа до 79 не доказывает совпадение skill. |
| [`g1-t20-l03`](../../backend/data/lessons/grade_1_ru_adapted.json#L5102) | `unmapped` | — | `20+13` включает три единицы и понимание двузначного числа; runtime `g1_t06` не проверяет ненулевые единицы. Совпадает лишь общий заголовок «без перехода». |

## Общие дефекты контрактов

1. `lesson_runtime_map.json` не загружается приложением: поиск его имени в `backend/deeptutor`, `backend/main.py` и тестах не находит потребителя. `SkillResolver` индексирует skill, runtime topic и topic name, но не lesson ID; переданный `lesson_id` ищется в индексе, где таких ключей нет ([`skill_runtime.py`](../../backend/deeptutor/services/skill_runtime.py#L59), [`resolve`](../../backend/deeptutor/services/skill_runtime.py#L113)).
2. Запрет для `unmapped` не реализован на уровне сервиса. Чистый прямой вызов `PracticeEngine.create_practice({"topic_id":"g1-t02-l01","lesson_id":"g1-t02-l01","status":"unmapped"})` вернул `9+5`, family `addition_within_10_part_whole`, `fallback_warning=null`. Причина: неизвестный topic доходит до общего генератора, а пустой family подменяется сложением ([`practice_engine.py`](../../backend/deeptutor/services/practice_engine.py#L250), [`fallback`](../../backend/deeptutor/services/practice_engine.py#L294)). Это доказывает отсутствие fail-closed контракта в `PracticeEngine`, но само по себе не доказывает доступность такого входа через HTTP или фактическое повышение mastery. Исходные 46 `unmapped` пока не имеют исполняемой гарантии исключения из automatic selection и mastery.
3. Выбор из diagnostic pool использует условие `topic_id OR item_family` ([`practice_engine.py`](../../backend/deeptutor/services/practice_engine.py#L128)). Для пилотных `g1_t07` + `addition_within_10_part_whole` variant 0 реально выбирается `g1_t03_q01`, потому что эта family общая для двух topics. Даже когда текст совпал (`8+5`), source topic identity уже потерян.
4. `DiagnosticEngine.get_questions_for_grade` не переносит исходный `item_family` в нормализованный вопрос ([`diagnostic_engine.py`](../../backend/deeptutor/services/diagnostic_engine.py#L180)). Дальше family восстанавливается отдельным словарём, который может расходиться с данными.
5. `g1_t03` внутренне противоречив: диагностика проверяет только переход через 10, skill называется «Сложение до 10», а статическая практика выдаёт `4+3` и `2+5` без перехода. `g1_t05` также противоречив: family называется `number_bond_missing_part`, но статическая практика даёт прямые `2+1` и `1+2`.
6. `g1_compose_decompose_10` одновременно владеет несвязанными `g1_t06` (сложение круглых десятков) и `g1_t07` (переход через 10), а его контракт включает две разные family ([реестр](../../backend/data/skill_registry.json#L105), [контракт](../../backend/data/skill_contracts.json#L395)). Mastery history хранится только по `skill_id` ([`plugins_api.py`](../../backend/deeptutor/api/routers/plugins_api.py#L245)), поэтому успешные попытки одного topic/family могут открыть весь объединённый skill.
7. `mode=shadow` и `coverage.status=partial` являются метаданными, а не запретом: текущий practice/mastery path всё равно разрешает skill и оценивает его. Уроки отдельно заявляют `mastery_policy=do_not_infer_from_one_lesson`; их семантический `mapped` не отменяет этот запрет.

## Проверенный пилот

`g1-t12-l01`, v2.0, `8+5` **семантически подтверждён** как `g1_t07` → `g1_compose_decompose_10` → `addition_within_10_part_whole`. Совпадают точное выражение, ответ 13, диапазон до 20 и предметная стратегия дополнения до 10. Это наиболее сильная цепочка первого полугодия.

Подтверждение связи не разрешает текущему runtime автоматически выбирать вопросы или повышать mastery. Для B1 пилот допустим только после fail-closed подключения карты, точного выбора `topic_id AND item_family` и изоляции mastery evidence от `g1_t06/compose_decompose_10`. Дополнительная содержательно согласованная цепочка — `g1-t09-l02` → `g1_t04` → `g1_subtraction_within_10` → `subtraction_within_10_part_whole`; у неё согласованы diagnostic, static practice и skill, но её lesson assessment также содержит `do_not_infer_from_one_lesson`.

## Условия включения B1 и дальнейшего runtime-покрытия

Для реализации и включения пилота B1:

- загружать само задание из `grade_1_ru_adapted.json` по точным `lesson_id` и `content_version`; diagnostic topic и family служат связью с runtime, а не источником случайной замены урока;
- загрузить карту как обязательный allowlist по точным `lesson_id` + `content_version=2.0` + принятому `status=mapped`; `review_required`, `unmapped`, неизвестные ID и несовпавшая версия должны завершаться явным отказом без генератора;
- в оставшихся путях выбора из diagnostic pool требовать точное совпадение topic и family; не объединять кандидатов через OR и не подменять topic общим family;
- переносить `item_family` из diagnostic question без отдельного восстановления;
- запретить default-addition fallback для curricular lesson route;
- отделить semantic mapping от assessment/mastery: rubric и `do_not_infer_from_one_lesson` не дают автоматического зачёта;
- для пилота разделить `g1_compose_decompose_10` на разные skills либо ключевать и проверять evidence как минимум по `skill_id + diagnostic_topic_id + item_family`; продвижение по одному family не должно осваивать другой;
- добавить проверки fail-closed для исходных 46 `unmapped`, новых пониженных строк, неверной версии, неизвестного lesson ID, topic/family collision и отсутствия fallback.

Смысловая приёмка D1 закрыта решениями по всем 32 строкам, включая честно сохранённые `review_required`. При расширении за пределы узкого пилота:

- решения уже перенесены в JSON; производные списки/counts пересчитаны, опровергнутые исходные `mapped` сняты;
- оставить 10 `review_required` закрытыми для автоматики до part-level mapping/разделения уроков или новых узких contracts/families;
- оставить 59 итоговых `unmapped` закрытыми для автоматики; новые runtime skills/families можно создавать отдельными задачами покрытия;
- исправить внутренние противоречия `g1_t01`, `g1_t03`, `g1_t05`, `g1_t06/g1_t07` и расширить валидатор от проверки существования ссылок до проверки разрешающего статуса, версии, точного topic/family selection и отсутствия fallback.

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

## Техническая приёмка в полной копии — 2026-09-10

Проверен HEAD `23b44e7df7f93f910274beaed3dee5b163816692` после `git fetch origin` и `git switch codex/d1-grade1-topic-identity-2026-09-10`. Рабочая директория на момент проверки была чистой. База сравнения: `origin/codex/active-orchestration-2026-09-09` = `f352af42f248475fbc6ccc8133111ecabd74870d`.

| Проверка | Результат |
|---|---|
| `python3 backend/scripts/validate_grade1_topic_identity.py` | OK: 26 тем, 78 уникальных уроков, 7 diagnostic topics, 6 grade-1 skills; 9 / 23 / 46 |
| `python3 -m py_compile backend/scripts/validate_grade1_topic_identity.py` | Код возврата 0 |
| `git diff --check origin/codex/active-orchestration-2026-09-09...HEAD` | Пустой вывод, код возврата 0 |
| `git diff --name-only origin/codex/active-orchestration-2026-09-09...HEAD` | Ровно четыре ожидаемых файла: карта, валидатор, этот аудит, WORKLOG; `user_states.json` отсутствует |
| `python3 backend/scripts/validate_adapted_lessons.py` | OK для 1–9 классов |
| `python3 backend/scripts/validate_grade1_reference.py --verify-sources` | OK; 14 unit_verified / 12 unverified / 1 missing_book |

Встроенная Git-проверка D1-валидатора видит только изменения относительно HEAD; отсутствие пользовательского состояния в diff ветки подтверждено отдельной командой выше. Зелёные проверки не подтверждают китайский нижний том и не заменяют смысловую приёмку. Отчёт этой приёмки добавляется следующим коммитом; исходный проверенный HEAD сохраняется как точка воспроизведения.

После переноса решений Sol все три валидатора и `py_compile` повторно прошли; D1 сообщает **9 mapped / 10 review_required / 59 unmapped**. Дополнительно сверены 32 уникальных решения, производные списки, неизменность всех 46 исходных unmapped и 51 локальная ссылка на доказательства. `git diff --check` без ошибок. Для `g1-t12-l01` чистый assessor принял 13 и отверг 12; для `g1-t09-l02` принял 6 и отверг 5. API и реальные профили в этих проверках не использовались.
