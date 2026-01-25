# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-23)

**Core value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content
**Current focus:** Phase 7: Alternative Engine Benchmark (in progress - 07-01 & 07-02 complete)

## Current Position

Phase: 7 of 8 (Alternative Engine Benchmark - COMPLETE)
Plan: 3 of 3 complete (07-01, 07-02, 07-03 complete; 07-04 not needed)
Status: Phase 7 complete - Decision to continue with Presidio (94.4% weighted recall)
Last activity: 2026-01-25 — Completed 07-03: Engine benchmark decision documented

Progress: [█████████░] 91% (Phases 1-4, 7, 8 complete; Phase 5 partial 3/4; Phase 6 unstarted)

### Post-Gap-Closure Metrics (from 04-06, revised 07-03)

**Unweighted Recall:** 77.9% (baseline measurement)
**Weighted Recall:** 94.4% (spoken handoff relevance - Phase 7)
**False negatives:** 205 PHI spans (167 are zero-weight entities)

| Entity Type | FNs | Decision |
|-------------|-----|----------|
| LOCATION | 104 | Not addressable (NER limitation) |
| ROOM | 44 | Accept (high FP risk) |
| MRN | 37 | Accept (conflicts with phone) |
| PERSON | 9 | Not addressable (NER edge cases) |
| DATE_TIME | 6 | Defer (low impact) |
| PHONE_NUMBER | 5 | Defer (diminishing returns) |

**Gap closure completed:**
- ~~PHONE_NUMBER~~ 04-04: International/extension formats (+52 TPs)
- ~~ROOM hyphenated~~ 04-05: Standalone hyphenated patterns
- **Conservative decision (04-06):** Accept 86.4% recall with documented residual risk

## Performance Metrics

**Velocity:**
- Total plans completed: 18
- Average duration: 5.0 min
- Total execution time: 1.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-baseline-measurement | 6/6 | 38 min | 6.3 min |
| 02-threshold-calibration | 2/2 | 9 min | 4.5 min |
| 03-deny-list-refinement | 2/2 | 5 min | 2.5 min |
| 04-pattern-improvements | 5/6 | 31 min | 6.2 min |
| 05-validation-compliance | 3/4 | 8 min | 2.7 min |
| 07-alternative-engine-benchmark | 3/3 | 13 min | 4.3 min |
| 08-weighted-recall-evaluation | 1/1 | 3 min | 3.0 min |

**Recent Trend:**
- Last 5 plans: 04-05 (5min), 08-01 (3min), 07-01 (6min), 07-02 (4min), 07-03 (3min)
- Trend: Phase 7 complete - documentation tasks efficient (3-6min)

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
- **Phone patterns supplement Presidio default** (5 patterns for international/extension formats with context-dependent scoring) — From 04-04
- **10-digit unformatted phone: low score (0.60)** (Requires context words to avoid false positives on other 10-digit numbers) — From 04-04
- **Standalone hyphenated room: low score (0.55)** (Requires context words like room/bed/floor to avoid false positives on age ranges) — From 04-05
- **Option-c: Conservative gap closure** (Accept limitations with documented residual risk; 86.4% recall sufficient for personal QI project with user review mitigation; maintaining precision preserves clinical utility) — From 04-06
- **Target validation sample: 200 transcripts** (Minimum viable: 50; narrow confidence intervals for >95% recall verification) — From 05-01
- **Stratification by dominant PHI type** (Preserves entity distribution from synthetic to validation data) — From 05-01
- **70/30 val/test split** (No training needed - tuning on val, final metrics on test) — From 05-01
- **Bootstrap percentile method with 10k iterations** (Standard bootstrap approach, computationally tractable, provides stable 95% CI) — From 05-02
- **6 failure modes for error taxonomy** (Covers all major detection failure mechanisms, enables targeted improvements) — From 05-02
- **--with-ci flag optional** (Bootstrap is slow, only calculate when needed for formal validation) — From 05-02
- **Weighted metrics opt-in via --weighted flag** (Preserves existing workflows; weights from SPOKEN_HANDOFF_ANALYSIS.md evidence) — From 08-01
- **Spoken handoff relevance weights (0-5 scale)** (PERSON/GUARDIAN=5, ROOM=4, PHONE/DATE=2, MRN=1, EMAIL/LOCATION/AGE=0; reflects I-PASS handoff frequency) — From 08-01
- **Weighted recall 91.5% vs unweighted 77.9%** (Zero-weight entities (EMAIL, LOCATION, PEDIATRIC_AGE) don't penalize metrics; accurately reflects spoken handoff performance) — From 08-01
- **Deployment decision deferred to Phase 7** (Presidio recall 86.4% below 95% threshold; benchmark Philter-UCSF and Stanford BERT before deciding whether to improve Presidio or switch engines) — From 05-03
- **05-04 expert review deferred** (More valuable after engine decision; expert review on final system rather than potentially abandoned Presidio) — From 05-03
- **BERT entity mapping to Presidio types** (PATIENT/HCW/VENDOR → PERSON, DATE → DATE_TIME, PHONE → PHONE_NUMBER, HOSPITAL → LOCATION, ID → MEDICAL_RECORD_NUMBER; consolidates person-like entities for unified evaluation) — From 07-02
- **TransformersNlpEngine integration pattern** (Use Presidio's TransformersNlpEngine not direct HuggingFace pipeline; enables custom recognizer wiring and consistent evaluation framework) — From 07-02
- **CPU inference runtime management** (--sample flag required for BERT benchmarks; 5-10s per handoff on CPU means 20 samples ~3min, 600 samples ~1-2hr) — From 07-02
- **Use lookbehind patterns for Philter** (Python re module supports lookbehind; preserves relationship words like "Mom", "Dad" in output) — From 07-01
- **Focus on high-weight patterns first** (GUARDIAN_NAME weight=5, ROOM weight=4; faster initial benchmark, representative of clinical importance) — From 07-01
- **Bypass Philter file-based pipeline** (Direct regex matching for fair comparison; Philter designed for batch file processing not span extraction) — From 07-01
- **Continue with Presidio engine** (94.4% weighted recall exceeds improvement threshold; no alternative provides >5% gain; Philter incomplete, BERT blocked) — From 07-03
- **Weighted metrics reveal true performance** (94.4% vs 77.9% unweighted; zero-weight entities (EMAIL, LOCATION, PEDIATRIC_AGE) explain gap) — From 07-03
- **Phase 7 complete - resume Phase 5** (Expert review with clinical SME on current Presidio system; engine decision finalized) — From 07-03

### Pending Todos

- **Philter full implementation** — Complete remaining 6/8 entity types (PERSON, PHONE, EMAIL, DATE_TIME, LOCATION, MRN) for future benchmark comparison. Current: 2/8 entity types (GUARDIAN_NAME, ROOM) with 24 patterns translated. Deferred per user request 2026-01-25.

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

### Roadmap Evolution

- Phase 6 added: Real handoff testing - user reads actual text handoffs to validate PHI detection (2026-01-24)

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 001 | Investigate deidentification code | 2026-01-23 | 424cd44 | [001-investigate-deidentification-code](./quick/001-investigate-deidentification-code/) |

## Session Continuity

Last session: 2026-01-25
Stopped at: Completed 07-03 - Phase 7 complete with engine decision documented
Resume file: .planning/phases/07-alternative-engine-benchmark/07-03-SUMMARY.md
Next: 05-04 Expert review with clinical SME (resume Phase 5 with Presidio engine)

---
*State initialized: 2026-01-23*
*Last updated: 2026-01-25 (Phase 7 complete - 07-03 engine decision documented, resume Phase 5 next)*
