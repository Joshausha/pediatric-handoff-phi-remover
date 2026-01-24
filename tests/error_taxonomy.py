#!/usr/bin/env python
"""
Error taxonomy for false negative classification.

Categorizes missed PHI by failure mode to enable targeted improvements.
This enables clinicians to understand WHY specific PHI was missed and
prioritize fixes by failure mode.

Failure modes:
- PATTERN_MISS: Regex pattern didn't match this variant
- THRESHOLD_MISS: Entity detected but score below threshold
- DENY_LIST_FILTER: Incorrectly filtered by deny list
- NOVEL_VARIANT: Pattern not seen in synthetic training data
- SPAN_BOUNDARY: Partial match only (boundary mismatch)
- NER_MISS: spaCy NER didn't recognize entity
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FailureMode(Enum):
    """Classification of why PHI detection failed."""
    PATTERN_MISS = "pattern_miss"        # Regex didn't match variant
    THRESHOLD_MISS = "threshold_miss"    # Detected but score below threshold
    DENY_LIST_FILTER = "deny_list_filtered"  # Incorrectly filtered by deny list
    NOVEL_VARIANT = "novel_variant"      # Pattern not in synthetic training
    SPAN_BOUNDARY = "span_boundary"      # Partial match only
    NER_MISS = "ner_miss"               # spaCy NER didn't recognize entity


@dataclass
class FalseNegativeCase:
    """
    A single false negative with context and failure mode classification.

    Attributes:
        entity_type: PHI type (PERSON, DATE_TIME, etc.)
        text: The missed PHI text
        context: 50 chars before/after for context
        start: Start position in original text
        end: End position in original text
        failure_mode: Why detection failed
        detected_partial: If partial match exists, the partial detection
    """
    entity_type: str
    text: str
    context: str  # 50 chars before/after
    start: int
    end: int
    failure_mode: FailureMode
    detected_partial: Optional[dict] = None  # If partial match exists


def _extract_context(text: str, start: int, end: int, context_chars: int = 50) -> str:
    """
    Extract context around a span for readability.

    Args:
        text: Full text
        start: Span start position
        end: Span end position
        context_chars: Number of chars before/after to include

    Returns:
        Context string with [...] markers for truncation
    """
    ctx_start = max(0, start - context_chars)
    ctx_end = min(len(text), end + context_chars)

    before = "..." if ctx_start > 0 else ""
    after = "..." if ctx_end < len(text) else ""

    context = text[ctx_start:ctx_end]
    return f"{before}{context}{after}"


def _check_partial_overlap(fn_span: dict, detected_spans: list[dict]) -> Optional[dict]:
    """
    Check if any detected span partially overlaps the false negative.

    Args:
        fn_span: False negative span with 'start' and 'end'
        detected_spans: List of detected spans

    Returns:
        Detected span if partial overlap exists, else None
    """
    fn_start, fn_end = fn_span["start"], fn_span["end"]

    for det in detected_spans:
        det_start, det_end = det["start"], det["end"]

        # Check for any overlap
        if not (det_end <= fn_start or det_start >= fn_end):
            # Calculate overlap ratio
            overlap_start = max(fn_start, det_start)
            overlap_end = min(fn_end, det_end)
            overlap_len = overlap_end - overlap_start
            fn_len = fn_end - fn_start

            # Partial overlap if < 50% coverage
            if 0 < overlap_len < fn_len * 0.5:
                return det

    return None


def _is_deny_list_filtered(text: str, entity_type: str, deny_lists: Optional[dict] = None) -> bool:
    """
    Check if text matches a deny list term.

    Args:
        text: Text to check
        entity_type: PHI entity type
        deny_lists: Dict mapping entity types to deny list terms

    Returns:
        True if text is in deny list for this entity type
    """
    if not deny_lists:
        return False

    deny_list = deny_lists.get(entity_type, [])
    return text.lower() in [term.lower() for term in deny_list]


def _is_novel_variant(text: str, entity_type: str, training_patterns: Optional[set] = None) -> bool:
    """
    Check if text represents a novel pattern not in training data.

    Args:
        text: Text to check
        entity_type: PHI entity type
        training_patterns: Set of patterns seen in synthetic training

    Returns:
        True if this is a novel pattern
    """
    # For now, we don't track training patterns, so always return False
    # In Phase 6, we could build this from synthetic dataset
    return False


def classify_failure(
    fn_span: dict,
    detected_spans: list[dict],
    text: str,
    threshold: float = 0.30,
    deny_lists: Optional[dict] = None
) -> tuple[FailureMode, Optional[dict]]:
    """
    Classify why a false negative occurred.

    Args:
        fn_span: False negative span with keys: entity_type, text, start, end
        detected_spans: All detected spans from Presidio
        text: Full handoff text
        threshold: Score threshold used for detection
        deny_lists: Optional dict of deny lists by entity type

    Returns:
        Tuple of (FailureMode, partial_match_if_exists)
    """
    entity_type = fn_span["entity_type"]
    fn_text = fn_span["text"]

    # Check for partial overlap (SPAN_BOUNDARY)
    partial = _check_partial_overlap(fn_span, detected_spans)
    if partial:
        return FailureMode.SPAN_BOUNDARY, partial

    # Check if deny list filtered (DENY_LIST_FILTER)
    if _is_deny_list_filtered(fn_text, entity_type, deny_lists):
        return FailureMode.DENY_LIST_FILTER, None

    # Check if novel variant (NOVEL_VARIANT)
    if _is_novel_variant(fn_text, entity_type):
        return FailureMode.NOVEL_VARIANT, None

    # Default to pattern miss (most common)
    # In future, could check if spaCy NER recognized it (NER_MISS)
    # or if it was detected with low score (THRESHOLD_MISS)
    return FailureMode.PATTERN_MISS, None


def build_error_taxonomy(results: list) -> dict[FailureMode, list[FalseNegativeCase]]:
    """
    Build error taxonomy from evaluation results.

    Groups all false negatives by failure mode for analysis.

    Args:
        results: List of DetectionResult objects from evaluation

    Returns:
        Dict mapping FailureMode to list of FalseNegativeCase instances
    """
    taxonomy = {mode: [] for mode in FailureMode}

    for result in results:
        if not result.false_negatives:
            continue

        # Get the full text from the handoff
        # For now, we'll extract from one of the spans
        # In practice, we'd want to pass the full handoff text
        for fn_span in result.false_negatives:
            # Convert PHISpan to dict for classification
            fn_dict = {
                "entity_type": fn_span.entity_type,
                "text": fn_span.text,
                "start": fn_span.start,
                "end": fn_span.end,
            }

            # For context extraction, we need the full text
            # We'll build it from the span (not perfect, but works)
            # In production, would pass full handoff text
            context = fn_span.text  # Simplified for now

            # Classify the failure
            failure_mode, partial = classify_failure(
                fn_dict,
                result.detected_spans,
                ""  # Full text not available in current structure
            )

            case = FalseNegativeCase(
                entity_type=fn_span.entity_type,
                text=fn_span.text,
                context=context,
                start=fn_span.start,
                end=fn_span.end,
                failure_mode=failure_mode,
                detected_partial=partial,
            )

            taxonomy[failure_mode].append(case)

    return taxonomy


def generate_error_report(taxonomy: dict[FailureMode, list[FalseNegativeCase]]) -> str:
    """
    Generate human-readable error taxonomy report.

    Shows counts per failure mode, top examples, and actionable recommendations.

    Args:
        taxonomy: Error taxonomy from build_error_taxonomy

    Returns:
        Formatted report string
    """
    lines = [
        "=" * 60,
        "PHI DETECTION ERROR TAXONOMY",
        "=" * 60,
        "",
        "This report categorizes missed PHI by failure mode to guide",
        "targeted improvements.",
        "",
    ]

    # Summary counts
    total_errors = sum(len(cases) for cases in taxonomy.values())
    lines.append(f"TOTAL FALSE NEGATIVES: {total_errors}")
    lines.append("")

    if total_errors == 0:
        lines.append("✅ NO ERRORS - 100% RECALL ACHIEVED!")
        return "\n".join(lines)

    lines.append("BREAKDOWN BY FAILURE MODE:")
    lines.append("")

    # Failure mode details
    for mode in FailureMode:
        cases = taxonomy[mode]
        if not cases:
            continue

        count = len(cases)
        pct = 100 * count / total_errors

        lines.append(f"{'─' * 60}")
        lines.append(f"{mode.value.upper().replace('_', ' ')}: {count} cases ({pct:.1f}%)")
        lines.append(f"{'─' * 60}")

        # Show up to 5 examples
        for i, case in enumerate(cases[:5], 1):
            lines.append(f"  {i}. {case.entity_type}: \"{case.text}\"")
            if case.detected_partial:
                lines.append(f"     Partial match: \"{case.detected_partial.get('text', '')}\"")

        if len(cases) > 5:
            lines.append(f"  ... and {len(cases) - 5} more")

        lines.append("")

        # Actionable recommendations per failure mode
        recommendations = {
            FailureMode.PATTERN_MISS: "→ Add regex patterns to custom recognizers",
            FailureMode.SPAN_BOUNDARY: "→ Review entity boundary detection logic",
            FailureMode.DENY_LIST_FILTER: "→ Remove incorrect deny list entries",
            FailureMode.NOVEL_VARIANT: "→ Expand synthetic training data coverage",
            FailureMode.THRESHOLD_MISS: "→ Lower score threshold (currently 0.30)",
            FailureMode.NER_MISS: "→ Train custom spaCy NER model or add patterns",
        }
        lines.append(f"  💡 {recommendations[mode]}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)
