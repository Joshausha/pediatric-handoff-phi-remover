# Phase 21 Plan 01: Transfer Context LOCATION Patterns Summary

**Phase:** 21-location-transfer-patterns
**Plan:** 01
**Subsystem:** PHI Detection / LOCATION Entity
**Tags:** presidio, recognizer, location, transfer, patterns

## Dependency Graph

- **requires:** Phase 11 (deny list word-boundary matching)
- **provides:** Transfer context LOCATION detection (5 patterns + 6 facility patterns)
- **affects:** Phase 21-02 (facility name patterns), Phase 22 (validation)

## Tech Stack

- **added:** None
- **patterns:** Lookbehind patterns with (?-i:[A-Z]) for case-sensitive uppercase requirement

## Key Files

- **created:** None
- **modified:**
  - `app/recognizers/medical.py` - Added Location Recognizer with 11 patterns
  - `app/deidentification.py` - Fixed LOCATION deny list word-boundary matching
  - `test_presidio.py` - Added 5 transfer context test cases
  - `tests/baselines/regression.json` - Updated with improved metrics

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| LOCATION-INLINE-CASE | Use (?-i:[A-Z]) inline flag | Requires uppercase first letter despite Presidio default IGNORECASE, prevents matching "was", "from", "transferred" |
| LOCATION-WORD-BOUNDARY | Use regex word-boundary for deny list | Prevents "OR" matching "Memorial" or "ER" matching "transferred" |
| LOCATION-TRANSFER-SCORE-0.80 | Score 0.80-0.85 for transfer contexts | High confidence - explicit transfer language indicates location follows |
| LOCATION-FACILITY-SCORE-0.55 | Score 0.55-0.70 for facility names | Lower confidence - facility suffix alone less reliable |
| LOCATION-LIMIT-WORDS | Limit facility patterns to 1-3 words before suffix | Prevents matching from sentence start ("Patient was transferred from Memorial Hospital") |

## Metrics

- **duration:** 11 minutes
- **completed:** 2026-01-31

## One-liner

Transfer context LOCATION patterns using lookbehind with (?-i:[A-Z]) case-sensitivity, improved recall 86.41% -> 91.51%

## Summary

Added Location Recognizer to medical.py with 11 patterns for detecting PHI in transfer contexts. The recognizer uses lookbehind patterns to preserve context words ("transferred from", "admitted from", etc.) while detecting hospital names, medical centers, clinics, and city names.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add transfer context LOCATION patterns | 61bfacd | app/recognizers/medical.py |
| 2 | Add transfer context test cases | 61bfacd | test_presidio.py |
| 3 | Verify integration and commit | 61bfacd | all 4 files |

## Verification Results

1. `python test_presidio.py` - 42/44 passed (95% pass rate), 2 known issues
2. `pytest tests/ -v` - 260 passed, 7 xfailed, 2 xpassed
3. Location Recognizer appears in analyzer registry with 11 patterns
4. Transfer patterns correctly detect hospital names and cities
5. Context words (transferred, admitted, sent, came, en route) preserved

## Patterns Added

### Transfer Context Patterns (5)
- `transferred_from` - "transferred from [Location]"
- `admitted_from` - "admitted from [Location]"
- `sent_from` - "sent from [Location]"
- `came_from` - "came from [Location]"
- `en_route_from` - "en route from [Location]"

### Facility Name Patterns (6)
- `hospital_name` - "[Name] Hospital"
- `medical_center_name` - "[Name] Medical Center"
- `clinic_name` - "[Name] Clinic"
- `pediatrics_office` - "[Name] Pediatrics"
- `urgent_care` - "[Name] Urgent Care"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] LOCATION deny list word-boundary matching**
- **Found during:** Task 1 verification
- **Issue:** Simple substring matching in deny list caused "OR" to match "Memorial", filtering valid PHI
- **Fix:** Changed from `term.lower() in detected_lower` to `re.search(r'\b' + re.escape(term.lower()) + r'\b', detected_lower)`
- **Files modified:** app/deidentification.py (added `import re`, updated LOCATION deny list logic)
- **Commit:** 61bfacd

**2. [Rule 1 - Bug] Facility name patterns matching too much**
- **Found during:** Task 1 verification
- **Issue:** Pattern `[A-Z][A-Za-z'\.]+(?:\s+[A-Z][A-Za-z'\.]+)*` with `*` matched unlimited words, causing "Patient was transferred from Memorial Hospital" to match entirely
- **Fix:** Used `(?-i:[A-Z])` inline flag to require case-sensitive uppercase first letter, stopping greedy matching at lowercase words
- **Files modified:** app/recognizers/medical.py
- **Commit:** 61bfacd

---

**Total deviations:** 2 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Critical fixes for correct PHI detection. Both issues caused either false negatives (deny list bug) or over-detection (greedy pattern bug).

## Success Criteria Met

- [x] LOCATION recognizer exists in medical.py with 11 transfer context patterns
- [x] All transfer patterns use fixed-width lookbehind (Python regex compliant)
- [x] 5 new test cases for transfer context detection pass
- [x] No regressions on existing tests (260 tests pass)
- [x] Context words (transferred, admitted, sent) are preserved
- [x] Hospital names with spaces/apostrophes detected correctly

## Next Phase Readiness

Phase 21-02 (if planned) should add:
- Residential address patterns ("lives at", "lives in")
- School name patterns ("attends", "goes to")
- Discharge destination patterns

No blockers or concerns for next phase.

---
*Generated: 2026-01-31T02:59:01Z*
