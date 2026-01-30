---
phase: 17-room-pattern-expansion
plan: 03
subsystem: phi-detection
tags: [presidio, regex, patterns, lookbehind, overlap-analysis]

# Dependency graph
requires:
  - phase: 17-02
    provides: ROOM precision fixed (17% → 49%) via street address negatives
provides:
  - Number-only ROOM patterns using lookbehind (match "7" not "bed 7")
  - Overlap analysis diagnostic test quantifying partial match impact
  - Documented interim 55% target with Phase 22 finalization commitment
  - Achieved 98% recall (far exceeding 55% target and original 80% goal)
affects: [phase-22-validation, precision-recall-balance]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lookbehind patterns for number-only matching ((?<=context\\s)\\d+)"
    - "Pattern priority via scoring (number-only 0.70, full-match 0.50)"
    - "Overlap analysis via exact/partial/missed classification"

key-files:
  created:
    - .planning/phases/17-room-pattern-expansion/17-03-SUMMARY.md
  modified:
    - app/recognizers/medical.py
    - tests/test_deidentification.py
    - .planning/ROADMAP.md

key-decisions:
  - "Use lookbehind patterns to match only numbers, not full phrases (aligns with ground truth)"
  - "Lower full-match pattern scores to 0.50 so number-only patterns take priority"
  - "Document 55% as interim target, defer final validation to Phase 22"
  - "Keep diagnostic test for future pattern analysis"

patterns-established:
  - "Number-only ROOM patterns: (?i)(?<=\\broom\\s)\\d{1,4}[A-Za-z]?\\b"
  - "ICU bed patterns updated: (?i)(?<=picu bed )\\d{1,3}[A-Za-z]?\\b"
  - "Diagnostic test pattern: exact/partial/missed classification with overlap rate calculation"

# Metrics
duration: 35min
completed: 2026-01-30
---

# Phase 17-03: Room Pattern Expansion Summary

**Number-only ROOM patterns using lookbehind achieve 98% recall (2% overlap) by aligning detections with ground truth format**

## Performance

- **Duration:** 35 min
- **Started:** 2026-01-30T20:40:50Z
- **Completed:** 2026-01-30T21:15:50Z (estimated)
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Quantified overlap matching impact: 55.1% partial matches inflating both FP and FN counts
- Added number-only patterns that match just the room number (not "bed 847", just "847")
- Achieved 98% exact match rate (up from 36.7%) and 100% effective recall
- ROOM recall: 98% on synthetic dataset (far exceeding 55% interim target)
- ROOM precision: 52% on full evaluation (exceeds 40% target from Plan 02)
- Documented interim target with Phase 22 finalization commitment

## Task Commits

Each task was committed atomically:

1. **Task 1: Analyze Overlap Matching Impact** - `5a960a4` (test)
   - Added diagnostic test to quantify overlap rate
   - Result: 55.1% partial matches, 91.8% effective recall

2. **Task 2: Add Number-Only Room Patterns** - `897d51d` (feat)
   - Added lookbehind patterns matching only numbers
   - Updated ICU bed patterns to match only number portion
   - Lowered full-match pattern scores (0.70 → 0.50)
   - Result: 98% exact matches, 2% overlap rate

3. **Task 3: Document Interim Recall Target** - `4ed282d` (docs)
   - Updated ROADMAP.md Phase 17 goal
   - Updated test docstring with target history
   - Verified Phase 22 has finalization commitment

## Files Created/Modified
- `tests/test_deidentification.py` - Added diagnostic test test_room_overlap_analysis, updated test_room_recall_improved docstring
- `app/recognizers/medical.py` - Added 8 number-only patterns, updated 7 ICU bed patterns, lowered 4 full-match scores
- `.planning/ROADMAP.md` - Updated Phase 17 goal, marked all plans complete

## Decisions Made

**1. Use lookbehind patterns for number-only matching**
- Rationale: Ground truth expects "847" not "bed 847", lookbehind requires context but doesn't include it
- Example: `(?i)(?<=\bbed\s)\d{1,4}[A-Za-z]?\b` matches "7" in "bed 7"
- Alternative considered: Capture groups (Presidio uses full match, so rejected)

**2. Lower full-match pattern scores instead of removing them**
- Rationale: Keep as fallback for edge cases where lookbehind might fail
- Implementation: 0.70 → 0.50 for room_standard, bed_standard, bay_number, isolette_number
- Result: Number-only patterns (0.70) take priority over full-match patterns (0.50)

**3. Document 55% as interim target, defer finalization to Phase 22**
- Rationale: Achieved 98% exceeds all targets, but pattern-based approach has inherent limits
- Phase 22 will validate across all entity types and make final recall target decisions
- Audit trail preserved: original 80% → revised 55% → achieved 98%

**4. Keep diagnostic test for future analysis**
- Rationale: Useful for understanding overlap behavior in other entity types
- Marked with `@pytest.mark.diagnostic` for optional execution
- Provides template for overlap analysis pattern

## Deviations from Plan

None - plan executed exactly as written.

All diagnostic findings, pattern additions, and documentation updates followed plan specifications.

## Issues Encountered

**Issue: Initial lookbehind patterns didn't take priority**
- Problem: Full-match patterns (score 0.70) still winning over number-only patterns (score 0.70)
- Cause: Presidio takes longest match when scores are equal
- Resolution: Lowered full-match pattern scores to 0.50, number-only patterns now take priority
- Verification: Overlap rate dropped from 55.1% to 2.0%

## Overlap Analysis Results

**Before number-only patterns:**
- Exact matches: 36.7% (18/49)
- Partial matches: 55.1% (27/49) - "bed 847" detected, "847" in ground truth
- Missed: 8.2% (4/49)
- Effective recall: 91.8%

**After number-only patterns:**
- Exact matches: 98.0% (48/49)
- Partial matches: 2.0% (1/49)
- Missed: 0.0% (0/49)
- Effective recall: 100.0%

**Key insight:** The 55.1% overlap rate was inflating both FP and FN counts. We were detecting the right rooms, just with extra context. Number-only patterns aligned detections with ground truth format.

## Next Phase Readiness

**Phase 17 complete:**
- All 3 plans complete (17-01, 17-02, 17-03)
- ROOM precision: 52% (exceeds 40% target)
- ROOM recall: 98% (far exceeds 55% interim target and original 80% goal)
- ROOM F1: 68%, F2: 82%
- No regressions on unit name preservation (PICU, NICU preserved)

**Ready for Phase 18:** Guardian edge cases can proceed independently
**Ready for Phase 22:** ROOM metrics significantly exceed interim targets, pattern-based limits well-understood

**No blockers or concerns**

---
*Phase: 17-room-pattern-expansion*
*Completed: 2026-01-30*
