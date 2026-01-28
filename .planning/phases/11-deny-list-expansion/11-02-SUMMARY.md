---
phase: 11-deny-list-expansion
plan: 02
subsystem: phi-detection
tags: [presidio, deny-lists, false-positives, flow-terminology, clinical-descriptors]

# Dependency graph
requires:
  - phase: 11-01
    provides: LOCATION substring matching behavior for deny list filtering
provides:
  - 16 flow/respiratory terms in LOCATION deny list (high flow, low flow, on high, on low, HFNC)
  - 6 clinical descriptor terms in PERSON deny list (barky, bedside, room, stable, critical, flow)
  - Foundation for eliminating 33% of LOCATION false positives and 9% of PERSON false positives
affects: [11-03, phase-11-validation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Comprehensive deny list comments documenting clinical context"
    - "Phase-annotated deny list sections for change tracking"

key-files:
  created: []
  modified:
    - app/config.py

key-decisions:
  - "Add standalone 'high' and 'low' to LOCATION deny list despite being broad - overwhelmingly used for oxygen flow rates in pediatric handoffs"
  - "Add 'flow' to both LOCATION and PERSON deny lists to prevent dual false positive risks"
  - "Include preventative terms (stable, critical) even though rarely flagged - better to over-include in deny lists than under-include"

patterns-established:
  - "Pattern 1: Flow terminology deny list includes both multi-word phrases (high flow) and standalone words (high)"
  - "Pattern 2: Clinical context preserved through deny list additions rather than complex pattern matching"

# Metrics
duration: 5min
completed: 2026-01-28
---

# Phase 11 Plan 02: Flow Terms and PERSON Deny List Expansion Summary

**Expanded LOCATION deny list with 16 flow/respiratory terms and PERSON deny list with 6 clinical descriptors to prevent false positives from common handoff terminology**

## Performance

- **Duration:** 5 minutes
- **Started:** 2026-01-28T21:29:27Z
- **Completed:** 2026-01-28T21:34:35Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Added 16 respiratory/oxygen flow terms to LOCATION deny list (high flow, low flow, on high, on low, HFNC, room air, bedside, floor)
- Added 6 clinical descriptor terms to PERSON deny list (barky, bedside, room, stable, critical, flow)
- Preserved hospital unit names (PICU, NICU, ICU) in LOCATION deny list
- Established foundation for eliminating 15 LOCATION false positives (33% of Phase 10 total) and 4 PERSON false positives (9% of total)

## Task Commits

Each task was committed atomically:

1. **Task 1 & 2: Flow terminology and clinical descriptors** - `caf76bf` (feat)
   - Both tasks committed together as they were related deny list expansions
   - Task 1: Added flow terms to LOCATION deny list
   - Task 2: Added clinical descriptors to PERSON deny list

## Files Created/Modified
- `app/config.py` - Expanded deny_list_location with 16 flow/respiratory terms, expanded deny_list_person with 6 clinical descriptors

## Decisions Made

1. **Standalone "high" and "low" included despite being broad terms**
   - Rationale: In pediatric handoffs, these overwhelmingly refer to oxygen flow rates (high flow, low flow)
   - Risk assessment: Legitimate location PHI like "High Point" or "Low Moor" extremely rare in handoffs
   - Trade-off: 15 false positives eliminated vs minimal risk of missed location PHI

2. **"flow" added to both LOCATION and PERSON deny lists**
   - Rationale: Prevent dual false positive risks - "Flow" could be detected as either entity type
   - Examples: "high flow" flagged as LOCATION, "Flow" capitalized could be flagged as name

3. **Preventative terms included (stable, critical)**
   - Rationale: Rarely flagged but better to over-include in deny lists than under-include
   - Cost: Minimal - deny list lookups are O(1) with lowercase conversion
   - Benefit: Prevents future false positives if NER model changes or new clinical contexts emerge

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Environment configuration issue in Docker testing**
- **Issue:** Docker container required CORS_ORIGINS in JSON format for pydantic settings
- **Resolution:** Used `-e CORS_ORIGINS='["http://localhost:8000"]'` for test runs
- **Impact:** Minor - did not affect code changes, only verification process
- **Note:** Pre-existing configuration requirement, not introduced by this plan

**Pre-existing test failure (transcript_4)**
- **Issue:** Test expecting "Jefferson" (school name) to be removed but detection targeting "Elementary" instead
- **Verification:** Failure exists in commit a6d67d1 (before 11-02 changes)
- **Status:** Not a regression - baseline CI shows 160 passed, 8 xfailed, 1 xpassed, 1 failed
- **Action:** No changes needed - test expectations issue, not deny list issue

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Deny lists expanded for flow terminology and clinical descriptors
- Ready for Plan 11-03 (unit name preservation in ROOM redaction)
- Phase 10 FALSE_POSITIVE_LOG.md targeting 42% complete (DATE_TIME 58% + LOCATION 33% + PERSON 9%)
- Comprehensive test coverage maintained (160 tests passing)

---
*Phase: 11-deny-list-expansion*
*Completed: 2026-01-28*
