---
phase: 03-deny-list-refinement
plan: 01
subsystem: phi-detection
tags: [presidio, deny-lists, false-positives, case-insensitive]

# Dependency graph
requires:
  - phase: 02-threshold-calibration
    provides: "Per-entity threshold calibration and baseline metrics"
provides:
  - "Case-insensitive deny list filtering for all entity types"
  - "Deny lists for DATE_TIME (dosing schedules), GUARDIAN_NAME (generic relationships), PEDIATRIC_AGE (age categories)"
  - "Consistent deny list pattern across LOCATION, PERSON, GUARDIAN_NAME, PEDIATRIC_AGE, DATE_TIME"
affects: [03-02-expand-deny-lists, 03-03-measurement, phase-04-pattern-improvements]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Case-insensitive deny list filtering pattern"]

key-files:
  created: []
  modified: [app/config.py, app/deidentification.py]

key-decisions:
  - "Case-insensitive deny lists (Consistency prevents edge case bugs; clinical terms appear in various cases)"
  - "Dosing schedules in DATE_TIME deny list (Reduces precision drop from 35.3% by filtering clinical abbreviations)"
  - "Generic age categories in PEDIATRIC_AGE deny list (Prevents over-redaction of clinical descriptors)"

patterns-established:
  - "Deny list filtering: detected_text.lower() in [w.lower() for w in deny_list]"
  - "Deny lists for all custom entity types (GUARDIAN_NAME, PEDIATRIC_AGE, DATE_TIME)"

# Metrics
duration: 2min
completed: 2026-01-24
---

# Phase 03 Plan 01: Deny List Refinement Summary

**Case-insensitive deny list filtering across all entity types with medical abbreviation filters for DATE_TIME, GUARDIAN_NAME, PEDIATRIC_AGE**

## Performance

- **Duration:** 2 min
- **Started:** 2026-01-24T01:17:24Z
- **Completed:** 2026-01-24T01:19:14Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Fixed LOCATION deny list case-insensitive bug (NC, nc, Nc all filtered correctly)
- Added deny_list_date_time filtering dosing schedules (q4h, BID, PRN, etc.)
- Added deny_list_guardian_name filtering generic relationship terms
- Added deny_list_pediatric_age filtering generic age categories
- Established consistent case-insensitive deny list pattern across all entity types

## Task Commits

Each task was committed atomically:

1. **Task 1: Add new deny lists to config.py** - `fed738a` (feat)
2. **Task 2: Fix LOCATION case-insensitive bug and add deny list filtering** - `f4c76ae` (fix)

## Files Created/Modified

- `app/config.py` - Added deny_list_guardian_name, deny_list_pediatric_age, deny_list_date_time; removed redundant capitalized Mom/Dad
- `app/deidentification.py` - Fixed LOCATION deny list to case-insensitive; added GUARDIAN_NAME, PEDIATRIC_AGE, DATE_TIME deny list filtering

## Decisions Made

1. **Case-insensitive deny lists** - Ensures consistency and prevents edge case bugs where medical abbreviations appear in various cases
2. **Dosing schedule deny list** - Addresses DATE_TIME low precision (35.3%) by filtering clinical abbreviations that are not PHI
3. **Generic age category deny list** - Prevents over-redaction of clinical descriptors like "infant" or "toddler"
4. **Removed redundant capitalized variants** - Mom/Dad duplicates removed from deny_list_person since case-insensitive matching handles all variants

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered

- **Numpy compatibility error in system Python**: Resolved by using project venv which has correct dependency versions
- **Environment dependency mismatch**: Not a code issue; verification tests pass in venv environment

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for 03-02 (Expand Deny Lists):**
- Case-insensitive deny list pattern established and tested
- Baseline deny lists in place for all entity types
- Framework supports easy addition of new deny list terms

**Ready for 03-03 (Measurement):**
- All deny list filtering operational
- Can measure false positive reduction impact

**Concerns:**
- DATE_TIME precision still low (35.3%) - more aggressive deny list expansion needed in 03-02
- LOCATION precision moderate (70.3%) - deny list expansion may help slightly but pattern improvements (Phase 4) will be primary solution

---
*Phase: 03-deny-list-refinement*
*Completed: 2026-01-24*
