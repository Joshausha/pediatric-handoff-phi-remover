# Validation Report: Pediatric Handoff PHI Remover

**Validation Date:** 2026-01-24T16:26:28.651886  
**Dataset Size:** 500 handoffs  
**Bootstrap Iterations:** 10000  

## Executive Summary

| Metric | Value | 95% Confidence Interval |
|--------|-------|------------------------|
| **Recall** | 74.8% | [72.7%, 76.9%] |
| **Precision** | 65.4% | [63.3%, 67.5%] |
| **F1 Score** | 69.8% | - |
| **F2 Score** | 72.7% | - |

### Deployment Decision

**Decision:** `RETURN_TO_PHASE_4`

**Rationale:** Recall 95% CI lower bound (72.7%) does not meet the 95% threshold required for clinical deployment.

**Safety Threshold:** Recall 95% CI lower bound must be ≥ 95%

## Detailed Metrics

### Detection Performance

- **Total PHI spans (ground truth):** 1672
- **Total spans detected:** 1913
- **True positives:** 1251
- **False negatives (PHI leaks):** 421
- **False positives (over-redaction):** 662

### Statistical Validation

Bootstrap confidence intervals (95%) calculated using percentile method with 10,000 iterations:

- **Recall CI:** [72.7%, 76.9%]
- **Precision CI:** [63.3%, 67.5%]

## Error Taxonomy

**Total false negatives:** 421

### Breakdown by Failure Mode

#### PATTERN MISS (388 cases, 92.2%)

1. **PEDIATRIC_AGE**: `5 days old`
2. **PEDIATRIC_AGE**: `6 weeks 4 days old`
3. **ROOM**: `847`
4. **PEDIATRIC_AGE**: `DOL 6`
5. **MEDICAL_RECORD_NUMBER**: `2694522`
   _(and 383 more)_

**Recommendation:** → Add regex patterns to custom recognizers

#### SPAN BOUNDARY (33 cases, 7.8%)

1. **ROOM**: `3-22`
2. **PEDIATRIC_AGE**: `5 weeks 6 days old`
3. **ROOM**: `2-25`
4. **PERSON**: `Virginia Daniels`
5. **PEDIATRIC_AGE**: `8 weeks 4 days old`
   _(and 28 more)_

**Recommendation:** → Review entity boundary detection logic

## Methodology

### Dataset

- **Source:** Synthetic handoff dataset (clinical patterns based on pediatric residency experience)
- **Size:** 500 handoffs
- **PHI entities:** PERSON, GUARDIAN_NAME, MEDICAL_RECORD_NUMBER, ROOM, DATE_TIME, LOCATION, PHONE_NUMBER, EMAIL_ADDRESS, PEDIATRIC_AGE

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

- **Recall performance:** 74.8% with 95% CI [72.7%, 76.9%]
- **Residual risk assessment:** Based on false negative rate and failure mode analysis
- **Statistical rigor:** Bootstrap confidence intervals quantify estimation uncertainty

### Intended Use

This tool is intended for personal quality improvement use only:

- **Use case:** Transcribe and de-identify pediatric handoff recordings for personal study
- **Data handling:** All processing occurs locally (no external API calls)
- **Risk mitigation:** User reviews de-identified output before any sharing

---

*Generated: 2026-01-24 16:26:28*