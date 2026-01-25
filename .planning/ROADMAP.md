# Roadmap: PHI Detection Overhaul

## Overview

This quality improvement project transforms the PHI detection system from 77.9% recall to >95% recall through systematic measurement, calibration, and refinement. Starting with baseline metrics, we'll optimize thresholds, enhance deny lists, fix regex patterns, and validate against real transcripts—delivering HIPAA-compliant de-identification ready for clinical deployment.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Baseline Measurement** - Establish evaluation framework and gold standard dataset ✓
- [x] **Phase 2: Threshold Calibration** - Data-driven threshold optimization with F2 score ✓
- [x] **Phase 3: Deny List Refinement** - Medical vocabulary filtering and case normalization ✓ (DENY-04 deferred to Phase 4)
- [ ] **Phase 4: Pattern Improvements** - Regex edge case fixes and bidirectional patterns (GAP CLOSURE IN PROGRESS)
- [ ] **Phase 5: Validation & Compliance** - External validation and clinical deployment readiness

## Phase Details

### Phase 1: Baseline Measurement
**Goal**: Establish rigorous evaluation framework with gold standard dataset and per-entity metrics
**Depends on**: Nothing (first phase)
**Requirements**: MEAS-01, MEAS-02, MEAS-03, MEAS-04
**Success Criteria** (what must be TRUE):
  1. System generates precision/recall/F1/F2 metrics for all 8 entity types (EMAIL, PERSON, DATE_TIME, PHONE, MRN, PEDIATRIC_AGE, ROOM, GUARDIAN_NAME)
  2. Gold standard test dataset exists with human-annotated PHI (50+ transcripts, inter-rater kappa >0.8)
  3. Baseline metrics are documented showing current performance: 77.9% recall, 87.4% precision, F1 0.82
  4. F2 score (recall-weighted) is calculated and established as primary optimization target
**Plans**: 4 plans in 2 waves

Plans:
- [x] 01-01-PLAN.md — Enhance evaluation infrastructure (F2 score, confusion matrix) ✓
- [x] 01-02-PLAN.md — Document baseline state (BASELINE_METRICS.md) ✓
- [x] 01-03-PLAN.md — Create adversarial synthetic dataset (edge case testing) ✓
- [x] 01-04-PLAN.md — Document CI/CD integration strategy ✓

### Phase 2: Threshold Calibration
**Goal**: Optimize detection and validation thresholds using precision-recall curve analysis
**Depends on**: Phase 1 (needs evaluation framework)
**Requirements**: THRS-01, THRS-02, THRS-03, THRS-04
**Success Criteria** (what must be TRUE):
  1. Precision-recall curves generated for all entity types across threshold range (0.3-0.6)
  2. Detection threshold calibrated with documented rationale (currently 0.35 arbitrary)
  3. Validation threshold aligned with detection threshold (fixes current 0.35/0.7 mismatch)
  4. Overall recall improved to >90% through threshold optimization alone
  5. Threshold calibration methodology documented in config.py with supporting metrics
**Plans**: 2 plans in 2 waves

Plans:
- [x] 02-01-PLAN.md — Create threshold calibration script and generate PR curves ✓
- [x] 02-02-PLAN.md — Apply calibrated thresholds to codebase and document results ✓

### Phase 3: Deny List Refinement
**Goal**: Reduce false positives through expanded medical vocabulary deny lists with consistent case handling
**Depends on**: Phase 2 (thresholds must be calibrated first)
**Requirements**: DENY-01, DENY-02, DENY-03, DENY-04
**Success Criteria** (what must be TRUE):
  1. All deny lists use case-insensitive matching (fixes LOCATION exact match bug)
  2. Medical abbreviation deny list expanded to cover common clinical terms (NC, RA, OR, ER, IV, PO, IM, SQ, PR, GT, NG, OG, NJ, ED)
  3. Deny lists exist for all custom entity types (GUARDIAN_NAME, PEDIATRIC_AGE)
  4. False positive rate reduced by >20% (precision improved from 87.4% to >90%)
**Plans**: 2 plans in 2 waves

Plans:
- [x] 03-01-PLAN.md — Fix case-insensitive bug and add new deny lists to config.py and deidentification.py ✓
- [x] 03-02-PLAN.md — Mirror deny list changes in test files and add regression tests ✓

