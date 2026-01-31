# Phase 19: Provider Name Detection - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Detect and redact provider names (physicians, nurses, other clinical staff) mentioned in handoff transcripts. Provider names are not direct HIPAA identifiers but are redacted conservatively to minimize re-identification risk when combined with other context.

</domain>

<decisions>
## Implementation Decisions

### PHI Scope Decision
- **Conservative approach**: Redact all provider names (Dr., nurses, attendings, etc.)
- Rationale: Minimize re-identification risk even though provider names aren't HIPAA's 18 identifiers
- Provider names combined with timing/location could narrow down patient identity

### Claude's Discretion
- Title detection strategy (Dr., RN, NP, PA, MD suffixes)
- Context patterns ("his nurse is [Name]", "the attending is [Name]", "paged Dr. [Name]")
- Deny list for generic role references ("the nurse", "the attending" without names)
- Score/confidence tuning (following Phase 18 patterns with 0.85 for high-confidence matches)
- Apply lookbehind patterns similar to Guardian detection (preserve context words)
- Use same capital-letter requirement as Phase 18-03 to prevent false positives

</decisions>

<specifics>
## Specific Ideas

- Follow Phase 18 (Guardian Edge Cases) implementation patterns — proven effective
- Use similar possessive patterns: "his nurse Sarah", "her doctor is Dr. Jones"
- Apply context-word patterns: "with Dr. [Name]", "paged [Name]", "the attending is [Name]"
- Preserve role words while redacting names: "his nurse [NAME]" (not just "[NAME]")

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 19-provider-name-detection*
*Context gathered: 2026-01-30*
