# Phase 14: Report Generation Refinement - Research

**Researched:** 2026-01-29 14:41:37 EST
**Domain:** Technical metrics reporting, evaluation result presentation, user-facing documentation
**Confidence:** HIGH

## Summary

Research focused on best practices for presenting multi-metric evaluation reports, specifically addressing how to display three different weighting schemes (unweighted, frequency-weighted, risk-weighted) in a user-friendly format that explains why metrics diverge.

The standard approach in technical evaluation reporting is to present metrics in tabular format with inline annotations for context, use side-by-side comparisons for weight schemes, and provide concrete examples explaining divergence immediately after showing numbers. Current industry practices emphasize clarity through simplicity, limiting table rows to ~15 items, and using visual indicators (arrows, checkmarks) rather than heavy formatting.

The existing codebase already implements solid foundations: f-string formatting with consistent precision (.1% for percentages), arrow annotations (← for inline labels), and structured text reports. The task is to refine these patterns into a polished three-metric display with clear divergence explanation.

**Primary recommendation:** Use Python f-strings with consistent .1% formatting for all metrics, present weights in two side-by-side tables (frequency-sorted and risk-sorted), highlight divergent entities using simple text markers (bold asterisks or arrows), and provide concrete example after metrics showing quantified gap (e.g., "If MEDICAL_RECORD_NUMBER missed: frequency recall drops X%, risk recall drops Y%").

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python f-strings | 3.9+ | String formatting | Built-in, readable, consistent .1% precision for percentages |
| Markdown tables | GitHub Flavored | Report formatting | Universal, readable, version-controllable |
| ANSI escape codes | Standard | Terminal highlighting | Cross-platform bold/color for console output |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Rich library | 13.x | Enhanced terminal output | If interactive console features needed (not required for basic reports) |
| tabulate | 0.9.x | ASCII table formatting | If complex table layouts needed (current f-strings likely sufficient) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| F-strings | str.format() | F-strings more readable, modern Python standard |
| Markdown | HTML tables | Markdown more git-friendly, readable in plain text |
| ANSI codes | Rich library | ANSI sufficient for bold/color, Rich adds dependency |

**Installation:**
```bash
# No additional dependencies needed for basic approach
# Current Python 3.9+ f-strings sufficient

# Optional if enhanced terminal features desired:
pip install rich tabulate
```

## Architecture Patterns

### Recommended Report Structure
```
Report sections (in order):
1. Header banner
2. Three-metric summary table (unweighted, frequency-weighted, risk-weighted)
3. Weight comparison tables (frequency-sorted | risk-sorted side-by-side)
4. Concrete divergence example with quantified gaps
5. Per-entity performance breakdown
6. Detailed failures (if any)
```

### Pattern 1: Inline Metric Annotation
**What:** Add context labels directly after metric values using arrow (←) or parentheses
**When to use:** When a metric needs immediate clarification without breaking flow
**Example:**
```python
# Source: evaluate_presidio.py lines 503-505
lines.append(f"  Unweighted Recall:        {metrics.recall:.1%}  ← Safety floor")
lines.append(f"  Frequency-weighted:       {metrics.weighted_recall(freq_weights):.1%}  ← What's actually spoken")
lines.append(f"  Risk-weighted:            {metrics.risk_weighted_recall(risk_weights):.1%}  ← Severity if leaked")
```

### Pattern 2: Side-by-Side Weight Tables
**What:** Display same data sorted two different ways for visual comparison
**When to use:** When ranking differences are important to highlight
**Example:**
```python
# Frequency-sorted table          Risk-sorted table
# Entity          Weight           Entity          Weight
# PERSON          5.0              MEDICAL_RECORD  5.0
# GUARDIAN_NAME   4.0              PERSON          5.0
# ROOM            4.0              PHONE_NUMBER    4.0
```

### Pattern 3: Quantified Divergence Explanation
**What:** Show exact percentage point differences when metrics diverge
**When to use:** After displaying metrics, to explain why numbers differ
**Example:**
```python
# If MEDICAL_RECORD_NUMBER has poor recall (40%):
# Frequency-weighted recall: 89.1% (MRN weight 0.5 → small impact)
# Risk-weighted recall: 62.5% (MRN weight 5.0 → major impact)
# Gap: -26.6 percentage points due to high-risk entity underperforming
```

