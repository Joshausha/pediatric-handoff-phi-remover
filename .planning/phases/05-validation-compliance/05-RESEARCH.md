# Phase 5: Validation & Compliance - Research

**Researched:** 2026-01-23
**Domain:** NER validation, statistical evaluation, HIPAA compliance documentation
**Confidence:** MEDIUM-HIGH

## Summary

Phase 5 validates that PHI detection improvements from Phases 2-4 achieve clinical deployment readiness. The domain requires three parallel workstreams: (1) **External validation** on real transcripts to detect domain shift from synthetic training data, (2) **Statistical validation** with confidence intervals to document >95% recall threshold, and (3) **HIPAA compliance documentation** calculating residual risk under Expert Determination standard.

The critical insight from research: **synthetic-to-real domain shift is a documented challenge in medical NER**. Studies from 2025 show performance gaps of 15-30% when models trained on synthetic data face real clinical text. This means the current ~78% baseline recall on synthetic data may drop significantly on real handoffs, requiring human-annotated gold standard validation.

**Primary recommendation:** Use stratified sampling with expert annotation to create a validation set of 50-100 real handoffs, calculate recall with 95% confidence intervals using bootstrap methods, and document residual risk under HIPAA Expert Determination standard (target: <0.04% re-identification risk).

## Standard Stack

