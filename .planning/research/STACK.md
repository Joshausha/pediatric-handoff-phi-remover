# Stack Research: Dual-Weight Recall Framework

**Feature:** Risk-weighted metrics alongside frequency-weighted metrics
**Researched:** 2026-01-29
**Confidence:** HIGH

## Executive Summary

**NO NEW DEPENDENCIES REQUIRED.** The existing stack fully supports dual-weight evaluation metrics. The EvaluationMetrics class already accepts `dict[str, float]` parameters, and Pydantic 2.6.1 natively validates float dictionaries. The only required change is updating config.py weight definitions from `int` to `float`.

## Recommended Stack

### Core (No Changes)

| Component | Current Version | Status | Notes |
|-----------|----------------|--------|-------|
| Python | 3.9+ | ✅ Keep | Native float support |
| numpy | 2.0.2* | ✅ Keep | Percentile calculations for CI |
| pydantic | 2.6.1 | ✅ Keep | Native `dict[str, float]` validation |
| pydantic-settings | 2.1.0 | ✅ Keep | Field() supports float dicts |
| pytest | 7.x | ✅ Keep | Existing test infrastructure |

*Note: requirements.txt specifies `numpy<2.0` but 2.0.2 is installed and working. This discrepancy should be resolved but doesn't block dual-weighting.

### Configuration Changes Only

**Current weight schema:**
```python
spoken_handoff_weights: dict[str, int] = Field(
    default={
        "PERSON": 5,
        "ROOM": 4,
        # ...
    }
)
```

**Required change:**
```python
spoken_handoff_weights: dict[str, float] = Field(
    default={
        "PERSON": 5.0,
        "ROOM": 4.0,
        # ...
    },
    description="Frequency weights: how often each PHI type is spoken"
)

spoken_handoff_risk_weights: dict[str, float] = Field(
    default={
        "MEDICAL_RECORD_NUMBER": 5.0,
        "PERSON": 5.0,
        "PHONE_NUMBER": 4.0,
        # ...
    },
    description="Risk weights: severity if each PHI type leaks"
)
```

## Integration Points

### 1. Evaluation Metrics (ALREADY COMPATIBLE)

**File:** `tests/evaluate_presidio.py`

**Evidence of float support:**
- Line 95: `def weighted_recall(self, weights: dict[str, float]) -> float:`
- Line 105: `def weighted_precision(self, weights: dict[str, float]) -> float:`
- Line 115: `def weighted_f2(self, weights: dict[str, float]) -> float:`
- Lines 124-134: Risk-weighted methods already implemented

**No code changes required** - these methods already accept and process float weights correctly.

### 2. Pydantic Settings (ALREADY COMPATIBLE)

**File:** `app/config.py`

**Validation capability:**
According to [Pydantic's official documentation](https://docs.pydantic.dev/latest/concepts/fields/), Field() with `dict[str, float]` provides automatic validation:
- Validates dictionary structure
- Validates string keys
- Validates numeric values with `__float__()` method
- Supports float constraints via Field parameters

**Implementation:**
```python
# Pydantic automatically validates this schema
spoken_handoff_weights: dict[str, float] = Field(
    default={"PERSON": 5.0},  # Float literals
    description="..."
)
```

No additional validation logic needed.

### 3. Test Infrastructure (ALREADY COMPATIBLE)

**File:** `tests/test_weighted_metrics.py`

**Current test structure:**
- Line 39: `weights = settings.spoken_handoff_weights` (type-agnostic)
- Lines 49-50: Manual calculation using weights (works with int or float)
- Line 54: Numeric comparison with tolerance (float-ready)

**Modification strategy:**
1. Update test assertions to expect float values
2. Add risk-weighted test cases (parallel structure to existing tests)
3. No changes to calculation logic needed

## What NOT to Add

### ❌ scipy.stats
**Why considered:** Advanced statistical distributions
**Why rejected:** Bootstrap CI already implemented with numpy.percentile (lines 171-173 in evaluate_presidio.py). No additional statistical functions needed.

### ❌ pandas
**Why considered:** Data manipulation for weights
**Why rejected:** Simple dict operations sufficient. Adding pandas introduces 20MB+ dependency for features already available in stdlib.

### ❌ typing_extensions
**Why considered:** Enhanced type hints
**Why rejected:** Python 3.9+ native typing supports `dict[str, float]`. No backport needed.

### ❌ pydantic validators
**Why considered:** Custom float range validation
**Why rejected:** Weight ranges (0.0-5.0) can be documented in docstrings. Pydantic's default float validation is sufficient. Over-engineering for 2 config fields.

### ❌ numpy version upgrade
**Current:** requirements.txt says `<2.0`, installed is `2.0.2`
**Recommendation:** Document discrepancy in separate issue, but DON'T change for this milestone. NumPy 2.0 has breaking ABI changes ([NumPy 2.0 migration guide](https://numpy.org/devdocs/numpy_2_0_migration_guide.html)) that could affect presidio-analyzer/spacy compatibility. Current setup works - don't introduce risk.

## Implementation Checklist

- [ ] Change `dict[str, int]` to `dict[str, float]` in config.py (line 315)
- [ ] Update weight values to float literals (5 → 5.0)
- [ ] Add `spoken_handoff_risk_weights` field to Settings class
- [ ] Update test_weighted_metrics.py assertions for float comparison
- [ ] Add risk-weighted test cases (parallel to existing frequency tests)
- [ ] Update evaluate_presidio.py report generation to display both weight schemes
- [ ] Document weight rationale in SPOKEN_HANDOFF_ANALYSIS.md

## Confidence Assessment

| Aspect | Level | Justification |
|--------|-------|---------------|
| No new dependencies | HIGH | Verified existing code uses `dict[str, float]` signatures |
| Pydantic compatibility | HIGH | Official docs confirm Field() validates dict[str, float] |
| NumPy compatibility | MEDIUM | Version discrepancy exists but doesn't block dual-weighting |
| Test compatibility | HIGH | Existing test structure supports float comparisons |

## Sources

**Official Documentation:**
- [Pydantic Fields](https://docs.pydantic.dev/latest/concepts/fields/) - Field validation and types
- [Pydantic Types](https://docs.pydantic.dev/latest/concepts/types/) - Dict and float type validation
- [NumPy 2.0 Migration Guide](https://numpy.org/devdocs/numpy_2_0_migration_guide.html) - Breaking changes reference

**Project Files:**
- `tests/evaluate_presidio.py` - Lines 95-134 show float weight support
- `app/config.py` - Lines 315-344 show current int-based weights
- `tests/test_weighted_metrics.py` - Lines 1-253 show type-agnostic test structure
- `requirements.txt` - Lines 16, 23-24 show numpy/pydantic versions

## Risk Analysis

**LOW RISK** implementation:

1. **Type system risk:** Zero - Python's duck typing means int/float distinction is transparent to calculation logic
2. **Validation risk:** Zero - Pydantic automatically validates dict[str, float]
3. **Calculation risk:** Zero - NumPy operations work identically with int and float
4. **Test risk:** Low - Float comparison requires tolerance (already present in line 54 of test_weighted_metrics.py)
5. **Dependency risk:** Zero - No new dependencies

**Only change:** Configuration schema (int → float) in a single file.
