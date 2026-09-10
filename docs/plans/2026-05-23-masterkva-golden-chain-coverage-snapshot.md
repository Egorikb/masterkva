# MasterKva Golden Chain Coverage Snapshot

## Scope
- `g1_early_arithmetic_core`
- `g2_addition_core`

## Baseline status
- v2 golden-chain baseline: frozen
- release gate: passing
- rollback target: `b974cbb`

## g1_early_arithmetic_core
- registry mode: shadow
- contract mode: shadow
- coverage status: partial
- visual template: number_bond
- board policy: off
- remediation default: number_bond
- mastery gate: backend-owned streak gate

## g2_addition_core
- registry mode: shadow
- contract mode: active
- coverage status: partial
- visual template: base_ten_blocks
- board policy: off
- remediation default: base_ten_blocks
- mastery gate: backend-owned accuracy gate

## Observations
- The chain is operational, hardened, and now frozen as the v2 golden-chain baseline.
- Release-gate acceptance covers diagnosis, explanation, `давай`, remediation, mastery check, promotion, and persistent profile updates.
- Coverage remains partial, so this is a stable baseline rather than full curriculum coverage.
- The next roadmap work should build from this frozen baseline without changing the release-gate contract.

## Recommended gate
- Keep the chain fixed as the rollback target while future roadmap steps extend coverage and curriculum structure.
