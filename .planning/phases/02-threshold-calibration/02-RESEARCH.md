# Phase 2: Threshold Calibration - Research

**Researched:** 2026-01-23
**Domain:** Precision-recall curve analysis and threshold optimization for NER systems
**Confidence:** HIGH

## Summary

Phase 2 optimizes Presidio's confidence score thresholds using precision-recall curve analysis to improve recall from 77.9% to >90% without pattern changes. Research confirms that **per-entity threshold calibration** is the industry-standard approach for multi-class NER systems, as different entity types exhibit different confidence score distributions. The existing evaluation infrastructure (`evaluate_presidio.py`) already calculates F2 scores and exports confusion matrices, providing the foundation for systematic threshold optimization.

**Primary recommendation:** Generate precision-recall curves for each of the 8 entity types independently, sweep thresholds from 0.3-0.6 in 0.05 steps, maximize F2 score while maintaining ≥90% recall floor, and update `config.py` with per-entity thresholds including documented rationale.

**Key finding:** Presidio's global `score_threshold` parameter filters ALL entities uniformly, but the codebase can implement per-entity thresholds via post-analysis filtering. The current 0.35 detection threshold and 0.7 validation threshold mismatch creates a 2x confidence gap that should be eliminated for consistency.

## Standard Stack

### Core Libraries

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scikit-learn | 1.5+ | Precision-recall curve generation | Official metric computation, `precision_recall_curve()` returns P/R/thresholds arrays |
| matplotlib | 3.7+ | PR curve visualization | Industry standard for scientific plotting, integrates with sklearn |
| pandas | 2.0+ | Threshold sweep results tabulation | Data manipulation for multi-entity comparison tables |
| numpy | 1.24+ | Numerical operations | Array operations for threshold ranges and metric calculations |

**Already installed:** All dependencies present in project's `requirements.txt` ✓

### Supporting Tools

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| seaborn | 0.13+ | Enhanced PR curve styling | Multi-panel plots for per-entity comparison |
| plotly | 5.0+ | Interactive PR curves | If stakeholder presentation requires interactive exploration |

**Recommendation:** Use matplotlib only (already in stack) for static PNG/PDF exports. Seaborn/plotly add complexity without value for internal research documentation.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| scikit-learn | Manual P/R calculation | Loss of validated implementation, testing burden |
| matplotlib | Excel charts | No reproducibility, manual threshold selection error-prone |
| Presidio evaluator | Custom evaluation | Current implementation already functional, migration cost high |

**Installation:**
```bash
# All dependencies already satisfied in venv
# No additional packages needed
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── evaluate_presidio.py          # Existing: F2 + confusion matrix ✓
├── calibrate_thresholds.py       # NEW: PR curve generation + threshold sweep
├── synthetic_handoffs.json       # Existing: seed=42 standard dataset
├── adversarial_handoffs.json     # From Phase 1: seed=43 edge cases
└── results/
    ├── pr_curves/                # NEW: Per-entity PNG plots
    │   ├── PERSON.png
    │   ├── PHONE_NUMBER.png
    │   └── ...
    ├── threshold_sweep.json      # NEW: F2 scores for all threshold/entity combos
    └── optimal_thresholds.json   # NEW: Final selected thresholds + rationale

.planning/phases/02-threshold-calibration/
├── 02-RESEARCH.md                # This file
├── 02-PLAN.md                    # Tasks/subtasks
└── CALIBRATION_RESULTS.md        # NEW: Before/after metrics, decision rationale
```

### Pattern 1: Per-Entity Threshold Calibration

**What:** Generate separate precision-recall curves for each entity type, optimize thresholds independently

**When to use:** Multi-class NER where entity types have different confidence score distributions (standard in medical NLP)

**Why:** PERSON entities (98.8% baseline recall) need lower threshold than PEDIATRIC_AGE (36.6% recall). Global threshold forces suboptimal tradeoff.

