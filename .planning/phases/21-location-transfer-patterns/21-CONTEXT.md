# Phase 21: Location/Transfer Patterns - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Improve LOCATION entity detection from 20% to ≥60% recall by adding transfer context patterns, hospital/clinic names, and city/town references. Focus on spoken handoff context where locations indicate where patients came from or where they receive care.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

User delegated all implementation decisions. Claude has flexibility on:

**Transfer context patterns:**
- Which context phrases to use ("from", "transferred from", "came from", "sent from")
- How to structure lookbehind/lookahead patterns
- Score thresholds for different context strengths

**Location type scope:**
- Priority order for location types (hospitals first, then cities, then clinics)
- Whether to use NER boosting or custom patterns
- How to handle ambiguous location names

**False positive handling:**
- Extending existing LOCATION deny list for unit names
- Handling common place names that appear in clinical contexts
- Score adjustments for low-confidence matches

**PCP/clinic references:**
- Pattern structure for "Dr X at Y Clinic" constructs
- Whether to detect standalone clinic names or require context
- How to preserve provider context while redacting location

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches based on existing codebase patterns.

Reference existing recognizer implementations:
- ROOM recognizer (Phase 17) for context-based detection patterns
- GUARDIAN recognizer (Phase 18) for lookbehind/lookahead structure
- Existing LOCATION deny list in app/config.py

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 21-location-transfer-patterns*
*Context gathered: 2026-01-30*
