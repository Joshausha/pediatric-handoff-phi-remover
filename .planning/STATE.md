# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-29)

**Core value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content
**Current focus:** v2.2 Dual-Weight Recall Framework - Phase 15 complete, ready for Phase 16

## Current Position

Phase: 15 of 16 (Documentation Updates)
Plan: 1 of 1 COMPLETE
Status: Phase 15 complete
Last activity: 2026-01-29 — Completed 15-01-PLAN.md (dual-weighting documentation)

Progress: [##########] 100% v1.0 | [##########] 100% v2.0 | [##########] 100% v2.1 | [#######░░░] 75% v2.2

## Milestones Shipped

| Version | Name | Phases | Plans | Shipped |
|---------|------|--------|-------|---------|
| v1.0 | PHI Detection Overhaul | 1-8 | 11 | 2026-01-25 |
| v2.0 | CI/CD Pipeline Fix | 9 | 2 | 2026-01-26 |
| v2.1 | Over-Detection Quality Pass | 10-12 | 7 | 2026-01-28 |

## v2.2 Roadmap Overview

**4 phases (13-16) covering 20 requirements:**

- Phase 13: Test Suite Migration (TEST-01 to TEST-06) - COMPLETE
- Phase 14: Report Generation Refinement (REPT-01 to REPT-06) - COMPLETE
- Phase 15: Documentation Updates (DOCS-01 to DOCS-05) - COMPLETE
- Phase 16: Integration Validation (CONF-01 to CONF-03 validation) - Ready to plan

**Phase 15 completed:** Dual-weighting methodology documented (frequency=spoken prevalence, risk=leak severity), v2.2 milestone marked as shipped.

## CI/CD Status

**GitHub Actions:** ALL GREEN

| Workflow | Status | Details |
|----------|--------|---------|
| test.yml | PASSING | 208 passed, 8 xfailed, 1 xpassed |
| docker.yml | PASSING | Build completes in ~24s |

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

### Pending Todos

None - ready to plan Phase 16.

### Blockers/Concerns

**Critical safety requirement:** Zero-weight entities (EMAIL_ADDRESS, PEDIATRIC_AGE) invisible in weighted metrics. Must always report unweighted recall as HIPAA compliance floor. (Now validated by `test_zero_weight_entities_invisible_in_weighted_visible_in_unweighted`)

## Session Continuity

Last session: 2026-01-29
Stopped at: Completed 15-01-PLAN.md
Resume file: None
Next: `/gsd:plan-phase 16`

---
*State initialized: 2026-01-23*
*Last updated: 2026-01-29 after Phase 15 complete*
