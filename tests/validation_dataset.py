#!/usr/bin/env python
"""
Validation dataset loader for real transcript evaluation.

Provides infrastructure for ingesting real transcripts with human annotations,
converting to PresidioEvaluator-compatible format.
"""

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from tests.annotation_schema import AnnotationSchema, ENTITY_TYPES
from tests.generate_test_data import PHISpan


@dataclass
class PHIAnnotation:
    """
    Human-annotated PHI span.

    Extends AnnotationSchema with metadata for validation tracking.
    """
    entity_type: str
    start: int
    end: int
    text: str
    confidence: Optional[float] = None
    annotator_id: Optional[str] = None
    notes: Optional[str] = None  # Annotator notes for edge cases

    def to_annotation_schema(self) -> AnnotationSchema:
        """Convert to AnnotationSchema for validation."""
        return AnnotationSchema(
            entity_type=self.entity_type,
            start=self.start,
            end=self.end,
            text=self.text,
            confidence=self.confidence,
            annotator_id=self.annotator_id,
        )


@dataclass
class ValidationHandoff:
    """
    Real handoff transcript with human PHI annotations.

    Compatible with PresidioEvaluator via phi_spans property.
    """
    id: int
    text: str
    phi_annotations: list[PHIAnnotation]
    source: str  # Data source identifier
    transcript_date: Optional[str] = None
    annotator_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def phi_spans(self) -> list[PHISpan]:
        """
        Convert PHIAnnotation list to PHISpan list for PresidioEvaluator compatibility.

        This property allows ValidationHandoff to be used directly with
        PresidioEvaluator.evaluate_handoff() just like SyntheticHandoff.
        """
        return [
            PHISpan(
                entity_type=ann.entity_type,
                start=ann.start,
                end=ann.end,
                text=ann.text
            )
            for ann in self.phi_annotations
        ]

    @property
    def phi_types(self) -> list[str]:
        """Get unique PHI types present in annotations."""
        return list(set(ann.entity_type for ann in self.phi_annotations))

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "id": self.id,
            "text": self.text,
            "phi_annotations": [
                {
                    "entity_type": ann.entity_type,
                    "start": ann.start,
                    "end": ann.end,
                    "text": ann.text,
                    "confidence": ann.confidence,
                    "annotator_id": ann.annotator_id,
                    "notes": ann.notes,
                }
                for ann in self.phi_annotations
            ],
            "source": self.source,
            "transcript_date": self.transcript_date,
            "annotator_id": self.annotator_id,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict) -> "ValidationHandoff":
        """Deserialize from JSON-compatible dict."""
        phi_annotations = [
            PHIAnnotation(
                entity_type=ann["entity_type"],
                start=ann["start"],
                end=ann["end"],
                text=ann["text"],
                confidence=ann.get("confidence"),
                annotator_id=ann.get("annotator_id"),
                notes=ann.get("notes"),
            )
            for ann in data["phi_annotations"]
        ]

        return ValidationHandoff(
            id=data["id"],
            text=data["text"],
            phi_annotations=phi_annotations,
            source=data["source"],
            transcript_date=data.get("transcript_date"),
            annotator_id=data.get("annotator_id"),
            metadata=data.get("metadata", {}),
        )


def load_validation_set(path: Path) -> list[ValidationHandoff]:
    """
    Load validation dataset from JSON file.

    Args:
        path: Path to JSON file with ValidationHandoff array

    Returns:
        List of ValidationHandoff objects

    File format:
    {
        "metadata": {
            "created": "2026-01-24",
            "source": "real_handoffs",
            "annotator": "annotator_id"
        },
        "handoffs": [
            {
                "id": 1,
                "text": "...",
                "phi_annotations": [...],
                "source": "..."
            },
            ...
        ]
    }
    """
    with open(path) as f:
        data = json.load(f)

    handoffs = []
    for h in data.get("handoffs", []):
        handoffs.append(ValidationHandoff.from_dict(h))

    return handoffs


def export_for_annotation(
    handoffs: list[ValidationHandoff],
    output_path: Path,
    include_text_only: bool = True
) -> None:
    """
    Export handoffs for manual annotation.

    Args:
        handoffs: List of handoffs to export
        output_path: Output JSON file path
        include_text_only: If True, export only text for initial annotation.
                           If False, export full structure for review.
    """
    if include_text_only:
        # Minimal export for initial annotation
        data = {
            "metadata": {
                "purpose": "initial_annotation",
                "n_handoffs": len(handoffs),
            },
            "handoffs": [
                {
                    "id": h.id,
                    "text": h.text,
                    "phi_annotations": [],  # Empty for annotator to fill
                }
                for h in handoffs
            ]
        }
    else:
        # Full export for review/verification
        data = {
            "metadata": {
                "purpose": "annotation_review",
                "n_handoffs": len(handoffs),
            },
            "handoffs": [h.to_dict() for h in handoffs]
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Exported {len(handoffs)} handoffs to {output_path}")


def stratified_sample(
    handoffs: list[ValidationHandoff],
    n: int,
    seed: int = 42
) -> list[ValidationHandoff]:
    """
    Create stratified sample based on dominant PHI type distribution.

    Args:
        handoffs: Full list of handoffs
        n: Target sample size
        seed: Random seed for reproducibility

    Returns:
        Stratified sample of handoffs

    Strategy:
        - Group handoffs by dominant PHI type (most common entity in handoff)
        - Sample proportionally from each group to maintain distribution
        - Ensures coverage of all PHI types in validation set
    """
    random.seed(seed)

    # Calculate dominant PHI type for each handoff
    def dominant_phi_type(h: ValidationHandoff) -> str:
        """Find most common PHI type in handoff."""
        if not h.phi_annotations:
            return "NONE"

        type_counts = {}
        for ann in h.phi_annotations:
            type_counts[ann.entity_type] = type_counts.get(ann.entity_type, 0) + 1

        return max(type_counts.items(), key=lambda x: x[1])[0]

    # Group by dominant type
    groups = {}
    for h in handoffs:
        dtype = dominant_phi_type(h)
        groups.setdefault(dtype, []).append(h)

    # Calculate samples per group (proportional)
    samples = []
    total_handoffs = len(handoffs)

    for dtype, group in sorted(groups.items()):
        proportion = len(group) / total_handoffs
        group_n = max(1, int(n * proportion))  # At least 1 from each group

        # Sample from this group
        group_sample = random.sample(group, min(group_n, len(group)))
        samples.extend(group_sample)

    # If we overshot due to rounding, trim randomly
    if len(samples) > n:
        samples = random.sample(samples, n)

    # If we undershot, add random samples from largest groups
    elif len(samples) < n:
        remaining = n - len(samples)
        largest_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)

        for dtype, group in largest_groups:
            if remaining == 0:
                break

            # Add samples not already selected
            available = [h for h in group if h not in samples]
            add_n = min(remaining, len(available))

            if add_n > 0:
                samples.extend(random.sample(available, add_n))
                remaining -= add_n

    return samples
