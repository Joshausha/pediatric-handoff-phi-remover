# Quick Task 001: Investigation Summary

**Three de-identification failures traced to spaCy NER false positives, missing recognizer patterns, and gestational age terminology debate**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-23T10:33:15-05:00
- **Completed:** 2026-01-23T10:36:41-05:00
- **Tasks:** 2 (investigation only, no code changes)
- **Files created:** 1

## Accomplishments

- Root cause identified for all three test failures with exact code references
- Each failure classified as false positive, false negative, or debatable case
- Design trade-offs documented for each case with recommended approaches
- Ready for Phase 1 baseline measurement with clear understanding of current system behavior

## Files Created

- `.planning/quick/001-investigate-deidentification-code/INVESTIGATION.md` - Complete root cause analysis with code references, design questions, and recommended fixes

## Key Findings

### Failure 1: "high flow" → "[LOCATION]flow" (False Positive)
- **Root cause:** spaCy NER detects "Patient on high" as LOCATION (score 0.60)
- **Deny list limitation:** Exact string matching fails; detected span "Patient on high" doesn't match deny list entries
- **Recommended fix:** Add multi-word medical phrases to deny list with phrase-boundary matching

### Failure 2: "Ronald McDonald House" not detected (False Negative)
- **Root cause:** School recognizer only covers schools/daycares, missing charity housing patterns
- **spaCy context-sensitivity:** "Ronald McDonald House" alone → PERSON (0.85), but in sentence "Family staying at..." → no detection
- **Recommended fix:** Extend school recognizer with charity housing patterns (Ronald McDonald House, Hope Lodge, Family House)

### Failure 3: "35 weeker" → "[AGE]" (Debatable)
- **Root cause:** Gestational age pattern explicitly includes "weeker" suffix in regex
- **Design tension:** Medical shorthand vs. potentially identifying age
- **Two detections:** DATE_TIME (0.85) AND PEDIATRIC_AGE (0.50) - DATE wins
- **Recommended fix:** Remove "er" suffix from pattern OR add to deny list for common medical terminology

## Design Trade-offs Identified

All three failures highlight the **core tension** of balanced precision/recall:

| Metric | Current Behavior | Impact |
|--------|------------------|--------|
| **Recall** (catch all PHI) | Optimized for high recall | "35 weeker" redacted (conservative) |
| **Precision** (preserve clinical content) | Secondary priority | "high flow" over-redacted (unintended consequence) |
| **Coverage** | Incomplete for pediatric locations | "Ronald McDonald House" missed (gap) |

**Key insight:** System is aggressive on standard medical terminology ("35 weeker") but has gaps in pediatric-specific locations. Deny list architecture needs enhancement for multi-word phrases.

## Decisions Made

None - investigation only, no code changes made per task constraints.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Initial Python import errors (missing venv activation) - resolved by activating virtual environment
- OpenSSL warning noise in output - filtered for cleaner investigation results

## Next Steps

This investigation provides the foundation for:

1. **Phase 1:** Baseline measurement with synthetic dataset (500 transcripts)
   - These three cases should become regression tests
   - Metrics will quantify current precision/recall balance

2. **Phase 2:** Threshold tuning (currently arbitrary: 0.35 detection, 0.7 validation)
   - May help with "high flow" false positive (score 0.60)
   - Won't help with "Ronald McDonald House" (score 0.0 - not detected)

3. **Phase 3:** Deny list improvements
   - Multi-word phrase support needed for "high flow"
   - Case-insensitive matching for consistency (PERSON already does this)

4. **Phase 4:** Custom recognizer enhancements
   - Add charity housing patterns to school/location recognizer
   - Decide on gestational age terminology policy ("weeker" redaction vs. preservation)

## Context for Future Work

**Code references documented in INVESTIGATION.md:**
- `app/deidentification.py` lines 142-165 (analysis and deny list filtering)
- `app/config.py` lines 66-108 (deny list definitions)
- `app/recognizers/pediatric.py` lines 190-195 (gestational age pattern), lines 213-243 (school recognizer)

**Policy questions requiring decisions:**
1. When is medical terminology "identifying" vs. "standard language"?
2. Should deny list support substring/phrase matching?
3. What pediatric-specific locations should be comprehensively covered?

---

*Quick Task: 001-investigate-deidentification-code*
*Completed: 2026-01-23*
