---
phase: 03-deny-list-refinement
plan: 02
subsystem: phi-detection
tags: [presidio, deny-lists, testing, regression-tests, precision-measurement]

# Dependency graph
requires:
  - phase: 03-01
    provides: "Case-insensitive deny list filtering in production code"
provides:
  - "Test files mirror production deny list filtering (evaluate_presidio.py, calibrate_thresholds.py)"
  - "Regression test suite for deny list filtering (33 parameterized tests)"
  - "Phase 03 precision improvement metrics documented in BASELINE_METRICS.md"
affects: [03-03-measurement, phase-04-pattern-improvements]

# Tech tracking
tech-stack:
  added: []
  patterns: ["pytest.mark.parametrize for comprehensive deny list testing"]

key-files:
  created: []
  modified:
    - tests/evaluate_presidio.py
    - tests/calibrate_thresholds.py
    - tests/test_deidentification.py
    - .planning/phases/01-baseline-measurement/BASELINE_METRICS.md

key-decisions:
  - "Test files intentionally duplicate deny list filtering logic (Maintains test isolation and keeps evaluation/calibration scripts self-contained)"
  - "DENY-04 targets not met via deny lists alone (4.1% FP reduction vs 20% target; deny lists preventative not corrective)"
  - "Documented gap analysis for unmet targets (Most false positives require Phase 4 pattern refinement, not deny list expansion)"

patterns-established:
  - "Regression test pattern: pytest.mark.parametrize for case variant testing"
  - "Per-phase metrics appended to BASELINE_METRICS.md (preserves baseline, tracks progress)"

# Metrics
duration: 3min
completed: 2026-01-24
---

# Phase 03 Plan 02: Test File Deny List Mirroring & Precision Measurement Summary

**Test files updated with consistent deny list filtering, regression tests added, precision improvement measured and documented**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-24T01:23:05Z
- **Completed:** 2026-01-24T01:26:02Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- Fixed LOCATION deny list case-insensitive matching in evaluate_presidio.py and calibrate_thresholds.py
- Added GUARDIAN_NAME, PEDIATRIC_AGE, DATE_TIME deny list filtering to test files
- Created TestDenyListFiltering regression test class with 33 parameterized tests (all passing)
- Measured precision improvement: 66.3% → 67.2% (+0.9%)
- Documented Phase 03 metrics and gap analysis in BASELINE_METRICS.md

## Task Commits

Each task was committed atomically:

1. **Task 1-2: Update deny list filtering in test files** - `a8d7838` (fix)
2. **Task 3: Add regression tests** - `4dec18c` (test)
3. **Task 4: Measure and document precision improvement** - `5df2285` (docs)

## Files Created/Modified

- `tests/evaluate_presidio.py` - Fixed LOCATION case-insensitive bug, added GUARDIAN_NAME/PEDIATRIC_AGE/DATE_TIME deny list filtering
- `tests/calibrate_thresholds.py` - Fixed LOCATION case-insensitive bug, added GUARDIAN_NAME/PEDIATRIC_AGE/DATE_TIME deny list filtering
- `tests/test_deidentification.py` - Added TestDenyListFiltering class with 33 regression tests
- `.planning/phases/01-baseline-measurement/BASELINE_METRICS.md` - Appended Phase 03 precision metrics and gap analysis

## Decisions Made

1. **Test file deny list duplication** - Test files intentionally duplicate deny list filtering logic from production code to maintain test isolation and keep evaluation/calibration scripts self-contained
2. **DENY-04 targets not met via deny lists alone** - 4.1% false positive reduction vs 20% target; deny lists are preventative (filter known safe terms) not corrective (fix pattern weaknesses)
3. **Gap analysis documentation** - Documented why targets not met: most false positives require Phase 4 pattern refinement, not deny list expansion

## Deviations from Plan

None - plan executed exactly as written

## Precision Improvement Results

### Overall Metrics
| Metric | Baseline (Phase 01) | Post-Phase 03 | Change |
|--------|---------------------|---------------|--------|
| Overall Precision | 66.3% | 67.2% | +0.9% |
| False Positives | 662 | 635 | -27 (-4.1%) |
| LOCATION Precision | 80.6% | 81% | +0.4% |
| DATE_TIME Precision | 35.5% | 37% | +1.5% |

### DENY-04 Requirement Status
- **False positive reduction >20%**: ❌ NOT MET (actual: 4.1%)
- **Precision toward 90%**: ❌ NOT MET (actual: 67.2%, +0.9% improvement)

### Gap Analysis
**Why targets not met:**
1. **Deny list impact limited**: Only 27 of 662 false positives (4.1%) were filterable via deny lists
2. **Most FPs are over-detections**: Remaining 635 false positives require pattern refinement (Phase 4)
3. **DATE_TIME precision remains low (37%)**: Dosing schedule deny list helped (+1.5%), but core issue is over-detection of clinical timestamps
4. **Deny lists are preventative, not corrective**: Prevent FPs on known safe terms, don't fix existing pattern weaknesses (PEDIATRIC_AGE 36.6% recall, ROOM 34.4% recall)

**Conclusion**: Deny list refinement achieved modest precision gains (+0.9%). Phase 4 pattern improvements required for significant precision/recall improvements toward 90% target.

## Regression Test Coverage

### TestDenyListFiltering (33 tests, all passing)
- **LOCATION deny list** (13 tests): NC, nc, Nc, RA, ra, OR, or, ER, er, IV, iv, PO, po
- **PERSON deny list** (8 tests): mom, Mom, MOM, dad, Dad, nurse, doctor, guardian
- **DATE_TIME deny list** (12 tests): BID, bid, TID, tid, QID, qid, PRN, prn, q4h, Q4H, daily, nightly

All tests verify case-insensitive matching and prevention of false positive redactions.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required

## Next Phase Readiness

**Ready for 03-03 (Measurement):**
- Test files use consistent deny list filtering with production code
- Regression tests in place to prevent future deny list regressions
- Phase 03 precision metrics documented

**Ready for Phase 4 (Pattern Improvements):**
- Baseline metrics updated with Phase 03 results
- Gap analysis clearly identifies pattern improvements as primary lever for precision/recall gains
- Deny list infrastructure solid (case-insensitive, comprehensive coverage)

**Concerns:**
- DENY-04 targets not met via deny lists alone (expected - deny lists have limited impact)
- Phase 4 pattern improvements critical for reaching 90% precision/recall targets

---
*Phase: 03-deny-list-refinement*
*Completed: 2026-01-24*
