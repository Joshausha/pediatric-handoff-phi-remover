---
phase: 11-deny-list-expansion
plan: 01
subsystem: phi-detection
tags: [presidio, deny-list, date-time, location, false-positives]

# Dependency graph
requires:
  - phase: 10-test-script-generation
    provides: FALSE_POSITIVE_LOG.md with 26 DATE_TIME and 15 LOCATION false positives
provides:
  - 70+ duration patterns in DATE_TIME deny list
  - Word-boundary substring matching for LOCATION deny list
  - Zero false positives for duration phrases (58% of total false positives eliminated)
affects: [11-02-flow-terms-location]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Word-boundary regex matching for deny lists to prevent substring false positives"
    - "Organized deny list with categorized sections and comments"

key-files:
  created: []
  modified:
    - app/config.py
    - app/deidentification.py

key-decisions:
  - "Used word-boundary regex matching for LOCATION deny list to prevent ER matching Jefferson"
  - "Added 70+ duration patterns covering all 26 documented DATE_TIME false positives from Phase 10"
  - "Favored recall over precision for duration patterns - acceptable to block true dates since handoffs rarely contain calendar dates"

patterns-established:
  - "Deny list organization: group patterns by category with comments for maintainability"
  - "Word boundary matching using \\b regex anchors for medical abbreviations"

# Metrics
duration: 6min
completed: 2026-01-28
---

# Phase 11 Plan 01: Duration Patterns and Matching Behavior Fix

**Eliminated 58% of false positives (26 DATE_TIME cases) via comprehensive duration patterns and fixed LOCATION deny list with word-boundary matching**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-28T21:18:47Z
- **Completed:** 2026-01-28T21:25:32Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Added 70+ duration patterns to DATE_TIME deny list (simple, numeric, informal, ranges, clinical percentages)
- Fixed LOCATION deny list matching from exact match to word-boundary substring match
- Prevented false positives like "ER" matching "Jefferson" while preserving NC/RA/OR filtering
- All 161 tests pass with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add comprehensive duration patterns to DATE_TIME deny list** - `aced0fd` (feat)
2. **Task 2: Switch LOCATION deny list to word-boundary substring matching** - `2dfb21d` (fix) - *amended from 9e84d44*
3. **Task 3: Run full test suite to verify no regressions** - `a6d67d1` (test)

_Note: Task 2 was amended after discovering word-boundary requirement_

## Files Created/Modified
- `app/config.py` - Added 70+ duration patterns organized in sections (simple, numeric, informal, ranges, clinical)
- `app/deidentification.py` - Changed LOCATION deny list from exact match to word-boundary regex matching

## Decisions Made

**Word-boundary regex matching for LOCATION deny list:**
- Rationale: Simple substring matching caused "ER" to match "Jefferson", filtering out valid PHI detection
- Solution: Use `\b` word boundaries with `re.search()` to ensure abbreviations only match whole words
- Example: "ER" matches "patient in ER" but not "goes to Jefferson"

**Comprehensive duration pattern coverage:**
- Added 70+ patterns across all categories to eliminate 26 documented DATE_TIME false positives
- Categories: simple duration (one day, two hours), numeric (24 hours, 48 hours), informal (a few days), ranges (two to three days), clinical percentages (mid-90s), dosing counts (4 doses)
- Cross-referenced against Phase 10 FALSE_POSITIVE_LOG.md to ensure complete coverage

**Recall over precision for duration patterns:**
- Decision: Favor blocking duration phrases even if occasionally blocks true dates
- Rationale: Handoffs rarely contain actual calendar dates; clinical timelines (day 4, three days ago) are not PHI
- Impact: Zero duration false positives in test suite

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Word boundary matching required for LOCATION deny list**
- **Found during:** Task 2 verification (transcript_4 test failure)
- **Issue:** Simple substring matching caused "ER" to match "Jefferson Elementary", filtering out valid PHI
- **Fix:** Changed from `term.lower() in detected_lower` to `re.search(r'\b' + re.escape(term.lower()) + r'\b', detected_lower)`
- **Files modified:** app/deidentification.py (added `import re`, updated LOCATION deny list logic)
- **Verification:** "Jefferson Elementary" correctly detected, "patient on NC oxygen" still filtered
- **Committed in:** 2dfb21d (amended Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Critical fix for correct PHI detection. Plan specified "word-boundary substring matching" but initial implementation used simple substring matching. Bug found via test failure and fixed immediately.

## Issues Encountered
None - all tasks completed as planned after word-boundary bug fix.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness

**Ready for Plan 11-02 (Flow Terms - LOCATION):**
- LOCATION deny list now uses word-boundary matching (DENY-03 resolved)
- Ready to add flow terms (high flow, low flow, room air) without false positives
- Remaining false positives: 15 LOCATION (33%), 4 PERSON (9%)

**Wave 1 complete:**
- DATE_TIME false positives eliminated (58% → 0%)
- LOCATION matching behavior fixed
- Wave 2 can proceed with flow terms and relationship words

---
*Phase: 11-deny-list-expansion*
*Completed: 2026-01-28*
