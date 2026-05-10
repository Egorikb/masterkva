# MasterKva MVP Current Status — 2026-05-10

## Scope
MVP route only: `диагностика → слабая тема → объяснение → практика → проверка → отчёт`.

## 1) Re-run quality gates

### Backend
```bash
cd /home/egor/workspace_hermes/masterkva/backend
python -m py_compile deeptutor/api/main.py deeptutor/api/routers/plugins_api.py deeptutor/services/diagnostic_engine.py deeptutor/services/practice_engine.py deeptutor/services/report_service.py
pytest tests/api/test_question_router.py tests/api/test_solve_router.py tests/core/test_prompt_manager.py tests/services/test_diagnostic_pool_contract.py tests/services/test_diagnostic_engine.py tests/services/test_practice_engine.py tests/services/test_report_service.py tests/api/test_plugins_api_check_answer_fuzzy_numeric_red.py tests/api/test_panda_chat_mvp_contract.py tests/api/test_plugins_api_no_unreachable_legacy.py -q
```
Observed:
- compile: PASS
- tests: `33 passed, 8 warnings`

### Frontend
```bash
cd /home/egor/workspace_hermes/masterkva/frontend
npm run lint
npm run typecheck
npm run build
```
Observed:
- lint: PASS, 3 warnings (`@next/next/no-img-element`)
- typecheck: PASS
- build: PASS
- Turbopack/NFT warning remains (`next.config.mjs` trace via image route)

## 2) Real E2E verification (API-driven)

Backend run:
```bash
cd /home/egor/workspace_hermes/masterkva/backend
uvicorn deeptutor.api.main:app --host 127.0.0.1 --port 8001
```

Health:
```bash
curl -sS -o /tmp/mk_health.txt -w '%{http_code}' http://127.0.0.1:8001/docs
# 200
```

Endpoint:
- `POST http://127.0.0.1:8001/api/v1/plugins/panda/chat`

Evidence:
- `docs/mvp-e2e-evidence-2026-05-10.json`

Observed after fix:
- diagnostic reaches `state.phase=explanation`
- `state.weak_topic` exists
- `weak_topic.source_question_id` now points to real failed diagnostic item (non-fallback):
  - `topic_id: g1_t01`
  - `source_question_id: g1_t01_q01`
- practice starts with `state.phase=practice` and `state.current_practice`
- practice answer checked by backend
- final `state.phase=report`

## 3) Fixes made in this pass

### Backend
- `backend/deeptutor/api/routers/plugins_api.py`
  - `get_diagnostic_question(...)` now returns stable metadata from diagnostic pool:
    - `id`
    - `topic_id`
    - `practice_ref`

Reason:
- without `id/topic_id`, diagnostic answers were recorded without resolvable question provenance,
  causing fallback weak-topic source in E2E.

Validation:
```bash
cd /home/egor/workspace_hermes/masterkva/backend
pytest tests/services/test_diagnostic_engine.py tests/api/test_panda_chat_mvp_contract.py tests/api/test_plugins_api_check_answer_fuzzy_numeric_red.py -q
# 7 passed
```

## 4) Frontend warnings decision

Status: documented, not refactored in this pass (scope-safe).
- 3 warnings in `components/interactive-blackboard.tsx` for `<img>`
- 1 Turbopack/NFT trace warning around image route and `next.config.mjs`

These are non-blocking for MVP E2E contract validation.

## 5) Git state / staging policy

Repo remains dirty (many unrelated modified/untracked files).
Do not use blind `git add .`.
Stage by groups only:
1. MVP backend contract/services/tests
2. Frontend MVP API-contract/client wiring
3. Docs/evidence/handoff
4. Unrelated legacy/config changes separately

## 6) Current blockers and readiness

### P0
- none (gates and E2E route pass)

### P1
- none for MVP route contract (weak-topic provenance fixed)

### P2
- frontend lint/build warnings listed above

## 7) Ready status

- **Commit:** conditionally yes, only with selective staging by scope groups.
- **Deploy/demo:** yes for MVP route demo (`diagnostic → weak topic → explanation → practice → check → report`).
