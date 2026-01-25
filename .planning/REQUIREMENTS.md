# Requirements: PHI Detection Overhaul

**Defined:** 2026-01-23
**Core Value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content.

## v1 Requirements

Requirements for this quality improvement milestone. Each maps to roadmap phases.

### Measurement (MEAS)

- [x] **MEAS-01**: System reports precision/recall/F1 metrics for each entity type (EMAIL, PERSON, DATE_TIME, PHONE, MRN, PEDIATRIC_AGE, ROOM, GUARDIAN_NAME) ✓
- [~] **MEAS-02**: Gold standard test dataset created with annotated PHI (minimum 50 transcripts) — Deferred to Phase 5 (IRB coordination); synthetic datasets used for Phase 1
- [x] **MEAS-03**: F2 score (recall-weighted) calculated and used as primary optimization target ✓
- [x] **MEAS-04**: Baseline metrics documented before any changes (current: 77.9% recall, 87.4% precision) ✓

### Threshold Calibration (THRS)

- [x] **THRS-01**: Detection threshold calibrated using precision-recall curve analysis (currently 0.35) ✓ — Calibrated to 0.30 per-entity
- [x] **THRS-02**: Validation threshold aligned with detection threshold (fix current 0.35/0.7 mismatch) ✓ — Both now use phi_score_thresholds
- [x] **THRS-03**: Threshold selection rationale documented with supporting metrics ✓ — CALIBRATION_RESULTS.md
- [~] **THRS-04**: Overall recall improved to >90% through threshold optimization — Partially met: 3/8 entities meet floor; 5/8 require Phase 4 pattern work

### Deny List Refinement (DENY)

- [x] **DENY-01**: All deny lists use case-insensitive matching (fix LOCATION exact match) ✓
- [x] **DENY-02**: Medical abbreviation deny list expanded (NC, RA, OR, ER, IV, PO, IM, SQ, etc.) ✓
- [x] **DENY-03**: Deny lists added for GUARDIAN_NAME and PEDIATRIC_AGE entity types ✓
- [~] **DENY-04**: False positive rate reduced by >20% (precision 87.4% → >90%) — Partial: 4.1% reduction via deny lists; additional improvement requires pattern refinement

### Pattern Improvements (PATT)

- [x] **PATT-01**: Lookbehind edge cases fixed (start-of-line, punctuation, word boundaries) ✓
- [x] **PATT-02**: Case normalization implemented ("mom jessica" caught, not just "Mom Jessica") ✓
- [x] **PATT-03**: Bidirectional patterns added ("Jessica is Mom" caught, not just "Mom Jessica") ✓
- [x] **PATT-04**: Speech-to-text artifacts handled (stutters, corrections, hesitations) ✓
- [~] **PATT-05**: PEDIATRIC_AGE recall improved from 36.6% to >90% — USER DECISION: Recognizer disabled (ages are NOT PHI under HIPAA unless 90+)
- [~] **PATT-06**: ROOM recall improved from 34.4% to >90% — Partial: 32.1% → 43.3% (+35% relative); 90% acknowledged as Presidio pattern limitation

### Validation & Compliance (VALD)

- [ ] **VALD-01**: External validation performed on data beyond synthetic corpus
- [ ] **VALD-02**: Error analysis identifies patterns in missed PHI (false negatives)
- [ ] **VALD-03**: Expert review of random sample validates detection quality
- [ ] **VALD-04**: Overall recall achieves >95% target for clinical deployment readiness

### Alternative Engine Benchmark (BENCH)

- [x] **BENCH-01**: Philter-UCSF installed and configured with pediatric patterns translated ✓ (partial: 2/8 entity types)
- [~] **BENCH-02**: Stanford BERT integrated as Presidio NER backend — Partial: TransformersNlpEngine blocked by environment issue
- [x] **BENCH-03**: Engine decision documented with comparative metrics ✓ — Decision: Continue with Presidio (94.4% weighted recall)

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Advanced Measurement

- **MEAS-05**: CI/CD integration runs evaluation on every commit
- **MEAS-06**: Per-entity-type thresholds optimized independently

### Advanced Compliance

- **VALD-05**: Residual risk calculated with 95% confidence interval
- **VALD-06**: HIPAA Safe Harbor compliance formally documented

### Advanced NER (conditional)

- **NER-01**: Evaluate transformer-based models vs spaCy en_core_web_lg
- **NER-02**: Benchmark domain-specific medical NER models
- **NER-03**: Implement model replacement if recall plateaus below 95%

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Performance optimization (model loading, Presidio scans) | Separate concern, not PHI accuracy |
| Additional security hardening (XSS, CSP, path traversal) | Separate milestone |
| Test coverage for non-PHI paths (concurrency, large files) | Separate milestone |
| New features (speaker diarization, batch processing, GPU) | Future enhancement |
| Unicode/international name support | Low priority for pediatric handoffs |
| Real-time streaming de-identification | Not needed for handoff use case |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MEAS-01 | Phase 1 | Complete |
| MEAS-02 | Phase 1 | Deferred (Phase 5) |
| MEAS-03 | Phase 1 | Complete |
| MEAS-04 | Phase 1 | Complete |
| THRS-01 | Phase 2 | Complete |
| THRS-02 | Phase 2 | Complete |
| THRS-03 | Phase 2 | Complete |
| THRS-04 | Phase 2 | Partial (3/8 entities) |
| DENY-01 | Phase 3 | Complete |
| DENY-02 | Phase 3 | Complete |
| DENY-03 | Phase 3 | Complete |
| DENY-04 | Phase 3 | Partial |
| PATT-01 | Phase 4 | Complete |
| PATT-02 | Phase 4 | Complete |
| PATT-03 | Phase 4 | Complete |
| PATT-04 | Phase 4 | Complete |
| PATT-05 | Phase 4 | User Decision |
| PATT-06 | Phase 4 | Partial |
| VALD-01 | Phase 5 | Pending |
| VALD-02 | Phase 5 | Pending |
| VALD-03 | Phase 5 | Pending |
| VALD-04 | Phase 5 | Pending |
| BENCH-01 | Phase 7 | Complete (partial) |
| BENCH-02 | Phase 7 | Partial (blocked) |
| BENCH-03 | Phase 7 | Complete |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-01-23*
*Last updated: 2026-01-25 after Phase 7 completion*