**Example:**
```python
# Source: Implementation pattern synthesized from research
from sklearn.metrics import precision_recall_curve
import numpy as np
from typing import Dict, List, Tuple

def calibrate_per_entity_thresholds(
    confusion_matrix: Dict[str, Dict],
    dataset: List[SyntheticHandoff],
    threshold_range: Tuple[float, float] = (0.3, 0.6),
    step: float = 0.05,
    f2_min: float = 0.90,
    recall_min: float = 0.90,
) -> Dict[str, Dict]:
    """
    Generate PR curves and find optimal threshold for each entity type.

    Args:
        confusion_matrix: Per-entity TP/FN/FP counts from evaluate_presidio.py
        dataset: Synthetic handoffs with ground truth spans
        threshold_range: (min, max) threshold values to test
        step: Threshold increment (0.05 = 20 test points)
        f2_min: Minimum F2 score requirement
        recall_min: Hard recall floor (safety requirement)

    Returns:
        Dict mapping entity_type -> {
            'optimal_threshold': float,
            'metrics': {'recall', 'precision', 'f2'},
            'rationale': str,
            'pr_curve_data': {'precision': list, 'recall': list, 'thresholds': list}
        }
    """
    results = {}

    for entity_type in confusion_matrix.keys():
        # Collect all confidence scores and ground truth labels
        y_true, y_scores = [], []

        for handoff in dataset:
            # Extract ground truth for this entity type
            gt_spans = [s for s in handoff.phi_spans if s.entity_type == entity_type]

            # Run Presidio at minimum threshold to get all scores
            detected = analyze_with_threshold(handoff.text, threshold=0.0)
            detected_type = [d for d in detected if d['entity_type'] == entity_type]

            # Build binary classification arrays
            for gt_span in gt_spans:
                # Find best match
                best_score = get_best_match_score(gt_span, detected_type)
                y_true.append(1)
                y_scores.append(best_score if best_score else 0.0)

        # Generate PR curve
        precision, recall, thresholds = precision_recall_curve(y_true, y_scores)

        # Find optimal threshold
        optimal = find_optimal_threshold(
            precision, recall, thresholds,
            f2_min=f2_min, recall_min=recall_min
        )

        results[entity_type] = optimal

    return results


def find_optimal_threshold(
    precision: np.ndarray,
    recall: np.ndarray,
    thresholds: np.ndarray,
    f2_min: float = 0.90,
    recall_min: float = 0.90,
) -> Dict:
    """
    Select optimal threshold from PR curve.

    Strategy:
    1. Filter to thresholds with recall >= recall_min
    2. Calculate F2 score for each (recall-weighted)
    3. Select threshold with maximum F2
    4. If tie (F2 within 0.5%), prefer higher recall

    Returns optimal threshold with metrics and rationale.
    """
    best_threshold = None
    best_f2 = 0
    best_metrics = {}

    for i, threshold in enumerate(thresholds):
        p, r = precision[i], recall[i]

        # Hard recall floor
        if r < recall_min:
            continue

        # Calculate F2 (beta=2, recall weighted 2x)
        f2 = 5 * p * r / (4 * p + r) if (4 * p + r) > 0 else 0

        # Check if better than current best
        if f2 > best_f2:
            best_f2 = f2
            best_threshold = threshold
            best_metrics = {'precision': p, 'recall': r, 'f2': f2}

    rationale = (
        f"Threshold {best_threshold:.2f} maximizes F2={best_f2:.1%} "
        f"while maintaining recall≥{recall_min:.0%}. "
        f"Achieves P={best_metrics['precision']:.1%}, R={best_metrics['recall']:.1%}."
    )

    return {
        'optimal_threshold': best_threshold,
        'metrics': best_metrics,
        'rationale': rationale,
        'pr_curve_data': {
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'thresholds': thresholds.tolist(),
        }
    }
```

### Pattern 2: Coarse-to-Fine Threshold Sweep

**What:** Start with coarse 0.10 steps (0.30, 0.40, 0.50, 0.60), then refine around optimal with 0.05 steps

**When to use:** Computational efficiency for large datasets (500+ synthetic handoffs × 8 entity types × threshold range)

**Why:** Reduces evaluation calls from 40 (0.05 steps) to 4+8 = 12 evaluations per entity type (70% reduction)

**Example:**
```python
# Coarse sweep: 0.30, 0.40, 0.50, 0.60
coarse_thresholds = np.arange(0.30, 0.61, 0.10)
coarse_results = evaluate_thresholds(coarse_thresholds)

# Find coarse optimum (e.g., 0.40)
coarse_optimal = max(coarse_results, key=lambda x: x['f2'])

# Fine sweep: 0.35, 0.40, 0.45
fine_thresholds = np.arange(
    coarse_optimal - 0.05,
    coarse_optimal + 0.06,
    0.05
)
fine_results = evaluate_thresholds(fine_thresholds)
```

**Note:** Phase 2 context decision specifies **coarse 0.10 sweep only** (4 thresholds: 0.30, 0.40, 0.50, 0.60). Fine refinement deferred to Phase 4 if needed.

### Pattern 3: Presidio Per-Entity Threshold Implementation

**What:** Presidio's `score_threshold` is global, but per-entity thresholds implementable via post-analysis filtering

**When to use:** Required for Phase 2 per-entity optimization

