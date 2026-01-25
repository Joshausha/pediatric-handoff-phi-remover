# Validation Report: Pediatric Handoff PHI Remover

**Validation Date:** 2026-01-25T01:19:50.961241  
**Dataset Size:** 500 handoffs  
**Bootstrap Iterations:** 10000  

## Executive Summary

| Metric | Value | 95% Confidence Interval |
|--------|-------|------------------------|
| **Recall** | 86.4% | [84.7%, 88.1%] |
| **Precision** | 66.3% | [64.2%, 68.4%] |
| **F1 Score** | 75.0% | - |
| **F2 Score** | 81.5% | - |

### Deployment Decision

**Decision:** `RETURN_TO_PHASE_4`

**Rationale:** Recall 95% CI lower bound (84.7%) does not meet the 95% threshold required for clinical deployment.

**Safety Threshold:** Recall 95% CI lower bound must be ≥ 95%

## Detailed Metrics

### Detection Performance

- **Total PHI spans (ground truth):** 1508
- **Total spans detected:** 1965
- **True positives:** 1303
- **False negatives (PHI leaks):** 205
- **False positives (over-redaction):** 662

### Statistical Validation

Bootstrap confidence intervals (95%) calculated using percentile method with 10,000 iterations:

- **Recall CI:** [84.7%, 88.1%]
- **Precision CI:** [64.2%, 68.4%]

## Error Taxonomy

**Total false negatives:** 205

### Breakdown by Failure Mode

#### PATTERN MISS (201 cases, 98.0%)

1. **ROOM**: `847`
2. **MEDICAL_RECORD_NUMBER**: `2694522`
3. **LOCATION**: `3419 Amanda Gardens Apt. 764`
4. **LOCATION**: `Daviston`
5. **LOCATION**: `6270 Stanton Track`
   _(and 196 more)_

**Recommendation:** → Add regex patterns to custom recognizers

#### SPAN BOUNDARY (4 cases, 2.0%)

1. **PERSON**: `Virginia Daniels`
2. **LOCATION**: `0083 Dodson Islands Apt. 003`
3. **LOCATION**: `276 Larry Loaf Suite 197`
4. **LOCATION**: `296 Hayes Well`

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

- **Recall performance:** 86.4% with 95% CI [84.7%, 88.1%]
- **Residual risk assessment:** Based on false negative rate and failure mode analysis
- **Statistical rigor:** Bootstrap confidence intervals quantify estimation uncertainty

### Intended Use

This tool is intended for personal quality improvement use only:

- **Use case:** Transcribe and de-identify pediatric handoff recordings for personal study
- **Data handling:** All processing occurs locally (no external API calls)
- **Risk mitigation:** User reviews de-identified output before any sharing

---

*Generated: 2026-01-25 01:19:50*