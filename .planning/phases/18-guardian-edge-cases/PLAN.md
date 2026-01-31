# Phase 18: Guardian Edge Cases - Execution Plans

**Phase:** 18
**Goal:** Catch possessive and appositive guardian name patterns
**Created:** 2026-01-30
**Status:** Ready for execution

## Phase Overview

This phase adds ~95 new regex patterns to detect guardian names in possessive and appositive constructions that the current recognizer misses.

**Examples of patterns now detected:**
- "his mom Sarah" → "his mom [GUARDIAN_NAME]"
- "her dad Tom" → "her dad [GUARDIAN_NAME]"
- "the mom, Jessica" → "the mom, [GUARDIAN_NAME]"
- "guardian (Sarah)" → "guardian ([GUARDIAN_NAME]"

## Execution Plans

| Plan | Wave | Description | Depends On |
|------|------|-------------|------------|
| [18-01](18-01-PLAN.md) | 1 | Possessive patterns (~60 patterns) | None |
| [18-02](18-02-PLAN.md) | 1 | Appositive patterns (~35 patterns) | None |
| [18-03](18-03-PLAN.md) | 2 | Validation & recall measurement | 18-01, 18-02 |

## Wave Execution

**Wave 1 (parallel):**
- 18-01: Add possessive patterns (his/her/their + relationship + name)
- 18-02: Add appositive patterns (relationship + punctuation + name)

**Wave 2 (sequential):**
- 18-03: Full validation and integration tests

## Success Criteria (from ROADMAP)

1. [x] "his mom Sarah" / "her dad Tom" (possessive + relationship) detected
2. [x] "the mom, Jessica" (appositive with comma) detected
3. [ ] "grandma's here, her name is Maria" detected - **DEFERRED** (cross-sentence requires sentence tokenization)
4. [ ] GUARDIAN_NAME recall improved without new false positives
5. [ ] Existing guardian patterns unaffected

## Deferred

**Cross-sentence patterns** ("Grandma's here. Her name is Maria") were intentionally deferred per research recommendation. The research found this requires sentence tokenization or custom EntityRecognizer logic beyond PatternRecognizer. Will be addressed in a future phase if recall gap still exists after this phase.

## Files Modified

- `app/recognizers/pediatric.py` - Add ~95 new patterns
- `test_presidio.py` - Add 7 unit tests
- `tests/test_deidentification.py` - Add 3 integration tests

## Verification Command

```bash
cd "/Users/joshpankin/My Drive/10-19 Projects/12 Development & AI Projects/12.09 Pediatric_Handoff_PHI_Remover"
python test_presidio.py && pytest tests/test_deidentification.py -v -k "guardian"
```
