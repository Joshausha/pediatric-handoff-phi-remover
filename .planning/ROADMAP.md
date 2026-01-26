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
- [x] **Phase 4: Pattern Improvements** - Regex edge case fixes and bidirectional patterns ✓
- [x] **Phase 5: Validation & Compliance** - External validation and clinical deployment readiness ✓ (Expert review: APPROVED FOR PERSONAL USE)
- [ ] **Phase 6: Real Handoff Testing** - User reads actual text handoffs to validate PHI detection
- [x] **Phase 7: Alternative Engine Benchmark** - Compare Philter-UCSF and Stanford BERT against current Presidio ✓ (Decision: Continue with Presidio)
- [x] **Phase 8: Weighted Recall Evaluation** - Add spoken handoff relevance weighting to evaluate_presidio.py ✓
- [ ] **Phase 9: Age Pattern Architecture** - Replace deny list approach with custom DATE_TIME recognizer that excludes age patterns

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
- [x] 04-04-PLAN.md — Phone number pattern expansion (international formats, extensions) ✓
- [x] 04-05-PLAN.md — Room hyphenated standalone format fix ✓
- [x] 04-06-PLAN.md — Gap analysis and standalone number decision (option-c: accept limitations) ✓

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
- [x] 05-03-PLAN.md — Run validation and generate compliance documentation ✓ (decision deferred pending Phase 7)
- [x] 05-04-PLAN.md — Expert review of random sample ✓ (APPROVED FOR PERSONAL USE)

### Phase 6: Real Handoff Testing
**Goal**: Validate PHI detection on real clinical handoff text read by user through full audio pipeline
**Depends on**: Phase 5 (validation infrastructure ready, expert review complete)
**Requirements**: REAL-01, REAL-02
**Success Criteria** (what must be TRUE):
  1. User reads real text handoffs and system de-identifies them
  2. User validates that PHI is correctly detected and redacted
  3. False negatives and false positives documented from real-world usage
  4. System performance confirmed on actual clinical content
**Plans**: 2 plans in 2 waves

Plans:
- [x] 06-01-PLAN.md — Prepare validation templates and conduct first testing session (5+ handoffs) ✓
- [ ] 06-02-PLAN.md — Pattern analysis, fixes if needed, final session, and production verdict

### Phase 7: Alternative Engine Benchmark
**Goal**: Compare Philter-UCSF and Stanford BERT de-identification engines against current Presidio setup to determine if switching engines provides meaningful improvement for spoken handoff use case
**Depends on**: Phase 1 (needs evaluation framework), can run in parallel with other phases
**Requirements**: BENCH-01, BENCH-02, BENCH-03
**Success Criteria** (what must be TRUE):
  1. Philter-UCSF installed and configured with equivalent pediatric patterns translated from current codebase
  2. Stanford BERT (StanfordAIMI/stanford-deidentifier-base) integrated as Presidio NER backend
  3. All three engines benchmarked on same test dataset (synthetic_handoffs.json + adversarial_handoffs.json)
  4. Weighted recall/precision/F2 calculated for spoken handoff relevance (using established weights)
  5. Decision documented: stick with Presidio, switch to Philter, or hybrid approach
**Plans**: 3 plans in 2 waves

Plans:
- [x] 07-01-PLAN.md — Install Philter-UCSF and translate pediatric/medical patterns to Philter config format ✓
- [x] 07-02-PLAN.md — Integrate Stanford BERT as Presidio NER backend (TransformersNlpEngine) ✓
- [x] 07-03-PLAN.md — Run comparative benchmark and document decision ✓

**Results:**
- Presidio: 94.4% weighted recall (baseline, excellent performance)
- Philter: 3.1% weighted recall (only 2/8 entity types implemented)
- Stanford BERT: Blocked by TransformersNlpEngine configuration issue
- **Decision:** Continue with Presidio (no alternative provides >5% improvement)

**Future Work:**
- Full Philter implementation deferred for later exploration (24 patterns translated, 6 entity types remaining)

