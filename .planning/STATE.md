# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-30)

**Core value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content
**Current focus:** Planning next milestone

## Current Position

Phase: 17 of 22 (Room Pattern Expansion) - NOT STARTED
Plan: 0 of ? (needs planning)
Status: v2.2 shipped, v2.3 milestone defined, ready to plan phases
Last activity: 2026-01-30 — v2.2 milestone completed and archived

Progress: [##########] 100% v1.0 | [##########] 100% v2.0 | [##########] 100% v2.1 | [##########] 100% v2.2 | [          ] 0% v2.3

## Milestones Shipped

| Version | Name | Phases | Plans | Shipped |
|---------|------|--------|-------|---------|
| v1.0 | PHI Detection Overhaul | 1-8 | 11 | 2026-01-25 |
| v2.0 | CI/CD Pipeline Fix | 9 | 2 | 2026-01-26 |
| v2.1 | Over-Detection Quality Pass | 10-12 | 7 | 2026-01-28 |
| v2.2 | Dual-Weight Recall Framework | 13-16 | 4 | 2026-01-30 |

## v2.3 Roadmap Overview

**6 phases (17-22) targeting recall improvements:**

- Phase 17: Room Pattern Expansion (32% → ≥80%) - NOT STARTED
- Phase 18: Guardian Edge Cases (possessive/appositive patterns) - NOT STARTED
- Phase 19: Provider Name Detection (attending/nurse names) - NOT STARTED
- Phase 20: Phone/Pager Patterns (76% → ≥90%) - NOT STARTED
- Phase 21: Location/Transfer Patterns (20% → ≥60%) - NOT STARTED
- Phase 22: Validation & Recall Targets (end-to-end validation) - NOT STARTED

**Phases 17-21 can execute in parallel** (no dependencies). Phase 22 validates all improvements.

**Brainstorm source:** Sequential thinking session analyzing recall gaps and proposing pattern improvements.

## CI/CD Status

**GitHub Actions:** ALL GREEN (with new integration tests)

| Workflow | Status | Details |
|----------|--------|---------|
| test.yml | PASSING | 208 passed + 6 integration tests, 8 xfailed, 1 xpassed |
| docker.yml | PASSING | Build completes in ~24s |

**Integration test coverage:**
- Smoke tests (test_regression.py) run on all PRs
- Full validation (test_full_evaluation.py) runs on main branch
- Unweighted recall >=85% enforced as CI failure condition

## Known Issues (Tech Debt)

Tracked via xfail markers in CI:

**Under-detection:**
- 7-digit phone numbers (555-0123)
- Detailed ages (3 weeks 2 days)
- Street addresses (425 Oak Street)
- School names (Jefferson Elementary)

**Over-detection:**
- None remaining (all fixed in v2.1)

## Accumulated Context

### Decisions

See `.planning/PROJECT.md` Key Decisions table for full history.

Recent decisions affecting v2.2:
- **Dual-weight framework**: Separate frequency (spoken) from risk (severity) metrics for complementary evaluation lenses
- **Float weights**: Migrated from int to float for finer granularity (0.5 weights for low-risk entities)
- **Three-metric reporting**: Always show unweighted as HIPAA safety floor alongside both weighted schemes
- **TEST-FLOAT-COMPARISON**: Use pytest.approx() for all float weight comparisons
- **TEST-DIVERGENCE-VALIDATION**: Add explicit tests for frequency vs risk weight divergence
- **Unified summary table**: Single table displays all three metric types (Recall, Precision, F2) for easier comparison
- **Side-by-side weight tables**: Frequency-sorted and risk-sorted columns shown simultaneously
- **Divergence threshold 2.0**: Mark entities with asterisk when abs(freq_weight - risk_weight) > 2.0
- **Dual-weighting documentation**: SPOKEN_HANDOFF_ANALYSIS.md explains WHY two weight schemes exist (frequency vs risk) and WHEN to use each metric
- **JSON baselines over pytest-regressions**: Simple JSON files for regression detection (fewer dependencies, easier to understand)
- **Module-scoped fixtures**: Run validation once per test file for efficiency
- **1% tolerance for metric comparisons**: Allows bootstrap sampling variation without spurious failures
- **Tiered CI workflow**: Smoke tests on all PRs, full validation only on main (balance thoroughness with speed)

### Pending Todos

- Plan Phase 17 (Room Pattern Expansion)
- Plan Phase 18 (Guardian Edge Cases)
- Plan Phase 19 (Provider Name Detection)
- Plan Phase 20 (Phone/Pager Patterns)
- Plan Phase 21 (Location/Transfer Patterns)

### Blockers/Concerns

None - ready to start v2.3 planning.

**Critical safety requirement validated:** Zero-weight entities (EMAIL_ADDRESS, PEDIATRIC_AGE) invisible in weighted metrics but protected by unweighted recall floor. Integration test `test_unweighted_recall_floor` enforces this with clear error message explaining why weighted metrics cannot replace unweighted.

### Roadmap Evolution

- 2026-01-30: v2.3 Recall Improvements milestone created (Phases 17-22)
  - Phase 17: Room Pattern Expansion
  - Phase 18: Guardian Edge Cases
  - Phase 19: Provider Name Detection
  - Phase 20: Phone/Pager Patterns
  - Phase 21: Location/Transfer Patterns
  - Phase 22: Validation & Recall Targets

## Session Continuity

Last session: 2026-01-30
Stopped at: v2.2 milestone completed and archived
Resume file: None
Next: Start v2.3 planning with /gsd:new-milestone or plan phases 17-21 directly

---
*State initialized: 2026-01-23*
*Last updated: 2026-01-30 — v2.2 Dual-Weight Recall Framework shipped and archived*
