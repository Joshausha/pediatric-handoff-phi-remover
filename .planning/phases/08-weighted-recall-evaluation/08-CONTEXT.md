# Phase 8: Weighted Recall Evaluation - Context

**Gathered:** 2026-01-25
**Status:** Complete (retrospective documentation)

<domain>
## Phase Boundary

Add spoken handoff relevance weighting to evaluate_presidio.py — metrics infrastructure that weights entity importance based on how frequently they appear in actual spoken handoffs. This makes evaluation metrics reflect clinical utility rather than treating all entity types equally.

</domain>

<decisions>
## Implementation Decisions

### Weight methodology
- Weights determined by **combination** of I-PASS frequency analysis (SPOKEN_HANDOFF_ANALYSIS.md) and clinical judgment from personal experience with spoken handoffs
- **0-5 scale chosen for granularity** — binary (relevant/not) too coarse; need to express that ROOM matters more than PHONE but less than PERSON
- **Zero-weight entities** (EMAIL, LOCATION, PEDIATRIC_AGE) are rare but possible in spoken handoffs — weighting at 0 because they're so infrequent they're essentially noise for this use case
- **Weights are provisional (v1)** — should be revisited after Phase 6 real handoff testing when actual data may reveal different patterns than analysis predicted

### Final weight assignments
- PERSON/GUARDIAN_NAME: 5 (most frequently mentioned)
- ROOM: 4 (location context common in handoffs)
- PHONE_NUMBER: 2 (callback numbers occasionally mentioned)
- DATE_TIME: 2 (admission times, procedure dates)
- MEDICAL_RECORD_NUMBER: 1 (rarely verbalized)
- EMAIL_ADDRESS: 0 (never verbalized)
- LOCATION: 0 (street addresses not in verbal handoffs)
- PEDIATRIC_AGE: 0 (ages not PHI under HIPAA unless 90+)

### Claude's Discretion
- Implementation details of weighted calculation
- Report formatting and display choices
- Config.py organization for weight storage

</decisions>

<specifics>
## Specific Ideas

- Weights reflect I-PASS handoff structure — what's actually said during verbal patient handoffs
- Unweighted recall (77.9%) underestimates real-world performance; weighted recall (91.5%) better reflects clinical relevance
- Zero weights don't penalize metrics for entities that aren't spoken anyway

</specifics>

<deferred>
## Deferred Ideas

- Per-specialty weight profiles (ICU vs general peds may differ) — future consideration
- User-configurable weights via UI — not needed for personal QI project

</deferred>

---

*Phase: 08-weighted-recall-evaluation*
*Context gathered: 2026-01-25 (retrospective)*
