# Phase 22: Validation & Recall Targets - Research

**Researched:** 2026-01-31
**Domain:** End-to-end validation testing and metric threshold enforcement
**Confidence:** HIGH

## Summary

Phase 22 requires comprehensive end-to-end validation confirming all recall targets from Phases 17-21 improvements. The project already has a mature validation infrastructure with dual-weighting framework (frequency vs. risk weights), bootstrap confidence intervals, JSON baselines for regression detection, and tiered CI/CD workflows.

Key findings:
- **Existing infrastructure is comprehensive**: `run_validation.py` orchestrates full evaluation with bootstrap CI, weighted metrics, error taxonomy, and deployment decision
- **Pytest integration tests already exist**: `test_full_evaluation.py` and `test_regression.py` provide module-scoped validation with 1% tolerance
- **Module-scope fixtures are optimal**: Balance test isolation with performance for expensive validation runs (established best practice)
- **Three-metric reporting is architected**: Unweighted (HIPAA floor), frequency-weighted (clinical reality), risk-weighted (leak severity)

**Primary recommendation:** Build Phase 22 validation by extending existing `tests/integration/` pytest infrastructure with entity-specific recall threshold tests and comprehensive milestone validation report generation.

## Standard Stack

The established libraries/tools for validation testing in this project:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 7.x+ | Test framework and runner | Industry standard Python testing framework with powerful fixtures and parametrization |
| numpy | 1.x+ | Bootstrap sampling and statistical calculations | Required for confidence interval calculations in `evaluate_presidio.py` |
| pydantic | 2.x+ | Settings validation and type safety | Already used for config.py weights validation (CONF-01, CONF-02, CONF-03) |
| pathlib | stdlib | File path handling | Modern Python standard for cross-platform paths |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json | stdlib | Baseline storage and report output | Simple regression baselines (already established pattern) |
| dataclasses | stdlib | Structured test result containers | Already used in `evaluate_presidio.py` for DetectionResult, EvaluationMetrics |
| pytest-xdist | Latest | Parallel test execution | Optional performance optimization for large test suites |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON baselines | pytest-regressions plugin | JSON baselines are simpler, easier to understand, fewer dependencies (established in Phase 12) |
| Module-scoped fixtures | Function-scoped fixtures | Module scope reduces test time but requires careful state management (project uses module scope successfully) |
| pytest | unittest | Pytest provides better fixtures, parametrization, and is already project standard |

**Installation:**
```bash
# Core dependencies already in requirements-dev.txt
pip install pytest numpy pydantic
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── integration/               # Integration tests (already exists)
│   ├── test_full_evaluation.py    # Full validation with all metrics
│   ├── test_regression.py         # Baseline regression detection
│   └── test_phase22_validation.py # NEW: Entity-specific recall targets
├── baselines/                 # Regression baselines (already exists)
│   ├── regression.json        # Current baseline with all 9 metrics
│   └── phase22_targets.json   # NEW: Entity-specific recall targets
├── run_validation.py          # Orchestrator (already exists)
└── evaluate_presidio.py       # Evaluation engine (already exists)
```

### Pattern 1: Module-Scoped Validation Fixture
**What:** Run expensive validation once per test module, share results across all tests
**When to use:** When validation is expensive (bootstrap sampling, full dataset evaluation)
**Example:**
```python
# Source: tests/integration/test_full_evaluation.py lines 19-26
@pytest.fixture(scope="module")
def validation_results():
    """Run validation once for all tests in module."""
    return run_validation(
        input_path=Path("tests/synthetic_handoffs.json"),
        n_bootstrap=1000,  # Reduced for speed
        verbose=False,
    )

def test_recall_floor(validation_results):
    """Tests consume shared fixture without re-running validation."""
    assert validation_results["metrics"]["recall"] >= 0.85
```

**Key insight:** Module scope provides 10-100x speedup for test suites with shared expensive setup, but requires tests to be read-only consumers of fixture data.