The established tools for NER validation in medical de-identification:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Microsoft Presidio-Research | Latest | Evaluation framework for PII detection | Official evaluation toolkit with dataset splitting, metrics calculation, error analysis |
| scikit-learn | 1.3+ | Metrics and stratification | Industry standard for StratifiedKFold, confusion matrices, bootstrap CI |
| pandas | 2.0+ | Results analysis and aggregation | De facto standard for tabular metrics and error categorization |
| jupyter | Latest | Interactive error analysis | Standard for exploratory validation analysis and visualization |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scipy.stats | 1.11+ | Statistical tests and CI | Bootstrap confidence intervals for recall/precision |
| matplotlib/seaborn | Latest | Visualization | Per-entity performance plots, confusion matrices |
| inter-annotator-agreement | Latest | IAA metrics (Cohen's kappa) | Human annotation quality assessment |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Presidio-Research | Custom evaluation | Presidio-Research is domain-standard; custom code risks bugs in metrics |
| Bootstrap CI | Normal approximation | Bootstrap handles small samples better (more robust for n=50-100) |
| Expert annotation | Crowd annotation | Medical PHI requires clinical expertise; crowd workers lack domain knowledge |

**Installation:**
```bash
# Core evaluation stack (already have Presidio)
pip install scikit-learn pandas jupyter scipy matplotlib seaborn

# Presidio-Research for advanced evaluation (optional)
pip install presidio-research
```

## Architecture Patterns

### Recommended Validation Workflow Structure
```
.planning/phases/05-validation-compliance/
├── datasets/
│   ├── real_handoffs_raw/          # Real audio (NEVER commit)
│   ├── real_handoffs_gold/         # Human-annotated JSON (anonymized IDs)
│   └── validation_split.json       # Train/val/test split indices
├── annotation/
│   ├── annotation_guidelines.md    # PHI entity definitions for annotators
│   ├── annotator_A_results.json    # First annotator (for IAA)
│   ├── annotator_B_results.json    # Second annotator (for IAA)
│   └── consensus_resolution.json   # Adjudicated gold standard
├── evaluation/
│   ├── external_validation.py      # Run Presidio on real data
│   ├── calculate_metrics.py        # Recall, precision, F2 with CI
│   └── error_analysis.py           # False negative taxonomy
├── compliance/
│   ├── residual_risk_calc.py       # HIPAA Expert Determination
│   └── compliance_report.md        # HIPAA documentation
└── notebooks/
    ├── 01_error_taxonomy.ipynb     # Interactive error categorization
    ├── 02_confidence_intervals.ipynb # Bootstrap CI calculation
    └── 03_per_entity_analysis.ipynb  # Entity-level deep dive
```

### Pattern 1: Stratified External Validation
**What:** Use stratified random sampling to create validation set that preserves entity distribution from synthetic data
**When to use:** When validating on real data beyond training corpus
**Example:**
```python
# Source: scikit-learn StratifiedKFold documentation
from sklearn.model_selection import train_test_split
import numpy as np

# Stratify by dominant PHI type per handoff
handoff_labels = [dominant_phi_type(h) for h in real_handoffs]
train, val = train_test_split(
    real_handoffs,
    test_size=0.3,
    stratify=handoff_labels,
    random_state=42
)
```

### Pattern 2: Bootstrap Confidence Intervals for Recall
**What:** Use percentile bootstrap method to calculate 95% CI for recall metric
**When to use:** Small validation sets (n=50-100) where normal approximation unreliable
**Example:**
```python
# Source: Statistical Inference via Data Science (moderndive.com)
import numpy as np
from scipy import stats

def bootstrap_recall_ci(y_true, y_pred, n_bootstrap=10000, confidence=0.95):
    """Calculate bootstrap CI for recall using percentile method."""
    n = len(y_true)
    recalls = []

    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]

        # Calculate recall for this bootstrap sample
        tp = np.sum((y_true_boot == 1) & (y_pred_boot == 1))
        fn = np.sum((y_true_boot == 1) & (y_pred_boot == 0))
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        recalls.append(recall)

    # Percentile method: find 2.5th and 97.5th percentiles
    alpha = 1 - confidence
    lower = np.percentile(recalls, 100 * alpha / 2)
    upper = np.percentile(recalls, 100 * (1 - alpha / 2))

    return np.mean(recalls), (lower, upper)

# Usage
recall_mean, (ci_lower, ci_upper) = bootstrap_recall_ci(y_true, y_pred)
print(f"Recall: {recall_mean:.1%} (95% CI: {ci_lower:.1%} - {ci_upper:.1%})")
```

### Pattern 3: Inter-Annotator Agreement for Gold Standard
**What:** Measure Cohen's kappa between two independent annotators before adjudication
**When to use:** Creating human-annotated gold standard for external validation
**Example:**
```python
# Source: Prodigy annotation metrics documentation
from sklearn.metrics import cohen_kappa_score

def calculate_entity_iaa(annotations_a, annotations_b, text):
    """Calculate token-level Cohen's kappa for NER annotations."""
    # Convert entity spans to token-level labels
    labels_a = spans_to_token_labels(annotations_a, text)
    labels_b = spans_to_token_labels(annotations_b, text)

    kappa = cohen_kappa_score(labels_a, labels_b)

    # For NER, average pairwise F1 is also recommended
    f1 = calculate_pairwise_f1(annotations_a, annotations_b)

    return {"kappa": kappa, "f1": f1}

# Target: kappa > 0.8 (substantial agreement)
# NER-specific: average pairwise F1 > 0.9
```

### Pattern 4: False Negative Error Taxonomy
**What:** Categorize missed PHI by failure mode to guide improvements
**When to use:** Error analysis phase of validation
**Example:**
```python
# Source: Presidio-Research evaluation notebooks
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class FalseNegativeCase:
    entity_type: str
    text: str
    context: str  # Surrounding text
    failure_mode: str  # "pattern_miss", "threshold_miss", "novel_variant", etc.

def categorize_false_negatives(results, evaluator):
    """Build taxonomy of FN patterns."""
    taxonomy = defaultdict(list)

    for result in results:
        for fn_span in result.false_negatives:
            # Get context
            context = get_context_window(result.text, fn_span.start, fn_span.end)

            # Classify failure mode
            mode = classify_failure_mode(fn_span, result.detected_spans)

            case = FalseNegativeCase(
                entity_type=fn_span.entity_type,
                text=fn_span.text,
                context=context,
                failure_mode=mode
            )
            taxonomy[mode].append(case)

    return taxonomy

# Common failure modes:
# - "pattern_miss": Regex didn't match variant
# - "threshold_miss": Detected but score below threshold
# - "deny_list_filtered": Incorrectly filtered by deny list
# - "novel_variant": Pattern not seen in synthetic data
```

### Pattern 5: HIPAA Residual Risk Calculation
**What:** Calculate re-identification risk under Expert Determination standard
**When to use:** HIPAA compliance documentation for clinical deployment
**Example:**
```python
# Source: HIPAA Expert Determination guidance (HHS.gov)
from dataclasses import dataclass

@dataclass
class ResidualRisk:
    """HIPAA residual risk assessment."""
    recall: float
    recall_ci_lower: float
    recall_ci_upper: float
    total_phi_spans: int
    false_negatives: int
    reidentification_risk: float  # Expected % of patients

    def is_compliant(self, threshold: float = 0.0004) -> bool:
        """Check if risk meets HIPAA threshold (<0.04%)."""
        return self.reidentification_risk <= threshold

    def generate_report(self) -> str:
        """Generate Expert Determination documentation."""
        return f"""
HIPAA Expert Determination - Residual Risk Assessment

1. Detection Performance:
   - Recall: {self.recall:.2%} (95% CI: {self.recall_ci_lower:.2%} - {self.recall_ci_upper:.2%})
   - Total PHI spans evaluated: {self.total_phi_spans}
   - False negatives: {self.false_negatives}

2. Re-identification Risk:
   - Conservative estimate: {self.reidentification_risk:.4%}
   - HIPAA threshold: 0.04%
   - Compliant: {'YES' if self.is_compliant() else 'NO'}

3. Methodology:
   - External validation on {self.total_phi_spans // 10} real handoffs
   - Human expert annotation with dual coding
   - Bootstrap confidence intervals (10,000 iterations)

4. Risk Mitigation:
   - Local processing only (no external API calls)
   - Audit logging of all processing events
   - Manual review required for high-risk transcripts
        """

# Usage
risk = ResidualRisk(
    recall=0.96,
    recall_ci_lower=0.94,
    recall_ci_upper=0.98,
    total_phi_spans=500,
    false_negatives=20,
    reidentification_risk=0.04  # 4 in 10,000 = 0.04%
)
```

### Anti-Patterns to Avoid
- **Normal approximation for small samples**: Use bootstrap CI instead (more robust for n<100)
- **Single annotator gold standard**: Always use dual coding with adjudication (Cohen's kappa > 0.8)
- **Ignoring domain shift**: Synthetic data performance ≠ real data performance (validate externally)
- **Entity name mismatches**: Align ground truth labels with Presidio output (e.g., "PER" vs "PERSON")
- **Threshold tuning on validation set**: Use separate test set or risk overfitting to validation data

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Metrics calculation | Custom precision/recall code | `sklearn.metrics` or Presidio-Research | Edge cases (zero division, empty sets) already handled |
| Confidence intervals | Normal approximation formula | `scipy.stats.bootstrap` or percentile method | Bootstrap handles small samples and non-normal distributions |
| Dataset splitting | Random shuffle | `sklearn.model_selection.StratifiedKFold` | Prevents entity distribution imbalance across folds |
| Inter-annotator agreement | Custom agreement calculator | `sklearn.metrics.cohen_kappa_score` | Handles chance agreement correction |
| Span overlap matching | String comparison | Presidio-Research overlap calculator | Handles partial overlaps, Jaccard-like scoring |

**Key insight:** Evaluation metrics are deceptively complex. Off-by-one errors, zero-division edge cases, and bootstrap sampling bugs can invalidate results. Use battle-tested libraries.

## Common Pitfalls

### Pitfall 1: Synthetic-to-Real Domain Shift
**What goes wrong:** Model performs well on synthetic data (~78% recall) but drops 15-30% on real clinical transcripts
**Why it happens:** Synthetic templates don't capture full variability of real speech patterns, abbreviations, and context
**How to avoid:**
- Reserve 20-30% of budget for external validation on real data
- Use stratified sampling to ensure entity type coverage
- Document performance gap in compliance report
**Warning signs:**
- Large performance drop on first real handoff
- New PHI patterns not in synthetic templates
- Higher FN rate for specific entity types

### Pitfall 2: Overfitting to Validation Set
**What goes wrong:** Tuning thresholds on validation set inflates performance estimates
**Why it happens:** Adjusting detection parameters based on validation errors introduces information leakage
**How to avoid:**
- Use train/val/test split (e.g., 60/20/20)
- Tune on validation set, report final metrics on held-out test set
- Document all threshold changes and their rationale
**Warning signs:**
- Performance significantly worse on test set than validation
- Multiple threshold adjustments based on validation errors
- Suspiciously high recall with no precision penalty

### Pitfall 3: Insufficient Sample Size for >95% Recall
**What goes wrong:** Need ~100 handoffs to distinguish 95% from 90% recall with confidence
**Why it happens:** Small samples have wide confidence intervals (e.g., n=20 gives ±10% CI)
**How to avoid:**
- Calculate sample size needed for target CI width (recommend 95% CI width ≤ 5%)
- For 95% recall target: need ~100-150 PHI spans minimum
- Use power analysis to justify sample size
**Warning signs:**
- Wide confidence intervals (>10% width)
- Unable to reject null hypothesis that recall < 95%
- High variance in bootstrap samples

### Pitfall 4: Entity Label Mismatches in Evaluation
**What goes wrong:** Precision/recall calculated incorrectly due to ground truth using different entity names than Presidio
**Why it happens:** Annotation tools use different standards (e.g., "PER" vs "PERSON")
**How to avoid:**
- Create entity type mapping dictionary (see `PresidioEvaluator.TYPE_MAPPING`)
- Document any custom entity types (GUARDIAN_NAME, PEDIATRIC_AGE)
- Validate mapping by spot-checking first 10 handoffs
**Warning signs:**
- Zero recall for specific entity type (but detections exist)
- False positives that match ground truth text but different label
- Confusion matrix shows off-diagonal spikes

### Pitfall 5: Ignoring Inter-Annotator Agreement
**What goes wrong:** Low IAA means gold standard is unreliable, invalidating validation results
**Why it happens:** PHI entity boundaries are ambiguous without clear guidelines
**Why it's critical:** Low agreement (kappa < 0.7) suggests annotation guidelines are unclear or task is too subjective
**How to avoid:**
- Measure Cohen's kappa on 20% double-coded sample (target: >0.8)
- For NER, also calculate average pairwise F1 score (target: >0.9)
- If IAA low, revise annotation guidelines and re-annotate
**Warning signs:**
- Annotators disagree on entity boundaries (e.g., "Mom Sarah" vs "Sarah")
- Systematic disagreements on specific entity types
- Adjudication required for >30% of cases

### Pitfall 6: HIPAA Safe Harbor vs. Expert Determination Confusion
**What goes wrong:** Assuming Safe Harbor method applies when using automated de-identification
**Why it happens:** Safe Harbor is a checklist (remove 18 identifiers); Expert Determination requires risk assessment
**Reality check:** Automated tools like Presidio require **Expert Determination** standard with quantified residual risk
**How to avoid:**
- Document recall with 95% CI
- Calculate re-identification risk (conservative estimate)
- Target: <0.04% risk (4 in 10,000 patients)
- Engage statistician or privacy expert for certification
**Warning signs:**
- Compliance documentation cites Safe Harbor
- No residual risk calculation
- No confidence intervals reported

## Code Examples

Verified patterns from official sources:

### Sample Size Calculation for Recall Target
```python
# Source: Extended sample size calculations for prediction models (PMC12210805)
from scipy.stats import norm

def sample_size_for_recall_ci(target_recall=0.95, ci_width=0.05, confidence=0.95):
    """
    Calculate required sample size to estimate recall within target CI width.

    Uses normal approximation for binomial proportion.
    Conservative estimate assumes worst-case variance (p=0.5).

    Args:
        target_recall: Expected recall (0-1)
        ci_width: Desired 95% CI width (e.g., 0.05 = ±2.5%)
        confidence: Confidence level (default: 0.95)

    Returns:
        Required number of PHI spans to validate
    """
    z = norm.ppf(1 - (1 - confidence) / 2)  # 1.96 for 95% CI

    # Margin of error = half the CI width
    margin = ci_width / 2

    # Conservative variance: p(1-p) maximized at p=0.5
    p = 0.5  # Worst case

    # n = (z^2 * p * (1-p)) / margin^2
    n = (z**2 * p * (1 - p)) / margin**2

    return int(np.ceil(n))

# Example: For 95% recall with 5% CI width (±2.5%)
n_required = sample_size_for_recall_ci(target_recall=0.95, ci_width=0.05)
print(f"Required PHI spans: {n_required}")  # ~385 spans
# At 5 PHI/handoff average: need ~77 handoffs
```

### Presidio-Research Dataset Evaluation
```python
# Source: Presidio-Research GitHub - notebooks/4_Evaluate_Presidio_Analyzer.ipynb
from presidio_evaluator import InputSample
from presidio_evaluator.evaluation import Evaluator, ModelError

# Convert existing evaluation to Presidio-Research format
def convert_to_input_samples(dataset):
    """Convert SyntheticHandoff dataset to Presidio-Research format."""
    samples = []
    for handoff in dataset:
        # Convert PHI spans to InputSample format
        spans = [
            {"start": s.start, "end": s.end, "label": s.entity_type}
            for s in handoff.phi_spans
        ]
        sample = InputSample(
            full_text=handoff.text,
            masked=None,  # Not using masking
            spans=spans,
            create_tags_from_span=True
        )
        samples.append(sample)
    return samples

# Evaluate with Presidio-Research
evaluator = Evaluator(model=presidio_analyzer)
evaluation_results = evaluator.evaluate_all(input_samples)

# Results include per-entity precision, recall, F1
for entity, metrics in evaluation_results.items():
    print(f"{entity}: P={metrics.precision:.1%} R={metrics.recall:.1%}")
```

### Error Analysis with Failure Mode Classification
```python
# Source: Custom implementation following Presidio-Research patterns
from enum import Enum
from typing import List, Tuple

class FailureMode(Enum):
    """Taxonomy of false negative failure modes."""
    PATTERN_MISS = "pattern_miss"  # Regex didn't match
    THRESHOLD_MISS = "threshold_miss"  # Score below threshold
    DENY_LIST_FILTER = "deny_list_filtered"  # Incorrectly filtered
    NOVEL_VARIANT = "novel_variant"  # Not in synthetic training
    CONTEXT_DEPENDENT = "context_dependent"  # Needs more context
    SPAN_BOUNDARY = "span_boundary"  # Partial match only

def classify_failure(
    fn_span: PHISpan,
    detected_spans: List[dict],
    threshold: float = 0.30
) -> FailureMode:
    """
    Classify why a PHI span was missed.

    Returns most specific failure mode.
    """
    # Check if partially detected (span boundary issue)
    for det in detected_spans:
        overlap = calculate_overlap(fn_span.start, fn_span.end, det["start"], det["end"])
        if 0.1 < overlap < 0.5:  # Partial overlap
            return FailureMode.SPAN_BOUNDARY

    # Check if detected but scored below threshold
    # (Would need access to raw analyzer results for this)
    # Placeholder: add this logic if available

    # Check if it matches a deny list pattern
    if fn_span.text.lower() in deny_list_terms:
        return FailureMode.DENY_LIST_FILTER

    # Check if pattern type not in synthetic templates
    if is_novel_pattern(fn_span):
        return FailureMode.NOVEL_VARIANT

    # Default: pattern miss
    return FailureMode.PATTERN_MISS

def generate_error_report(failure_taxonomy):
    """Generate actionable error analysis report."""
    print("FALSE NEGATIVE TAXONOMY")
    print("=" * 60)

    for mode, cases in sorted(failure_taxonomy.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{mode.value.upper()}: {len(cases)} cases")
        print("-" * 40)

        # Show top 5 examples
        for case in cases[:5]:
            print(f"  {case.entity_type}: '{case.text}'")
            print(f"    Context: ...{case.context}...")

        # Actionable recommendation
        recommendations = {
            FailureMode.PATTERN_MISS: "Add regex pattern or training examples",
            FailureMode.THRESHOLD_MISS: "Lower detection threshold or improve recognizer",
            FailureMode.DENY_LIST_FILTER: "Review deny list for over-aggressive filtering",
            FailureMode.NOVEL_VARIANT: "Expand synthetic templates or add custom recognizer",
            FailureMode.SPAN_BOUNDARY: "Adjust tokenization or overlap matching threshold",
        }
        print(f"  → Recommendation: {recommendations.get(mode, 'Investigate further')}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 100% recall requirement | >95% recall with risk calc | 2024-2025 research | Acknowledges no de-identification is perfect; focus on quantifying residual risk |
| Single annotator | Dual coding + adjudication | Standard practice (2020+) | Cohen's kappa >0.8 ensures reliable gold standard |
| Normal approximation CI | Bootstrap percentile method | 2020+ (small sample awareness) | More robust for n<100, handles non-normal distributions |
| Vanilla Presidio | Configured Presidio + custom recognizers | Ongoing | ~30% F-score improvement (Presidio docs) |
| Training-only evaluation | External validation required | 2024-2025 (domain shift research) | Studies show 15-30% performance drop on real data |

**State-of-the-art performance (2025):**
- John Snow Labs Healthcare NLP: **96% F1** for PHI detection (regulatory-grade)
- Microsoft Azure: 91% F1
- AWS Comprehend Medical: 83% F1
- GPT-4: 79% F1

**Implication for this project:** 95% recall target is achievable but requires careful validation and custom recognizers (already implemented in Phases 2-4).

**Deprecated/outdated:**
- **Safe Harbor for automated de-identification**: HIPAA Safe Harbor is for manual removal of 18 identifiers; automated tools require Expert Determination with risk quantification
- **10-fold CV on synthetic data only**: Now considered insufficient; external validation on real data is standard
- **Cohen's kappa alone for NER**: NER community now recommends average pairwise F1 as primary IAA metric (kappa is secondary)

## Open Questions

Things that couldn't be fully resolved:

1. **IRB approval timeline for real handoff access**
   - What we know: Need IRB approval to collect real handoffs for validation
   - What's unclear: Timeline (6-12 months?), whether de-identified handoffs qualify as exempt
   - Recommendation: Start IRB application early in Phase 5; alternatively, use publicly available medical transcripts (e.g., MIMIC-III) as interim external validation

2. **Optimal validation set size given budget constraints**
   - What we know: Sample size calculation suggests ~77 handoffs for 5% CI width
   - What's unclear: Trade-off between annotation cost and statistical power
   - Recommendation: Start with 50 handoffs (pragmatic minimum), expand to 100+ if recall CI too wide

3. **Expert Determination certification process**
   - What we know: HIPAA requires qualified statistician/privacy expert for Expert Determination
   - What's unclear: Formal certification requirements, who qualifies as "expert"
   - Recommendation: Engage hospital privacy officer or biostatistics consultant for final certification

4. **Handling adversarial cases in validation set**
   - What we know: 100 adversarial handoffs exist in synthetic corpus
   - What's unclear: Should validation set include adversarial cases or only natural variation?
   - Recommendation: Stratify validation set to include 20% adversarial cases (mirrors synthetic distribution)

5. **Threshold for "very small" re-identification risk**
   - What we know: HHS doesn't define exact threshold; 0.04% (4 in 10,000) is nationally accepted
   - What's unclear: Whether pediatric handoffs require stricter threshold (children are vulnerable population)
   - Recommendation: Use 0.04% as baseline; document conservative assumptions in risk calculation

## Sources

### Primary (HIGH confidence)
- [Microsoft Presidio Official Evaluation Documentation](https://microsoft.github.io/presidio/evaluation/) - Metrics, dataset formats, evaluation best practices
- [Microsoft Presidio-Research GitHub](https://github.com/microsoft/presidio-research) - Dataset splitting, evaluation notebooks, metrics calculation
- [HHS HIPAA De-identification Guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html) - Safe Harbor vs Expert Determination, residual risk requirements
- [HIPAA Journal: De-identification 2026 Update](https://www.hipaajournal.com/de-identification-protected-health-information/) - Current best practices, risk thresholds

### Secondary (MEDIUM confidence)
- [Benchmarking Modern NER for Health Record De-identification (PMC8378656)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8378656/) - Bi-LSTM-CRF architecture, character embeddings impact on recall
- [Using Synthetic Healthcare Data for Medical NER (JMIR 2025)](https://www.jmir.org/2025/1/e66279) - Synthetic-to-real domain shift, F1 scores of 0.69 (drugs) and 0.38 (procedures)
- [Bootstrap Confidence Intervals (Statistical Inference via Data Science)](https://moderndive.com/8-confidence-intervals.html) - Percentile method for 95% CI
- [Smooth Bootstrap for Binomial Proportions (PMC4789773)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4789773/) - Confidence intervals for recall metric
- [Cohen's Kappa for Medical Image Annotation (PMC10062409)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10062409/) - IAA best practices, kappa >0.8 target
- [Prodigy Annotation Metrics](https://prodi.gy/docs/metrics) - Token-based NER F1 score for IAA
- [Sample Size for Prediction Models (PMC12210805)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12210805/) - Sample size calculations for precision/recall CI

### Tertiary (LOW confidence - for further investigation)
- [2025 De-identification Tools Benchmark (Censinet)](https://www.censinet.com/perspectives/2025-benchmark-de-identification-tools) - John Snow Labs 96% F1 benchmark, vendor comparison
- [Efficient Medical NER with Annotation Guidelines (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/pii/S1386505625004472) - Annotation guideline development for LLM-based NER
- [Synthetic4Health Clinical Letters (Frontiers 2025)](https://www.frontiersin.org/journals/digital-health/articles/10.3389/fdgth.2025.1497130/full) - Synthetic data for NER task validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Presidio-Research and scikit-learn are industry standards verified via official docs
- Architecture: MEDIUM-HIGH - Patterns drawn from academic papers and Presidio docs; some customization needed for pediatric domain
- Statistical methods: HIGH - Bootstrap CI and sample size calculations verified via peer-reviewed sources
- HIPAA compliance: MEDIUM - Expert Determination process documented by HHS but lacks specific implementation examples for NER systems
- Domain shift: MEDIUM - Multiple 2025 studies confirm issue, but exact magnitude varies by domain (15-30% range)

**Research date:** 2026-01-23
**Valid until:** ~60 days (2026-03-23) - Statistical methods stable; HIPAA guidance stable; Presidio library may receive updates

**Research limitations:**
- No access to Context7 for Presidio-specific queries (library may not be indexed)
- IRB processes are institution-specific; general guidance only
- Expert Determination certification varies by jurisdiction
- Synthetic-to-real performance gap estimates based on general medical NER, not pediatric handoffs specifically
