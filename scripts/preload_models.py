#!/usr/bin/env python3
"""
Preload ML models during Docker build or container startup.

This script downloads and caches:
1. faster-whisper model (specified by WHISPER_MODEL env var)
2. spaCy en_core_web_lg model (for Presidio NER)

Run during Docker build for faster container startup,
or run at container start if you prefer smaller images.

Usage:
    python scripts/preload_models.py
    WHISPER_MODEL=large-v3 python scripts/preload_models.py
"""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def preload_whisper():
    """Download and cache the Whisper model."""
    model_name = os.environ.get("WHISPER_MODEL", "medium.en")
    logger.info(f"Preloading Whisper model: {model_name}")

    try:
        from faster_whisper import WhisperModel

        # This downloads the model if not cached
        model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8"
        )
        logger.info(f"Whisper model '{model_name}' loaded successfully")
        del model  # Free memory

    except Exception as e:
        logger.error(f"Failed to preload Whisper model: {e}")
        return False

    return True


def preload_spacy():
    """Ensure spaCy model is downloaded."""
    model_name = os.environ.get("SPACY_MODEL", "en_core_web_lg")
    logger.info(f"Checking spaCy model: {model_name}")

    try:
        import spacy
        spacy.load(model_name)
        logger.info(f"spaCy model '{model_name}' available")

    except OSError:
        logger.info(f"Downloading spaCy model: {model_name}")
        from spacy.cli import download
        download(model_name)
        logger.info(f"spaCy model '{model_name}' downloaded successfully")

    except Exception as e:
        logger.error(f"Failed to load spaCy model: {e}")
        return False

    return True


def preload_presidio():
    """Initialize Presidio engines to cache any lazy-loaded resources."""
    logger.info("Initializing Presidio engines...")

    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine

        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()

        # Run a test analysis to warm up
        analyzer.analyze(text="Test text for warmup", language="en")
        logger.info("Presidio engines initialized successfully")
        del analyzer, anonymizer

    except Exception as e:
        logger.error(f"Failed to initialize Presidio: {e}")
        return False

    return True


def main():
    """Preload all models."""
    logger.info("=" * 60)
    logger.info("PRELOADING ML MODELS")
    logger.info("=" * 60)

    success = True

    # Preload in order of importance
    if not preload_spacy():
        success = False

    if not preload_whisper():
        success = False

    if not preload_presidio():
        success = False

    if success:
        logger.info("=" * 60)
        logger.info("ALL MODELS PRELOADED SUCCESSFULLY")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error("SOME MODELS FAILED TO PRELOAD")
        logger.error("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
