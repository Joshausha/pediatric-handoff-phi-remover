#!/usr/bin/env python
"""
Validation runner for Pediatric Handoff PHI Remover.

Orchestrates:
1. Presidio evaluation on validation dataset
2. Bootstrap confidence interval calculation (95% CI)
3. Error taxonomy generation
4. Compliance report generation with deployment decision

This is the main entry point for HIPAA Expert Determination validation.

Usage:
    python tests/run_validation.py --input tests/synthetic_handoffs.json
    python tests/run_validation.py --input validation_set.json --n-bootstrap 10000 --report VALIDATION_REPORT.md
"""

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.evaluate_presidio import PresidioEvaluator, EvaluationMetrics, load_dataset
from tests.error_taxonomy import build_error_taxonomy, generate_error_report, FailureMode


def run_validation(
    input_path: Path,
    n_bootstrap: int = 10000,
    overlap_threshold: float = 0.5,
    verbose: bool = True,
) -> dict:
    """
    Run complete validation pipeline.

    Args:
        input_path: Path to validation dataset JSON
        n_bootstrap: Number of bootstrap iterations for CI calculation
        overlap_threshold: Overlap threshold for span matching
        verbose: Show progress messages

    Returns:
        Dict with keys:
            - metrics: EvaluationMetrics with recall, precision, F2, CI bounds
            - error_taxonomy: Dict mapping FailureMode to list of cases
            - deployment_readiness: Dict with decision and reasoning
    """
    if verbose:
        print("=" * 60)
        print("PEDIATRIC HANDOFF PHI REMOVER - VALIDATION PIPELINE")
        print("=" * 60)
        print()

    # Load dataset
    if verbose:
        print(f"Loading validation dataset from {input_path}...")

    dataset = load_dataset(input_path)

    if verbose:
        print(f"✓ Loaded {len(dataset)} handoffs")
        print()

    # Run Presidio evaluation
    if verbose:
        print("Running Presidio evaluation...")

    evaluator = PresidioEvaluator(overlap_threshold=overlap_threshold)
    metrics, results = evaluator.evaluate_dataset(dataset, verbose=verbose)

    if verbose:
        print(f"✓ Evaluation complete")
        print(f"  Recall: {metrics.recall:.1%}")
        print(f"  Precision: {metrics.precision:.1%}")
        print(f"  F2 Score: {metrics.f2:.1%}")
        print()

    # Calculate bootstrap confidence intervals
    if verbose:
        print(f"Calculating bootstrap confidence intervals (n={n_bootstrap})...")

    recall_mean, (recall_lower, recall_upper) = metrics.bootstrap_recall_ci(
        metrics._y_true, metrics._y_pred, n_bootstrap=n_bootstrap
    )
    prec_mean, (prec_lower, prec_upper) = metrics.bootstrap_precision_ci(
        metrics._y_true, metrics._y_pred, n_bootstrap=n_bootstrap
    )

    if verbose:
        print(f"✓ CI calculated")
        print(f"  Recall 95% CI: [{recall_lower:.1%}, {recall_upper:.1%}]")
        print(f"  Precision 95% CI: [{prec_lower:.1%}, {prec_upper:.1%}]")
        print()

    # Build error taxonomy
    if verbose:
        print("Building error taxonomy...")

    taxonomy = build_error_taxonomy(results)

    total_errors = sum(len(cases) for cases in taxonomy.values())
    if verbose:
        print(f"✓ Taxonomy complete")
        print(f"  Total false negatives: {total_errors}")
        for mode in FailureMode:
            count = len(taxonomy[mode])
            if count > 0:
                print(f"  - {mode.value}: {count}")
        print()

    # Deployment decision
    if verbose:
        print("Making deployment decision...")

    # Decision based on 95% CI lower bound >= 95%
    deploy_threshold = 0.95
    meets_threshold = recall_lower >= deploy_threshold

    deployment_readiness = {
        "decision": "DEPLOY" if meets_threshold else "RETURN_TO_PHASE_4",
        "recall_point_estimate": float(metrics.recall),
        "recall_ci_lower": float(recall_lower),
        "recall_ci_upper": float(recall_upper),
        "threshold": float(deploy_threshold),
        "meets_threshold": bool(meets_threshold),
        "reasoning": (
            f"Recall 95% CI lower bound ({recall_lower:.1%}) {'meets' if meets_threshold else 'does not meet'} "
            f"the {deploy_threshold:.0%} threshold required for clinical deployment."
        )
    }

    if verbose:
        print(f"✓ Decision: {deployment_readiness['decision']}")
        print(f"  {deployment_readiness['reasoning']}")
        print()

    return {
        "metrics": {
            "total_expected": int(metrics.total_expected),
            "total_detected": int(metrics.total_detected),
            "true_positives": int(metrics.true_positives),
            "false_negatives": int(metrics.false_negatives),
            "false_positives": int(metrics.false_positives),
            "precision": float(metrics.precision),
            "recall": float(metrics.recall),
            "f1": float(metrics.f1),
            "f2": float(metrics.f2),
            "precision_mean": float(prec_mean),
            "precision_ci_lower": float(prec_lower),
            "precision_ci_upper": float(prec_upper),
            "recall_mean": float(recall_mean),
            "recall_ci_lower": float(recall_lower),
            "recall_ci_upper": float(recall_upper),
        },
        "error_taxonomy": {
            mode.value: [
                {
                    "entity_type": case.entity_type,
                    "text": case.text,
                    "context": case.context,
                    "start": case.start,
                    "end": case.end,
                    "failure_mode": case.failure_mode.value,
                }
                for case in cases
            ]
            for mode, cases in taxonomy.items()
        },
        "deployment_readiness": deployment_readiness,
        "metadata": {
            "validation_date": datetime.now().isoformat(),
            "n_handoffs": len(dataset),
            "n_bootstrap_iterations": n_bootstrap,
            "overlap_threshold": overlap_threshold,
        }
    }


