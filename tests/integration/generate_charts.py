"""Generate metric comparison charts for visual analysis.

This module creates visualizations comparing unweighted, frequency-weighted,
and risk-weighted metrics to show divergence patterns.
"""

from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np


def generate_metric_comparison_chart(metrics: Dict[str, float], output_path: Path) -> Path:
    """Generate grouped bar chart comparing three metric types.

    Args:
        metrics: Dict with keys:
            - recall, precision (unweighted)
            - freq_weighted_recall, freq_weighted_precision
            - risk_weighted_recall, risk_weighted_precision
        output_path: Where to save the PNG chart

    Returns:
        Path to the generated chart
    """
    # Extract metric values
    unweighted = {
        "recall": metrics["recall"],
        "precision": metrics["precision"],
    }
    freq_weighted = {
        "recall": metrics["freq_weighted_recall"],
        "precision": metrics["freq_weighted_precision"],
    }
    risk_weighted = {
        "recall": metrics["risk_weighted_recall"],
        "precision": metrics["risk_weighted_precision"],
    }

    # Set up the figure
    fig, ax = plt.subplots(figsize=(12, 7))

    # X-axis positions for three groups
    x = np.arange(3)
    width = 0.35  # Width of bars

    # Create bars
    recall_bars = ax.bar(
        x - width / 2,
        [unweighted["recall"], freq_weighted["recall"], risk_weighted["recall"]],
        width,
        label="Recall",
        color="#4CAF50",
    )
    precision_bars = ax.bar(
        x + width / 2,
        [unweighted["precision"], freq_weighted["precision"], risk_weighted["precision"]],
        width,
        label="Precision",
        color="#2196F3",
    )

    # Add value labels on top of bars
    for bars in [recall_bars, precision_bars]:
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1%}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    # Add 85% threshold line
    ax.axhline(
        y=0.85,
        color="red",
        linestyle="--",
        linewidth=2,
        label="85% threshold",
        alpha=0.7,
    )

    # Customize chart
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Metric Comparison: Unweighted vs Weighted", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(
        ["Unweighted\n(Safety Floor)", "Frequency-weighted\n(Spoken)", "Risk-weighted\n(Severity)"]
    )
    ax.set_ylim(0, 1.0)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(axis="y", alpha=0.3, linestyle=":")

    # Save chart
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    return output_path


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add parent directory to path to import run_validation
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from run_validation import run_validation

    # Run validation - now returns weighted metrics directly in the dict
    print("Running validation to extract metrics...")
    results = run_validation(
        input_path=Path("tests/synthetic_handoffs.json"),
        n_bootstrap=1000,
        verbose=True,
    )

    # Extract metrics directly from the returned dict
    # (16-01 Task 1 added these to the return value)
    metrics = {
        "recall": results["metrics"]["recall"],
        "precision": results["metrics"]["precision"],
        "freq_weighted_recall": results["metrics"]["freq_weighted_recall"],
        "freq_weighted_precision": results["metrics"]["freq_weighted_precision"],
        "risk_weighted_recall": results["metrics"]["risk_weighted_recall"],
        "risk_weighted_precision": results["metrics"]["risk_weighted_precision"],
    }

    output_path = Path("tests/artifacts/metric_comparison.png")
    generate_metric_comparison_chart(metrics, output_path)
    print(f"\n✓ Chart saved to {output_path}")
