"""
Tests for weighted metrics in evaluation.

Run with: pytest tests/test_weighted_metrics.py -v
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.evaluate_presidio import EvaluationMetrics
from app.config import settings


class TestWeightedMetrics:
    """Test weighted metrics calculations."""

    def test_weighted_recall_matches_analysis(self):
        """
        Verify weighted recall calculation matches manual verification in SPOKEN_HANDOFF_ANALYSIS.md.

        Expected weighted recall: ~91.5% (from appendix calculations)
        """
        # From SPOKEN_HANDOFF_ANALYSIS.md appendix (actual values from synthetic dataset)
        entity_stats = {
            "PERSON": {"tp": 747, "fn": 9, "fp": 79},
            "ROOM": {"tp": 31, "fn": 59, "fp": 24},
            "PHONE_NUMBER": {"tp": 142, "fn": 50, "fp": 1},
            "DATE_TIME": {"tp": 184, "fn": 6, "fp": 334},
            "MEDICAL_RECORD_NUMBER": {"tp": 90, "fn": 37, "fp": 12},
            "EMAIL_ADDRESS": {"tp": 24, "fn": 0, "fp": 0},
            "LOCATION": {"tp": 25, "fn": 104, "fp": 6},
            "PEDIATRIC_AGE": {"tp": 60, "fn": 104, "fp": 9},
        }

        weights = settings.spoken_handoff_weights

        # Create metrics object and populate entity_stats
        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        # Calculate weighted recall
        weighted_recall = metrics.weighted_recall(weights)

        # Manual calculation for verification
        weighted_tp = sum(stats["tp"] * weights.get(e, 0) for e, stats in entity_stats.items())
        weighted_total = sum((stats["tp"] + stats["fn"]) * weights.get(e, 0) for e, stats in entity_stats.items())
        expected_recall = weighted_tp / weighted_total

        # Should match ~91.5% (within rounding tolerance)
        assert abs(weighted_recall - 0.915) < 0.01, \
            f"Weighted recall {weighted_recall:.1%} doesn't match expected ~91.5%"

        # Verify manual calculation matches method
        assert abs(weighted_recall - expected_recall) < 0.001, \
            "Method calculation differs from manual calculation"

    def test_weighted_precision_calculation(self):
        """Test weighted precision calculation."""
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

        weighted_precision = metrics.weighted_precision(weights)

        # Manual calculation
        # PERSON: tp=100*5=500, detected=120*5=600
        # ROOM: tp=50*4=200, detected=60*4=240
        # weighted_tp = 500 + 200 = 700
        # weighted_detected = 600 + 240 = 840
        # precision = 700/840 = 0.833...
        expected_precision = 700 / 840

        assert abs(weighted_precision - expected_precision) < 0.001

    def test_weighted_f2_calculation(self):
        """Test weighted F2 score calculation."""
        entity_stats = {
            "PERSON": {"tp": 100, "fn": 10, "fp": 20},
        }

        weights = {"PERSON": 5.0}

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        weighted_f2 = metrics.weighted_f2(weights)

        # Manual calculation
        # precision = 100/120 = 0.833...
        # recall = 100/110 = 0.909...
        # F2 = (1 + 4) * (p * r) / (4 * p + r)
        p = 100 / 120
        r = 100 / 110
        beta = 2.0
        expected_f2 = (1 + beta**2) * (p * r) / (beta**2 * p + r)

        assert abs(weighted_f2 - expected_f2) < 0.001

    def test_weighted_metrics_zero_weight_entities_ignored(self):
        """Test that zero-weight entities don't affect weighted metrics."""
        entity_stats = {
            "PERSON": {"tp": 100, "fn": 10, "fp": 20},
            "EMAIL_ADDRESS": {"tp": 50, "fn": 0, "fp": 0},  # Weight 0
        }

        weights = {
            "PERSON": 5.0,
            "EMAIL_ADDRESS": 0.0,
        }

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        weighted_recall = metrics.weighted_recall(weights)

        # Only PERSON should count
        # recall = 100 / 110 = 0.909...
        expected_recall = 100 / 110

        assert abs(weighted_recall - expected_recall) < 0.001

    def test_weighted_metrics_empty_stats(self):
        """Test weighted metrics with empty entity stats."""
        metrics = EvaluationMetrics()
        metrics.entity_stats = {}

        weights = settings.spoken_handoff_weights

        assert metrics.weighted_recall(weights) == 0.0
        assert metrics.weighted_precision(weights) == 0.0
        assert metrics.weighted_f2(weights) == 0.0

    def test_weighted_metrics_unknown_entity_type(self):
        """Test that unknown entity types get weight 0."""
        entity_stats = {
            "UNKNOWN_ENTITY": {"tp": 100, "fn": 10, "fp": 20},
        }

        weights = {
            "PERSON": 5,
            # UNKNOWN_ENTITY not in weights
        }

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        # Unknown entity should be ignored (weight 0)
        assert metrics.weighted_recall(weights) == 0.0
        assert metrics.weighted_precision(weights) == 0.0

    def test_weighted_recall_higher_than_unweighted(self):
        """
        Test that weighted recall is higher than unweighted when low-performing
        entities have low weights (as expected from analysis).
        """
        # Simulate scenario where high-weight entities perform well
        # but low-weight entities perform poorly
        entity_stats = {
            "PERSON": {"tp": 100, "fn": 5, "fp": 10},      # 95% recall, weight 5
            "ROOM": {"tp": 30, "fn": 70, "fp": 10},        # 30% recall, weight 4
            "EMAIL_ADDRESS": {"tp": 10, "fn": 90, "fp": 0},  # 10% recall, weight 0
        }

        weights = {
            "PERSON": 5,
            "ROOM": 4,
            "EMAIL_ADDRESS": 0,
        }

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        # Calculate unweighted recall
        total_tp = 100 + 30 + 10
        total_fn = 5 + 70 + 90
        unweighted_recall = total_tp / (total_tp + total_fn)

        # Calculate weighted recall
        weighted_recall = metrics.weighted_recall(weights)

        # Weighted should be higher (EMAIL_ADDRESS with 10% recall gets weight 0)
        assert weighted_recall > unweighted_recall, \
            "Weighted recall should be higher when low-performing entities have low weights"