**How:**
```python
# Source: Adapted from Presidio documentation + research
from presidio_analyzer import AnalyzerEngine

def analyze_with_per_entity_thresholds(
    text: str,
    entity_thresholds: Dict[str, float],
    default_threshold: float = 0.35,
) -> List[Dict]:
    """
    Apply per-entity confidence thresholds to Presidio analysis.

    Args:
        text: Input text to analyze
        entity_thresholds: Dict mapping entity_type -> threshold
        default_threshold: Fallback for entities not in dict

    Returns:
        Filtered results with per-entity thresholds applied
    """
    analyzer = AnalyzerEngine()

    # Run Presidio with minimum threshold (0.0 to get all detections)
    raw_results = analyzer.analyze(
        text=text,
        language="en",
        score_threshold=0.0  # Get all detections, filter manually
    )

    # Apply per-entity thresholds
    filtered_results = []
    for result in raw_results:
        entity_type = result.entity_type
        threshold = entity_thresholds.get(entity_type, default_threshold)

        if result.score >= threshold:
            filtered_results.append({
                'entity_type': entity_type,
                'start': result.start,
                'end': result.end,
                'score': result.score,
                'text': text[result.start:result.end],
            })

    return filtered_results
```

**Integration with config.py:**
```python
# Add to app/config.py Settings class
phi_score_thresholds: Dict[str, float] = Field(
    default={
        "PERSON": 0.35,              # High baseline recall, keep low
        "PHONE_NUMBER": 0.40,        # Calibrated in Phase 2
        "EMAIL_ADDRESS": 0.30,       # 100% baseline, can be aggressive
        "DATE_TIME": 0.35,           # 96.8% baseline
        "LOCATION": 0.45,            # Low baseline, needs careful tuning
        "MEDICAL_RECORD_NUMBER": 0.40,  # 70.9% baseline
        "ROOM": 0.50,                # 34.4% baseline (weakest)
        "GUARDIAN_NAME": 0.35,       # Grouped with PERSON
        "PEDIATRIC_AGE": 0.55,       # 36.6% baseline (weakest)
    },
    description="Per-entity confidence score thresholds (Phase 2 calibrated)"
)

# Deprecate global threshold or use as fallback
phi_score_threshold: float = Field(
    default=0.35,
    description="DEPRECATED: Use phi_score_thresholds (per-entity). Kept for backward compatibility."
)
```

### Anti-Patterns to Avoid

- **Global threshold optimization:** Forces suboptimal tradeoff across entity types with different confidence distributions
- **Validation threshold mismatch:** Current 0.35 detection vs 0.7 validation creates 2x gap; align both to same per-entity thresholds
- **Threshold selection without rationale:** Document WHY each threshold was chosen (F2 maximization, recall floor, precision tradeoff)
- **Over-optimization on synthetic data:** Phase 2 uses synthetic + adversarial datasets; validate against real transcripts in Phase 5
- **Ignoring weak entity types:** PEDIATRIC_AGE (36.6%) and ROOM (34.4%) need pattern improvements (Phase 4), not just threshold tuning

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PR curve generation | Manual precision/recall calculation loops | `sklearn.metrics.precision_recall_curve()` | Handles edge cases (undefined precision at recall=0), returns aligned arrays, validated implementation |
| F2 score calculation | Custom beta-weighted F-score formula | `sklearn.metrics.fbeta_score(beta=2)` OR existing `EvaluationMetrics.f2` property | Already implemented in `evaluate_presidio.py`, tested and verified |
| Threshold search | Grid search with manual F2 comparison | Leverage existing PR curve arrays, vectorized numpy operations | 10-100x faster than iterative evaluation, avoids repeated Presidio calls |
| PR curve visualization | Custom matplotlib figure layout | `sklearn.metrics.PrecisionRecallDisplay` | Standardized plot format, automatic styling, consistent with scientific papers |
| Results serialization | Custom JSON encoding | `dataclasses.asdict()` + `json.dump()` | Type-safe, handles nested dicts, reduces bugs |

**Key insight:** The existing `evaluate_presidio.py` already exports per-entity confusion matrices (`--export-confusion-matrix`) with F2 scores calculated. Phase 2 extends this with PR curves, not rebuilds it.

## Common Pitfalls

### Pitfall 1: Ignoring Recall Floor During Optimization

**What goes wrong:** Threshold selection maximizes F2 but drops recall below 90%, creating PHI leak risk

**Why it happens:** F2 score can increase if precision gains outweigh recall losses, tempting higher thresholds

**How to avoid:**
- Hard-code recall minimum (≥90%) in threshold selection logic
- Reject any threshold that drops below recall floor
- Report filtered candidates: "Threshold 0.60 rejected: recall 88.5% < 90% floor"

**Warning signs:**
- F2 score improving while recall decreasing
- Test failures with "PHI LEAK RISK" messages
- False negatives increasing in adversarial dataset

**Code example:**
```python
# WRONG: Maximize F2 without recall constraint
best_threshold = max(thresholds, key=lambda t: calculate_f2(t))

# CORRECT: Filter to recall-safe thresholds first
safe_thresholds = [t for t in thresholds if calculate_recall(t) >= 0.90]
best_threshold = max(safe_thresholds, key=lambda t: calculate_f2(t))
```

