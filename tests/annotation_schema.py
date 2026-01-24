#!/usr/bin/env python
"""
Annotation schema for human PHI labeling.

Defines entity types, annotation format, and validation rules for
creating gold standard ground truth datasets.
"""

from dataclasses import dataclass
from typing import Optional


# Entity types matching Presidio configuration
ENTITY_TYPES = [
    "PERSON",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "DATE_TIME",
    "LOCATION",
    "MEDICAL_RECORD_NUMBER",
    "ROOM",
    "PEDIATRIC_AGE",
    "GUARDIAN_NAME",
]


# Annotation guidelines for human annotators
ANNOTATION_GUIDELINES = """
PHI ANNOTATION GUIDELINES
=========================

Entity Type Definitions:

1. PERSON
   - Full names, first names, last names
   - Healthcare provider names (doctors, nurses, staff)
   - Patient relatives mentioned by name
   - Exclude: Generic roles ("mom", "nurse") without names

2. PHONE_NUMBER
   - Any phone number format (including extensions)
   - Pager numbers if patient-specific
   - Exclude: Generic hospital switchboard numbers

3. EMAIL_ADDRESS
   - Any email address
   - Patient, family, or provider emails

4. DATE_TIME
   - Specific dates (absolute or relative)
   - Times of day when combined with dates
   - Exclude: Isolated times without date context

5. LOCATION
   - Street addresses, cities, states
   - Geographic locations that could identify patient
   - Hospital/clinic names
   - School names
   - Exclude: Generic medical unit abbreviations (PICU, NICU, ER)

6. MEDICAL_RECORD_NUMBER
   - MRN in any format
   - Account numbers
   - Patient identifiers

7. ROOM
   - Room numbers
   - Bed numbers
   - Combined with unit (e.g., "PICU bed 12")

8. PEDIATRIC_AGE
   - Detailed ages (e.g., "3 weeks 2 days old")
   - Ages >89 years (HIPAA requirement)
   - Exclude: General age ranges without detail

9. GUARDIAN_NAME
   - Parent/guardian names in context
   - Pattern: "Mom Sarah", "Dad Mike"
   - Include relationship word + name together

Annotation Rules:
- Mark exact span boundaries (start/end character indices)
- Include surrounding context words when part of pattern (e.g., "Mom Sarah")
- If uncertain about entity type, use most specific applicable type
- Mark overlapping entities separately if different types
- Document edge cases in annotator notes
"""


@dataclass
class AnnotationSchema:
    """
    Schema for a single PHI annotation.

    Compatible with Presidio entity types and evaluation framework.
    """
    entity_type: str
    start: int
    end: int
    text: str
    confidence: Optional[float] = None  # For annotator uncertainty
    annotator_id: Optional[str] = None  # For IAA tracking

    def __post_init__(self):
        """Validate annotation schema."""
        if self.entity_type not in ENTITY_TYPES:
            raise ValueError(
                f"Invalid entity type: {self.entity_type}. "
                f"Must be one of {ENTITY_TYPES}"
            )
        if self.start >= self.end:
            raise ValueError(
                f"Invalid span: start ({self.start}) must be < end ({self.end})"
            )
        if self.start < 0:
            raise ValueError(f"Invalid start position: {self.start}")


def validate_annotations(annotations: list[AnnotationSchema], text: str) -> list[str]:
    """
    Validate annotations against source text.

    Args:
        annotations: List of annotations to validate
        text: Source text that was annotated

    Returns:
        List of validation errors (empty if all valid)
    """
    errors = []

    for i, ann in enumerate(annotations):
        # Check span is within text bounds
        if ann.end > len(text):
            errors.append(
                f"Annotation {i}: span end ({ann.end}) exceeds text length ({len(text)})"
            )
            continue

        # Check annotated text matches span
        actual_text = text[ann.start:ann.end]
        if actual_text != ann.text:
            errors.append(
                f"Annotation {i}: text mismatch. "
                f"Expected '{ann.text}', got '{actual_text}' at [{ann.start}:{ann.end}]"
            )

    return errors
