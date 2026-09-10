# MasterKva — точка входа

Обновлено 2026-09-11. Перед работой читать AGENTS.md и [docs/WORKLOG.md](docs/WORKLOG.md). Поручения моделям: [docs/ORCHESTRATION.md](docs/ORCHESTRATION.md).

- Рабочая база: `/home/egor/workspace_hermes/MasterKva/ACTIVE`.
- Ветка: `codex/active-orchestration-2026-09-09`; GitHub: Egorikb/masterkva. main с полным DeepTutor не заменять MVP.
- Backend: FastAPI, `cd backend && uvicorn main:app --host 127.0.0.1 --port 8001`; frontend Next.js на 3000. После изменения кэшируемых диагностических данных нужен перезапуск.
- Учебные данные: backend/data. Curriculum, адаптированные уроки и диагностические topic_id не тождественны по номеру.
- 1 класс: reference_version 2.0, 26 тем, 26 примеров, 78 заданий; 24 exact, 33 ordered, 21 rubric. [Пособие](docs/grade1/TEACHER_GUIDE.md), [стандарт и ограничения](docs/GRADE1_REFERENCE.md).
- Верхний китайский том PEP 2022 найден: 42 задания привязаны к проверенным разделам. Нижний том не подтверждён: 36 заданий unverified. Статус источников: backend/data/curriculum/grade_1_sources.json.
- lesson_assessment.py — чистая оценка по частям/рубрикам. Локальный B1 подключает только `g1-t12-l01` v2.0 к `/api/v1/plugins/panda/chat`; рубрика и один урок не дают автоматического mastery.
- Сервер определяет оценку и прогресс; LLM объясняет. Не смешивать запрос подсказки и попытку ответа.
- 2–9 классы прошли структурную миграцию, не финальную предметную проверку. Миграторы пропускают reference_version.
- Последний B1-прогон в архивной копии: автономные 23/23, py_compile и валидаторы identity/adapted/reference прошли; штатные pytest/TestClient и полный frontend typecheck не выполнены из-за отсутствующих зависимостей.
- Чужие изменения user_states.json не читать/не править/не коммитить без отдельной задачи. Параллельная настройка Notion в README/.vscode/scripts принадлежит соседней работе.
- Ветки учебной цепочки, registry/контракты и пользовательское состояние менять только по конкретной карточке; в registry 40 навыков.
- D1 принят: 9 mapped / 10 review_required / 59 unmapped. B1 реализован локальным patch, но ещё не опубликован и не принят. Следующие работы: штатный regression gate и Sol-приёмка B1, затем B2; параллельно C1 по нижнему оригиналу.

## Команды текущего этапа

```bash
python3 backend/scripts/validate_adapted_lessons.py
python3 backend/scripts/validate_grade1_topic_identity.py
python3 backend/scripts/validate_grade1_reference.py --verify-sources
pytest -q tests/services/test_curricular_lesson_runtime.py tests/api/test_panda_curricular_b1.py tests/api/test_panda_chat_mvp_contract.py
python3 backend/scripts/export_grade1_guide.py
git diff --check
```

Исторический milestone мая 2026: tag masterkva-v2-milestone-complete, commit 033ec4c. Его отметки complete и прежние числа тестов не описывают текущую готовность приложения. Полезная история сохранена в Git и WORKLOG; заметки о посторонних проектах удалены из этой точки входа.
