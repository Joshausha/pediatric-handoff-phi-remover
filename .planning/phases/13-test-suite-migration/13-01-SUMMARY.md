---
phase: 13-test-suite-migration
plan: 01
subsystem: testing
tags: [tests, weighted-metrics, float-weights, risk-weights, dual-weighting]

dependency_graph:
  requires: [08-weighted-recall-evaluation]
  provides: [complete-test-coverage-dual-weights]
  affects: [14-report-generation, 16-integration-validation]

tech_stack:
  added: []
  patterns: [pytest.approx-for-floats, dual-weight-testing]

key_files:
  created: []
  modified:
    - tests/test_weighted_metrics.py

decisions:
  - id: TEST-FLOAT-COMPARISON
    choice: "Use pytest.approx() for all float weight comparisons"
    rationale: "Float comparison with == can fail due to floating point precision"
  - id: TEST-DIVERGENCE-VALIDATION
    choice: "Add explicit tests for frequency vs risk weight divergence"
    rationale: "Core value proposition of dual-weighting is that they CAN diverge - must test this"

metrics:
  duration: "2 minutes 26 seconds"
  completed: "2026-01-29"
---

# Phase 13 Plan 01: Test Suite Migration Summary

**One-liner:** Migrated weighted metrics tests from int to float, added risk-weighted and divergence tests

## What Was Done

### Task 1: Fix existing failing tests for float weights
- Updated `test_weight_values_in_valid_range` to accept `(int, float)` instead of `int`
- Updated `test_critical_entities_have_high_weights` with `pytest.approx()` assertions
- Renamed `test_never_spoken_entities_have_zero_weight` to `test_rarely_or_never_spoken_entities_have_low_weights`
- Updated assertions to match current config values (GUARDIAN_NAME=4.0, LOCATION=0.5)

### Task 2: Add risk-weighted metric tests
Added `TestRiskWeightedMetrics` class with 5 tests:
- `test_risk_weighted_recall_calculation` - validates risk-weighted recall with manual calculation
- `test_risk_weighted_precision_calculation` - validates risk-weighted precision
- `test_risk_weighted_f2_calculation` - validates risk-weighted F2 score
- `test_risk_weights_loaded_from_config` - verifies all entities have risk weights
- `test_risk_weight_values_in_valid_range` - validates risk weights 0.0-5.0

### Task 3: Add frequency vs risk divergence validation tests
Added `TestWeightDivergence` class with 4 tests:
- `test_mixed_entities_frequency_vs_risk_divergence` - proves frequency and risk CAN produce different values
- `test_zero_weight_entities_invisible_in_weighted_visible_in_unweighted` - HIPAA safety check
- `test_actual_config_weights_show_expected_divergence_pattern` - uses real config values
- `test_all_zero_weights_return_zero` - edge case: no division by zero

## Key Outcomes

| Metric | Before | After |
|--------|--------|-------|
| Total tests | 11 | 20 |
| Passing tests | 8 | 20 |
| Failing tests | 3 | 0 |
| Test file lines | ~250 | 500 |
| Execution time | 0.25s | 0.18s |

## Test Classes Summary

| Class | Tests | Purpose |
|-------|-------|---------|
| TestWeightedMetrics | 7 | Frequency-weighted metric calculations |
| TestWeightConfiguration | 4 | Config validation for frequency weights |
| TestRiskWeightedMetrics | 5 | Risk-weighted metric calculations |
| TestWeightDivergence | 4 | Validates dual-weight divergence behavior |

## Success Criteria Verification

- [x] TEST-01: Existing weighted metric tests pass with float weights
- [x] TEST-02: Risk-weighted recall calculation has test coverage
- [x] TEST-03: Risk-weighted precision calculation has test coverage
- [x] TEST-04: Risk-weighted F2 calculation has test coverage
- [x] TEST-05: Float assertions use tolerance (pytest.approx)
- [x] TEST-06: Test validates frequency vs risk weight divergence behavior

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Hash | Message |
|------|---------|
| 7051a9d | fix(13-01): update weight tests for float weights |
| 4449d9f | test(13-01): add risk-weighted metrics test class |
| 8e648ec | test(13-01): add frequency vs risk divergence tests |

## Files Modified

- `tests/test_weighted_metrics.py` - Added 2 new test classes, fixed 3 failing tests

## Next Phase Readiness

Phase 14 (Report Generation Refinement) can proceed:
- All weighted metric methods have test coverage
- Dual-weight calculation behavior is validated
- Config validation ensures weights are properly loaded

No blockers identified.