### Phase 4: Pattern Improvements
**Goal**: Fix regex edge cases and enhance custom recognizers to catch all PHI variants
**Depends on**: Phase 2 (thresholds must be calibrated first)
**Requirements**: PATT-01, PATT-02, PATT-03, PATT-04, PATT-05, PATT-06
**Success Criteria** (what must be TRUE):
  1. Lookbehind patterns catch edge cases (start-of-line, punctuation, word boundaries like "mom jessica" not just "Mom Jessica")
  2. Bidirectional patterns implemented ("Jessica is Mom" caught, not just "Mom Jessica")
  3. Speech-to-text artifacts handled (stutters, corrections, hesitations in transcripts)
  4. PEDIATRIC_AGE recall improved from 36.6% to >90% (currently weakest entity type)
  5. ROOM recall improved from 34.4% to >90% (currently weakest entity type)
  6. Regression test suite covers all edge cases with pytest parameterized tests
**Plans**: 6 plans in 2 waves

Plans:
- [x] 04-01-PLAN.md — Guardian and baby name pattern improvements (case-insensitive, bidirectional, speech artifacts) ✓
- [x] 04-02-PLAN.md — Room and MRN pattern improvements (case-insensitive, expanded formats) ✓
- [x] 04-03-PLAN.md — PEDIATRIC_AGE decision checkpoint and regression test suite ✓
- [ ] 04-04-PLAN.md — Phone number pattern expansion (international formats, extensions) [GAP CLOSURE]
- [ ] 04-05-PLAN.md — Room hyphenated standalone format fix [GAP CLOSURE]
- [ ] 04-06-PLAN.md — Gap analysis and standalone number decision [GAP CLOSURE]

### Phase 5: Validation & Compliance
**Goal**: Validate performance on synthetic corpus (with real data validation deferred to IRB availability) and achieve >95% recall for personal clinical deployment readiness
**Depends on**: Phases 3 and 4 (all improvements complete)
**Requirements**: VALD-01, VALD-02, VALD-03, VALD-04
**Success Criteria** (what must be TRUE):
  1. Validation infrastructure ready for real transcripts; synthetic corpus used as proxy until IRB data available
  2. Error analysis identifies and categorizes patterns in missed PHI (false negative taxonomy)
  3. Expert review completed on random sample validates detection quality (user serves as clinical expert for personal QI project)
  4. Overall recall achieves >95% target on validation set (clinical deployment threshold met)
  5. Residual risk calculated with 95% confidence interval for HIPAA compliance documentation
**Plans**: 4 plans in 3 waves

Plans:
- [x] 05-01-PLAN.md — Create validation data pipeline (annotation schema, dataset loader) ✓
- [x] 05-02-PLAN.md — Add bootstrap CI and error taxonomy to evaluation infrastructure ✓
- [ ] 05-03-PLAN.md — Run validation and generate compliance documentation (BLOCKED - waiting for 04 gap closure)
- [ ] 05-04-PLAN.md — Expert review of random sample (user as clinical expert)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

**Phase 3 and 4 can execute in parallel** after Phase 2 completes (independent improvements).

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Baseline Measurement | 4/4 | ✓ Complete | 2026-01-23 |
| 2. Threshold Calibration | 2/2 | ✓ Complete | 2026-01-23 |
| 3. Deny List Refinement | 2/2 | ✓ Complete (DENY-04 deferred) | 2026-01-24 |
| 4. Pattern Improvements | 3/6 | Gap Closure | 2026-01-24 |
| 5. Validation & Compliance | 2/4 | Blocked by Phase 4 | - |

---

**Gap Closure Context (04-04 through 04-06):**

Phase 5 validation revealed 83% recall (target 95%), with 257 false negatives:
- PHONE_NUMBER: International formats (001-, +1-), extensions (x12345), dot separators
- ROOM: Hyphenated standalone (3-22), raw numbers (847, 16)
- MRN: Unprefixed 7-8 digit numbers
- LOCATION: Full addresses (NER limitation, not addressable)

Plans 04-04 and 04-05 address easy wins. Plan 04-06 analyzes remaining gaps and captures decision on risky patterns.

---

**Dependencies Summary:**
- Phase 1 blocks all other phases (measurement framework required)
- Phase 2 blocks Phases 3-4 (threshold calibration required before pattern tuning)
- Phases 3-4 can run in parallel (deny lists and regex improvements are independent)
- Phase 5 requires Phases 3-4 complete (validation needs all improvements in place)

**Quick Wins Identified:**
- Phase 2: Case normalization (1-2 hours, high impact)
- Phase 2: Threshold alignment (30 minutes, catches missed PHI)
- Phase 3: Medical abbreviation deny lists (2-4 hours, reduces false positives)

---
*Roadmap created: 2026-01-23*
*Last updated: 2026-01-24 (Phase 4 gap closure plans created)*
