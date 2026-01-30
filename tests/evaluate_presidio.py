#!/usr/bin/env python
"""
Evaluate Presidio PHI detection against synthetic test dataset.

This script compares Presidio's detection output against ground truth
PHI spans to calculate precision, recall, and F1 scores.

CRITICAL: Recall must be 100% for PHI safety - any missed PHI is a leak.

Usage:
    python tests/evaluate_presidio.py
    python tests/evaluate_presidio.py --input tests/synthetic_handoffs.json --verbose
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Handle imports when run as script vs module
try:
    from tests.generate_test_data import SyntheticHandoff, PHISpan, load_dataset
except ImportError:
    from generate_test_data import SyntheticHandoff, PHISpan, load_dataset


@dataclass
class DetectionResult:
    """Result of a single PHI detection comparison."""
    handoff_id: int
    expected_spans: list[PHISpan]
    detected_spans: list[dict]  # Presidio results
    true_positives: list[PHISpan] = field(default_factory=list)
    false_negatives: list[PHISpan] = field(default_factory=list)  # CRITICAL - PHI leaks
    false_positives: list[dict] = field(default_factory=list)  # Over-redaction


@dataclass
class EvaluationMetrics:
    """Overall evaluation metrics."""
    total_expected: int = 0
    total_detected: int = 0
    true_positives: int = 0
    false_negatives: int = 0  # PHI leaks - must be 0
    false_positives: int = 0  # Over-redaction

    # Per-entity type tracking for weighted calculation
    entity_stats: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def precision(self) -> float:
        """Precision = TP / (TP + FP)"""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)

    @property
    def recall(self) -> float:
        """Recall = TP / (TP + FN) - MUST BE 100% for safety"""
        if self.total_expected == 0:
            return 1.0
        return self.true_positives / self.total_expected

    @property
    def f1(self) -> float:
        """F1 = 2 * (precision * recall) / (precision + recall)"""
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)

    @property
    def f2(self) -> float:
        """F2 score (recall-weighted): beta=2 emphasizes recall 2x precision.

        F2 = (1 + beta^2) * (precision * recall) / (beta^2 * precision + recall)
        where beta = 2
        """
        beta = 2.0
        if self.precision + self.recall == 0:
            return 0.0
        return (1 + beta**2) * (self.precision * self.recall) / (beta**2 * self.precision + self.recall)

    @property
    def is_safe(self) -> bool:
        """Safety check: no PHI leaks (100% recall)."""
        return self.false_negatives == 0

    def weighted_recall(self, weights: dict[str, float]) -> float:
        """Calculate recall weighted by spoken handoff frequency."""
        weighted_tp = 0.0
        weighted_total = 0.0
        for entity_type, stats in self.entity_stats.items():
            weight = weights.get(entity_type, 0.0)
            weighted_tp += stats["tp"] * weight
            weighted_total += (stats["tp"] + stats["fn"]) * weight
        return weighted_tp / weighted_total if weighted_total > 0 else 0.0

    def weighted_precision(self, weights: dict[str, float]) -> float:
        """Calculate precision weighted by spoken handoff frequency."""
        weighted_tp = 0.0
        weighted_detected = 0.0
        for entity_type, stats in self.entity_stats.items():
            weight = weights.get(entity_type, 0.0)
            weighted_tp += stats["tp"] * weight
            weighted_detected += (stats["tp"] + stats["fp"]) * weight
        return weighted_tp / weighted_detected if weighted_detected > 0 else 0.0

    def weighted_f2(self, weights: dict[str, float]) -> float:
        """Calculate F2 score weighted by spoken handoff frequency."""
        p = self.weighted_precision(weights)
        r = self.weighted_recall(weights)
        beta = 2.0
        if p + r == 0:
            return 0.0
        return (1 + beta**2) * (p * r) / (beta**2 * p + r)

    def risk_weighted_recall(self, risk_weights: dict[str, float]) -> float:
        """Calculate recall weighted by PHI leak severity/risk."""
        return self.weighted_recall(risk_weights)

    def risk_weighted_precision(self, risk_weights: dict[str, float]) -> float:
        """Calculate precision weighted by PHI leak severity/risk."""
        return self.weighted_precision(risk_weights)

    def risk_weighted_f2(self, risk_weights: dict[str, float]) -> float:
        """Calculate F2 score weighted by PHI leak severity/risk."""
        return self.weighted_f2(risk_weights)

    def bootstrap_recall_ci(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        n_bootstrap: int = 10000,
        confidence: float = 0.95,
        seed: int = 42
    ) -> Tuple[float, Tuple[float, float]]:
        """
        Calculate bootstrap CI for recall using percentile method.

        Args:
            y_true: Binary array (1 = PHI present, 0 = no PHI)
            y_pred: Binary array (1 = detected, 0 = not detected)
            n_bootstrap: Number of bootstrap iterations
            confidence: Confidence level (default 0.95)
            seed: Random seed for reproducibility

        Returns:
            Tuple of (point_estimate, (ci_lower, ci_upper))
        """
        np.random.seed(seed)
        n = len(y_true)
        recalls = []

        for _ in range(n_bootstrap):
            indices = np.random.choice(n, size=n, replace=True)
            y_true_boot = y_true[indices]
            y_pred_boot = y_pred[indices]

            tp = np.sum((y_true_boot == 1) & (y_pred_boot == 1))
            fn = np.sum((y_true_boot == 1) & (y_pred_boot == 0))
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            recalls.append(recall)

        alpha = 1 - confidence
        lower = np.percentile(recalls, 100 * alpha / 2)
        upper = np.percentile(recalls, 100 * (1 - alpha / 2))

        return np.mean(recalls), (lower, upper)

    def bootstrap_precision_ci(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        n_bootstrap: int = 10000,
        confidence: float = 0.95,
        seed: int = 42
    ) -> Tuple[float, Tuple[float, float]]:
        """Calculate bootstrap CI for precision."""
        np.random.seed(seed)
        n = len(y_true)
        precisions = []

        for _ in range(n_bootstrap):
            indices = np.random.choice(n, size=n, replace=True)
            y_true_boot = y_true[indices]
            y_pred_boot = y_pred[indices]

            tp = np.sum((y_true_boot == 1) & (y_pred_boot == 1))
            fp = np.sum((y_true_boot == 0) & (y_pred_boot == 1))
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            precisions.append(precision)

        alpha = 1 - confidence
        lower = np.percentile(precisions, 100 * alpha / 2)
        upper = np.percentile(precisions, 100 * (1 - alpha / 2))

        return np.mean(precisions), (lower, upper)


class PresidioEvaluator:
    """
    Evaluator for Presidio PHI detection accuracy.

    Compares Presidio output against ground truth spans using
    overlap-based matching.
    """

    # Mapping from ground truth types to Presidio types
    TYPE_MAPPING = {
        "PERSON": ["PERSON", "GUARDIAN_NAME"],
        "PHONE_NUMBER": ["PHONE_NUMBER"],
        "EMAIL_ADDRESS": ["EMAIL_ADDRESS"],
        "DATE_TIME": ["DATE_TIME"],
        "LOCATION": ["LOCATION"],
        "MEDICAL_RECORD_NUMBER": ["MEDICAL_RECORD_NUMBER"],
        "ROOM": ["ROOM"],
        "PEDIATRIC_AGE": ["PEDIATRIC_AGE"],
    }

    def __init__(self, overlap_threshold: float = 0.5):
        """
        Initialize evaluator.

        Args:
            overlap_threshold: Minimum overlap ratio to consider a match (0-1)
        """
        self.overlap_threshold = overlap_threshold
        self._analyzer = None
        self._anonymizer = None

    def _load_presidio(self):
        """Lazy load Presidio to avoid import overhead."""
        if self._analyzer is None:
            # Import here to avoid circular imports
            from app.deidentification import _get_engines
            self._analyzer, self._anonymizer = _get_engines()

    def _calculate_overlap(self, span1_start: int, span1_end: int,
                           span2_start: int, span2_end: int) -> float:
        """Calculate overlap ratio between two spans."""
        overlap_start = max(span1_start, span2_start)
        overlap_end = min(span1_end, span2_end)

        if overlap_start >= overlap_end:
            return 0.0

        overlap_length = overlap_end - overlap_start
        span1_length = span1_end - span1_start
        span2_length = span2_end - span2_start

        # Use Jaccard-like overlap: overlap / union
        union_length = span1_length + span2_length - overlap_length
        return overlap_length / union_length if union_length > 0 else 0.0

    def _types_match(self, expected_type: str, detected_type: str) -> bool:
        """Check if PHI types are compatible."""
        expected_variants = self.TYPE_MAPPING.get(expected_type, [expected_type])
        return detected_type in expected_variants

    def analyze_text(self, text: str) -> list[dict]:
        """
        Run Presidio analysis on text.

        Returns list of detected entities as dicts with start, end, entity_type.
        """
        self._load_presidio()

        from app.config import settings

        results = self._analyzer.analyze(
            text=text,
            language="en",
            entities=settings.phi_entities,
            score_threshold=settings.phi_score_threshold
        )

        # Filter out deny-listed terms
        filtered = []
        for result in results:
            detected_text = text[result.start:result.end].strip()

            if result.entity_type == "LOCATION" and detected_text.lower() in [w.lower() for w in settings.deny_list_location]:
                continue
            if result.entity_type == "PERSON" and detected_text.lower() in [w.lower() for w in settings.deny_list_person]:
                continue
            if result.entity_type == "GUARDIAN_NAME" and detected_text.lower() in [w.lower() for w in settings.deny_list_guardian_name]:
                continue
            if result.entity_type == "PEDIATRIC_AGE" and detected_text.lower() in [w.lower() for w in settings.deny_list_pediatric_age]:
                continue
            if result.entity_type == "DATE_TIME" and detected_text.lower() in [w.lower() for w in settings.deny_list_date_time]:
                continue

            filtered.append({
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score,
                "text": text[result.start:result.end],
            })

        return filtered

    def evaluate_handoff(self, handoff: SyntheticHandoff) -> DetectionResult:
        """
        Evaluate Presidio detection on a single handoff.

        Args:
            handoff: Synthetic handoff with ground truth spans

        Returns:
            DetectionResult with TP, FN, FP classifications
        """
        detected = self.analyze_text(handoff.text)

        result = DetectionResult(
            handoff_id=handoff.id,
            expected_spans=handoff.phi_spans,
            detected_spans=detected,
        )

        # Track which spans have been matched
        matched_expected = set()
        matched_detected = set()

        # Find matches using overlap
        for i, expected in enumerate(handoff.phi_spans):
            for j, det in enumerate(detected):
                if j in matched_detected:
                    continue

                # Check overlap
                overlap = self._calculate_overlap(
                    expected.start, expected.end,
                    det["start"], det["end"]
                )

                if overlap >= self.overlap_threshold:
                    # Check type compatibility
                    if self._types_match(expected.entity_type, det["entity_type"]):
                        result.true_positives.append(expected)
                        matched_expected.add(i)
                        matched_detected.add(j)
                        break

        # False negatives: expected but not detected (PHI LEAKS!)
        for i, expected in enumerate(handoff.phi_spans):
            if i not in matched_expected:
                result.false_negatives.append(expected)

        # False positives: detected but not expected (over-redaction)
        for j, det in enumerate(detected):
            if j not in matched_detected:
                result.false_positives.append(det)

        return result

    def evaluate_dataset(
        self,
        dataset: list[SyntheticHandoff],
        verbose: bool = False,
    ) -> tuple[EvaluationMetrics, list[DetectionResult]]:
        """
        Evaluate Presidio on entire dataset.

        Args:
            dataset: List of synthetic handoffs
            verbose: Print progress and details

        Returns:
            Tuple of (overall metrics, list of per-handoff results)
        """
        metrics = EvaluationMetrics()
        results = []

        if verbose:
            print(f"Evaluating {len(dataset)} handoffs...")

        for i, handoff in enumerate(dataset):
            if verbose and (i + 1) % 50 == 0:
                print(f"  Progress: {i + 1}/{len(dataset)}")

            result = self.evaluate_handoff(handoff)
            results.append(result)

            # Update metrics
            metrics.total_expected += len(handoff.phi_spans)
            metrics.total_detected += len(result.detected_spans)
            metrics.true_positives += len(result.true_positives)
            metrics.false_negatives += len(result.false_negatives)
            metrics.false_positives += len(result.false_positives)

        # Initialize entity stats tracking
        entity_stats = {}

        for result in results:
            for span in result.true_positives:
                entity_stats.setdefault(span.entity_type, {"tp": 0, "fn": 0, "fp": 0})
                entity_stats[span.entity_type]["tp"] += 1
            for span in result.false_negatives:
                entity_stats.setdefault(span.entity_type, {"tp": 0, "fn": 0, "fp": 0})
                entity_stats[span.entity_type]["fn"] += 1
            for det in result.false_positives:
                entity_stats.setdefault(det["entity_type"], {"tp": 0, "fn": 0, "fp": 0})
                entity_stats[det["entity_type"]]["fp"] += 1

        metrics.entity_stats = entity_stats

        # Build binary arrays for CI calculation
        y_true = []
        y_pred = []
        for result in results:
            for _ in result.true_positives:
                y_true.append(1)
                y_pred.append(1)
            for _ in result.false_negatives:
                y_true.append(1)
                y_pred.append(0)
            for _ in result.false_positives:
                y_true.append(0)
                y_pred.append(1)

        metrics._y_true = np.array(y_true)
        metrics._y_pred = np.array(y_pred)

        return metrics, results

    def generate_report(
        self,
        metrics: EvaluationMetrics,
        results: list[DetectionResult],
        show_failures: bool = True,
        weighted: bool = False,
    ) -> str:
        """
        Generate evaluation report.

        Args:
            metrics: Overall metrics
            results: Per-handoff results
            show_failures: Include details of missed PHI

        Returns:
            Formatted report string
        """
        lines = [
            "=" * 60,
            "PRESIDIO PHI DETECTION EVALUATION REPORT",
            "=" * 60,
            "",
            "OVERALL METRICS:",
            f"  Total expected PHI spans: {metrics.total_expected}",
            f"  Total detected spans:     {metrics.total_detected}",
            f"  True positives:           {metrics.true_positives}",
            f"  False negatives (LEAKS):  {metrics.false_negatives}",
            f"  False positives:          {metrics.false_positives}",
            "",
            f"  Precision: {metrics.precision:.1%}",
            f"  Recall:    {metrics.recall:.1%}",
            f"  F1 Score:  {metrics.f1:.1%}",
            f"  F2 Score:  {metrics.f2:.1%}  ← PRIMARY METRIC (recall-weighted)",
            "",
        ]

        # Add confidence intervals if available
        if hasattr(metrics, '_y_true') and len(metrics._y_true) > 0:
            recall_mean, (recall_lower, recall_upper) = metrics.bootstrap_recall_ci(
                metrics._y_true, metrics._y_pred
            )
            prec_mean, (prec_lower, prec_upper) = metrics.bootstrap_precision_ci(
                metrics._y_true, metrics._y_pred
            )
            lines.append("CONFIDENCE INTERVALS (95%, bootstrap n=10,000):")
            lines.append(f"  Recall:    [{recall_lower:.1%}, {recall_upper:.1%}]")
            lines.append(f"  Precision: [{prec_lower:.1%}, {prec_upper:.1%}]")
            lines.append("")

        # Add weighted metrics if requested
        if weighted:
            from app.config import settings
            freq_weights = settings.spoken_handoff_weights
            risk_weights = settings.spoken_handoff_risk_weights

            lines.append("METRIC SUMMARY:")
            lines.append("")
            lines.append("                            Recall  Precision    F2")
            lines.append("  --------------------------------------------------")
            lines.append(f"  Unweighted (Safety Floor)  {metrics.recall:.1%}     {metrics.precision:.1%}  {metrics.f2:.1%}")
            lines.append(f"  Frequency-weighted         {metrics.weighted_recall(freq_weights):.1%}     {metrics.weighted_precision(freq_weights):.1%}  {metrics.weighted_f2(freq_weights):.1%}")
            lines.append(f"  Risk-weighted              {metrics.risk_weighted_recall(risk_weights):.1%}     {metrics.risk_weighted_precision(risk_weights):.1%}  {metrics.risk_weighted_f2(risk_weights):.1%}")
            lines.append("")

            # Side-by-side weight comparison tables
            lines.append("WEIGHT COMPARISON:")
            lines.append("")

            # Build sorted lists for both weight schemes
            freq_sorted = sorted(freq_weights.items(), key=lambda x: (-x[1], x[0]))
            risk_sorted = sorted(risk_weights.items(), key=lambda x: (-x[1], x[0]))

            # Mark entities with divergence >2.0
            divergent = set()
            for entity in freq_weights.keys():
                freq = freq_weights.get(entity, 0.0)
                risk = risk_weights.get(entity, 0.0)
                if abs(freq - risk) > 2.0:
                    divergent.add(entity)

            lines.append("  Frequency (How Often Spoken)      Risk (Severity If Leaked)")
            lines.append("  --------------------------        -------------------------")

            # Display side-by-side (pad to equal length)
            max_len = max(len(freq_sorted), len(risk_sorted))
            for i in range(max_len):
                left_entity = freq_sorted[i][0] if i < len(freq_sorted) else ""
                left_weight = freq_sorted[i][1] if i < len(freq_sorted) else 0.0
                left_marker = "* " if left_entity in divergent else "  "

                right_entity = risk_sorted[i][0] if i < len(risk_sorted) else ""
                right_weight = risk_sorted[i][1] if i < len(risk_sorted) else 0.0
                right_marker = "* " if right_entity in divergent else "  "

                left_str = f"{left_marker}{left_entity:<24} {left_weight:>4.1f}" if left_entity else " " * 32
                right_str = f"{right_marker}{right_entity:<24} {right_weight:>4.1f}" if right_entity else ""

                lines.append(f"{left_str}      {right_str}")

            lines.append("")
            lines.append("* = Weight divergence >2.0 between frequency and risk")
            lines.append("")

            # Zero-weight entity note
            zero_weight = [entity for entity, weight in freq_weights.items() if weight == 0.0]
            if zero_weight:
                lines.append("NOTE: Zero-weight entities")
                for entity in sorted(zero_weight):
                    if entity == "EMAIL_ADDRESS":
                        lines.append(f"  {entity} (0.0): Never spoken in verbal handoffs")
                    elif entity == "PEDIATRIC_AGE":
                        lines.append(f"  {entity} (0.0): Not PHI under HIPAA unless age 90+")
                    else:
                        lines.append(f"  {entity} (0.0): Zero weight in both schemes")
                lines.append("  These entities count in unweighted metrics but are excluded from weighted calculations.")
                lines.append("")

            # Metric divergence explanation
            freq_recall = metrics.weighted_recall(freq_weights)
            risk_recall = metrics.risk_weighted_recall(risk_weights)
            gap = freq_recall - risk_recall

            lines.append("METRIC DIVERGENCE EXPLANATION:")
            lines.append("")
            lines.append(f"  Frequency-weighted recall: {freq_recall:.1%}")
            lines.append(f"  Risk-weighted recall:      {risk_recall:.1%}")
            lines.append(f"  Gap: {gap:+.1%} percentage points")
            lines.append("")
            lines.append("  Why they differ:")
            lines.append("  - MEDICAL_RECORD_NUMBER has low frequency weight (0.5) but high risk weight (5.0)")
            lines.append("  - When MRN detection underperforms, frequency recall stays high")
            lines.append("    (dominated by PERSON with weight 5.0)")
            lines.append("  - But risk-weighted recall drops significantly")
            lines.append("    (MRN and PERSON have equal weight, MRN drags down average)")
            lines.append("")
            lines.append("  Guidance:")
            lines.append("  - Unweighted recall is your HIPAA compliance floor (all entities equal)")
            lines.append("  - Frequency-weighted reflects operational reality (what's actually spoken)")
            lines.append("  - Risk-weighted highlights critical vulnerabilities (severity if leaked)")
            lines.append("")

        # Safety check
        if metrics.is_safe:
            lines.append("✅ SAFETY CHECK: PASSED (100% recall, no PHI leaks)")
        else:
            lines.append("❌ SAFETY CHECK: FAILED - PHI LEAKS DETECTED!")
            lines.append(f"   {metrics.false_negatives} PHI spans were NOT detected!")

        lines.append("")

        # Type breakdown
        type_stats = {}
        for result in results:
            for span in result.true_positives:
                key = span.entity_type
                type_stats.setdefault(key, {"tp": 0, "fn": 0, "fp": 0})
                type_stats[key]["tp"] += 1
            for span in result.false_negatives:
                key = span.entity_type
                type_stats.setdefault(key, {"tp": 0, "fn": 0, "fp": 0})
                type_stats[key]["fn"] += 1
            for det in result.false_positives:
                key = det["entity_type"]
                type_stats.setdefault(key, {"tp": 0, "fn": 0, "fp": 0})
                type_stats[key]["fp"] += 1

        lines.append("PER-TYPE PERFORMANCE:")
        for phi_type, stats in sorted(type_stats.items()):
            tp, fn, fp = stats["tp"], stats["fn"], stats["fp"]
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            f2 = 5 * precision * recall / (4 * precision + recall) if (4 * precision + recall) > 0 else 0.0
            status = "✅" if fn == 0 else "❌"
            lines.append(f"  {status} {phi_type}: P={precision:.0%} R={recall:.0%} F1={f1:.0%} F2={f2:.0%}")

        lines.append("")

        # Show failure details
        if show_failures and metrics.false_negatives > 0:
            lines.append("MISSED PHI DETAILS (CRITICAL):")
            lines.append("-" * 40)

            for result in results:
                if result.false_negatives:
                    lines.append(f"Handoff #{result.handoff_id}:")
                    for span in result.false_negatives:
                        lines.append(f"  MISSED: {span.entity_type} '{span.text}' at [{span.start}:{span.end}]")

            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Presidio PHI detection against synthetic dataset"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("tests/synthetic_handoffs.json"),
        help="Input dataset file (default: tests/synthetic_handoffs.json)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output report file (optional, defaults to stdout)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show progress during evaluation"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--overlap",
        type=float,
        default=0.5,
        help="Overlap threshold for span matching (default: 0.5)"
    )
    parser.add_argument(
        "--export-confusion-matrix",
        type=Path,
        help="Export per-entity confusion matrix to JSON file"
    )
    parser.add_argument(
        "--with-ci",
        action="store_true",
        help="Calculate bootstrap 95%% confidence intervals (slower)"
    )
    parser.add_argument(
        "--weighted",
        action="store_true",
        help="Report weighted metrics using spoken handoff relevance weights"
    )

    args = parser.parse_args()

    # Check input exists
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        print("Run generate_test_data.py first to create the dataset.")
        sys.exit(1)

    # Load dataset
    print(f"Loading dataset from {args.input}...")
    dataset = load_dataset(args.input)
    print(f"Loaded {len(dataset)} handoffs")

    # Evaluate
    evaluator = PresidioEvaluator(overlap_threshold=args.overlap)
    metrics, results = evaluator.evaluate_dataset(dataset, verbose=args.verbose)

    # Calculate confidence intervals if requested
    if not args.with_ci and hasattr(metrics, '_y_true'):
        # Remove CI data if not requested to save memory
        delattr(metrics, '_y_true')
        delattr(metrics, '_y_pred')

    # Export confusion matrix if requested
    if args.export_confusion_matrix:
        # Build per-entity confusion matrix
        confusion = {}
        for result in results:
            for span in result.true_positives:
                confusion.setdefault(span.entity_type, {"tp": 0, "fn": 0, "fp": 0})
                confusion[span.entity_type]["tp"] += 1
            for span in result.false_negatives:
                confusion.setdefault(span.entity_type, {"tp": 0, "fn": 0, "fp": 0})
                confusion[span.entity_type]["fn"] += 1
            for det in result.false_positives:
                confusion.setdefault(det["entity_type"], {"tp": 0, "fn": 0, "fp": 0})
                confusion[det["entity_type"]]["fp"] += 1

        # Calculate metrics per entity
        for entity_type, counts in confusion.items():
            tp, fn, fp = counts["tp"], counts["fn"], counts["fp"]
            counts["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            counts["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            p, r = counts["precision"], counts["recall"]
            counts["f1"] = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
            counts["f2"] = 5 * p * r / (4 * p + r) if (4 * p + r) > 0 else 0.0

        args.export_confusion_matrix.parent.mkdir(parents=True, exist_ok=True)
        with open(args.export_confusion_matrix, "w") as f:
            json.dump(confusion, f, indent=2)
        print(f"Confusion matrix exported to {args.export_confusion_matrix}")

    if args.json:
        # JSON output
        output = {
            "metrics": {
                "total_expected": metrics.total_expected,
                "total_detected": metrics.total_detected,
                "true_positives": metrics.true_positives,
                "false_negatives": metrics.false_negatives,
                "false_positives": metrics.false_positives,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1": metrics.f1,
                "f2": metrics.f2,
                "is_safe": metrics.is_safe,
            },
            "failures": [
                {
                    "handoff_id": r.handoff_id,
                    "missed": [
                        {"type": s.entity_type, "text": s.text, "start": s.start, "end": s.end}
                        for s in r.false_negatives
                    ]
                }
                for r in results if r.false_negatives
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        # Text report
        report = evaluator.generate_report(metrics, results, weighted=args.weighted)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)

    # Exit with error if PHI leaks detected
    if not metrics.is_safe:
        sys.exit(1)


if __name__ == "__main__":
    main()
