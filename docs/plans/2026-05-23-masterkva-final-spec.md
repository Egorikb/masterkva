# MasterKva Final v1 → v2 Spec

## 1. Purpose

This document freezes the current v1 baseline and defines the exact next implementation order for the first v2 hardening path.

The project goal is to become a deterministic educational system for grades 1–9, not a generic AI tutor.

## 2. Frozen baseline

The baseline is considered proven and must stay intact:

- diagnosis is separated from learning;
- after diagnosis the system enters `explanation`;
- `давай` is the explicit continuation trigger;
- `skill-aware runtime` exists;
- `skill_registry.json` exists;
- `skill_contracts.json` exists;
- `g2_addition_core` is the active pilot;
- `number_bond` is confirmed for grade 1;
- live QA passed on the real flow;
- current tests are green.

## 3. First golden chain

The first v2 hardening target is:

- `g1_early_arithmetic_core`
- `g2_addition_core`

This chain is correct because it is small, pedagogically fundamental, and already compatible with the verified baseline.

### Current chain state
- `g1_early_arithmetic_core`: shadow / partial
- `g2_addition_core`: active / partial
- `g1 -> g2` prerequisite path exists in the registry
- live QA already validates the grade-2 end of the chain

## 4. What is already correct

### Architecture
- backend owns transitions;
- LLM is a helper, not the authority;
- active/shadow rollout is the right safety mechanism;
- deterministic state machine is the correct v1 core.

### Pedagogy
- diagnosis and learning are separated;
- visual policy is age-aware;
- `number_bond` is the right grade-1 visual primitive;
- the current flow is already aligned with the educational route.

### Data model
- registry exists;
- contracts exist;
- diagnostic pool exists;
- visual topic map exists;
- curriculum_detailed materials exist.

## 5. What must be done now

### Priority 1 — Freeze the baseline as a regression target
Keep the current flow stable and treat it as the rollback target.

### Priority 2 — Harden the golden chain
The chain must become a deterministic, measurable path, not only a metadata path.

### Priority 3 — Expand coverage only inside the chain
Do not expand beyond the chain until the chain passes coverage and mastery gates.

## 6. Immediate implementation order

### Step 1 — Golden chain manifest
Use a dedicated manifest for the chain.

Current artifact:
- `backend/data/golden_chains/g1_to_g2_addition.json`

This should remain the canonical chain definition for the first v2 hardening wave.

### Step 2 — Coverage snapshot and QA gate
Keep a chain-level coverage snapshot and update it when the chain changes.

Current artifact:
- `docs/plans/2026-05-23-masterkva-golden-chain-coverage-snapshot.md`

### Step 3 — Skill contract hardening
For the chain, strengthen:
- coverage status;
- diagnostic rules;
- remediation mapping;
- visual policy;
- board policy;
- mastery gate;
- validation rules.

### Step 4 — Backend mastery ownership
Introduce a deterministic mastery evaluator in the backend/state machine path so promotion is not decided by LLM text.

### Step 5 — Error taxonomy and remediation branching
Split remediation by error type, not by generic similarity.

## 7. Gaps that are still open

- coverage is still partial for both chain skills;
- `g1_early_arithmetic_core` needs more diagnostic breadth;
- `g2_addition_core` needs a stronger mastery gate path;
- remediation still needs more explicit branching;
- the chain still needs a strict release gate before any broader curriculum expansion.

## 8. What can wait

Do not start yet:

- full curriculum graph for all grades;
- broad diagnostic expansion outside the chain;
- teacher/parent dashboards;
- SSO and school integrations;
- heavy gamification;
- multi-language support;
- complex LLM orchestration.

## 9. Risks to avoid

- letting LLM decide mastery;
- using registry as decoration while transitions still follow topic labels;
- widening the golden chain too early;
- re-enabling board hints during diagnosis;
- merging explanation and practice back into one phase;
- treating partial coverage as production-ready coverage.

## 10. Definition of done for the first v2 hardening wave

The first v2 hardening wave is done when:

- the baseline still passes regression tests and live QA;
- the golden chain has explicit coverage and contract checks;
- mastery promotion is backend-owned;
- remediation is deterministic;
- the chain can be validated repeatedly without manual patching;
- no expansion beyond the chain is needed to keep the flow stable.

## 11. Final rule

Do not expand the project in width until the first golden chain is hardened in depth.
