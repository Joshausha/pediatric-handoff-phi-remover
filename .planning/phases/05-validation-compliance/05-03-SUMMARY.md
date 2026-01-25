---
phase: 05-validation-compliance
plan: 03
title: "Run validation and generate compliance report"
subsystem: validation
status: complete
completed: 2026-01-25

# Dependencies
requires:
  - phase: 05-validation-compliance
    plan: 01
    reason: Validation dataset infrastructure
  - phase: 05-validation-compliance
    plan: 02
    reason: Bootstrap CI and error taxonomy

provides:
  - capability: validation-runner
    description: Single command validation with CI and error taxonomy
    export: tests/run_validation.py
  - capability: compliance-report
    description: VALIDATION_REPORT.md with metrics and deployment decision
    export: .planning/phases/05-validation-compliance/VALIDATION_REPORT.md

affects:
  - phase: 07
    reason: Benchmark comparison baseline
  - phase: 05
    plan: 04
    reason: Expert review deferred pending engine decision

# Technology
tech-stack:
  added: []
  patterns:
    - Validation orchestration with bootstrap CI
    - Error taxonomy integration
    - Compliance report generation

# Artifacts
key-files:
  created:
    - tests/run_validation.py (already existed from prior work)
    - .planning/phases/05-validation-compliance/VALIDATION_REPORT.md
    - .planning/phases/05-validation-compliance/validation_results.json
  modified: []

# Decisions
decisions:
  - id: DECISION_DEFERRED
    choice: Defer deployment decision pending Phase 7 alternative engine benchmark
    rationale: "Current Presidio recall (86.4%) below 95% threshold. Phase 7 will benchmark Philter-UCSF and Stanford BERT. Decision on whether to improve Presidio patterns or switch engines depends on benchmark results."
    alternatives:
      - Return to Phase 4 for more pattern improvements (original automated recommendation)
      - Accept current recall for personal QI use (Phase 4 decision 04-06)

# Metrics
metrics:
  duration: "Pre-existing (validation run previously)"
  commits: 1
  files-changed: 1
---

# Phase 5 Plan 3: Validation & Compliance Report Summary

**One-liner**: Validation completed with 86.4% recall baseline; deployment decision deferred pending Phase 7 alternative engine benchmark.

## What Was Built

### 1. Validation Runner (`tests/run_validation.py`)

**Purpose**: Single-command validation orchestrator with bootstrap CI and error taxonomy.

**Features**:
- Loads synthetic handoff dataset
- Runs PresidioEvaluator with full metrics
- Calculates 95% CI via bootstrap (10,000 iterations)
- Generates error taxonomy by failure mode
- Outputs JSON results and markdown report

**Usage**:
```bash
python tests/run_validation.py \
  --input tests/synthetic_handoffs.json \
  --output validation_results.json \
  --report VALIDATION_REPORT.md \
  --n-bootstrap 10000
```

### 2. Validation Report (`VALIDATION_REPORT.md`)

**Current metrics (Presidio baseline)**:

| Metric | Value | 95% CI |
|--------|-------|--------|
| **Recall** | 86.4% | [84.7%, 88.1%] |
| Precision | 66.3% | [64.2%, 68.4%] |
| F1 Score | 75.0% | - |
| F2 Score | 81.5% | - |

**False Negatives**: 205 of 1508 PHI spans (13.6%)
- Pattern miss: 201 cases (98%) — ROOM raw numbers, unprefixed MRNs, LOCATION addresses
- Span boundary: 4 cases (2%)

**Automated Decision**: RETURN_TO_PHASE_4 (recall CI lower 84.7% < 95% threshold)

### 3. Raw Results (`validation_results.json`)

Complete JSON output with:
- Per-entity metrics
- Bootstrap CI arrays
- Error taxonomy counts
- Methodology parameters

## Decision: Deferred Pending Phase 7

The automated validation system recommends returning to Phase 4 for pattern improvements.

However, this decision is **deferred** pending Phase 7 (Alternative Engine Benchmark):

1. **Phase 7 will benchmark**:
   - Philter-UCSF (99.5% recall on i2b2 written clinical notes)
   - Stanford BERT (97-99% F1 on de-identification)

2. **Key question**: Do these gains on written notes translate to spoken handoffs?

3. **Decision paths after Phase 7**:
   - If alternative achieves >95% recall → switch engines
   - If alternatives similar to Presidio → accept current recall for personal QI use
   - If alternatives worse → return to Phase 4 for Presidio improvements

## Validation Methodology

- **Dataset**: 500 synthetic handoffs (clinical patterns from pediatric experience)
- **Span matching**: 50% Jaccard overlap threshold
- **Statistical method**: Bootstrap percentile CI (10,000 iterations, seed=42)
- **Excluded entity**: PEDIATRIC_AGE (ages <90 not PHI under HIPAA)

## HIPAA Compliance Documentation

The VALIDATION_REPORT.md serves as Expert Determination evidence:
- Statistical rigor via bootstrap CI
- Failure mode analysis for residual risk assessment
- Intended use documented (personal QI, local processing only)

## Files

### Created/Updated
- `tests/run_validation.py` — Validation orchestrator (pre-existing, verified functional)
- `.planning/phases/05-validation-compliance/VALIDATION_REPORT.md` — Compliance documentation
- `.planning/phases/05-validation-compliance/validation_results.json` — Raw JSON results

## Next Steps

1. **Phase 7**: Benchmark alternative engines (Philter, Stanford BERT)
2. **After Phase 7**: Make engine decision based on benchmark results
3. **05-04**: Expert review deferred until engine chosen (more valuable on final system)

## Commits

```
docs(05-03): complete validation with decision deferred pending Phase 7
```

---
*Phase: 05-validation-compliance*
*Completed: 2026-01-25*
*Decision: Deferred pending Phase 7 alternative engine benchmark*
