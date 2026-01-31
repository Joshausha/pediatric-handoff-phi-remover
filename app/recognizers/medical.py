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
        # DEPRECATED: Full match patterns (score lowered to 0.50)
        # These patterns match "bed 847" instead of just "847"
        # Kept for fallback but number-only patterns (Phase 17-03) take priority
        # Standard room format: "Room 302", "Rm 404", "room 5A", "ROOM 12"
        # Case-insensitive, handles start-of-line
        Pattern(
            name="room_standard",
            regex=r"(?i)\b(?:room|rm)\s+\d{1,4}[A-Za-z]?\b",
            score=0.50  # Lowered from 0.70 - number-only patterns preferred
        ),
        # Bed number: "Bed 5", "bed 12A"
        Pattern(
            name="bed_standard",
            regex=r"(?i)\bbed\s+\d{1,2}[A-Za-z]?\b",
            score=0.50  # Lowered from 0.65 - number-only patterns preferred
        ),
        # ICU bed formats with unit names (preserve unit, redact number)
        # Updated Phase 17-03: Now matches ONLY the number (not "bed X")
        # "PICU bed 7" -> matches "7", "NICU bed 21" -> matches "21"

        # PICU bed - match only the number (PICU and "bed" preserved)
        Pattern(
            name="picu_bed",
            regex=r"(?i)(?<=picu bed )\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # NICU bed - match only the number (NICU and "bed" preserved)
        Pattern(
            name="nicu_bed",
            regex=r"(?i)(?<=nicu bed )\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # ICU bed - match only the number (ICU and "bed" preserved)
        Pattern(
            name="icu_bed",
            regex=r"(?i)(?<=icu bed )\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # CVICU bed - match only the number (CVICU and "bed" preserved)
        Pattern(
            name="cvicu_bed",
            regex=r"(?i)(?<=cvicu bed )\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # CCU bed - match only the number (CCU and "bed" preserved)
        Pattern(
            name="ccu_bed",
            regex=r"(?i)(?<=ccu bed )\d{1,3}[A-Za-z]?\b",
            score=0.80
        ),
        # PACU bed - match only the number (PACU and "bed" preserved)
        Pattern(
            name="pacu_bed",
            regex=r"(?i)(?<=pacu bed )\d{1,3}[A-Za-z]?\b",
            score=0.75
        ),
        # L&D room - match only the number (L&D and "room" preserved)
        Pattern(
            name="ld_room",
            regex=r"(?i)(?<=l&d room )\d{1,4}[A-Za-z]?\b",
            score=0.75
        ),
        # Bay number (NICU specific): "bay 5", "Bay 12"
        # Lowered score - number-only pattern preferred
        Pattern(
            name="bay_number",
            regex=r"(?i)\bbay\s+\d{1,2}[A-Za-z]?\b",
            score=0.50  # Lowered from 0.65 - number-only patterns preferred
        ),
        # Isolette number (NICU specific): "isolette 21", "Isolette 3"
        # DEPRECATED - number-only pattern (isolette_number_only) preferred
        Pattern(
            name="isolette_number",
            regex=r"(?i)\bisolette\s+\d{1,3}\b",
            score=0.50  # Lowered from 0.70 - number-only patterns preferred
        ),
        # Multi-part room numbers: "Room 3-22", "room 4/11"
        Pattern(
            name="room_multipart",
            regex=r"(?i)\b(?:room|rm)\s+\d{1,2}[-/]\d{1,2}\b",
            score=0.70
        ),

        # =====================================================================
        # NUMBER-ONLY PATTERNS - Phase 17-03
        # Match only the number (not "bed 847", just "847") to align with ground truth
        # Uses lookbehind to require context but not include it in match
        # =====================================================================

        # Pattern 1: Room number after "room" - match only the number
        # "Room 228" -> matches "228", "room 16" -> matches "16"
        # Uses lookbehind to require context but not include it in match
        Pattern(
            name="room_number_after_room",
            regex=r"(?i)(?<=\broom\s)\d{1,4}[A-Za-z]?\b",
            score=0.70
        ),

        # Pattern 2: Bed number after "bed" - match only the number
        # "bed 17" -> matches "17", "PICU bed 847" -> matches "847"
        Pattern(
            name="bed_number_only",
            regex=r"(?i)(?<=\bbed\s)\d{1,4}[A-Za-z]?\b",
            score=0.70
        ),

        # Pattern 3: Isolette number after "isolette" - match only the number
        # "isolette 907" -> matches "907"
        Pattern(
            name="isolette_number_only",
            regex=r"(?i)(?<=\bisolette\s)\d{1,4}\b",
            score=0.70
        ),

        # Pattern 4: Space/pod/cubicle/crib number only (match number after synonym)
        # "space 5" -> matches "5", "pod 3" -> matches "3"
        # NOTE: Python regex lookbehind has limitations with alternation
        # Using separate patterns for reliability
        Pattern(
            name="space_number_only",
            regex=r"(?i)(?<=\bspace\s)\d{1,3}\b",
            score=0.65
        ),
        Pattern(
            name="pod_number_only",
            regex=r"(?i)(?<=\bpod\s)\d{1,3}\b",
            score=0.65
        ),
        Pattern(
            name="cubicle_number_only",
            regex=r"(?i)(?<=\bcubicle\s)\d{1,3}\b",
            score=0.65
        ),
        Pattern(
            name="crib_number_only",
            regex=r"(?i)(?<=\bcrib\s)\d{1,3}\b",
            score=0.65
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

    # =========================================================================
    # Location Recognizer (Transfer/Medical Context)
    # =========================================================================
    # Pattern-based LOCATION detection for clinical handoff contexts.
    # Supplements spaCy NER baseline (20% recall) with context-specific patterns.
    # Target: ≥60% recall with lookbehind patterns preserving context words.

    location_patterns = [
        # === TRANSFER CONTEXT PATTERNS (50% of dataset) ===
        # High confidence - explicit transfer language indicates location follows
        # NOTE: Use (?-i:[A-Z]) to require uppercase first letter despite global (?i)
        # This prevents matching lowercase words like "yesterday" after the location

        # "transferred from Memorial Hospital" -> matches "Memorial Hospital"
        # Also matches "home" as keyword since it's a valid location
        # Fixed-width lookbehind: "transferred from " = 17 chars
        Pattern(
            name="transferred_from",
            regex=r"(?i)(?<=transferred from )(home|(?-i:[A-Z])[a-z']*(?:\s+(?-i:[A-Z])[a-z']*)*(?:\s+(?:Hospital|Medical Center|Clinic|Urgent Care))?)",
            score=0.80
        ),
        # "admitted from Springfield" -> matches "Springfield" or "home"
        # Fixed-width lookbehind: "admitted from " = 14 chars
        Pattern(
            name="admitted_from",
            regex=r"(?i)(?<=admitted from )(home|(?-i:[A-Z])[a-z']*(?:\s+(?-i:[A-Z])[a-z']*)*(?:\s+(?:Hospital|Clinic))?)",
            score=0.80
        ),
        # "sent from Children's Hospital" -> matches "Children's Hospital"
        # Fixed-width lookbehind: "sent from " = 10 chars
        Pattern(
            name="sent_from",
            regex=r"(?i)(?<=sent from )(?-i:[A-Z])[a-z']*(?:\s+(?-i:[A-Z])[a-z']*)*(?:\s+(?:Hospital|Medical Center|Clinic))?",
            score=0.75
        ),
        # "came from Mass General" -> matches "Mass General"
        # Fixed-width lookbehind: "came from " = 10 chars
        Pattern(
            name="came_from",
            regex=r"(?i)(?<=came from )(?-i:[A-Z])[a-z']*(?:\s+(?-i:[A-Z])[a-z']*)*(?:\s+(?:Hospital|Medical Center))?",
            score=0.75
        ),
        # "en route from Boston" -> matches "Boston"
        # Fixed-width lookbehind: "en route from " = 14 chars
        Pattern(
            name="en_route_from",
            regex=r"(?i)(?<=en route from )(?-i:[A-Z])[a-z']*(?:\s+(?-i:[A-Z])[a-z']*)*",
            score=0.75
        ),

        # === FACILITY NAME PATTERNS (19% of dataset) ===
        # Detect medical facilities by explicit keywords (Hospital, Clinic, Medical Center)
        # NOTE: Presidio uses IGNORECASE by default, so we use (?-i:[A-Z]) to force
        # case-sensitive matching for capital letters. This prevents matching lowercase
        # words like "was", "from" etc. between the first word and the facility keyword.

        # "[Name] Hospital" -> matches entire phrase
        # Examples: "Memorial Hospital", "Children's Hospital"
        Pattern(
            name="hospital_name",
            regex=r"\b(?-i:[A-Z])[A-Za-z'\.]+(?:\s+(?-i:[A-Z])[A-Za-z'\.]+)*\s+Hospital\b",
            score=0.70
        ),
        # "[Name] Medical Center" -> matches entire phrase
        # Examples: "Boston Medical Center", "Children's Medical Center"
        Pattern(
            name="medical_center_name",
            regex=r"\b(?-i:[A-Z])[A-Za-z'\.]+(?:\s+(?-i:[A-Z])[A-Za-z'\.]+)*\s+Medical Center\b",
            score=0.70
        ),
        # "[Name] Clinic" -> matches entire phrase
        # Examples: "Springfield Clinic", "Oak Street Clinic"
        Pattern(
            name="clinic_name",
            regex=r"\b(?-i:[A-Z])[A-Za-z'\.]+(?:\s+(?-i:[A-Z])[A-Za-z'\.]+)*\s+Clinic\b",
            score=0.65
        ),
        # "[Name] Pediatrics" -> matches entire phrase
        # Examples: "Springfield Pediatrics", "Main Street Pediatrics"
        Pattern(
            name="pediatrics_office",
            regex=r"\b(?-i:[A-Z])[A-Za-z'\.]+(?:\s+(?-i:[A-Z])[A-Za-z'\.]+)*\s+Pediatrics\b",
            score=0.65
        ),
        # "[Name] Health System" / "[Name] Health Center" -> matches entire phrase
        Pattern(
            name="health_system",
            regex=r"\b(?-i:[A-Z])[A-Za-z'\.]+(?:\s+(?-i:[A-Z])[A-Za-z'\.]+)*\s+Health\s+(?:System|Center)\b",
            score=0.65
        ),
        # "Urgent Care" with name prefix -> matches entire phrase
        Pattern(
            name="urgent_care",
            regex=r"\b(?-i:[A-Z])[A-Za-z'\.]+(?:\s+(?-i:[A-Z])[A-Za-z'\.]+)*\s+Urgent Care\b",
            score=0.65
        ),

        # === RESIDENTIAL ADDRESS PATTERNS (16% of dataset) ===
        # Detect addresses in residential context (lives at, discharge to)
        # NOTE: Use (?-i:...) for case-sensitive capital letter requirements

        # "lives at 123 Main Street" -> matches "123 Main Street"
        # Fixed-width lookbehind: "lives at " = 9 chars
        # Covers common street type suffixes
        Pattern(
            name="lives_at_address",
            regex=r"(?i)(?<=lives at )\d+\s+(?-i:[A-Z])[A-Za-z'\s]+(?:Street|Drive|Avenue|Road|Lane|Way|Court|Place|Circle|Boulevard|Heights|Manor|Hill)\b(?:\s+(?:Apt|Suite|Unit)\.\s*\w+)?",
            score=0.75
        ),
        # "lives in Boston" -> matches "Boston"
        # Fixed-width lookbehind: "lives in " = 9 chars
        # Only matches capitalized words (stops at lowercase like "with")
        Pattern(
            name="lives_in_city",
            regex=r"(?i)(?<=lives in )(?-i:[A-Z])[a-z']*(?:\s+(?-i:[A-Z])[a-z']*)*",
            score=0.70
        ),
        # "discharge to home" or "discharge to 456 Oak Lane" -> matches location
        # Fixed-width lookbehind: "discharge to " = 13 chars
        Pattern(
            name="discharge_to",
            regex=r"(?i)(?<=discharge to )(?:home|(?-i:[A-Z])[A-Za-z0-9'\s]+(?:Street|Drive|Avenue|Road|Lane|Way|Court|Home)?)\b",
            score=0.70
        ),
        # "from [City]" with common city suffixes (ville, ton, port, etc.)
        # Helps detect city names that spaCy might miss
        # Fixed-width lookbehind: "from " = 5 chars
        Pattern(
            name="from_city",
            regex=r"(?i)(?<=from )(?-i:[A-Z])[a-z]+(?:ville|ton|burg|port|haven|chester|wood|field|land)\b",
            score=0.65
        ),

        # === PCP/CLINIC CONTEXT PATTERNS ===
        # "PCP is Dr. Smith at Springfield Pediatrics" -> matches "Springfield Pediatrics"
        # Fixed-width lookbehind: "at " = 3 chars (short, need facility keyword)
        Pattern(
            name="pcp_at_facility",
            regex=r"(?i)(?<=\bat )(?-i:[A-Z])[A-Za-z'\s]+(?:Pediatrics|Clinic|Associates|Medical)\b",
            score=0.60  # Lower score - indirect context
        ),
    ]

    location_recognizer = PatternRecognizer(
        supported_entity="LOCATION",
        name="Location Recognizer",
        patterns=location_patterns,
        context=[
            # Transfer context words (from 21-01)
            "transferred", "admitted", "sent", "came", "en route",
            # Medical facility keywords
            "hospital", "clinic", "medical center", "urgent care", "pediatrics",
            # Residential context
            "home", "lives", "discharge", "address", "family",
            # PCP context
            "pcp", "doctor", "office"
        ]
    )
    recognizers.append(location_recognizer)

    return recognizers
