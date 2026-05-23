# MasterKva v1 Baseline and Golden Chain Note

## Frozen baseline

The current v1 baseline has been verified and must remain intact:

- diagnosis is separated from learning
- the system enters `explanation` after diagnosis
- `давай` is the explicit continuation trigger into practice
- `skill-aware runtime` is active
- `skill_registry.json` exists
- `skill_contracts.json` exists
- `g2_addition_core` is the active pilot
- `number_bond` is confirmed for early arithmetic
- live QA passed on the real flow

## First golden chain for v2 hardening

The first controlled v2 expansion uses the following chain:

- `g1_early_arithmetic_core`
- `g2_addition_core`

This chain is now represented explicitly in:

- `backend/data/golden_chains/g1_to_g2_addition.json`
- `tests/services/test_golden_chain_manifest.py`

## Why this chain

This is the safest first v2 target because it:

- matches the already verified early-arithmetic flow;
- uses the existing `number_bond` and `base_ten_blocks` policies;
- stays inside the smallest useful prerequisite chain;
- avoids widening scope before the core is hardened.

## Current gap

The chain is operational but still partial.
The next steps are to harden the chain with:

- more diagnostic depth;
- more remediation branches;
- strict coverage validation;
- deterministic mastery ownership in the backend.

## Rule

Do not expand beyond this chain until the golden chain is hardened and passes its coverage gate.
