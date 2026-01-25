#!/usr/bin/env python3
"""
Philter-UCSF benchmark script.

Benchmarks Philter's rule-based de-identification against synthetic handoff dataset.
Compares to Presidio baseline to evaluate alternative engine performance.

LOOKBEHIND SUPPORT: ✓ CONFIRMED
- Python re module fully supports lookbehind patterns
- Using lookbehind patterns: (?<=mom )\\w+ matches only the name
- Preserves relationship words ("Mom", "Dad") in output

Pattern Translation:
- Guardian names: Translated 24 lookbehind/lookahead patterns from pediatric.py
- Room numbers: Translated 8 context-aware patterns from medical.py
- Focus on high-weight patterns (GUARDIAN_NAME weight=5, ROOM weight=4)

Usage:
    python scripts/benchmark_philter.py --input tests/synthetic_handoffs.json
    python scripts/benchmark_philter.py --input tests/synthetic_handoffs.json --weighted
    python scripts/benchmark_philter.py --input tests/synthetic_handoffs.json --verbose
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.evaluate_presidio import EvaluationMetrics, DetectionResult
from tests.generate_test_data import SyntheticHandoff, PHISpan, load_dataset


class PhilterBenchmark:
    """
    Benchmark Philter-UCSF rule-based de-identification.

    Philter uses compiled regex patterns to detect PHI. This benchmark
    runs Philter patterns directly (without full Philter pipeline) to
    extract PHI spans for comparison with ground truth.
    """

    def __init__(self, patterns_config: Path):
        """
        Initialize benchmark with pattern configuration.

        Args:
            patterns_config: Path to philter_patterns.json
        """
        self.patterns = self._load_patterns(patterns_config)

    def _load_patterns(self, config_path: Path) -> List[Dict]:
        """Load and compile Philter patterns."""
        with open(config_path) as f:
            pattern_configs = json.load(f)

        patterns = []
        for config in pattern_configs:
            # Read regex from file
            pattern_file = Path(config["filepath"])
            if not pattern_file.exists():
                raise FileNotFoundError(f"Pattern file not found: {pattern_file}")

            with open(pattern_file) as f:
                regex_text = f.read().strip()

            # Compile regex
            try:
                compiled = re.compile(regex_text)
            except re.error as e:
                raise ValueError(f"Invalid regex in {pattern_file}: {e}")

            patterns.append({
                "title": config["title"],
                "phi_type": config["phi_type"],
                "regex": compiled,
                "exclude": config.get("exclude", False)
            })

        return patterns

    def detect_phi(self, text: str) -> List[Dict]:
        """
        Detect PHI in text using Philter patterns.

        Args:
            text: Input text to analyze

        Returns:
            List of detected PHI spans with entity_type, start, end, text
        """
        detected = []

        for pattern in self.patterns:
            # Find all matches
            for match in pattern["regex"].finditer(text):
                detected.append({
                    "entity_type": pattern["phi_type"],
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                    "score": 0.85  # Philter patterns are high-confidence
                })

        # Sort by position for consistent ordering
        detected.sort(key=lambda x: (x["start"], x["end"]))

        return detected

    def evaluate_handoff(self, handoff: SyntheticHandoff, overlap_threshold: float = 0.5) -> DetectionResult:
        """
        Evaluate Philter detection on a single handoff.

        Args:
            handoff: Synthetic handoff with ground truth spans
            overlap_threshold: Minimum overlap ratio for match

        Returns:
            DetectionResult with TP, FN, FP classifications
        """
        detected = self.detect_phi(handoff.text)

        result = DetectionResult(
            handoff_id=handoff.id,
            expected_spans=handoff.phi_spans,
            detected_spans=detected,
        )

        # Track which spans have been matched
        matched_expected = set()
        matched_detected = set()

        # Find matches using overlap (same logic as Presidio evaluator)
        for i, expected in enumerate(handoff.phi_spans):
            for j, det in enumerate(detected):
                if j in matched_detected:
                    continue

                # Calculate overlap
                overlap = self._calculate_overlap(
                    expected.start, expected.end,
                    det["start"], det["end"]
                )

                if overlap >= overlap_threshold:
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

    def _calculate_overlap(self, span1_start: int, span1_end: int,
                           span2_start: int, span2_end: int) -> float:
        """Calculate Jaccard overlap between two spans."""
        overlap_start = max(span1_start, span2_start)
        overlap_end = min(span1_end, span2_end)

        if overlap_start >= overlap_end:
            return 0.0

        overlap_length = overlap_end - overlap_start
        span1_length = span1_end - span1_start
        span2_length = span2_end - span2_start

        union_length = span1_length + span2_length - overlap_length
        return overlap_length / union_length if union_length > 0 else 0.0

    def _types_match(self, expected_type: str, detected_type: str) -> bool:
        """Check if PHI types are compatible."""
        # Philter uses exact type matching (GUARDIAN_NAME vs GUARDIAN_NAME, ROOM vs ROOM)
        return expected_type == detected_type

    def evaluate_dataset(
        self,
        dataset: List[SyntheticHandoff],
        verbose: bool = False,
    ) -> Tuple[EvaluationMetrics, List[DetectionResult]]:
        """
        Evaluate Philter on entire dataset.

        Args:
            dataset: List of synthetic handoffs
            verbose: Print progress and details

        Returns:
            Tuple of (overall metrics, list of per-handoff results)
        """
        metrics = EvaluationMetrics()
        results = []

        if verbose:
            print(f"Evaluating {len(dataset)} handoffs with Philter...")

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

        return metrics, results

    def generate_report(
        self,
        metrics: EvaluationMetrics,
        results: List[DetectionResult],
        show_failures: bool = True,
        weighted: bool = False,
    ) -> str:
        """
        Generate evaluation report.

        Args:
            metrics: Overall metrics
            results: Per-handoff results
            show_failures: Include details of missed PHI
            weighted: Include weighted metrics

        Returns:
            Formatted report string
        """
        lines = [
            "=" * 60,
            "PHILTER-UCSF PHI DETECTION BENCHMARK REPORT",
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

        # Add weighted metrics if requested
        if weighted:
            from app.config import settings
            weights = settings.spoken_handoff_weights

            lines.append("WEIGHTED METRICS (spoken handoff relevance):")
            lines.append(f"  Weighted Recall:    {metrics.weighted_recall(weights):.1%}")
            lines.append(f"  Weighted Precision: {metrics.weighted_precision(weights):.1%}")
            lines.append(f"  Weighted F2 Score:  {metrics.weighted_f2(weights):.1%}  ← PRIMARY METRIC")
            lines.append("")
            lines.append("  Weights applied:")
            for entity, weight in sorted(weights.items(), key=lambda x: -x[1]):
                lines.append(f"    {entity}: {weight}")
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
        description="Benchmark Philter-UCSF PHI detection against synthetic dataset"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("tests/synthetic_handoffs.json"),
        help="Input dataset file (default: tests/synthetic_handoffs.json)"
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=Path("configs/philter_patterns.json"),
        help="Philter patterns config (default: configs/philter_patterns.json)"
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

    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)

    # Load dataset
    print(f"Loading dataset from {args.input}...")
    with open(args.input) as f:
        data = json.load(f)
    dataset = data["handoffs"]  # Access handoffs from dict

    # Convert to SyntheticHandoff objects
    handoffs = []
    for item in dataset:
        phi_spans = [PHISpan(**span) for span in item["phi_spans"]]
        handoff = SyntheticHandoff(
            id=item["id"],
            text=item["text"],
            template_id=item["template_id"],
            phi_spans=phi_spans
        )
        handoffs.append(handoff)

    print(f"Loaded {len(handoffs)} handoffs")

    # Initialize benchmark
    benchmark = PhilterBenchmark(args.config)
    print(f"Loaded {len(benchmark.patterns)} Philter patterns")

    # Evaluate
    metrics, results = benchmark.evaluate_dataset(handoffs, verbose=args.verbose)

    # Generate report
    report = benchmark.generate_report(metrics, results, weighted=args.weighted)

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
