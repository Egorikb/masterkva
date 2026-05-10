# GPT-4o mini — навигация по проекту DeepTutor

> Этот документ — быстрый вход для GPT-4o mini. Читай его первым, чтобы не тратить контекст на лишние файлы.

## 1) Что это за ветка проекта
Это локальная рабочая зона по адаптации китайских школьных материалов под DeepTutor:
- `curriculum` — структура тем по классам;
- `curriculum_detailed` — подробные темы/задания для старших классов;
- `lessons` — адаптированные уроки;
- `diagnostic_pool.json` — пул диагностических вопросов;
- `docs/` — планы, итоги, чеклисты и маршруты.

### Источник истины
Если есть расхождение между документами, опирайся в таком порядке:
1. `docs/final_summary_china_curriculum.md`
2. `docs/implementation_plan.md`
3. `data/diagnostic_pool.json`
4. `docs/orchestration_prompt_and_checklist.md`

Старые analysis-документы уже вынесены в `docs/ARCHIVE_INDEX.md`. Используй их только как исторический контекст, а не как текущий статус.

## 2) Читать в таком порядке
1. `docs/final_summary_china_curriculum.md`
2. `docs/implementation_plan.md`
3. `docs/orchestration_prompt_and_checklist.md`
4. `docs/FINAL_CHECKLIST.md`
5. `docs/ARCHIVE_INDEX.md` — только если нужен исторический контекст

## 3) Главные файлы-сигналы
- `docs/final_summary_china_curriculum.md` — что уже готово и что осталось.
- `docs/implementation_plan.md` — этапы работ и порядок выполнения.
- `docs/orchestration_prompt_and_checklist.md` — мастер-маршрут и распределение по моделям.
- `docs/FINAL_CHECKLIST.md` — финальная проверка качества.
- `scripts/expand_diagnostic.py` — генератор/обновлятор `diagnostic_pool.json`.
- `deeptutor/services/diagnostic_engine.py` — как диагностика потребляет пул вопросов.

## 4) Текущее состояние по классам
- **1–6 классы** — базовые материалы и диагностика.
- **7–9 классы** — более подробный curriculum, часто с привязкой к PDF и CPA-структуре.
- **Диагностика** — должна быть согласована по всем классам **1–9**.

## 5) Как ориентироваться по задаче
### Если нужно понять, что уже сделано
Смотри:
- `docs/final_summary_china_curriculum.md`
- `docs/FINAL_CHECKLIST.md`

### Если нужно понять, что делать дальше
Смотри:
- `docs/implementation_plan.md`
- `docs/orchestration_prompt_and_checklist.md`

### Если нужно править диагностику
Смотри:
- `scripts/expand_diagnostic.py`
- `deeptutor/services/diagnostic_engine.py`
- `data/diagnostic_pool.json`

### Если нужен только старый контекст
Смотри:
- `docs/ARCHIVE_INDEX.md`

### Если нужно делать content QA
Проверяй:
- уникальность вопросов,
- возрастную уместность,
- русский контекст,
- отсутствие поломки JSON-схемы,
- согласованность с классом и темой.

## 6) Быстрый маршрут для GPT-4o mini
Если у тебя мало контекста, делай так:
1. Прочитай `docs/GPT4O_MINI_NAV.md`.
2. Прочитай один документ про статус.
3. Прочитай один документ про план.
4. Читай только нужный файл данных.
5. Не открывай весь репозиторий без необходимости.

## 7) Правило по модели
Для этой ветки проекта:
- **gpt-5.4 mini** — быстрый аудит;
- **gpt-5.2 codex** — основная правка данных;
- **gpt-5.4** — QA;
- **gpt-5.3 codex** — точечные фиксы;
- **gpt-5.5** — финальная интеграция.

## 8) Важный ориентир
Не переписывай всё целиком, если достаточно точечных правок. Сначала проверь статус, потом меняй только нужную часть.
