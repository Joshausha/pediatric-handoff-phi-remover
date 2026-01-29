# Roadmap: Pediatric Handoff PHI Remover

## Milestones

- ✅ **v1.0 PHI Detection Overhaul** - Phases 1-8 (shipped 2026-01-25)
- ✅ **v2.0 CI/CD Pipeline Fix** - Phase 9 (shipped 2026-01-26)
- ✅ **v2.1 Over-Detection Quality Pass** - Phases 10-12 (shipped 2026-01-28)
- 🚧 **v2.2 Dual-Weight Recall Framework** - Phases 13-16 (in progress)

## Phases

<details>
<summary>✅ v1.0 PHI Detection Overhaul (Phases 1-8) - SHIPPED 2026-01-25</summary>

### Phase 1: Evaluation Framework Foundation
**Goal**: Establish F2-based evaluation pipeline with per-entity metrics
**Plans**: 3 plans

Plans:
- [x] 01-01: Create baseline test harness
- [x] 01-02: Implement per-entity scoring
- [x] 01-03: Generate initial PR curves

### Phase 2: Threshold Calibration
**Goal**: Set optimal confidence thresholds for each PHI entity type
**Plans**: 3 plans

Plans:
- [x] 02-01: Analyze threshold sensitivity
- [x] 02-02: Implement per-entity thresholds
- [x] 02-03: Validate on synthetic dataset

### Phase 3: Deny List Architecture
**Goal**: Case-insensitive medical abbreviation filtering system
**Plans**: 3 plans

Plans:
- [x] 03-01: Build deny list infrastructure
- [x] 03-02: Populate medical abbreviations
- [x] 03-03: Integrate with recognizers

### Phase 4: Guardian/Baby Name Detection
**Goal**: Bidirectional pattern matching for pediatric entities
**Plans**: 3 plans

Plans:
- [x] 04-01: Create pattern library
- [x] 04-02: Implement lookbehind logic
- [x] 04-03: Test preservation of context words

### Phase 5: Medical Record Number Patterns
**Goal**: Detect all MRN formats including hash notation
**Plans**: 1 plan

Plans:
- [x] 05-01: Implement MRN recognizer with #12345678 support

### Phase 6: Room/Bed Number Detection
**Goal**: Redact room numbers while preserving unit names
**Plans**: 2 plans

Plans:
- [x] 06-01: Create ROOM recognizer
- [x] 06-02: Add unit preservation logic

### Phase 7: Weighted Recall Metrics
**Goal**: Frequency-weighted evaluation for spoken handoff context
**Plans**: 2 plans

Plans:
- [x] 07-01: Implement weighted recall/precision/F2
- [x] 07-02: Add bootstrap confidence intervals

### Phase 8: Real Handoff Validation
**Goal**: Validate on 27 real clinical handoffs with zero false negatives
**Plans**: 2 plans

Plans:
- [x] 08-01: Record and transcribe validation set
- [x] 08-02: Achieve 94.4% weighted recall

</details>

<details>
<summary>✅ v2.0 CI/CD Pipeline Fix (Phase 9) - SHIPPED 2026-01-26</summary>

### Phase 9: CI/CD Pipeline Stabilization
**Goal**: Green GitHub Actions pipeline with automated regression testing
**Plans**: 2 plans

Plans:
- [x] 09-01: Resolve dependency conflicts
- [x] 09-02: Align test expectations with v1.0 behavior

</details>

<details>
<summary>✅ v2.1 Over-Detection Quality Pass (Phases 10-12) - SHIPPED 2026-01-28</summary>

### Phase 10: Test Script Generation
**Goal**: Create realistic I-PASS handoff scripts targeting false positives
**Plans**: 2 plans

Plans:
- [x] 10-01: Generate 6 realistic handoff scripts
- [x] 10-02: Generate 4 edge-case scripts

### Phase 11: Systematic False Positive Analysis
**Goal**: Document and eliminate all false positive patterns
**Plans**: 3 plans

Plans:
- [x] 11-01: Record and analyze false positives
- [x] 11-02: Expand DATE_TIME deny list (70+ patterns)
- [x] 11-03: Fix LOCATION word-boundary matching

### Phase 12: Regression Test Suite
**Goal**: Prevent reintroduction of fixed false positives
**Plans**: 2 plans

Plans:
- [x] 12-01: Create 36 regression tests
- [x] 12-02: Validate no recall degradation

</details>

### 🚧 v2.2 Dual-Weight Recall Framework (In Progress)

**Milestone Goal:** Implement three-metric recall evaluation separating frequency (spoken prevalence) from risk (leak severity) for spoken handoffs.

