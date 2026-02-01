"""
Configuration module using Pydantic Settings.

All settings can be overridden via environment variables or .env file.
"""

from functools import lru_cache

from pydantic import Field, field_validator
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
            "PROVIDER_NAME",
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
            # Provider names (Phase 19) - title-prefixed patterns
            "PROVIDER_NAME": 0.30,
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
            # Basic medical abbreviations
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

            # ===== Phase 11-02: Flow Terminology Expansion =====
            # Flow rates and oxygen delivery (commonly misdetected as LOCATION)
            "high flow",                # High flow oxygen
            "low flow",                 # Low flow oxygen
            "on high",                  # "Currently on high"
            "on low",                   # "Currently on low"
            "high",                     # Standalone in respiratory context
            "low",                      # Standalone in respiratory context
            "flow",                     # Generic flow term
            "nasal high flow",          # Nasal high flow oxygen
            "high flow nasal cannula",  # HFNC spelled out
            "HFNC",                     # High flow nasal cannula abbreviation

            # Room air variations
            "room air",                 # Full phrase (RA already covered)

            # Hospital unit names (ensure protected - some already in PERSON list)
            "PICU",                     # Pediatric ICU
            "NICU",                     # Neonatal ICU
            "ICU",                      # Intensive care unit

            # Clinical location context (not PHI)
            "bedside",                  # At bedside
            "floor",                    # Hospital floor
        ],
        description="Medical abbreviations that should not be flagged as LOCATION"
    )
    deny_list_person: list[str] = Field(
        default=[
            # Relationships and roles
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
            "CVICU", # Cardiovascular ICU
            "CCU",   # Cardiac care unit
            "PACU",  # Post-anesthesia care unit

            # ===== Phase 11-02: Clinical Descriptor Expansion =====
            # Clinical symptom descriptors (sound like names to NER)
            "barky",                    # Croup cough descriptor

            # Location descriptors in clinical context
            "bedside",                  # At bedside / bedside nurse
            "room",                     # Room air context

            # Clinical status descriptors (rarely flagged but preventative)
            "stable",                   # Patient status
            "critical",                 # Patient status

            # Respiratory terms (prevent over-detection)
            "flow",                     # Prevent "Flow" as name

            # Common prepositions sometimes flagged as names
            "at",                       # "mom at bedside" - prevent "at" detection
        ],
        description="Words that should not be flagged as PERSON"
    )
    deny_list_guardian_name: list[str] = Field(
        default=[
            "parent", "guardian", "caregiver", "family",
            # Speech artifacts (Phase 4 addition)
            "uh", "um",
            # Common prepositions (Phase 11 addition - prevent "mom at bedside")
            "at",
        ],
        description="Generic relationship terms not flagged as GUARDIAN_NAME"
    )
    deny_list_pediatric_age: list[str] = Field(
        default=["infant", "toddler", "child", "adolescent", "teen", "newborn", "neonate"],
        description="Generic age categories not flagged as PEDIATRIC_AGE"
    )
    deny_list_provider_name: list[str] = Field(
        default=[
            # Generic role terms (not names)
            "attending", "fellow", "resident", "intern",
            "doctor", "nurse", "nursing", "physician", "provider", "clinician",
            # Title abbreviations (prevent standalone flagging)
            "Dr", "NP", "PA", "RN", "LPN", "CNA", "MD",
            # Speech artifacts
            "uh", "um", "the",
        ],
        description="Generic provider terms not flagged as PROVIDER_NAME"
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

            # ===== Phase 11-01: Duration Pattern Expansion =====
            # Simple duration (written-out numbers) - DAYS
            "one day", "two days", "three days", "four days", "five days",
            "six days", "seven days",
            # Simple duration (written-out numbers) - WEEKS
            "one week", "two weeks", "three weeks", "four weeks",
            # Simple duration (written-out numbers) - MONTHS
            "one month", "two months", "three months",
            # Simple duration (written-out numbers) - HOURS
            "one hour", "two hours", "three hours", "four hours", "five hours",
            "six hours", "eight hours", "twelve hours", "twenty-four hours",

            # Numeric duration (common values)
            "24 hours", "48 hours", "72 hours",
            "1 hour", "2 hours", "3 hours", "4 hours", "6 hours",
            "12 hours", "18 hours", "36 hours", "60 hours",

            # Informal duration
            "a day", "a few days", "couple days", "half a day",
            "a week", "a few weeks", "couple weeks",
            "a couple of days", "a couple of hours",
            "another hour", "another day", "one more hour", "one more day",

            # Duration ranges
            "two to three days", "three to four days", "one to two weeks",
            "a day or two", "a few more days",

            # Recent past patterns (substring matches)
            "the past two days", "the past few days", "the last few days",
            "last 24 hours", "past 24 hours", "past 48 hours",
            "the past week", "the last week",

            # Duration context words
            "days ago", "weeks ago", "months ago",
            "a day and a half", "day and a half",
            "five hours ago", "six hours ago", "twelve hours ago",

            # Clinical percentages (oxygen saturation context)
            "mid-90s", "low 90s", "high 90s",
            "mid-80s", "low 80s", "high 80s",

            # Dosing counts that look like dates
            "4 doses", "3 doses", "2 doses", "1 dose",
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
    # Spoken Handoff Weights (Phase 8 + v2.2 Dual-Weighting)
    # =========================================================================
    # Two separate weight schemes for different evaluation purposes:
    # 1. Frequency weights: How often is this PHI type actually spoken?
    # 2. Risk weights: If missed, how severe is the PHI leak?
    #
    # Source: SPOKEN_HANDOFF_ANALYSIS.md (updated 2026-01-28)

    # Frequency weights: Based on how often each PHI type is spoken in I-PASS handoffs
    spoken_handoff_weights: dict[str, float] = Field(
        default={
            "PERSON": 5.0,              # Constantly - patient name every handoff
            "GUARDIAN_NAME": 4.0,       # Commonly - "mom Jessica at bedside"
            "ROOM": 4.0,                # Constantly - primary identification
            "DATE_TIME": 2.0,           # Sometimes - admission/illness onset dates
            "PHONE_NUMBER": 1.0,        # Rarely - usually referenced, not spoken aloud
            "MEDICAL_RECORD_NUMBER": 0.5,  # Almost never - on screen, not spoken
            "LOCATION": 0.5,            # Almost never - but "transferred from Memorial" possible
            "EMAIL_ADDRESS": 0.0,       # Never spoken in handoffs
            "PEDIATRIC_AGE": 0.0,       # N/A - not PHI under HIPAA unless 90+
            "PROVIDER_NAME": 3.0,       # Commonly - "Dr. Smith is primary"
        },
        description="Frequency weights: how often each PHI type is spoken in handoffs"
    )

    # Risk weights: Severity if this PHI type leaks (how identifying is it?)
    spoken_handoff_risk_weights: dict[str, float] = Field(
        default={
            "MEDICAL_RECORD_NUMBER": 5.0,  # THE unique identifier - most critical
            "PERSON": 5.0,              # Directly identifies patient
            "PHONE_NUMBER": 4.0,        # Personally identifying contact
            "GUARDIAN_NAME": 4.0,       # Identifies family member
            "LOCATION": 4.0,            # Addresses are very identifying
            "EMAIL_ADDRESS": 4.0,       # Personally identifying
            "ROOM": 2.0,                # Semi-identifying (hospital context only)
            "DATE_TIME": 1.0,           # Rarely uniquely identifying alone
            "PEDIATRIC_AGE": 0.0,       # Not PHI under HIPAA unless 90+
            "PROVIDER_NAME": 2.0,       # Moderate risk - providers less identifying than patients
        },
        description="Risk weights: severity if each PHI type leaks (how identifying)"
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
    # Transfer Facility Configuration (Phase 23 - v2.4)
    # =========================================================================
    transfer_facility_mode: str = Field(
        default="conservative",
        description=(
            "Transfer facility handling mode:\n"
            "- 'conservative' (default): Redact all locations per HIPAA Safe Harbor\n"
            "- 'clinical': Preserve transfer facility names for care coordination\n"
            "WARNING: Clinical mode does not meet HIPAA Safe Harbor requirements"
        )
    )

    @field_validator("transfer_facility_mode")
    @classmethod
    def validate_transfer_mode(cls, v):
        allowed = ["conservative", "clinical"]
        if v not in allowed:
            raise ValueError(
                f"transfer_facility_mode must be one of {allowed}, got '{v}'"
            )
        return v

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
