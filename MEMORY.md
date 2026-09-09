# MasterKva — Долгосрочная память проекта

> Этот файл — расширение memory tool. Читается в каждой новой сессии.
> Обновлять при каждом значимом изменении.

## Статус проекта

- **Последний milestone:** v2 phases 0-10 complete (2026-05-24)
- **Git tag:** `masterkva-v2-milestone-complete`, commit `033ec4c`
- **Дорожная карта:** `/home/egor/Desktop/roadmap.txt`
- **Рабочая директория:** `/home/egor/workspace_hermes/masterkva-assembled`
- **Ветка:** `main`

## Архитектура

### Backend
- **Запуск:** `cd backend/ && uvicorn main:app --host 127.0.0.1 --port 8001`
- **Порт:** 127.0.0.1:8001 (Порт 8002 НЕ использовать!)
- **Health:** `curl http://127.0.0.1:8001/health`
- **После изменения diagnostic data файлов — рестарт uvicorn!** (кэширует DiagnosticEngine в памяти)

### Frontend
- Next.js dev server на :3000
- Для QA: Playwright Chromium с `--no-sandbox`

### Frozen Chains (3)
1. `g1→g2_addition` (`g1_early_arithmetic_core → g2_addition_core`)
2. `g1→g2_subtraction` (`g1_early_arithmetic_core → g2_subtraction_core`)
3. `g2→g3_time` (`g2_addition_core → g3_time_measurement_core`)

### Ключевые компоненты
| Файл | Назначение |
|------|-----------|
| `skill_registry.json` | 10 skills (g1-g9) |
| `skill_contracts.json` | validation + remediation + mastery gate |
| `error_taxonomy.py` | item-family driven error classification |
| `student_profile_store.py` | персистентный профиль, blocked/unblocked flow |
| `coverage_runner.py` | quality gate |
| `progress_analytics.py` | read-only GET /panda/progress/{user_id} |
| `mastery_evaluator.py` | deterministic backend mastery evaluator |
| `plugins_api.py` | state machine, mastery gate, promotion |

### Визуализации
- 7 canonical visual types
- `number_bond` для ранней арифметики (НЕ CPA-шаблон)
- Board off в диагностике, board on в обучении

## Тесты
- Последний регресс: **39 passed**
- Команда: `pytest -q tests/`
- Release gate: `tests/api/test_golden_chain_release_gate.py`
- Chain tests: `test_subtraction_chain.py`, `test_time_chain.py`, `test_progress_analytics.py`

## Ключевые принципы

1. **LLM НЕ источник истины для mastery** — только deterministic backend evaluator
2. **Board off в диагностике, board on  — в обучении**
3. **number_bond** для ранней арифметики, не общий CPA-шаблон
4. **item_family-driven remediation** с blocked_by flow
5. **Масштабирование только по проверенным цепочкам**
6. **Разделять** Diagnosis, Remediation, Mastery gate

## Roadmap фазы

| Фаза | Статус |
|------|--------|
| 0. Baseline v1 freeze | ✅ |
| 1. Golden skill-chain | ✅ |
| 2. Skill registry expansion | ✅ |
| 3. Skill contracts hardening | ✅ |
| 4. Mistake taxonomy | ✅ |
| 5. Deterministic remediation engine | ✅ |
| 6. Persistent student profile | ✅ |
| 7. Coverage-run quality gate | ✅ |
| 8. Visual map unification | ✅ |
| 9. Scaling by chains (3 frozen) | ✅ |
| 10. Analytics (read-only API) | ✅ |
| 11. Integrations | ⏸️ Deferred to v2 |

## Внешние интеграции

### Aymo
- GPT-5.5 доступен для архитектурных вопросов
- DeepSeek V4 Pro / Claude Sonnet 4.6 — заблокированы upgrade-plan gate
- Использовать по необходимости для complex reasoning

### SMB Share
- `smb://keenetic-0174.local/5836f55b36f53b18/`
- Папки: `/сайты/`, `/сайты/Готово/`, `/сайты/тест/`

## Live QA сценарии

### Ответы школьника для smoke-теста
`13, 7, 7, 3, 17, 120`, затем `давай`

### Для coverage-run (grade 9)
`13, 7, 7, 3, 17, 120, 4, 5, 50, 2, 5, парабола`

## Документация
- `/home/egor/workspace_hermes/masterkva-assembled/README.md`
- `/home/egor/workspace_hermes/masterkva-assembled/docs/plans/` — все plan-документы
- `/home/egor/Desktop/MasterKva_Project_Description.txt` — полный доклад
- `/home/egor/Desktop/MasterKva_Deep_Project_Report.txt` — глубокий отчёт
- `/tmp/rebuild-log-session.md` — лог восстановления

## Частые проблемы и решения

| Проблема | Решение |
|----------|---------|
| `browser_navigate` sandbox error | Playwright + Chromium + `--no-sandbox` |
| Backend не импортирует `main` | Запускать из `backend/`, не из корня |
| State устарел после правки JSON | Рестарт uvicorn |
| `page.waitForResponse` timeout | Метод ненадёжен для этого сценария |
| Memory tool full | Удалять старые записи, использовать MEMORY.md |

## Критерии качества

- Тесты должны проходить перед каждым коммитом
- Live QA после каждого milestone
- Coverage snapshot обновлён при изменении chains
- Не расширять scope без подтверждения

## video_site — Контент-воронка

- **Сайт:** https://idealive-app.vercel.app/blog
- **Директория:** `/home/egor/workspace_hermes/video_site/`
- **Статей:** 21 (JSON-формат), деплой на Vercel
- **Telegram:** @aaaanewsFromIT, chat_id `-1003916066966`, 21 пост (msg_id 130-148)
- **Бот:** News_to_day_bot, публикация через curl sendPhoto, caption ≤1000 зн
- **Vercel deploy:** `vercel --prod --yes --token $VERCEL_TOKEN` (токен из `/home/egor/backups/openclaw/2026-05-06/.env.bak`)
- **YouTube API key:** `~/workspace_hermes/youtube-ai-pipeline/.env` (YOUTUBE_API_KEY)
- **Транскрибация:** `yt-dlp --write-auto-sub --sub-lang en --sub-format srt` (работает ~95% видео)
- **Фактчекинг:** обязателен — сравнивать статью с транскриптом, убирать галлюцинации
- **Стиль:** журналистский, от третьего лица, без выдуманных цифр
- **YouTube mapping:** `/tmp/youtube_mapping.json` — slug → video_id
- **Транскрипты:** `/tmp/transcripts/{slug}.txt`
- **Процедура:** references/article-cleanup-procedure.md
