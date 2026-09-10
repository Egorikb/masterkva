# MasterKva Golden Chain QA Gap Report

## Scope

This note covers the first v2 golden chain:

- `g1_early_arithmetic_core`
- `g2_addition_core`

The purpose is to document what is already strong in this chain and what still needs to be completed before the chain can be considered fully hardened.

## What is already strong

### g1_early_arithmetic_core
- registry entry exists
- contract exists
- diagnostic items exist for the mapped topics
- visual policy is defined as `number_bond`
- board policy is `off`
- remediation path is explicit
- the skill is suitable as the grade-1 foundation of the chain

### g2_addition_core
- registry entry exists
- contract exists
- diagnostic item exists
- active pilot is already enabled
- visual policy is defined as `base_ten_blocks`
- board policy is `off`
- live QA has already validated the flow on this skill

## Observed gaps

### 1. Coverage is still partial
The contracts for both skills are marked as `partial`, even though the runtime path is already usable.

This means:
- the chain is operational;
- the chain is not yet fully hardened as a complete curriculum segment.

### 2. Diagnostic breadth is still thin
Current diagnostic pool coverage for the golden chain is still limited:
- grade 1 has only a small set of topic-linked items;
- grade 2 has only one diagnostic question in the current pool.

This is enough for a pilot, but not enough for a fully stable coverage-run.

### 3. Remediation needs more structured variants
The chain already has a default remediation path, but the remediation layer still needs:
- clearer error branching;
- stronger distinction between computational, conceptual, and procedural failures;
- more explicit retry boundaries.

### 4. Coverage-run is not yet a strict gate for this chain
The chain can run, but the project still needs the stronger rule:

- if coverage is incomplete, the skill should not be promoted beyond its current safe mode.

## Recommended next actions for this chain

1. Expand the diagnostic set for `g1_early_arithmetic_core` and `g2_addition_core`.
2. Add remediation variants for the most likely error types.
3. Define completion criteria for each skill inside the contract.
4. Add a repeatable coverage-run specifically for the golden chain.
5. Keep `g3_time_measurement_core` out of the first hardening wave until the first chain is fully stable.

## Conclusion

The first golden chain is the right starting point for v2:

- it is already the most validated part of the system;
- it matches the current live behavior;
- it has the clearest visual policy;
- it is small enough to harden properly before scale-up.

The main remaining work is not architectural invention. It is coverage hardening: more diagnostic depth, more remediation specificity, and a strict quality gate before any broader expansion.
