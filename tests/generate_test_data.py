#!/usr/bin/env python
"""
Generate synthetic pediatric handoff dataset with labeled PHI spans.

This script creates a test dataset of synthetic pediatric handoffs with
ground truth PHI labels for validating Presidio detection accuracy.

Usage:
    python tests/generate_test_data.py --output tests/synthetic_handoffs.json
    python tests/generate_test_data.py --samples 1000 --seed 42
"""

import argparse
import json
import random
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from faker import Faker

# Handle imports when run as script vs module
try:
    from tests.handoff_templates import ALL_TEMPLATES, HANDOFF_TEMPLATES, MINIMAL_PHI_TEMPLATES
    from tests.medical_providers import CUSTOM_PROVIDERS
except ImportError:
    from handoff_templates import ALL_TEMPLATES, HANDOFF_TEMPLATES, MINIMAL_PHI_TEMPLATES
    from medical_providers import CUSTOM_PROVIDERS


@dataclass
class PHISpan:
    """Represents a PHI entity span in text."""
    entity_type: str
    start: int
    end: int
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SyntheticHandoff:
    """A synthetic handoff with ground truth PHI labels."""
    id: int
    text: str
    template_id: int
    phi_spans: list[PHISpan] = field(default_factory=list)
    phi_types: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "template_id": self.template_id,
            "phi_spans": [span.to_dict() for span in self.phi_spans],
            "phi_types": self.phi_types,
        }


