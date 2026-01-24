"""
Medical-context Presidio recognizers.

Handles general medical PHI patterns:
- Medical Record Numbers (MRN)
- Room numbers (with case-insensitive matching)

Updated: Phase 04-02 - Improved patterns for case-insensitivity and edge cases.
"""


from presidio_analyzer import Pattern, PatternRecognizer


def get_medical_recognizers() -> list[PatternRecognizer]:
    """
    Create medical-context PHI recognizers.

    Returns:
        List of PatternRecognizer instances
    """
    recognizers = []

    # =========================================================================
    # Medical Record Number (MRN) Recognizer
    # =========================================================================
    mrn_patterns = [
        # Explicit MRN label (case-insensitive)
        Pattern(
            name="mrn_labeled",
            regex=r"(?i)\b(?:mrn)[:\s#]?\s*(\d{6,10})\b",
            score=0.85
        ),
        # Medical record / chart number (case-insensitive)
        # Pattern: "Medical record number: 87654321" or "chart #12345678"
        Pattern(
            name="medical_record",
            regex=r"(?i)\b(?:medical\s+record|chart)\s*(?:number)?[:#]?\s*\d{6,10}\b",
            score=0.75
        ),
        # Letter prefix format (e.g., "AB12345678") - keep case-sensitive for letter prefix
        Pattern(
            name="mrn_prefix",
            regex=r"\b[A-Z]{2}\d{6,8}\b",
            score=0.6
        ),
        # Hash prefix: "#12345678" (patient ID shorthand)
        Pattern(
            name="mrn_hash",
            regex=r"#(\d{6,10})\b",
            score=0.7
        ),
        # "Patient #" followed by number (case-insensitive)
        Pattern(
            name="patient_number",
            regex=r"(?i)\bpatient\s*#?\s*(\d{6,10})\b",
            score=0.75
        ),
    ]

    mrn_recognizer = PatternRecognizer(
        supported_entity="MEDICAL_RECORD_NUMBER",
        name="MRN Recognizer",
        patterns=mrn_patterns,
        context=["mrn", "medical record", "chart", "record number", "patient id"]
    )
    recognizers.append(mrn_recognizer)

    # =========================================================================
    # Room Number Recognizer
    # =========================================================================
    # NOTE: Using (?i) flag for case-insensitive matching instead of lookbehind.
    # Lookbehind (e.g., (?<=Room )) fails at start-of-line (position 0).
    # These patterns capture the full match but context ensures appropriate usage.
    room_patterns = [
        # Standard room format: "Room 302", "Rm 404", "room 5A", "ROOM 12"
        # Case-insensitive, handles start-of-line
        Pattern(
            name="room_standard",
            regex=r"(?i)\b(?:room|rm)\s+\d{1,4}[A-Za-z]?\b",
            score=0.70
        ),
        # Bed number: "Bed 5", "bed 12A"
        Pattern(
            name="bed_standard",
            regex=r"(?i)\bbed\s+\d{1,2}[A-Za-z]?\b",
            score=0.65
        ),
        # ICU bed formats with unit names (preserve unit, redact number)
        # "PICU bed 7", "picu bed 3A", "NICU bed 21", "ICU bed 4"
        Pattern(
            name="icu_bed",
            regex=r"(?i)\b(?:picu|nicu|icu)\s+bed\s+\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # Bay number (NICU specific): "bay 5", "Bay 12"
        Pattern(
            name="bay_number",
            regex=r"(?i)\bbay\s+\d{1,2}[A-Za-z]?\b",
            score=0.65
        ),
        # Isolette number (NICU specific): "isolette 21", "Isolette 3"
        Pattern(
            name="isolette_number",
            regex=r"(?i)\bisolette\s+\d{1,3}\b",
            score=0.70
        ),
        # Multi-part room numbers: "Room 3-22", "room 4/11"
        Pattern(
            name="room_multipart",
            regex=r"(?i)\b(?:room|rm)\s+\d{1,2}[-/]\d{1,2}\b",
            score=0.70
        ),
        # Floor + direction: "4 West", "3 South", "2 north"
        # Case-insensitive for direction words
        Pattern(
            name="floor_unit",
            regex=r"(?i)\b\d{1,2}\s*(?:north|south|east|west|tower|floor)\b",
            score=0.50
        ),
    ]

    room_recognizer = PatternRecognizer(
        supported_entity="ROOM",
        name="Room Number Recognizer",
        patterns=room_patterns,
        context=["room", "bed", "floor", "unit", "located", "admitted to", "transferred to", "bay", "isolette"]
    )
    recognizers.append(room_recognizer)

    return recognizers
