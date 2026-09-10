# MasterKva mastery gate hardening note

## Scope
- `g2_addition_core`
- backend-owned mastery gate path

## What was hardened
- mastery decisions are now recorded explicitly in skill runtime state;
- `mastery_gate_status` is stored alongside `mastery_check_result`;
- `promotion_eligible` and `mastery_check_pending` are derived from the backend evaluator, not from LLM text;
- the `mastery_check` phase now distinguishes `mastered` from blocked decisions.

## QA coverage
- verified `mastered` path with a full five-attempt window;
- verified `insufficient_evidence` stays closed;
- verified chain-level regression stays green.

## Rule
- do not widen beyond the golden chain while the gate is still being hardened.
