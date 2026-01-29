# Phase 14: Report Generation Refinement - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Polish the three-metric evaluation report display with clear explanations. Users need to understand what each metric measures and why they might differ. This phase covers report formatting and explanation content—NOT new metrics, detection logic changes, or calculation modifications (those are complete from Phase 13).

</domain>

<decisions>
## Implementation Decisions

### Metric Display Format
- Single table with all three metric types (unweighted, frequency-weighted, risk-weighted)
- Columns: Recall, Precision, F2 for each weighting scheme
- Unweighted row labeled as "Unweighted (Safety Floor)" — inline annotation
- All metrics displayed with 1 decimal place precision (e.g., 86.4%, 94.2%)

### Weight Comparison Table
- Two side-by-side tables: one sorted by frequency weight, one sorted by risk weight
- Each table shows: Entity, Weight (simple two-column format)
- Zero-weight entities (EMAIL_ADDRESS, PEDIATRIC_AGE) included with note explaining exclusion from weighted metrics
- Visually highlight entities where frequency weight ≠ risk weight (bold or color)

### Divergence Documentation
- Concrete example explaining when/why metrics diverge (e.g., "If PERSON missed, risk recall drops more than frequency recall because...")
- Placed after metrics table — users see numbers first, then explanation
- Include guidance with context: "For HIPAA compliance, unweighted recall is your floor. For operational insight, consider weighted metrics."
- Quantify the gap explicitly when divergence occurs (e.g., "Frequency recall: 94.2%, Risk recall: 91.8% (−2.4 pp)")

### Claude's Discretion
- Exact styling/colors for weight divergence highlighting
- Phrasing of concrete divergence example
- Table header labels and formatting details
- Whether to use markdown tables or other formatting

</decisions>

<specifics>
## Specific Ideas

- User wants to see both frequency and risk sorted views simultaneously for comparison
- Highlighting should draw attention to entities that rank differently across the two weighting schemes
- The report should help users understand the "why" behind metric differences, not just show numbers

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 14-report-refinement*
*Context gathered: 2026-01-29*
