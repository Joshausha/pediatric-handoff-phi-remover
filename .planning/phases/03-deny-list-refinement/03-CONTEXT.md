# Phase 3: Deny List Refinement - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Reduce false positives through expanded medical vocabulary deny lists with consistent case handling. Scope includes: case normalization across all deny lists, expanding medical abbreviation coverage, and creating deny lists for all custom entity types (GUARDIAN_NAME, PEDIATRIC_AGE). Pattern improvements (regex changes, recognizer modifications) are Phase 4—not this phase.

</domain>

<decisions>
## Implementation Decisions

### Medical Abbreviation Scope
- Conservative approach: Only add abbreviations with clear false positive evidence from testing
- Entity-specific deny lists: LOCATION deny list for 'NC', 'OR'; PERSON deny list for 'mom', 'dad'
- Evidence-required maintenance: New terms only added when false positive is documented in test case
- Context-only for ambiguous terms: Don't add terms that could be both abbreviations AND names (e.g., 'Gene', 'Art', 'Ed')—let Presidio's context analysis handle them

### Case Handling Strategy
- Case-insensitive matching: Store terms lowercase, compare lowercase ('NC', 'nc', 'Nc' all match)
- Normalize all existing deny lists to lowercase during this phase
- Test-driven changes: Every deny list addition needs a test case that was failing before

### Claude's Discretion
- Deny list storage location (keep in config.py vs external file)
- Specific implementation of case normalization
- Organization of entity-specific deny lists within config.py

</decisions>

<specifics>
## Specific Ideas

- Codebase is Python (FastAPI), not TypeScript—continue with Python for medical NLP library compatibility
- Current LOCATION deny list already has some entries but uses exact match (case-sensitive bug noted in STATE.md)
- Precision target: improve from 87.4% to >90% per ROADMAP.md success criteria

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-deny-list-refinement*
*Context gathered: 2026-01-23*
