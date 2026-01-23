# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-23)

**Core value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content
**Current focus:** Phase 2: Threshold Calibration (COMPLETE)

## Current Position

Phase: 2 of 5 (Threshold Calibration)
Plan: 2 of 2 (Phase Complete)
Status: Phase complete
Last activity: 2026-01-23 — Completed 02-02-PLAN.md (apply thresholds)

Progress: [████░░░░░░] 40% (Phase 1 complete, Phase 2 complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 8
- Average duration: 5.6 min
- Total execution time: 0.75 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-baseline-measurement | 6/6 | 38 min | 6.3 min |
| 02-threshold-calibration | 2/2 | 9 min | 4.5 min |

**Recent Trend:**
- Last 5 plans: 01-04 (3min), 01-03-exec (12min), 01-02-exec (4min), 02-01 (6min), 02-02 (3min)
- Trend: Fast execution, threshold calibration completed in 9 min total

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

**Technical Debt:**
- ~~Current thresholds arbitrary (detection 0.35, validation 0.7)~~ **RESOLVED** (02-02: per-entity 0.30, aligned)
- ~~Detection/validation threshold mismatch (THRS-02)~~ **RESOLVED** (02-02: both use phi_score_thresholds)
- LOCATION deny list case-sensitive (inconsistent) — Phase 3 will fix
- Room number patterns too narrow (only "Room X" format) — Phase 4 priority #1
- Pediatric age abbreviation patterns missing — Phase 4 priority #2

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 001 | Investigate deidentification code | 2026-01-23 | 424cd44 | [001-investigate-deidentification-code](./quick/001-investigate-deidentification-code/) |

## Session Continuity

Last session: 2026-01-23
Stopped at: Completed Phase 2 (Threshold Calibration)
Resume file: None
Next: Phase 3 (Deny List Tuning) or Phase 4 (Pattern Improvements)

---
*State initialized: 2026-01-23*
*Last updated: 2026-01-23 21:46:30 UTC (after 02-02 completion)*
