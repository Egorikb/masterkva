# MasterKva Subtraction Chain Note

## Scope

This note records the next minimal chain expansion after the first golden chain.

## New chain

- `g1_early_arithmetic_core`
- `g2_subtraction_core`

## Why this chain

Subtraction is the smallest safe sibling of the already hardened addition chain. It reuses:

- part-whole reasoning
- number bonds
- backend-owned mastery evaluation
- the existing persistent student profile layer

## Implementation details

- `backend/data/golden_chains/g1_to_g2_subtraction.json`
  - new chain manifest
- `backend/data/skill_registry.json`
  - added `g2_subtraction_core` as a shadow skill
- `backend/data/skill_contracts.json`
  - added `g2_subtraction_core.v1` as a shadow partial contract
- `tests/services/test_golden_chain_manifest.py`
  - added subtraction-chain manifest validation

## What remains deferred

- runtime routing toward subtraction remains deferred
- broader grade-2 expansion remains deferred
- subtraction-specific visual fine-tuning can come after the chain is wired and validated

## Verification

- service tests passed
- api contract tests passed
- baseline addition chain remained intact
