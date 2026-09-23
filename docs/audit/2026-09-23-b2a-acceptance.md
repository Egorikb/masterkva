# Приёмка B2a — действия Panda Chat

Дата: 23.09.2026. Ветка: `codex/b1-curricular-runtime-2026-09-11`. Перед началом HEAD был `30e7cbcd1a36aa638b790fd5725b0c970648d9ab`; принятая база B1 `a9672a1` является его предком. Два последующих коммита с планом сохранены. Чужой `docs/EXECUTION_PLAN_2026-09-22/_prompts_queue.md` не читался, не изменялся и не включён в результат.

## Результат

- `ChatRequest` и TypeScript-контракт принимают `start`, `answer`, `hint`, `rephrase`, `pause`, `resume`, `advance`.
- Только `answer` оценивает сообщение и увеличивает попытку. `hint` и `rephrase` сохраняют текущую часть и возвращают безопасный ответ без эталона; новая legacy-помощь также удаляет эталонные поля из публичного состояния.
- Явная пауза сохраняет curricular lesson/version/part и legacy-вопрос. `resume` возвращает сохранённый вопрос, не оценивая `message`. Во время паузы остальные явные действия отклоняются без изменения состояния.
- `advance` остаётся серверным gate. Неверная фаза, преждевременный переход, повторная помощь завершённой ordered-части и несоответствие сессии возвращают явный код ошибки.
- Старый клиент без `action`, текстовое «стоп» и возврат из curricular в прежний legacy-контекст сохранили поведение B1.

Полный контракт для Terra: [panda-actions.md](../api/panda-actions.md).

## Проверки

```text
timeout 90s python3 -m pytest -q tests/api/test_panda_actions_b2a.py
5 passed, 2 warnings in 2.48s

PYTHONDONTWRITEBYTECODE=1 timeout 90s python3 -m pytest -q \
  tests/api/test_panda_curricular_b1.py tests/api/test_panda_chat_mvp_contract.py \
  -p no:cacheprovider -o faulthandler_timeout=35
27 passed, 24 warnings in 2.03s

PYTHONDONTWRITEBYTECODE=1 timeout 120s python3 -m pytest -q tests \
  -p no:cacheprovider -o faulthandler_timeout=35
219 passed, 33 warnings in 4.85s

cd frontend && npm run typecheck
OK

python3 -m py_compile backend/deeptutor/api/routers/plugins_api.py \
  tests/api/test_panda_actions_b2a.py
OK
```

Новая приёмка поднимает Uvicorn на `127.0.0.1` и отправляет настоящие HTTP POST через стандартную библиотеку. Её запускали вне filesystem/network sandbox, поскольку sandbox запрещает создание локального сокета. Синтетические профили изолированы временным state-файлом; реальные состояния и API моделей не использовались. Предупреждения относятся к устаревающим интерфейсам httpx/websockets, падений и исключённых тестов нет.

## Границы и передача

**B2b:** расширять этот же контракт, не заводить второй endpoint или второй набор названий действий. Добавить ID доставки/попытки, серверный номер части, обработку повтора и устаревшего ответа, затем выход после трёх математических ошибок. B2a не даёт транзакционной идемпотентности; хранение всё ещё JSON.

**U1a:** использовать [контракт кнопок](../api/panda-actions.md). UI отправляет действие ребёнка, но не меняет локально attempts/part/phase до ответа сервера. Для первого экрана доступен только допущенный `g1-t12-l01` v2.0; остальные 77 уроков закрыты. Поля B2b заранее не придумывать.

Обычные legacy-ответы сохраняют историческую полную форму состояния ради совместимости; новый child-safe фильтр применяется к `hint/rephrase`, а curricular-ответы остаются child-safe по B1. Новый UI U1a должен работать через curricular-контракт. Голос, новый UI, SQLite, новые уроки и mastery в B2a не добавлялись.

Следующий ID по очереди: **B2b**. U1a может брать зафиксированный контракт B2a, но эта приёмка не начинала ни B2b, ни U1a.
