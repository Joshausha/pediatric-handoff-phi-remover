# Phase 2: Threshold Calibration - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Optimize detection and validation thresholds using precision-recall curve analysis. Goal is to improve overall recall from ~78% to >90% through threshold tuning alone. Pattern improvements and deny list refinements are separate phases (3 and 4).

</domain>

<decisions>
## Implementation Decisions

### Methodology
- Per-entity thresholds (not global) — each of the 8 entity types gets individually optimized
- Threshold range: 0.3 to 0.6 (focused on typical Presidio confidence scores)
- Step size: 0.10 (coarse sweep: 0.30, 0.40, 0.50, 0.60)
- Run against both standard (seed=42) and adversarial (seed=43) synthetic datasets

### Decision Criteria
- Primary optimization target: **Maximize F2 score** (recall weighted 2x precision)
- Hard recall floor: **90% minimum** — reject any threshold that drops recall below 90%
- Tiebreaker when F2 scores within 0.5%: **Higher recall wins** (HIPAA-conservative)

### Claude's Discretion
- Output format (PR curves, tables, visualizations)
- How results are saved and documented
- Script structure and implementation approach
- How new thresholds are applied to config.py
- Whether to add CLI flags or environment variable overrides

</decisions>

<specifics>
## Specific Ideas

- Research project context — methodology should be defensible and reproducible
- Per-entity approach addresses known weak spots (ROOM 19%, PEDIATRIC_AGE 25% adversarial recall)
- Align validation threshold with detection threshold (fix current 0.35/0.7 mismatch noted in STATE.md)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-threshold-calibration*
*Context gathered: 2026-01-23*