### Pattern 2: JSON Baseline Regression Detection
**What:** Store expected metrics in JSON, compare current run with 1% tolerance
**When to use:** Detect unintended metric changes across code changes
**Example:**
```python
# Source: tests/integration/test_regression.py lines 47-104
baseline_path = Path("tests/baselines/regression.json")
with open(baseline_path) as f:
    baseline = json.load(f)

results = run_validation(input_path, n_bootstrap=1000)
current = results["metrics"]

for metric_name in metrics_to_compare:
    baseline_value = baseline[metric_name]
    current_value = current[metric_name]

    assert current_value == pytest.approx(baseline_value, rel=0.01), (
        f"REGRESSION: {metric_name} changed from {baseline_value:.4f} "
        f"to {current_value:.4f} (>1% change)"
    )
```

**Key insight:** 1% tolerance accommodates bootstrap sampling variation while catching real regressions. Clear error messages explain how to update baselines when changes are intentional.

### Pattern 3: Three-Metric Validation Framework
**What:** Always report unweighted (HIPAA floor), frequency-weighted (clinical reality), risk-weighted (leak severity)
**When to use:** Every validation run - provides complementary evaluation lenses
**Example:**
```python
# Source: tests/run_validation.py lines 196-202
metrics = {
    # Unweighted (HIPAA compliance floor)
    "recall": float(metrics.recall),
    "precision": float(metrics.precision),
    "f2": float(metrics.f2),
    # Frequency-weighted (spoken prevalence)
    "freq_weighted_recall": float(metrics.weighted_recall(settings.spoken_handoff_weights)),
    "freq_weighted_precision": float(metrics.weighted_precision(settings.spoken_handoff_weights)),
    "freq_weighted_f2": float(metrics.weighted_f2(settings.spoken_handoff_weights)),
    # Risk-weighted (leak severity)
    "risk_weighted_recall": float(metrics.risk_weighted_recall(settings.spoken_handoff_risk_weights)),
    "risk_weighted_precision": float(metrics.risk_weighted_precision(settings.spoken_handoff_risk_weights)),
    "risk_weighted_f2": float(metrics.risk_weighted_f2(settings.spoken_handoff_risk_weights)),
}
```

**Key insight:** Weighted metrics cannot replace unweighted recall floor - zero-weight entities (EMAIL_ADDRESS, PEDIATRIC_AGE) are invisible in weighted metrics but still matter for HIPAA compliance.

### Pattern 4: Entity-Specific Metric Tracking
**What:** Track TP/FN/FP per entity type for weighted calculation and targeted improvement
**When to use:** When different entity types have different detection performance and importance
**Example:**
```python
# Source: tests/evaluate_presidio.py lines 46-55
@dataclass
class EvaluationMetrics:
    # Per-entity type tracking for weighted calculation
    entity_stats: dict[str, dict[str, int]] = field(default_factory=dict)
    # Example: {"ROOM": {"tp": 86, "fn": 4, "fp": 78}, "PHONE_NUMBER": {"tp": 192, "fn": 0, "fp": 1}}

def weighted_recall(self, weights: dict[str, float]) -> float:
    """Calculate recall weighted by entity importance."""
    weighted_tp = sum(stats["tp"] * weights.get(e, 0.0) for e, stats in self.entity_stats.items())
    weighted_total = sum((stats["tp"] + stats["fn"]) * weights.get(e, 0.0) for e, stats in self.entity_stats.items())
    return weighted_tp / weighted_total if weighted_total > 0 else 0.0
```

**Key insight:** Entity-level stats enable both weighted metrics and targeted debugging of specific PHI types with low recall.

### Anti-Patterns to Avoid
- **Function-scoped expensive fixtures:** Running full validation with bootstrap sampling in function scope causes 10x+ test slowdown
- **Hard-coded metric expectations:** Use JSON baselines with tolerance instead of hard-coded assertions - baselines are version-controlled and updatable
- **Ignoring weighted metrics:** Unweighted recall alone doesn't reflect clinical reality (EMAIL_ADDRESS same weight as PERSON despite never spoken in handoffs)
- **Tight tolerance on bootstrap metrics:** Bootstrap sampling introduces 0.1-0.5% natural variation - 1% tolerance prevents spurious failures
- **Silent baseline updates:** Baseline changes should be explicit commits with justification, not automatic overwrites

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bootstrap confidence intervals | Custom percentile calculation | `numpy.percentile()` with replacement sampling | Already implemented in `evaluate_presidio.py`, statistically validated |
| Test parametrization | Loops in test functions | `pytest.mark.parametrize` | Better test isolation, clearer failure reporting, existing project pattern |
| Baseline comparison | Manual JSON diffing | `pytest.approx()` with rel/abs tolerance | Handles float comparison correctly, clear error messages |
| Module fixtures | Setup/teardown methods | `@pytest.fixture(scope="module")` | Better resource management, explicit dependencies, pytest standard |
| Regression detection | Ad-hoc metric storage | JSON baselines in version control | Simple, auditable, established in Phase 12 |

