# Requirements: PHI Detection Overhaul

**Defined:** 2026-01-23
**Core Value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content.

## v1 Requirements

Requirements for this quality improvement milestone. Each maps to roadmap phases.

### Measurement (MEAS)

- [ ] **MEAS-01**: System reports precision/recall/F1 metrics for each entity type (EMAIL, PERSON, DATE_TIME, PHONE, MRN, PEDIATRIC_AGE, ROOM, GUARDIAN_NAME)
- [ ] **MEAS-02**: Gold standard test dataset created with annotated PHI (minimum 50 transcripts)
- [ ] **MEAS-03**: F2 score (recall-weighted) calculated and used as primary optimization target
- [ ] **MEAS-04**: Baseline metrics documented before any changes (current: 77.9% recall, 87.4% precision)

### Threshold Calibration (THRS)

- [ ] **THRS-01**: Detection threshold calibrated using precision-recall curve analysis (currently 0.35)
- [ ] **THRS-02**: Validation threshold aligned with detection threshold (fix current 0.35/0.7 mismatch)
- [ ] **THRS-03**: Threshold selection rationale documented with supporting metrics
- [ ] **THRS-04**: Overall recall improved to >90% through threshold optimization

### Deny List Refinement (DENY)

- [ ] **DENY-01**: All deny lists use case-insensitive matching (fix LOCATION exact match)
- [ ] **DENY-02**: Medical abbreviation deny list expanded (NC, RA, OR, ER, IV, PO, IM, SQ, etc.)
- [ ] **DENY-03**: Deny lists added for GUARDIAN_NAME and PEDIATRIC_AGE entity types
- [ ] **DENY-04**: False positive rate reduced by >20% (precision 87.4% → >90%)

### Pattern Improvements (PATT)

- [ ] **PATT-01**: Lookbehind edge cases fixed (start-of-line, punctuation, word boundaries)
- [ ] **PATT-02**: Case normalization implemented ("mom jessica" caught, not just "Mom Jessica")
- [ ] **PATT-03**: Bidirectional patterns added ("Jessica is Mom" caught, not just "Mom Jessica")
- [ ] **PATT-04**: Speech-to-text artifacts handled (stutters, corrections, hesitations)
- [ ] **PATT-05**: PEDIATRIC_AGE recall improved from 36.6% to >90%
- [ ] **PATT-06**: ROOM recall improved from 34.4% to >90%

### Validation & Compliance (VALD)

- [ ] **VALD-01**: External validation performed on data beyond synthetic corpus
- [ ] **VALD-02**: Error analysis identifies patterns in missed PHI (false negatives)
- [ ] **VALD-03**: Expert review of random sample validates detection quality
- [ ] **VALD-04**: Overall recall achieves >95% target for clinical deployment readiness

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
| MEAS-01 | Phase 1 | Pending |
| MEAS-02 | Phase 1 | Pending |
| MEAS-03 | Phase 1 | Pending |
| MEAS-04 | Phase 1 | Pending |
| THRS-01 | Phase 2 | Pending |
| THRS-02 | Phase 2 | Pending |
| THRS-03 | Phase 2 | Pending |
| THRS-04 | Phase 2 | Pending |
| DENY-01 | Phase 3 | Pending |
| DENY-02 | Phase 3 | Pending |
| DENY-03 | Phase 3 | Pending |
| DENY-04 | Phase 3 | Pending |
| PATT-01 | Phase 4 | Pending |
| PATT-02 | Phase 4 | Pending |
| PATT-03 | Phase 4 | Pending |
| PATT-04 | Phase 4 | Pending |
| PATT-05 | Phase 4 | Pending |
| PATT-06 | Phase 4 | Pending |
| VALD-01 | Phase 5 | Pending |
| VALD-02 | Phase 5 | Pending |
| VALD-03 | Phase 5 | Pending |
| VALD-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-01-23*
*Last updated: 2026-01-23 after initial definition*
