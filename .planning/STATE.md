# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-28)

**Core value:** Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content
**Current focus:** Phase 11 - Deny List Expansion

## Current Position

Phase: 11 of 12 (Deny List Expansion)
Plan: 02 of 3
Status: In progress
Last activity: 2026-01-28 — Completed 11-02-PLAN.md (flow terms and PERSON deny list expansion)

Progress: [##########] 100% v1.0 | [##########] 100% v2.0 | [####░░░░░░] 40% v2.1

## Milestones Shipped

| Version | Name | Phases | Plans | Shipped |
|---------|------|--------|-------|---------|
| v1.0 | PHI Detection Overhaul | 1-8 | 11 | 2026-01-25 |
| v2.0 | CI/CD Pipeline Fix | 9 | 2 | 2026-01-26 |

## CI/CD Status

**GitHub Actions:** ALL GREEN

| Workflow | Status | Details |
|----------|--------|---------|
| test.yml | PASSING | 172 passed, 8 xfailed, 1 xpassed |
| docker.yml | PASSING | Build completes in ~24s |

## Known Issues (Tech Debt)

Tracked via xfail markers in CI:

**Under-detection:**
- 7-digit phone numbers (555-0123)
- Detailed ages (3 weeks 2 days)
- Street addresses (425 Oak Street)

**Over-detection:**
- ~~"Currently on high" as LOCATION~~ FIXED in 11-02
- ~~Duration phrases ("three days of symptoms") as DATE_TIME~~ FIXED in 11-01
- ~~Unit names lost during ROOM redaction~~ FIXED in 11-03

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

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-01-28
Stopped at: Completed 11-02-PLAN.md (flow terms and PERSON deny list expansion)
Resume file: None
Next: Phase 11 complete - ready for final validation

---
*State initialized: 2026-01-23*
*Last updated: 2026-01-28*
