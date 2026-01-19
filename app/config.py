"""
Configuration module using Pydantic Settings.

All settings can be overridden via environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # =========================================================================
    # Whisper Configuration
    # =========================================================================
    whisper_model: str = Field(
        default="medium.en",
        description="Whisper model size. Options: tiny.en, base.en, small.en, medium.en, large-v3"
    )
    whisper_device: str = Field(
        default="cpu",
        description="Device for Whisper inference. Options: cpu, cuda"
    )
    whisper_compute_type: str = Field(
        default="int8",
        description="Compute type. Options: int8 (CPU), float16 (GPU)"
    )

    # =========================================================================
    # Presidio Configuration
    # =========================================================================
    phi_entities: List[str] = Field(
        default=[
            "PERSON",
            "PHONE_NUMBER",
            "EMAIL_ADDRESS",
            "DATE_TIME",
            "LOCATION",
            "US_SSN",
            "MEDICAL_LICENSE",
            "US_DRIVER_LICENSE",
            # Custom entities
            "MEDICAL_RECORD_NUMBER",
            "ROOM",
            "GUARDIAN_NAME",
            "PEDIATRIC_AGE",
        ],
        description="PHI entity types to detect"
    )
    phi_score_threshold: float = Field(
        default=0.35,
        description="Minimum confidence score for PHI detection (lower = more aggressive)"
    )
    enable_custom_recognizers: bool = Field(
        default=True,
        description="Enable pediatric-specific custom recognizers"
    )

    # =========================================================================
    # Custom MRN Patterns (hospital-specific, may need adjustment)
    # =========================================================================
    mrn_patterns: List[str] = Field(
        default=[
            r"\b\d{7,10}\b",           # Generic 7-10 digit number
            r"\bMRN[:\s]?\d{6,10}\b",  # "MRN: 1234567" format
            r"\b[A-Z]{2}\d{6,8}\b",    # Letter prefix format (e.g., "AB12345678")
        ],
        description="Regex patterns for Medical Record Numbers"
    )

    # =========================================================================
    # Application Settings
    # =========================================================================
    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    max_audio_size_mb: int = Field(
        default=50,
        description="Maximum audio file size in MB"
    )
    temp_dir: str = Field(
        default="/tmp/handoff-transcriber",
        description="Temporary directory for audio processing"
    )

    # =========================================================================
    # SpaCy Configuration
    # =========================================================================
    spacy_model: str = Field(
        default="en_core_web_lg",
        description="SpaCy model for NER. Options: en_core_web_sm, en_core_web_md, en_core_web_lg"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
