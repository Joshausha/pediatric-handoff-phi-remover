"""
De-identification module using Microsoft Presidio.

Removes PHI from transcripts using:
1. Standard Presidio NER (PERSON, PHONE, etc.)
2. Custom pediatric recognizers (guardian names, detailed ages)
3. Custom medical recognizers (MRN, room numbers)
"""

import logging
import re
import threading
from dataclasses import dataclass, field
from typing import Optional

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import PhoneRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .config import settings
from .recognizers import get_medical_recognizers, get_pediatric_recognizers, get_provider_recognizers

logger = logging.getLogger(__name__)

# Thread-safe engine loading
_analyzer: Optional[AnalyzerEngine] = None
_anonymizer: Optional[AnonymizerEngine] = None
_engine_lock = threading.Lock()


@dataclass
class EntityInfo:
    """Information about a detected PHI entity."""
    entity_type: str
    score: float
    start: int
    end: int
    text_preview: str  # Partially masked for display


@dataclass
class DeidentificationResult:
    """Result of de-identification operation."""
    clean_text: str
    original_text: str
    entities_found: list[EntityInfo] = field(default_factory=list)
    entity_count: int = 0
    entity_counts_by_type: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def _mask_text_preview(text: str, max_reveal: int = 3) -> str:
    """
    Create a partially masked preview of PHI text for display.

    Args:
        text: The PHI text to mask
        max_reveal: Maximum characters to reveal at start/end

    Returns:
        Masked preview like "Sar***ah" or "555-***-5309"
    """
    if len(text) <= max_reveal * 2:
        return "*" * len(text)

    start = text[:max_reveal]
    end = text[-max_reveal:] if len(text) > max_reveal else ""
    middle = "*" * (len(text) - max_reveal * 2)

    return f"{start}{middle}{end}"


def _get_engines() -> tuple[AnalyzerEngine, AnonymizerEngine]:
    """
    Lazy-load and cache Presidio engines. Thread-safe.

    Returns:
        Tuple of (AnalyzerEngine, AnonymizerEngine)
    """
    global _analyzer, _anonymizer

    if _analyzer is None or _anonymizer is None:
        with _engine_lock:
            if _analyzer is None:
                logger.info("Loading Presidio engines...")

                # Configure NLP engine with spaCy
                nlp_config = {
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": settings.spacy_model}]
                }

                provider = NlpEngineProvider(nlp_configuration=nlp_config)
                nlp_engine = provider.create_engine()

                # Create registry with predefined recognizers
                registry = RecognizerRegistry()
                registry.load_predefined_recognizers(nlp_engine=nlp_engine)

                # Override default PhoneRecognizer with lenient matching (Phase 20)
                # Default leniency=1 is too strict for clinical handoffs; leniency=0 catches
                # extensions (x310) and standard dash-separated formats that were missed.
                registry.remove_recognizer("PhoneRecognizer")
                custom_phone = PhoneRecognizer(
                    supported_regions=("US",),
                    leniency=0,  # Most lenient - catches all valid formats
                )
                registry.add_recognizer(custom_phone)
                logger.debug("Added custom PhoneRecognizer with leniency=0")

                # Add custom recognizers
                if settings.enable_custom_recognizers:
                    for recognizer in get_medical_recognizers():
                        registry.add_recognizer(recognizer)
                        logger.debug(f"Added recognizer: {recognizer.name}")

                    for recognizer in get_pediatric_recognizers():
                        registry.add_recognizer(recognizer)
                        logger.debug(f"Added recognizer: {recognizer.name}")

                    for recognizer in get_provider_recognizers():
                        registry.add_recognizer(recognizer)
                        logger.debug(f"Added recognizer: {recognizer.name}")

                _analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
                _anonymizer = AnonymizerEngine()

                logger.info("Presidio engines loaded successfully")

    return _analyzer, _anonymizer


def is_engines_loaded() -> bool:
    """Check if Presidio engines are loaded."""
    return _analyzer is not None and _anonymizer is not None


