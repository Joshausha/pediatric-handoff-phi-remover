# Architecture Research: Dual-Weight Recall Framework Integration

**Date:** 2026-01-29
**Confidence:** HIGH
**Context:** v2.2 milestone - adding risk-weighted metrics alongside existing frequency-weighted metrics

## Executive Summary

The dual-weight recall framework integrates cleanly with existing `EvaluationMetrics` architecture. Partial implementation is complete in working tree. The framework adds **risk weights** (severity if leaked) alongside existing **frequency weights** (how often spoken), enabling two complementary views of PHI detection performance.

**Key insight:** Both weight schemes use identical calculation logic—only the weight values differ. This allows code reuse via delegation methods (`risk_weighted_recall` → `weighted_recall` with different weights).

## Current Architecture

### Component Inventory

| Component | Location | Purpose | Current State |
|-----------|----------|---------|---------------|
| **Frequency weights** | `app/config.py:315-329` | How often PHI spoken in handoffs | ✅ Exists (migrated to float) |
| **Risk weights** | `app/config.py:331-344` | Severity if PHI leaks | ✅ Added in working tree |
| **EvaluationMetrics class** | `tests/evaluate_presidio.py:46-205` | Metrics calculation with entity stats | ✅ Exists |
| **weighted_recall/precision/f2** | `tests/evaluate_presidio.py:95-122` | Generic weighted calculation | ✅ Migrated to float |
| **risk_weighted_*** | `tests/evaluate_presidio.py:124-134` | Delegation wrappers | ✅ Added in working tree |
| **Report generation** | `tests/evaluate_presidio.py:434-569` | Text report with metrics | ⚠️ Partially updated |
| **Test suite** | `tests/test_weighted_metrics.py` | Unit tests for calculations | ⚠️ Partially updated |

### Data Flow

```
Dataset (ground truth)
    ↓
PresidioEvaluator.evaluate_dataset()
    ↓
Per-handoff evaluation → entity_stats aggregation
    ↓
EvaluationMetrics object
    ├→ weighted_recall(frequency_weights)    ← Existing
    ├→ weighted_precision(frequency_weights)
    ├→ weighted_f2(frequency_weights)
    ├→ risk_weighted_recall(risk_weights)    ← NEW (delegates)
    ├→ risk_weighted_precision(risk_weights) ← NEW (delegates)
    └→ risk_weighted_f2(risk_weights)        ← NEW (delegates)
    ↓
Report generation (both metrics displayed)
    ↓
Output (console or file)
```

### Weight Calculation Logic

**Generic formula (applies to both schemes):**

```python
# For recall
weighted_tp = Σ(tp[entity] × weight[entity])
weighted_total = Σ((tp[entity] + fn[entity]) × weight[entity])
weighted_recall = weighted_tp / weighted_total

# For precision
weighted_detected = Σ((tp[entity] + fp[entity]) × weight[entity])
weighted_precision = weighted_tp / weighted_detected

# For F2
beta = 2.0
weighted_f2 = (1 + beta²) × (P × R) / (beta² × P + R)
```

**Frequency weights example:**
- `PERSON: 5.0` - Spoken constantly (every handoff)
- `ROOM: 4.0` - Spoken constantly (primary ID)
- `PHONE_NUMBER: 1.0` - Rarely spoken
- `EMAIL_ADDRESS: 0.0` - Never spoken

**Risk weights example:**
- `MEDICAL_RECORD_NUMBER: 5.0` - THE unique identifier
- `PERSON: 5.0` - Directly identifies patient
- `ROOM: 2.0` - Semi-identifying (hospital context only)
- `DATE_TIME: 1.0` - Rarely uniquely identifying

## Integration Points

### 1. Configuration Layer (`app/config.py`)

**Status:** ✅ Complete

**Changes made:**
- Migrated `spoken_handoff_weights` from `dict[str, int]` → `dict[str, float]`
- Added `spoken_handoff_risk_weights: dict[str, float]`
- Updated docstrings to clarify frequency vs risk
- Updated weight values (refined from integer scale to float)

**Integration notes:**
- Both weight dicts live in same config section (lines 303-344)
- Same entity keys across both dicts (9 entity types)
- Pydantic validation ensures type safety (float values)
- Environment variable overrides work for both dicts

### 2. Metrics Calculation (`tests/evaluate_presidio.py`)

**Status:** ⚠️ Core methods complete, report generation partial

