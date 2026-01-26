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
        description="DEPRECATED: Use phi_score_thresholds instead. Global fallback threshold."
    )
    phi_score_thresholds: dict[str, float] = Field(
        default={
            # Phase 2 calibrated thresholds (2026-01-23)
            # Methodology: PR curve analysis, F2 optimization, recall>=90% floor
            "PERSON": 0.30,              # R=98.9%, P=73.3%, F2=92.4% - meets 90% recall
            "PHONE_NUMBER": 0.30,        # R=75.7%, P=99.4%, F2=79.5% - needs Phase 4 patterns
            "EMAIL_ADDRESS": 0.30,       # R=100%, P=100%, F2=100% - meets 90% recall
            "DATE_TIME": 0.30,           # R=95.1%, P=35.3%, F2=71.0% - meets 90% recall
            "LOCATION": 0.30,            # R=20.0%, P=70.3%, F2=23.3% - needs Phase 4 patterns
            "MEDICAL_RECORD_NUMBER": 0.30,  # R=72.3%, P=89.2%, F2=75.1% - needs Phase 4 patterns
            "ROOM": 0.30,                # R=32.1%, P=53.1%, F2=34.8% - needs Phase 4 patterns
            "PEDIATRIC_AGE": 0.30,       # R=35.8%, P=85.1%, F2=40.5% - needs Phase 4 patterns
            # Guardian names mapped to PERSON threshold
            "GUARDIAN_NAME": 0.30,
        },
        description="Per-entity confidence thresholds (Phase 2 calibrated 2026-01-23)"
    )

    # =========================================================================
    # Threshold Calibration Metadata
    # =========================================================================
    threshold_calibration_date: str = Field(
        default="2026-01-23",
        description="ISO date of threshold calibration"
    )
    threshold_calibration_method: str = Field(
        default="PR curve analysis, F2 optimization, recall>=90% floor",
        description="Methodology used for threshold calibration"
    )
    threshold_calibration_dataset: str = Field(
        default="synthetic_handoffs.json (500) + adversarial_handoffs.json (100)",
        description="Datasets used for threshold calibration"
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
            # Pediatric clinical descriptors (Phase 4 addition)
            "baby",
            "infant",
            "newborn",
            "neonate",
            # Generic terms (Phase 6 addition)
            "kid",
            "child",
            "toddler",
            # Medical abbreviations mistaken for names (Phase 6 addition)
            "DKA",   # Diabetic ketoacidosis
            "CT",    # Computed tomography
            "MRI",   # Magnetic resonance imaging
            "EEG",   # Electroencephalogram
            "ECG",   # Electrocardiogram
            "EKG",   # Electrocardiogram (alternate)
            "ICU",   # Intensive care unit
            "PICU",  # Pediatric ICU
            "NICU",  # Neonatal ICU
        ],
        description="Words that should not be flagged as PERSON"
    )
    deny_list_guardian_name: list[str] = Field(
        default=[
            "parent", "guardian", "caregiver", "family",
            # Speech artifacts (Phase 4 addition)
            "uh", "um",
        ],
        description="Generic relationship terms not flagged as GUARDIAN_NAME"
    )
    deny_list_pediatric_age: list[str] = Field(
        default=["infant", "toddler", "child", "adolescent", "teen", "newborn", "neonate"],
        description="Generic age categories not flagged as PEDIATRIC_AGE"
    )
    deny_list_date_time: list[str] = Field(
        default=[
            # Relative time words
            "today", "tonight", "yesterday", "tomorrow", "overnight",
            # Dosing schedules
            "q4h", "q6h", "q8h", "q12h",
            "BID", "TID", "QID", "PRN", "prn",
            "daily", "nightly", "qd", "qhs",
            # Day of illness patterns (clinical timeline - not PHI)
            "day 1", "day 2", "day 3", "day 4", "day 5", "day 6", "day 7",
            "day 8", "day 9", "day 10", "day 11", "day 12", "day 13", "day 14",
            # Day of life (neonatal - not PHI)
            "day of life", "dol",
            "dol 1", "dol 2", "dol 3", "dol 4", "dol 5", "dol 6", "dol 7",
            # Age descriptors - SPACE separated (not PHI under HIPAA unless 90+)
            "days old", "weeks old", "months old", "years old",
            "week old", "month old", "year old", "day old",
            # Age descriptors - HYPHENATED (Phase 6 fix: matches "7-year-old" etc.)
            "day-old", "week-old", "month-old", "year-old",
            "days-old", "weeks-old", "months-old", "years-old",
            # Duration patterns (not dates)
            "hours ago", "minutes ago",
            "this morning", "this afternoon", "this evening", "last night",
            "three minutes", "two minutes", "five minutes",
        ],
        description="Generic time references, dosing schedules, and clinical timeline terms not flagged as DATE_TIME"
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
    # Spoken Handoff Relevance Weights (Phase 8)
    # =========================================================================
    # Weights for weighted recall calculation based on spoken handoff relevance
    # Higher weight = more frequently spoken during I-PASS handoffs
    # Source: SPOKEN_HANDOFF_ANALYSIS.md (2026-01-25)
    spoken_handoff_weights: Dict[str, int] = Field(
        default={
            "PERSON": 5,              # Critical - spoken constantly
            "GUARDIAN_NAME": 5,       # Same as PERSON
            "ROOM": 4,                # High - used for patient identification
            "PHONE_NUMBER": 2,        # Medium - occasionally spoken
            "DATE_TIME": 2,           # Medium - admission dates, but often vague
            "MEDICAL_RECORD_NUMBER": 1,  # Low - rarely spoken aloud
            "EMAIL_ADDRESS": 0,       # Never spoken
            "LOCATION": 0,            # Never spoken - addresses not relevant
            "PEDIATRIC_AGE": 0,       # User decision - ages not PHI under HIPAA
        },
        description="Spoken handoff relevance weights for weighted recall calculation"
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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