def _get_entity_threshold(entity_type: str) -> float:
    """
    Get confidence threshold for entity type.

    Uses per-entity calibrated thresholds from Phase 2, falling back
    to global threshold for unknown entity types.

    Args:
        entity_type: The PHI entity type (e.g., "PERSON", "PHONE_NUMBER")

    Returns:
        Confidence threshold (0.0-1.0)
    """
    return settings.phi_score_thresholds.get(
        entity_type,
        settings.phi_score_threshold  # Fallback to global for unknown types
    )


def deidentify_text(
    text: str,
    strategy: str = "type_marker",
    transfer_facility_mode: str | None = None
) -> DeidentificationResult:
    """
    Remove PHI from text using Presidio.

    Args:
        text: The transcript to de-identify
        strategy: Replacement approach
            - "type_marker": [NAME], [PHONE], [DATE], etc. (default, most readable)
            - "redact": [REDACTED] for all PHI
            - "mask": **** asterisks
        transfer_facility_mode: Transfer facility handling mode
            - None (default): Use settings.transfer_facility_mode
            - "conservative": Redact all LOCATION entities (HIPAA Safe Harbor)
            - "clinical": Preserve LOCATION entities (care coordination)

    Returns:
        DeidentificationResult with clean text and entity details
    """
    # Resolve transfer facility mode (use setting if not specified)
    if transfer_facility_mode is None:
        transfer_facility_mode = settings.transfer_facility_mode

    analyzer, anonymizer = _get_engines()

    # Analyze text for PHI entities with minimum threshold (get all candidates)
    # We filter by per-entity thresholds below
    raw_results = analyzer.analyze(
        text=text,
        language="en",
        entities=settings.phi_entities,
        score_threshold=0.0  # Get all, filter by per-entity threshold below
    )

    # Filter by per-entity thresholds, then deny lists
    results = []
    for result in raw_results:
        # Apply per-entity threshold (Phase 2 calibration)
        entity_threshold = _get_entity_threshold(result.entity_type)
        if result.score < entity_threshold:
            logger.debug(
                f"Filtered by threshold: {result.entity_type} "
                f"(score: {result.score:.2f} < threshold: {entity_threshold:.2f})"
            )
            continue

        detected_text = text[result.start:result.end].strip()

        # Check LOCATION deny list (uses word-boundary substring matching)
        # NOTE: Word boundaries prevent "ER" matching "Memorial" or "transfer"
        if result.entity_type == "LOCATION":
            detected_lower = detected_text.lower()
            is_denied = any(
                re.search(r'\b' + re.escape(term.lower()) + r'\b', detected_lower)
                for term in settings.deny_list_location
            )
            if is_denied:
                logger.debug(f"Filtered out deny-listed LOCATION: {detected_text}")
                continue

        # Check PERSON deny list
        if result.entity_type == "PERSON" and detected_text.lower() in [w.lower() for w in settings.deny_list_person]:
            logger.debug(f"Filtered out deny-listed PERSON: {detected_text}")
            continue

        # Check GUARDIAN_NAME deny list
        if result.entity_type == "GUARDIAN_NAME" and detected_text.lower() in [w.lower() for w in settings.deny_list_guardian_name]:
            logger.debug(f"Filtered out deny-listed GUARDIAN_NAME: {detected_text}")
            continue

        # Check PROVIDER_NAME deny list
        if result.entity_type == "PROVIDER_NAME" and detected_text.lower() in [w.lower() for w in settings.deny_list_provider_name]:
            logger.debug(f"Filtered out deny-listed PROVIDER_NAME: {detected_text}")
            continue

        # Check PEDIATRIC_AGE deny list
        if result.entity_type == "PEDIATRIC_AGE" and detected_text.lower() in [w.lower() for w in settings.deny_list_pediatric_age]:
            logger.debug(f"Filtered out deny-listed PEDIATRIC_AGE: {detected_text}")
            continue

        # Check DATE_TIME deny list (uses substring match for clinical timeline patterns)
        # e.g., "5 months old" matches "months old" in deny list
        if result.entity_type == "DATE_TIME":
            detected_lower = detected_text.lower()
            if any(term.lower() in detected_lower for term in settings.deny_list_date_time):
                logger.debug(f"Filtered out deny-listed DATE_TIME: {detected_text}")
                continue

        results.append(result)

    # Build entity info list and count by type
    entities_found = []
    entity_counts: dict[str, int] = {}

    for result in results:
        # Get the detected text
        detected_text = text[result.start:result.end]

        # Create masked preview
        preview = _mask_text_preview(detected_text)

        entities_found.append(EntityInfo(
            entity_type=result.entity_type,
            score=result.score,
            start=result.start,
            end=result.end,
            text_preview=preview
        ))

        # Count by type
        entity_counts[result.entity_type] = entity_counts.get(result.entity_type, 0) + 1

    # Configure replacement operator based on strategy
    if strategy == "type_marker":
        # Replace with type marker: [NAME], [PHONE], etc.
        operators = {}
        for entity_type in settings.phi_entities:
            # Create readable marker
            marker = f"[{entity_type.replace('_', ' ').title()}]"
            # Simplify common markers
            marker_map = {
                "[Person]": "[NAME]",
                "[Phone Number]": "[PHONE]",
                "[Email Address]": "[EMAIL]",
                "[Date Time]": "[DATE]",
                "[Medical Record Number]": "[MRN]",
                "[Guardian Name]": "[NAME]",
                "[Provider Name]": "[NAME]",
                "[Pediatric Age]": "[AGE]",
                "[Room]": "[ROOM]",
                "[Location]": "[LOCATION]",
            }
            marker = marker_map.get(marker, marker)

            # LOCATION handling: conditional on transfer_facility_mode (Phase 23)
            if entity_type == "LOCATION" and transfer_facility_mode == "clinical":
                # Clinical mode: preserve LOCATION entities (for transfer facilities)
                # Uses Presidio "keep" operator which leaves text unchanged
                operators[entity_type] = OperatorConfig("keep", {})
                logger.debug("Clinical mode: LOCATION entities will be preserved")
            else:
                # Conservative mode (default): redact all PHI
                operators[entity_type] = OperatorConfig("replace", {"new_value": marker})

    elif strategy == "redact":
        operators = {
            "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})
        }

    elif strategy == "mask":
        operators = {
            "DEFAULT": OperatorConfig("mask", {
                "type": "mask",
                "masking_char": "*",
                "chars_to_mask": 100,  # Mask entire entity
                "from_end": False
            })
        }

    else:
        # Default to type_marker
        operators = {
            "DEFAULT": OperatorConfig("replace", {"new_value": "<PHI>"})
        }

    # Anonymize the text
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators
    )

    logger.info(f"De-identification complete: {len(results)} PHI entities found")

    return DeidentificationResult(
        clean_text=anonymized.text,
        original_text=text,
        entities_found=entities_found,
        entity_count=len(results),
        entity_counts_by_type=entity_counts
    )


