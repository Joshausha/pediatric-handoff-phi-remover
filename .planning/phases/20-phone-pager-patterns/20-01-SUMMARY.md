---
phase: 20-phone-pager-patterns
plan: 01
subsystem: phi-detection
tags: [presidio, phone-detection, phonenumbers, leniency, recall]

# Dependency graph
requires:
  - phase: 12-regression-validation
    provides: Baseline metrics and validation framework
provides:
  - PHONE_NUMBER recall improvement from 75.7% to 100%
  - Custom PhoneRecognizer with leniency=0 for lenient matching
  - 5 new regression tests for phone edge cases
affects: [22-validation-recall-targets, recall-improvements]

# Tech tracking
tech-stack:
  added: []  # No new libraries, configuration change only
  patterns:
    - "Override predefined Presidio recognizers via registry.remove_recognizer() then registry.add_recognizer()"
    - "Use leniency=0 for phonenumbers library in clinical contexts where formatting varies"

key-files:
  created: []
  modified:
    - app/deidentification.py
    - tests/test_deidentification.py

key-decisions:
  - "PHONE-LENIENCY-0: Use leniency=0 (most lenient) for PhoneRecognizer to catch all valid formats including extensions and standard dash-separated numbers"
  - "PHONE-REGISTRY-OVERRIDE: Remove default PhoneRecognizer before adding custom one to prevent duplicate entities"

patterns-established:
  - "Presidio recognizer override pattern: registry.remove_recognizer(name) → create custom → registry.add_recognizer(custom)"

# Metrics
duration: 3min
completed: 2026-01-31
---

# Phase 20 Plan 01: Phone Leniency Override Summary

**PHONE_NUMBER recall improved from 75.7% to 100% by switching Presidio PhoneRecognizer to leniency=0**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-31T02:47:36Z
- **Completed:** 2026-01-31T02:50:38Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- PHONE_NUMBER recall improved from 75.7% to 100% (exceeds 90% target)
- All 5 known false negatives now detected (extensions and standard dash-separated formats)
- No false positives on clinical numbers (vitals, weights, doses)
- 234 tests pass with no regressions on other entity types

## Task Commits

Each task was committed atomically:

1. **Task 1: Override PhoneRecognizer with leniency=0** - `6a2757c` (feat)
2. **Task 2: Add regression tests and validate recall** - `542348b` (test)

## Files Created/Modified
- `app/deidentification.py` - Added PhoneRecognizer import, removed default recognizer, added custom with leniency=0
- `tests/test_deidentification.py` - Added 5 Phase 20 test cases to PHONE_NUMBER_EDGE_CASES list

## Decisions Made

**PHONE-LENIENCY-0:** Changed from Presidio's default leniency=1 (VALID) to leniency=0 (POSSIBLE) for PhoneRecognizer. The default leniency level requires strict format validation, which is too strict for transcribed clinical handoffs where formatting varies. Leniency=0 catches all valid phone formats including:
- Extensions with "x" suffix (264-517-0805x310)
- Standard dash-separated without extension (576-959-1803)
- Long extensions (394-678-7300x2447)

**PHONE-REGISTRY-OVERRIDE:** Must call `registry.remove_recognizer("PhoneRecognizer")` before adding custom PhoneRecognizer to prevent duplicate entity detection at the same position. This is the standard pattern for overriding Presidio's predefined recognizers.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation was straightforward. The phonenumbers library with leniency=0 immediately fixed all 5 known false negatives without any false positives.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

PHONE_NUMBER detection now exceeds recall target (100% vs 90% goal). Ready for:
- Phase 21: Location/Transfer Patterns (parallel execution possible)
- Phase 22: Validation & Recall Targets (final end-to-end validation)

The test suite change from XFAIL to XPASS on `test_bulk_phone_detection` indicates the improvement was even better than expected - the phone detection now passes tests that were previously marked as expected failures.

---
*Phase: 20-phone-pager-patterns*
*Completed: 2026-01-31*
