---
phase: 16-integration-validation
plan: 01
subsystem: testing
tags: [pytest, integration-testing, CI/CD, regression-detection, dual-weighting, validation]

# Dependency graph
requires:
  - phase: 13-test-suite-migration
    provides: Pytest-based test infrastructure for validation
  - phase: 14-report-generation
    provides: Weighted metrics calculation framework (frequency, risk)
  - phase: 15-documentation-updates
    provides: Dual-weighting methodology documentation

provides:
  - End-to-end integration test suite validating complete evaluation pipeline
  - Regression baseline with all three metric types (unweighted, frequency-weighted, risk-weighted)
  - Tiered CI workflow enforcing 85% unweighted recall floor
  - Automated detection of metric regressions before production

affects: [future-metric-changes, CI-enforcement, deployment-validation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pytest fixtures for shared validation runs (module-scoped for efficiency)"
    - "JSON baseline files for regression detection (1% tolerance)"
    - "Tiered CI: smoke tests on all PRs, full validation on main branch"
    - "Config validation tests (CONF-01, CONF-02, CONF-03 enforcement)"

key-files:
  created:
    - tests/integration/__init__.py
    - tests/integration/test_full_evaluation.py
    - tests/integration/test_regression.py
    - tests/baselines/regression.json
  modified:
    - tests/run_validation.py
    - .github/workflows/test.yml

key-decisions:
  - "Use simple JSON baseline files instead of pytest-regressions library (fewer dependencies, more control)"
  - "Module-scoped pytest fixture for validation run (efficiency - run once, test multiple assertions)"
  - "1% relative tolerance for float metric comparisons (allows bootstrap sampling variation)"
  - "Tiered CI: regression tests on all PRs, full validation only on main (balance thoroughness with CI speed)"
  - "Unweighted recall >=85% as hard CI failure (HIPAA safety floor cannot be compromised)"

patterns-established:
  - "Integration tests validate end-to-end orchestration, not individual components"
  - "Config tests verify pydantic settings load correctly (validates requirements indirectly)"
  - "Regression baselines committed to git for reproducible performance tracking"
  - "Clear error messages guide baseline update when intentional changes occur"

# Metrics
duration: 4min
completed: 2026-01-30
---

# Phase 16 Plan 01: Integration Validation Summary

**End-to-end integration test suite with regression baselines, tiered CI workflow, and 85% recall floor enforcement**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-30T19:10:37Z
- **Completed:** 2026-01-30T19:14:26Z
- **Tasks:** 3
- **Files modified:** 5
- **Commits:** 3 (all atomic, one per task)

## Accomplishments

- Extended run_validation() to return entity_stats and pre-computed weighted metrics (6 total: freq/risk × recall/precision/F2)
- Created integration test suite with 6 tests validating:
  - Three metric types calculated correctly (unweighted, frequency-weighted, risk-weighted)
  - Unweighted recall >=85% floor (HIPAA safety requirement)
  - Config weights properly loaded (validates CONF-01, CONF-02, CONF-03)
  - Entity stats provided for weighted calculations
  - Regression detection against committed baseline
- Committed regression baseline with current performance:
  - Unweighted: recall=86.41%, precision=69.01%, F2=82.26%
  - Frequency-weighted: recall=93.63%, precision=71.09%, F2=88.04%
  - Risk-weighted: recall=87.67%, precision=76.62%, F2=85.21%
- Updated CI workflow with tiered integration tests:
  - Smoke tests (test_regression.py) run on all pushes/PRs
  - Full validation (test_full_evaluation.py) runs only on main branch
  - Unweighted recall floor enforced as CI failure condition

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend run_validation.py to return weighted metrics** - `6a674f3` (feat)
   - Import settings from app.config
   - Add entity_stats dict to metrics
   - Add six pre-computed weighted metrics (freq_weighted_*, risk_weighted_*)
   - Enables integration tests to access metrics directly without reconstructing EvaluationMetrics

2. **Task 2: Create integration test infrastructure** - `2231ab6` (test)
   - Created tests/integration/ directory with __init__.py
   - Created test_full_evaluation.py with 4 tests (dataset validation, three metrics, config weights, entity stats)
   - Created test_regression.py with 2 tests (recall floor, baseline comparison)
   - Used module-scoped pytest fixtures for efficiency
   - All tests validate CONF-01, CONF-02, CONF-03 requirements indirectly

3. **Task 3: Create regression baseline and CI workflow** - `fccea26` (test)
   - Generated baseline from current validation run (1000 bootstrap iterations)
   - Created tests/baselines/regression.json with all metrics (20 values)
   - Updated .github/workflows/test.yml with tiered integration steps
   - All 6 integration tests now pass (0 skipped)

## Files Created/Modified

### Created
- `tests/integration/__init__.py` - Package initialization for integration tests
- `tests/integration/test_full_evaluation.py` - End-to-end validation orchestration tests (4 tests, 130 lines)
- `tests/integration/test_regression.py` - Regression detection with baseline comparison (2 tests, 90 lines)
- `tests/baselines/regression.json` - Committed baseline metrics for regression detection

### Modified
- `tests/run_validation.py` - Extended to return entity_stats and pre-computed weighted metrics
- `.github/workflows/test.yml` - Added tiered integration test steps (smoke on all PRs, full on main)

## Decisions Made

1. **Simple JSON baselines over pytest-regressions library** - Fewer dependencies, more explicit control, easier to understand for medical domain users

2. **Module-scoped fixture for validation run** - Run validation once per test file, share results across tests. Faster execution (12s vs 25s+ if each test ran separately)

3. **1% relative tolerance for metric comparisons** - Allows natural bootstrap sampling variation without spurious failures. Tight enough to catch real regressions.

4. **Tiered CI workflow** - Balance thoroughness with CI speed:
   - Smoke tests (regression) on every PR: catches recall floor violations immediately
   - Full validation only on main: comprehensive checks after merge, no PR slowdown

5. **Config validation via test_config_weights_loaded()** - Validates CONF-01, CONF-02, CONF-03 indirectly by checking settings object. More maintainable than hardcoded assertions on dict contents.

## Deviations from Plan

None - plan executed exactly as written.

All requirements delivered:
- ✅ run_validation() returns entity_stats and weighted metrics
- ✅ Integration tests validate three metric types from returned dict
- ✅ Unweighted recall >=85% floor enforced
- ✅ Config weights validated (CONF-01, CONF-02, CONF-03)
- ✅ Regression baseline committed with all metrics
- ✅ CI workflow updated with tiered integration tests
- ✅ All integration tests pass locally

## Issues Encountered

None - execution was smooth.

Initial attempt to run validation without activating venv hit numpy version incompatibility, but switching to `source venv/bin/activate` resolved it immediately. All other operations worked as expected.

## User Setup Required

None - no external service configuration required.

Integration tests run automatically in CI. Developers can run locally with:
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run just smoke tests (quick check)
pytest tests/integration/test_regression.py -v

# Run just full validation
pytest tests/integration/test_full_evaluation.py -v
```

To update baseline after intentional changes:
```bash
python -c "from tests.run_validation import run_validation; from pathlib import Path; import json; r = run_validation(Path('tests/synthetic_handoffs.json'), n_bootstrap=1000, verbose=False); b = {k: round(v, 4) for k, v in r['metrics'].items() if isinstance(v, (int, float))}; Path('tests/baselines/regression.json').write_text(json.dumps(b, indent=2, sort_keys=True))"
```

## Next Phase Readiness

Phase 16 complete - v2.2 Dual-Weight Recall Framework fully delivered.

**v2.2 shipping criteria met:**
- ✅ Test suite migrated to per-entity tracking (Phase 13)
- ✅ Report generation refined with dual-weight tables (Phase 14)
- ✅ Dual-weighting methodology documented (Phase 15)
- ✅ Integration validation suite operational (Phase 16)

**Key artifacts ready for deployment:**
- run_validation.py orchestrates complete evaluation pipeline
- Weighted metrics calculated automatically (frequency, risk)
- Reports show side-by-side weight schemes with divergence marking
- Integration tests catch regressions before production
- CI enforces 85% recall floor as HIPAA safety requirement

**Zero-weight entity safety validated:**
EMAIL_ADDRESS and PEDIATRIC_AGE (both weight=0.0) are invisible in weighted metrics but still protected by unweighted recall floor. Integration tests explicitly validate this (test_unweighted_recall_floor with clear error message explaining why weighted metrics cannot replace unweighted).

**No blockers.** System is production-ready for v2.2 release.

---
*Phase: 16-integration-validation*
*Completed: 2026-01-30*
