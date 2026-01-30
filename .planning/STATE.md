# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-30)

**Core value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content
**Current focus:** Planning next milestone

## Current Position

Phase: 17 of 22 (Room Pattern Expansion) - IN PROGRESS
Plan: 2 of 2 (17-02-PLAN.md completed)
Status: v2.3 in progress, Phase 17 Plans 01-02 complete (recall/precision balance)
Last activity: 2026-01-30 — Completed 17-02-PLAN.md (ROOM precision 17% → 48.9%, recall 51.1%)

Progress: [##########] 100% v1.0 | [##########] 100% v2.0 | [##########] 100% v2.1 | [##########] 100% v2.2 | [###       ] 33% v2.3

## Milestones Shipped

| Version | Name | Phases | Plans | Shipped |
|---------|------|--------|-------|---------|
| v1.0 | PHI Detection Overhaul | 1-8 | 11 | 2026-01-25 |
| v2.0 | CI/CD Pipeline Fix | 9 | 2 | 2026-01-26 |
| v2.1 | Over-Detection Quality Pass | 10-12 | 7 | 2026-01-28 |
| v2.2 | Dual-Weight Recall Framework | 13-16 | 4 | 2026-01-30 |

## v2.3 Roadmap Overview

**6 phases (17-22) targeting recall improvements:**

- Phase 17: Room Pattern Expansion (Precision 17% → 48.9%, Recall 32% → 51%) - COMPLETE (2/2 plans)
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

Recent decisions affecting v2.2-v2.3:
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
- **ROOM-CONTEXT-BOOST-STRATEGY** (Phase 17-01): Use score=0.30 for standalone numbers, rely on Presidio context enhancement (+0.35 boost)
- **ROOM-NEGATIVE-PATTERNS** (Phase 17-01): Comprehensive negative lookahead/lookbehind to exclude clinical units (mg, ml, kg, %, old, day, etc.)
- **ROOM-CONTEXT-EXPANSION** (Phase 17-01): Expanded context word list to 35+ terms (prepositions, verbs, synonyms) for conversational handoff patterns
- **ROOM-EXPLICIT-CONTEXT** (Phase 17-02): Replace broad contextual pattern with explicit context requirement (score=0.60), achieving 48.9% precision (up from 17%)
- **ROOM-ADDRESS-EXCLUSION** (Phase 17-02): Use negative lookahead to exclude street addresses from "transferred from" pattern

### Pending Todos

- Decide next direction: Continue recall improvements (Phase 18-21) OR focus on other milestones
- Plan Phase 18 (Guardian Edge Cases) - if proceeding with recall improvements
- Plan Phase 19 (Provider Name Detection) - if proceeding with recall improvements
- Plan Phase 20 (Phone/Pager Patterns) - if proceeding with recall improvements
- Plan Phase 21 (Location/Transfer Patterns) - if proceeding with recall improvements
- Consider ROOM recall target adjustment in Phase 22 (51% achieved vs 80% target)

### Blockers/Concerns

**ROOM Recall Gap (Phase 17):**
- Target: 80% recall
- Achieved: 51.1% recall after precision fix (Phase 17-02)
- Gap: 29 percentage points
- Trade-off: Precision improved from 17% → 48.9% (79.7% reduction in false positives)
- Analysis:
  - Phase 17-01 broad pattern (score=0.30) achieved 54% recall but only 17% precision (236 FP)
  - Phase 17-02 explicit context pattern (score=0.60) achieved 51% recall and 49% precision (48 FP)
  - Trade-off: Removed 188 false positives at cost of 3 percentage points recall
- Recommended next steps:
  - Phase 18-21: Improve recall for other entity types (Guardian, Provider, Phone, Location)
  - Phase 22: Re-evaluate ROOM recall target (80% may require NER, not pattern-based approach)
  - Alternative: Accept 50-60% ROOM recall as sufficient for v2.3 given precision constraints

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
Stopped at: Completed Phase 17 Plans 01-02 (ROOM precision/recall balance)
Resume file: None
Next: Continue with Phase 18-21 planning OR focus on other milestones (Phase 17 complete with acceptable balance)

---
*State initialized: 2026-01-23*
*Last updated: 2026-01-30 — v2.2 Dual-Weight Recall Framework shipped and archived*