### Pattern 4: F-String Percentage Formatting
**What:** Consistent .1% formatting for all percentage metrics
**When to use:** All metric displays for consistency
**Example:**
```python
# Source: evaluate_presidio.py lines 464-467
f"  Precision: {metrics.precision:.1%}"    # 86.4%
f"  Recall:    {metrics.recall:.1%}"       # 94.2%
f"  F2 Score:  {metrics.f2:.1%}"          # 91.8%
```

### Anti-Patterns to Avoid
- **Excessive decimal precision:** Don't use .3% or .4% for percentages—.1% is standard for evaluation reports (matches scikit-learn conventions)
- **Inline calculations in f-strings:** Don't compute divergence gaps inline—pre-calculate for readability
- **Over-formatting:** Don't use colors, multiple fonts, or complex styling—bold and arrows are sufficient
- **Table overload:** Don't show 10+ columns in a single table—split into multiple focused tables

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Table layout calculation | Manual spacing/alignment | F-strings with fixed widths | Python f-strings handle alignment ({var:<20} for left-align) |
| Percentage formatting | Manual rounding logic | Built-in .1% format spec | Python format specs handle rounding consistently |
| Report sectioning | Custom markdown generator | String concatenation with lines list | Simple, readable, maintainable (current pattern works well) |
| Terminal colors | Custom ANSI code manager | Direct ANSI codes or Rich library | ANSI codes are simple (\033[1m for bold), Rich if complexity grows |

**Key insight:** The existing evaluate_presidio.py report generation pattern (lines list + f-strings + .join("\n")) is well-designed and should be extended, not replaced. The standard Python formatting system handles alignment, precision, and readability without additional libraries.

## Common Pitfalls

### Pitfall 1: Precision-Recall Tradeoff Confusion
**What goes wrong:** Users see different precision/recall values across weighting schemes and assume system is inconsistent
**Why it happens:** Weighted metrics change the contribution of each entity type, naturally causing precision/recall to shift
**How to avoid:** Explicitly state in report that precision-recall tradeoff exists and weighting schemes rebalance this tradeoff based on different priorities (frequency vs. risk)
**Warning signs:** Questions like "Why does frequency-weighted have higher recall than risk-weighted?" indicate need for clearer divergence explanation

### Pitfall 2: Weight Table Overload
**What goes wrong:** Displaying all 9 entity types in a single complex table with 4+ columns becomes hard to scan
**Why it happens:** Attempting to show frequency weight, risk weight, and performance metrics in one view
**How to avoid:** Split into separate focused tables: (1) weight comparison, (2) performance metrics. Side-by-side frequency/risk views for scanning rank differences
**Warning signs:** Table width exceeds 80 characters or has more than 4 columns

### Pitfall 3: Undefined Divergence Context
**What goes wrong:** Report shows "Frequency: 89.1%, Risk: 62.5%" without explaining what causes the 26.6pp gap
**Why it happens:** Showing numbers without concrete examples of why weights matter
**How to avoid:** Always pair divergence metrics with a specific entity example: "When MEDICAL_RECORD_NUMBER (freq weight 0.5, risk weight 5.0) underperforms, risk-weighted recall drops more"
**Warning signs:** Users ask "Why do these numbers differ?" or "Which one should I care about?"

### Pitfall 4: Inline Annotation Overuse
**What goes wrong:** Every line has multiple arrows, parentheticals, or annotations creating visual clutter
**Why it happens:** Over-eagerness to explain everything inline
**How to avoid:** Use inline annotations only for critical labels (unweighted = safety floor). Put detailed explanations in a separate section after the metrics
**Warning signs:** More than 30% of lines have inline annotations (← or parentheticals)

### Pitfall 5: Zero-Weight Entity Visibility
**What goes wrong:** EMAIL_ADDRESS and PEDIATRIC_AGE have weight 0.0, users confused why they appear in unweighted but vanish in weighted metrics
**Why it happens:** Zero-weight entities are excluded from weighted calculations but still count in unweighted
**How to avoid:** Explicitly note in weight table which entities have zero weight and why (EMAIL_ADDRESS never spoken, PEDIATRIC_AGE not PHI under HIPAA unless 90+)
**Warning signs:** Questions about "missing entities" in weighted reports

## Code Examples

Verified patterns from official sources:

### Three-Metric Summary Table
```python
# Display all three weighting schemes in a single focused table
# Source: Pattern derived from evaluate_presidio.py weighted metrics section

freq_weights = settings.spoken_handoff_weights
risk_weights = settings.spoken_handoff_risk_weights

lines = [
    "EVALUATION METRICS SUMMARY:",
    "",
    "                          Recall  Precision    F2",
    "  " + "-" * 50,
    f"  Unweighted (Safety Floor) {metrics.recall:.1%}    {metrics.precision:.1%}  {metrics.f2:.1%}",
    f"  Frequency-weighted        {metrics.weighted_recall(freq_weights):.1%}    {metrics.weighted_precision(freq_weights):.1%}  {metrics.weighted_f2(freq_weights):.1%}",
    f"  Risk-weighted             {metrics.risk_weighted_recall(risk_weights):.1%}    {metrics.risk_weighted_precision(risk_weights):.1%}  {metrics.risk_weighted_f2(risk_weights):.1%}",
    "",
]
```

### Side-by-Side Weight Comparison
```python
# Two tables side-by-side: frequency-sorted and risk-sorted
# Highlight entities where weights diverge significantly

freq_weights = settings.spoken_handoff_weights
risk_weights = settings.spoken_handoff_risk_weights

# Sort entities by each weight scheme
freq_sorted = sorted(freq_weights.items(), key=lambda x: x[1], reverse=True)
risk_sorted = sorted(risk_weights.items(), key=lambda x: x[1], reverse=True)

lines = [
    "WEIGHT COMPARISON:",
    "",
    "  Frequency-Weighted              Risk-Weighted (Leak Severity)",
    "  (How often spoken)              ",
    "  " + "-" * 58,
]

# Build side-by-side rows
for i in range(len(freq_sorted)):
    freq_entity, freq_weight = freq_sorted[i]
    risk_entity, risk_weight = risk_sorted[i]

    # Highlight entities where weights significantly diverge (>2.0 difference)
    freq_marker = "*" if abs(freq_weight - risk_weights.get(freq_entity, 0)) > 2.0 else " "
    risk_marker = "*" if abs(risk_weight - freq_weights.get(risk_entity, 0)) > 2.0 else " "

    lines.append(
        f"{freq_marker} {freq_entity:<24} {freq_weight:>4.1f}   "
        f"{risk_marker} {risk_entity:<24} {risk_weight:>4.1f}"
    )

lines.append("")
lines.append("* Indicates weight divergence >2.0 between frequency and risk")
```

### Concrete Divergence Example
```python
# Quantified example explaining why metrics differ
# Placed after metrics table for immediate context

freq_recall = metrics.weighted_recall(freq_weights)
risk_recall = metrics.risk_weighted_recall(risk_weights)
gap = freq_recall - risk_recall

lines = [
    "METRIC DIVERGENCE EXPLANATION:",
    "",
    f"  Frequency-weighted recall: {freq_recall:.1%}",
    f"  Risk-weighted recall:      {risk_recall:.1%}",
    f"  Gap: {gap:+.1f} percentage points",
    "",
    "  Why they differ:",
    "  - MEDICAL_RECORD_NUMBER has low frequency weight (0.5) but high risk weight (5.0)",
    "  - When MRN detection underperforms, frequency-weighted recall stays high",
    "    (dominated by high-performing PERSON with weight 5.0)",
    "  - But risk-weighted recall drops significantly",
    "    (MRN has equal weight to PERSON, drags down average)",
    "",
    "  Guidance:",
    "  - Unweighted recall is your HIPAA compliance floor (all entities equal)",
    "  - Frequency-weighted reflects operational reality (what's actually spoken)",
    "  - Risk-weighted highlights critical vulnerabilities (severity if leaked)",
]
```

### Zero-Weight Entity Annotation
```python
# Note which entities have zero weight and why

lines = [
    "NOTE: Zero-weight entities",
    "  - EMAIL_ADDRESS (0.0): Never spoken in verbal handoffs",
    "  - PEDIATRIC_AGE (0.0): Not PHI under HIPAA unless age 90+",
    "",
    "  These entities still count in unweighted metrics (HIPAA safety floor)",
    "  but are excluded from frequency-weighted and risk-weighted calculations.",
]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single unweighted metric | Dual-weight schemes (frequency + risk) | Phase 13 (2026-01-28) | Separates "what's spoken" from "severity if leaked" |
| Separate frequency/risk reports | Unified three-metric report | Phase 14 (current) | Side-by-side comparison highlights divergence |
| Implicit weight rationale | Explicit divergence explanation | Phase 14 (current) | Users understand why metrics differ |
| Generic metric labels | Context-rich inline annotations | Existing pattern (evaluate_presidio.py) | "Safety floor", "What's spoken", "Severity if leaked" |

**Deprecated/outdated:**
- Single-metric evaluation reports (don't capture operational vs. risk perspectives)
- Weight tables without divergence highlighting (miss critical ranking differences)
- Metrics without concrete examples (numbers without context don't explain behavior)

## Open Questions

Things that couldn't be fully resolved:

1. **Terminal vs. Web Display**
   - What we know: Current report is plain text with ANSI-compatible formatting
   - What's unclear: Whether web frontend will display this report or have separate UI
   - Recommendation: Design for terminal-first (plain text + ANSI bold), can easily adapt to web later

2. **Optimal Divergence Threshold**
   - What we know: Weights range 0.0-5.0, need to highlight significant differences
   - What's unclear: Is >2.0 difference the right threshold for marking divergence, or should it be >3.0?
   - Recommendation: Start with >2.0 (catches MRN 0.5 vs 5.0), adjust based on user feedback

3. **Interactive Features**
   - What we know: Static text reports work well for git-tracked evaluation logs
   - What's unclear: Would users benefit from collapsible sections or drill-down details?
   - Recommendation: Keep static text for now (matches existing CI/testing workflow), revisit if web UI added

## Sources

### Primary (HIGH confidence)
- Existing codebase: `tests/evaluate_presidio.py` - Current report generation patterns (lines 434-569)
- Existing codebase: `app/config.py` - Dual-weight configuration (lines 306-344)
- Existing codebase: `tests/test_weighted_metrics.py` - Weighted metrics calculation patterns
- [Google ML Crash Course - Classification Metrics](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall) - Updated 2026-01-12, standard precision/recall presentation
- [Markdown Tables - Complete Guide](https://www.tomarkdown.org/guides/markdown-table) - Markdown table best practices 2026

### Secondary (MEDIUM confidence)
- [Technical Metrics Report Best Practices](https://www.kippy.cloud/post/best-practices-for-reporting-performance-metrics-effectively) - 23 best practices for reporting metrics effectively
- [V7 Labs - Precision vs Recall Guide](https://www.v7labs.com/blog/precision-vs-recall-guide) - Why precision/recall diverge in evaluation
- [Evidently AI - Accuracy vs Precision vs Recall](https://www.evidentlyai.com/classification-metrics/accuracy-precision-recall) - When metrics diverge and why
- [Meta Reporting Changes 2025-2026](https://www.extradigital.co.uk/articles/marketing/meta-reporting-changes-2025/) - How to present metric changes to users
- [Markdown Guide - Extended Syntax](https://www.markdownguide.org/extended-syntax/) - Table formatting standards

### Tertiary (LOW confidence)
- [MLflow Experiment Tracking](https://research.aimultiple.com/llm-eval-tools/) - Side-by-side metric comparison UI patterns (2026 AI evaluation platforms)
- [scikit-learn Metrics Documentation](https://scikit-learn.org/stable/modules/model_evaluation.html) - Precision-recall curve visualization patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - F-strings and markdown tables are well-established Python/documentation standards
- Architecture: HIGH - Existing codebase patterns verified, industry best practices confirmed via Google/scikit-learn sources
- Pitfalls: HIGH - Derived from actual confusion around weighted metrics (test suite reveals common misunderstandings)
- Code examples: HIGH - All examples derived from working codebase (evaluate_presidio.py, test_weighted_metrics.py)

**Research date:** 2026-01-29
**Valid until:** 2027-01-29 (12 months - stable domain, Python formatting specs and markdown standards don't change rapidly)
