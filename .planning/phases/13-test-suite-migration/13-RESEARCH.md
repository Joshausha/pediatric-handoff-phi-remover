# Phase 13: Test Suite Migration - Research

**Researched:** 2026-01-29
**Domain:** Python testing (pytest), float-weighted metrics validation
**Confidence:** HIGH

## Summary

Phase 13 migrates existing test suite from integer weights to float weights and adds complete test coverage for the dual-weight recall framework (frequency-weighted and risk-weighted metrics). The existing `test_weighted_metrics.py` suite already has 8/11 tests passing with correct calculation logic—3 tests fail only because they assert integer types and old weight values. The risk-weighted methods (recall, precision, F2) are thin wrappers that delegate to the existing weighted calculation methods, requiring minimal additional test coverage.

**Current test performance:** 0.16 seconds for 11 tests (well under 5-second target)

**Primary recommendation:** Fix the 3 failing tests by converting assertions to use `pytest.approx()` with float tolerance and updating expected weight values, then add focused test cases for divergence validation between frequency and risk weights. This is test migration, not new functionality—implementation already exists and works.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 7.4.4+ | Test framework | Industry standard Python testing, already in use |
| pytest.approx() | built-in | Float comparison | Built into pytest, designed specifically for floating-point assertions |
| numpy | 1.21+ | Binary arrays for CI | Already used for bootstrap CI calculations in evaluate_presidio.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-benchmark | 4.0+ | Performance regression tests | Optional: if 5-second target becomes concern |
| pytest-xdist | 3.5+ | Parallel test execution | Optional: only if test suite grows significantly |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest.approx() | math.isclose() | pytest.approx() integrates better with pytest assertions and supports collections |
| numpy arrays | pure Python lists | numpy already a dependency, provides cleaner CI calculation |

**Installation:**
```bash
# Already installed (no new dependencies needed)
pytest>=7.4.4
numpy>=1.21.0
```

## Architecture Patterns

### Recommended Test Structure
```
tests/
├── test_weighted_metrics.py    # Float weight tests, divergence validation
├── evaluate_presidio.py         # Contains EvaluationMetrics class with calculations
└── conftest.py                  # Shared fixtures (if needed)
```

### Pattern 1: Float Assertions with Tolerance
**What:** Use `pytest.approx()` for all float comparisons
**When to use:** Any test that compares weighted metric calculations (recall, precision, F2)

**Example:**
```python
# Source: https://pytest-with-eric.com/pytest-advanced/pytest-approx/
def test_weighted_recall_calculation(self):
    """Test weighted recall calculation with float tolerance."""
    entity_stats = {
        "PERSON": {"tp": 100, "fn": 10, "fp": 20},
        "ROOM": {"tp": 50, "fn": 25, "fp": 10},
    }

    weights = {
        "PERSON": 5.0,
        "ROOM": 4.0,
    }

    metrics = EvaluationMetrics()
    metrics.entity_stats = entity_stats

    weighted_recall = metrics.weighted_recall(weights)

    # Manual calculation for verification
    # PERSON: tp=100*5=500, total=110*5=550
    # ROOM: tp=50*4=200, total=75*4=300
    # weighted_recall = (500+200)/(550+300) = 700/850 = 0.823529...
    expected_recall = 700 / 850

    # Use pytest.approx() with default 1e-6 relative tolerance
    assert weighted_recall == pytest.approx(expected_recall)
```

### Pattern 2: Divergence Validation Tests
**What:** Create test cases where frequency and risk weights deliberately differ
**When to use:** Validate that both weight schemes calculate independently and correctly