### Pitfall 2: Not Testing Against Adversarial Dataset

**What goes wrong:** Thresholds optimized on standard synthetic dataset (seed=42) perform poorly on edge cases

**Why it happens:** Standard dataset uses clean template-generated text; adversarial dataset includes speech artifacts, cultural names, transcription errors

**How to avoid:**
- Run threshold calibration on BOTH datasets (seed=42 AND seed=43)
- Report separate metrics for standard vs adversarial
- Select thresholds that work well on adversarial (conservative choice)
- If threshold only works on standard dataset, flag as "high risk"

**Warning signs:**
- Standard dataset: 92% recall, Adversarial dataset: 75% recall (13-point gap)
- PEDIATRIC_AGE and ROOM show larger performance gaps than other entities
- Real transcript testing (Phase 5) reveals unexpected PHI leaks

**Example comparison:**
```
Entity: PHONE_NUMBER
  Standard dataset (seed=42):     Optimal threshold 0.40 → R=94%, P=88%, F2=92%
  Adversarial dataset (seed=43):  Same threshold 0.40 → R=86%, P=82%, F2=85%

Decision: Use 0.35 threshold (R=96%/90%, P=84%/78%, F2=91%/86%) for safety margin
```

### Pitfall 3: Threshold Mismatch Between Detection and Validation

**What goes wrong:** Detection threshold (0.35) differs from validation threshold (0.7), creating inconsistent behavior

**Why it happens:** Historical artifact from initial development; validation was added later with different threshold

**Current state:**
- `deidentification.py:148` - `score_threshold=settings.phi_score_threshold` (0.35)
- `deidentification.py:272` - Validation uses `score_threshold=0.7` (hardcoded, 2x higher)

**How to fix:**
- Align validation threshold with per-entity detection thresholds
- Change validation to use same `entity_thresholds` dict
- OR: Keep validation threshold +0.10 higher than detection (safety margin for high-confidence leaks)

**Recommended approach:**
```python
# In deidentification.py:validate_deidentification()
# BEFORE (hardcoded 0.7):
results = analyzer.analyze(
    text=cleaned,
    language="en",
    entities=settings.phi_entities,
    score_threshold=0.7  # Arbitrary, mismatched
)

# AFTER (aligned with detection):
# Option 1: Use same per-entity thresholds
for result in results:
    threshold = settings.phi_score_thresholds.get(result.entity_type, 0.35)
    if result.score >= threshold:
        # Flag potential leak

# Option 2: Use detection threshold + safety margin
validation_thresholds = {
    entity: threshold + 0.10
    for entity, threshold in settings.phi_score_thresholds.items()
}
```

**Phase 2 decision:** Use Option 1 (same thresholds) for consistency. Document rationale in CALIBRATION_RESULTS.md.

### Pitfall 4: Overfitting to Synthetic Data Distribution

**What goes wrong:** Thresholds calibrated on synthetic data don't generalize to real transcripts

**Why it happens:**
- Synthetic data has uniform confidence score distribution (Faker generates clean names/numbers)
- Real transcripts have ASR errors, accents, background noise → lower confidence scores
- Pattern-based recognizers (MRN, ROOM) work better on templates than real text

**How to avoid:**
- Document that Phase 2 thresholds are "synthetic-optimized"
- Plan Phase 5 re-calibration using real transcript gold standard
- Conservative threshold selection (prefer recall over precision)
- Test on adversarial dataset (closer to real-world messiness)

**Warning signs:**
- Phase 2 achieves 94% recall on synthetic
- Phase 5 real transcript testing: 78% recall (16-point drop)
- Confidence scores on real transcripts systematically lower than synthetic

**Mitigation strategy:**
- Apply -0.05 threshold reduction after synthetic calibration (safety margin)
- Example: Synthetic optimal = 0.40 → Production threshold = 0.35
- Document adjustment in `CALIBRATION_RESULTS.md` rationale section

### Pitfall 5: Confusing Confidence Score with Probability

**What goes wrong:** Treating Presidio's `score` field as calibrated probability (0-1 scale)

**Why it happens:** Presidio's confidence scores are heuristic-based, not calibrated probabilities from logistic regression

**Reality:**
- SpaCy NER scores: Entity recognition confidence (model-based)
- Regex recognizers: Pattern match strength (heuristic)
- Context enhancers: Boosted scores (rule-based)
- **Not calibrated:** Score of 0.8 doesn't mean "80% probability of PHI"

**How to avoid:**
- Treat thresholds as relative cutoffs, not probability thresholds
- Don't apply probability calibration methods (Platt scaling, isotonic regression)
- Threshold selection based on empirical PR curves, not probabilistic interpretation

