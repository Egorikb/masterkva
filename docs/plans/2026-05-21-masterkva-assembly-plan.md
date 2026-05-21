# MasterKva Assembly Plan

> **For Hermes:** implement task-by-task in the separate workspace at `/home/egor/workspace_hermes/masterkva-assembled`.

**Goal:** собрать отдельную рабочую версию MasterKva по приоритетам: учебный backend, стабильный кабинет, учебный RAG, state-transition tests.

**Architecture:** backend-first educational flow. UI только отображает и маршрутизирует состояние. RAG подключается только к учебным сценариям и не должен расползаться по всему приложению. Тесты фиксируют переходы состояний, чтобы не ломать маршрут диагностика → объяснение → практика → отчёт.

**Tech Stack:** Next.js frontend, Python/FastAPI backend, DeepTutor-inspired orchestrator/service separation, pytest.

---

## Status update
- Task 1 is now implemented in the assembled workspace.
- Verified with: `pytest tests/services/test_diagnostic_engine.py tests/services/test_practice_engine.py tests/services/test_report_service.py tests/api/test_panda_chat_mvp_contract.py -q`
- Result: `11 passed`
- Task 2 is now implemented in the assembled workspace.
- Frontend sources copied into `frontend/` from the stabilized MasterKva frontend.
- Verified with: `npm install` and `npm run build`
- Result: production build passed; only the pre-existing Turbopack NFT trace warning remains.
- Task 3 is now implemented in the assembled workspace.
- RAG is limited to the educational corpus in `backend/data/{lessons,curriculum,curriculum_detailed}` and is attached only to the learning flow.
- Verified with: `pytest tests/services/test_learning_rag.py tests/api/test_panda_chat_mvp_contract.py -q`
- Result: `7 passed`
- Task 4 is now partially implemented with an added RAG-specific contract test in `tests/api/test_panda_chat_mvp_contract.py`.

## Task 1: Strengthen the learning backend cycle

**Objective:** make the diagnostic/explanation/practice/report loop deterministic and testable.

**Files to create/modify:**
- `backend/deeptutor/services/diagnostic_engine.py`
- `backend/deeptutor/services/practice_engine.py`
- `backend/deeptutor/services/report_service.py`
- `backend/deeptutor/api/routers/plugins_api.py`
- `backend/tests/api/test_panda_chat_mvp_contract.py`

**Why first:** the product is only useful if the learning loop works end-to-end.

## Task 2: Stabilize the UI cabinet

**Objective:** make login/dashboard/session flows hydration-safe and predictable.

**Files to create/modify:**
- `frontend/app/page.tsx`
- `frontend/app/login/page.tsx`
- `frontend/app/signup/page.tsx`
- `frontend/app/dashboard/layout.tsx`
- `frontend/app/dashboard/page.tsx`
- `frontend/lib/auth-store.ts`

**Why second:** users must enter the learning flow without flicker, premature redirects, or hidden state.

## Task 3: Add RAG only inside the educational context

**Objective:** allow teacher-style answers from curriculum/materials without turning the app into a generic chat bot.

**Files to create/modify:**
- `backend/deeptutor/services/learning_rag.py`
- `backend/deeptutor/api/routers/plugins_api.py`
- `backend/data/lessons/`
- `backend/data/curriculum/`
- `backend/data/curriculum_detailed/`
- `tests/services/test_learning_rag.py`
- `tests/api/test_panda_chat_mvp_contract.py`

**Why third:** RAG should enrich learning, not become a separate product path.

## Task 4: Add state-transition tests

**Objective:** protect the contract between states so changes cannot silently break the learning path.

**Files to create/modify:**
- `backend/tests/api/test_panda_chat_mvp_contract.py`
- `backend/tests/services/test_diagnostic_engine.py`
- `backend/tests/services/test_practice_engine.py`
- `backend/tests/services/test_report_service.py`

**Why fourth:** tests lock the behavior after the core flow is stable.

---

## Do-not-expand list
- TutorBot ecosystem
- payments
- book engine
- notebook/memory/skills editors
- multi-channel bots
- admin panel work unless required by auth

## Acceptance checkpoint
- The learning cycle is deterministic
- The dashboard does not misredirect during hydration
- RAG is visible only in educational scenarios
- Tests cover state transitions end-to-end