**Changes made:**
- Migrated existing methods to accept `dict[str, float]` (was `dict[str, int]`)
- Added delegation wrappers (lines 124-134):
  - `risk_weighted_recall()` → calls `weighted_recall(risk_weights)`
  - `risk_weighted_precision()` → calls `weighted_precision(risk_weights)`
  - `risk_weighted_f2()` → calls `weighted_f2(risk_weights)`
- Updated `generate_report()` to show both metrics (lines 484-515)

**Remaining work:**
- Report shows "FREQUENCY-WEIGHTED" and "RISK-WEIGHTED" sections
- Weight table shows both frequency and risk columns
- Metric summary explains all three views (unweighted, frequency, risk)

**Design rationale:**
- **Why delegation?** Code reuse—identical calculation logic, different weights
- **Why not inheritance?** Single class avoids abstraction overhead
- **Why float migration?** Risk weights need granularity (0.5 for low-risk entities)

### 3. Test Suite (`tests/test_weighted_metrics.py`)

**Status:** ⚠️ Partially updated

**Changes made:**
- Test methods updated for float weights (lines 68-70, 94, 120-121)
- Assertions still use integer logic (no tolerance for float comparison)

**Remaining work:**
- Add `TestRiskWeightedMetrics` class (parallel to existing `TestWeightedMetrics`)
- Test risk weight calculation correctness
- Test frequency vs risk divergence scenarios
- Update weight config tests for float type and dual schemes

**Integration notes:**
- Existing test structure reusable (same calculation patterns)
- Need separate test class to distinguish frequency vs risk behavior
- Weight fixture can load both from settings

### 4. Report Generation (`tests/evaluate_presidio.py:434-569`)

**Status:** ⚠️ Structure added, needs refinement

**Changes integrated:**
- Two separate metric sections (frequency-weighted, risk-weighted)
- Weight table shows both columns side-by-side
- Metric summary explains all three views

**Remaining work:**
- Verify table alignment (lines 509-515)
- Add contextual explanations (what each metric measures)
- Consider adding delta columns (risk - frequency difference)

## New Components

**None required.** The dual-weight framework uses existing architecture with:
- Configuration layer (weights as Pydantic fields)
- Calculation layer (delegation methods)
- Reporting layer (enhanced text generation)

**Why no new components?**
- Risk weights follow identical calculation pattern as frequency weights
- Delegation methods avoid duplication
- Report generation already parameterized for metrics display

## Suggested Build Order

Based on existing partial implementation and dependency flow:

### Phase 1: Complete Test Suite Migration ⚠️ PRIORITY
**File:** `tests/test_weighted_metrics.py`

**Tasks:**
1. Update `TestWeightConfiguration.test_weight_values_in_valid_range()` - remove integer assertion, allow floats
2. Update `TestWeightConfiguration.test_critical_entities_have_high_weights()` - adjust for new frequency values
3. Add `TestRiskWeightConfiguration` class:
   - `test_risk_weights_loaded_from_config()`
   - `test_risk_weight_values_in_valid_range()` (floats, 0-5 range)
   - `test_critical_identifiers_have_high_risk()` (MRN, PERSON = 5.0)
   - `test_low_identifying_entities_have_low_risk()` (DATE_TIME = 1.0, ROOM = 2.0)
4. Add `TestRiskWeightedMetrics` class:
   - `test_risk_weighted_recall_calculation()` - verify against manual calculation
   - `test_risk_weighted_precision_calculation()`
   - `test_risk_weighted_f2_calculation()`
   - `test_risk_vs_frequency_divergence()` - scenario where risk > frequency (MRN) or frequency > risk (ROOM)

**Verification:** `pytest tests/test_weighted_metrics.py -v` (21+ tests passing)

**Why first?** Tests validate calculation correctness before report changes. Failing tests block merge.

### Phase 2: Finalize Report Generation ⚠️ CRITICAL PATH
**File:** `tests/evaluate_presidio.py`

**Tasks:**
1. Verify weight table formatting (lines 509-515):
   - Ensure column alignment with variable-length entity names
   - Test with actual dataset output (not just inspection)
2. Add contextual explanations to each section:
   - Frequency-weighted: "Reflects how often each PHI type is spoken during I-PASS handoffs"
   - Risk-weighted: "Reflects severity of privacy breach if each PHI type leaks"
   - Metric summary: Brief interpretation guidance
3. Consider adding delta analysis:
   - For each entity, show `risk_weight - freq_weight`
   - Positive = more identifying than frequent (MRN, PHONE)
   - Negative = more frequent than identifying (ROOM)

