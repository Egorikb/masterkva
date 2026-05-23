# MasterKva v2 Golden-Chain Baseline Freeze

Date: 2026-05-23

## Purpose
Freeze the hardened golden chain as a stable rollback target before any further expansion.

## Baseline scope
- `g1_early_arithmetic_core -> g2_addition_core`
- deterministic diagnosis / explanation / `давай` / practice / mastery flow
- remediation branching with item-family-driven taxonomy
- backend-owned mastery evaluator and promotion gate
- persistent student profile updates
- visual policy for early arithmetic
- acceptance suite for the release gate

## Current baseline artifacts
- `backend/data/skill_registry.json`
- `backend/data/skill_contracts.json`
- `backend/data/diagnostic_pool.json`
- `backend/data/visual_topic_map.json`
- `backend/deeptutor/api/routers/plugins_api.py`
- `backend/deeptutor/services/skill_runtime.py`
- `backend/deeptutor/services/error_taxonomy.py`
- `backend/deeptutor/services/mastery_evaluator.py`
- `backend/deeptutor/services/student_profile_store.py`
- `backend/deeptutor/services/practice_engine.py`
- `tests/services/test_golden_chain_manifest.py`
- `tests/api/test_panda_chat_mvp_contract.py`
- `tests/api/test_golden_chain_release_gate.py`

## Acceptance status
- Targeted regression suite: passing
- Golden-chain release gate suite: passing
- Promotion flow from `g1_early_arithmetic_core` to `g2_addition_core`: passing

## Freeze rule
From this point, treat the current hardened chain as the baseline reference.
Do not widen curriculum or alter the release-gate contract unless the next roadmap step explicitly requires it.

## Rollback target
If a later change breaks the deterministic chain, roll back to the latest commit that still passes the release gate and re-run the acceptance suite before continuing.
