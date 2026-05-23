# MasterKva Golden Chain Coverage Snapshot

## Scope
- `g1_early_arithmetic_core`
- `g2_addition_core`

## g1_early_arithmetic_core
- registry mode: shadow
- contract mode: shadow
- coverage status: partial
- diagnostics mapped: 4
- visual template: number_bond
- board policy: off
- detectable errors: carry_error, procedural_slip, visual_misread
- remediation default: number_bond
- mastery gate: `{"type": "streak", "correct": 4, "window": 5}`

## g2_addition_core
- registry mode: shadow
- contract mode: active
- coverage status: partial
- diagnostics mapped: 1
- visual template: base_ten_blocks
- board policy: off
- detectable errors: place_value_error, carry_error, procedural_slip
- remediation default: base_ten_blocks
- mastery gate: `{"type": "accuracy_over_n", "correct": 4, "window": 5}`

## Observations
- The chain is operational and already supported by live QA at the `g2_addition_core` end.
- Coverage is still partial, so the chain is not yet a fully hardened v2 segment.
- The backend-owned mastery gate for `g2_addition_core` is now explicitly tracked in state and covered by tests.
- The strongest next improvement is diagnostic breadth and remediation branching for the prerequisite skill.

## Recommended gate
- Keep the chain in controlled hardening until coverage and mastery validation are explicitly expanded.
