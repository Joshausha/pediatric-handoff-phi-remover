# Roadmap: Pediatric Handoff PHI Remover

## Milestones

- [x] **v1.0 PHI Detection Overhaul** - Phases 1-8 (shipped 2026-01-25)
- [ ] **v2.0 CI/CD Pipeline Fix** - Phase 9 (in progress)

## Phases

<details>
<summary>v1.0 PHI Detection Overhaul (Phases 1-8) - SHIPPED 2026-01-25</summary>

**Delivered:** Production-ready PHI detection with 94.4% weighted recall, validated on 27 real clinical handoffs with zero false negatives.

**Key accomplishments:**
- Established evaluation framework with F2 score as primary metric
- Calibrated per-entity thresholds to 0.30 via PR curve analysis
- Implemented case-insensitive deny lists with 45+ medical abbreviations
- Created 41 bidirectional patterns for guardian/baby name detection
- Validated on 27 real clinical handoffs with 0 false negatives
- Achieved APPROVED FOR PRODUCTION status

**Stats:** 8 phases, 24 plans, 2,085 LOC Python (app)

</details>

### v2.0 CI/CD Pipeline Fix (In Progress)

**Milestone Goal:** Get GitHub Actions workflows passing so regressions are caught automatically.

#### Phase 9: CI/CD Fixes

**Goal**: Fix dependency and test expectation issues so CI pipeline passes
**Depends on**: v1.0 complete
**Requirements**: DEP-01, TEST-01, TEST-02, CI-01, CI-02
**Success Criteria** (what must be TRUE):
  1. `pip install -r requirements.txt` succeeds without errors
  2. `pytest tests/` passes all tests (0 failures)
  3. GitHub Actions test workflow shows green checkmark
  4. GitHub Actions Docker build workflow shows green checkmark
**Plans**: TBD

Plans:
- [ ] 09-01: Fix dependencies and test expectations
- [ ] 09-02: Verify CI pipelines pass

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-8 | v1.0 | 24/24 | Complete | 2026-01-25 |
| 9 | v2.0 | 0/2 | Not started | - |
