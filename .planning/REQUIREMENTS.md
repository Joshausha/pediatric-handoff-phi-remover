# Requirements: Pediatric Handoff PHI Remover v2.1

**Defined:** 2026-01-28
**Core Value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content

## v2.1 Requirements

Requirements for over-detection quality pass. Each maps to roadmap phases.

### Test Scripts

- [x] **TEST-01**: Generate realistic I-PASS handoff scripts with respiratory support terminology
- [x] **TEST-02**: Generate realistic scripts with medication dosing and timeline language
- [x] **TEST-03**: Generate edge-case scripts targeting duration phrases ("three days of symptoms")
- [x] **TEST-04**: Generate edge-case scripts targeting flow terminology ("on high flow", "placed on high")
- [x] **TEST-05**: Record test scripts and process through PHI detection pipeline

### Deny List Expansion

- [ ] **DENY-01**: Add duration patterns to DATE_TIME deny list (one/two/three/etc. days, weeks, months)
- [ ] **DENY-02**: Add medical flow terms to LOCATION deny list with word boundary protection
- [ ] **DENY-03**: Switch LOCATION deny list from exact match to substring match with word boundaries
- [ ] **DENY-04**: Preserve unit names (PICU, NICU) during ROOM entity redaction

### Validation

- [ ] **VAL-01**: Verify no regressions on existing 27 real handoff validation set
- [ ] **VAL-02**: Document all false positives found during test script processing
- [ ] **VAL-03**: CI passes with expanded deny lists

## Future Requirements

Deferred to later milestones.

### Under-Detection Fixes (v3.0+)

- **UNDER-01**: Improve 7-digit phone number detection (555-0123)
- **UNDER-02**: Improve detailed age detection ("3 weeks 2 days old")
- **UNDER-03**: Improve street address detection ("425 Oak Street")

## Out of Scope

| Feature | Reason |
|---------|--------|
| Machine learning false positive classifier | Overkill for current deny list size (<100 terms) |
| Custom spaCy model training | Premature optimization — fix config first |
| Performance benchmarking | Not primary goal of this milestone |
| Unicode/accent normalization | English-only transcription, rare edge case |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TEST-01 | Phase 10 | Complete |
| TEST-02 | Phase 10 | Complete |
| TEST-03 | Phase 10 | Complete |
| TEST-04 | Phase 10 | Complete |
| TEST-05 | Phase 10 | Complete |
| DENY-01 | Phase 11 | Pending |
| DENY-02 | Phase 11 | Pending |
| DENY-03 | Phase 11 | Pending |
| DENY-04 | Phase 11 | Pending |
| VAL-01 | Phase 12 | Pending |
| VAL-02 | Phase 12 | Pending |
| VAL-03 | Phase 12 | Pending |

**Coverage:**
- v2.1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-01-28*
*Last updated: 2026-01-28 (Phase 10 complete - TEST-01 through TEST-05)*