class PediatricHandoffGenerator:
    """
    Generator for synthetic pediatric handoffs with labeled PHI.

    Uses Faker with custom medical providers to generate realistic
    clinical text with ground truth PHI span labels.
    """

    # Mapping of template placeholders to PHI entity types
    PHI_PLACEHOLDER_MAPPING = {
        "person": "PERSON",
        "last_name": "PERSON",
        "phone_number": "PHONE_NUMBER",
        "email": "EMAIL_ADDRESS",
        "date": "DATE_TIME",
        "time": "DATE_TIME",
        "address": "LOCATION",
        "city": "LOCATION",
        "location": "LOCATION",
        "mrn": "MEDICAL_RECORD_NUMBER",
        "mrn_numeric": "MEDICAL_RECORD_NUMBER",
        "room_number": "ROOM",
        "pediatric_age": "PEDIATRIC_AGE",
        "school_name": "LOCATION",
        "hospital_name": "LOCATION",
    }

    # Non-PHI placeholders (clinical content)
    NON_PHI_PLACEHOLDERS = {
        "medication", "condition", "respiratory_support", "symptom",
        "service_need", "relationship", "gender", "delivery_type",
        "frequency", "parameter", "clinic_name", "pharmacy", "concern",
        "fio2", "saturation", "target_sat", "ph", "pco2", "po2", "anc",
        "antibiotic", "trend_direction", "current_support", "escalation_med",
        "hours", "number", "treatment", "weight", "gestational_age",
        "pager_number",  # Pager could be PHI but often internal
    }

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.faker = Faker()
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        # Add custom providers
        for provider in CUSTOM_PROVIDERS:
            self.faker.add_provider(provider)

    def _extract_placeholders(self, template: str) -> list[tuple[str, int, int]]:
        """
        Extract placeholder names and positions from template.

        Returns list of (placeholder_name, start, end) tuples.
        """
        pattern = r"\{\{(\w+)\}\}"
        placeholders = []
        for match in re.finditer(pattern, template):
            placeholders.append((
                match.group(1),  # placeholder name
                match.start(),   # start position
                match.end(),     # end position
            ))
        return placeholders

    def _generate_value(self, placeholder: str) -> str:
        """Generate a value for a placeholder using Faker."""
        # Standard Faker methods
        faker_methods = {
            "person": lambda: self.faker.name(),
            "last_name": lambda: self.faker.last_name(),
            "phone_number": lambda: self.faker.phone_number(),
            "email": lambda: self.faker.email(),
            "date": lambda: self.faker.date_this_year().strftime("%B %d"),
            "time": lambda: self.faker.time(pattern="%I:%M %p"),
            "address": lambda: self.faker.street_address(),
            "city": lambda: self.faker.city(),
            "location": lambda: self.faker.city(),
        }

        # Custom provider methods
        custom_methods = {
            "mrn": lambda: self.faker.mrn(),
            "mrn_numeric": lambda: self.faker.mrn_numeric(),
            "room_number": lambda: self.faker.room_number(),
            "pager_number": lambda: self.faker.pager_number(),
            "pediatric_age": lambda: self.faker.pediatric_age(),
            "gestational_age": lambda: self.faker.gestational_age(),
            "medication": lambda: self.faker.medication(),
            "condition": lambda: self.faker.condition(),
            "respiratory_support": lambda: self.faker.respiratory_support(),
            "symptom": lambda: self.faker.symptom(),
            "service_need": lambda: self.faker.service_need(),
            "relationship": lambda: self.faker.relationship(),
            "gender": lambda: self.faker.gender(),
            "delivery_type": lambda: self.faker.delivery_type(),
            "frequency": lambda: self.faker.frequency(),
            "parameter": lambda: self.faker.parameter(),
            "hospital_name": lambda: self.faker.hospital_name(),
            "school_name": lambda: self.faker.school_name(),
            "clinic_name": lambda: self.faker.clinic_name(),
            "pharmacy": lambda: self.faker.pharmacy(),
            "concern": lambda: self.faker.concern(),
            "fio2": lambda: self.faker.fio2(),
            "saturation": lambda: self.faker.saturation(),
            "target_sat": lambda: self.faker.target_sat(),
            "ph": lambda: self.faker.ph(),
            "pco2": lambda: self.faker.pco2(),
            "po2": lambda: self.faker.po2(),
            "anc": lambda: self.faker.anc(),
            "antibiotic": lambda: self.faker.antibiotic(),
            "trend_direction": lambda: self.faker.trend_direction(),
            "current_support": lambda: self.faker.current_support(),
            "escalation_med": lambda: self.faker.escalation_med(),
            "hours": lambda: self.faker.hours(),
            "number": lambda: self.faker.number(),
            "treatment": lambda: self.faker.treatment(),
            "weight": lambda: self.faker.weight(),
        }

        # Try custom methods first, then standard Faker
        if placeholder in custom_methods:
            return custom_methods[placeholder]()
        elif placeholder in faker_methods:
            return faker_methods[placeholder]()
        else:
            # Fallback: try calling Faker method directly
            try:
                return getattr(self.faker, placeholder)()
            except AttributeError:
                return f"[UNKNOWN:{placeholder}]"

    def generate_handoff(self, template: str, handoff_id: int, template_id: int) -> SyntheticHandoff:
        """
        Generate a single synthetic handoff from a template.

        Args:
            template: Template string with {{placeholders}}
            handoff_id: Unique ID for this handoff
            template_id: ID of the source template

        Returns:
            SyntheticHandoff with text and PHI span labels
        """
        # Extract placeholders
        placeholders = self._extract_placeholders(template)

        # Generate values and track spans
        result_text = template
        phi_spans = []
        offset = 0  # Track position offset as we replace placeholders

        for placeholder_name, orig_start, orig_end in placeholders:
            # Generate replacement value
            value = self._generate_value(placeholder_name)

            # Calculate actual position after previous replacements
            actual_start = orig_start + offset

            # Replace in text
            pattern = "{{" + placeholder_name + "}}"
            result_text = result_text[:actual_start] + value + result_text[actual_start + len(pattern):]

            # Track PHI span if this is a PHI placeholder
            if placeholder_name in self.PHI_PLACEHOLDER_MAPPING:
                entity_type = self.PHI_PLACEHOLDER_MAPPING[placeholder_name]
                phi_spans.append(PHISpan(
                    entity_type=entity_type,
                    start=actual_start,
                    end=actual_start + len(value),
                    text=value,
                ))

            # Update offset
            offset += len(value) - len(pattern)

        # Get unique PHI types
        phi_types = list(set(span.entity_type for span in phi_spans))

        return SyntheticHandoff(
            id=handoff_id,
            text=result_text,
            template_id=template_id,
            phi_spans=phi_spans,
            phi_types=phi_types,
        )

    def generate_dataset(
        self,
        n_samples: int = 500,
        templates: Optional[list[str]] = None,
    ) -> list[SyntheticHandoff]:
        """
        Generate a dataset of synthetic handoffs.

        Args:
            n_samples: Number of handoffs to generate
            templates: List of templates to use (default: ALL_TEMPLATES)

        Returns:
            List of SyntheticHandoff objects
        """
        if templates is None:
            templates = ALL_TEMPLATES

        dataset = []
        for i in range(n_samples):
            template_id = i % len(templates)
            template = templates[template_id]
            handoff = self.generate_handoff(template, handoff_id=i, template_id=template_id)
            dataset.append(handoff)

        return dataset


