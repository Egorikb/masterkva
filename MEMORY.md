# MasterKva — точка входа

Обновлено 2026-09-23. Перед работой читать AGENTS.md и [docs/WORKLOG.md](docs/WORKLOG.md). Поручения моделям: [docs/ORCHESTRATION.md](docs/ORCHESTRATION.md).

Экономный порядок исполнения и отдельные ТЗ моделей: [план завершения](docs/EXECUTION_PLAN_2026-09-22/README.md). Следующий backend-запуск: **Sol/high, карточка B2b**; Terra/U1a может брать принятый контракт B2a. Остальные карточки выдавать по одной из QUEUE. Astra — только спорный узел или итоговая независимая проверка.

Продуктовая цель первой версии: конкретный пробел арифметики у ребёнка 1–3 класса → наглядное действие → самостоятельная новая задача → повторная проверка. H0 проверяет управление сразу после U1a; [H1](docs/EXECUTION_PLAN_2026-09-22/PILOT.md) проверяет маршрут с 5–10 семьями до расширения содержания. Это принятые требования плана, не проведённый пилот.

- Рабочая база: `/home/egor/workspace_hermes/MasterKva/ACTIVE`.
- Базовая ветка: `codex/active-orchestration-2026-09-09`; текущая B1: `codex/b1-curricular-runtime-2026-09-11`, [PR #3](https://github.com/Egorikb/masterkva/pull/3). GitHub: Egorikb/masterkva. main с полным DeepTutor не заменять MVP.
- Backend: FastAPI, `cd backend && uvicorn main:app --host 127.0.0.1 --port 8001`; frontend Next.js на 3000. После изменения кэшируемых диагностических данных нужен перезапуск.
- Учебные данные: backend/data. Curriculum, адаптированные уроки и диагностические topic_id не тождественны по номеру.
- 1 класс: reference_version 2.0, 26 тем, 26 примеров, 78 заданий; 24 exact, 33 ordered, 21 rubric. [Пособие](docs/grade1/TEACHER_GUIDE.md), [стандарт и ограничения](docs/GRADE1_REFERENCE.md).
- Верхний китайский том PEP 2022 найден: 42 задания привязаны к проверенным разделам. Нижний том не подтверждён: 36 заданий unverified. Статус источников: backend/data/curriculum/grade_1_sources.json.
- lesson_assessment.py — чистая оценка по частям/рубрикам. Узкий B1 принят: только `g1-t12-l01` v2.0 в `/api/v1/plugins/panda/chat`; остальные 77 уроков закрыты, mastery не повышается. B2a принят: [answer/hint/rephrase/pause/resume/advance](docs/api/panda-actions.md) разделены, переходы проверяет сервер. Вход в пилот через UI пока не реализован (U1a).
- Сервер определяет оценку и прогресс; LLM объясняет. Только `answer` является попыткой; помощь и возврат после паузы не оценивают сообщение.
- 2–9 классы прошли структурную миграцию, не финальную предметную проверку. Миграторы пропускают reference_version.
- Приёмка B2a 23.09: **219 pytest passed**, включая 5 сценариев на настоящем локальном HTTP; frontend typecheck — OK. Тесты изолируют состояние детей и LLM-ключи. [Доказательства и передача B2b/U1a](docs/audit/2026-09-23-b2a-acceptance.md).
- Чужие изменения user_states.json не читать/не править/не коммитить без отдельной задачи. Параллельная настройка Notion в README/.vscode/scripts принадлежит соседней работе.
- Ветки учебной цепочки, registry/контракты и пользовательское состояние менять только по конкретной карточке; в registry 40 навыков.
- D1 принят: 9 mapped / 10 review_required / 59 unmapped, PR #2 вошёл в базу `0d53e1f`. Следующий backend-этап — B2b: повтор запроса, устаревший ответ и выход после ошибок. Параллельно допустимы U1a по контракту B2a и C1 по нижнему оригиналу; расширение допуска уроков требует отдельной проверки.

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
