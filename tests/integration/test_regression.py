"""
Regression tests to detect metric changes between runs.

These tests protect against accidental regressions by comparing current
performance against committed baselines.

Key safety requirements:
- Unweighted recall must stay >= 85% (HIPAA compliance floor)
- Weighted metrics should remain stable (within tolerance)
"""

import json
import pytest
from pathlib import Path
from tests.run_validation import run_validation


@pytest.fixture(scope="module")
def validation_results():
    """Run validation once for all regression tests."""
    return run_validation(
        input_path=Path("tests/synthetic_handoffs.json"),
        n_bootstrap=1000,
        verbose=False,
    )


def test_unweighted_recall_floor(validation_results):
    """Test that unweighted recall stays above 85% HIPAA safety floor.

    This is the most critical safety requirement - weighted metrics cannot
    replace the unweighted recall floor. Zero-weight entities (like EMAIL_ADDRESS
    and PEDIATRIC_AGE) are invisible in weighted metrics but still matter for
    HIPAA compliance.
    """
    recall = validation_results["metrics"]["recall"]

    assert recall >= 0.85, (
        f"REGRESSION: Unweighted recall {recall:.1%} below 85% floor. "
        f"This violates HIPAA safety requirements. Weighted metrics show "
        f"freq={validation_results['metrics']['freq_weighted_recall']:.1%}, "
        f"risk={validation_results['metrics']['risk_weighted_recall']:.1%} "
        f"but unweighted recall is the compliance floor."
    )


def test_metrics_match_baseline():
    """Test that current metrics match committed baseline (within tolerance).

    This catches unintended regressions in:
    - Unweighted metrics (recall, precision, F2)
    - Frequency-weighted metrics
    - Risk-weighted metrics

    Tolerance: 1% relative change (allows minor variation from sampling/bootstrap)
    """
    baseline_path = Path("tests/baselines/regression.json")

    # Skip if baseline doesn't exist yet (first run)
    if not baseline_path.exists():
        pytest.skip("Baseline not yet established")

    # Load baseline
    with open(baseline_path) as f:
        baseline = json.load(f)

    # Run fresh validation
    results = run_validation(
        input_path=Path("tests/synthetic_handoffs.json"),
        n_bootstrap=1000,
        verbose=False,
    )
    current = results["metrics"]

    # Compare key metrics with 1% tolerance
    metrics_to_compare = [
        "recall",
        "precision",
        "f2",
        "freq_weighted_recall",
        "freq_weighted_precision",
        "freq_weighted_f2",
        "risk_weighted_recall",
        "risk_weighted_precision",
        "risk_weighted_f2",
    ]

    for metric_name in metrics_to_compare:
        if metric_name not in baseline:
            continue  # Skip if baseline doesn't have this metric yet

        baseline_value = baseline[metric_name]
        current_value = current[metric_name]

        assert current_value == pytest.approx(baseline_value, rel=0.01), (
            f"REGRESSION: {metric_name} changed from {baseline_value:.4f} "
            f"to {current_value:.4f} (>{1}% change). "
            f"If this is intentional, update baseline with: "
            f"python -c 'from tests.run_validation import run_validation; "
            f"from pathlib import Path; import json; "
            f"r = run_validation(Path(\"tests/synthetic_handoffs.json\"), n_bootstrap=1000, verbose=False); "
            f"b = {{k: round(v, 4) for k, v in r[\"metrics\"].items() if isinstance(v, (int, float))}}; "
            f"Path(\"tests/baselines/regression.json\").write_text(json.dumps(b, indent=2, sort_keys=True))'"
        )