**Example:**
```python
def test_frequency_vs_risk_weight_divergence(self):
    """Test that frequency and risk weights can produce different results."""
    # Scenario: MRN has low frequency (0.5) but high risk (5.0)
    entity_stats = {
        "MEDICAL_RECORD_NUMBER": {"tp": 50, "fn": 50, "fp": 10},  # 50% recall
        "PERSON": {"tp": 100, "fn": 5, "fp": 15},                 # 95% recall
    }

    freq_weights = {
        "MEDICAL_RECORD_NUMBER": 0.5,  # Rarely spoken
        "PERSON": 5.0,                 # Always spoken
    }

    risk_weights = {
        "MEDICAL_RECORD_NUMBER": 5.0,  # Critical if leaked
        "PERSON": 5.0,                 # Critical if leaked
    }

    metrics = EvaluationMetrics()
    metrics.entity_stats = entity_stats

    freq_recall = metrics.weighted_recall(freq_weights)
    risk_recall = metrics.risk_weighted_recall(risk_weights)

    # Frequency-weighted should be higher (dominated by high-performing PERSON)
    # Risk-weighted should be lower (MRN has equal weight and drags down average)
    assert freq_recall > risk_recall

    # Verify calculations independently
    # Frequency: (50*0.5 + 100*5.0) / (100*0.5 + 105*5.0) = 525 / 575 = 0.913
    # Risk:      (50*5.0 + 100*5.0) / (100*5.0 + 105*5.0) = 750 / 1025 = 0.732
    assert freq_recall == pytest.approx(525 / 575)
    assert risk_recall == pytest.approx(750 / 1025)
```

### Pattern 3: Zero-Weight Safety Tests
**What:** Ensure zero-weight entities (EMAIL_ADDRESS, PEDIATRIC_AGE) don't disappear from reports
**When to use:** Test HIPAA safety guarantee that unweighted recall remains visible

**Example:**
```python
def test_zero_weight_entities_visible_in_unweighted_recall(self):
    """Test that zero-weight entities still count in unweighted recall (safety floor)."""
    entity_stats = {
        "PERSON": {"tp": 100, "fn": 0, "fp": 10},       # 100% recall, weight 5.0
        "EMAIL_ADDRESS": {"tp": 0, "fn": 50, "fp": 0},  # 0% recall, weight 0.0
    }

    weights = {
        "PERSON": 5.0,
        "EMAIL_ADDRESS": 0.0,
    }

    metrics = EvaluationMetrics()
    metrics.entity_stats = entity_stats

    # Unweighted recall includes EMAIL_ADDRESS failures
    unweighted_recall = metrics.recall
    assert unweighted_recall == pytest.approx(100 / 150)  # 66.7%

    # Weighted recall ignores zero-weight EMAIL_ADDRESS
    weighted_recall = metrics.weighted_recall(weights)
    assert weighted_recall == pytest.approx(1.0)  # 100%

    # Safety check: unweighted is visible and lower
    assert unweighted_recall < weighted_recall
```

### Anti-Patterns to Avoid
- **Exact float equality:** `assert 0.823529411764706 == weighted_recall` will fail due to float precision
- **Integer type assertions:** `assert isinstance(weight, int)` fails for float weights (legacy test issue)
- **Testing implementation details:** Don't test that risk_weighted_recall() calls weighted_recall(), test that it produces correct results
- **Over-testing thin wrappers:** risk_weighted_* methods are 1-line delegations—focus tests on calculation correctness, not delegation

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Float comparison | Custom tolerance checks | pytest.approx() | Handles edge cases (inf, nan), supports collections, pytest-integrated |
| Test performance profiling | Manual timing | pytest --durations=10 | Built-in, shows slowest tests immediately |
| Parallel test execution | Threading logic | pytest-xdist | Mature, handles fixtures correctly, automatic CPU detection |
| Bootstrap CI calculations | Custom resampling | Use existing numpy implementation in evaluate_presidio.py | Already tested and working |

**Key insight:** pytest.approx() handles the hard parts of float comparison (relative vs absolute tolerance, special values, collections) that custom code often gets wrong.

## Common Pitfalls

### Pitfall 1: Using Exact Float Equality
**What goes wrong:** Tests fail due to floating-point precision (e.g., 0.8235294117647058 != 0.823529411764706)

**Why it happens:** Division produces IEEE 754 floating-point results with limited precision

**How to avoid:** Always use pytest.approx() for float comparisons
```python
# BAD
assert weighted_recall == 0.823529411764706

# GOOD
assert weighted_recall == pytest.approx(0.823529411764706)
# or even better, calculate expected from same formula
assert weighted_recall == pytest.approx(700 / 850)
```

