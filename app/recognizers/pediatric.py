"""
Pediatric-specific Presidio recognizers.

Critical for pediatric handoffs where standard NER misses context-specific PHI:
- Guardian names ("Mom Jessica", "Dad Mike")
- Detailed pediatric ages ("3 weeks 2 days old")
- School/daycare names
"""

from typing import List
from presidio_analyzer import PatternRecognizer, Pattern


def get_pediatric_recognizers() -> List[PatternRecognizer]:
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
    # IMPORTANT: Using lookbehind assertions so only the NAME gets replaced,
    # preserving the relationship word (Mom, Dad, etc.)
    guardian_patterns = [
        # Mom/Mother + Name (using lookbehind to preserve "Mom")
        Pattern(
            name="mom_name",
            regex=r"(?<=Mom )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="mother_name",
            regex=r"(?<=Mother )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="mommy_name",
            regex=r"(?<=Mommy )[A-Z][a-z]+\b",
            score=0.85
        ),
        # Dad/Father + Name
        Pattern(
            name="dad_name",
            regex=r"(?<=Dad )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="father_name",
            regex=r"(?<=Father )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="daddy_name",
            regex=r"(?<=Daddy )[A-Z][a-z]+\b",
            score=0.85
        ),
        # Grandparents
        Pattern(
            name="grandma_name",
            regex=r"(?<=Grandma )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="grandpa_name",
            regex=r"(?<=Grandpa )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="nana_name",
            regex=r"(?<=Nana )[A-Z][a-z]+\b",
            score=0.85
        ),
        # Aunt/Uncle
        Pattern(
            name="aunt_name",
            regex=r"(?<=Aunt )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="uncle_name",
            regex=r"(?<=Uncle )[A-Z][a-z]+\b",
            score=0.85
        ),
        # Step-parents
        Pattern(
            name="stepmom_name",
            regex=r"(?<=Stepmom )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="stepdad_name",
            regex=r"(?<=Stepdad )[A-Z][a-z]+\b",
            score=0.85
        ),
        # Generic guardian
        Pattern(
            name="guardian_name",
            regex=r"(?<=Guardian )[A-Z][a-z]+\b",
            score=0.80
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
    baby_name_patterns = [
        Pattern(
            name="baby_lastname",
            regex=r"(?<=Baby )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="infant_lastname",
            regex=r"(?<=Infant )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="newborn_lastname",
            regex=r"(?<=Newborn )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="baby_boy_lastname",
            regex=r"(?<=Baby Boy )[A-Z][a-z]+\b",
            score=0.85
        ),
        Pattern(
            name="baby_girl_lastname",
            regex=r"(?<=Baby Girl )[A-Z][a-z]+\b",
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
