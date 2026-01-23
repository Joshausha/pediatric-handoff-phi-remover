# Phase 2: Threshold Calibration Results

**Calibration Date:** 2026-01-23
**Methodology:** PR curve analysis, F2 optimization with 90% recall floor
**Datasets:** synthetic_handoffs.json (500) + adversarial_handoffs.json (100) = 600 handoffs

## Executive Summary

Threshold calibration reduced global threshold from 0.35 to 0.30 and implemented per-entity thresholds. Key findings:

1. **Threshold tuning has LIMITED impact** - Presidio scores cluster at extremes (0.0 or 0.85+), so threshold changes have minimal effect on most entities
2. **3 of 8 entities meet 90% recall floor** - PERSON (98.9%), EMAIL_ADDRESS (100%), DATE_TIME (95.1%)
3. **5 of 8 entities require Phase 4 pattern work** - Cannot achieve 90% recall through thresholds alone
4. **THRS-02 fixed** - Detection and validation now use same per-entity thresholds (was 0.35/0.7 mismatch)

## Before/After Comparison

### Overall Metrics

| Metric | Before (0.35 global) | After (0.30 per-entity) | Change |
|--------|---------------------|-------------------------|--------|
| Detection Threshold | 0.35 (all entities) | 0.30 (per-entity) | -0.05 |
| Validation Threshold | 0.70 (hardcoded) | 0.30 (same as detection) | -0.40 |
| Threshold Consistency | Mismatched (2x gap) | Aligned | Fixed |

### Per-Entity Changes

| Entity | Threshold Before | Threshold After | Recall (Combined Dataset) | Status |
|--------|-----------------|-----------------|---------------------------|--------|
| PERSON | 0.35 | 0.30 | 98.9% | >= 90% floor |
| PHONE_NUMBER | 0.35 | 0.30 | 75.7% | < 90% (Phase 4) |
| EMAIL_ADDRESS | 0.35 | 0.30 | 100.0% | >= 90% floor |
| DATE_TIME | 0.35 | 0.30 | 95.1% | >= 90% floor |
| LOCATION | 0.35 | 0.30 | 20.0% | < 90% (Phase 4) |
| MEDICAL_RECORD_NUMBER | 0.35 | 0.30 | 72.3% | < 90% (Phase 4) |
| ROOM | 0.35 | 0.30 | 32.1% | < 90% (Phase 4) |
| PEDIATRIC_AGE | 0.35 | 0.30 | 35.8% | < 90% (Phase 4) |

**Note:** Recall values are unchanged from baseline because Presidio score distribution has gaps between 0.0 and 0.85+. Lowering threshold from 0.35 to 0.30 doesn't capture additional entities.

## Calibrated Per-Entity Thresholds

All thresholds set to 0.30 based on F2 optimization with 90% recall constraint.

| Entity Type | Threshold | Precision | Recall | F1 | F2 | Rationale |
|-------------|-----------|-----------|--------|-----|-----|-----------|
| PERSON | 0.30 | 73.3% | 98.9% | 84.2% | 92.4% | Meets 90% floor, F2=92.4% optimal |
| PHONE_NUMBER | 0.30 | 99.4% | 75.7% | 85.9% | 79.5% | No threshold achieves 90% floor; 0.30 maximizes recall |
| EMAIL_ADDRESS | 0.30 | 100.0% | 100.0% | 100.0% | 100.0% | Perfect detection at all thresholds |
| DATE_TIME | 0.30 | 35.3% | 95.1% | 51.5% | 71.0% | Meets 90% floor; low precision is over-redaction |
| LOCATION | 0.30 | 70.3% | 20.0% | 31.1% | 23.3% | No threshold achieves 90% floor; pattern gaps |
| MEDICAL_RECORD_NUMBER | 0.30 | 89.2% | 72.3% | 79.8% | 75.1% | No threshold achieves 90% floor |
| ROOM | 0.30 | 53.1% | 32.1% | 40.0% | 34.8% | No threshold achieves 90% floor |
| PEDIATRIC_AGE | 0.30 | 85.1% | 35.8% | 50.4% | 40.5% | No threshold achieves 90% floor |
| GUARDIAN_NAME | 0.30 | - | - | - | - | Mapped to PERSON threshold |

## Threshold Mismatch Fix (THRS-02)

### Problem
Detection used 0.35 threshold, but validation used hardcoded 0.7 threshold - a 2x inconsistency.

### Solution
- Detection: Uses `settings.phi_score_thresholds[entity_type]` (default 0.30)
- Validation: Now uses same `settings.phi_score_thresholds[entity_type]` (was hardcoded 0.7)
- Fallback: Unknown entity types fall back to `settings.phi_score_threshold` (0.35)

