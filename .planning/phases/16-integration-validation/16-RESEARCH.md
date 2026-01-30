# Phase 16: Integration Validation - Research

**Researched:** 2026-01-30
**Domain:** End-to-end integration testing, CI/CD regression patterns, metric validation
**Confidence:** HIGH

## Summary

Integration validation for the dual-weight recall framework requires orchestrating existing validation infrastructure (`run_validation.py`, `evaluate_presidio.py`) within GitHub Actions CI while establishing regression baselines for three metric variants (unweighted, frequency-weighted, risk-weighted). The project already has comprehensive evaluation code with bootstrap confidence intervals, weighted metric calculations, and markdown report generation—integration validation primarily involves CI orchestration, baseline storage, and visual metric comparison.

The standard approach uses pytest-regressions for baseline JSON storage, pytest-mpl for chart generation/comparison, and GitHub Actions matrix strategy for tiered testing (smoke tests on PRs, full validation on main branch merges). Pre-computed expected results for the 27-recording validation set avoid PHI exposure in CI while maintaining real-world validation coverage.

**Primary recommendation:** Use pytest integration test wrapping `run_validation.py`, store baselines in `tests/baselines/regression.json`, generate metric comparison charts with matplotlib, and implement two-tier GitHub Actions workflow (quick smoke test + full validation).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 7.0+ | Test orchestration | Industry standard Python testing, already in project |
| pytest-regressions | 2.5+ | Baseline JSON storage | Automatic baseline creation/comparison, git-committable |
| matplotlib | 3.8+ | Metric comparison charts | Standard Python visualization, already in project deps |
| GitHub Actions | N/A | CI/CD automation | Project already uses `.github/workflows/test.yml` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-mpl | 0.18+ | Chart regression testing | If chart visual regression needed (optional) |
| numpy | <2.0 | Numerical operations | Already required for spacy compatibility |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest-regressions | Hardcoded constants | JSON more maintainable, easier to update baselines |
| matplotlib | plotly | matplotlib simpler for CI, no JS dependencies |
| GitHub Actions | Jenkins/GitLab CI | Actions already configured, native GitHub integration |

**Installation:**
```bash
pip install pytest-regressions
# matplotlib already in requirements.txt
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── integration/              # Integration tests
│   ├── __init__.py
│   ├── test_full_evaluation.py  # End-to-end validation
│   └── test_regression.py       # Regression baseline checks
├── baselines/                # Regression baselines (committed to git)
│   ├── regression.json       # Metric baselines
│   └── expected_results/     # Pre-computed validation results
│       └── validation_27_recordings.json
└── artifacts/                # Generated reports (gitignored)
    ├── validation_report.md
    └── metric_comparison.png
```

### Pattern 1: Integration Test Wrapper
**What:** pytest test that orchestrates `run_validation.py` and validates outputs
**When to use:** Need CI-integrated validation with pytest assertions
**Example:**
```python
# Source: pytest best practices (official docs)
import pytest
from pathlib import Path
from tests.run_validation import run_validation

def test_full_evaluation_synthetic_dataset():
    """End-to-end evaluation on synthetic dataset."""
    input_path = Path("tests/synthetic_handoffs.json")

    results = run_validation(
        input_path=input_path,
        n_bootstrap=10000,
        overlap_threshold=0.5,
        verbose=False,
    )

    # Assertions
    assert results["deployment_readiness"]["meets_threshold"]
    assert results["metrics"]["recall"] >= 0.85
    assert "error_taxonomy" in results
    assert "metrics" in results
```

### Pattern 2: Baseline Regression Testing
**What:** Compare current metrics against committed baseline JSON
**When to use:** Detect unintended metric regressions in CI
**Example:**
```python
# Source: pytest-regressions documentation
def test_metrics_regression(data_regression):
    """Ensure metrics don't regress from baseline."""
    results = run_validation(...)

    # Extract metrics for comparison
    metrics_snapshot = {
        "recall": results["metrics"]["recall"],
        "precision": results["metrics"]["precision"],
        "f2": results["metrics"]["f2"],
        "freq_weighted_recall": results["metrics"]["freq_weighted_recall"],
        "risk_weighted_recall": results["metrics"]["risk_weighted_recall"],
    }

    # First run creates baseline, subsequent runs compare
    data_regression.check(metrics_snapshot)
```

