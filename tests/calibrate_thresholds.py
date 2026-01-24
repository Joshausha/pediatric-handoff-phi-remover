#!/usr/bin/env python
"""
Threshold calibration script for per-entity PHI detection optimization.

Generates precision-recall curves and identifies optimal thresholds for all
entity types using F2 optimization with a configurable recall floor.

Usage:
    python tests/calibrate_thresholds.py --verbose
    python tests/calibrate_thresholds.py --recall-floor 0.90 --output-dir tests/results
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Handle imports when run as script vs module
try:
    from tests.generate_test_data import SyntheticHandoff, PHISpan, load_dataset
    from tests.evaluate_presidio import PresidioEvaluator, EvaluationMetrics
except ImportError:
    from generate_test_data import SyntheticHandoff, PHISpan, load_dataset
    from evaluate_presidio import PresidioEvaluator, EvaluationMetrics


@dataclass
class ThresholdResult:
    """Result of evaluating a single threshold for an entity type."""
    threshold: float
    precision: float
    recall: float
    f1: float
    f2: float
    tp: int
    fn: int
    fp: int
    meets_recall_floor: bool


@dataclass
class EntityCalibrationResult:
    """Complete calibration result for a single entity type."""
    entity_type: str
    optimal_threshold: float
    metrics: dict
    rationale: str
    sweep_results: list[ThresholdResult]
    pr_curve_data: dict = field(default_factory=dict)


class ThresholdCalibrator:
    """
    Calibrator for per-entity confidence score thresholds.

    Uses precision-recall curve analysis to find optimal thresholds
    that maximize F2 score while maintaining a recall floor.
    """

    # Entity types to calibrate (matches evaluate_presidio.py TYPE_MAPPING)
    ENTITY_TYPES = [
        "PERSON",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "DATE_TIME",
        "LOCATION",
        "MEDICAL_RECORD_NUMBER",
        "ROOM",
        "PEDIATRIC_AGE",
    ]

    def __init__(
        self,
        recall_floor: float = 0.90,
        thresholds: list[float] = None,
        overlap_threshold: float = 0.5,
    ):
        """
        Initialize calibrator.

        Args:
            recall_floor: Minimum acceptable recall (safety requirement)
            thresholds: List of thresholds to sweep (default: [0.30, 0.40, 0.50, 0.60])
            overlap_threshold: Minimum overlap ratio for span matching
        """
        self.recall_floor = recall_floor
        self.thresholds = thresholds or [0.30, 0.40, 0.50, 0.60]
        self.overlap_threshold = overlap_threshold
        self._analyzer = None
        self._anonymizer = None

    def _load_presidio(self):
        """Lazy load Presidio engines."""
        if self._analyzer is None:
            from app.deidentification import _get_engines
            self._analyzer, self._anonymizer = _get_engines()

    def _analyze_text_raw(self, text: str, threshold: float = 0.0) -> list[dict]:
        """
        Run Presidio analysis at specified threshold.

        Args:
            text: Input text to analyze
            threshold: Confidence score threshold (0.0 returns all detections)

        Returns:
            List of detected entities with scores
        """
        self._load_presidio()

        from app.config import settings

        results = self._analyzer.analyze(
            text=text,
            language="en",
            entities=settings.phi_entities,
            score_threshold=threshold
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

    def _calculate_overlap(
        self,
        span1_start: int,
        span1_end: int,
        span2_start: int,
        span2_end: int
    ) -> float:
        """Calculate Jaccard-like overlap ratio between two spans."""
        overlap_start = max(span1_start, span2_start)
        overlap_end = min(span1_end, span2_end)

        if overlap_start >= overlap_end:
            return 0.0

        overlap_length = overlap_end - overlap_start
        span1_length = span1_end - span1_start
        span2_length = span2_end - span2_start

        union_length = span1_length + span2_length - overlap_length
        return overlap_length / union_length if union_length > 0 else 0.0

    def _get_best_match_score(
        self,
        gt_span: PHISpan,
        detections: list[dict]
    ) -> Optional[float]:
        """
        Find the best matching detection for a ground truth span.

        Args:
            gt_span: Ground truth PHI span
            detections: List of Presidio detections (already filtered by entity type)

        Returns:
            Score of best matching detection, or None if no match
        """
        best_score = None
        best_overlap = 0.0

        for det in detections:
            overlap = self._calculate_overlap(
                gt_span.start, gt_span.end,
                det["start"], det["end"]
            )

            if overlap >= self.overlap_threshold and overlap > best_overlap:
                best_overlap = overlap
                best_score = det["score"]

        return best_score

    def collect_scores_for_entity(
        self,
        entity_type: str,
        dataset: list[SyntheticHandoff],
        verbose: bool = False
    ) -> tuple[list[int], list[float]]:
        """
        Collect ground truth labels and confidence scores for an entity type.

        Args:
            entity_type: Entity type to collect scores for
            dataset: Dataset with ground truth spans
            verbose: Print progress

        Returns:
            Tuple of (y_true, y_scores) arrays for PR curve generation
        """
        y_true = []
        y_scores = []

        for handoff in dataset:
            # Get ground truth spans for this entity type
            gt_spans = [s for s in handoff.phi_spans if s.entity_type == entity_type]

            if not gt_spans:
                continue

            # Get all detections at threshold=0 (all scores)
            all_detections = self._analyze_text_raw(handoff.text, threshold=0.0)

            # Filter to matching entity types (handle GUARDIAN_NAME -> PERSON mapping)
            if entity_type == "PERSON":
                entity_detections = [
                    d for d in all_detections
                    if d["entity_type"] in ["PERSON", "GUARDIAN_NAME"]
                ]
            else:
                entity_detections = [
                    d for d in all_detections
                    if d["entity_type"] == entity_type
                ]

            # For each ground truth span, find best matching detection
            for gt_span in gt_spans:
                best_score = self._get_best_match_score(gt_span, entity_detections)

                y_true.append(1)  # Ground truth positive
                y_scores.append(best_score if best_score is not None else 0.0)

        return y_true, y_scores

    def evaluate_at_threshold(
        self,
        entity_type: str,
        dataset: list[SyntheticHandoff],
        threshold: float,
    ) -> ThresholdResult:
        """
        Evaluate detection performance at a specific threshold.

        Args:
            entity_type: Entity type to evaluate
            dataset: Dataset with ground truth spans
            threshold: Confidence threshold to apply

        Returns:
            ThresholdResult with metrics
        """
        tp, fn, fp = 0, 0, 0

        for handoff in dataset:
            # Get ground truth spans for this entity type
            gt_spans = [s for s in handoff.phi_spans if s.entity_type == entity_type]

            # Get detections at this threshold
            all_detections = self._analyze_text_raw(handoff.text, threshold=0.0)

            # Filter by threshold and entity type
            if entity_type == "PERSON":
                entity_detections = [
                    d for d in all_detections
                    if d["entity_type"] in ["PERSON", "GUARDIAN_NAME"] and d["score"] >= threshold
                ]
            else:
                entity_detections = [
                    d for d in all_detections
                    if d["entity_type"] == entity_type and d["score"] >= threshold
                ]

            # Match ground truth to detections
            matched_gt = set()
            matched_det = set()

            for i, gt_span in enumerate(gt_spans):
                for j, det in enumerate(entity_detections):
                    if j in matched_det:
                        continue

                    overlap = self._calculate_overlap(
                        gt_span.start, gt_span.end,
                        det["start"], det["end"]
                    )

                    if overlap >= self.overlap_threshold:
                        matched_gt.add(i)
                        matched_det.add(j)
                        tp += 1
                        break

            # Count false negatives (unmatched ground truth)
            fn += len(gt_spans) - len(matched_gt)

            # Count false positives (unmatched detections)
            fp += len(entity_detections) - len(matched_det)

        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0 if tp == 0 and fn == 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f2 = 5 * precision * recall / (4 * precision + recall) if (4 * precision + recall) > 0 else 0.0

        return ThresholdResult(
            threshold=threshold,
            precision=precision,
            recall=recall,
            f1=f1,
            f2=f2,
            tp=tp,
            fn=fn,
            fp=fp,
            meets_recall_floor=recall >= self.recall_floor
        )

    def calibrate_entity(
        self,
        entity_type: str,
        dataset: list[SyntheticHandoff],
        verbose: bool = False,
    ) -> EntityCalibrationResult:
        """
        Calibrate threshold for a single entity type.

        Args:
            entity_type: Entity type to calibrate
            dataset: Dataset with ground truth spans
            verbose: Print progress

        Returns:
            EntityCalibrationResult with optimal threshold and rationale
        """
        if verbose:
            print(f"  Calibrating {entity_type}...")

        # Sweep all thresholds
        sweep_results = []
        for threshold in self.thresholds:
            result = self.evaluate_at_threshold(entity_type, dataset, threshold)
            sweep_results.append(result)

            if verbose:
                status = "OK" if result.meets_recall_floor else "BELOW FLOOR"
                print(f"    {threshold:.2f}: P={result.precision:.1%} R={result.recall:.1%} F2={result.f2:.1%} [{status}]")

        # Collect PR curve data
        y_true, y_scores = self.collect_scores_for_entity(entity_type, dataset, verbose)

        # Generate PR curve arrays
        from sklearn.metrics import precision_recall_curve

        if y_true and any(s > 0 for s in y_scores):
            precision_arr, recall_arr, thresholds_arr = precision_recall_curve(y_true, y_scores)
            pr_curve_data = {
                "precision": precision_arr.tolist(),
                "recall": recall_arr.tolist(),
                "thresholds": thresholds_arr.tolist(),
            }
        else:
            pr_curve_data = {
                "precision": [],
                "recall": [],
                "thresholds": [],
            }

        # Select optimal threshold
        safe_results = [r for r in sweep_results if r.meets_recall_floor]

        if not safe_results:
            # No threshold meets recall floor - use lowest threshold
            best = sweep_results[0]  # Lowest threshold (0.30)
            for r in sweep_results:
                if r.recall > best.recall:
                    best = r

            rationale = (
                f"No threshold achieves {self.recall_floor:.0%} recall floor. "
                f"Using threshold {best.threshold:.2f} for maximum recall={best.recall:.1%}. "
                f"Pattern improvements required (Phase 4)."
            )
        else:
            # Find threshold with maximum F2
            best = max(safe_results, key=lambda r: r.f2)

            # Tie-breaking: if multiple within 0.5% F2, prefer higher recall
            ties = [r for r in safe_results if abs(r.f2 - best.f2) < 0.005]
            if len(ties) > 1:
                best = max(ties, key=lambda r: r.recall)
                tie_note = " (tie-break: higher recall preferred)"
            else:
                tie_note = ""

            rationale = (
                f"Threshold {best.threshold:.2f} maximizes F2={best.f2:.1%} "
                f"while maintaining recall>={self.recall_floor:.0%}. "
                f"Achieves P={best.precision:.1%}, R={best.recall:.1%}.{tie_note}"
            )

        return EntityCalibrationResult(
            entity_type=entity_type,
            optimal_threshold=best.threshold,
            metrics={
                "precision": best.precision,
                "recall": best.recall,
                "f1": best.f1,
                "f2": best.f2,
                "tp": best.tp,
                "fn": best.fn,
                "fp": best.fp,
            },
            rationale=rationale,
            sweep_results=sweep_results,
            pr_curve_data=pr_curve_data,
        )

    def calibrate_all(
        self,
        datasets: list[tuple[str, list[SyntheticHandoff]]],
        verbose: bool = False,
    ) -> dict[str, EntityCalibrationResult]:
        """
        Calibrate thresholds for all entity types.

        Args:
            datasets: List of (name, dataset) tuples to combine
            verbose: Print progress

        Returns:
            Dict mapping entity_type to calibration result
        """
        # Combine all datasets
        combined_dataset = []
        dataset_names = []
        for name, dataset in datasets:
            combined_dataset.extend(dataset)
            dataset_names.append(name)

        if verbose:
            print(f"Calibrating thresholds for {len(self.ENTITY_TYPES)} entity types")
            print(f"Datasets: {', '.join(dataset_names)} ({len(combined_dataset)} total handoffs)")
            print(f"Thresholds: {self.thresholds}")
            print(f"Recall floor: {self.recall_floor:.0%}")
            print()

        results = {}
        for entity_type in self.ENTITY_TYPES:
            result = self.calibrate_entity(entity_type, combined_dataset, verbose)
            results[entity_type] = result

        return results

    def generate_pr_curve_plot(
        self,
        result: EntityCalibrationResult,
        output_path: Path,
    ) -> None:
        """
        Generate and save a precision-recall curve plot.

        Args:
            result: Calibration result with PR curve data
            output_path: Path to save PNG plot
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(8, 6))

        pr_data = result.pr_curve_data

        if pr_data["precision"] and pr_data["recall"]:
            # Plot PR curve
            ax.plot(pr_data["recall"], pr_data["precision"], 'b-', linewidth=2, label="PR Curve")

            # Mark recall floor
            ax.axvline(x=self.recall_floor, color='r', linestyle='--', alpha=0.7,
                       label=f'Recall Floor ({self.recall_floor:.0%})')

            # Mark sweep thresholds
            for sweep_result in result.sweep_results:
                marker = 'o' if sweep_result.threshold == result.optimal_threshold else 's'
                color = 'green' if sweep_result.meets_recall_floor else 'red'
                size = 150 if sweep_result.threshold == result.optimal_threshold else 80

                ax.scatter(
                    sweep_result.recall,
                    sweep_result.precision,
                    c=color,
                    s=size,
                    marker=marker,
                    zorder=5,
                    label=f't={sweep_result.threshold:.2f}' if sweep_result.threshold == result.optimal_threshold else None
                )

            # Add optimal threshold annotation
            best_sweep = next(r for r in result.sweep_results if r.threshold == result.optimal_threshold)
            ax.annotate(
                f'Optimal: t={result.optimal_threshold:.2f}\nF2={best_sweep.f2:.1%}',
                xy=(best_sweep.recall, best_sweep.precision),
                xytext=(best_sweep.recall - 0.15, best_sweep.precision - 0.1),
                arrowprops=dict(arrowstyle='->', color='green'),
                fontsize=10,
                color='green',
            )
        else:
            ax.text(0.5, 0.5, 'Insufficient data for PR curve',
                    ha='center', va='center', fontsize=12)

        ax.set_xlabel('Recall', fontsize=12)
        ax.set_ylabel('Precision', fontsize=12)
        ax.set_title(f'Precision-Recall Curve: {result.entity_type}', fontsize=14)
        ax.set_xlim([0, 1.05])
        ax.set_ylim([0, 1.05])
        ax.grid(True, alpha=0.3)
        ax.legend(loc='lower left')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

    def save_results(
        self,
        results: dict[str, EntityCalibrationResult],
        output_dir: Path,
        dataset_names: list[str],
    ) -> None:
        """
        Save calibration results to JSON files and generate PR curve plots.

        Args:
            results: Calibration results by entity type
            output_dir: Output directory
            dataset_names: Names of datasets used
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        pr_curves_dir = output_dir / "pr_curves"
        pr_curves_dir.mkdir(parents=True, exist_ok=True)

        # Generate PR curve plots
        for entity_type, result in results.items():
            plot_path = pr_curves_dir / f"{entity_type}.png"
            self.generate_pr_curve_plot(result, plot_path)

        # Save threshold sweep results
        sweep_data = {
            "calibration_date": datetime.now().strftime("%Y-%m-%d"),
            "calibration_time": datetime.now().strftime("%H:%M:%S"),
            "datasets": dataset_names,
            "recall_floor": self.recall_floor,
            "thresholds_tested": self.thresholds,
            "results_by_entity": {},
        }

        for entity_type, result in results.items():
            sweep_data["results_by_entity"][entity_type] = {
                "sweep_results": [
                    {
                        "threshold": r.threshold,
                        "precision": round(r.precision, 4),
                        "recall": round(r.recall, 4),
                        "f1": round(r.f1, 4),
                        "f2": round(r.f2, 4),
                        "tp": r.tp,
                        "fn": r.fn,
                        "fp": r.fp,
                        "meets_recall_floor": r.meets_recall_floor,
                    }
                    for r in result.sweep_results
                ],
                "pr_curve_data": result.pr_curve_data,
            }

        with open(output_dir / "threshold_sweep.json", "w") as f:
            json.dump(sweep_data, f, indent=2)

        # Save optimal thresholds
        optimal_data = {
            "calibration_date": datetime.now().strftime("%Y-%m-%d"),
            "datasets": dataset_names,
            "methodology": f"PR curve analysis, F2 optimization, recall>={self.recall_floor:.0%} floor",
            "thresholds": {},
        }

        for entity_type, result in results.items():
            optimal_data["thresholds"][entity_type] = {
                "optimal_threshold": result.optimal_threshold,
                "metrics": {
                    "precision": round(result.metrics["precision"], 4),
                    "recall": round(result.metrics["recall"], 4),
                    "f1": round(result.metrics["f1"], 4),
                    "f2": round(result.metrics["f2"], 4),
                },
                "rationale": result.rationale,
            }

        with open(output_dir / "optimal_thresholds.json", "w") as f:
            json.dump(optimal_data, f, indent=2)


def print_summary(results: dict[str, EntityCalibrationResult], recall_floor: float) -> None:
    """Print calibration summary to console."""
    print("\n" + "=" * 70)
    print("THRESHOLD CALIBRATION SUMMARY")
    print("=" * 70)
    print()

    meets_floor_count = 0
    below_floor_count = 0

    print(f"{'Entity Type':<25} {'Threshold':>10} {'Precision':>10} {'Recall':>10} {'F2':>10} {'Status':>12}")
    print("-" * 77)

    for entity_type, result in results.items():
        metrics = result.metrics
        meets_floor = metrics["recall"] >= recall_floor
        status = "OK" if meets_floor else "BELOW FLOOR"

        if meets_floor:
            meets_floor_count += 1
        else:
            below_floor_count += 1

        print(f"{entity_type:<25} {result.optimal_threshold:>10.2f} "
              f"{metrics['precision']:>10.1%} {metrics['recall']:>10.1%} "
              f"{metrics['f2']:>10.1%} {status:>12}")

    print("-" * 77)
    print()
    print(f"Entities meeting {recall_floor:.0%} recall floor: {meets_floor_count}/{len(results)}")
    print(f"Entities below recall floor: {below_floor_count}/{len(results)}")

    if below_floor_count > 0:
        print("\nEntities requiring Phase 4 pattern improvements:")
        for entity_type, result in results.items():
            if result.metrics["recall"] < recall_floor:
                print(f"  - {entity_type}: best recall={result.metrics['recall']:.1%}")

    print()
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate per-entity confidence score thresholds"
    )
    parser.add_argument(
        "--standard-dataset",
        type=Path,
        default=Path("tests/synthetic_handoffs.json"),
        help="Standard dataset path (default: tests/synthetic_handoffs.json)"
    )
    parser.add_argument(
        "--adversarial-dataset",
        type=Path,
        default=Path("tests/adversarial_handoffs.json"),
        help="Adversarial dataset path (default: tests/adversarial_handoffs.json)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tests/results"),
        help="Output directory (default: tests/results)"
    )
    parser.add_argument(
        "--recall-floor",
        type=float,
        default=0.90,
        help="Minimum acceptable recall (default: 0.90)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed progress"
    )

    args = parser.parse_args()

    # Load datasets
    datasets = []
    dataset_names = []

    if args.standard_dataset.exists():
        print(f"Loading standard dataset: {args.standard_dataset}")
        standard = load_dataset(args.standard_dataset)
        datasets.append((args.standard_dataset.name, standard))
        dataset_names.append(args.standard_dataset.name)
        print(f"  Loaded {len(standard)} handoffs")
    else:
        print(f"Warning: Standard dataset not found: {args.standard_dataset}")

    if args.adversarial_dataset.exists():
        print(f"Loading adversarial dataset: {args.adversarial_dataset}")
        adversarial = load_dataset(args.adversarial_dataset)
        datasets.append((args.adversarial_dataset.name, adversarial))
        dataset_names.append(args.adversarial_dataset.name)
        print(f"  Loaded {len(adversarial)} handoffs")
    else:
        print(f"Warning: Adversarial dataset not found: {args.adversarial_dataset}")

    if not datasets:
        print("Error: No datasets found. Run generate_test_data.py first.")
        sys.exit(1)

    print()

    # Run calibration
    calibrator = ThresholdCalibrator(recall_floor=args.recall_floor)
    results = calibrator.calibrate_all(datasets, verbose=args.verbose)

    # Save results
    calibrator.save_results(results, args.output_dir, dataset_names)

    # Print summary
    print_summary(results, args.recall_floor)

    # Print output file locations
    print("Output files:")
    print(f"  PR curves: {args.output_dir / 'pr_curves'}/*.png")
    print(f"  Threshold sweep: {args.output_dir / 'threshold_sweep.json'}")
    print(f"  Optimal thresholds: {args.output_dir / 'optimal_thresholds.json'}")


if __name__ == "__main__":
    main()