### Implementation
```python
# Before (deidentification.py line ~272)
score_threshold=0.7  # Higher threshold for validation

# After
score_threshold=0.0  # Get all, filter by per-entity threshold below
# Then: if result.score >= _get_entity_threshold(result.entity_type)
```

## Entities Requiring Phase 4 Pattern Improvements

These 5 entities cannot achieve 90% recall through threshold tuning:

### 1. PEDIATRIC_AGE (35.8% recall, needs +54.2%)
**Root cause:** Pattern recognizer only matches "X years/months/days old" format
**Missing patterns:**
- Abbreviations: "17yo", "4 yo", "22mo", "3 mo"
- Day of life: "DOL 6", "day of life 7"
- Varied spacing: "3 weeks 2 days old"

### 2. ROOM (32.1% recall, needs +57.9%)
**Root cause:** Pattern only matches "Room X" format
**Missing patterns:**
- Unit prefixes: "bed 14", "bay 5", "isolette 21"
- Multi-part: "3-22", "4/11"
- Standalone digits in context: "admitted to 512"

### 3. LOCATION (20.0% recall, needs +70.0%)
**Root cause:** spaCy NER misses generic hospital/location names
**Missing patterns:**
- Hospital names: "Memorial Hospital", "General Hospital"
- Full addresses: "6270 Stanton Track Suite 710"
- City names without context

### 4. PHONE_NUMBER (75.7% recall, needs +14.3%)
**Root cause:** Some international/extension formats not covered
**Missing patterns:**
- International: "001-359-886-6201", "+1-496-268-9139"
- Dot separators: "594.480.2422"
- Extensions: "001-885-221-6484x1298"

### 5. MEDICAL_RECORD_NUMBER (72.3% recall, needs +17.7%)
**Root cause:** Some MRN formats not recognized
**Missing patterns:**
- Bare 7-digit numbers without "MRN" label
- Hash prefix: "#1234567" (addressed in Phase 1)

## DATE_TIME Precision Concern

DATE_TIME has high recall (95.1%) but very low precision (35.3%):
- 354 false positives (over-redaction) vs 193 true positives
- Over-redacting clinical time references, dosing schedules, etc.

**Recommendation for Phase 3/4:**
- Add clinical time patterns to deny list (e.g., "q4h", "BID", "PRN")
- Consider context-aware filtering for dosing schedules

## Key Insight: Score Distribution

Presidio confidence scores cluster at extremes:
- **Detected entities:** Score 0.85-1.0 (high confidence)
- **Missed entities:** Score 0.0 (not detected at all)
- **Gap:** Very few scores in 0.30-0.85 range

This means:
1. Lowering threshold from 0.35 to 0.30 has minimal impact
2. Pattern improvements (Phase 4) are essential for recall gains
3. Threshold tuning is mostly about consistency, not performance

## Implementation Files

### Updated Config (`app/config.py`)
```python
phi_score_thresholds: Dict[str, float] = Field(
    default={
        "PERSON": 0.30,
        "PHONE_NUMBER": 0.30,
        "EMAIL_ADDRESS": 0.30,
        "DATE_TIME": 0.30,
        "LOCATION": 0.30,
        "MEDICAL_RECORD_NUMBER": 0.30,
        "ROOM": 0.30,
        "PEDIATRIC_AGE": 0.30,
        "GUARDIAN_NAME": 0.30,
    },
    description="Per-entity confidence thresholds (Phase 2 calibrated 2026-01-23)"
)
```

### Updated Detection (`app/deidentification.py`)
- `_get_entity_threshold()` helper function
- `deidentify_text()` uses per-entity filtering
- `validate_deidentification()` uses same thresholds as detection

## Raw Data References

| File | Purpose |
|------|---------|
| `tests/results/optimal_thresholds.json` | Per-entity thresholds with rationale |
| `tests/results/threshold_sweep.json` | Full sweep results (4 thresholds x 8 entities) |
| `tests/results/pr_curves/*.png` | PR curve visualizations |
| `tests/calibrate_thresholds.py` | Calibration script (741 lines) |

## Success Criteria Verification

| Criteria | Status |
|----------|--------|
| Per-entity thresholds integrated into production code | Done (config.py) |
| Detection and validation thresholds aligned (THRS-02) | Done (deidentification.py) |
| Recall improvement documented with actual metrics | Done (this document) |
| Threshold rationale documented for reproducibility | Done (optimal_thresholds.json) |
| Entities requiring Phase 4 work clearly identified | Done (5 entities listed) |

---
*Calibrated: 2026-01-23*
*Next: Phase 3 (Deny List Tuning) or Phase 4 (Pattern Improvements)*
