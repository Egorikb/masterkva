# MasterKva v1 → v2 Launch Roadmap

## 1. Purpose

This document freezes the current working baseline of MasterKva v1 and defines the first controlled expansion path toward v2.

The project goal is not to add more features for their own sake. The goal is to turn MasterKva into a deterministic educational system that can:

- diagnose skill gaps;
- explain using the curriculum material;
- remediate errors with the right visual support;
- verify mastery;
- promote the learner only when the contract is satisfied.

## 2. Frozen v1 baseline

The current v1 baseline is considered proven because the following behavior has already been verified:

- diagnosis is separated from learning;
- after diagnosis the system enters `explanation`;
- `давай` is the explicit continuation trigger into practice;
- `skill-aware runtime` is available;
- `skill_registry.json` exists;
- `skill_contracts.json` exists;
- `g2_addition_core` is running as the active pilot;
- `number_bond` is confirmed for early arithmetic;
- live QA has validated the end-to-end flow;
- backend and frontend already support the educational path as a working scenario.

### Baseline rule

Do not change the current flow unless a change is required to preserve the baseline or to support a controlled v2 expansion.

## 3. First golden skill-chain

The first v2 expansion should not start with the whole 1–9 curriculum.
It should start with one short, high-confidence chain that can be stabilized end-to-end.

### Chosen golden chain

- `g1_early_arithmetic_core`
- `g2_addition_core`

### Why this chain first

- it is the most pedagogically fundamental part of the current system;
- it already matches the validated live behavior;
- it has the clearest visual policy (`number_bond` for grade 1, constrained visual support for grade 2);
- it lets us test registry, contracts, remediation, and QA without bringing in unrelated domain complexity.

### Extension after the first chain is stable

Only after the pair `g1 → g2` is fully validated should the project extend the same pattern to:

- `g3_time_measurement_core`
- then other early-grade chains
- then the rest of the curriculum in controlled steps

## 4. v2 work plan

### Phase 0 — Baseline freeze

**Goal:** lock the current working behavior and prevent regressions.

**Deliverables:**
- documented baseline flow;
- regression tests for state transitions;
- stable QA scenario for diagnosis → explanation → `давай` → practice;
- acceptance checklist for the baseline.

**Done when:**
- the current flow passes tests and live QA without drift;
- the baseline is documented as the reference path.

### Phase 1 — Curriculum graph for the golden chain

**Goal:** convert the selected chain into a formal prerequisite graph.

**Deliverables:**
- explicit prerequisite links;
- explicit next-skill links;
- one validated chain with no dangling transitions;
- a clear path from grade 1 to grade 2.

**Done when:**
- the chain can be reasoned about as a graph, not only as a list of topics.

### Phase 2 — Skill registry hardening

**Goal:** make the registry a real structural source of truth.

**Deliverables:**
- `skill_id`
- `grade`
- `domain`
- `topic`
- `prerequisites`
- `next_skills`
- `maturity_status`

**Recommended maturity statuses:**
- `draft`
- `shadow`
- `active_pilot`
- `active`
- `deprecated`

**Done when:**
- the golden chain is fully represented in the registry;
- skills are clearly separated by maturity level.

### Phase 3 — Skill contracts as the pedagogical layer

**Goal:** make the contract the place where the system knows how to teach, test, remediate, and promote a skill.

**Each contract should define:**
- coverage status;
- diagnostic rules;
- remediation mapping;
- visual template;
- board policy;
- mastery gate;
- error model;
- validation rules.

**Done when:**
- every skill in the golden chain has a complete, validated contract.

### Phase 4 — Mistake taxonomy

**Goal:** distinguish error types so remediation becomes cause-oriented instead of generic.

**Suggested error classes:**
- computational error;
- conceptual error;
- reading error;
- sign error;
- place-value error;
- procedural slip;
- visual misread;
- misconception.

**Done when:**
- the system can classify errors into stable buckets and route remediation accordingly.

### Phase 5 — Deterministic remediation engine

**Goal:** turn “give 2–5 similar tasks” into a concrete, repeatable cycle.

**Recommended cycle:**
1. error;
2. classification;
3. clarifying task;
4. same-level practice;
5. short explanation;
6. repeat check;
7. mastery check;
8. promotion or return to remediation.

**Done when:**
- the cycle is predictable;
- LLM does not own the transition logic;
- the system does not get stuck in an endless loop.

### Phase 6 — Persistent student profile

**Goal:** preserve learner context across sessions.

**Profile should store:**
- mastered skills;
- weak skills;
- error history;
- response speed;
- pending remediation;
- last active skill;
- diagnosis confidence;
- mastery status history.

**Done when:**
- a returning learner continues from the real learning state, not from a blank slate.

### Phase 7 — Coverage-run and quality gates

**Goal:** make content coverage machine-checkable.

**For each skill verify:**
- diagnostic item exists;
- practice exists;
- explanation exists;
- visual policy exists;
- remediation rule exists;
- mastery gate exists.

**Rule:**
- if coverage is incomplete, the skill must not become `active`.
- it should remain `shadow` or `incomplete`.

**Done when:**
- the golden chain passes a repeatable coverage-run.

### Phase 8 — Visual map expansion

**Goal:** turn visual support into a curated pedagogy library, not a generic UI layer.

**For now, the age-appropriate visual policy should remain:**
- grade 1: `number_bond`, concrete objects, number line;
- grade 2–4: number sense, place value, structured arithmetic visuals;
- grade 5–6: equations, percent grids, fraction / ratio models;
- grade 7–9: rational numbers, graphs, coordinate systems, algebraic visuals.

**Done when:**
- every visual template is linked to a contract and age-appropriate learning goal.

### Phase 9 — Scale to more chains

**Goal:** replicate the golden chain pattern to the next curriculum segments.

**Expansion order suggestion:**
1. early arithmetic chain;
2. place value / number sense;
3. equations;
4. fractions / percents;
5. rational numbers;
6. graphs and functions.

**Done when:**
- each new chain is added with the same quality controls as the first one.

### Phase 10 — Analytics and integrations

**Goal:** add product-level reporting only after the educational core is stable.

**Possible outputs later:**
- parent dashboard;
- teacher dashboard;
- PDF exports;
- progress reports;
- school integrations;
- SSO;
- multilingual support.

**Important rule:**
- these are v2+ growth features, not the first thing to build.

## 5. What must not happen

Do not:

- expand to the full curriculum before the golden chain is stable;
- let LLM become the source of truth for mastery decisions;
- add a heavy orchestrator before the state machine is stable;
- build broad integrations before educational coverage is reliable;
- replace focused visual templates with one universal board.

## 6. Current working principle

The right development order is:

1. freeze baseline;
2. stabilize the golden chain;
3. formalize graph;
4. harden registry;
5. complete contracts;
6. classify errors;
7. make remediation deterministic;
8. persist learner state;
9. add coverage gates;
10. expand visuals;
11. scale curriculum;
12. add analytics and integrations.

## 7. Final note

The project is already beyond the prototype stage.
The next step is not to make it bigger immediately, but to make the educational core strict, testable, and reusable.
