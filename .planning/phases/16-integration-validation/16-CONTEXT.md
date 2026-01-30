# Phase 16: Integration Validation - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

End-to-end validation that the dual-weight recall framework works correctly. Establish regression baselines in CI. Confirm unweighted, frequency-weighted, and risk-weighted metrics all calculate and display correctly with no regressions from v2.1.

</domain>

<decisions>
## Implementation Decisions

### Validation Scope
- Run against both synthetic dataset AND real handoff validation set (27 recordings)
- Automated in CI (GitHub Actions) — not a one-time manual run
- Tiered approach: quick smoke test on every push, full run on main branch merges
- Real handoff validation uses pre-computed expected results (no audio in CI, no PHI concerns)

### Regression Thresholds
- Unweighted recall floor: ≥85% (hard fail if below)
- CI failure blocks PR merge — regression must be fixed
- Weighted metric thresholds: Claude's discretion on whether frequency/risk-weighted need separate thresholds
- Baseline storage format: Claude's discretion (hardcoded vs JSON file)

### Output Artifacts
- Both CI logs AND markdown validation report
- Report is summary-level (overall metrics, not per-entity breakdown)
- Report storage location: Claude's discretion (CI artifact vs committed)
- Include metric comparison charts (PNG) — visual representation of unweighted vs weighted metrics

### Divergence Validation
- Frequency > risk recall pattern: documented observation, not automated assertion
- Flag large divergence between frequency and risk metrics in report
- Divergence threshold for flagging: Claude's discretion
- Risk weight config validation: Claude's discretion (implicit via metrics vs explicit assertion)

### Claude's Discretion
- Whether weighted metrics need their own regression thresholds
- Baseline storage format (hardcoded constants vs JSON file)
- Markdown report storage location (CI artifact only vs committed to repo)
- Divergence flagging threshold (somewhere between 5-10 percentage points)
- Whether to add explicit test for risk weight config loading

</decisions>

<specifics>
## Specific Ideas

- Tiered CI approach mirrors common patterns (fast feedback on PR, comprehensive on merge)
- Pre-computed results for real handoffs avoids PHI in CI while still validating against real data
- Metric charts make it easy to spot issues visually during review

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 16-integration-validation*
*Context gathered: 2026-01-30*
