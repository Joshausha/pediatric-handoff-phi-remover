# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-23)

**Core value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content
**Current focus:** Phase 5: External Validation (NEXT)

## Current Position

Phase: 4 of 5 (Pattern Improvements) - GAPS FOUND
Plan: 3 of 3 complete + gap closure needed
Status: Validation revealed pattern gaps requiring Phase 4 improvements
Last activity: 2026-01-24 — Phase 5 validation: 83% recall [81%, 85%], need 95%

Progress: [███████░░░] 70% (Phases 1-4 executed, gaps found in validation)

### Validation Gap Summary (from 05-03)

**Recall:** 83.0% (95% CI: 81.0% - 84.8%) — Target: 95%
**False negatives:** 257 PHI spans missed

| Failure Mode | Count | Top Entities |
|--------------|-------|--------------|
| pattern_miss | 246 | ROOM (standalone numbers), MRN (no # prefix), LOCATION (addresses) |
| span_boundary | 11 | ROOM (hyphenated like 3-22) |

**Gap closure needed for:**
1. ROOM - standalone numbers (847, 16, 8) without "Room" prefix
2. MEDICAL_RECORD_NUMBER - 7-digit numbers without # prefix (2694522)
3. LOCATION - full addresses missed by spaCy NER
4. PHONE_NUMBER - international format (001-411-671-8227)

## Performance Metrics

**Velocity:**
- Total plans completed: 15
- Average duration: 5.2 min
- Total execution time: 1.3 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-baseline-measurement | 6/6 | 38 min | 6.3 min |
| 02-threshold-calibration | 2/2 | 9 min | 4.5 min |
| 03-deny-list-refinement | 2/2 | 5 min | 2.5 min |
| 04-pattern-improvements | 3/3 | 21 min | 7.0 min |
| 05-validation-compliance | 2/3 | 6 min | 3.0 min |

**Recent Trend:**
- Last 5 plans: 04-01 (9min), 04-02 (4min), 04-03 (8min), 05-01 (3min), 05-02 (3min)
- Trend: Infrastructure setup faster than pattern work

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Metrics-based success criteria (Research setting needs defensible evidence; 500 synthetic transcripts enable measurement)
- Balanced precision/recall trade-off (Clinical utility requires readable transcripts; pure aggressive approach over-redacts)
- Case-insensitive deny lists (Consistency prevents edge case bugs; clinical terms appear in various cases)
- F2 as primary metric for PHI detection (False negatives more dangerous than false positives; beta=2 weights recall 2x precision) — From 01-01
- Confusion matrix export as separate CLI flag (Enables threshold calibration without cluttering default output) — From 01-01
- Threshold defaults (recall 95%, precision 70%, F2 90%) (Balance HIPAA compliance with clinical utility) — From 01-04
- CI/CD as v2 implementation (Manual validation sufficient for Phase 1 research focus) — From 01-04
- Separate CI jobs for PHI vs unit tests (Enables parallel execution and independent failure analysis) — From 01-04
- Seed=43 for adversarial dataset (Maintains separation from standard dataset seed=42, enables reproducibility) — From 01-03
- 100 adversarial samples sufficient (Provides full template coverage while keeping evaluation fast) — From 01-03
- 6-category adversarial organization (Groups edge cases by weakness type for clear Phase 4 targeting) — From 01-03
- MEAS-02 deferral to Phase 5 (Human-annotated gold standard requires IRB coordination; synthetic datasets sufficient for Phase 1 baseline) — From 01-02
- Baseline documentation captures 77.9% recall (Defensible research evidence for "before" snapshot; all improvements measured against this timestamp) — From 01-02
- **Universal 0.30 threshold** (Lowest threshold maximizes recall; Presidio scores cluster at extremes) — From 02-01
- **5/8 entities require Phase 4 pattern improvements** (PHONE_NUMBER, LOCATION, MRN, ROOM, PEDIATRIC_AGE cannot achieve 90% recall via thresholds) — From 02-01
- **Combined dataset calibration** (600 handoffs: 500 standard + 100 adversarial for robust threshold selection) — From 02-01
- **Per-entity threshold dict** (Enables future per-entity tuning; replaces global threshold) — From 02-02
- **THRS-02 fix: aligned thresholds** (Detection and validation now use same per-entity thresholds) — From 02-02
- **Case-insensitive deny lists** (Consistency prevents edge case bugs; clinical terms appear in various cases) — From 03-01
- **Dosing schedules in DATE_TIME deny list** (Reduces precision drop from 35.3% by filtering clinical abbreviations) — From 03-01
- **Generic age categories in PEDIATRIC_AGE deny list** (Prevents over-redaction of clinical descriptors) — From 03-01
- **Test files intentionally duplicate deny list filtering logic** (Maintains test isolation and keeps evaluation/calibration scripts self-contained) — From 03-02
- **DENY-04 targets not met via deny lists alone** (4.1% FP reduction vs 20% target; deny lists preventative not corrective) — From 03-02
- **Word boundary with (?i) flag instead of lookbehind** (Lookbehind fails at start-of-line position 0) — From 04-02
- **Presidio replaces entire matched span, not capture groups** (Tests verify unit names in surrounding context) — From 04-02
- **Lookbehind with (?i) flag works for guardian patterns** (Matches only the name, preserves relationship word) — From 04-01
- **Lookahead for bidirectional patterns** (`Jessica is Mom` -> match only "Jessica") — From 04-01
- **Pediatric descriptors added to PERSON deny list** (baby, infant, newborn, neonate) — From 04-01
- **PEDIATRIC_AGE recognizer DISABLED** (Ages not PHI under HIPAA unless 90+; preserved for clinical utility) — From 04-03
- **Regression test thresholds** (Guardian >80%, Room >40%, standard entities >90%) — From 04-03
- **Target validation sample: 200 transcripts** (Minimum viable: 50; narrow confidence intervals for >95% recall verification) — From 05-01
- **Stratification by dominant PHI type** (Preserves entity distribution from synthetic to validation data) — From 05-01
- **70/30 val/test split** (No training needed - tuning on val, final metrics on test) — From 05-01
- **Bootstrap percentile method with 10k iterations** (Standard bootstrap approach, computationally tractable, provides stable 95% CI) — From 05-02
- **6 failure modes for error taxonomy** (Covers all major detection failure mechanisms, enables targeted improvements) — From 05-02
- **--with-ci flag optional** (Bootstrap is slow, only calculate when needed for formal validation) — From 05-02

### Pending Todos

None yet.

### Blockers/Concerns

**From Research:**
- Synthetic data may not represent real transcripts — external validation in Phase 5 is critical
- Weakest entities (PEDIATRIC_AGE 25% adversarial recall, ROOM 19% adversarial recall) require significant pattern work in Phase 4

**From Threshold Calibration:**
- Threshold tuning has LIMITED impact on recall — Presidio scores cluster at extremes (0.0 or 0.85+)
- 5/8 entities cannot achieve 90% recall through thresholds alone:
  - PHONE_NUMBER: 75.7% recall (pattern improvements needed)
  - LOCATION: 20.0% recall (pattern improvements + deny list tuning needed)
  - MEDICAL_RECORD_NUMBER: 72.3% recall (pattern improvements needed)
  - ROOM: 32.1% recall (pattern improvements needed)
  - PEDIATRIC_AGE: 35.8% recall (pattern improvements needed)
- DATE_TIME: High recall (95.1%) but LOW precision (35.3%) — over-redacting clinical content

**From Deny List Refinement:**
- Deny list impact on precision is LIMITED — only 4.1% false positive reduction (27 of 662 FPs filterable)
- Most false positives (635) are over-detections requiring Phase 4 pattern refinement
- Precision improvement: 66.3% → 67.2% (+0.9%) — modest gains via deny lists
- Deny lists are preventative (filter known safe terms), not corrective (don't fix pattern weaknesses)

**From Pattern Improvements (04-01):**
- NER overlap with custom patterns causes over-redaction in some cases ("Grandma Rosa" detected as full PERSON)
- Lowercase variants work correctly; capitalized variants may over-redact when NER takes precedence
- This is safe (over-redaction) but not ideal for readability

**Technical Debt:**
- ~~Current thresholds arbitrary (detection 0.35, validation 0.7)~~ **RESOLVED** (02-02: per-entity 0.30, aligned)
- ~~Detection/validation threshold mismatch (THRS-02)~~ **RESOLVED** (02-02: both use phi_score_thresholds)
- ~~LOCATION deny list case-sensitive (inconsistent)~~ **RESOLVED** (03-01: case-insensitive filtering)
- ~~Room number patterns too narrow (only "Room X" format)~~ **RESOLVED** (04-02: case-insensitive, bay, isolette, multipart)
- ~~Guardian name patterns need case-insensitivity~~ **RESOLVED** (04-01: all patterns now case-insensitive)
- ~~Pediatric age abbreviation patterns still need work~~ **RESOLVED** (04-03: PEDIATRIC_AGE disabled, ages not PHI)
- 8 pre-existing test failures from Phase 3 deny list changes need test expectation updates

**From Pattern Improvements (04-03):**
- ROOM recall improved from 32.1% to 43.3% (+35% relative improvement) but still below 90% target
- LOCATION recall (19.4%) remains very low - fundamental Presidio NER limitation with address formats
- DATE_TIME precision (37.5%) causes over-redaction - may need deny list expansion in Phase 5

**From Bootstrap CI & Error Taxonomy (05-02):**
- ⚠️ Pre-existing numpy compatibility error in environment (numpy.dtype size changed)
- This is a thinc/spacy/numpy version mismatch in system Python, unrelated to plan changes
- Bootstrap CI functionality verified via unit tests, full integration testing blocked by environment issue

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 001 | Investigate deidentification code | 2026-01-23 | 424cd44 | [001-investigate-deidentification-code](./quick/001-investigate-deidentification-code/) |

## Session Continuity

Last session: 2026-01-24
Stopped at: Phase 5 validation revealed gaps — returning to Phase 4
Resume file: .planning/phases/05-validation-compliance/validation_results.json
Next: `/gsd:plan-phase 4 --gaps` to create gap closure plans

---
*State initialized: 2026-01-23*
*Last updated: 2026-01-24 (Validation gaps found, returning to Phase 4)*