**Verification:** `python tests/evaluate_presidio.py --weighted` (report renders correctly)

**Why second?** Report display depends on metrics being correct (validated in Phase 1).

### Phase 3: Documentation Updates 📄
**Files:**
- `docs/SPOKEN_HANDOFF_ANALYSIS.md` (update with risk weights)
- `.planning/phases/08-weighted-recall-evaluation/08-VERIFICATION.md` (add dual-weight section)

**Tasks:**
1. Update `SPOKEN_HANDOFF_ANALYSIS.md`:
   - Add "Dual-Weighting Framework" section
   - Document risk weight rationale (why MRN=5.0, why ROOM=2.0)
   - Add table comparing frequency vs risk for each entity
   - Update methodology section
2. Update `08-VERIFICATION.md`:
   - Add risk-weighted metrics to success criteria
   - Document expected ranges (risk recall likely lower than frequency)
   - Add regression test baselines

**Verification:** Documentation review (no automated check)

**Why third?** Tests and code must work before documenting results.

### Phase 4: Integration Validation 🧪
**New file:** `tests/test_dual_weighting_integration.py`

**Tasks:**
1. Create integration test that:
   - Loads actual synthetic dataset
   - Runs full evaluation with both metrics
   - Asserts frequency recall > risk recall (expected pattern)
   - Asserts both metrics present in report output
2. Add regression baseline:
   - Capture current frequency-weighted recall (91.5%)
   - Capture risk-weighted recall (expected ~85-88%)
   - Flag if either drops significantly

**Verification:** `pytest tests/test_dual_weighting_integration.py -v`

**Why fourth?** Integration test validates end-to-end behavior after unit tests pass.

## Data Flow Changes

**Before (single weighting):**
```
evaluate_dataset() → EvaluationMetrics
    ↓
weighted_recall(frequency_weights)
    ↓
Report shows: unweighted + frequency-weighted
```

**After (dual weighting):**
```
evaluate_dataset() → EvaluationMetrics (unchanged)
    ↓
weighted_recall(frequency_weights)        ← Existing path
risk_weighted_recall(risk_weights)        ← New path (same logic)
    ↓
Report shows: unweighted + frequency-weighted + risk-weighted
```

**Key insight:** No changes to data collection (`evaluate_dataset`), only to metric calculation and display.

## Architecture Strengths

1. **Code reuse via delegation** - `risk_weighted_*` methods delegate to `weighted_*` with different weights
2. **Type safety** - Pydantic ensures float weights, config validation
3. **Backward compatibility** - Existing frequency-weighted code path unchanged
4. **Testability** - Unit tests can mock weights independently
5. **Configuration-driven** - Both weight schemes in config, no hardcoded values

## Architecture Concerns

1. **Float comparison in tests** - Need tolerance checks (not exact equality)
2. **Report verbosity** - Three metric views may overwhelm users (consider summary view)
3. **Weight maintenance** - Two dicts must stay in sync (same entity keys)
4. **Interpretation guidance** - Users need help understanding which metric matters when

**Mitigations:**
- Use `abs(actual - expected) < 0.001` in tests
- Add "Metric Summary" section with interpretation guidance
- Pydantic validation can enforce entity key consistency (future enhancement)
- Document metric use cases in `SPOKEN_HANDOFF_ANALYSIS.md`

## Build Order Rationale

**Why test suite first?**
- Blocks merge if calculations wrong
- Fast feedback loop (seconds to run)
- Validates core logic before UI changes

**Why report generation second?**
- User-facing changes require correct calculations
- Visual inspection needed (automated testing limited)
- Iterative refinement expected

**Why documentation third?**
- Documents actual behavior (not planned behavior)
- Risk weights may be adjusted based on test results
- Avoids documentation thrash

**Why integration tests last?**
- Requires all components working
- Establishes regression baselines
- Validates end-to-end behavior

## Sources

- **Config implementation**: `app/config.py` lines 303-344 (working tree)
- **Metrics implementation**: `tests/evaluate_presidio.py` lines 95-134, 484-515 (working tree)
- **Test suite**: `tests/test_weighted_metrics.py` (working tree)
- **Original analysis**: `docs/SPOKEN_HANDOFF_ANALYSIS.md` (committed)
- **Existing architecture**: `.planning/codebase/ARCHITECTURE.md` (committed)

**Confidence:** HIGH - Partial implementation exists, architecture proven, calculations reuse existing patterns.