**Warning signs:** Intermittent test failures on different platforms, test failures after refactoring that didn't change logic

### Pitfall 2: Forgetting to Update Weight Type Assertions
**What goes wrong:** Tests assert `isinstance(weight, int)` when weights are now `float`

**Why it happens:** Tests were written when weights were integers (Phase 8), now migrating to floats (v2.2)

**How to avoid:** Remove type assertions or change to `isinstance(weight, (int, float))`
```python
# BAD (fails for float weights)
assert isinstance(weight, int)

# GOOD (accepts both)
assert isinstance(weight, (int, float))
# or remove type check entirely and just validate range
assert 0.0 <= weight <= 5.0
```

**Warning signs:**
- Current test failures: `test_weight_values_in_valid_range` fails with "PERSON weight is not an integer"
- Tests that check type instead of behavior

### Pitfall 3: Testing Wrong Weight Values
**What goes wrong:** Tests assert outdated weight values (e.g., `GUARDIAN_NAME == 5` when it's now `4.0`)

**Why it happens:** Weights were refined in v2.2 dual-weight framework based on SPOKEN_HANDOFF_ANALYSIS.md

**How to avoid:** Update test assertions to match current config.py values
```python
# BAD (assumes old weights)
assert weights["GUARDIAN_NAME"] == 5
assert weights["LOCATION"] == 0

# GOOD (matches current config.py)
assert weights["GUARDIAN_NAME"] == pytest.approx(4.0)
assert weights["LOCATION"] == pytest.approx(0.5)
```

**Warning signs:**
- Current test failures: `test_critical_entities_have_high_weights` fails "GUARDIAN_NAME should have weight 5"
- Assertion errors showing `4.0 == 5` or `0.5 == 0`

### Pitfall 4: Over-Complicating Risk-Weighted Tests
**What goes wrong:** Writing extensive tests for risk_weighted_recall() when it's a 1-line wrapper

**Why it happens:** Desire for "complete coverage" without recognizing implementation simplicity

**How to avoid:** Focus tests on calculation correctness and divergence validation, not delegation mechanics
```python
# UNNECESSARY (testing delegation, not calculation)
def test_risk_weighted_recall_calls_weighted_recall():
    with mock.patch.object(metrics, 'weighted_recall') as mock_wr:
        metrics.risk_weighted_recall(risk_weights)
        mock_wr.assert_called_once_with(risk_weights)

# BETTER (testing actual behavior)
def test_risk_weighted_recall_calculation():
    """Test risk-weighted recall produces correct results."""
    # Set up test case with known answer
    metrics.entity_stats = {...}
    risk_weights = {...}

    # Verify calculation
    result = metrics.risk_weighted_recall(risk_weights)
    assert result == pytest.approx(expected_value)
```

**Warning signs:** Tests that use mocking for simple delegation, low value from test relative to complexity

### Pitfall 5: Missing Edge Case Coverage
**What goes wrong:** Tests pass for typical cases but fail on edge cases (all zeros, empty stats, unknown entities)

**Why it happens:** Focusing on happy path, not considering boundary conditions

**How to avoid:** Explicitly test edge cases that could cause divide-by-zero or incorrect behavior
```python
def test_weighted_metrics_all_zero_weights(self):
    """Test that all-zero weights return 0.0 (not division by zero)."""
    entity_stats = {
        "EMAIL_ADDRESS": {"tp": 50, "fn": 0, "fp": 0},
        "PEDIATRIC_AGE": {"tp": 60, "fn": 0, "fp": 0},
    }

    weights = {
        "EMAIL_ADDRESS": 0.0,
        "PEDIATRIC_AGE": 0.0,
    }

    metrics = EvaluationMetrics()
    metrics.entity_stats = entity_stats

    # Should return 0.0, not raise ZeroDivisionError
    assert metrics.weighted_recall(weights) == 0.0
    assert metrics.weighted_precision(weights) == 0.0
```

**Warning signs:** Tests that only use "realistic" data, no tests for empty/zero/unknown cases

## Code Examples

Verified patterns from existing codebase and pytest best practices.

### Updating Existing Tests to Float Weights

**Current failing test (test_weighted_metrics.py:223-230):**
```python
# Source: /Users/joshpankin/My Drive/.../test_weighted_metrics.py
def test_weight_values_in_valid_range(self):
    """Test that all weights are non-negative integers."""
    weights = settings.spoken_handoff_weights

    for entity, weight in weights.items():
        assert isinstance(weight, int), f"{entity} weight is not an integer"  # FAILS
        assert weight >= 0, f"{entity} weight is negative"
        assert weight <= 5, f"{entity} weight exceeds maximum of 5"
```

**Fixed version with float support:**
```python
def test_weight_values_in_valid_range(self):
    """Test that all weights are non-negative floats in valid range."""
    weights = settings.spoken_handoff_weights

    for entity, weight in weights.items():
        assert isinstance(weight, (int, float)), f"{entity} weight is not numeric"
        assert weight >= 0.0, f"{entity} weight is negative"
        assert weight <= 5.0, f"{entity} weight exceeds maximum of 5"
```

### Risk-Weighted Calculation Tests

```python
# Source: Based on existing weighted_recall test pattern
class TestRiskWeightedMetrics:
    """Test risk-weighted metrics calculations."""

    def test_risk_weighted_recall_calculation(self):
        """Test risk-weighted recall with HIPAA severity weights."""
        # MRN has highest risk (5.0) but moderate performance
        # PERSON has high risk (5.0) and high performance
        entity_stats = {
            "MEDICAL_RECORD_NUMBER": {"tp": 70, "fn": 30, "fp": 10},  # 70% recall
            "PERSON": {"tp": 95, "fn": 5, "fp": 10},                  # 95% recall
        }

        risk_weights = settings.spoken_handoff_risk_weights

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        risk_recall = metrics.risk_weighted_recall(risk_weights)

        # Manual calculation:
        # MRN: tp=70*5=350, total=100*5=500
        # PERSON: tp=95*5=475, total=100*5=500
        # risk_recall = (350+475)/(500+500) = 825/1000 = 0.825
        expected_recall = 825 / 1000

        assert risk_recall == pytest.approx(expected_recall)

    def test_risk_weighted_precision_calculation(self):
        """Test risk-weighted precision with HIPAA severity weights."""
        entity_stats = {
            "PHONE_NUMBER": {"tp": 80, "fn": 20, "fp": 20},  # 80% precision
            "LOCATION": {"tp": 60, "fn": 40, "fp": 15},      # 80% precision
        }

        risk_weights = {
            "PHONE_NUMBER": 4.0,
            "LOCATION": 4.0,
        }

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        risk_precision = metrics.risk_weighted_precision(risk_weights)

        # PHONE: tp=80*4=320, detected=100*4=400
        # LOCATION: tp=60*4=240, detected=75*4=300
        # precision = (320+240)/(400+300) = 560/700 = 0.8
        expected_precision = 560 / 700

        assert risk_precision == pytest.approx(expected_precision)

    def test_risk_weighted_f2_calculation(self):
        """Test risk-weighted F2 score (recall-weighted)."""
        entity_stats = {
            "GUARDIAN_NAME": {"tp": 85, "fn": 15, "fp": 10},
        }

        risk_weights = {"GUARDIAN_NAME": 4.0}

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        risk_f2 = metrics.risk_weighted_f2(risk_weights)

        # Calculate expected F2
        # precision = 85/95 = 0.894...
        # recall = 85/100 = 0.85
        # F2 = (1 + 4) * (p * r) / (4 * p + r)
        p = 85 / 95
        r = 85 / 100
        beta = 2.0
        expected_f2 = (1 + beta**2) * (p * r) / (beta**2 * p + r)

        assert risk_f2 == pytest.approx(expected_f2)
```

### Frequency vs Risk Divergence Validation

```python
class TestWeightDivergence:
    """Test that frequency and risk weights can diverge appropriately."""

    def test_mrn_low_frequency_high_risk(self):
        """Test MRN: rarely spoken (0.5) but critical if leaked (5.0)."""
        entity_stats = {
            "MEDICAL_RECORD_NUMBER": {"tp": 50, "fn": 50, "fp": 10},  # 50% recall
        }

        freq_weights = settings.spoken_handoff_weights
        risk_weights = settings.spoken_handoff_risk_weights

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        # Both should calculate to 50% recall for single entity
        freq_recall = metrics.weighted_recall(freq_weights)
        risk_recall = metrics.risk_weighted_recall(risk_weights)

        # Single entity: weight magnitude doesn't matter, only relative weight
        # Both should equal 50%
        assert freq_recall == pytest.approx(0.5)
        assert risk_recall == pytest.approx(0.5)

        # But verify different weights were applied
        assert freq_weights["MEDICAL_RECORD_NUMBER"] == pytest.approx(0.5)
        assert risk_weights["MEDICAL_RECORD_NUMBER"] == pytest.approx(5.0)

    def test_mixed_entities_frequency_vs_risk_divergence(self):
        """Test that frequency and risk can produce different metric values."""
        # Setup: MRN performs poorly but has different weights
        #        PERSON performs well and has high weight in both
        entity_stats = {
            "MEDICAL_RECORD_NUMBER": {"tp": 30, "fn": 70, "fp": 5},   # 30% recall
            "PERSON": {"tp": 95, "fn": 5, "fp": 10},                  # 95% recall
        }

        freq_weights = {
            "MEDICAL_RECORD_NUMBER": 0.5,   # Rarely spoken
            "PERSON": 5.0,                  # Always spoken
        }

        risk_weights = {
            "MEDICAL_RECORD_NUMBER": 5.0,   # Critical if leaked
            "PERSON": 5.0,                  # Critical if leaked
        }

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        freq_recall = metrics.weighted_recall(freq_weights)
        risk_recall = metrics.risk_weighted_recall(risk_weights)

        # Frequency-weighted: dominated by high-performing PERSON (weight 5.0)
        # MRN: tp=30*0.5=15, total=100*0.5=50
        # PERSON: tp=95*5=475, total=100*5=500
        # freq = (15+475)/(50+500) = 490/550 = 0.8909...
        assert freq_recall == pytest.approx(490 / 550)

        # Risk-weighted: MRN has equal weight (5.0), drags down average
        # MRN: tp=30*5=150, total=100*5=500
        # PERSON: tp=95*5=475, total=100*5=500
        # risk = (150+475)/(500+500) = 625/1000 = 0.625
        assert risk_recall == pytest.approx(625 / 1000)

        # Verify divergence
        assert freq_recall > risk_recall
        assert abs(freq_recall - risk_recall) > 0.2  # Significant difference

    def test_zero_weight_entities_ignored_in_both_schemes(self):
        """Test that zero-weight entities (EMAIL, PEDIATRIC_AGE) don't affect either metric."""
        entity_stats = {
            "PERSON": {"tp": 90, "fn": 10, "fp": 15},
            "EMAIL_ADDRESS": {"tp": 20, "fn": 5, "fp": 0},      # Weight 0 in freq
            "PEDIATRIC_AGE": {"tp": 30, "fn": 10, "fp": 2},     # Weight 0 in both
        }

        freq_weights = settings.spoken_handoff_weights
        risk_weights = settings.spoken_handoff_risk_weights

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        # Only PERSON should count (both weights 5.0 for PERSON, but 0.0 for PEDIATRIC_AGE)
        # EMAIL has risk weight 4.0, so it counts in risk but not frequency
        freq_recall = metrics.weighted_recall(freq_weights)
        risk_recall = metrics.risk_weighted_recall(risk_weights)

        # Frequency: only PERSON (weight 5.0)
        # recall = 90/100 = 0.9
        assert freq_recall == pytest.approx(0.9)

        # Risk: PERSON (5.0) + EMAIL (4.0), but not PEDIATRIC_AGE (0.0)
        # PERSON: tp=90*5=450, total=100*5=500
        # EMAIL: tp=20*4=80, total=25*4=100
        # risk = (450+80)/(500+100) = 530/600 = 0.883...
        assert risk_recall == pytest.approx(530 / 600)

        # Verify they diverge due to EMAIL inclusion
        assert risk_recall < freq_recall
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Integer weights (1-5) | Float weights (0.0-5.0) | v2.2 (2026-01-28) | Allows fractional weights (0.5 for MRN/LOCATION frequency) |
| Single weight scheme | Dual weights (frequency + risk) | v2.2 (2026-01-28) | Separates "how often spoken" from "severity if leaked" |
| Exact float equality | pytest.approx() tolerance | Pytest best practice (2026) | Prevents flaky tests from float precision |
| Manual calculation tests | Bootstrap CI for metrics | Added Phase 1 | Provides statistical confidence intervals |

**Deprecated/outdated:**
- Integer-only weight assertions: Now `isinstance(weight, (int, float))` or remove type check
- Hardcoded old weight values: GUARDIAN_NAME was 5, now 4.0; LOCATION was 0, now 0.5

## Open Questions

Things that couldn't be fully resolved:

1. **Should risk weights allow values > 5.0?**
   - What we know: Current config.py has max 5.0 for all entities
   - What's unclear: Whether future risk analysis might justify higher severity weights
   - Recommendation: Keep 5.0 max for now, documented in test. Revisit if HIPAA guidance suggests different severity tiers

2. **What tolerance should pytest.approx() use?**
   - What we know: Default 1e-6 relative tolerance works for typical metric calculations
   - What's unclear: Whether edge cases (very small weights) need absolute tolerance
   - Recommendation: Use default pytest.approx() (rel=1e-6, abs=1e-12) unless specific test case requires tighter/looser tolerance

3. **Should we test that risk_weighted_* delegates to weighted_*?**
   - What we know: Implementation is trivial 1-line delegation
   - What's unclear: Whether delegation testing adds value vs clutter
   - Recommendation: No delegation testing—focus on calculation correctness. Delegation is implementation detail, not behavior

## Sources

### Primary (HIGH confidence)
- pytest.approx() documentation: https://docs.pytest.org/en/latest/reference/reference.html
- [Pytest Approx Guide](https://pytest-with-eric.com/pytest-advanced/pytest-approx/) - Comprehensive float comparison best practices
- [Float Comparison in Python](https://dev.to/somacdivad/the-right-way-to-compare-floats-in-python-2fml) - Why exact equality fails
- Existing test_weighted_metrics.py - 8/11 tests passing, calculation logic verified
- Existing evaluate_presidio.py - Implementation of all weighted metric calculations (lines 95-134)

### Secondary (MEDIUM confidence)
- [Pytest Test Organization](https://pytest-with-eric.com/pytest-best-practices/pytest-organize-tests/) - Best practices for test structure
- [Python Testing Guide](https://testomat.io/blog/a-guide-to-the-basics-of-python-testing-how-to-write-unit-tests-and-organize-execution-test-cases/) - Unit test organization patterns
- [Pytest Performance Optimization](https://pytest-with-eric.com/pytest-advanced/pytest-improve-runtime/) - 13 proven optimization techniques
- [scikit-learn Model Evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) - Weighted metrics in ML context

### Tertiary (LOW confidence)
- [Edge Case Testing](https://testomat.io/blog/edge-cases-in-software-development/) - General edge case patterns
- [F2 Score Guide](https://www.datacamp.com/tutorial/f1-score) - Understanding recall-weighted F-beta scores

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pytest.approx() is proven, no new dependencies needed
- Architecture: HIGH - Existing tests demonstrate correct patterns, just need float migration
- Pitfalls: HIGH - Current test failures clearly show exact issues (type assertions, old values, exact equality)
- Edge cases: MEDIUM - Basic edge cases covered (zero weights, empty stats), but haven't explored all float precision edge cases

**Research date:** 2026-01-29
**Valid until:** 60 days (pytest API stable, Python 3.9+ guaranteed until 2025-10-05)

**Key insight:** This is test migration, not new development. Implementation already exists and calculates correctly (8/11 tests pass). The 3 failures are assertion issues (int vs float type, outdated weight values), not calculation bugs. Risk-weighted methods are 1-line wrappers—focus tests on correctness and divergence validation, not implementation details.
