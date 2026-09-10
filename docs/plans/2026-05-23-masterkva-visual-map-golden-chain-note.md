# MasterKva Visual Map Expansion Note

## Scope

This note records the minimal phase-8 visual-map expansion for the first golden chain only.

## Patched early-arithmetic overrides

The following grade-1 early arithmetic topics now explicitly resolve to `number_bond`:

- `СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5`
- `ЧИСЛА 6-7`
- `ЧИСЛА 8-9`

## Why this change

The early arithmetic chain should remain concrete and part-whole oriented. For these topics, `number_bond` is a better pedagogical fit than the generic полосовая модель.

## Implementation details

- `backend/data/visual_topic_map.json`
  - patched the three early-grade topics above to `visual_type: number_bond`
- `backend/deeptutor/services/visual_template_service.py`
  - added a dedicated `number_bond` blueprint template
  - ensured early arithmetic overrides are not downgraded to the simple-arithmetic fallback
- `tests/services/test_visual_template_service.py`
  - added coverage for the three early-grade topics

## What remains unchanged

- `g2_addition_core` remains on the existing place-value / base-ten path.
- diagnosis remains board-off.
- broader visual-map expansion outside the golden chain is still deferred.

## Verification

- service tests passed
- api contract tests passed
- baseline behavior remained intact
