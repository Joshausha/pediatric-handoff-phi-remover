---
phase: 08
plan: 01
subsystem: evaluation
tags: [metrics, weighted-recall, clinical-relevance, spoken-handoff]
requires: [04-06]
provides: [weighted-metrics-infrastructure]
affects: [evaluation, benchmarking]
tech-stack:
  added: []
  patterns: [weighted-metrics, clinical-relevance-weighting]
key-files:
  created: [tests/test_weighted_metrics.py]
  modified: [app/config.py, tests/evaluate_presidio.py]
decisions:
  - id: weights-from-analysis
    what: Use weights from SPOKEN_HANDOFF_ANALYSIS.md
    why: Evidence-based values from actual handoff frequency data
    impact: Metrics reflect real-world clinical importance
  - id: backward-compatible
    what: Weighted metrics opt-in via --weighted flag
    why: Preserve existing workflows, allow comparison
    impact: No breaking changes to existing evaluation scripts
metrics:
  duration: 3 minutes
  completed: 2026-01-25
---

# Phase 8 Plan 1: Add Weighted Scoring to evaluate_presidio.py Summary

**One-liner:** Implemented spoken handoff relevance weighting so evaluation metrics reflect real-world clinical importance (weighted recall 91.5% vs unweighted 77.9%)

## What Was Built

Added weighted metrics infrastructure to evaluation system:
1. **Configuration** - Weights for 9 entity types (0-5 scale) in config.py
2. **Metrics Methods** - weighted_recall(), weighted_precision(), weighted_f2() in EvaluationMetrics
3. **Evaluation Tracking** - Per-entity TP/FN/FP stats populated during evaluation
4. **CLI Integration** - Optional --weighted flag to show weighted metrics
5. **Validation Tests** - 11 tests verify calculations match SPOKEN_HANDOFF_ANALYSIS.md

## Key Implementation Details

### Weight Assignments (Clinical Evidence-Based)

| Entity | Weight | Rationale |
|--------|--------|-----------|
| PERSON, GUARDIAN_NAME | 5 | Critical - spoken constantly |
| ROOM | 4 | High - used for patient identification |
| PHONE_NUMBER, DATE_TIME | 2 | Medium - occasionally spoken |
| MEDICAL_RECORD_NUMBER | 1 | Low - rarely spoken aloud |
| EMAIL_ADDRESS, LOCATION, PEDIATRIC_AGE | 0 | Never spoken during handoffs |

Source: SPOKEN_HANDOFF_ANALYSIS.md (2026-01-25)

### Calculation Method

**Weighted Recall:**
```
weighted_tp = Σ(entity_tp × weight)
weighted_total = Σ((entity_tp + entity_fn) × weight)
weighted_recall = weighted_tp / weighted_total
```

Zero-weight entities (EMAIL, LOCATION, PEDIATRIC_AGE) don't affect weighted metrics, accurately reflecting spoken handoff performance.

### Example Output

```
WEIGHTED METRICS (spoken handoff relevance):
  Weighted Recall:    91.5%
  Weighted Precision: 79.7%
  Weighted F2 Score:  88.8%  ← PRIMARY METRIC

  Weights applied:
    PERSON: 5
    GUARDIAN_NAME: 5
    ROOM: 4
    PHONE_NUMBER: 2
    DATE_TIME: 2
    MEDICAL_RECORD_NUMBER: 1
    EMAIL_ADDRESS: 0
    LOCATION: 0
    PEDIATRIC_AGE: 0
```

## Commits

1. `cfd5c8b` - Add spoken handoff relevance weights to config
2. `c8b8f96` - Add weighted metrics methods to EvaluationMetrics
3. `efbab8d` - Populate entity_stats during dataset evaluation
4. `761793a` - Add --weighted CLI flag to evaluation script
5. `af6c193` - Display weighted metrics in evaluation report
6. `fcdd7e6` - Add weighted metrics validation tests (11 tests)

## Testing

**Test Coverage:**
- ✅ Weighted recall matches SPOKEN_HANDOFF_ANALYSIS.md (~91.5%)
- ✅ Weighted precision/F2 calculations correct
- ✅ Zero-weight entities ignored properly
- ✅ Empty stats edge case handled
- ✅ Unknown entity types default to weight 0
- ✅ Configuration loading validated
- ✅ Weight value ranges checked (0-5 integers)

**All 11 tests passing** in test_weighted_metrics.py

## Deviations from Plan

None - plan executed exactly as written.

## Impact

**Before:** Unweighted recall (77.9%) underestimated actual spoken handoff performance

**After:** Weighted recall (91.5%) accurately reflects clinical relevance
- EMAIL addresses (never spoken, 100% recall) don't inflate metrics
- LOCATION (never spoken, 19% recall) doesn't penalize overall score
- PERSON/GUARDIAN names (constantly spoken, 98.8% recall) properly weighted

**Clinical Significance:** Metrics now align with real I-PASS handoff scenarios, providing accurate assessment for clinical deployment readiness.

## Next Phase Readiness

**Ready for:** External validation (Phase 5) with realistic spoken handoff metrics

**Dependencies Satisfied:**
- Weighted metrics infrastructure complete
- Backward compatible (existing scripts unchanged)
- Configurable weights (can adjust for different handoff types)
- Validated against SPOKEN_HANDOFF_ANALYSIS.md data

**Blockers:** None

**Concerns:** None - all success criteria met
