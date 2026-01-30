# Roadmap: Pediatric Handoff PHI Remover

## Milestones

- ✅ **v1.0 PHI Detection Overhaul** - Phases 1-8 (shipped 2026-01-25)
- ✅ **v2.0 CI/CD Pipeline Fix** - Phase 9 (shipped 2026-01-26)
- ✅ **v2.1 Over-Detection Quality Pass** - Phases 10-12 (shipped 2026-01-28)
- ✅ **v2.2 Dual-Weight Recall Framework** - Phases 13-16 (shipped 2026-01-30) → [archived](milestones/v2.2-ROADMAP.md)
- 🚧 **v2.3 Recall Improvements** - Phases 17-22 (in progress)

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

<details>
<summary>✅ v2.2 Dual-Weight Recall Framework (Phases 13-16) - SHIPPED 2026-01-30</summary>

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
- [x] 14-01-PLAN.md — Three-metric summary table, side-by-side weights, divergence explanation

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
**Plans**: 1 plan

Plans:
- [x] 15-01-PLAN.md — Add dual-weighting methodology section, update PROJECT.md

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
**Plans**: 2 plans

Plans:
- [x] 16-01-PLAN.md — Integration test infrastructure, regression baselines, tiered CI
- [x] 16-02-PLAN.md — Metric comparison charts, v2.2 completion verification

</details>

<details open>
<summary>🚧 v2.3 Recall Improvements (Phases 17-22) - IN PROGRESS</summary>

**Milestone Goal:** Close critical recall gaps in ROOM (32%), LOCATION (20%), PHONE (76%), and MRN (72%) entities while maintaining precision.

**Current Recall Targets:**
| Entity | v2.2 Recall | v2.3 Target |
|--------|-------------|-------------|
| ROOM | 32.1% | ≥80% |
| LOCATION | 20.0% | ≥60% |
| PHONE_NUMBER | 75.7% | ≥90% |
| MRN | 72.3% | ≥85% |

### Phase 17: Room Pattern Expansion
**Goal**: Improve ROOM recall from 32% to ≥80% with conversational patterns
**Depends on**: Nothing (can start immediately)
**Success Criteria**:
  1. "in [number]" context pattern catches informal room references
  2. "space", "pod", "cubicle", "crib" variations detected
  3. Hyphenated "3-22" format with context confirmation
  4. ROOM recall ≥80% on validation set
  5. No regression on PICU/NICU unit preservation
**Plans**: 1 plan

Plans:
- [ ] 17-01-PLAN.md — Add low-confidence contextual patterns, room synonyms, expanded context words

### Phase 18: Guardian Edge Cases
**Goal**: Catch possessive and appositive guardian name patterns
**Depends on**: Nothing (can start immediately)
**Success Criteria**:
  1. "his mom Sarah" / "her dad Tom" (possessive + relationship) detected
  2. "the mom, Jessica" (appositive with comma) detected
  3. "grandma's here, her name is Maria" detected
  4. GUARDIAN_NAME recall improved without new false positives
  5. Existing guardian patterns unaffected
**Plans**: 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 18 to break down)

### Phase 19: Provider Name Detection
**Goal**: Detect provider names in clinical handoff context
**Depends on**: Nothing (can start immediately)
**Success Criteria**:
  1. "with Dr. [Name]", "paged Dr. [Name]" patterns detected
  2. "the attending is [Name]" (no Dr. prefix) detected
  3. "his nurse is Sarah" and similar nursing staff patterns
  4. Provider deny list prevents over-detection of titles
  5. PERSON recall improvement measured
**Plans**: 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 19 to break down)

### Phase 20: Phone/Pager Patterns
**Goal**: Improve PHONE_NUMBER recall from 76% to ≥90%
**Depends on**: Nothing (can start immediately)
**Success Criteria**:
  1. "pager 12345", "page to 55555" patterns detected
  2. "ext. 1234", "extension 1234" variations covered
  3. 5-digit internal numbers with "call" context
  4. PHONE_NUMBER recall ≥90% on validation set
  5. No false positives on clinical numbers (vitals, doses)
**Plans**: 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 20 to break down)

### Phase 21: Location/Transfer Patterns
**Goal**: Improve LOCATION recall from 20% to ≥60%
**Depends on**: Nothing (can start immediately)
**Success Criteria**:
  1. "from [Hospital Name]", "transferred from [Place]" detected
  2. "lives in [City]", "from [Town]" patterns added
  3. PCP office names detected with clinic context
  4. LOCATION recall ≥60% on validation set
  5. Hospital unit names (PICU, ED) remain on deny list
**Plans**: 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 21 to break down)

### Phase 22: Validation & Recall Targets
**Goal**: End-to-end validation confirming all recall targets met
**Depends on**: Phases 17-21
**Success Criteria**:
  1. ROOM recall ≥80%
  2. LOCATION recall ≥60%
  3. PHONE_NUMBER recall ≥90%
  4. MRN recall ≥85%
  5. Overall weighted recall improvement documented
  6. No precision regression (false positives stay low)
**Plans**: 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 22 to break down)

</details>

## Progress

**Execution Order:**
Phases 17-21 can execute in parallel (no dependencies). Phase 22 validates all.

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
| 14. Report Refinement | v2.2 | 1/1 | Complete | 2026-01-29 |
| 15. Documentation | v2.2 | 1/1 | Complete | 2026-01-29 |
| 16. Integration Validation | v2.2 | 2/2 | Complete | 2026-01-30 |
| 17. Room Pattern Expansion | v2.3 | 0/1 | Planned | - |
| 18. Guardian Edge Cases | v2.3 | 0/? | Not started | - |
| 19. Provider Name Detection | v2.3 | 0/? | Not started | - |
| 20. Phone/Pager Patterns | v2.3 | 0/? | Not started | - |
| 21. Location/Transfer Patterns | v2.3 | 0/? | Not started | - |
| 22. Validation & Recall Targets | v2.3 | 0/? | Not started | - |

---
*Roadmap created: 2026-01-29*
*Last updated: 2026-01-30 — Phase 17 planned (1 plan)*
