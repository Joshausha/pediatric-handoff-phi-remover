# Phase 7: Alternative Engine Benchmark - Context

**Gathered:** 2026-01-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Compare Philter-UCSF and Stanford BERT de-identification engines against current Presidio setup to determine if switching engines provides meaningful improvement for spoken pediatric handoff use case. Output is a documented decision (stick with Presidio, switch, or hybrid), not production code.

</domain>

<decisions>
## Implementation Decisions

### Benchmark Scope
- Spot-check 10-20 synthetic samples for annotation quality before benchmarking
- After validation, benchmark on full corpus (600 handoffs: 500 standard + 100 adversarial)
- Use existing synthetic datasets from Phase 1

### Engine Configuration
- Moderate optimization effort — translate pediatric patterns, tune thresholds to match recall targets
- Stanford BERT runs as Presidio backend (TransformersNlpEngine), not standalone
- Philter-UCSF runs independently with its own config format
- Document limitations when engines can't support specific pattern types (e.g., lookbehinds)

### Decision Criteria
- Primary metric: Weighted recall (spoken handoff relevance weights from Phase 8)
- Precision floor: >70% required to maintain clinical utility
- Improvement threshold: >5% weighted recall improvement justifies switching engines
- If no engine beats Presidio by 5%+: Consider hybrid approach (e.g., BERT for PERSON, Presidio for custom patterns)

### Pattern Translation
- Focus on high-weight patterns: GUARDIAN_NAME (weight 5), ROOM (weight 4)
- Skip low-weight/disabled patterns (MRN weight 1, PEDIATRIC_AGE disabled)
- No deny list translation — test raw pattern matching for cleaner comparison
- If pattern issues discovered: fix for all engines to keep comparison fair

### Claude's Discretion
- Philter pattern translation approach (direct port vs Philter defaults + add-ons)
- PEDIATRIC_AGE inclusion in benchmark (weight=0, so no impact on decision)
- Exact threshold tuning per engine
- Hybrid architecture design if hybrid approach selected

</decisions>

<specifics>
## Specific Ideas

- User wants to validate synthetic data quality before trusting benchmark results
- Hybrid approach is preferred outcome if no clear winner — leverage strengths of multiple engines
- Fair comparison requires fixing pattern issues discovered during translation for all engines

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-alternative-engine-benchmark*
*Context gathered: 2026-01-25*
