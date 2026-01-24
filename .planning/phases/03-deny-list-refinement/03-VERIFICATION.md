---
phase: 03-deny-list-refinement
verified: 2026-01-24T01:29:45Z
status: gaps_found
score: 3/4 must-haves verified
gaps:
  - truth: "False positive rate reduced by >20% (precision improved from 87.4% to >90%)"
    status: failed
    reason: "Deny lists only reduced false positives by 4.1% (27 FPs eliminated out of 662), precision improved from 66.3% to 67.2% (+0.9%)"
    artifacts:
      - path: "app/config.py"
        issue: "Deny lists working as designed but limited scope - only medical abbreviations filterable"
      - path: "app/deidentification.py"
        issue: "Deny list filtering working but most FPs are over-detections requiring pattern refinement"
    missing:
      - "Pattern improvements in Phase 4 (deny lists are preventative, not corrective for existing over-detection)"
      - "Remaining 635 false positives require regex pattern refinement, not deny list expansion"
---

# Phase 03: Deny List Refinement Verification Report

**Phase Goal:** Reduce false positives through expanded medical vocabulary deny lists with consistent case handling

**Verified:** 2026-01-24T01:29:45Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All deny lists use case-insensitive matching (fixes LOCATION exact match bug) | ✓ VERIFIED | `deidentification.py` lines 185-207 all use `.lower()` pattern; 33 regression tests pass |
| 2 | Medical abbreviation deny list expanded to cover common clinical terms (NC, RA, OR, ER, IV, PO, IM, SQ, PR, GT, NG, OG, NJ, ED) | ✓ VERIFIED | `config.py` lines 100-115 contain all 13 terms; regression tests confirm filtering |
| 3 | Deny lists exist for all custom entity types (GUARDIAN_NAME, PEDIATRIC_AGE) | ✓ VERIFIED | `config.py` lines 140-156 contain deny_list_guardian_name, deny_list_pediatric_age, deny_list_date_time |
| 4 | False positive rate reduced by >20% (precision improved from 87.4% to >90%) | ✗ FAILED | Precision 66.3% → 67.2% (+0.9%); FP reduction 27/662 = 4.1% (not 20%) |

**Score:** 3/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/config.py` | Case-insensitive deny lists for LOCATION, PERSON, GUARDIAN_NAME, PEDIATRIC_AGE, DATE_TIME | ✓ VERIFIED | Lines 99-156 contain all deny lists with lowercase values |
| `app/deidentification.py` | Case-insensitive filtering logic for all entity types | ✓ VERIFIED | Lines 185-207 use `.lower() in [w.lower() for w in ...]` pattern |
| `tests/test_deidentification.py` | Regression tests for deny list filtering | ✓ VERIFIED | TestDenyListFiltering class with 33 parameterized tests (all passing) |
| `tests/evaluate_presidio.py` | Mirrored deny list logic | ✓ VERIFIED | Contains identical case-insensitive filtering |
| `tests/calibrate_thresholds.py` | Mirrored deny list logic | ✓ VERIFIED | Contains identical case-insensitive filtering |
| `.planning/phases/01-baseline-measurement/BASELINE_METRICS.md` | Phase 03 precision metrics | ✓ VERIFIED | Lines 314-350 document Phase 03 results and gap analysis |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| config.py | deidentification.py | settings.deny_list_* imports | ✓ WIRED | Lines 185-207 reference all 5 deny lists |
| deidentification.py | config.py deny lists | Case-insensitive matching | ✓ WIRED | `.lower()` pattern applied to all deny list checks |
| test_deidentification.py | deidentification.py | deidentify_text calls | ✓ WIRED | 33 regression tests call production code |
| evaluate_presidio.py | deny lists | Duplicated logic | ✓ WIRED | Self-contained evaluation script mirrors production filtering |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| DENY-01: All deny lists use case-insensitive matching | ✓ SATISFIED | None - verified in code and tests |
| DENY-02: Medical abbreviation deny list expanded | ✓ SATISFIED | None - all 13 terms present |
| DENY-03: Deny lists exist for all custom entity types | ✓ SATISFIED | None - GUARDIAN_NAME, PEDIATRIC_AGE, DATE_TIME all present |
| DENY-04: False positive rate reduced by >20% (precision 87.4% → >90%) | ✗ BLOCKED | Only 4.1% FP reduction achieved (27 of 662 FPs eliminated); precision 67.2% vs 90% target |

### Anti-Patterns Found

No blocking anti-patterns detected. Code is production-quality with proper error handling and logging.

### Human Verification Required

None - all verification criteria are programmatically verifiable.

### Gaps Summary

**DENY-04 Not Met: Precision improvement insufficient**

The deny list refinement achieved all technical objectives but fell short on the precision improvement target:

**What was accomplished:**
- Case-insensitive deny list filtering working correctly across all entity types
- 13 medical abbreviations properly filtered (NC, RA, OR, ER, IV, PO, IM, SQ, PR, GT, NG, OG, NJ)
- Deny lists for GUARDIAN_NAME, PEDIATRIC_AGE, DATE_TIME properly implemented
- 33 regression tests all passing
- 27 false positives eliminated

**Why the precision target wasn't met:**
1. **Limited scope of deny lists**: Only 27 of 662 false positives (4.1%) were medical abbreviations that deny lists could filter
2. **Root cause is over-detection**: Remaining 635 false positives are caused by regex patterns that over-detect (e.g., DATE_TIME catching "today" and "daily" even with deny lists)
3. **Deny lists are preventative, not corrective**: They prevent FPs on known safe terms, but don't fix the underlying pattern weaknesses

**What's needed to reach 90% precision:**
- Phase 4 pattern improvements to reduce over-detection
- Tighter regex patterns for DATE_TIME (currently 37% precision)
- Tighter regex patterns for ROOM (currently 56% precision)
- Possible spaCy model fine-tuning for LOCATION (currently 81% precision but 19% recall)

**Phase 03 was successful in its scope** - deny lists are working as designed. The precision target (90%) requires pattern refinement (Phase 4), not just deny list expansion.

---

_Verified: 2026-01-24T01:29:45Z_
_Verifier: Claude (gsd-verifier)_
