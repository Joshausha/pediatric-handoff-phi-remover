# Phase 4 Gap Analysis Report

**Date:** 2026-01-25
**Baseline Recall:** 83.0% (95% CI: 81.0% - 84.8%)
**Post-Gap-Closure Recall:** 86.4% (95% CI: 84.6% - 88.0%)

## Gap Closure Summary

### Addressed Gaps (04-04, 04-05)

| Gap | Count | Plan | Status |
|-----|-------|------|--------|
| Phone international formats (001-, +1-) | ~40 | 04-04 | Fixed |
| Phone dot-separated formats | ~10 | 04-04 | Fixed |
| Phone parentheses with extensions | ~5 | 04-04 | Fixed |
| Room hyphenated standalone (3-22) | ~11 | 04-05 | Fixed |
| **Subtotal** | ~66 | | |

**Improvement:** 257 -> 205 FNs (-52 FNs, -20%)

### Remaining Gaps

| Gap | Count | Decision | Rationale |
|-----|-------|----------|-----------|
| LOCATION addresses | 104 | Not addressable | Fundamental Presidio NER limitation |
| ROOM standalone numbers | 44 | Accept | High FP risk with ages/vitals/doses |
| MRN unprefixed | 37 | Accept | Conflicts with phone numbers |
| PERSON NER misses | 9 | Not addressable | Rare NER failures |
| DATE_TIME formats | 6 | Defer | Low impact |
| PHONE_NUMBER remaining | 5 | Defer | Diminishing returns |

## Decision Record

**Selected Option:** option-c (Conservative: Accept limitations, document residual risk)
**Decision Date:** 2026-01-25
**Rationale:**
- 86.4% recall with documented residual risk is defensible for HIPAA Expert Determination
- LOCATION (51% of remaining FNs) is a fundamental NER limitation unaddressable via regex
- Maintaining precision (66.3%) preserves clinical utility of transcripts
- Manual review serves as mitigation for remaining PHI risk
- Personal QI project where over-redaction harms usability more than marginal recall gain

## Residual Risk Assessment

**Expected Final Recall:** 86.4%
**Remaining False Negatives:** 205

### Risk by Entity Type

| Entity | FNs | Risk Level | Mitigation |
|--------|-----|------------|------------|
| LOCATION | 104 | Medium | User review of addresses in transcripts |
| ROOM | 44 | Low | Room numbers rarely sensitive without context |
| MRN | 37 | Medium | User review of 7-8 digit numbers |
| PERSON | 9 | Low | Rare edge cases |
| DATE_TIME | 6 | Very Low | Times not typically identifying |
| PHONE_NUMBER | 5 | Low | Most formats already caught |

### HIPAA Compliance Approach

**Expert Determination Method:**
1. Statistical evidence: 86.4% recall with documented 95% CI
2. Residual risk: 205 FNs across 600 test transcripts = 0.34 FNs per transcript
3. Risk categories: 51% are addresses (medium risk), 49% are numbers (lower risk)
4. Mitigation: User performs manual review of de-identified output before sharing

**Compliance Statement:**
The de-identification system achieves 86.4% PHI detection recall with known limitations in address detection (Presidio NER constraint) and unprefixed numeric identifiers. Residual risk is documented and mitigated through user review. This approach is appropriate for a personal quality improvement project with manual oversight.

---

## Detailed Failure Analysis

### LOCATION (104 FNs) - Not Addressable

Presidio relies on spaCy NER for location detection. The following patterns are not detected:

- **Full addresses**: "3419 Amanda Gardens Apt. 764", "6270 Stanton Track"
- **City names**: "Daviston", "Angelahaven", "Port Eric"
- **Hospital names**: "Memorial Hospital", "Children's Hospital", "General Hospital"
- **School names**: "Kennedy Elementary", "Lakewood Academy"

**Why not addressable:** These require named entity recognition, not regex patterns. Adding regex patterns for addresses would have massive false positive rates.

### ROOM (44 FNs) - Accepted Limitation

Standalone room numbers without context words:

- Single digits: "7", "8", "5"
- 2-3 digits: "16", "17", "847", "512"
- Hyphenated: "5-34", "5-05", "8-17"

**Why not addressed:** Pattern `\b\d{1,3}\b` would match ages ("4 year old"), vitals ("HR 120"), doses ("give 5 mg"), temps ("38.5"), saturations ("98"). Precision would drop catastrophically.

### MRN (37 FNs) - Accepted Limitation

7-8 digit numbers without "#" or "MRN" prefix:

- "2694522", "46855845", "20814950"

**Why not addressed:** Pattern `\b\d{7,8}\b` would conflict with unformatted phone numbers. Current patterns detect prefixed MRNs (e.g., "#1234567", "MRN 12345678").

---
*Generated: 2026-01-25*