#### Phase 13: Test Suite Migration
**Goal**: Complete test coverage for float weights and risk-weighted metrics
**Depends on**: Nothing (research complete, partial implementation in working tree)
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06
**Success Criteria** (what must be TRUE):
  1. All existing weighted metric tests pass with float weights (not int)
  2. Risk-weighted recall/precision/F2 calculations have test coverage
  3. Float assertions use tolerance-based comparison (not exact equality)
  4. Tests validate frequency vs risk weight divergence behavior
  5. Test suite runs in under 5 seconds (unit tests only, no audio)
**Plans**: 1 plan

Plans:
- [x] 13-01-PLAN.md — Fix float assertions, add risk-weighted tests, add divergence validation

#### Phase 14: Report Generation Refinement
**Goal**: Polish three-metric report display with clear explanations
**Depends on**: Phase 13 (validated calculations)
**Requirements**: REPT-01, REPT-02, REPT-03, REPT-04, REPT-05, REPT-06
**Success Criteria** (what must be TRUE):
  1. Evaluation report displays all three metrics (unweighted, frequency-weighted, risk-weighted)
  2. Unweighted recall labeled as "Safety floor" (HIPAA compliance baseline)
  3. Side-by-side weight comparison table renders correctly (entity, frequency, risk)
  4. Report explains what each metric captures (spoken prevalence vs leak severity)
  5. Metric divergence is clearly documented (when/why they differ)
**Plans**: 1 plan

Plans:
- [ ] 14-01-PLAN.md — Three-metric summary table, side-by-side weights, divergence explanation

#### Phase 15: Documentation Updates
**Goal**: Document dual-weighting rationale and usage guidance
**Depends on**: Phase 14 (finalized report format)
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04, DOCS-05
**Success Criteria** (what must be TRUE):
  1. SPOKEN_HANDOFF_ANALYSIS.md documents dual-weighting rationale
  2. Frequency weight purpose clearly explained (spoken prevalence)
  3. Risk weight purpose clearly explained (leak severity)
  4. PROJECT.md updated with v2.2 completion status
  5. Key Decisions table includes dual-weighting decision with rationale
**Plans**: TBD

Plans:
- [ ] 15-01: TBD during phase planning

#### Phase 16: Integration Validation
**Goal**: End-to-end validation with regression baselines established
**Depends on**: Phase 13, Phase 14, Phase 15
**Requirements**: CONF-01, CONF-02, CONF-03 (validation that config complete)
**Success Criteria** (what must be TRUE):
  1. Full evaluation runs successfully on synthetic dataset
  2. All three metrics displayed in report (unweighted, frequency, risk)
  3. Risk weights properly loaded from pydantic settings
  4. Expected metric divergence observed (frequency > risk recall pattern)
  5. No regressions on v2.1 validation set (86.4% recall maintained)
**Plans**: TBD

Plans:
- [ ] 16-01: TBD during phase planning

## Progress

**Execution Order:**
Phases execute in numeric order: 13 → 14 → 15 → 16

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Evaluation Framework | v1.0 | 3/3 | Complete | 2026-01-25 |
| 2. Threshold Calibration | v1.0 | 3/3 | Complete | 2026-01-25 |
| 3. Deny List Architecture | v1.0 | 3/3 | Complete | 2026-01-25 |
| 4. Guardian/Baby Names | v1.0 | 3/3 | Complete | 2026-01-25 |
| 5. MRN Patterns | v1.0 | 1/1 | Complete | 2026-01-25 |
| 6. Room/Bed Numbers | v1.0 | 2/2 | Complete | 2026-01-25 |
| 7. Weighted Metrics | v1.0 | 2/2 | Complete | 2026-01-25 |
| 8. Real Handoff Validation | v1.0 | 2/2 | Complete | 2026-01-25 |
| 9. CI/CD Pipeline | v2.0 | 2/2 | Complete | 2026-01-26 |
| 10. Test Scripts | v2.1 | 2/2 | Complete | 2026-01-28 |
| 11. False Positive Analysis | v2.1 | 3/3 | Complete | 2026-01-28 |
| 12. Regression Tests | v2.1 | 2/2 | Complete | 2026-01-28 |
| 13. Test Suite Migration | v2.2 | 1/1 | Complete | 2026-01-29 |
| 14. Report Refinement | v2.2 | 0/1 | Planning complete | - |
| 15. Documentation | v2.2 | 0/TBD | Not started | - |
| 16. Integration Validation | v2.2 | 0/TBD | Not started | - |

---
*Roadmap created: 2026-01-29*
*Last updated: 2026-01-29 after Phase 14 planning complete*
