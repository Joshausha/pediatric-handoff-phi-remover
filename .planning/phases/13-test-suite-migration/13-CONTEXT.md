# Phase 13: Test Suite Migration - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete test coverage for float weights and risk-weighted metrics. Validate that the dual-weight recall framework calculates correctly with float precision. This phase tests existing implementation — it does NOT add new functionality.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

User delegated all testing decisions to Claude based on the project goal: **high recall PHI detection**.

Claude will decide based on these principles:

**Test organization:**
- Keep tests in existing `tests/` structure
- Add to `test_weighted_metrics.py` for weighted calculation coverage
- Separate concerns: float precision tests vs divergence validation tests

**Float comparison strategy:**
- Use `pytest.approx()` with relative tolerance (1e-6 default)
- Avoid exact float equality assertions
- Document tolerance rationale in test docstrings

**Divergence validation:**
- Create test cases where frequency and risk weights deliberately differ
- Verify both metrics calculate independently and correctly
- Include edge case: zero-weight entities visible in unweighted but invisible in weighted

**Coverage scope:**
- Unit tests only for fast CI execution (<5 seconds target)
- Test the calculation functions, not the full evaluation pipeline
- Edge cases: zero weights, max weights, mixed scenarios

**HIPAA safety focus:**
- Always test that unweighted recall remains visible as safety floor
- Verify zero-weight entities (EMAIL_ADDRESS, PEDIATRIC_AGE) don't disappear silently

</decisions>

<specifics>
## Specific Ideas

No specific requirements from user — open to standard testing approaches that support high recall goals.

**Guiding principle:** Tests should catch regressions that could silently reduce recall.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-test-suite-migration*
*Context gathered: 2026-01-29*