**Key insight:** Project already has mature patterns established in Phases 12, 16 - Phase 22 should extend rather than replace these patterns.

## Common Pitfalls

### Pitfall 1: Module Fixture State Pollution
**What goes wrong:** One test modifies shared module fixture, breaking subsequent tests
**Why it happens:** Module-scoped fixtures are shared across all tests in module
**How to avoid:**
- Make validation_results fixture read-only (return dict/dataclass, not mutable objects)
- Tests should only read from fixture, never modify
- If test needs to modify, create a deep copy: `import copy; modified = copy.deepcopy(validation_results)`
**Warning signs:**
- Tests pass in isolation but fail when run together
- Test order affects pass/fail results
- Intermittent failures in CI

### Pitfall 2: Baseline Drift Without Documentation
**What goes wrong:** Baselines get updated without recording why metrics changed
**Why it happens:** Quick fix to make tests pass after code changes
**How to avoid:**
- Baseline updates should be separate commits with clear messages
- Include reason in commit message: "Update baseline: Phase 20 phone patterns improved recall 76% → 100%"
- Link to verification report or plan that explains improvement
**Warning signs:**
- Baselines updated in same commit as code changes
- No documentation explaining metric changes
- Unclear whether change is improvement or regression

### Pitfall 3: Ignoring Tolerance on Bootstrap Metrics
**What goes wrong:** Tests fail intermittently due to bootstrap sampling variation
**Why it happens:** Bootstrap percentiles vary slightly between runs (random sampling)
**How to avoid:**
- Always use `pytest.approx(baseline, rel=0.01)` for bootstrap-derived metrics
- 1% tolerance accommodates natural variation while catching real changes
- Never use exact equality (`==`) for floating-point metrics
**Warning signs:**
- Tests fail ~5% of time with "changed from 0.9152 to 0.9143"
- Failures disappear on re-run
- CI shows green/red flapping on same code

### Pitfall 4: Missing Entity-Specific Validation
**What goes wrong:** Overall metrics pass but individual entity types regress
**Why it happens:** Weighted metrics can hide poor performance on low-weight entities
**How to avoid:**
- Test each entity type's recall against its specific target (ROOM ≥55%, PHONE ≥90%, etc.)
- Don't rely solely on overall metrics
- Use entity_stats from validation results to check per-type performance
**Warning signs:**
- Overall recall stays high but specific PHI types start leaking
- Weighted recall masks unweighted recall degradation
- Entity-specific xfail tests start passing unexpectedly

### Pitfall 5: Insufficient Error Context
**What goes wrong:** Test fails with "recall below threshold" but no guidance on what broke
**Why it happens:** Generic assertions without diagnostic information
**How to avoid:**
```python
# BAD
assert recall >= 0.85

# GOOD
assert recall >= 0.85, (
    f"REGRESSION: Recall {recall:.1%} below 85% HIPAA floor. "
    f"Entity breakdown: {entity_stats}. "
    f"False negatives: {fn_count} (up from baseline {baseline_fn})"
)
```
**Warning signs:**
- Need to re-run tests with `-v` to understand failure
- Unclear whether failure is regression or improved detection trade-off
- No guidance on which entity type or pattern caused issue

## Code Examples

Verified patterns from existing codebase:

