#!/usr/bin/env python3
"""
Benchmark Stanford BERT (StanfordAIMI/stanford-deidentifier-base) PHI detection.

Integrates Stanford BERT via Presidio's TransformersNlpEngine to enable
comparative evaluation against current spaCy NER + custom patterns approach.

Usage:
    python scripts/benchmark_bert.py --sample 20 --verbose
    python scripts/benchmark_bert.py --input tests/synthetic_handoffs.json
    python scripts/benchmark_bert.py --weighted --with-ci

Runtime warning: BERT inference on CPU is slow (5-10 seconds per handoff).
- 20 samples: ~2-3 minutes
- 100 samples: ~10-15 minutes
- 600 samples (full): ~1-2 hours

Use --sample flag for initial testing before committing to full benchmark.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.evaluate_presidio import EvaluationMetrics, DetectionResult
from tests.generate_test_data import PHISpan


def load_entity_mapping(mapping_path: Path) -> dict[str, Optional[str]]:
    """Load Stanford BERT to Presidio entity type mapping."""
    with open(mapping_path) as f:
        config = json.load(f)
    return config["mapping"]


def create_bert_analyzer():
    """
    Create AnalyzerEngine with Stanford BERT via TransformersNlpEngine.

    Returns:
        Tuple of (analyzer, entity_mapping)
    """
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    # Configure TransformersNlpEngine with Stanford BERT
    nlp_config = {
        "nlp_engine_name": "transformers",
        "models": [{
            "lang_code": "en",
            "model_name": {
                "spacy": "en_core_web_sm",
                "transformers": "StanfordAIMI/stanford-deidentifier-base"
            }
        }]
    }

    # Create NLP engine provider
    provider = NlpEngineProvider(nlp_configuration=nlp_config)
    nlp_engine = provider.create_engine()

    # Create analyzer with transformer engine
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

    # Wire custom pediatric recognizers
    from app.recognizers.pediatric import get_pediatric_recognizers
    pediatric_recognizers = get_pediatric_recognizers()
    for recognizer in pediatric_recognizers:
        analyzer.registry.add_recognizer(recognizer)

    # Load entity mapping
    mapping_path = Path(__file__).parent.parent / "configs" / "bert_entity_mapping.json"
    entity_mapping = load_entity_mapping(mapping_path)

    return analyzer, entity_mapping


def analyze_handoff(
    analyzer,
    text: str,
    entity_mapping: dict[str, Optional[str]]
) -> list[dict]:
    """
    Analyze handoff text with BERT and map entities to Presidio types.

    Args:
        analyzer: AnalyzerEngine configured with BERT
        text: Handoff text to analyze
        entity_mapping: BERT entity to Presidio entity mapping

    Returns:
        List of detected PHI spans with Presidio entity types
    """
    # Run BERT analysis (no score threshold - collect all)
    results = analyzer.analyze(
        text=text,
        language="en",
        score_threshold=0.0
    )

    # Map BERT entities to Presidio types
    mapped_results = []
    for result in results:
        # Get BERT entity type
        bert_entity = result.entity_type

        # Map to Presidio type
        presidio_entity = entity_mapping.get(bert_entity)

        # Skip "O" (outside) entities
        if presidio_entity is None:
            continue

        mapped_results.append({
            "entity_type": presidio_entity,
            "start": result.start,
            "end": result.end,
            "score": result.score,
            "text": text[result.start:result.end]
        })

    return mapped_results


def calculate_overlap(span1_start: int, span1_end: int,
                     span2_start: int, span2_end: int) -> float:
    """Calculate Jaccard-like overlap between two spans."""
    overlap_start = max(span1_start, span2_start)
    overlap_end = min(span1_end, span2_end)

    if overlap_start >= overlap_end:
        return 0.0

    overlap_length = overlap_end - overlap_start
    span1_length = span1_end - span1_start
    span2_length = span2_end - span2_start

    union_length = span1_length + span2_length - overlap_length
    return overlap_length / union_length if union_length > 0 else 0.0


def evaluate_handoff(
    handoff_id: int,
    text: str,
    expected_spans: list[dict],
    detected_spans: list[dict],
    overlap_threshold: float = 0.5
) -> DetectionResult:
    """
    Compare detected spans against ground truth.

    Args:
        handoff_id: Handoff identifier
        text: Handoff text
        expected_spans: Ground truth PHI spans
        detected_spans: BERT-detected PHI spans
        overlap_threshold: Minimum overlap to consider a match

    Returns:
        DetectionResult with TP/FN/FP classifications
    """
    # Convert expected spans to PHISpan objects
    expected_phi = [
        PHISpan(
            entity_type=s["entity_type"],
            start=s["start"],
            end=s["end"],
            text=s["text"]
        )
        for s in expected_spans
    ]

    result = DetectionResult(
        handoff_id=handoff_id,
        expected_spans=expected_phi,
        detected_spans=detected_spans
    )

    # Track which expected spans were matched
    matched_expected = set()
    matched_detected = set()

    # Find true positives: detected spans that overlap expected spans
    for i, detected in enumerate(detected_spans):
        best_overlap = 0.0
        best_match = None

        for j, expected in enumerate(expected_phi):
            # Check if types match
            if detected["entity_type"] != expected.entity_type:
                continue

            # Calculate overlap
            overlap = calculate_overlap(
                detected["start"], detected["end"],
                expected.start, expected.end
            )

            if overlap > best_overlap:
                best_overlap = overlap
                best_match = j

        # If overlap exceeds threshold, it's a true positive
        if best_overlap >= overlap_threshold and best_match is not None:
            result.true_positives.append(expected_phi[best_match])
            matched_expected.add(best_match)
            matched_detected.add(i)

    # False negatives: expected spans that weren't detected
    for j, expected in enumerate(expected_phi):
        if j not in matched_expected:
            result.false_negatives.append(expected)

    # False positives: detected spans that don't match any expected span
    for i, detected in enumerate(detected_spans):
        if i not in matched_detected:
            result.false_positives.append(detected)

    return result


def benchmark_bert(
    input_path: Path,
    sample: int = 0,
    weighted: bool = False,
    with_ci: bool = False,
    verbose: bool = False
) -> EvaluationMetrics:
    """
    Run Stanford BERT benchmark on handoff dataset.

    Args:
        input_path: Path to synthetic handoff JSON
        sample: Run on first N samples (0 = all)
        weighted: Calculate weighted metrics
        with_ci: Calculate bootstrap confidence intervals
        verbose: Print per-handoff details

    Returns:
        EvaluationMetrics with precision/recall/F2
    """
    # Load dataset
    with open(input_path) as f:
        data = json.load(f)
    handoffs = data["handoffs"]

    # Sample if requested
    if sample > 0:
        handoffs = handoffs[:sample]
        print(f"Running on {sample} sample handoffs (for time estimation)")

    print(f"Loaded {len(handoffs)} handoffs from {input_path}")

    # Create BERT analyzer
    print("Initializing Stanford BERT analyzer...")
    start_init = time.time()
    analyzer, entity_mapping = create_bert_analyzer()
    init_time = time.time() - start_init
    print(f"Analyzer initialized in {init_time:.1f}s")
    print(f"Entity mapping: {entity_mapping}")

    # Initialize metrics
    metrics = EvaluationMetrics()
    all_results = []

    # Process each handoff
    start_inference = time.time()
    for i, handoff in enumerate(handoffs):
        handoff_start = time.time()

        # Analyze with BERT
        detected_spans = analyze_handoff(
            analyzer,
            handoff["text"],
            entity_mapping
        )

        # Evaluate against ground truth
        result = evaluate_handoff(
            handoff_id=handoff["id"],
            text=handoff["text"],
            expected_spans=handoff["phi_spans"],
            detected_spans=detected_spans
        )

        all_results.append(result)

        # Update metrics
        metrics.total_expected += len(result.expected_spans)
        metrics.total_detected += len(detected_spans)
        metrics.true_positives += len(result.true_positives)
        metrics.false_negatives += len(result.false_negatives)
        metrics.false_positives += len(result.false_positives)

        # Update per-entity stats for weighted metrics
        for span in result.expected_spans:
            entity_type = span.entity_type
            if entity_type not in metrics.entity_stats:
                metrics.entity_stats[entity_type] = {"tp": 0, "fn": 0, "fp": 0}

        for span in result.true_positives:
            metrics.entity_stats[span.entity_type]["tp"] += 1

        for span in result.false_negatives:
            metrics.entity_stats[span.entity_type]["fn"] += 1

        for detected in result.false_positives:
            entity_type = detected["entity_type"]
            if entity_type not in metrics.entity_stats:
                metrics.entity_stats[entity_type] = {"tp": 0, "fn": 0, "fp": 0}
            metrics.entity_stats[entity_type]["fp"] += 1

        handoff_time = time.time() - handoff_start

        if verbose:
            print(f"\nHandoff {i+1}/{len(handoffs)} ({handoff_time:.1f}s):")
            print(f"  TP: {len(result.true_positives)}, "
                  f"FN: {len(result.false_negatives)}, "
                  f"FP: {len(result.false_positives)}")
            if result.false_negatives:
                print(f"  Missed PHI: {[span.text for span in result.false_negatives]}")

        # Progress indicator for long runs
        if not verbose and (i + 1) % 10 == 0:
            elapsed = time.time() - start_inference
            rate = (i + 1) / elapsed
            remaining = (len(handoffs) - (i + 1)) / rate
            print(f"Progress: {i+1}/{len(handoffs)} "
                  f"({rate:.1f} handoffs/min, "
                  f"~{remaining/60:.1f}min remaining)")

    total_time = time.time() - start_inference
    print(f"\nTotal inference time: {total_time:.1f}s "
          f"({total_time/len(handoffs):.1f}s per handoff)")

    # Print metrics
    print("\n" + "="*60)
    print("STANFORD BERT BENCHMARK RESULTS")
    print("="*60)
    print(f"Precision: {metrics.precision:.1%}")
    print(f"Recall:    {metrics.recall:.1%}")
    print(f"F2 score:  {metrics.f2:.1%}")
    print(f"\nTP: {metrics.true_positives}, "
          f"FN: {metrics.false_negatives}, "
          f"FP: {metrics.false_positives}")

    # Weighted metrics if requested
    if weighted:
        # Spoken handoff relevance weights from 08-01
        weights = {
            "PERSON": 5,
            "GUARDIAN_NAME": 5,
            "ROOM": 4,
            "PHONE_NUMBER": 2,
            "DATE_TIME": 2,
            "MEDICAL_RECORD_NUMBER": 1,
            "EMAIL_ADDRESS": 0,
            "LOCATION": 0,
            "PEDIATRIC_AGE": 0
        }
        print("\n" + "-"*60)
        print("WEIGHTED METRICS (spoken handoff relevance)")
        print("-"*60)
        print(f"Weighted Precision: {metrics.weighted_precision(weights):.1%}")
        print(f"Weighted Recall:    {metrics.weighted_recall(weights):.1%}")
        print(f"Weighted F2:        {metrics.weighted_f2(weights):.1%}")

    # Per-entity breakdown
    print("\n" + "-"*60)
    print("PER-ENTITY BREAKDOWN")
    print("-"*60)
    for entity_type, stats in sorted(metrics.entity_stats.items()):
        tp = stats["tp"]
        fn = stats["fn"]
        fp = stats["fp"]
        total = tp + fn
        detected = tp + fp

        recall = tp / total if total > 0 else 0.0
        precision = tp / detected if detected > 0 else 0.0

        print(f"{entity_type:25} "
              f"Recall: {recall:5.1%} ({tp:3}/{total:3})  "
              f"Precision: {precision:5.1%} ({tp:3}/{detected:3})")

    # Bootstrap CI if requested
    if with_ci:
        print("\n" + "-"*60)
        print("BOOTSTRAP CONFIDENCE INTERVALS (95%)")
        print("-"*60)
        print("Note: Bootstrap calculation is slow (~30s for 10k iterations)")
        # TODO: Implement bootstrap CI calculation
        print("Bootstrap CI not yet implemented for BERT benchmark")

    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Stanford BERT PHI detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Runtime estimates (CPU inference):
  --sample 20:  ~2-3 minutes
  --sample 100: ~10-15 minutes
  Full (600):   ~1-2 hours

Use --sample for initial testing before committing to full benchmark.
        """
    )

    parser.add_argument(
        '--input',
        type=Path,
        default=Path('tests/synthetic_handoffs.json'),
        help='Path to synthetic handoff JSON (default: tests/synthetic_handoffs.json)'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=0,
        help='Run on first N samples only (0=all). Use for initial testing.'
    )
    parser.add_argument(
        '--weighted',
        action='store_true',
        help='Calculate weighted metrics using spoken handoff relevance weights'
    )
    parser.add_argument(
        '--with-ci',
        action='store_true',
        help='Calculate bootstrap confidence intervals (slow)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print per-handoff detection details'
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Run benchmark
    metrics = benchmark_bert(
        input_path=args.input,
        sample=args.sample,
        weighted=args.weighted,
        with_ci=args.with_ci,
        verbose=args.verbose
    )

    # Exit with error if recall is below safety threshold
    if metrics.recall < 0.95:
        print(f"\nWARNING: Recall {metrics.recall:.1%} below 95% safety threshold")
        sys.exit(1)

    print("\nBenchmark complete!")


if __name__ == '__main__':
    main()
