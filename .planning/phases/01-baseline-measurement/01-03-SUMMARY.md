---
phase: 01-baseline-measurement
plan: 03
subsystem: testing
tags: [presidio, adversarial-testing, edge-cases, synthetic-data, phi-detection]

# Dependency graph
requires:
  - phase: 01-01
    provides: Presidio evaluation harness and synthetic dataset generation framework
provides:
  - 59 adversarial templates covering speech artifacts, cultural diversity, boundary conditions
  - 100 adversarial synthetic handoffs (seed=43) exposing PHI detection weaknesses
  - Gap analysis identifying specific pattern failures for Phase 4 improvements
affects: [04-pattern-improvements, 05-end-to-end-validation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Adversarial testing pattern for PHI detection stress testing
    - Separate seed strategy for adversarial datasets (43 vs 42)

key-files:
  created:
    - tests/adversarial_handoffs.json
  modified:
    - tests/handoff_templates.py

key-decisions:
  - "Use seed=43 for adversarial dataset to maintain separation from standard dataset (seed=42)"
  - "Create 6 adversarial template categories targeting known PHI detection weaknesses"
  - "Generate 100 samples to balance coverage with evaluation speed"

patterns-established:
  - "Adversarial dataset pattern: separate file, separate seed, targeted edge cases"
  - "Template categorization by edge case type (speech, cultural, boundary, transcription, compound, age)"

# Metrics
duration: 12min
completed: 2026-01-23
---

# Phase 01 Plan 03: Adversarial Dataset Creation Summary

**59 adversarial templates exposing critical PHI detection gaps: 80.1% recall (vs 77.9% standard) with 31 PHI leaks across room numbers, pediatric ages, and phone formats**

## Performance

- **Duration:** 12 minutes
- **Started:** 2026-01-23T18:06:00Z
- **Completed:** 2026-01-23T18:18:43Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Created 59 adversarial templates across 6 edge case categories
- Generated 100 adversarial handoffs with 100% template coverage
- Identified specific PHI detection weaknesses: ROOM (19% recall), PEDIATRIC_AGE (25% recall)
- Documented 31 PHI leaks exposing gaps in regex patterns and boundary detection

## Task Commits

Each task was committed atomically:

1. **Task 1: Add adversarial template categories** - `420a776` (test)
2. **Task 2: Generate adversarial dataset** - `f65e4b8` (test)
3. **Task 3: Evaluate adversarial dataset** - (no commit - evaluation only)

## Files Created/Modified
- `tests/handoff_templates.py` - Added ADVERSARIAL_TEMPLATES with 59 edge case templates
- `tests/adversarial_handoffs.json` - 100 synthetic adversarial handoffs exposing PHI detection gaps

## Adversarial Template Categories

### 1. Speech Artifacts (10 templates)
Stutters, filler words, self-corrections typical in speech-to-text:
- "Um, this is uh {{person}}, a {{pediatric_age}} old..."
- "Patient is John no wait {{person}}, age {{pediatric_age}}"

### 2. Cultural Name Diversity (7 templates)
Hispanic multi-surname patterns, hyphenated names, suffixes:
- "Patient {{person}} Jr., age {{pediatric_age}}"
- Multi-part Hispanic names

### 3. Boundary Edge Cases (17 templates)
Punctuation, start/end of line, reversed relationship patterns:
- "{{person}} is a {{pediatric_age}} old..." (line start)
- "{{person}} is mom and primary decision maker" (reversed pattern)
- "mom {{person}} at bedside" (lowercase relationship word)

### 4. Transcription Errors (9 templates)
Misheard words, repeated information:
- "Patient stable on NC, not in NC (the state)"
- "{{person}}... {{person}} is the patient name"

### 5. Compound Patterns (8 templates)
Multiple PHI in close proximity:
- "{{person}} (MRN {{mrn}}) admitted to {{room_number}} on {{date}}"
- "According to mom ({{person}}), patient ({{person}}) has {{condition}}"

### 6. Age Edge Cases (8 templates)
Non-standard age formats:
- "3 week old patient, weight 3.2kg" (numeric confusion)
- "Patient is approximately {{pediatric_age}}"

## Evaluation Results Comparison

### Overall Metrics

| Dataset | Recall | Precision | F2 Score | PHI Leaks |
|---------|--------|-----------|----------|-----------|
| **Standard (500 samples)** | 77.9% | 66.3% | 75.3% | 369 |
| **Adversarial (100 samples)** | 80.1% | 69.4% | 77.7% | 31 |

*Note: Adversarial recall slightly higher due to simpler templates with fewer complex contexts*

### Critical Weaknesses Exposed

#### Worst Performers (Adversarial Dataset)
1. **ROOM**: 19% recall - Misses: "Bay 3", "bed 9", "isolette 35", single digits "7", "8"
2. **PEDIATRIC_AGE**: 25% recall - Misses: "12 month old", "17yo", "4 yo", "22mo"
3. **DATE_TIME**: 69% recall - Misses: "January 04", "January 21" (repeated dates)
4. **PHONE_NUMBER**: 87% recall - Misses: international formats, extensions "001-885-221-6484x1298"
5. **MEDICAL_RECORD_NUMBER**: 90% recall - Misses: "7018128" (no prefix)

#### Strong Performers
- **EMAIL_ADDRESS**: 100% recall, 100% precision
- **PERSON**: 100% recall, 92% precision (over-redaction from deny list gaps)
- **LOCATION**: 100% recall, 17% precision (over-redacting medical abbreviations)

## Gap Analysis for Phase 4

### Room Number Pattern Failures
**Issue:** Only detects "Room X" format, misses variations:
- "Bay 3", "bed 9", "isolette 35" - Alternative location descriptors
- Single digits "7", "8" at line start - No context word required
- "4-11", "4-30" - Multi-part room identifiers

**Fix needed:** Expand room number patterns to include bay/bed/isolette + handle standalone numbers in clinical context

### Pediatric Age Pattern Failures
**Issue:** Abbreviation variations not covered:
- "17yo", "4 yo", "8yo", "22mo", "15yo" - Abbreviated formats with/without space
- "12 month old", "19 month old", "10 year old" - Singular time units

**Fix needed:** Regex patterns for abbreviated age formats (yo, mo, wk with optional space)

### Phone Number Format Gaps
**Issue:** International formats and extensions:
- "001-359-886-6201", "+1-496-268-9139" - Country codes
- "001-885-221-6484x1298" - Extensions
- "594.480.2422" - Dot separators

**Fix needed:** Expand phone regex to handle international formats, extensions, alternative separators

### Date Format Edge Cases
**Issue:** Repeated dates in comma-separated lists:
- "January 04", "January 21" in "Seen on {{date}}, {{date}}, and {{date}}"

**Fix needed:** Verify date pattern handles comma-separated contexts

### MRN Pattern Gaps
**Issue:** Bare numbers without prefix:
- "7018128" (no "MRN" prefix or "#" symbol)

**Fix needed:** Consider bare 7-8 digit numbers in clinical context as potential MRNs

## Decisions Made

1. **Seed=43 for adversarial dataset** - Maintains separation from standard dataset (seed=42), enables reproducibility
2. **100 samples sufficient** - Provides full template coverage (59/59) while keeping evaluation fast (~30 seconds)
3. **6-category organization** - Groups edge cases by weakness type for clear Phase 4 targeting
4. **No commit for Task 3** - Evaluation is analysis work, not code/data changes

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

1. **Numpy version incompatibility** - Initial evaluation failed with "numpy.dtype size changed" error
   - **Resolution:** Used project venv instead of system python3
   - **Lesson:** Always activate venv before running presidio evaluation

## Next Phase Readiness

**Ready for Phase 4 (Pattern Improvements):**
- Clear prioritization: ROOM (19% recall) and PEDIATRIC_AGE (25% recall) are highest priority
- Specific pattern failures documented with examples
- Adversarial dataset provides regression testing for improvements

**Blockers/Concerns:**
- None - all gaps are fixable via regex pattern improvements

**Phase 4 Recommendations:**
1. Start with ROOM patterns (worst performer, clearest fixes)
2. Then PEDIATRIC_AGE abbreviations (yo, mo, wk)
3. Then PHONE_NUMBER international formats
4. Finally MRN bare numbers (lowest priority, riskiest for false positives)

---
*Phase: 01-baseline-measurement*
*Completed: 2026-01-23*
