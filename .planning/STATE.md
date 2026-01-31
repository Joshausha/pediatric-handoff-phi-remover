# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-30)

**Core value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content
**Current focus:** Planning next milestone

## Current Position

Phase: 18 of 22 (Guardian Edge Cases) - IN PROGRESS
Plan: 2 of 3 (18-02-PLAN.md completed)
Status: v2.3 in progress, Phase 18 in progress (appositive patterns added)
Last activity: 2026-01-31 — Completed 18-02-PLAN.md (41 appositive guardian patterns, 3 new tests passing)

Progress: [##########] 100% v1.0 | [##########] 100% v2.0 | [##########] 100% v2.1 | [##########] 100% v2.2 | [#####     ] 50% v2.3

## Milestones Shipped

| Version | Name | Phases | Plans | Shipped |
|---------|------|--------|-------|---------|
| v1.0 | PHI Detection Overhaul | 1-8 | 11 | 2026-01-25 |
| v2.0 | CI/CD Pipeline Fix | 9 | 2 | 2026-01-26 |
| v2.1 | Over-Detection Quality Pass | 10-12 | 7 | 2026-01-28 |
| v2.2 | Dual-Weight Recall Framework | 13-16 | 4 | 2026-01-30 |

## v2.3 Roadmap Overview

**6 phases (17-22) targeting recall improvements:**

- Phase 17: Room Pattern Expansion (Precision 52%, Recall 98%, F1 68%) - COMPLETE (3/3 plans)
- Phase 18: Guardian Edge Cases (possessive/appositive patterns) - IN PROGRESS (2/3 plans)
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
- **ROOM-NUMBER-ONLY-PATTERNS** (Phase 17-03): Use lookbehind to match only room numbers (not "bed 847", just "847"), achieving 98% exact match rate and 100% effective recall
- **ROOM-PATTERN-PRIORITY** (Phase 17-03): Lower full-match pattern scores to 0.50, number-only patterns (0.70) take priority, reducing overlap from 55% to 2%
- **ROOM-INTERIM-TARGET** (Phase 17-03): Document 55% as interim target (achieved 98%), defer final validation to Phase 22

### Pending Todos

- Decide next direction: Continue recall improvements (Phase 18-21) OR focus on other milestones
- Plan Phase 18 (Guardian Edge Cases) - if proceeding with recall improvements
- Plan Phase 19 (Provider Name Detection) - if proceeding with recall improvements
- Plan Phase 20 (Phone/Pager Patterns) - if proceeding with recall improvements
- Plan Phase 21 (Location/Transfer Patterns) - if proceeding with recall improvements
- Phase 22 will finalize all recall targets (ROOM far exceeds interim 55% target at 98%)

### Blockers/Concerns

**ROOM Recall Gap RESOLVED (Phase 17):**
- Original target: 80% recall
- Revised interim target: 55% (pattern-based approach limit)
- Achieved: 98% recall (Phase 17-03 number-only patterns)
- Precision: 52% (Phase 17-02 explicit context, Phase 17-03 number-only)
- Resolution:
  - Phase 17-01: Broad pattern (score=0.30) → 54% recall, 17% precision (236 FP)
  - Phase 17-02: Explicit context (score=0.60) → 51% recall, 49% precision (48 FP)
  - Phase 17-03: Number-only patterns (lookbehind) → 98% recall, 52% precision, 2% overlap
  - Key insight: Overlap mismatch (55%) was inflating both FP and FN counts
- Next steps:
  - Phase 18-21: Improve recall for other entity types (Guardian, Provider, Phone, Location)
  - Phase 22: Final validation across all entity types

**No current blockers or concerns**

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
Stopped at: Completed Phase 17 (all 3 plans) — ROOM detection 98% recall, 52% precision
Resume file: None
Next: Continue with Phase 18-21 planning OR focus on other milestones (Phase 17 complete, far exceeding targets)

---
*State initialized: 2026-01-23*
*Last updated: 2026-01-30 — Phase 17 complete (ROOM 98% recall, 52% precision)*
