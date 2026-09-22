# MasterKva — точка входа

Обновлено 2026-09-22. Перед работой читать AGENTS.md и [docs/WORKLOG.md](docs/WORKLOG.md). Поручения моделям: [docs/ORCHESTRATION.md](docs/ORCHESTRATION.md).

- Рабочая база: `/home/egor/workspace_hermes/MasterKva/ACTIVE`.
- Базовая ветка: `codex/active-orchestration-2026-09-09`; текущая B1: `codex/b1-curricular-runtime-2026-09-11`, [PR #3](https://github.com/Egorikb/masterkva/pull/3). GitHub: Egorikb/masterkva. main с полным DeepTutor не заменять MVP.
- Backend: FastAPI, `cd backend && uvicorn main:app --host 127.0.0.1 --port 8001`; frontend Next.js на 3000. После изменения кэшируемых диагностических данных нужен перезапуск.
- Учебные данные: backend/data. Curriculum, адаптированные уроки и диагностические topic_id не тождественны по номеру.
- 1 класс: reference_version 2.0, 26 тем, 26 примеров, 78 заданий; 24 exact, 33 ordered, 21 rubric. [Пособие](docs/grade1/TEACHER_GUIDE.md), [стандарт и ограничения](docs/GRADE1_REFERENCE.md).
- Верхний китайский том PEP 2022 найден: 42 задания привязаны к проверенным разделам. Нижний том не подтверждён: 36 заданий unverified. Статус источников: backend/data/curriculum/grade_1_sources.json.
- lesson_assessment.py — чистая оценка по частям/рубрикам. Узкий B1 принят: только `g1-t12-l01` v2.0 в `/api/v1/plugins/panda/chat`; остальные 77 уроков закрыты, mastery не повышается. Вход в пилот через UI пока не реализован (U1).
- Сервер определяет оценку и прогресс; LLM объясняет. Не смешивать запрос подсказки и попытку ответа.
- 2–9 классы прошли структурную миграцию, не финальную предметную проверку. Миграторы пропускают reference_version.
- Приёмка 13.09 после исправлений Sol: **214 pytest passed**, включая штатный TestClient вне песочницы; frontend typecheck/lint/build и три валидатора данных — OK. Тесты изолируют состояние детей и LLM-ключи. [Доказательства и API для U1](docs/audit/2026-09-13-b1-acceptance.md).
- Чужие изменения user_states.json не читать/не править/не коммитить без отдельной задачи. Параллельная настройка Notion в README/.vscode/scripts принадлежит соседней работе.
- Ветки учебной цепочки, registry/контракты и пользовательское состояние менять только по конкретной карточке; в registry 40 навыков.
- D1 принят: 9 mapped / 10 review_required / 59 unmapped, PR #2 вошёл в базу `0d53e1f`. Следующий backend-этап — B2: действия, повтор запроса и выход после ошибок. Параллельно допустимы U1 по контракту B1 и C1 по нижнему оригиналу; расширение допуска уроков требует отдельной проверки.

## Команды текущего этапа

```bash
python3 backend/scripts/validate_adapted_lessons.py
python3 backend/scripts/validate_grade1_topic_identity.py
python3 backend/scripts/validate_grade1_reference.py --verify-sources
PYTHONDONTWRITEBYTECODE=1 timeout 55s python3 -m pytest -q tests -p no:cacheprovider -o faulthandler_timeout=25
python3 backend/scripts/export_grade1_guide.py
git diff --check
```

Исторический milestone мая 2026: tag masterkva-v2-milestone-complete, commit 033ec4c. Его отметки complete и прежние числа тестов не описывают текущую готовность приложения. Полезная история сохранена в Git и WORKLOG; заметки о посторонних проектах удалены из этой точки входа.
