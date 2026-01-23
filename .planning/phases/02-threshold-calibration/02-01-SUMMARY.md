---
phase: 02-threshold-calibration
plan: 01
subsystem: testing
tags: [sklearn, matplotlib, precision-recall, F2, threshold-optimization]

# Dependency graph
requires:
  - phase: 01-baseline-measurement
    provides: evaluation infrastructure (evaluate_presidio.py, generate_test_data.py, datasets)
provides:
  - Per-entity threshold calibration script
  - PR curve visualizations for all 8 entity types
  - Optimal threshold recommendations with rationale
  - Baseline calibration data for Phase 4 pattern improvements
affects: [02-threshold-calibration, 03-deny-list-tuning, 04-pattern-improvements, 05-validation]

# Tech tracking
tech-stack:
  added: [matplotlib, scikit-learn]
  patterns: [per-entity threshold calibration, F2 optimization with recall floor]

key-files:
  created:
    - tests/calibrate_thresholds.py
    - tests/results/optimal_thresholds.json
    - tests/results/threshold_sweep.json
    - tests/results/pr_curves/*.png
  modified: []

key-decisions:
  - "Use 0.30 threshold universally (lowest tested threshold maximizes recall for all entities)"
  - "5 of 8 entities cannot achieve 90% recall through threshold tuning alone - require Phase 4 pattern improvements"
  - "Combined standard (500) + adversarial (100) datasets for calibration (600 total handoffs)"

patterns-established:
  - "Per-entity threshold sweep: test at [0.30, 0.40, 0.50, 0.60] with 90% recall floor"
  - "F2 maximization with recall constraint: reject thresholds below floor, maximize F2 among safe options"
  - "Tie-breaking: when F2 within 0.5%, prefer higher recall"

# Metrics
duration: 6min
completed: 2026-01-23
---

# Phase 2 Plan 1: Threshold Calibration Summary

**Per-entity threshold calibration reveals 5/8 entities require pattern improvements (Phase 4), with 3/8 meeting 90% recall floor (PERSON, EMAIL_ADDRESS, DATE_TIME)**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-23T21:34:34Z
- **Completed:** 2026-01-23T21:40:10Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Created comprehensive threshold calibration script (741 lines) with CLI interface
- Generated PR curve visualizations for all 8 entity types
- Identified that threshold tuning alone insufficient for 5 entities - documented need for Phase 4 pattern improvements
- Established baseline calibration data: 0.30 threshold optimal for all entities (maximizes recall)

## Calibration Results

| Entity Type | Optimal Threshold | Precision | Recall | F2 | Meets 90% Floor |
|-------------|-------------------|-----------|--------|----|-----------------|
| PERSON | 0.30 | 73.3% | 98.9% | 92.4% | Yes |
| PHONE_NUMBER | 0.30 | 99.4% | 75.7% | 79.5% | No |
| EMAIL_ADDRESS | 0.30 | 100.0% | 100.0% | 100.0% | Yes |
| DATE_TIME | 0.30 | 35.3% | 95.1% | 71.0% | Yes |
| LOCATION | 0.30 | 70.3% | 20.0% | 23.3% | No |
| MEDICAL_RECORD_NUMBER | 0.30 | 89.2% | 72.3% | 75.1% | No |
| ROOM | 0.30 | 53.1% | 32.1% | 34.8% | No |
| PEDIATRIC_AGE | 0.30 | 85.1% | 35.8% | 40.5% | No |

## Task Commits

Each task was committed atomically:

1. **Task 1: Create threshold calibration script** - `7eff9ea` (feat)
2. **Task 2: Generate PR curves and optimal thresholds** - `a874707` (feat)

## Files Created/Modified

- `tests/calibrate_thresholds.py` - Threshold calibration script with CLI (741 lines)
- `tests/results/optimal_thresholds.json` - Per-entity optimal thresholds with metrics and rationale
- `tests/results/threshold_sweep.json` - Full sweep results for all entity × threshold combinations
- `tests/results/pr_curves/PERSON.png` - PR curve visualization
- `tests/results/pr_curves/PHONE_NUMBER.png` - PR curve visualization
- `tests/results/pr_curves/EMAIL_ADDRESS.png` - PR curve visualization
- `tests/results/pr_curves/DATE_TIME.png` - PR curve visualization
- `tests/results/pr_curves/LOCATION.png` - PR curve visualization
- `tests/results/pr_curves/MEDICAL_RECORD_NUMBER.png` - PR curve visualization
- `tests/results/pr_curves/ROOM.png` - PR curve visualization
- `tests/results/pr_curves/PEDIATRIC_AGE.png` - PR curve visualization

## Decisions Made

1. **Universal 0.30 threshold** - Lowest tested threshold (0.30) provides maximum recall for all entity types. Higher thresholds do not improve performance for most entities (Presidio scores cluster at extremes 0.0 or 0.85+).

2. **Pattern improvements required for 5 entities** - PHONE_NUMBER, LOCATION, MEDICAL_RECORD_NUMBER, ROOM, PEDIATRIC_AGE cannot achieve 90% recall through threshold tuning alone. These require Phase 4 pattern improvements to address recognition gaps.

3. **Combined dataset calibration** - Used both standard (seed=42, 500 handoffs) and adversarial (seed=43, 100 handoffs) datasets for more robust threshold selection. Total: 600 handoffs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing matplotlib and scikit-learn**
- **Found during:** Task 1 (script execution)
- **Issue:** matplotlib and scikit-learn not installed in venv
- **Fix:** Ran `pip install matplotlib scikit-learn` in venv
- **Files modified:** venv (not committed)
- **Verification:** Script runs successfully
- **Committed in:** N/A (dependency installation, not code change)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential dependency for PR curve generation. No scope creep.

## Issues Encountered

- Presidio confidence scores cluster at extremes (0.0 for misses, 0.85+ for detections), making threshold sweep show identical results across 0.30-0.50 range for most entities. This is expected behavior - Presidio's pattern-based recognizers produce high-confidence matches or no matches.

## Key Insight

**Threshold calibration has limited impact on recall.** The core issue is that Presidio's recognizers either:
1. Detect entities with high confidence (0.85+) - these are already captured at any reasonable threshold
2. Miss entities entirely (0.0 score) - no threshold can recover these

For entities below 90% recall, the problem is recognition patterns, not confidence thresholds. Phase 4 pattern improvements are essential.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for:**
- Phase 2 Plan 2 (if any): Apply optimal thresholds to config.py
- Phase 3 (Deny List Tuning): Can proceed independently
- Phase 4 (Pattern Improvements): Critical - 5 entities require pattern work to achieve 90% recall

**Blockers:**
- None - calibration complete with documented recommendations

**Concerns:**
- DATE_TIME has high recall (95.1%) but very low precision (35.3%) - over-redacting clinical content
- LOCATION recall (20%) extremely low - deny list and pattern improvements both needed

---
*Phase: 02-threshold-calibration*
*Completed: 2026-01-23*
