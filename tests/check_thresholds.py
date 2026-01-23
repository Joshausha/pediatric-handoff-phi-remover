#!/usr/bin/env python3
"""
Check PHI detection metrics against safety thresholds.

This script validates that the PHI detection system meets minimum
recall (for safety) and precision (for clinical utility) thresholds.

Usage:
    python tests/evaluate_presidio.py --json | python tests/check_thresholds.py
    python tests/check_thresholds.py metrics.json
    python tests/check_thresholds.py --recall-min 0.90 --precision-min 0.65 metrics.json

Exit codes:
    0: All thresholds passed
    1: One or more thresholds failed
"""

import argparse
import json
import sys
from pathlib import Path


# Default safety thresholds
DEFAULT_RECALL_MIN = 0.95      # HIPAA compliance: catch >95% of PHI
DEFAULT_PRECISION_MIN = 0.70   # Clinical utility: don't over-redact
DEFAULT_F2_MIN = 0.90          # Recall-weighted: balance safety and utility


def check_thresholds(
    metrics: dict,
    recall_min: float = DEFAULT_RECALL_MIN,
    precision_min: float = DEFAULT_PRECISION_MIN,
    f2_min: float = DEFAULT_F2_MIN,
) -> tuple[bool, list[str]]:
    """
    Check metrics against thresholds.

    Args:
        metrics: Dict with 'recall', 'precision', 'f2' keys
        recall_min: Minimum recall threshold
        precision_min: Minimum precision threshold
        f2_min: Minimum F2 score threshold

    Returns:
        Tuple of (all_passed, list of failure messages)
    """
    failures = []

    recall = metrics.get("recall", 0)
    precision = metrics.get("precision", 0)
    f2 = metrics.get("f2", 0)

    if recall < recall_min:
        failures.append(
            f"RECALL: {recall:.1%} < {recall_min:.0%} threshold "
            f"(PHI LEAK RISK: {(1 - recall) * 100:.1f}% of PHI may be missed)"
        )

    if precision < precision_min:
        failures.append(
            f"PRECISION: {precision:.1%} < {precision_min:.0%} threshold "
            f"(OVER-REDACTION: {(1 - precision) * 100:.1f}% false positives)"
        )

    if f2 < f2_min:
        failures.append(
            f"F2 SCORE: {f2:.1%} < {f2_min:.0%} threshold "
            f"(OVERALL: recall-weighted performance below target)"
        )

    return len(failures) == 0, failures


def main():
    parser = argparse.ArgumentParser(
        description="Check PHI detection metrics against safety thresholds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help="JSON metrics file (or reads from stdin if not provided)",
    )
    parser.add_argument(
        "--recall-min",
        type=float,
        default=DEFAULT_RECALL_MIN,
        help=f"Minimum recall threshold (default: {DEFAULT_RECALL_MIN:.0f})",
    )
    parser.add_argument(
        "--precision-min",
        type=float,
        default=DEFAULT_PRECISION_MIN,
        help=f"Minimum precision threshold (default: {DEFAULT_PRECISION_MIN:.0f})",
    )
    parser.add_argument(
        "--f2-min",
        type=float,
        default=DEFAULT_F2_MIN,
        help=f"Minimum F2 score threshold (default: {DEFAULT_F2_MIN:.0f})",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output failures (no success messages)",
    )

    args = parser.parse_args()

    # Load metrics from file or stdin
    try:
        if args.input:
            with open(args.input) as f:
                data = json.load(f)
        else:
            data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Extract metrics (handle both direct and nested formats)
    metrics = data.get("metrics", data)

    # Check thresholds
    passed, failures = check_thresholds(
        metrics,
        recall_min=args.recall_min,
        precision_min=args.precision_min,
        f2_min=args.f2_min,
    )

    # Output results
    if failures:
        print("=" * 60)
        print("PHI DETECTION THRESHOLD CHECK: FAILED")
        print("=" * 60)
        for failure in failures:
            print(f"  {failure}")
        print()
        print("Action required: Improve PHI detection before deployment.")
        print("=" * 60)
        sys.exit(1)
    else:
        if not args.quiet:
            print("=" * 60)
            print("PHI DETECTION THRESHOLD CHECK: PASSED")
            print("=" * 60)
            print(f"  Recall:    {metrics.get('recall', 0):.1%} >= {args.recall_min:.0%}")
            print(f"  Precision: {metrics.get('precision', 0):.1%} >= {args.precision_min:.0%}")
            print(f"  F2 Score:  {metrics.get('f2', 0):.1%} >= {args.f2_min:.0%}")
            print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()
