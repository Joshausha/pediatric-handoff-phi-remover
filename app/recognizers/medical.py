"""
Medical-context Presidio recognizers.

Handles general medical PHI patterns:
- Medical Record Numbers (MRN)
- Room numbers
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
        # Explicit MRN label
        Pattern(
            name="mrn_labeled",
            regex=r"\b(?:MRN|mrn)[:\s#]?\s*(\d{6,10})\b",
            score=0.85
        ),
        # Medical record / chart number (case-insensitive)
        Pattern(
            name="medical_record",
            regex=r"(?i)\b(?:medical\s+record|chart)\s*(?:number|#|:)?\s*:?\s*(\d{6,10})\b",
            score=0.75
        ),
        # Letter prefix format (e.g., "AB12345678")
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
        # "Patient #" followed by number
        Pattern(
            name="patient_number",
            regex=r"\b[Pp]atient\s*#?\s*(\d{6,10})\b",
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
    room_patterns = [
        # Standard room format: "Room 302", "Rm 404", "room 5A"
        # Using lookbehind to only capture the room number
        Pattern(
            name="room_standard",
            regex=r"(?<=Room |room |Rm |rm )\d{1,4}[A-Za-z]?\b",
            score=0.6
        ),
        # Bed number: "Bed 5", "bed 12A"
        Pattern(
            name="bed_number",
            regex=r"(?<=bed |Bed )\d{1,2}[A-Za-z]?\b",
            score=0.55
        ),
        # ICU bed numbers: preserve unit name, redact only number
        # "PICU bed 3" -> "PICU bed [ROOM]"
        Pattern(
            name="picu_bed",
            regex=r"(?<=PICU bed |PICU Bed )\d{1,3}[A-Za-z]?\b",
            score=0.7
        ),
        Pattern(
            name="nicu_bed",
            regex=r"(?<=NICU bed |NICU Bed )\d{1,3}[A-Za-z]?\b",
            score=0.7
        ),
        Pattern(
            name="icu_bed",
            regex=r"(?<=ICU bed |ICU Bed )\d{1,3}[A-Za-z]?\b",
            score=0.7
        ),
        # Floor + direction: "4 West", "3 South"
        Pattern(
            name="floor_unit",
            regex=r"\b(\d{1,2})\s*(?:North|South|East|West|Tower|Floor)\b",
            score=0.5
        ),
    ]

    room_recognizer = PatternRecognizer(
        supported_entity="ROOM",
        name="Room Number Recognizer",
        patterns=room_patterns,
        context=["room", "bed", "floor", "unit", "located", "admitted to"]
    )
    recognizers.append(room_recognizer)

    # =========================================================================
    # Short Phone Number Recognizer (7-digit local numbers)
    # =========================================================================
    # Presidio's PHONE_NUMBER expects 10-digit formats; this catches shorter ones
    phone_patterns = [
        # 7-digit with dash: "555-1234"
        Pattern(
            name="phone_7digit_dash",
            regex=r"\b\d{3}-\d{4}\b",
            score=0.4
        ),
        # 7-digit with dot: "555.1234"
        Pattern(
            name="phone_7digit_dot",
            regex=r"\b\d{3}\.\d{4}\b",
            score=0.4
        ),
    ]

    phone_recognizer = PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        name="Short Phone Recognizer",
        patterns=phone_patterns,
        context=["call", "reach", "phone", "contact", "number", "tel", "cell", "mobile"]
    )
    recognizers.append(phone_recognizer)

    # =========================================================================
    # Street Address Recognizer
    # =========================================================================
    address_patterns = [
        # Standard street address: "123 Main Street", "425 Oak St"
        Pattern(
            name="street_address",
            regex=r"\b\d{1,5}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl)\b",
            score=0.6
        ),
    ]

    address_recognizer = PatternRecognizer(
        supported_entity="LOCATION",
        name="Street Address Recognizer",
        patterns=address_patterns,
        context=["lives", "address", "located", "home", "residence"]
    )
    recognizers.append(address_recognizer)

    return recognizers