### Pattern 3: Tiered CI Testing
**What:** Fast smoke test on every push, comprehensive validation on main branch
**When to use:** Balance CI speed vs. coverage
**Example:**
```yaml
# Source: GitHub Actions CI patterns 2026
jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - name: Quick validation (10 handoffs)
        run: pytest tests/integration/test_smoke.py -v

  full-validation:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Full validation (500 handoffs + 27 real)
        run: pytest tests/integration/test_full_evaluation.py -v
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: validation-report
          path: tests/artifacts/
```

### Pattern 4: Metric Comparison Charts
**What:** Visual bar chart comparing unweighted/frequency/risk metrics
**When to use:** Make divergence patterns visible in reports
**Example:**
```python
# Source: matplotlib testing documentation
import matplotlib.pyplot as plt
import numpy as np

def generate_metric_comparison_chart(metrics, output_path):
    """Generate bar chart comparing metric variants."""
    labels = ['Unweighted', 'Frequency-weighted', 'Risk-weighted']
    recall = [
        metrics['recall'],
        metrics['freq_weighted_recall'],
        metrics['risk_weighted_recall'],
    ]
    precision = [
        metrics['precision'],
        metrics['freq_weighted_precision'],
        metrics['risk_weighted_precision'],
    ]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width/2, recall, width, label='Recall')
    ax.bar(x + width/2, precision, width, label='Precision')

    ax.set_ylabel('Score')
    ax.set_title('Metric Comparison: Unweighted vs Weighted')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha='right')
    ax.legend()
    ax.set_ylim(0, 1.0)
    ax.axhline(y=0.85, color='r', linestyle='--', label='85% threshold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
```

### Anti-Patterns to Avoid
- **Running transcription in CI:** Use pre-computed transcripts (no audio files in CI, no PHI risk, faster)
- **Hardcoded baseline constants:** Use JSON file so baselines can be updated with `pytest --force-regen`
- **Unconditional CI failures on weighted metrics:** Only unweighted recall should hard-fail (weighted metrics are observational)
- **Chart comparison without tolerance:** Matplotlib rendering varies slightly across platforms—use tolerance or skip visual regression

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Baseline storage/comparison | Custom JSON diff logic | pytest-regressions | Handles file I/O, diffs, regeneration automatically |
| CI artifact upload | Manual upload scripts | actions/upload-artifact@v4 | Standard GH Actions pattern, proper retention |
| Metric visualization | Custom plotting code | matplotlib with standard patterns | Already in deps, well-tested, simple API |
| Bootstrap CI calculation | Custom resampling | Existing `EvaluationMetrics.bootstrap_*_ci()` | Already implemented and tested |
| Confidence interval reporting | Manual formatting | Existing `generate_compliance_report()` | Already formats CI bounds correctly |

**Key insight:** The project already has 90% of validation infrastructure—integration validation is about orchestration, not reimplementation.

## Common Pitfalls

### Pitfall 1: PHI Exposure in CI Logs
**What goes wrong:** Running actual transcription in CI exposes PHI in logs
**Why it happens:** Temptation to use real audio files for "true" validation
**How to avoid:** Use pre-computed expected results JSON (transcripts without audio)
**Warning signs:** Audio files committed to repo, transcription step in CI workflow

### Pitfall 2: Flaky Chart Comparisons
**What goes wrong:** matplotlib charts differ slightly across platforms/versions
**Why it happens:** Floating-point rendering, font differences, DPI variations
**How to avoid:** Either skip visual regression (just generate charts) or use high tolerance
**Warning signs:** CI passes locally but fails in Actions, "image mismatch" errors

### Pitfall 3: Overly Strict Regression Thresholds
**What goes wrong:** CI fails on tiny acceptable metric variations (0.1% change)
**Why it happens:** Treating baselines as exact targets instead of floors
**How to avoid:** Use `>=` assertions with meaningful thresholds (85% floor), not exact equality
**Warning signs:** Frequent baseline updates, CI failures on minor code changes

### Pitfall 4: Missing Baseline Regeneration Workflow
**What goes wrong:** Baselines become stale, no clear process to update them
**Why it happens:** No documented workflow for intentional baseline updates
**How to avoid:** Document `pytest --force-regen` workflow, require explanation in PR description
**Warning signs:** Developers commenting out assertions, baseline drift

### Pitfall 5: CI Timeout on Full Validation
**What goes wrong:** 27-recording validation times out (10+ minutes)
**Why it happens:** Bootstrap CI calculation (10k iterations) is slow
**How to avoid:** Use tiered approach—smoke test on PR, full validation on main branch only
**Warning signs:** CI jobs timing out, developers skipping CI checks

## Code Examples

Verified patterns from official sources:

