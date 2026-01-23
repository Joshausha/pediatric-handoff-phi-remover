"""
Configuration module using Pydantic Settings.

All settings can be overridden via environment variables or .env file.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


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
    phi_entities: list[str] = Field(
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
    # Deny List - Medical terms that should NOT be flagged as PHI
    # =========================================================================
    # These are medical abbreviations/terms that NER models often misclassify
    deny_list_location: list[str] = Field(
        default=[
            "NC",    # Nasal cannula
            "RA",    # Room air
            "OR",    # Operating room (generic)
            "ER",    # Emergency room (generic)
            "ED",    # Emergency department
            "IV",    # Intravenous
            "PO",    # By mouth (per os)
            "IM",    # Intramuscular
            "SQ",    # Subcutaneous
            "PR",    # Per rectum
            "GT",    # Gastrostomy tube
            "NG",    # Nasogastric
            "OG",    # Orogastric
            "NJ",    # Nasojejunal
        ],
        description="Medical abbreviations that should not be flagged as LOCATION"
    )
    deny_list_person: list[str] = Field(
        default=[
            "mom",   # Generic relationship, not a name
            "dad",   # Generic relationship, not a name
            "Mom",   # Generic relationship
            "Dad",   # Generic relationship
            "parent",
            "parents",
            "guardian",
            "caregiver",
            "nurse",
            "doctor",
            "attending",
            "resident",
            "fellow",
            "intern",
            "NP",    # Nurse practitioner
            "PA",    # Physician assistant
            "RN",    # Registered nurse
            "LPN",   # Licensed practical nurse
            "CNA",   # Certified nursing assistant
        ],
        description="Words that should not be flagged as PERSON"
    )
    # Patterns for pediatric clinical terms misclassified as DATE_TIME
    deny_list_date_patterns: list[str] = Field(
        default=[
            r"\d+\s*(?:month|months|mo)\s*old",      # "2 month old", "2 months old"
            r"\d+\s*(?:week|weeks|wk)\s*old",        # "3 week old", "3 weeks old"
            r"\d+\s*(?:day|days)\s*old",             # "5 day old", "5 days old"
            r"\d+\s*(?:year|years|yr|yrs)\s*old",    # "4 year old", "6 years old"
            r"\d+\s*weeker",                          # "35 weeker" (premature infant)
            r"\d+\s*(?:week|weeks)\s*gestation",     # "36 weeks gestation"
            r"\d+\s*hours?",                          # "48 hours" (clinical duration)
        ],
        description="Regex patterns for clinical age terms that should not be flagged as DATE_TIME"
    )

    # =========================================================================
    # Custom MRN Patterns (hospital-specific, may need adjustment)
    # =========================================================================
    mrn_patterns: list[str] = Field(
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
        default=False,
        description="Enable debug mode (set DEBUG=true in environment to enable)"
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

    # =========================================================================
    # Security Configuration
    # =========================================================================
    cors_origins: list[str] = Field(
        default=["http://localhost:8000", "http://127.0.0.1:8000"],
        description="Allowed CORS origins. Set CORS_ORIGINS env var to comma-separated list for production."
    )
    rate_limit_requests: int = Field(
        default=10,
        description="Maximum requests per rate limit window"
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Rate limit window in seconds"
    )
    enable_audit_logging: bool = Field(
        default=True,
        description="Enable HIPAA-compliant audit logging (no PHI in logs)"
    )
    audit_log_file: str = Field(
        default="logs/audit.log",
        description="Path to audit log file"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
