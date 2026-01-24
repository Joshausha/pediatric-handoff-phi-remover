# Phase 4: Pattern Improvements - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix regex edge cases and enhance custom recognizers to catch all PHI variants. Targets: PEDIATRIC_AGE recall from 35.8% to >90%, ROOM recall from 32.1% to >90%. Includes lookbehind patterns, bidirectional patterns, and speech artifact handling.

</domain>

<decisions>
## Implementation Decisions

### Pediatric Age Handling
- **Keep ages for clinical utility** — age alone is not PHI under HIPAA (unless 90+)
- Support both abbreviated formats ("2yo", "3mo", "6wo") AND gestational notation ("34 weeker", "ex-28 weeker", "36+3")
- Focus on removing other identifiers (names, MRN, room) rather than redacting ages
- This is a **scope change**: PEDIATRIC_AGE recognizer should be reviewed for whether it's needed at all

### Room/Bed Patterns
- Preserve unit names (PICU, NICU, 4 West) — clinical context, not identifying
- Require keywords ("room", "bed") before numbers — conservative approach to avoid false positives on standalone numbers
- Handle multiple formats: "PICU room 12", "NICU bed 3A", "4 West room 412", "bed A"
- Lettered beds ("bed A", "bed B"): Claude's discretion based on HIPAA minimum necessary

### Speech Artifact Handling
- Handle repetitions/stutters (e.g., "mom mom Jessica" should still catch "Jessica")
- **Defer fuzzy matching** for transcription errors (e.g., "Jessika" for "Jessica") — rely on Presidio NER for now
- Complete words only — no need to handle partial/truncated words (Whisper produces complete words)
- Investigate punctuation patterns in actual transcripts — unknown if Whisper adds inconsistent punctuation

### Pattern Strictness
- **Balanced approach**: Target >95% recall with >85% precision
- Entity-based tiebreaker: High-risk entities (names, MRN) default to redact; low-risk (room letters) may preserve
- **Add confidence score display** for low-confidence redactions to enable human review

### Claude's Discretion
- Whether PEDIATRIC_AGE recognizer should be disabled entirely (since ages aren't PHI)
- Exact regex patterns for gestational notation variants
- Punctuation-flexible patterns if investigation shows variability
- Lettered bed redaction decision based on HIPAA minimum necessary analysis

</decisions>

<specifics>
## Specific Ideas

- "Age can be important to know clinically" — preserve rather than redact
- "Conservative: require keywords" for room numbers — avoid false positives on standalone 3-4 digit numbers
- Current recall targets from STATE.md: PEDIATRIC_AGE 35.8% → 90%, ROOM 32.1% → 90%
- Balanced approach reflects research context — not public release, but still needs HIPAA compliance

</specifics>

<deferred>
## Deferred Ideas

- **Fuzzy name matching** (Soundex/Metaphone) for transcription errors — add later if recall still insufficient
- **Confidence threshold tuning** — may need calibration after patterns are improved

</deferred>

---

*Phase: 04-pattern-improvements*
*Context gathered: 2026-01-23*
