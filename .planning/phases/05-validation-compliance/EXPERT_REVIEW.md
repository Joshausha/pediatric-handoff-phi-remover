# Expert Review: HIPAA Expert Determination (VALD-03)

**Review Date:** 2026-01-25
**Reviewer:** Dr. Josh Pankin, MD (Pediatric Resident PGY-3)
**Related Document:** [VALIDATION_REPORT.md](./VALIDATION_REPORT.md)

---

## 1. Reviewer Qualification

### Reviewer Background

| Qualification | Details |
|---------------|---------|
| Name | Dr. Josh Pankin |
| Title | Pediatric Resident PGY-3 |
| Institution | [Institution] |
| HIPAA Training | Yes - Annual institutional training |
| Domain Expertise | Pediatric medicine, clinical documentation, quality improvement |
| Role in Project | System developer and clinical expert reviewer |

### Basis for Expert Determination Authority

Per HIPAA Safe Harbor (45 CFR 164.514(b)), an expert determination requires a person with:
- Appropriate knowledge and experience with statistical and scientific principles
- Knowledge of the types of data and identifiers involved
- Ability to render an expert opinion regarding re-identification risk

**For this personal QI project:**
- The reviewer is both the system developer (understands technical implementation) and clinical user (understands handoff context)
- No IRB or external research team involvement (personal tool for self-study)
- Expert review serves as quality assurance before personal clinical use

---

## 2. Review Protocol

### Methodology

1. **Sample Selection:** 10 random handoffs stratified by dominant PHI type
2. **Seed:** 42 (reproducible)
3. **Source:** `expert_review_sample.json` generated from synthetic dataset

### Review Process

For each sample:
1. Read the `original_text` containing synthetic PHI
2. Read the `deidentified_text` (Presidio output)
3. Compare: Is any PHI from original still visible in deidentified output?
4. Document any findings (missed PHI, over-redaction, quality issues)

### PHI Types Under Review

| Entity Type | Weight | Clinical Relevance |
|-------------|--------|-------------------|
| PERSON | 5 (High) | Patient/family names |
| GUARDIAN_NAME | 5 (High) | Parent/caregiver names |
| PHONE_NUMBER | 2 (Medium) | Contact numbers |
| ROOM | 4 (High) | Bed/room identifiers |
| DATE_TIME | 2 (Medium) | Dates of service |
| LOCATION | 0 (Low) | Addresses (rare in spoken handoffs) |
| MEDICAL_RECORD_NUMBER | 1 (Low) | MRN (rare in spoken handoffs) |
| EMAIL_ADDRESS | 0 (Low) | Email (rare in spoken handoffs) |

---

## 3. Sample Review Results

### Instructions
For each row: Mark PHI status, note any issues, and provide expert assessment.

| # | Sample ID | PHI Detected | Missed PHI? | Over-redacted? | Notes | Status |
|---|-----------|--------------|-------------|----------------|-------|--------|
| 1 | 15 | 8 entities | [x] Yes | [ ] No | Address "6247 Hickman Cliffs" visible | Issue |
| 2 | 223 | 5 entities | [ ] No | [ ] No | All PHI caught | OK |
| 3 | 26 | 3 entities | [ ] No | [ ] No | All PHI caught | OK |
| 4 | 98 | 6 entities | [x] Yes | [ ] No | Address "20472 West Avenue Apt. 043" visible | Issue |
| 5 | 209 | 4 entities | [ ] No | [ ] No | Pager "#1719" is provider pager (Dr. Dawson), not PHI | OK |
| 6 | 38 | 1 entity | [ ] No | [ ] No | All PHI caught | OK |
| 7 | 109 | 0 entities | [ ] No | [ ] No | No PHI in original | OK |
| 8 | 373 | 2 entities | [ ] No | [x] Yes | "5 months old" and "day 4" over-redacted as [DATE] | Issue |
| 9 | 92 | 1 entity | [ ] No | [x] Yes | "overnight" over-redacted as [DATE] | Issue |
| 10 | 147 | 1 entity | [ ] No | [x] Yes | "overnight" over-redacted as [DATE] | Issue |

---

## 4. Findings Summary

### Missed PHI Instances

_Document any PHI visible in de-identified output that should have been redacted:_

| Sample ID | Missed PHI | Entity Type | Risk Level | Notes |
|-----------|------------|-------------|------------|-------|
| 15 | "6247 Hickman Cliffs" | LOCATION | Low (weight=0) | Address - known NER limitation |
| 98 | "20472 West Avenue Apt. 043" | LOCATION | Low (weight=0) | Address - known NER limitation |

**Total missed PHI:** 2 / ~31 spans reviewed

**Note:** Sample 209 pager "#1719" initially flagged but determined to be Dr. Dawson's (fellow) provider pager — provider contact info is NOT patient PHI.

### Over-Redaction Instances

_Document any clinical content inappropriately redacted:_

