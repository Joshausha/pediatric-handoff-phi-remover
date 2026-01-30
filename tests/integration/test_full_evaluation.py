"""
Integration tests for full end-to-end validation.

Tests the complete evaluation pipeline:
- run_validation() orchestration
- Three metric types calculated (unweighted, frequency-weighted, risk-weighted)
- Config weights properly loaded
- Dual-weight framework functioning

This module runs the full validation once and shares results across tests for efficiency.
"""

import pytest
from pathlib import Path
from tests.run_validation import run_validation
from app.config import settings


@pytest.fixture(scope="module")
def validation_results():
    """Run validation once for all tests in module."""
    return run_validation(
        input_path=Path("tests/synthetic_handoffs.json"),
        n_bootstrap=1000,  # Reduced for speed
        verbose=False,
    )


def test_synthetic_dataset_evaluation(validation_results):
    """Test that validation runs and meets minimum quality thresholds.

    This is the HIPAA safety floor - unweighted recall must be >=85% for deployment.
    """
    metrics = validation_results["metrics"]

    # HARD FAIL: Unweighted recall floor (HIPAA compliance requirement)
    assert metrics["recall"] >= 0.85, (
        f"REGRESSION: Unweighted recall {metrics['recall']:.1%} below 85% floor. "
        f"This is the HIPAA safety requirement - weighted metrics cannot replace it."
    )

    # Verify all three metric types present
    assert "recall" in metrics, "Unweighted recall missing"
    assert "freq_weighted_recall" in metrics, "Frequency-weighted recall missing"
    assert "risk_weighted_recall" in metrics, "Risk-weighted recall missing"

    # Verify all metrics are float type
    assert isinstance(metrics["recall"], float)
    assert isinstance(metrics["freq_weighted_recall"], float)
    assert isinstance(metrics["risk_weighted_recall"], float)


def test_three_metrics_calculated(validation_results):
    """Test that all three metric types are calculated.

    Dual-weighting framework provides three complementary views:
    1. Unweighted: HIPAA safety floor (equal weight to all PHI types)
    2. Frequency-weighted: Spoken prevalence (matches clinical reality)
    3. Risk-weighted: Leak severity (prioritizes identifying PHI)

    NOTE: We observe divergence but do not enforce it as a hard requirement.
    The dual-weight framework is designed to provide different perspectives,
    but similar weights may legitimately produce similar metrics.

    See: SPOKEN_HANDOFF_ANALYSIS.md for methodology.
    """
    metrics = validation_results["metrics"]

    # All three recalls must exist
    recall_unweighted = metrics["recall"]
    recall_freq = metrics["freq_weighted_recall"]
    recall_risk = metrics["risk_weighted_recall"]

    assert recall_unweighted > 0, "Unweighted recall should be non-zero"
    assert recall_freq > 0, "Frequency-weighted recall should be non-zero"
    assert recall_risk > 0, "Risk-weighted recall should be non-zero"

    # Same for precision
    assert "precision" in metrics
    assert "freq_weighted_precision" in metrics
    assert "risk_weighted_precision" in metrics

    # Same for F2
    assert "f2" in metrics
    assert "freq_weighted_f2" in metrics
    assert "risk_weighted_f2" in metrics


def test_config_weights_loaded():
    """Test that pydantic settings correctly load both weight schemes.

    This validates requirements CONF-01, CONF-02, CONF-03:
    - CONF-01: spoken_handoff_weights (frequency) exists
    - CONF-02: spoken_handoff_risk_weights exists
    - CONF-03: Both cover same entity types
    """
    # CONF-01: Frequency weights loaded
    assert hasattr(settings, "spoken_handoff_weights")
    assert isinstance(settings.spoken_handoff_weights, dict)
    assert len(settings.spoken_handoff_weights) > 0

    # All weights should be float type
    for entity_type, weight in settings.spoken_handoff_weights.items():
        assert isinstance(weight, (int, float)), f"{entity_type} weight is not numeric"

    # CONF-02: Risk weights loaded
    assert hasattr(settings, "spoken_handoff_risk_weights")
    assert isinstance(settings.spoken_handoff_risk_weights, dict)
    assert len(settings.spoken_handoff_risk_weights) > 0

    # All risk weights should be float type
    for entity_type, weight in settings.spoken_handoff_risk_weights.items():
        assert isinstance(weight, (int, float)), f"{entity_type} risk weight is not numeric"

    # CONF-03: Both dicts cover same entity types
    freq_entities = set(settings.spoken_handoff_weights.keys())
    risk_entities = set(settings.spoken_handoff_risk_weights.keys())

    assert freq_entities == risk_entities, (
        f"Weight scheme mismatch. "
        f"Frequency-only: {freq_entities - risk_entities}, "
        f"Risk-only: {risk_entities - freq_entities}"
    )


def test_entity_stats_provided(validation_results):
    """Test that entity_stats are included in results for weighted calculation."""
    metrics = validation_results["metrics"]

    assert "entity_stats" in metrics, "entity_stats missing from results"
    assert isinstance(metrics["entity_stats"], dict)

    # Each entity should have tp, fn, fp counts
    for entity_type, stats in metrics["entity_stats"].items():
        assert "tp" in stats, f"{entity_type} missing tp count"
        assert "fn" in stats, f"{entity_type} missing fn count"
        assert "fp" in stats, f"{entity_type} missing fp count"

        # All should be non-negative integers
        assert stats["tp"] >= 0
        assert stats["fn"] >= 0
        assert stats["fp"] >= 0
