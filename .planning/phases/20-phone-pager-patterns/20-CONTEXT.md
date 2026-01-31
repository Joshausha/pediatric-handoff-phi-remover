# Phase 20: Phone/Pager Patterns - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Improve PHONE_NUMBER detection from 76% to ≥90% recall. Focus on clinical handoff-specific patterns: pager numbers, extensions, internal hospital lines. No false positives on clinical numbers (vitals, doses, weights).

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

User delegated all implementation decisions. Claude has full flexibility on:

**Pattern scope:**
- Which phone formats to prioritize (pagers, extensions, cell numbers, hospital lines)
- Order of pattern implementation
- Which edge cases to handle vs. defer

**Context requirements:**
- How much surrounding context required for detection
- Whether standalone 5-digit numbers need context words
- Which context words trigger phone detection ("call", "page", "reach", etc.)

**Overlap handling:**
- How to distinguish phone/pager from vitals, doses, weights, room numbers
- Negative patterns to exclude clinical measurements
- Confidence adjustments based on context

**Confidence scoring:**
- Threshold selection for different pattern types
- Score differentiation between high-context and low-context matches
- Balance between recall improvement and precision maintenance

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

Research should analyze:
1. Current false negatives in validation set (what phone patterns are missed?)
2. Common handoff phone formats (pager, extension, direct lines)
3. Overlap risks with clinical numbers

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 20-phone-pager-patterns*
*Context gathered: 2026-01-30*
