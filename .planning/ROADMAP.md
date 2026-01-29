# Roadmap: Pediatric Handoff PHI Remover

## Milestones

- ✅ **v1.0 PHI Detection Overhaul** - Phases 1-8 (shipped 2026-01-25)
- ✅ **v2.0 CI/CD Pipeline Fix** - Phase 9 (shipped 2026-01-26)
- ✅ **v2.1 Over-Detection Quality Pass** - Phases 10-12 (shipped 2026-01-28)

## Phases

<details>
<summary>✅ v1.0 PHI Detection Overhaul (Phases 1-8) - SHIPPED 2026-01-25</summary>

### Phase 1: Test Harness
**Goal**: Isolated Presidio testing environment
**Plans**: 1 plan
- [x] 01-01: Create test_presidio.py with 21 test cases

### Phase 2: Deny List Foundation
**Goal**: Core medical abbreviations protected from false positives
**Plans**: 1 plan
- [x] 02-01: Add LOCATION and PERSON deny lists to config

### Phase 3: Guardian Detection
**Goal**: "Mom [NAME]", "Dad [NAME]" patterns working
**Plans**: 1 plan
- [x] 03-01: Implement lookbehind patterns for guardian names

### Phase 4: Baby Detection
**Goal**: "Baby [NAME]", "Infant [NAME]" patterns working
**Plans**: 1 plan
- [x] 04-01: Extend recognizer for baby name patterns

### Phase 5: Medical Identifiers
**Goal**: MRN and room numbers detected with unit preservation
**Plans**: 2 plans
- [x] 05-01: Add MRN recognizer with hash pattern
- [x] 05-02: Add ROOM recognizer with unit preservation

### Phase 6: Deny List Filtering
**Goal**: Case-insensitive filtering integrated into all recognizers
**Plans**: 1 plan
- [x] 06-01: Implement deny list filtering logic

### Phase 7: Calibration
**Goal**: Optimal thresholds and bidirectional matching configured
**Plans**: 2 plans
- [x] 07-01: Set per-entity thresholds to 0.30
- [x] 07-02: Configure bidirectional pattern matching

### Phase 8: Validation
**Goal**: Real handoff validation showing 94.4% weighted recall
**Plans**: 3 plans
- [x] 08-01: Process 27 real handoff recordings
- [x] 08-02: Calculate F2 and weighted recall metrics
- [x] 08-03: Document results and decisions

</details>

<details>
<summary>✅ v2.0 CI/CD Pipeline Fix (Phase 9) - SHIPPED 2026-01-26</summary>

### Phase 9: CI/CD Pipeline Fix
**Goal**: Green CI with numpy<2.0 constraint and aligned test expectations
**Plans**: 2 plans
- [x] 09-01: Fix dependency conflicts (numpy, philter-ucsf)
- [x] 09-02: Align test expectations with v1.0 behavior

</details>

<details>
<summary>✅ v2.1 Over-Detection Quality Pass (Phases 10-12) - SHIPPED 2026-01-28</summary>

### Phase 10: Test Script Generation and Recording
**Goal**: Realistic and edge-case handoff test data created and processed
**Depends on**: Phase 9 (CI/CD working)
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05
**Success Criteria** (what must be TRUE):
  1. User has at least 6 realistic I-PASS handoff scripts covering respiratory support and medication dosing
  2. User has at least 4 edge-case scripts targeting duration phrases and flow terminology
  3. User has recorded audio versions of all test scripts
  4. User has processed recordings through PHI detection pipeline
  5. User has documented all false positives discovered during processing
**Plans**: 2 plans

Plans:
- [x] 10-01-PLAN.md — Prepare test scripts and documentation infrastructure
- [x] 10-02-PLAN.md — Record, process, and document false positives

### Phase 11: Deny List Expansion and Unit Preservation
**Goal**: False positives eliminated via targeted deny list additions and config fixes
**Depends on**: Phase 10 (test data processed)
**Requirements**: DENY-01, DENY-02, DENY-03, DENY-04
**Success Criteria** (what must be TRUE):
  1. Duration patterns ("one day", "two days", "three days", etc.) no longer flagged as DATE_TIME
  2. Medical flow terms ("high flow", "on high", "placed on high") no longer flagged as LOCATION
  3. LOCATION deny list uses substring matching with word boundaries (like DATE_TIME)
  4. Unit names (PICU, NICU) preserved during ROOM redaction
**Plans**: 4 plans

Plans:
- [x] 11-01-PLAN.md — Duration patterns and matching behavior fix
- [x] 11-02-PLAN.md — Flow terms and PERSON deny list expansion
- [x] 11-03-PLAN.md — Unit name preservation in ROOM redaction
- [x] 11-04-PLAN.md — False positive verification and regression tests

### Phase 12: Regression Validation and CI Verification
**Goal**: No regressions on real handoffs and green CI with expanded deny lists
**Depends on**: Phase 11 (deny lists expanded)
**Requirements**: VAL-01, VAL-02, VAL-03
**Success Criteria** (what must be TRUE):
  1. All 27 real handoff recordings still pass validation (no new false negatives)
  2. All false positives from test script processing are documented in research/ or tests/
  3. CI passes with expanded deny lists (all workflows green)
**Plans**: 1 plan

Plans:
- [x] 12-01-PLAN.md — Final validation, CI verification, and v2.1 milestone completion

</details>

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → ... → 12

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Test Harness | v1.0 | 1/1 | Complete | 2026-01-25 |
| 2. Deny List Foundation | v1.0 | 1/1 | Complete | 2026-01-25 |
| 3. Guardian Detection | v1.0 | 1/1 | Complete | 2026-01-25 |
| 4. Baby Detection | v1.0 | 1/1 | Complete | 2026-01-25 |
| 5. Medical Identifiers | v1.0 | 2/2 | Complete | 2026-01-25 |
| 6. Deny List Filtering | v1.0 | 1/1 | Complete | 2026-01-25 |
| 7. Calibration | v1.0 | 2/2 | Complete | 2026-01-25 |
| 8. Validation | v1.0 | 3/3 | Complete | 2026-01-25 |
| 9. CI/CD Pipeline Fix | v2.0 | 2/2 | Complete | 2026-01-26 |
| 10. Test Script Generation | v2.1 | 2/2 | Complete | 2026-01-28 |
| 11. Deny List Expansion | v2.1 | 4/4 | Complete | 2026-01-28 |
| 12. Regression Validation | v2.1 | 1/1 | Complete | 2026-01-28 |

---
*Roadmap created: 2026-01-28*
*Last updated: 2026-01-28 (v2.1 shipped)*