### Full Evaluation Integration Test
```python
# Source: pytest integration testing best practices
# tests/integration/test_full_evaluation.py
import pytest
from pathlib import Path
from tests.run_validation import run_validation, generate_compliance_report

def test_synthetic_dataset_evaluation():
    """End-to-end evaluation on synthetic dataset."""
    input_path = Path("tests/synthetic_handoffs.json")
    output_json = Path("tests/artifacts/validation_results.json")
    output_report = Path("tests/artifacts/VALIDATION_REPORT.md")

    # Run validation
    results = run_validation(
        input_path=input_path,
        n_bootstrap=10000,
        overlap_threshold=0.5,
        verbose=False,
    )

    # Generate report
    generate_compliance_report(results, output_report)

    # Assertions
    assert results["deployment_readiness"]["meets_threshold"], \
        "Deployment threshold not met"
    assert results["metrics"]["recall"] >= 0.85, \
        f"Recall below floor: {results['metrics']['recall']:.1%}"
    assert results["metrics"]["freq_weighted_recall"] >= results["metrics"]["risk_weighted_recall"], \
        "Expected frequency > risk recall pattern not observed"

    # Save results for artifacts
    output_json.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)

def test_validation_set_27_recordings():
    """Validation against 27 real handoff recordings (pre-computed)."""
    # Load pre-computed expected results (no audio processing in CI)
    expected_path = Path("tests/baselines/expected_results/validation_27_recordings.json")

    # This would load and compare against expected metrics
    # (Actual implementation depends on Phase 15 output format)
    assert expected_path.exists(), "Pre-computed validation results missing"
```

### Regression Baseline Testing
```python
# Source: pytest-regressions documentation
# tests/integration/test_regression.py
import pytest
from pathlib import Path
from tests.run_validation import run_validation

def test_metrics_do_not_regress(data_regression):
    """Ensure metrics don't regress from v2.1 baseline."""
    results = run_validation(
        input_path=Path("tests/synthetic_handoffs.json"),
        n_bootstrap=1000,  # Reduced for speed
        overlap_threshold=0.5,
        verbose=False,
    )

    # Round to avoid floating-point noise
    metrics_snapshot = {
        "recall": round(results["metrics"]["recall"], 4),
        "precision": round(results["metrics"]["precision"], 4),
        "f2": round(results["metrics"]["f2"], 4),
        "freq_weighted_recall": round(results["metrics"]["freq_weighted_recall"], 4),
        "risk_weighted_recall": round(results["metrics"]["risk_weighted_recall"], 4),
    }

    # First run: pytest --force-regen to create baseline
    # Subsequent runs: compare against baseline
    data_regression.check(metrics_snapshot)

def test_unweighted_recall_floor():
    """Hard requirement: unweighted recall >= 85%."""
    results = run_validation(
        input_path=Path("tests/synthetic_handoffs.json"),
        n_bootstrap=1000,
        overlap_threshold=0.5,
        verbose=False,
    )

    recall = results["metrics"]["recall"]
    assert recall >= 0.85, \
        f"REGRESSION: Unweighted recall {recall:.1%} below 85% floor"
```

### Metric Comparison Chart Generation
```python
# Source: matplotlib testing documentation
# tests/integration/generate_charts.py
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def generate_metric_comparison_chart(metrics: dict, output_path: Path):
    """Generate bar chart comparing unweighted vs weighted metrics."""
    labels = ['Unweighted\n(Safety Floor)', 'Frequency-weighted\n(Spoken)', 'Risk-weighted\n(Severity)']

    recall_values = [
        metrics['recall'],
        metrics.get('freq_weighted_recall', 0),
        metrics.get('risk_weighted_recall', 0),
    ]

    precision_values = [
        metrics['precision'],
        metrics.get('freq_weighted_precision', 0),
        metrics.get('risk_weighted_precision', 0),
    ]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 7))

    # Bars
    bars1 = ax.bar(x - width/2, recall_values, width, label='Recall', color='#2ecc71')
    bars2 = ax.bar(x + width/2, precision_values, width, label='Precision', color='#3498db')

    # Threshold line
    ax.axhline(y=0.85, color='#e74c3c', linestyle='--', linewidth=2, label='85% Threshold')

    # Labels and formatting
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('Metric Comparison: Unweighted vs Weighted', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.legend(fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.grid(axis='y', alpha=0.3)

    # Value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1%}',
                   ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return output_path
```

