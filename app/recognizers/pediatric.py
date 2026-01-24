"""
Pediatric-specific Presidio recognizers.

Critical for pediatric handoffs where standard NER misses context-specific PHI:
- Guardian names ("Mom Jessica", "Dad Mike")
- Detailed pediatric ages ("3 weeks 2 days old")
- School/daycare names

Pattern Design Notes (Phase 4 improvements):
- All patterns use (?i) for case-insensitive matching (catches "mom jessica", "MOM JESSICA")
- Lookbehind patterns match ONLY the name (not the relationship word) so "Mom" is preserved
- Lookahead patterns for bidirectional catch "Jessica is Mom" (match only "Jessica")
- Speech artifact patterns handle "um", "uh" filler words between relationship word and name
"""


from presidio_analyzer import Pattern, PatternRecognizer


def get_pediatric_recognizers() -> list[PatternRecognizer]:
    """
    Create pediatric-specific PHI recognizers.

    These catch PHI patterns that standard NER models miss in pediatric context.

    Returns:
        List of PatternRecognizer instances
    """
    recognizers = []

    # =========================================================================
    # Guardian Relationship Recognizer (CRITICAL for pediatrics)
    # =========================================================================
    # In pediatrics, we say "Mom Jessica is at bedside" - standard NER misses
    # that "Jessica" is PHI because of the relationship context.
    #
    # Pattern strategy:
    # 1. Case-insensitive (?i) catches "mom jessica", "Mom Jessica", "MOM JESSICA"
    # 2. Lookbehind (?<=) matches ONLY the name - preserves "Mom", "Dad", etc.
    # 3. Lookahead (?=) for bidirectional patterns - "Jessica is Mom"
    # 4. Fixed-width lookbehind for speech artifacts - "mom uh Jessica"
    #
    # Note: Lookbehind requires fixed width, so we use separate patterns for
    # different relationship word lengths and filler combinations.
    guardian_patterns = [
        # =================================================================
        # Forward patterns: "Mom Jessica", "dad mike", etc. (score 0.85)
        # Using lookbehind to match ONLY the name
        # =================================================================
        # Mom (3 chars + space = 4 char lookbehind)
        Pattern(
            name="mom_name",
            regex=r"(?i)(?<=mom )[a-z][a-z]+\b",
            score=0.85
        ),
        # Mother (6 chars + space = 7 char lookbehind)
        Pattern(
            name="mother_name",
            regex=r"(?i)(?<=mother )[a-z][a-z]+\b",
            score=0.85
        ),
        # Mommy (5 chars + space = 6 char lookbehind)
        Pattern(
            name="mommy_name",
            regex=r"(?i)(?<=mommy )[a-z][a-z]+\b",
            score=0.85
        ),
        # Dad (3 chars + space = 4 char lookbehind)
        Pattern(
            name="dad_name",
            regex=r"(?i)(?<=dad )[a-z][a-z]+\b",
            score=0.85
        ),
        # Father (6 chars + space = 7 char lookbehind)
        Pattern(
            name="father_name",
            regex=r"(?i)(?<=father )[a-z][a-z]+\b",
            score=0.85
        ),
        # Daddy (5 chars + space = 6 char lookbehind)
        Pattern(
            name="daddy_name",
            regex=r"(?i)(?<=daddy )[a-z][a-z]+\b",
            score=0.85
        ),
        # Grandparents
        Pattern(
            name="grandma_name",
            regex=r"(?i)(?<=grandma )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="grandmother_name",
            regex=r"(?i)(?<=grandmother )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="grandpa_name",
            regex=r"(?i)(?<=grandpa )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="grandfather_name",
            regex=r"(?i)(?<=grandfather )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="nana_name",
            regex=r"(?i)(?<=nana )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="papa_name",
            regex=r"(?i)(?<=papa )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="granny_name",
            regex=r"(?i)(?<=granny )[a-z][a-z]+\b",
            score=0.85
        ),
        # Aunt/Uncle
        Pattern(
            name="aunt_name",
            regex=r"(?i)(?<=aunt )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="auntie_name",
            regex=r"(?i)(?<=auntie )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="uncle_name",
            regex=r"(?i)(?<=uncle )[a-z][a-z]+\b",
            score=0.85
        ),
        # Step-parents
        Pattern(
            name="stepmom_name",
            regex=r"(?i)(?<=stepmom )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="stepdad_name",
            regex=r"(?i)(?<=stepdad )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="stepmother_name",
            regex=r"(?i)(?<=stepmother )[a-z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="stepfather_name",
            regex=r"(?i)(?<=stepfather )[a-z][a-z]+\b",
            score=0.85
        ),
        # Generic guardian
        Pattern(
            name="guardian_name",
            regex=r"(?i)(?<=guardian )[a-z][a-z]+\b",
            score=0.80
        ),

        # =================================================================
        # Bidirectional patterns: "Jessica is Mom" (score 0.80)
        # Using lookahead to match ONLY the name before "is [relationship]"
        # =================================================================
        Pattern(
            name="is_mom_bidirectional",
            regex=r"(?i)\b[a-z][a-z]+(?= is (?:mom|mother|mommy)\b)",
            score=0.80
        ),
        Pattern(
            name="is_dad_bidirectional",
            regex=r"(?i)\b[a-z][a-z]+(?= is (?:dad|father|daddy)\b)",
            score=0.80
        ),
        Pattern(
            name="is_grandparent_bidirectional",
            regex=r"(?i)\b[a-z][a-z]+(?= is (?:grandma|grandmother|grandpa|grandfather|nana|papa|granny)\b)",
            score=0.80
        ),
        Pattern(
            name="is_relative_bidirectional",
            regex=r"(?i)\b[a-z][a-z]+(?= is (?:aunt|auntie|uncle|guardian)\b)",
            score=0.80
        ),

        # =================================================================
        # Speech artifact patterns: "mom uh Jessica", "mom um Jessica" (score 0.75)
        # Using fixed-width lookbehind (relationship word + space + filler + space)
        # =================================================================
        # "mom uh " = 7 chars
        Pattern(
            name="mom_uh_name",
            regex=r"(?i)(?<=mom uh )[a-z][a-z]+\b",
            score=0.75
        ),
        # "mom um " = 7 chars
        Pattern(
            name="mom_um_name",
            regex=r"(?i)(?<=mom um )[a-z][a-z]+\b",
            score=0.75
        ),
        # "dad uh " = 7 chars
        Pattern(
            name="dad_uh_name",
            regex=r"(?i)(?<=dad uh )[a-z][a-z]+\b",
            score=0.75
        ),
        # "dad um " = 7 chars
        Pattern(
            name="dad_um_name",
            regex=r"(?i)(?<=dad um )[a-z][a-z]+\b",
            score=0.75
        ),
        # Repetition: "mom mom " = 8 chars
        Pattern(
            name="mom_mom_name",
            regex=r"(?i)(?<=mom mom )[a-z][a-z]+\b",
            score=0.75
        ),
        # "dad dad " = 8 chars
        Pattern(
            name="dad_dad_name",
            regex=r"(?i)(?<=dad dad )[a-z][a-z]+\b",
            score=0.75
        ),
    ]

    guardian_recognizer = PatternRecognizer(
        supported_entity="GUARDIAN_NAME",
        name="Guardian Name Recognizer",
        patterns=guardian_patterns,
        context=["parent", "guardian", "family", "caregiver", "at bedside", "reached at", "contact"]
    )
    recognizers.append(guardian_recognizer)

    # =========================================================================
    # Baby/Infant Name Recognizer
    # =========================================================================
    # Common pediatric pattern: "Baby Smith", "Infant Jones"
    # Using case-insensitive lookbehind to match ONLY the last name
    baby_name_patterns = [
        # "baby " = 5 chars
        Pattern(
            name="baby_lastname",
            regex=r"(?i)(?<=baby )[a-z][a-z]+\b",
            score=0.85
        ),
        # "infant " = 7 chars
        Pattern(
            name="infant_lastname",
            regex=r"(?i)(?<=infant )[a-z][a-z]+\b",
            score=0.85
        ),
        # "newborn " = 8 chars
        Pattern(
            name="newborn_lastname",
            regex=r"(?i)(?<=newborn )[a-z][a-z]+\b",
            score=0.85
        ),
        # "baby boy " = 9 chars
        Pattern(
            name="baby_boy_lastname",
            regex=r"(?i)(?<=baby boy )[a-z][a-z]+\b",
            score=0.85
        ),
        # "baby girl " = 10 chars
        Pattern(
            name="baby_girl_lastname",
            regex=r"(?i)(?<=baby girl )[a-z][a-z]+\b",
            score=0.85
        ),
    ]

    baby_name_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        name="Baby Name Recognizer",
        patterns=baby_name_patterns,
        context=["baby", "infant", "newborn", "neonate", "NICU", "nursery"]
    )
    recognizers.append(baby_name_recognizer)

    # =========================================================================
    # Pediatric Age Detail Recognizer
    # =========================================================================
    # Very specific ages like "3 weeks 2 days old" can be identifying for
    # rare conditions, especially when combined with other information.
    age_patterns = [
        # Days old: "5 day old", "3-day-old"
        Pattern(
            name="age_days",
            regex=r"\b(\d{1,3})[\s-]?(?:day|d)[\s-]?(?:s)?[\s-]?old\b",
            score=0.5
        ),
        # Weeks old: "3 week old"
        Pattern(
            name="age_weeks",
            regex=r"\b(\d{1,2})[\s-]?(?:week|wk)[\s-]?(?:s)?[\s-]?old\b",
            score=0.5
        ),
        # Weeks + days: "3 weeks 2 days old"
        Pattern(
            name="age_weeks_days",
            regex=r"\b(\d{1,2})\s*(?:weeks?|wks?)\s*(?:and\s*)?(\d{1,2})\s*(?:days?|d)\s*old\b",
            score=0.6
        ),
        # Months + days: "2 months 5 days"
        Pattern(
            name="age_months_days",
            regex=r"\b(\d{1,2})\s*(?:months?|mo)\s*(?:and\s*)?(\d{1,2})\s*(?:days?|d)(?:\s*old)?\b",
            score=0.55
        ),
        # Gestational age: "28 week gestation", "32 weeker"
        Pattern(
            name="gestational_age",
            regex=r"\b(\d{2})[\s-]?(?:week|wk)(?:er|s)?(?:\s+(?:gestation|gestational|GA))?\b",
            score=0.5
        ),
        # Corrected gestational age
        Pattern(
            name="corrected_age",
            regex=r"\b(?:corrected|adjusted)[\s-]?(?:gestational)?[\s-]?age[\s:]+(\d{1,2})\s*(?:weeks?|months?)\b",
            score=0.6
        ),
    ]

    age_recognizer = PatternRecognizer(
        supported_entity="PEDIATRIC_AGE",
        name="Pediatric Age Recognizer",
        patterns=age_patterns,
        context=["born", "premature", "preterm", "neonate", "infant", "baby", "delivery"]
    )
    recognizers.append(age_recognizer)

    # =========================================================================
    # School/Daycare Recognizer
    # =========================================================================
    # School names can identify patients, especially with other context
    school_patterns = [
        # Elementary/Middle/High School
        Pattern(
            name="school_name",
            regex=r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:Elementary|Middle|High|Primary|Secondary)\s+(?:School)?\b",
            score=0.6
        ),
        # Daycare/Preschool
        Pattern(
            name="daycare_name",
            regex=r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:Daycare|Day\s+Care|Preschool|Pre-school|Nursery)\b",
            score=0.6
        ),
        # "goes to [School]", "attends [School]"
        Pattern(
            name="attends_school",
            regex=r"\b(?:goes\s+to|attends|enrolled\s+at)\s+([A-Z][A-Za-z\s]+?)(?:\s+(?:school|daycare|preschool))?\b",
            score=0.55
        ),
    ]

    school_recognizer = PatternRecognizer(
        supported_entity="LOCATION",  # Map to LOCATION entity
        name="School Name Recognizer",
        patterns=school_patterns,
        context=["school", "daycare", "attends", "enrolled", "student", "teacher", "nurse"]
    )
    recognizers.append(school_recognizer)

    return recognizers
