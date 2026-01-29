# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-28)

**Core value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content
**Current focus:** v2.1 complete - over-detection quality pass shipped

## Current Position

Phase: 12 of 12 (Regression Validation)
Plan: 1 of 1 (complete)
Status: Phase complete - v2.1 shipped
Last activity: 2026-01-28 — Completed 12-01-PLAN.md (regression validation and v2.1 milestone)

Progress: [##########] 100% v1.0 | [##########] 100% v2.0 | [##########] 100% v2.1

## Milestones Shipped

| Version | Name | Phases | Plans | Shipped |
|---------|------|--------|-------|---------|
| v1.0 | PHI Detection Overhaul | 1-8 | 11 | 2026-01-25 |
| v2.0 | CI/CD Pipeline Fix | 9 | 2 | 2026-01-26 |
| v2.1 | Over-Detection Quality Pass | 10-12 | 7 | 2026-01-28 |

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
- ~~All 45 documented false positives from Phase 10~~ FIXED in Phase 11 (100% elimination)

## Accumulated Context

### Decisions

Recent decisions affecting current work:
- **v2.1 scope**: Focus on over-detection quality via systematic test script generation and deny list expansion
- **Test strategy**: Generate realistic + edge-case scripts, record and process to discover false positives
- **Research findings**: Duration patterns and flow terms need deny list additions; word boundaries critical
- **10-01: Script organization**: Separated realistic vs edge-case scripts for clear purpose differentiation
- **10-01: Logging structure**: Per-script sections with tables, then batch pattern analysis for systematic documentation
- **10-02: Manual review**: Used human review over automation to identify context-dependent false positives
- **10-02: Impact prioritization**: Prioritized Phase 11 work by false positive volume (DATE_TIME 58%, LOCATION 33%, PERSON 9%)
- **11-02: Broad deny terms justified**: Added standalone "high" and "low" to LOCATION deny list despite being broad - overwhelmingly used for oxygen flow rates in pediatric handoffs, minimal risk of missing legitimate location PHI
- **11-02: Dual deny list inclusion**: Added "flow" to both LOCATION and PERSON deny lists to prevent false positives in either entity type
- **11-03: Unit preservation**: Use separate fixed-width lookbehind patterns per unit type instead of alternation for reliable regex matching
- **11-04: Text-based verification**: Process test scripts through Presidio directly instead of re-recording audio - faster, more precise, removes transcription variables
- **12-01: Regression baseline**: Phase 5 validation results used as baseline (86.4% recall, same as current - no regression)
- **12-01: Precision improvement**: Phase 11 deny lists reduced false positives by 77 (11.6% improvement) while maintaining recall

### Pending Todos

None - v2.1 complete.

### Blockers/Concerns

None - system ready for production use.

## Session Continuity

Last session: 2026-01-28
Stopped at: Completed 12-01-PLAN.md (v2.1 Over-Detection Quality Pass shipped)
Resume file: None
Next: Optional future work - see tech debt for enhancement opportunities

---
*State initialized: 2026-01-23*
*Last updated: 2026-01-28*