### GitHub Actions Workflow
```yaml
# Source: GitHub Actions CI patterns 2026
# .github/workflows/integration-validation.yml
name: Integration Validation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  smoke-test:
    name: Quick Validation (Smoke Test)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt -r requirements-dev.txt
          pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl

      - name: Run smoke test (10 handoffs)
        run: pytest tests/integration/test_smoke.py -v

      - name: Check regression baselines
        run: pytest tests/integration/test_regression.py -v

  full-validation:
    name: Full Validation (Main Branch Only)
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt -r requirements-dev.txt
          pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl

      - name: Run full evaluation
        run: pytest tests/integration/test_full_evaluation.py -v

      - name: Generate metric comparison chart
        run: python tests/integration/generate_charts.py

      - name: Upload validation report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: validation-report
          path: tests/artifacts/
          retention-days: 90
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual validation runs | CI-automated regression testing | ~2020-2022 | Catch regressions before merge |
| Hardcoded baseline constants | pytest-regressions JSON files | ~2019 | Easier baseline updates, version control |
| Visual inspection only | Automated chart generation | ~2021+ | Faster review, archived artifacts |
| Single metric validation | Multi-metric with divergence tracking | 2026 (this project) | Detect frequency/risk tradeoffs |

**Deprecated/outdated:**
- Manual CSV comparison for metrics (replaced by pytest-regressions JSON)
- Running full test suite on every commit (replaced by tiered smoke/full approach)
- Storing test data in databases (replaced by committed JSON fixtures)

## Open Questions

Things that couldn't be fully resolved:

1. **Pre-computed validation results format**
   - What we know: Need 27-recording validation without audio processing
   - What's unclear: Exact JSON schema for pre-computed expected results
   - Recommendation: Design schema in Phase 16 planning based on `run_validation.py` output format

2. **Divergence flagging threshold**
   - What we know: Flag "large" divergence between frequency/risk metrics
   - What's unclear: Exact percentage point threshold (5%? 10%? 15%?)
   - Recommendation: Start with 10 percentage points, tune based on observed patterns

3. **Weighted metric regression thresholds**
   - What we know: Unweighted recall floor is 85% (hard fail)
   - What's unclear: Should frequency/risk-weighted have separate floors?
   - Recommendation: Make weighted metrics observational (report but don't fail CI)—unweighted is safety floor

4. **Baseline storage location**
   - What we know: Either commit to repo or store as CI artifact
   - What's unclear: Which is better for this project?
   - Recommendation: Commit `tests/baselines/regression.json` to repo (easier review, version history)

5. **Chart visual regression**
   - What we know: matplotlib can do image comparison via pytest-mpl
   - What's unclear: Worth the maintenance burden?
   - Recommendation: Skip visual regression—just generate charts for review (simpler, no flakiness)

## Sources

### Primary (HIGH confidence)
- pytest integration testing best practices: [Good Integration Practices - pytest documentation](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
- pytest-regressions for baseline storage: [pytest-regressions documentation](https://pytest-regressions.readthedocs.io/en/latest/overview.html)
- matplotlib testing patterns: [Testing — Matplotlib documentation](https://matplotlib.org/stable/devel/testing.html)
- GitHub Actions CI patterns: [GitHub Actions Documentation](https://docs.github.com/en/actions)

### Secondary (MEDIUM confidence)
- [Integration Testing with pytest - Medium](https://medium.com/@ujwalabothe/integration-testing-with-pytest-testing-real-world-scenarios-c506f4bf1bff) - real-world integration test patterns
- [Automating Regression Testing with Cypress and GitHub Actions](https://www.longsight.com/blog/automating-regression-testing-with-cypress-and-github-actions/) - CI regression patterns
- [pytest-mpl plugin](https://github.com/matplotlib/pytest-mpl) - chart comparison (if needed)

### Tertiary (LOW confidence)
- WebSearch results on LLM CI/CD patterns - less relevant for PHI detection but validate general CI approach

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pytest, matplotlib, GitHub Actions all standard and already in project
- Architecture: HIGH - patterns verified from official documentation, match existing codebase structure
- Pitfalls: HIGH - common integration testing pitfalls well-documented, PHI-specific ones from project context

**Research date:** 2026-01-30
**Valid until:** 60 days (stable testing ecosystem, slow-changing patterns)

---

**Key Insight:** Integration validation is 90% orchestration of existing code (`run_validation.py`, `evaluate_presidio.py`, weighted metrics) plus 10% new infrastructure (pytest wrappers, baseline JSON, CI workflow). The dual-weighting validation pattern is novel but the underlying testing infrastructure is standard.
