# Приёмка B2b — идемпотентность и выход после ошибок

Дата: 23.09.2026. Ветка: `codex/b1-curricular-runtime-2026-09-11`, исходный HEAD `917d0798efa87cd0b294ed0cfe689c73564a96c6`. B2a принята и является непосредственной базой. Чужой `docs/EXECUTION_PLAN_2026-09-22/_prompts_queue.md` не читался, не изменялся и не включён в результат.

## Результат

- Сервер выдаёт `session_id` и `part_revision`; клиентский `request_id` проверяется в области ребёнок + занятие. Журнал хранит SHA-256 отпечаток содержимого, идентичность урока/версии/части и прежний child-facing ответ.
- Точный повтор возвращает прежний ответ с `replayed: true`. Другая нагрузка под тем же ID получает `request_id_conflict`. Новый ID с тем же математическим текстом создаёт новую попытку, пока часть активна.
- Повтор `start` не создаёт новую сессию, повтор `advance` не перепрыгивает часть. Повтор уже принятого старого ответа воспроизводится из журнала; новый ID со старой ревизией получает `stale_part`, запрос к прежнему занятию — `stale_session`.
- Parsed answer, помощь, техническое событие, пустой/неразобранный ответ и ручная проверка имеют разные `event_kind`. `invalid_input` не увеличивает `attempts` или `incorrect_attempts`; пустой legacy-ответ не запускает remediation.
- После трёх `incorrect` curricular-runtime возвращает первые проверенные шаги текущего урока без финального ответа и предлагает взрослого или паузу. Часть и mastery не закрываются. Произвольное задание или соседняя тема не выбираются.

Публичные поля, ошибки и атомарный набор для Terra/S1a зафиксированы в [panda-actions.md](../api/panda-actions.md).

## Проверки

```text
PYTHONDONTWRITEBYTECODE=1 timeout 120s python3 -m pytest -q \
  tests/api/test_panda_actions_b2a.py -p no:cacheprovider \
  -o faulthandler_timeout=35
8 passed, 2 warnings in 3.41s

PYTHONDONTWRITEBYTECODE=1 timeout 120s python3 -m pytest -q \
  tests/api/test_panda_curricular_b1.py tests/api/test_panda_chat_mvp_contract.py \
  tests/services/test_curricular_lesson_runtime.py tests/services/test_lesson_assessment.py \
  -p no:cacheprovider -o faulthandler_timeout=35
53 passed, 24 warnings in 2.22s

PYTHONDONTWRITEBYTECODE=1 timeout 150s python3 -m pytest -q tests \
  -p no:cacheprovider -o faulthandler_timeout=35
222 passed, 33 warnings in 6.48s

cd frontend && npm run typecheck
OK

python3 -m py_compile backend/deeptutor/api/routers/plugins_api.py \
  backend/deeptutor/services/curricular_lesson_runtime.py \
  tests/api/test_panda_actions_b2a.py tests/services/test_lesson_assessment.py
OK
```

HTTP-приёмка поднимает настоящий Uvicorn на `127.0.0.1` и использует синтетические профили. Она проверяет одинаковый/конфликтующий ID, новый ID с тем же ответом, повтор start/advance, late answer, stale session/part, три ошибки, паузу/возврат и отсутствие утечки финального ответа/mastery. Числовая регрессия сохраняет дроби, десятичные числа, ноль и единицы измерения. Реальные состояния детей и внешние модели не использовались.

## Ограничения и передача

Текущий JSON-журнал ограничен 64 результатами. Запись учебного изменения и запись результата выполняются последовательно, поэтому B2b не обещает атомарность при падении между ними и гонке нескольких процессов. Транзакция, уникальный индекс `(user_id, session_id, request_id)` и восстановление незавершённой операции принадлежат S1a.

Terra/U1a должна отправлять новый `request_id` для нового действия и повторять прежний ID только при повторной доставке. После `start` она хранит `session_id`; после каждого ответа — серверный `part_revision`. Attempts/phase/part меняются только по ответу сервера. S1a переносит перечисленные в контракте поля без переименования API и без второго журнала.

Следующий ID по очереди: **U1a**. Эта карточка не начинала UI, H0 или S1a.