### Entity-Specific Recall Validation
```python
# Source: Adapted from tests/test_deidentification.py Phase 17/20/21 patterns
# Pattern: Test each entity type's recall against phase-specific target

@pytest.fixture(scope="module")
def validation_results():
    """Run validation once for entire module."""
    return run_validation(
        input_path=Path("tests/synthetic_handoffs.json"),
        n_bootstrap=1000,
        verbose=False,
    )

def test_room_recall_target(validation_results):
    """ROOM recall should meet Phase 17 interim target of 55%."""
    entity_stats = validation_results["metrics"]["entity_stats"]

    if "ROOM" not in entity_stats:
        pytest.skip("No ROOM entities in validation dataset")

    room_stats = entity_stats["ROOM"]
    tp = room_stats["tp"]
    fn = room_stats["fn"]
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    assert recall >= 0.55, (
        f"ROOM recall {recall:.1%} below 55% interim target. "
        f"TP={tp}, FN={fn}. Phase 17 achieved 95.6% - investigate regression."
    )

def test_phone_recall_target(validation_results):
    """PHONE_NUMBER recall should meet Phase 20 target of 90%."""
    entity_stats = validation_results["metrics"]["entity_stats"]

    phone_stats = entity_stats.get("PHONE_NUMBER", {})
    tp = phone_stats.get("tp", 0)
    fn = phone_stats.get("fn", 0)
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    assert recall >= 0.90, (
        f"PHONE_NUMBER recall {recall:.1%} below 90% target. "
        f"TP={tp}, FN={fn}. Phase 20 achieved 100% - check PhoneRecognizer config."
    )

def test_location_recall_documented_limit(validation_results):
    """LOCATION recall has documented pattern-based approach limit."""
    entity_stats = validation_results["metrics"]["entity_stats"]

    location_stats = entity_stats.get("LOCATION", {})
    tp = location_stats.get("tp", 0)
    fn = location_stats.get("fn", 0)
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    # Phase 21 documented: pattern-based approach achieves 44.2%, target was 60%
    # 17 patterns added (+24pp improvement), further requires geographic NER
    assert recall >= 0.40, (
        f"LOCATION recall {recall:.1%} below 40% floor. "
        f"Pattern-based limit documented at 44.2% in Phase 21. "
        f"TP={tp}, FN={fn}, FP={location_stats.get('fp', 0)}"
    )
```

### Milestone Validation Report Generation
```python
# Source: Adapted from tests/run_validation.py generate_compliance_report pattern
# Pattern: Generate comprehensive markdown report with all metrics

def generate_phase22_report(validation_results: dict, output_path: Path) -> None:
    """Generate Phase 22 milestone validation report.

    Confirms all Phase 17-21 recall targets and overall milestone success.
    """
    metrics = validation_results["metrics"]
    entity_stats = metrics["entity_stats"]

    # Calculate entity-specific recalls
    entity_recalls = {}
    for entity_type, stats in entity_stats.items():
        tp, fn = stats["tp"], stats["fn"]
        entity_recalls[entity_type] = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    lines = [
        "# Phase 22: Validation & Recall Targets - Milestone Report",
        "",
        f"**Validation Date:** {validation_results['metadata']['validation_date']}",
        f"**Dataset:** {validation_results['metadata']['n_handoffs']} handoffs",
        "",
        "## Executive Summary",
        "",
        "v2.3 Recall Improvements milestone validation complete.",
        "",
        "| Metric Type | Recall | Precision | F2 Score |",
        "|-------------|--------|-----------|----------|",
        f"| Unweighted (HIPAA floor) | {metrics['recall']:.1%} | {metrics['precision']:.1%} | {metrics['f2']:.1%} |",
        f"| Frequency-weighted | {metrics['freq_weighted_recall']:.1%} | {metrics['freq_weighted_precision']:.1%} | {metrics['freq_weighted_f2']:.1%} |",
        f"| Risk-weighted | {metrics['risk_weighted_recall']:.1%} | {metrics['risk_weighted_precision']:.1%} | {metrics['risk_weighted_f2']:.1%} |",
        "",
        "## Entity-Specific Recall Targets",
        "",
        "| Entity | Phase | Target | Achieved | Status |",
        "|--------|-------|--------|----------|--------|",
        f"| ROOM | 17 | ≥55% | {entity_recalls.get('ROOM', 0):.1%} | {'✓ PASS' if entity_recalls.get('ROOM', 0) >= 0.55 else '✗ FAIL'} |",
        f"| PHONE_NUMBER | 20 | ≥90% | {entity_recalls.get('PHONE_NUMBER', 0):.1%} | {'✓ PASS' if entity_recalls.get('PHONE_NUMBER', 0) >= 0.90 else '✗ FAIL'} |",
        f"| LOCATION | 21 | ≥60% (revised 40%) | {entity_recalls.get('LOCATION', 0):.1%} | {'✓ PASS (revised)' if entity_recalls.get('LOCATION', 0) >= 0.40 else '✗ FAIL'} |",
        f"| MEDICAL_RECORD_NUMBER | - | ≥85% | {entity_recalls.get('MEDICAL_RECORD_NUMBER', 0):.1%} | {'✓ PASS' if entity_recalls.get('MEDICAL_RECORD_NUMBER', 0) >= 0.85 else '✗ FAIL'} |",
        "",
        "## Pattern-Based Approach Limits",
        "",
        "Documented decisions on entity-specific recall ceilings:",
        "",
        "- **LOCATION:** Pattern-based approach achieves 44.2% (Phase 21)",
        "  - spaCy NER baseline: 20%",
        "  - 17 custom patterns: +24.2pp improvement",
        "  - Limit: Geographic names without context require NER/gazetteers",
        "  - Decision: Accept 44.2% as pattern-based ceiling, defer geographic NER to future work",
        "",
    ]

    output_path.write_text("\n".join(lines))
```