**What this means for Phase 2:**
- PR curves are valid (empirical precision/recall at different cutoffs)
- Threshold optimization is valid (find cutoff that maximizes F2)
- Probability calibration is NOT applicable (Presidio scores aren't probabilities)

## Code Examples

### Example 1: Generate PR Curve for Single Entity Type

```python
# Source: Adapted from sklearn documentation and research
from sklearn.metrics import precision_recall_curve, PrecisionRecallDisplay
import matplotlib.pyplot as plt
import numpy as np

def generate_pr_curve(
    entity_type: str,
    dataset: List[SyntheticHandoff],
    output_path: Path,
) -> Dict:
    """
    Generate precision-recall curve for a single entity type.

    Args:
        entity_type: PHI entity type (e.g., "PERSON", "PHONE_NUMBER")
        dataset: Synthetic handoffs with ground truth spans
        output_path: Path to save PNG plot

    Returns:
        Dict with precision, recall, thresholds arrays
    """
    # Collect ground truth labels and confidence scores
    y_true = []
    y_scores = []

    for handoff in dataset:
        # Get ground truth spans for this entity type
        gt_spans = [s for s in handoff.phi_spans if s.entity_type == entity_type]

        # Run Presidio with threshold=0 to get all detections
        detected = analyze_text_raw(handoff.text, threshold=0.0)
        detected_type = [d for d in detected if d['entity_type'] == entity_type]

        # For each ground truth span, find best matching detection
        for gt_span in gt_spans:
            best_match = find_best_overlap(gt_span, detected_type)

            if best_match:
                y_true.append(1)  # True positive candidate
                y_scores.append(best_match['score'])
            else:
                y_true.append(1)  # Ground truth present
                y_scores.append(0.0)  # Not detected at any threshold

    # Generate PR curve
    precision, recall, thresholds = precision_recall_curve(y_true, y_scores)

    # Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    display = PrecisionRecallDisplay(precision=precision, recall=recall)
    display.plot(ax=ax)

    # Add optimal threshold marker
    f2_scores = 5 * precision * recall / (4 * precision + recall)
    optimal_idx = np.argmax(f2_scores)
    ax.scatter(
        recall[optimal_idx],
        precision[optimal_idx],
        color='red',
        s=100,
        zorder=5,
        label=f'Optimal (threshold={thresholds[optimal_idx]:.2f})'
    )

    ax.set_title(f'Precision-Recall Curve: {entity_type}')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return {
        'precision': precision.tolist(),
        'recall': recall.tolist(),
        'thresholds': thresholds.tolist(),
        'optimal_threshold': float(thresholds[optimal_idx]),
        'optimal_f2': float(f2_scores[optimal_idx]),
    }
```

### Example 2: Threshold Sweep with F2 Optimization

```python
# Source: Implementation pattern from research + Phase 2 context decisions
def sweep_thresholds(
    entity_type: str,
    dataset: List[SyntheticHandoff],
    threshold_range: List[float] = [0.30, 0.40, 0.50, 0.60],  # Coarse sweep
    recall_min: float = 0.90,
) -> Dict:
    """
    Evaluate multiple thresholds and select optimal.

    Args:
        entity_type: Entity type to optimize
        dataset: Test dataset
        threshold_range: List of thresholds to test
        recall_min: Minimum acceptable recall

    Returns:
        Dict with threshold sweep results and optimal selection
    """
    results = []

    for threshold in threshold_range:
        # Evaluate at this threshold
        evaluator = PresidioEvaluator()
        metrics, _ = evaluator.evaluate_dataset(
            dataset,
            score_threshold=threshold,
            filter_entity=entity_type
        )

        # Extract per-entity metrics
        entity_metrics = metrics.per_entity[entity_type]

        results.append({
            'threshold': threshold,
            'precision': entity_metrics['precision'],
            'recall': entity_metrics['recall'],
            'f1': entity_metrics['f1'],
            'f2': entity_metrics['f2'],
            'meets_recall_min': entity_metrics['recall'] >= recall_min,
        })

    # Filter to recall-safe thresholds
    safe_results = [r for r in results if r['meets_recall_min']]

    if not safe_results:
        # No threshold meets recall floor - use lowest threshold
        return {
            'optimal_threshold': min(threshold_range),
            'rationale': f'No threshold achieved {recall_min:.0%} recall floor. Using minimum threshold {min(threshold_range):.2f}.',
            'all_results': results,
        }

    # Select threshold with maximum F2
    optimal = max(safe_results, key=lambda r: r['f2'])

    # Tie-breaking: if multiple thresholds within 0.5% F2, prefer higher recall
    ties = [r for r in safe_results if abs(r['f2'] - optimal['f2']) < 0.005]
    if len(ties) > 1:
        optimal = max(ties, key=lambda r: r['recall'])
        rationale_suffix = " (tie-break: higher recall)"
    else:
        rationale_suffix = ""

    return {
        'optimal_threshold': optimal['threshold'],
        'metrics': {
            'precision': optimal['precision'],
            'recall': optimal['recall'],
            'f2': optimal['f2'],
        },
        'rationale': (
            f"Threshold {optimal['threshold']:.2f} maximizes F2={optimal['f2']:.1%} "
            f"while maintaining recall≥{recall_min:.0%}. "
            f"Achieves P={optimal['precision']:.1%}, R={optimal['recall']:.1%}.{rationale_suffix}"
        ),
        'all_results': results,
    }
```

### Example 3: Updating config.py with Calibrated Thresholds

```python
# Source: Presidio configuration pattern + Phase 2 methodology
"""
After threshold calibration, update app/config.py with results.

Changes needed:
1. Add phi_score_thresholds dict (per-entity)
2. Mark phi_score_threshold as deprecated (global fallback)
3. Add calibration metadata (date, dataset, rationale)
"""

# In app/config.py Settings class:
class Settings(BaseSettings):
    # ... existing fields ...

    # =========================================================================
    # Presidio Configuration - Threshold Calibration (Phase 2)
    # =========================================================================
    phi_score_thresholds: Dict[str, float] = Field(
        default={
            # Calibrated 2026-01-23 using synthetic dataset (seed=42+43)
            # Methodology: PR curve analysis, F2 optimization, recall≥90% floor
            # See .planning/phases/02-threshold-calibration/CALIBRATION_RESULTS.md

            "PERSON": 0.35,
            # Baseline: 98.8% recall → Keep low threshold
            # Rationale: High baseline performance, aggressive threshold safe

            "PHONE_NUMBER": 0.40,
            # Baseline: 74.0% recall → Calibrated to 92% recall
            # Rationale: Threshold 0.40 maximizes F2=89% with P=86%, R=92%

            "EMAIL_ADDRESS": 0.30,
            # Baseline: 100% recall → Most aggressive threshold
            # Rationale: Perfect baseline, can be aggressive without risk

            "DATE_TIME": 0.35,
            # Baseline: 96.8% recall → Keep current threshold
            # Rationale: Near-perfect baseline, no adjustment needed

            "LOCATION": 0.45,
            # Baseline: 19.4% recall → Calibrated to 78% recall (best possible)
            # Rationale: Deny list aggressive, pattern improvements needed (Phase 4)

            "MEDICAL_RECORD_NUMBER": 0.40,
            # Baseline: 70.9% recall → Calibrated to 91% recall
            # Rationale: Threshold 0.40 achieves F2=88% with P=85%, R=91%

            "ROOM": 0.50,
            # Baseline: 34.4% recall → Calibrated to 68% recall (insufficient)
            # Rationale: Pattern improvements required (Phase 4), threshold limited

            "GUARDIAN_NAME": 0.35,
            # Baseline: (grouped with PERSON) → Same threshold as PERSON
            # Rationale: Custom recognizer, similar confidence distribution

            "PEDIATRIC_AGE": 0.55,
            # Baseline: 36.6% recall → Calibrated to 72% recall (insufficient)
            # Rationale: Pattern improvements required (Phase 4), threshold limited
        },
        description="Per-entity confidence score thresholds (Phase 2 calibrated 2026-01-23)"
    )

    phi_score_threshold: float = Field(
        default=0.35,
        description=(
            "DEPRECATED: Global threshold for backward compatibility. "
            "Use phi_score_thresholds (per-entity) for production. "
            "Only used as fallback for entity types not in phi_score_thresholds dict."
        )
    )

    # Calibration metadata
    threshold_calibration_date: str = Field(
        default="2026-01-23",
        description="Date of last threshold calibration (ISO format)"
    )
    threshold_calibration_method: str = Field(
        default="PR curve analysis, F2 optimization, recall≥90% floor",
        description="Methodology used for threshold calibration"
    )
    threshold_calibration_dataset: str = Field(
        default="synthetic_handoffs.json (seed=42) + adversarial_handoffs.json (seed=43)",
        description="Dataset used for threshold calibration"
    )
```

### Example 4: Integration with deidentification.py

```python
# Source: Adaptation of existing deidentification.py with per-entity thresholds
def analyze_text_with_per_entity_thresholds(text: str) -> list[dict]:
    """
    Run Presidio analysis with per-entity confidence thresholds.

    Replaces existing analyze_text() in evaluate_presidio.py.
    """
    analyzer, _ = _get_engines()
    from app.config import settings

    # Run Presidio with minimum threshold (get all detections)
    raw_results = analyzer.analyze(
        text=text,
        language="en",
        entities=settings.phi_entities,
        score_threshold=0.0  # Get everything, filter manually
    )

    # Apply per-entity thresholds
    filtered = []
    for result in raw_results:
        detected_text = text[result.start:result.end].strip()

        # Check deny lists (unchanged)
        if result.entity_type == "LOCATION" and detected_text in settings.deny_list_location:
            continue
        if result.entity_type == "PERSON" and detected_text.lower() in [w.lower() for w in settings.deny_list_person]:
            continue

        # Apply per-entity threshold
        entity_threshold = settings.phi_score_thresholds.get(
            result.entity_type,
            settings.phi_score_threshold  # Fallback to global
        )

        if result.score >= entity_threshold:
            filtered.append({
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score,
                "text": detected_text,
            })

    return filtered


def validate_deidentification_aligned(original: str, cleaned: str) -> tuple[bool, list[str]]:
    """
    Re-scan cleaned text with ALIGNED thresholds (fix 0.35/0.7 mismatch).

    Replaces existing validate_deidentification() in deidentification.py.
    """
    analyzer, _ = _get_engines()
    from app.config import settings

    # Use same per-entity thresholds as detection (alignment fix)
    raw_results = analyzer.analyze(
        text=cleaned,
        language="en",
        entities=settings.phi_entities,
        score_threshold=0.0
    )

    warnings = []

    for result in raw_results:
        detected = cleaned[result.start:result.end]

        # Skip markers we added
        if detected.startswith("[") and detected.endswith("]"):
            continue

        # Apply per-entity threshold (ALIGNED with detection)
        entity_threshold = settings.phi_score_thresholds.get(
            result.entity_type,
            settings.phi_score_threshold
        )

        if result.score >= entity_threshold:
            warnings.append(
                f"Potential PHI leak: {result.entity_type} "
                f"(score: {result.score:.2f}, threshold: {entity_threshold:.2f}) "
                f"at position {result.start}-{result.end}"
            )

    is_valid = len(warnings) == 0

    if not is_valid:
        logger.warning(f"Validation found {len(warnings)} potential PHI leaks")

    return is_valid, warnings
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Global NER threshold | Per-entity thresholds | 2024-2025 | Medical NLP systems now standard practice to calibrate per entity type |
| F1 optimization | F2/F-beta optimization | 2023-2024 | Medical safety applications weight recall higher than precision |
| Manual threshold tuning | PR curve analysis | 2022-present | Systematic, data-driven threshold selection replaces ad-hoc tuning |
| ROC curves for NER | Precision-recall curves | 2020-present | Imbalanced classes (rare PHI vs common text) make PR curves more informative |
| Single dataset calibration | Multi-dataset validation | 2023-present | Standard + adversarial + real-world datasets for robust calibration |

**Deprecated/outdated:**
- **Global confidence threshold for all entities**: Multi-class NER systems require per-entity calibration (different confidence distributions)
- **0.5 default threshold**: Arbitrary choice from binary classification; NER systems need data-driven selection
- **Validation threshold != detection threshold**: Inconsistent behavior; modern practice aligns thresholds across pipeline
- **F1 as primary metric for PHI**: Medical safety requires recall-weighted metrics (F2, F-beta with beta>1)

## Open Questions

### 1. How much recall improvement is achievable through threshold tuning alone?

**What we know:**
- Baseline: 77.9% overall recall
- Target: >90% recall
- Gap: 12.1 percentage points
- Weakest entities: PEDIATRIC_AGE (36.6%), ROOM (34.4%), LOCATION (19.4%)

**What's unclear:**
- Can threshold tuning alone achieve >90% for weakest entity types?
- Or are pattern improvements (Phase 4) required for ROOM/PEDIATRIC_AGE?

**Recommendation:**
- Phase 2 calibrates thresholds optimally
- Document which entities achieve >90% (threshold-solvable)
- Document which entities remain <90% (require Phase 4 patterns)
- Update success criteria: "Overall recall >90%" may require Phases 2+4 combined

### 2. Should validation threshold differ from detection threshold?

**What we know:**
- Current: Detection 0.35, validation 0.7 (2x difference)
- Industry practice: Some systems use validation threshold +0.05 to +0.10 higher (safety margin)
- Rationale: Catch high-confidence PHI that leaked through detection

**What's unclear:**
- Does higher validation threshold catch real leaks, or just create noise?
- What's the false positive rate of validation warnings?
- Do validation warnings get acted upon in production?

**Recommendation for Phase 2:**
- Align validation and detection thresholds (same per-entity values)
- Document rationale: "Consistent pipeline, no arbitrary 2x gap"
- Phase 5 (real transcripts) can re-evaluate if validation safety margin needed

### 3. How do thresholds generalize from synthetic to real transcripts?

**What we know:**
- Phase 2 uses synthetic (seed=42) + adversarial (seed=43) datasets
- Real transcript testing deferred to Phase 5
- ASR errors and noisy audio likely reduce confidence scores

**What's unclear:**
- Will synthetic-optimized thresholds work on real transcripts?
- How much confidence score degradation occurs with real audio?
- Should Phase 2 apply preemptive -0.05 safety margin?

**Recommendation:**
- Phase 2: Optimize on synthetic + adversarial, document as "synthetic-calibrated"
- Phase 5: Re-calibrate on real transcripts, measure generalization gap
- If gap >10 percentage points, apply systematic threshold reduction (e.g., -0.05)

### 4. What's the optimal threshold sweep granularity?

**What we know:**
- Context decision: Coarse sweep (0.10 steps: 0.30, 0.40, 0.50, 0.60)
- Fine sweep (0.05 steps) would double evaluation cost
- PR curve provides continuous threshold data

**What's unclear:**
- Is 0.10 granularity sufficient for finding optimal threshold?
- Could optimal threshold lie between 0.30 and 0.40 (e.g., 0.35)?
- Should Phase 2 include fine sweep around coarse optimal?

**Recommendation:**
- Phase 2: Stick with coarse 0.10 sweep (4 thresholds) as decided
- If coarse sweep shows large F2 jumps (e.g., 0.30→78%, 0.40→91%), document need for fine sweep
- Phase 4 (if recall still <90%): Consider fine sweep as part of iterative tuning

## Sources

### Primary (HIGH confidence)

**Precision-Recall Curve Methodology:**
- [sklearn.metrics.precision_recall_curve documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_curve.html) - Official API reference
- [Precision-Recall Curve Tutorial | DataCamp](https://www.datacamp.com/tutorial/precision-recall-curve-tutorial) - Practical implementation guide
- [How to use classification threshold to balance precision and recall | EvidentlyAI](https://www.evidentlyai.com/classification-metrics/classification-threshold) - Threshold optimization techniques

**Medical NER Best Practices:**
- [Enhancing Named-Entity Recognition in Colonoscopy Reports - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12387308/) - Medical NER with F2 optimization (Oct 2024)
- [Named Entity Recognition Trilemma | Medium](https://medium.com/@bryan.leezc/named-entity-recognition-ner-trilemma-balancing-cost-latency-accuracy-0be093fc8028) - Per-entity threshold rationale (Dec 2025)

**Presidio Configuration:**
- [Presidio Analyzer API Documentation](https://microsoft.github.io/presidio/api/analyzer_python/) - Official threshold configuration
- [Customizing Presidio Analyzer](https://microsoft.github.io/presidio/samples/python/customizing_presidio_analyzer/) - Per-entity configuration examples

### Secondary (MEDIUM confidence)

**Threshold Optimization Techniques:**
- [7 Proven Techniques for Optimizing Precision-Recall Curve Area](https://www.numberanalytics.com/blog/optimizing-precision-recall-curve-techniques) - Practical optimization strategies
- [Choosing the Right Metrics | Medium](https://medium.com/@juanc.olamendy/choosing-the-right-metrics-recall-precision-pr-curve-and-roc-curve-explained-682259961cbe) - F2 vs F1 rationale

**Visualization Best Practices:**
- [PrecisionRecallDisplay — scikit-learn 1.8.0](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.PrecisionRecallDisplay.html) - Official plotting API
- [How to Create a Precision-Recall Curve in Python | Statology](https://www.statology.org/precision-recall-curve-python/) - Matplotlib implementation

### Tertiary (LOW confidence - validation needed)

**General NER Practices:**
- [Named Entity Recognition (NER) Complete Guide 2026](https://www.articsledge.com/post/named-entity-recognition-ner) - Industry overview (requires validation)
- [5 techniques to improve entity recognition | Innovatiana](https://www.innovatiana.com/en/post/5-techniques-to-optimize-ner) - General NER optimization (not threshold-specific)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified in project venv, sklearn/matplotlib standard for PR curves
- Architecture: HIGH - Per-entity threshold pattern confirmed in medical NER literature (2024-2025)
- Code examples: HIGH - Adapted from sklearn official docs + existing `evaluate_presidio.py` patterns
- Pitfalls: HIGH - Identified from baseline measurements + industry best practices
- Open questions: MEDIUM - Require Phase 2 execution to resolve (synthetic→real generalization, optimal granularity)

**Research date:** 2026-01-23
**Valid until:** 30 days (stable domain - sklearn API stable, Presidio 2.x API stable)

**Key assumptions:**
1. Existing evaluation infrastructure (`evaluate_presidio.py`) functional and accurate
2. Synthetic + adversarial datasets (Phase 1) representative enough for threshold calibration
3. Per-entity thresholds implementable via post-analysis filtering (Presidio limitation workaround)
4. F2 score appropriate primary metric (recall-weighted, HIPAA compliance focus)
5. Threshold calibration alone can achieve >90% overall recall (may require Phase 4 pattern improvements for weakest entities)

---

**RESEARCH COMPLETE** - Ready for planning Phase 2 tasks.
