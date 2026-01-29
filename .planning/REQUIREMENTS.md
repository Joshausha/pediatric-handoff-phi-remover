# Requirements: Pediatric Handoff PHI Remover v2.2

**Defined:** 2026-01-29
**Core Value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content

## v2.2 Requirements

Requirements for Dual-Weight Recall Framework milestone. Each maps to roadmap phases.

### Test Suite

- [ ] **TEST-01**: Existing weighted metric tests pass with float weights
- [ ] **TEST-02**: Risk-weighted recall calculation has test coverage
- [ ] **TEST-03**: Risk-weighted precision calculation has test coverage
- [ ] **TEST-04**: Risk-weighted F2 calculation has test coverage
- [ ] **TEST-05**: Float assertions use tolerance (not exact comparison)
- [ ] **TEST-06**: Test validates frequency vs risk weight divergence behavior

### Report Generation

- [ ] **REPT-01**: Evaluation report displays unweighted metrics
- [ ] **REPT-02**: Evaluation report displays frequency-weighted metrics
- [ ] **REPT-03**: Evaluation report displays risk-weighted metrics
- [ ] **REPT-04**: Unweighted recall labeled as "Safety floor"
- [ ] **REPT-05**: Report includes side-by-side weight comparison table (entity, frequency, risk)
- [ ] **REPT-06**: Report explains metric divergence (what each metric captures)

### Configuration

- [ ] **CONF-01**: Risk weights defined in pydantic settings (spoken_handoff_risk_weights)
- [ ] **CONF-02**: Frequency weights use float type (not int)
- [ ] **CONF-03**: Both weight dicts cover all PHI entity types

### Documentation

- [ ] **DOCS-01**: SPOKEN_HANDOFF_ANALYSIS.md updated with dual-weighting rationale
- [ ] **DOCS-02**: SPOKEN_HANDOFF_ANALYSIS.md documents frequency weight purpose
- [ ] **DOCS-03**: SPOKEN_HANDOFF_ANALYSIS.md documents risk weight purpose
- [ ] **DOCS-04**: PROJECT.md updated with v2.2 milestone completion
- [ ] **DOCS-05**: Key Decisions table updated with dual-weighting decision

## Future Requirements (v2.3+)

Deferred to later releases. Tracked but not in current roadmap.

### Advanced Metrics

- **ADV-01**: Bootstrap confidence intervals for weighted metrics
- **ADV-02**: Risk-adjusted threshold tuning (optimize weighted recall)
- **ADV-03**: Weight scheme versioning for historical comparison

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Combined weighting (frequency * risk) | Loses interpretability; keep dimensions separate |
| Macro averaging across entities | Biases toward rare types; use unweighted as baseline |
| Learned weights from data | Need transparency; fixed weights from domain expertise |
| Cost-sensitive training | Out of scope for evaluation changes |
| Weight normalization | 0-5 scale sufficient; normalization adds complexity |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TEST-01 | TBD | Pending |
| TEST-02 | TBD | Pending |
| TEST-03 | TBD | Pending |
| TEST-04 | TBD | Pending |
| TEST-05 | TBD | Pending |
| TEST-06 | TBD | Pending |
| REPT-01 | TBD | Pending |
| REPT-02 | TBD | Pending |
| REPT-03 | TBD | Pending |
| REPT-04 | TBD | Pending |
| REPT-05 | TBD | Pending |
| REPT-06 | TBD | Pending |
| CONF-01 | TBD | Pending |
| CONF-02 | TBD | Pending |
| CONF-03 | TBD | Pending |
| DOCS-01 | TBD | Pending |
| DOCS-02 | TBD | Pending |
| DOCS-03 | TBD | Pending |
| DOCS-04 | TBD | Pending |
| DOCS-05 | TBD | Pending |

**Coverage:**
- v2.2 requirements: 20 total
- Mapped to phases: 0
- Unmapped: 20 ⚠️

---
*Requirements defined: 2026-01-29*
*Last updated: 2026-01-29 after initial definition*