### Comprehensive Threshold Enforcement
```python
# Source: Pattern combining test_regression.py baseline comparison with entity-specific targets
# Pattern: Both regression detection AND target validation

class TestPhase22Validation:
    """Phase 22: End-to-end validation with all recall targets."""

    @pytest.fixture(scope="class")
    def validation_results(self):
        """Run validation once for entire test class."""
        return run_validation(
            input_path=Path("tests/synthetic_handoffs.json"),
            n_bootstrap=1000,
            verbose=False,
        )

    def test_no_regression_from_baseline(self, validation_results):
        """No metrics regressed from established baseline."""
        baseline_path = Path("tests/baselines/regression.json")

        if not baseline_path.exists():
            pytest.skip("Baseline not established")

        with open(baseline_path) as f:
            baseline = json.load(f)

        metrics = validation_results["metrics"]

        # Check all 9 metrics for regression
        for metric_name in ["recall", "precision", "f2",
                           "freq_weighted_recall", "freq_weighted_precision", "freq_weighted_f2",
                           "risk_weighted_recall", "risk_weighted_precision", "risk_weighted_f2"]:
            if metric_name not in baseline:
                continue

            baseline_value = baseline[metric_name]
            current_value = metrics[metric_name]

            assert current_value == pytest.approx(baseline_value, rel=0.01), (
                f"REGRESSION: {metric_name} changed {baseline_value:.4f} → {current_value:.4f}"
            )

    def test_all_entity_targets_met(self, validation_results):
        """All Phase 17-21 entity-specific recall targets met."""
        entity_stats = validation_results["metrics"]["entity_stats"]

        # Define targets from Phase 17-21 success criteria
        targets = {
            "ROOM": 0.55,                    # Phase 17 interim target (achieved 95.6%)
            "PHONE_NUMBER": 0.90,            # Phase 20 target (achieved 100%)
            "LOCATION": 0.40,                # Phase 21 revised floor (pattern limit 44.2%)
            "MEDICAL_RECORD_NUMBER": 0.85,   # Phase 22 target
        }

        failures = []
        for entity_type, target in targets.items():
            stats = entity_stats.get(entity_type, {"tp": 0, "fn": 0})
            tp, fn = stats["tp"], stats["fn"]
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

            if recall < target:
                failures.append(f"{entity_type}: {recall:.1%} < {target:.0%} (TP={tp}, FN={fn})")

        assert not failures, (
            f"Entity recall targets not met:\n" + "\n".join(f"  - {f}" for f in failures)
        )

    def test_weighted_recall_improvement_documented(self, validation_results):
        """Overall weighted recall improvement from v2.2 documented."""
        metrics = validation_results["metrics"]

        # v2.2 baseline (from Phase 16 completion)
        baseline_freq_recall = 0.9737  # From regression.json
        baseline_risk_recall = 0.9137

        current_freq = metrics["freq_weighted_recall"]
        current_risk = metrics["risk_weighted_recall"]

        # Document improvement (or stability if already high)
        freq_delta = current_freq - baseline_freq_recall
        risk_delta = current_risk - baseline_risk_recall

        # Assert no regression (allow 1% tolerance for bootstrap variation)
        assert current_freq >= baseline_freq_recall - 0.01, (
            f"Frequency-weighted recall regressed: {baseline_freq_recall:.1%} → {current_freq:.1%}"
        )
        assert current_risk >= baseline_risk_recall - 0.01, (
            f"Risk-weighted recall regressed: {baseline_risk_recall:.1%} → {current_risk:.1%}"
        )

        # Log improvement if significant
        if abs(freq_delta) > 0.01 or abs(risk_delta) > 0.01:
            print(f"\nWeighted recall changes:")
            print(f"  Frequency: {baseline_freq_recall:.1%} → {current_freq:.1%} ({freq_delta:+.1%})")
            print(f"  Risk: {baseline_risk_recall:.1%} → {current_risk:.1%} ({risk_delta:+.1%})")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Function-scoped validation | Module-scoped fixtures | Phase 16 | 10-100x test speedup, established pattern |
| pytest-regressions plugin | JSON baselines | Phase 12 | Simpler dependencies, easier to understand |
| Single unweighted metric | Three-metric framework | Phase 14 | Frequency/risk lenses + HIPAA floor |
| Manual metric tracking | Entity-level stats dict | Phase 7 | Enables weighted metrics and targeted debugging |
| Hard-coded thresholds | JSON baseline with tolerance | Phase 12 | Version-controlled, clear update process |

**Deprecated/outdated:**
- **pytest-regressions:** Replaced with simple JSON baselines in Phase 12 (decision: fewer dependencies, easier maintenance)
- **Function-scoped expensive fixtures:** Replaced with module scope in Phase 16 (10x speedup for integration tests)
- **Global phi_score_threshold:** Replaced with per-entity thresholds dict in Phase 2 (entity-specific calibration)

## Open Questions

Things that couldn't be fully resolved:

1. **Should Phase 22 create new baseline or just validate against existing?**
   - What we know: `tests/baselines/regression.json` exists with 9 metrics from v2.2
   - What's unclear: Whether Phase 22 should update baseline to reflect v2.3 improvements or keep v2.2 as regression floor
   - Recommendation: Keep existing baseline for regression detection, add separate `phase22_targets.json` with entity-specific targets

2. **How to handle entity types with zero occurrences in validation dataset?**
   - What we know: Some entity types (EMAIL_ADDRESS, PROVIDER_NAME) may have zero or few instances
   - What's unclear: Should tests skip, assume 100%, or require minimum dataset coverage?
   - Recommendation: Use `pytest.skip()` if entity count < 5, add dataset coverage validation test

3. **Should weighted metrics have threshold enforcement or just documentation?**
   - What we know: Weighted recall is 97.4% (freq) / 91.4% (risk) as of v2.2
   - What's unclear: Whether to enforce minimums or just track trends
   - Recommendation: Document trends, don't enforce - weighted metrics complement unweighted floor but shouldn't gate deployment

## Sources

### Primary (HIGH confidence)
- [pytest-regressions documentation](https://pytest-regressions.readthedocs.io/en/latest/overview.html) - Baseline regression testing patterns
- [Pytest fixture scope guide](https://pytest-with-eric.com/fixtures/pytest-fixture-scope/) - Module vs function scope trade-offs
- [Better Stack pytest fixtures guide](https://betterstack.com/community/guides/testing/pytest-fixtures-guide/) - Fixture best practices
- Codebase analysis: `tests/integration/test_full_evaluation.py`, `test_regression.py`, `run_validation.py`, `evaluate_presidio.py`
- Project STATE.md and ROADMAP.md - Established patterns and Phase 17-21 results

### Secondary (MEDIUM confidence)
- [Test metrics and thresholds guide](https://testsigma.com/blog/metrics-for-testing/) - Software testing KPIs and threshold enforcement
- [ML model validation metrics](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall) - Precision/recall trade-offs
- [Pytest best practices 2026](https://pytest-with-eric.com/pytest-best-practices/pytest-organize-tests/) - Test organization patterns

### Tertiary (LOW confidence)
- None - all findings verified with official docs or project codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Established in project codebase (pytest, numpy already used)
- Architecture: HIGH - Patterns verified in existing integration tests (Phases 12, 16)
- Pitfalls: HIGH - Based on actual project patterns and pytest documentation

**Research date:** 2026-01-31
**Valid until:** 30 days (stable testing patterns, minimal churn expected)
