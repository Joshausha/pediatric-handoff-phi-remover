# Validation Report: Pediatric Handoff PHI Remover

**Validation Date:** 2026-01-24T18:43:57.825778  
**Dataset Size:** 500 handoffs  
**Bootstrap Iterations:** 10000  

## Executive Summary

| Metric | Value | 95% Confidence Interval |
|--------|-------|------------------------|
| **Recall** | 83.0% | [81.0%, 84.8%] |
| **Precision** | 65.4% | [63.3%, 67.5%] |
| **F1 Score** | 73.1% | - |
| **F2 Score** | 78.7% | - |

### Deployment Decision

**Decision:** `RETURN_TO_PHASE_4`

**Rationale:** Recall 95% CI lower bound (81.0%) does not meet the 95% threshold required for clinical deployment.

**Safety Threshold:** Recall 95% CI lower bound must be ≥ 95%

## Detailed Metrics

### Detection Performance

- **Total PHI spans (ground truth):** 1508
- **Total spans detected:** 1913
- **True positives:** 1251
- **False negatives (PHI leaks):** 257
- **False positives (over-redaction):** 662

### Statistical Validation

Bootstrap confidence intervals (95%) calculated using percentile method with 10,000 iterations:

- **Recall CI:** [81.0%, 84.8%]
- **Precision CI:** [63.3%, 67.5%]

## Error Taxonomy

**Total false negatives:** 257

### Breakdown by Failure Mode

#### PATTERN MISS (246 cases, 95.7%)

1. **ROOM**: `847`
2. **MEDICAL_RECORD_NUMBER**: `2694522`
3. **LOCATION**: `3419 Amanda Gardens Apt. 764`
4. **LOCATION**: `Daviston`
5. **LOCATION**: `6270 Stanton Track`
   _(and 241 more)_

**Recommendation:** → Add regex patterns to custom recognizers

#### SPAN BOUNDARY (11 cases, 4.3%)

1. **ROOM**: `3-22`
2. **ROOM**: `2-25`
3. **PERSON**: `Virginia Daniels`
4. **ROOM**: `9-27`
5. **ROOM**: `3-22`
   _(and 6 more)_

**Recommendation:** → Review entity boundary detection logic

## Methodology

### Dataset

- **Source:** Synthetic handoff dataset (clinical patterns based on pediatric residency experience)
- **Size:** 500 handoffs
- **PHI entities evaluated:** PERSON, GUARDIAN_NAME, MEDICAL_RECORD_NUMBER, ROOM, DATE_TIME, LOCATION, PHONE_NUMBER, EMAIL_ADDRESS
- **Excluded entity types:** PEDIATRIC_AGE

**Note on PEDIATRIC_AGE exclusion:** Ages under 90 are not considered PHI under HIPAA (45 CFR 164.514(b)(2)(i)(C)).
The PEDIATRIC_AGE recognizer was intentionally disabled in Phase 4 (decision 04-03). Validation metrics
exclude these spans to reflect the actual PHI detection scope.

**Note on External Validation:** This validation uses synthetic data designed to represent realistic
clinical patterns. External validation on real de-identified transcripts requires IRB approval for
prospective collection. For this personal quality improvement project, synthetic validation serves
as the practical validation path.

### Evaluation Method

- **Span matching:** Jaccard-like overlap (union-based)
- **Overlap threshold:** 50.0% minimum overlap to consider match
- **Type matching:** Ground truth types mapped to Presidio entity types

### Statistical Analysis

- **Bootstrap method:** Percentile method with replacement sampling
- **Iterations:** 10,000
- **Confidence level:** 95%
- **Random seed:** 42 (reproducibility)

### Safety Threshold

Deployment requires recall 95% CI lower bound ≥ 95% to ensure PHI safety.
This threshold accounts for statistical uncertainty in recall estimation.

## HIPAA Compliance

### Expert Determination (§164.514(b))

This validation provides statistical evidence for HIPAA Expert Determination:

- **Recall performance:** 83.0% with 95% CI [81.0%, 84.8%]
- **Residual risk assessment:** Based on false negative rate and failure mode analysis
- **Statistical rigor:** Bootstrap confidence intervals quantify estimation uncertainty

### Intended Use

This tool is intended for personal quality improvement use only:

- **Use case:** Transcribe and de-identify pediatric handoff recordings for personal study
- **Data handling:** All processing occurs locally (no external API calls)
- **Risk mitigation:** User reviews de-identified output before any sharing

---

*Generated: 2026-01-24 18:43:57*