def validate_deidentification(
    original: str,
    cleaned: str
) -> tuple[bool, list[str]]:
    """
    Re-scan cleaned text to catch any PHI that might have been missed.

    Uses the same per-entity thresholds as detection for consistency
    (fixes THRS-02: detection/validation threshold mismatch).

    Args:
        original: Original text before de-identification
        cleaned: Text after de-identification

    Returns:
        Tuple of (is_valid, list_of_warnings)
        is_valid is True if no PHI above per-entity threshold remains
    """
    analyzer, _ = _get_engines()

    # Scan the cleaned text with minimum threshold (filter per-entity below)
    results = analyzer.analyze(
        text=cleaned,
        language="en",
        entities=settings.phi_entities,
        score_threshold=0.0  # Get all, filter by per-entity threshold below
    )

    warnings = []

    for result in results:
        # Skip markers we added
        detected = cleaned[result.start:result.end]
        if detected.startswith("[") and detected.endswith("]"):
            continue

        # Apply same per-entity threshold as detection (fixes THRS-02)
        entity_threshold = _get_entity_threshold(result.entity_type)
        if result.score >= entity_threshold:
            warnings.append(
                f"Potential PHI leak: {result.entity_type} "
                f"(score: {result.score:.2f}, threshold: {entity_threshold:.2f}) "
                f"at position {result.start}-{result.end}"
            )

    is_valid = len(warnings) == 0

    if not is_valid:
        logger.warning(f"Validation found {len(warnings)} potential PHI leaks")

    return is_valid, warnings