class TestWeightConfiguration:
    """Test weight configuration from settings."""

    def test_weights_loaded_from_config(self):
        """Test that weights are properly loaded from config."""
        weights = settings.spoken_handoff_weights

        # Verify all expected entities have weights
        expected_entities = [
            "PERSON",
            "GUARDIAN_NAME",
            "ROOM",
            "PHONE_NUMBER",
            "DATE_TIME",
            "MEDICAL_RECORD_NUMBER",
            "EMAIL_ADDRESS",
            "LOCATION",
            "PEDIATRIC_AGE",
        ]

        for entity in expected_entities:
            assert entity in weights, f"{entity} missing from weights config"

    def test_weight_values_in_valid_range(self):
        """Test that all weights are non-negative floats in valid range."""
        weights = settings.spoken_handoff_weights

        for entity, weight in weights.items():
            assert isinstance(weight, (int, float)), f"{entity} weight is not numeric"
            assert weight >= 0.0, f"{entity} weight is negative"
            assert weight <= 5.0, f"{entity} weight exceeds maximum of 5"

    def test_critical_entities_have_high_weights(self):
        """Test that frequently spoken entities have high weights (>=4.0)."""
        weights = settings.spoken_handoff_weights

        # PERSON should have highest weight (5.0 - constantly spoken)
        assert weights["PERSON"] == pytest.approx(5.0), "PERSON should have weight 5.0 (critical)"

        # GUARDIAN_NAME and ROOM should have high weights (4.0 - commonly spoken)
        assert weights["GUARDIAN_NAME"] == pytest.approx(4.0), "GUARDIAN_NAME should have weight 4.0 (high)"
        assert weights["ROOM"] == pytest.approx(4.0), "ROOM should have weight 4.0 (high)"

    def test_rarely_or_never_spoken_entities_have_low_weights(self):
        """Test that rarely/never-spoken entities have low weights (<=0.5).

        EMAIL_ADDRESS (0.0) and PEDIATRIC_AGE (0.0) are never spoken.
        LOCATION (0.5) is rarely spoken but possible ("transferred from Memorial").
        """
        weights = settings.spoken_handoff_weights

        # EMAIL_ADDRESS never spoken in handoffs (weight 0.0)
        assert weights["EMAIL_ADDRESS"] == pytest.approx(0.0), "EMAIL_ADDRESS should have weight 0.0"

        # PEDIATRIC_AGE not PHI under HIPAA (weight 0.0)
        assert weights["PEDIATRIC_AGE"] == pytest.approx(0.0), "PEDIATRIC_AGE should have weight 0.0"

        # LOCATION rarely spoken but possible (weight 0.5)
        assert weights["LOCATION"] == pytest.approx(0.5), "LOCATION should have weight 0.5"


