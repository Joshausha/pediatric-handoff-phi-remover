"""
Medical-context Presidio recognizers.

Handles general medical PHI patterns:
- Medical Record Numbers (MRN)
- Room numbers (with case-insensitive matching)
- Phone numbers (international formats, extensions)

Updated: Phase 04-04 - Added phone number patterns for international/extension formats.
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
        # Using lookbehind to match only "bed X" portion, preserving unit name
        # "PICU bed 7" -> "PICU [ROOM]", "NICU bed 21" -> "NICU [ROOM]"

        # PICU bed - match only "bed X" portion (PICU preserved)
        Pattern(
            name="picu_bed",
            regex=r"(?i)(?<=picu )bed\s+\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # NICU bed - match only "bed X" portion (NICU preserved)
        Pattern(
            name="nicu_bed",
            regex=r"(?i)(?<=nicu )bed\s+\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # ICU bed - match only "bed X" portion (ICU preserved)
        Pattern(
            name="icu_bed",
            regex=r"(?i)(?<=icu )bed\s+\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # CVICU bed - match only "bed X" portion (CVICU preserved)
        Pattern(
            name="cvicu_bed",
            regex=r"(?i)(?<=cvicu )bed\s+\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # CCU bed - match only "bed X" portion (CCU preserved)
        Pattern(
            name="ccu_bed",
            regex=r"(?i)(?<=ccu )bed\s+\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # PACU bed - match only "bed X" portion (PACU preserved)
        Pattern(
            name="pacu_bed",
            regex=r"(?i)(?<=pacu )bed\s+\d{1,3}[A-Za-z]?\b",
            score=0.75
        ),
        # L&D room - match only "room X" portion (L&D preserved)
        Pattern(
            name="ld_room",
            regex=r"(?i)(?<=l&d )room\s+\d{1,4}[A-Za-z]?\b",
            score=0.75
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

        # =====================================================================
        # NEW CONTEXTUAL PATTERNS - Phase 17-01
        # Low-confidence patterns that rely on context words for confirmation
        # =====================================================================

        # Room synonym patterns (score=0.55)
        # "space 5", "pod 3", "cubicle 12", "crib 8"
        Pattern(
            name="room_space",
            regex=r"(?i)\bspace\s+\d{1,3}\b",
            score=0.55
        ),
        Pattern(
            name="room_pod",
            regex=r"(?i)\bpod\s+\d{1,3}\b",
            score=0.55
        ),
        Pattern(
            name="room_cubicle",
            regex=r"(?i)\bcubicle\s+\d{1,3}\b",
            score=0.55
        ),
        Pattern(
            name="room_crib",
            regex=r"(?i)\bcrib\s+\d{1,3}\b",
            score=0.55
        ),

        # Explicit room context patterns - replaces overly broad contextual pattern
        # Requires explicit room context words to avoid false positives on dates/times/phones/addresses
        # "patient in 8", "moved to 512", "transferred from 302"
        # Negative lookahead prevents matching street addresses (numbers followed by street names)
        Pattern(
            name="room_number_with_location_prep",
            regex=r"(?i)(?:patient\s+in|currently\s+in|over\s+in|moved\s+to|moving\s+to|transferred\s+to|transferred\s+from|placed\s+in|assigned\s+to)\s+(\d{1,4})(?!\s+\w+\s+(?:Street|Drive|Road|Avenue|Blvd|Lane|Way|Court|Place|Circle|Cliffs))\b",
            score=0.60  # Higher score - explicit context required
        ),

        # Standalone hyphenated room (without prefix): "3-22", "5-10", "2-25"
        # Common in PICU/NICU settings where room format is floor-bed
        # Using word boundary and context to reduce false positives
        Pattern(
            name="room_hyphenated_standalone",
            regex=r"\b\d{1,2}-\d{1,2}\b",
            score=0.55  # Lower score - relies on context for confirmation
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
        context=[
            # Existing context words
            "room", "bed", "floor", "unit", "located", "admitted to", "transferred to",
            "bay", "isolette", "picu", "nicu", "icu", "cvicu", "ccu", "pacu", "l&d",
            # NEW: Location prepositions (enable weak pattern detection)
            "in", "to", "from",
            # NEW: Movement verbs
            "moved", "moving", "transferred", "placed", "assigned",
            # NEW: Room synonyms
            "space", "pod", "cubicle", "crib",
            # NEW: Patient location phrases
            "patient in", "currently in", "over in"
        ]
    )
    recognizers.append(room_recognizer)

    # =========================================================================
    # Phone Number Recognizer (Extended Formats)
    # =========================================================================
    # Catches formats that Presidio's default phone recognizer misses:
    # - International with 001 prefix (001-411-671-8227)
    # - International with +1 prefix (+1-899-904-9027x87429)
    # - Dot-separated (538.372.6247)
    # - Parentheses without space ((392)832-2602x56342)
    # - 10-digit unformatted (3405785932) - context-dependent
    phone_patterns = [
        # International with 001 prefix: 001-411-671-8227, 001.723.437.4989x41343
        Pattern(
            name="phone_001_intl",
            regex=r"(?i)001[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}(?:x\d{1,5})?\b",
            score=0.85
        ),
        # International with +1 prefix: +1-899-904-9027x87429, +1.788.499.2107
        Pattern(
            name="phone_plus1_intl",
            regex=r"\+1[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}(?:x\d{1,5})?\b",
            score=0.90
        ),
        # Dot-separated format: 538.372.6247, 200.954.1199x867
        Pattern(
            name="phone_dot_separated",
            regex=r"\b\d{3}\.\d{3}\.\d{4}(?:x\d{1,5})?\b",
            score=0.80
        ),
        # Parentheses format without space: (392)832-2602x56342, (288)857-4489
        Pattern(
            name="phone_parens_no_space",
            regex=r"\(\d{3}\)\d{3}[-.]?\d{4}(?:x\d{1,5})?\b",
            score=0.85
        ),
        # 10-digit unformatted (context-dependent): 3405785932
        # Lower score - requires context words to avoid false positives
        Pattern(
            name="phone_10digit_unformatted",
            regex=r"\b\d{10}\b",
            score=0.60
        ),
    ]

    phone_recognizer = PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        name="Phone Number Recognizer",
        patterns=phone_patterns,
        context=["call", "phone", "contact", "reach", "pager", "cell", "mobile", "number", "tel", "telephone"]
    )
    recognizers.append(phone_recognizer)

    return recognizers