| Sample ID | Over-redacted Text | Expected Behavior | Impact |
|-----------|-------------------|-------------------|--------|
| 373 | "5 months old" → [DATE] | Keep (age not PHI unless 90+) | **CRITICAL** - loses patient age for clinical decision-making |
| 373 | "day 4" → [DATE] | Keep (clinical timeline) | **CRITICAL** - loses illness timeline for clinical decisions |
| 92, 147 | "overnight" → [DATE] | Keep (relative time word) | **CRITICAL** - loses clinical timeline context |

### Overall Assessment

- **Total samples reviewed:** 10
- **Samples with issues:** 5 (2 missed PHI, 3 over-redaction)
- **Samples fully acceptable:** 5
- **Missed PHI (high-weight):** 0 — only LOCATION (weight=0) missed; no patient-identifiable PHI leaked
- **Over-redaction (clinical impact):** 3 samples — **CRITICAL** for clinical decision-making context

---

## 5. Risk Assessment

### Residual Re-identification Risk

Based on [VALIDATION_REPORT.md](./VALIDATION_REPORT.md):
- **Automated recall:** 86.4% (94.4% weighted)
- **95% CI:** [84.7%, 88.1%]
- **False negatives:** 205 spans (205/1508 = 13.6%)

### Expert Opinion on Residual Risk

_Provide expert opinion on whether residual risk is acceptable for intended use:_

- **Intended use:** Personal QI project - transcribe handoff recordings for self-study
- **Data flow:** Audio → Local transcription → Local de-identification → User review → Personal notes
- **Mitigation:** User reviews de-identified output before any external sharing

**Risk Assessment:**

[ ] **ACCEPTABLE** - Residual risk is acceptable given:
  - Intended use is personal (not sharing with others)
  - User review provides final check before any output use
  - No real-time clinical decision making based on output
  - Statistical performance (94.4% weighted recall) adequate for personal use

[ x] **REQUIRES IMPROVEMENT** - Residual risk requires:
  - [ x] Additional pattern improvements
  - [ ] Enhanced user training
  - [ ] Workflow modifications
  - [ ] Other: _______________

---

## 6. Expert Sign-off

### Determination Statement

Based on my review of:
1. The random sample of 10 de-identified outputs
2. The automated validation metrics ([VALIDATION_REPORT.md](./VALIDATION_REPORT.md))
3. The intended use case (personal QI project)

I hereby determine that:

### [ ] APPROVED FOR PERSONAL USE

The Pediatric Handoff PHI Remover system provides acceptable de-identification for the intended use case. The residual re-identification risk is:
- Low given the personal use context
- Mitigated by user review of all outputs
- Acceptable per HIPAA Expert Determination standards for this use case

### [x] REQUIRES IMPROVEMENT

The system requires the following improvements before use:
- **CRITICAL:** Over-redaction of clinical timeline information ("5 months old", "day 4", "overnight") removes essential context for clinical decision-making
- **Action needed:** Add deny list entries for relative time words and pediatric age descriptors that are not HIPAA PHI
- **PHI safety:** No high-weight PHI was leaked (only LOCATION addresses, weight=0, never spoken in handoffs)

---

**Signature:** _____Josh Pankin____________________________

**Date:** _______1/25/26________

**Print Name:** Dr. Josh Pankin, MD

---

## Appendix: Cross-Reference to Automated Validation

### Validation Metrics Summary (from VALIDATION_REPORT.md)

| Metric | Value | Note |
|--------|-------|------|
| Recall (unweighted) | 86.4% | All entity types equally weighted |
| Recall (weighted) | 94.4% | Weighted by spoken handoff relevance |
| Precision | 66.3% | Some over-redaction expected |
| F2 Score | 81.5% | Recall-weighted harmonic mean |
| False Negatives | 205 | Of 1508 total PHI spans |

### Entity-Specific Performance

| Entity Type | Recall | False Negatives | Weight |
|-------------|--------|-----------------|--------|
| PERSON | ~95% | 9 | 5 |
| GUARDIAN_NAME | ~85% | Low | 5 |
| ROOM | ~43% | 44 | 4 |
| PHONE_NUMBER | ~95% | 5 | 2 |
| DATE_TIME | ~95% | 6 | 2 |
| MRN | ~72% | 37 | 1 |
| LOCATION | ~20% | 104 | 0 |
| EMAIL | ~100% | 0 | 0 |

### Known Limitations (Accepted)

Per Phase 7 decision ([07-03-SUMMARY.md](../07-alternative-engine-benchmark/07-03-SUMMARY.md)):
- LOCATION recall (20%) is low but zero-weighted (rare in spoken handoffs)
- ROOM recall (43%) accepted to avoid false positives on age ranges
- MRN recall (72%) accepted to avoid conflicts with phone numbers

---

*Generated: 2026-01-25*
*Review Completed: 2026-01-25*
*Review Template Version: 1.0*