class TestRiskWeightedMetrics:
    """Test risk-weighted metrics calculations (severity if leaked)."""

    def test_risk_weighted_recall_calculation(self):
        """Test risk-weighted recall with HIPAA severity weights."""
        entity_stats = {
            "MEDICAL_RECORD_NUMBER": {"tp": 70, "fn": 30, "fp": 10},  # 70% recall, risk=5.0
            "PERSON": {"tp": 95, "fn": 5, "fp": 10},                  # 95% recall, risk=5.0
        }

        risk_weights = {
            "MEDICAL_RECORD_NUMBER": 5.0,
            "PERSON": 5.0,
        }

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
            "PHONE_NUMBER": {"tp": 80, "fn": 20, "fp": 20},  # 80% precision, risk=4.0
            "LOCATION": {"tp": 60, "fn": 40, "fp": 15},      # 80% precision, risk=4.0
        }

        risk_weights = {
            "PHONE_NUMBER": 4.0,
            "LOCATION": 4.0,
        }

        metrics = EvaluationMetrics()
        metrics.entity_stats = entity_stats

        risk_precision = metrics.risk_weighted_precision(risk_weights)

        # Manual calculation:
        # PHONE: tp=80*4=320, detected=100*4=400
        # LOCATION: tp=60*4=240, detected=75*4=300
        # precision = (320+240)/(400+300) = 560/700 = 0.8
        expected_precision = 560 / 700

        assert risk_precision == pytest.approx(expected_precision)

    def test_risk_weighted_f2_calculation(self):
        """Test risk-weighted F2 score (recall-weighted)."""
        entity_stats = {
            "GUARDIAN_NAME": {"tp": 85, "fn": 15, "fp": 10},  # risk=4.0
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

    def test_risk_weights_loaded_from_config(self):
        """Test that risk weights are properly loaded from config."""
        risk_weights = settings.spoken_handoff_risk_weights

        # Verify all expected entities have risk weights
        expected_entities = [
            "PERSON",
            "GUARDIAN_NAME",
            "ROOM",
            "PHONE_NUMBER",
            "DATE_TIME",
            "MEDICAL_RECORD_NUMBER",
            "EMAIL_ADDRESS",
            "LOCATION",
            "PEDIATRIC_AGE",
        ]

        for entity in expected_entities:
            assert entity in risk_weights, f"{entity} missing from risk weights config"

    def test_risk_weight_values_in_valid_range(self):
        """Test that all risk weights are non-negative floats in valid range."""
        risk_weights = settings.spoken_handoff_risk_weights

        for entity, weight in risk_weights.items():
            assert isinstance(weight, (int, float)), f"{entity} risk weight is not numeric"
            assert weight >= 0.0, f"{entity} risk weight is negative"
            assert weight <= 5.0, f"{entity} risk weight exceeds maximum of 5"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
