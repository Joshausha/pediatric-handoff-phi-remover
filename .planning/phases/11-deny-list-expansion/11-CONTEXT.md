# Phase 11: Deny List Expansion and Unit Preservation - Context

**Gathered:** 2026-01-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Eliminate false positives via targeted deny list additions, matching behavior fixes, and unit name preservation. This phase modifies configuration and recognizer logic — no new PHI entity types or detection capabilities.

</domain>

<decisions>
## Implementation Decisions

### Duration Pattern Handling
- Use pattern-based matching (regex) rather than exhaustive entry lists
- Cover hours, days, weeks, and months (1-14 days, 1-24 hours, 1-4 weeks, 1-3 months)
- Include informal durations: "a day", "a few days", "couple days", "half a day"
- Favor recall over precision — acceptable to block true dates to maximize duration protection (handoffs rarely mention actual calendar dates)

### Flow Terms / Medical Dictionary
- Create a **global medical deny list** that applies to ALL entity types
- Use pattern matching with word boundaries (handles "high-flow", "highflow" variations)
- Cover broader medical vocabulary: respiratory terms, vitals, medication routes, lab terms, procedure names
- Hybrid approach for building initial list: Claude proposes categories, pulls specifics from Phase 10 false positive data
- Merge existing entity-specific deny lists (LOCATION, PERSON) into global list

### Deny List Matching Behavior
- Align all deny lists to use word-boundary substring matching (consistent with DATE_TIME behavior)
- Case-insensitive matching for all deny lists
- Word boundaries include punctuation — "NC," and "(NC)" should match "NC" entry

### Unit Name Preservation
- Use regex capture groups in ROOM recognizer to preserve unit names while redacting room numbers
- Maintain explicit list of pediatric units: PICU, NICU, PEDS, ED, CVICU, CCU, L&D, PACU, OR, ICU
- "PICU bed 12" → "PICU [ROOM]"

### Testing Approach
- Phrase-level tests using real transcript phrases from Phase 10 recordings
- Full regression testing against all 27 real handoff recordings for every change
- No changes deployed without passing full test suite

### False Positive Workflow
- User maintains a log file to record false positives encountered in daily use
- Claude reviews and proposes fixes on demand (not scheduled)
- All fixes require full regression testing before deployment

### Claude's Discretion
- Configuration structure (Python vs external files) — maintain what works best for the codebase
- Handling of room numbers without unit context ("bed 12") — evaluate PHI risk and recommend
- Exact regex patterns for duration matching
- Initial medical vocabulary list compilation from Phase 10 data + medical knowledge

</decisions>

<specifics>
## Specific Ideas

- Duration patterns should cover natural speech: "one day of fever", "two hours of symptoms"
- Global deny list should be the single source of truth for medical terminology protection
- Word boundary matching must handle transcription variability (Whisper output quirks)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-deny-list-expansion*
*Context gathered: 2026-01-28*