def generate_compliance_report(validation_results: dict, output_path: Path) -> None:
    """
    Generate VALIDATION_REPORT.md with full compliance documentation.

    Args:
        validation_results: Output from run_validation()
        output_path: Path to write markdown report
    """
    metrics = validation_results["metrics"]
    taxonomy = validation_results["error_taxonomy"]
    deployment = validation_results["deployment_readiness"]
    metadata = validation_results["metadata"]

    lines = [
        "# Validation Report: Pediatric Handoff PHI Remover",
        "",
        f"**Validation Date:** {metadata['validation_date']}  ",
        f"**Dataset Size:** {metadata['n_handoffs']} handoffs  ",
        f"**Bootstrap Iterations:** {metadata['n_bootstrap_iterations']}  ",
        "",
        "## Executive Summary",
        "",
        "| Metric | Value | 95% Confidence Interval |",
        "|--------|-------|------------------------|",
        f"| **Recall** | {metrics['recall']:.1%} | [{metrics['recall_ci_lower']:.1%}, {metrics['recall_ci_upper']:.1%}] |",
        f"| **Precision** | {metrics['precision']:.1%} | [{metrics['precision_ci_lower']:.1%}, {metrics['precision_ci_upper']:.1%}] |",
        f"| **F1 Score** | {metrics['f1']:.1%} | - |",
        f"| **F2 Score** | {metrics['f2']:.1%} | - |",
        "",
        "### Deployment Decision",
        "",
        f"**Decision:** `{deployment['decision']}`",
        "",
        f"**Rationale:** {deployment['reasoning']}",
        "",
        f"**Safety Threshold:** Recall 95% CI lower bound must be ≥ {deployment['threshold']:.0%}",
        "",
    ]

    # Detailed metrics
    lines.extend([
        "## Detailed Metrics",
        "",
        "### Detection Performance",
        "",
        f"- **Total PHI spans (ground truth):** {metrics['total_expected']}",
        f"- **Total spans detected:** {metrics['total_detected']}",
        f"- **True positives:** {metrics['true_positives']}",
        f"- **False negatives (PHI leaks):** {metrics['false_negatives']}",
        f"- **False positives (over-redaction):** {metrics['false_positives']}",
        "",
        "### Statistical Validation",
        "",
        "Bootstrap confidence intervals (95%) calculated using percentile method with "
        f"{metadata['n_bootstrap_iterations']:,} iterations:",
        "",
        f"- **Recall CI:** [{metrics['recall_ci_lower']:.1%}, {metrics['recall_ci_upper']:.1%}]",
        f"- **Precision CI:** [{metrics['precision_ci_lower']:.1%}, {metrics['precision_ci_upper']:.1%}]",
        "",
    ])

    # Error taxonomy
    total_errors = sum(len(cases) for cases in taxonomy.values())

    if total_errors > 0:
        lines.extend([
            "## Error Taxonomy",
            "",
            f"**Total false negatives:** {total_errors}",
            "",
            "### Breakdown by Failure Mode",
            "",
        ])

        for mode_str, cases in taxonomy.items():
            if not cases:
                continue

            count = len(cases)
            pct = 100 * count / total_errors

            lines.extend([
                f"#### {mode_str.upper().replace('_', ' ')} ({count} cases, {pct:.1f}%)",
                "",
            ])

            # Show examples
            for i, case in enumerate(cases[:5], 1):
                lines.append(f"{i}. **{case['entity_type']}**: `{case['text']}`")

            if len(cases) > 5:
                lines.append(f"   _(and {len(cases) - 5} more)_")

            lines.append("")

            # Recommendations
            recommendations = {
                "pattern_miss": "→ Add regex patterns to custom recognizers",
                "span_boundary": "→ Review entity boundary detection logic",
                "deny_list_filtered": "→ Remove incorrect deny list entries",
                "novel_variant": "→ Expand synthetic training data coverage",
                "threshold_miss": "→ Lower score threshold (currently 0.30)",
                "ner_miss": "→ Train custom spaCy NER model or add patterns",
            }

            if mode_str in recommendations:
                lines.extend([
                    f"**Recommendation:** {recommendations[mode_str]}",
                    "",
                ])
    else:
        lines.extend([
            "## Error Taxonomy",
            "",
            "✅ **NO ERRORS** - 100% recall achieved!",
            "",
        ])

    # Methodology
    lines.extend([
        "## Methodology",
        "",
        "### Dataset",
        "",
        f"- **Source:** Synthetic handoff dataset (clinical patterns based on pediatric residency experience)",
        f"- **Size:** {metadata['n_handoffs']} handoffs",
        f"- **PHI entities:** PERSON, GUARDIAN_NAME, MEDICAL_RECORD_NUMBER, ROOM, DATE_TIME, LOCATION, PHONE_NUMBER, EMAIL_ADDRESS, PEDIATRIC_AGE",
        "",
        "**Note on External Validation:** This validation uses synthetic data designed to represent realistic",
        "clinical patterns. External validation on real de-identified transcripts requires IRB approval for",
        "prospective collection. For this personal quality improvement project, synthetic validation serves",
        "as the practical validation path.",
        "",
        "### Evaluation Method",
        "",
        "- **Span matching:** Jaccard-like overlap (union-based)",
        f"- **Overlap threshold:** {metadata['overlap_threshold']:.1%} minimum overlap to consider match",
        "- **Type matching:** Ground truth types mapped to Presidio entity types",
        "",
        "### Statistical Analysis",
        "",
        "- **Bootstrap method:** Percentile method with replacement sampling",
        f"- **Iterations:** {metadata['n_bootstrap_iterations']:,}",
        "- **Confidence level:** 95%",
        "- **Random seed:** 42 (reproducibility)",
        "",
        "### Safety Threshold",
        "",
        f"Deployment requires recall 95% CI lower bound ≥ {deployment['threshold']:.0%} to ensure PHI safety.",
        "This threshold accounts for statistical uncertainty in recall estimation.",
        "",
        "## HIPAA Compliance",
        "",
        "### Expert Determination (§164.514(b))",
        "",
        "This validation provides statistical evidence for HIPAA Expert Determination:",
        "",
        f"- **Recall performance:** {metrics['recall']:.1%} with 95% CI [{metrics['recall_ci_lower']:.1%}, {metrics['recall_ci_upper']:.1%}]",
        "- **Residual risk assessment:** Based on false negative rate and failure mode analysis",
        "- **Statistical rigor:** Bootstrap confidence intervals quantify estimation uncertainty",
        "",
        "### Intended Use",
        "",
        "This tool is intended for personal quality improvement use only:",
        "",
        "- **Use case:** Transcribe and de-identify pediatric handoff recordings for personal study",
        "- **Data handling:** All processing occurs locally (no external API calls)",
        "- **Risk mitigation:** User reviews de-identified output before any sharing",
        "",
        "---",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
    ])

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="Run validation pipeline and generate compliance report"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Input validation dataset (JSON file with handoffs)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output JSON file for validation results (optional)"
    )
    parser.add_argument(
        "--report", "-r",
        type=Path,
        help="Output markdown file for compliance report (optional)"
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=10000,
        help="Number of bootstrap iterations for CI calculation (default: 10000)"
    )
    parser.add_argument(
        "--overlap",
        type=float,
        default=0.5,
        help="Overlap threshold for span matching (default: 0.5)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )

    args = parser.parse_args()

    # Check input exists
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Run validation
    results = run_validation(
        input_path=args.input,
        n_bootstrap=args.n_bootstrap,
        overlap_threshold=args.overlap,
        verbose=not args.quiet,
    )

    # Save JSON results if requested
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)

        if not args.quiet:
            print(f"✓ Results saved to {args.output}")

    # Generate compliance report if requested
    if args.report:
        generate_compliance_report(results, args.report)

        if not args.quiet:
            print(f"✓ Report saved to {args.report}")

    # Print summary
    if not args.quiet:
        print()
        print("=" * 60)
        print("VALIDATION COMPLETE")
        print("=" * 60)
        print()
        print(f"Decision: {results['deployment_readiness']['decision']}")
        print(f"Recall CI: [{results['metrics']['recall_ci_lower']:.1%}, {results['metrics']['recall_ci_upper']:.1%}]")
        print()

    # Exit with error code if deployment not recommended
    if results['deployment_readiness']['decision'] != "DEPLOY":
        sys.exit(1)


if __name__ == "__main__":
    main()
