# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-29)

**Core value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content
**Current focus:** v2.2 Dual-Weight Recall Framework - Phase 16 complete, ready to ship

## Current Position

Phase: 16 of 16 (Integration Validation)
Plan: 2 of 2 COMPLETE
Status: Phase 16 complete - v2.2 SHIPPED ✓
Last activity: 2026-01-30 — Completed 16-02-PLAN.md (metric comparison charts and v2.2 finalization)

Progress: [##########] 100% v1.0 | [##########] 100% v2.0 | [##########] 100% v2.1 | [##########] 100% v2.2

## Milestones Shipped

| Version | Name | Phases | Plans | Shipped |
|---------|------|--------|-------|---------|
| v1.0 | PHI Detection Overhaul | 1-8 | 11 | 2026-01-25 |
| v2.0 | CI/CD Pipeline Fix | 9 | 2 | 2026-01-26 |
| v2.1 | Over-Detection Quality Pass | 10-12 | 7 | 2026-01-28 |
| v2.2 | Dual-Weight Recall Framework | 13-16 | 4 | 2026-01-30 |

## v2.2 Roadmap Overview

**4 phases (13-16) covering 20 requirements - ALL COMPLETE:**

- Phase 13: Test Suite Migration (TEST-01 to TEST-06) - COMPLETE
- Phase 14: Report Generation Refinement (REPT-01 to REPT-06) - COMPLETE
- Phase 15: Documentation Updates (DOCS-01 to DOCS-05) - COMPLETE
- Phase 16: Integration Validation (CONF-01 to CONF-03 validation) - COMPLETE

**Phase 16 completed:** Integration test suite with regression baselines, tiered CI workflow, and 85% recall floor enforcement. v2.2 ready for production deployment.

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

None - v2.2 shipped! Ready for production deployment.

### Blockers/Concerns

None - v2.2 complete and production-ready.

**Critical safety requirement validated:** Zero-weight entities (EMAIL_ADDRESS, PEDIATRIC_AGE) invisible in weighted metrics but protected by unweighted recall floor. Integration test `test_unweighted_recall_floor` enforces this with clear error message explaining why weighted metrics cannot replace unweighted.

## Session Continuity

Last session: 2026-01-30
Stopped at: Completed 16-02-PLAN.md (metric comparison charts and v2.2 finalization)
Resume file: None
Next: Celebrate v2.2 ship! 🎉 Then deploy to production or plan next feature development

---
*State initialized: 2026-01-23*
*Last updated: 2026-01-30 after Phase 16 Plan 02 complete - v2.2 SHIPPED ✓*