def save_dataset(dataset: list[SyntheticHandoff], output_path: Path) -> None:
    """Save dataset to JSON file."""
    data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "n_samples": len(dataset),
            "phi_types": list(set(
                phi_type
                for handoff in dataset
                for phi_type in handoff.phi_types
            )),
        },
        "handoffs": [h.to_dict() for h in dataset],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(dataset)} handoffs to {output_path}")


def load_dataset(input_path: Path) -> list[SyntheticHandoff]:
    """Load dataset from JSON file."""
    with open(input_path) as f:
        data = json.load(f)

    handoffs = []
    for h in data["handoffs"]:
        phi_spans = [PHISpan(**span) for span in h["phi_spans"]]
        handoffs.append(SyntheticHandoff(
            id=h["id"],
            text=h["text"],
            template_id=h["template_id"],
            phi_spans=phi_spans,
            phi_types=h["phi_types"],
        ))

    return handoffs


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic pediatric handoff dataset with labeled PHI"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("tests/synthetic_handoffs.json"),
        help="Output file path (default: tests/synthetic_handoffs.json)"
    )
    parser.add_argument(
        "--samples", "-n",
        type=int,
        default=500,
        help="Number of samples to generate (default: 500)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview first 5 samples instead of saving"
    )

    args = parser.parse_args()

    # Generate dataset
    generator = PediatricHandoffGenerator(seed=args.seed)
    dataset = generator.generate_dataset(n_samples=args.samples)

    if args.preview:
        print("\n=== Preview of Generated Handoffs ===\n")
        for handoff in dataset[:5]:
            print(f"ID: {handoff.id}")
            print(f"Template: {handoff.template_id}")
            print(f"Text: {handoff.text[:200]}...")
            print(f"PHI Types: {handoff.phi_types}")
            print(f"PHI Spans: {len(handoff.phi_spans)}")
            for span in handoff.phi_spans[:3]:
                print(f"  - {span.entity_type}: '{span.text}' at [{span.start}:{span.end}]")
            print("-" * 60)
    else:
        save_dataset(dataset, args.output)

        # Print summary statistics
        total_spans = sum(len(h.phi_spans) for h in dataset)
        type_counts = {}
        for h in dataset:
            for span in h.phi_spans:
                type_counts[span.entity_type] = type_counts.get(span.entity_type, 0) + 1

        print("\n=== Dataset Summary ===")
        print(f"Total handoffs: {len(dataset)}")
        print(f"Total PHI spans: {total_spans}")
        print(f"Average spans per handoff: {total_spans / len(dataset):.1f}")
        print("\nPHI type distribution:")
        for phi_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {phi_type}: {count}")


if __name__ == "__main__":
    main()