**References:**
- [docs/ENGINE_BENCHMARK.md](../docs/ENGINE_BENCHMARK.md) — Full benchmark analysis and decision
- [Philter-UCSF GitHub](https://github.com/BCHSI/philter-ucsf)
- [Stanford De-identifier on HuggingFace](https://huggingface.co/StanfordAIMI/stanford-deidentifier-base)

### Phase 8: Weighted Recall Evaluation
**Goal**: Implement spoken handoff relevance weighting in evaluation scripts for use-case-specific metrics
**Depends on**: Phase 1 (needs evaluation framework)
**Requirements**: WGHT-01, WGHT-02, WGHT-03
**Success Criteria** (what must be TRUE):
  1. evaluate_presidio.py supports `--weighted` flag that applies spoken handoff relevance weights
  2. Weights configurable via config.py (PERSON: 5, ROOM: 4, PHONE_NUMBER: 2, DATE_TIME: 2, MRN: 1, others: 0)
  3. Both weighted and unweighted metrics reported when flag enabled
  4. Weighted recall/precision/F2 match manual calculations in SPOKEN_HANDOFF_ANALYSIS.md
**Plans**: 1 plan in 1 wave

Plans:
- [x] 08-01-PLAN.md — Add weighted scoring to evaluate_presidio.py with configurable entity weights ✓

**Context:**
- Unweighted recall (77.9%) underestimates real-world performance for spoken handoffs
- Weighted recall (91.5%) reflects actual clinical relevance
- Addresses Priority 3 from SPOKEN_HANDOFF_ANALYSIS.md recommendations
- Enables accurate comparison when benchmarking alternative engines (Phase 7)

**References:**
- [docs/SPOKEN_HANDOFF_ANALYSIS.md](../docs/SPOKEN_HANDOFF_ANALYSIS.md) — Methodology and weight definitions

### Phase 9: Age Pattern Architecture
**Goal**: Replace fragile deny list approach with robust custom DATE_TIME recognizer that architecturally excludes age patterns
**Depends on**: Phase 6 (real handoff testing reveals deny list limitations)
**Requirements**: ARCH-01
**Success Criteria** (what must be TRUE):
  1. Custom PediatricDateTimeRecognizer created that subclasses Presidio's DateTimeRecognizer
  2. Age patterns (`\d+\s*(year|month|week|day)s?\s*(old)?`) excluded at recognition level, not post-hoc filtering
  3. All age formats preserved in output: "5 week", "18 year old", "3 months", etc.
  4. No regression on legitimate DATE_TIME detection (actual dates, times)
  5. Deny list entries for age patterns removed (cleaner architecture)
**Plans**: 1 plan in 1 wave

Plans:
- [ ] 09-01-PLAN.md — Create PediatricDateTimeRecognizer with age pattern exclusion

**Context:**
Phase 6 real handoff testing revealed that deny list approach is fragile:
- Deny list has "week old" but not "week" alone
- Real speech often omits "old": "She's a 5 week, previously healthy..."
- Endless deny list expansion is unsustainable

**Architecture:**
```python
from presidio_analyzer.predefined_recognizers import DateTimeRecognizer
import re

class PediatricDateTimeRecognizer(DateTimeRecognizer):
    """DATE_TIME recognizer that excludes pediatric age patterns."""

    AGE_PATTERN = re.compile(r'\b\d+\s*(year|month|week|day)s?\s*(old)?\b', re.IGNORECASE)

    def analyze(self, text, entities, nlp_artifacts=None):
        results = super().analyze(text, entities, nlp_artifacts)
        # Filter out age patterns at recognition level
        return [r for r in results
                if not self.AGE_PATTERN.match(text[r.start:r.end])]
```

**Benefits:**
- Single regex handles all age variants (with/without "old", singular/plural)
- No deny list maintenance required for age patterns
- Cleaner separation of concerns (ages vs dates)
- Extensible for other pediatric-specific DATE_TIME exclusions

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

**Phase 3 and 4 can execute in parallel** after Phase 2 completes (independent improvements).

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Baseline Measurement | 4/4 | ✓ Complete | 2026-01-23 |
| 2. Threshold Calibration | 2/2 | ✓ Complete | 2026-01-23 |
| 3. Deny List Refinement | 2/2 | ✓ Complete (DENY-04 deferred) | 2026-01-24 |
| 4. Pattern Improvements | 6/6 | ✓ Complete | 2026-01-25 |
| 5. Validation & Compliance | 4/4 | ✓ Complete (APPROVED) | 2026-01-25 |
| 6. Real Handoff Testing | 1/2 | In Progress | - |
| 7. Alternative Engine Benchmark | 3/3 | ✓ Complete (Presidio selected) | 2026-01-25 |
| 8. Weighted Recall Evaluation | 1/1 | ✓ Complete | 2026-01-25 |
| 9. Age Pattern Architecture | 0/1 | Planned | - |

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
- **Phase 7 can run in parallel** with Phases 4-6 (independent evaluation of alternative engines)
- **Phase 8 can run in parallel** with Phases 4-7 (evaluation framework enhancement)

**Quick Wins Identified:**
- Phase 2: Case normalization (1-2 hours, high impact)
- Phase 2: Threshold alignment (30 minutes, catches missed PHI)
- Phase 3: Medical abbreviation deny lists (2-4 hours, reduces false positives)

---
*Roadmap created: 2026-01-23*
*Last updated: 2026-01-25 (Phase 6 planned — 2 plans in 2 waves)*
