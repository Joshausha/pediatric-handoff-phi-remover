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
    guardian_patterns = [
        # Mom/Mother + Name
        Pattern(
            name="mom_name",
            regex=r"\b(?:Mom|Mother|Mommy|Mama)\s+([A-Z][a-z]+)\b",
            score=0.85
        ),
        # Dad/Father + Name
        Pattern(
            name="dad_name",
            regex=r"\b(?:Dad|Father|Daddy|Papa)\s+([A-Z][a-z]+)\b",
            score=0.85
        ),
        # Grandparents
        Pattern(
            name="grandparent_name",
            regex=r"\b(?:Grandma|Grandmother|Grammy|Nana|Grandpa|Grandfather|Papa|Gramps)\s+([A-Z][a-z]+)\b",
            score=0.85
        ),
        # Aunt/Uncle
        Pattern(
            name="aunt_uncle_name",
            regex=r"\b(?:Aunt|Auntie|Uncle)\s+([A-Z][a-z]+)\b",
            score=0.85
        ),
        # Step-parents
        Pattern(
            name="step_parent_name",
            regex=r"\b(?:Stepmom|Stepmother|Stepdad|Stepfather)\s+([A-Z][a-z]+)\b",
            score=0.85
        ),
        # Foster parents
        Pattern(
            name="foster_parent_name",
            regex=r"\b(?:Foster\s+(?:mom|mother|dad|father|parent))\s+([A-Z][a-z]+)\b",
            score=0.85
        ),
        # Generic guardian
        Pattern(
            name="guardian_name",
            regex=r"\b(?:Guardian|Caregiver|Caretaker)\s+([A-Z][a-z]+)\b",
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
