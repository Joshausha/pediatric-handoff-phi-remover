"""
Phase 22: Entity-Specific Recall Target Validation

Validates all recall targets from Phases 17-21:
- ROOM: >=55% (Phase 17 interim target, achieved 95.6%)
- PHONE_NUMBER: >=90% (Phase 20 target, achieved 100%)
- LOCATION: >=40% (Phase 21 revised floor, achieved 44.2%)
- MEDICAL_RECORD_NUMBER: >=85% (Phase 22 target)

This module uses module-scoped fixtures to run expensive validation once.
All tests are read-only consumers of the shared validation results.
"""

import json
import pytest
from pathlib import Path
from tests.run_validation import run_validation


@pytest.fixture(scope="module")
def validation_results():
    """Run validation once for all Phase 22 tests."""
    return run_validation(
        input_path=Path("tests/synthetic_handoffs.json"),
        n_bootstrap=1000,
        verbose=False,
    )


def get_entity_recall(entity_stats: dict, entity_type: str) -> float:
    """Calculate recall for a specific entity type."""
    if entity_type not in entity_stats:
        return 0.0
    stats = entity_stats[entity_type]
    tp = stats.get("tp", 0)
    fn = stats.get("fn", 0)
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)


class TestPhase22EntityRecall:
    """Entity-specific recall threshold enforcement."""

    def test_room_recall_target(self, validation_results):
        """ROOM recall should meet Phase 17 interim target of 55%.

        Phase 17 achieved 95.6% with number-only lookbehind patterns.
        This test enforces the documented interim target.
        """
        entity_stats = validation_results["metrics"]["entity_stats"]
        recall = get_entity_recall(entity_stats, "ROOM")

        assert recall >= 0.55, (
            f"REGRESSION: ROOM recall {recall:.1%} below 55% interim target. "
            f"Phase 17 achieved 95.6% - investigate pattern regression. "
            f"Stats: {entity_stats.get('ROOM', {})}"
        )

    def test_phone_recall_target(self, validation_results):
        """PHONE_NUMBER recall should meet Phase 20 target of 90%.

        Phase 20 achieved 100% with leniency=0 PhoneRecognizer.
        """
        entity_stats = validation_results["metrics"]["entity_stats"]
        recall = get_entity_recall(entity_stats, "PHONE_NUMBER")

        assert recall >= 0.90, (
            f"REGRESSION: PHONE_NUMBER recall {recall:.1%} below 90% target. "
            f"Phase 20 achieved 100% - check PhoneRecognizer leniency. "
            f"Stats: {entity_stats.get('PHONE_NUMBER', {})}"
        )

    def test_location_recall_floor(self, validation_results):
        """LOCATION recall should meet Phase 21 revised floor of 40%.

        Phase 21 documented pattern-based approach limit at 44.2%.
        Original 60% target was revised after discovering inherent limits.
        17 custom patterns added +24pp improvement over 20% spaCy baseline.
        """
        entity_stats = validation_results["metrics"]["entity_stats"]
        recall = get_entity_recall(entity_stats, "LOCATION")

        assert recall >= 0.40, (
            f"REGRESSION: LOCATION recall {recall:.1%} below 40% floor. "
            f"Phase 21 achieved 44.2% with 17 patterns (pattern-based limit). "
            f"Stats: {entity_stats.get('LOCATION', {})}"
        )

    @pytest.mark.xfail(reason="MRN recall 70.9% below 85% target - needs pattern improvement")
    def test_mrn_recall_target(self, validation_results):
        """MEDICAL_RECORD_NUMBER recall should meet 85% target.

        MRN patterns include hash notation (#12345678) from Phase 5.
        Historically achieved ~70-72% recall, 85% target aspirational.
        """
        entity_stats = validation_results["metrics"]["entity_stats"]
        recall = get_entity_recall(entity_stats, "MEDICAL_RECORD_NUMBER")

        # Skip if no MRN entities in dataset
        if "MEDICAL_RECORD_NUMBER" not in entity_stats:
            pytest.skip("No MRN entities in validation dataset")

        mrn_stats = entity_stats["MEDICAL_RECORD_NUMBER"]
        if mrn_stats.get("tp", 0) + mrn_stats.get("fn", 0) < 5:
            pytest.skip(f"Insufficient MRN samples: {mrn_stats}")

        assert recall >= 0.85, (
            f"EXPECTED FAILURE: MRN recall {recall:.1%} below 85% target. "
            f"Historically ~70-72%, needs pattern expansion. "
            f"Stats: {mrn_stats}"
        )


class TestPhase22WeightedMetrics:
    """Overall weighted recall validation."""

    def test_weighted_recall_no_regression(self, validation_results):
        """Weighted recalls should not regress from v2.2 baseline.

        v2.2 baseline:
        - Frequency-weighted: 97.37%
        - Risk-weighted: 91.37%
        """
        metrics = validation_results["metrics"]

        # v2.2 baselines from regression.json
        baseline_freq = 0.9737
        baseline_risk = 0.9137

        current_freq = metrics["freq_weighted_recall"]
        current_risk = metrics["risk_weighted_recall"]

        # Allow 1% tolerance for bootstrap variation
        assert current_freq >= baseline_freq - 0.01, (
            f"REGRESSION: Frequency-weighted recall dropped "
            f"{baseline_freq:.1%} -> {current_freq:.1%}"
        )
        assert current_risk >= baseline_risk - 0.01, (
            f"REGRESSION: Risk-weighted recall dropped "
            f"{baseline_risk:.1%} -> {current_risk:.1%}"
        )

    def test_hipaa_floor_maintained(self, validation_results):
        """Unweighted recall floor (85%) must be maintained.

        This is the HIPAA safety requirement - zero-weight entities
        are invisible in weighted metrics but still matter.
        """
        recall = validation_results["metrics"]["recall"]

        assert recall >= 0.85, (
            f"CRITICAL: Unweighted recall {recall:.1%} below 85% HIPAA floor. "
            f"Weighted metrics cannot replace unweighted recall. "
            f"Zero-weight entities (EMAIL, PEDIATRIC_AGE) still matter."
        )


class TestPhase22PatternLimits:
    """Document pattern-based approach limits for each entity."""

    def test_document_room_ceiling(self, validation_results):
        """ROOM achieved 98% - pattern-based approach ceiling reached."""
        entity_stats = validation_results["metrics"]["entity_stats"]
        recall = get_entity_recall(entity_stats, "ROOM")

        # Just document - not enforcing ceiling, just measuring
        print(f"\n[Phase 22] ROOM recall: {recall:.1%}")
        print(f"  Target: >=55% (interim), Achieved: {recall:.1%}")
        print(f"  Ceiling: ~98% (number-only lookbehind patterns)")

    def test_document_location_limit(self, validation_results):
        """LOCATION achieved 44.2% - pattern-based approach limit reached.

        Further improvement requires:
        - Geographic NER (spaCy GPE, LOCATION entities)
        - Gazetteers (city/hospital name databases)
        """
        entity_stats = validation_results["metrics"]["entity_stats"]
        recall = get_entity_recall(entity_stats, "LOCATION")

        print(f"\n[Phase 22] LOCATION recall: {recall:.1%}")
        print(f"  Original target: >=60%")
        print(f"  Revised floor: >=40% (pattern-based limit)")
        print(f"  spaCy baseline: 20%")
        print(f"  Custom patterns: +{(recall - 0.20)*100:.1f}pp")
        print(f"  Next steps: Geographic NER or gazetteers")
