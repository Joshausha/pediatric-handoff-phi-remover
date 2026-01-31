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
        # Possessive patterns: "his mom Sarah", "her dad Tom" (score 0.85)
        # Using lookbehind to match ONLY the name
        # =================================================================

        # --- his + relationship (3 + space + relationship + space) ---
        # "his mom " = 8 chars
        Pattern(name="his_mom_name", regex=r"(?i)(?<=his mom )[a-z][a-z]+\b", score=0.85),
        # "his mother " = 11 chars
        Pattern(name="his_mother_name", regex=r"(?i)(?<=his mother )[a-z][a-z]+\b", score=0.85),
        # "his mommy " = 10 chars
        Pattern(name="his_mommy_name", regex=r"(?i)(?<=his mommy )[a-z][a-z]+\b", score=0.85),
        # "his dad " = 8 chars
        Pattern(name="his_dad_name", regex=r"(?i)(?<=his dad )[a-z][a-z]+\b", score=0.85),
        # "his father " = 11 chars
        Pattern(name="his_father_name", regex=r"(?i)(?<=his father )[a-z][a-z]+\b", score=0.85),
        # "his daddy " = 10 chars
        Pattern(name="his_daddy_name", regex=r"(?i)(?<=his daddy )[a-z][a-z]+\b", score=0.85),
        # "his grandma " = 12 chars
        Pattern(name="his_grandma_name", regex=r"(?i)(?<=his grandma )[a-z][a-z]+\b", score=0.85),
        # "his grandmother " = 16 chars
        Pattern(name="his_grandmother_name", regex=r"(?i)(?<=his grandmother )[a-z][a-z]+\b", score=0.85),
        # "his grandpa " = 12 chars
        Pattern(name="his_grandpa_name", regex=r"(?i)(?<=his grandpa )[a-z][a-z]+\b", score=0.85),
        # "his grandfather " = 16 chars
        Pattern(name="his_grandfather_name", regex=r"(?i)(?<=his grandfather )[a-z][a-z]+\b", score=0.85),
        # "his nana " = 9 chars
        Pattern(name="his_nana_name", regex=r"(?i)(?<=his nana )[a-z][a-z]+\b", score=0.85),
        # "his papa " = 9 chars
        Pattern(name="his_papa_name", regex=r"(?i)(?<=his papa )[a-z][a-z]+\b", score=0.85),
        # "his granny " = 11 chars
        Pattern(name="his_granny_name", regex=r"(?i)(?<=his granny )[a-z][a-z]+\b", score=0.85),
        # "his aunt " = 9 chars
        Pattern(name="his_aunt_name", regex=r"(?i)(?<=his aunt )[a-z][a-z]+\b", score=0.85),
        # "his auntie " = 11 chars
        Pattern(name="his_auntie_name", regex=r"(?i)(?<=his auntie )[a-z][a-z]+\b", score=0.85),
        # "his uncle " = 10 chars
        Pattern(name="his_uncle_name", regex=r"(?i)(?<=his uncle )[a-z][a-z]+\b", score=0.85),
        # "his guardian " = 13 chars
        Pattern(name="his_guardian_name", regex=r"(?i)(?<=his guardian )[a-z][a-z]+\b", score=0.85),

        # --- her + relationship (3 + space + relationship + space) ---
        # "her mom " = 8 chars
        Pattern(name="her_mom_name", regex=r"(?i)(?<=her mom )[a-z][a-z]+\b", score=0.85),
        # "her mother " = 11 chars
        Pattern(name="her_mother_name", regex=r"(?i)(?<=her mother )[a-z][a-z]+\b", score=0.85),
        # "her mommy " = 10 chars
        Pattern(name="her_mommy_name", regex=r"(?i)(?<=her mommy )[a-z][a-z]+\b", score=0.85),
        # "her dad " = 8 chars
        Pattern(name="her_dad_name", regex=r"(?i)(?<=her dad )[a-z][a-z]+\b", score=0.85),
        # "her father " = 11 chars
        Pattern(name="her_father_name", regex=r"(?i)(?<=her father )[a-z][a-z]+\b", score=0.85),
        # "her daddy " = 10 chars
        Pattern(name="her_daddy_name", regex=r"(?i)(?<=her daddy )[a-z][a-z]+\b", score=0.85),
        # "her grandma " = 12 chars
        Pattern(name="her_grandma_name", regex=r"(?i)(?<=her grandma )[a-z][a-z]+\b", score=0.85),
        # "her grandmother " = 16 chars
        Pattern(name="her_grandmother_name", regex=r"(?i)(?<=her grandmother )[a-z][a-z]+\b", score=0.85),
        # "her grandpa " = 12 chars
        Pattern(name="her_grandpa_name", regex=r"(?i)(?<=her grandpa )[a-z][a-z]+\b", score=0.85),
        # "her grandfather " = 16 chars
        Pattern(name="her_grandfather_name", regex=r"(?i)(?<=her grandfather )[a-z][a-z]+\b", score=0.85),
        # "her nana " = 9 chars
        Pattern(name="her_nana_name", regex=r"(?i)(?<=her nana )[a-z][a-z]+\b", score=0.85),
        # "her papa " = 9 chars
        Pattern(name="her_papa_name", regex=r"(?i)(?<=her papa )[a-z][a-z]+\b", score=0.85),
        # "her granny " = 11 chars
        Pattern(name="her_granny_name", regex=r"(?i)(?<=her granny )[a-z][a-z]+\b", score=0.85),
        # "her aunt " = 9 chars
        Pattern(name="her_aunt_name", regex=r"(?i)(?<=her aunt )[a-z][a-z]+\b", score=0.85),
        # "her auntie " = 11 chars
        Pattern(name="her_auntie_name", regex=r"(?i)(?<=her auntie )[a-z][a-z]+\b", score=0.85),
        # "her uncle " = 10 chars
        Pattern(name="her_uncle_name", regex=r"(?i)(?<=her uncle )[a-z][a-z]+\b", score=0.85),
        # "her guardian " = 13 chars
        Pattern(name="her_guardian_name", regex=r"(?i)(?<=her guardian )[a-z][a-z]+\b", score=0.85),

        # --- their + relationship (5 + space + relationship + space) ---
        # "their mom " = 10 chars
        Pattern(name="their_mom_name", regex=r"(?i)(?<=their mom )[a-z][a-z]+\b", score=0.85),
        # "their mother " = 13 chars
        Pattern(name="their_mother_name", regex=r"(?i)(?<=their mother )[a-z][a-z]+\b", score=0.85),
        # "their mommy " = 12 chars
        Pattern(name="their_mommy_name", regex=r"(?i)(?<=their mommy )[a-z][a-z]+\b", score=0.85),
        # "their dad " = 10 chars
        Pattern(name="their_dad_name", regex=r"(?i)(?<=their dad )[a-z][a-z]+\b", score=0.85),
        # "their father " = 13 chars
        Pattern(name="their_father_name", regex=r"(?i)(?<=their father )[a-z][a-z]+\b", score=0.85),
        # "their daddy " = 12 chars
        Pattern(name="their_daddy_name", regex=r"(?i)(?<=their daddy )[a-z][a-z]+\b", score=0.85),
        # "their grandma " = 14 chars
        Pattern(name="their_grandma_name", regex=r"(?i)(?<=their grandma )[a-z][a-z]+\b", score=0.85),
        # "their grandmother " = 18 chars
        Pattern(name="their_grandmother_name", regex=r"(?i)(?<=their grandmother )[a-z][a-z]+\b", score=0.85),
        # "their grandpa " = 14 chars
        Pattern(name="their_grandpa_name", regex=r"(?i)(?<=their grandpa )[a-z][a-z]+\b", score=0.85),
        # "their grandfather " = 18 chars
        Pattern(name="their_grandfather_name", regex=r"(?i)(?<=their grandfather )[a-z][a-z]+\b", score=0.85),
        # "their nana " = 11 chars
        Pattern(name="their_nana_name", regex=r"(?i)(?<=their nana )[a-z][a-z]+\b", score=0.85),
        # "their papa " = 11 chars
        Pattern(name="their_papa_name", regex=r"(?i)(?<=their papa )[a-z][a-z]+\b", score=0.85),
        # "their granny " = 13 chars
        Pattern(name="their_granny_name", regex=r"(?i)(?<=their granny )[a-z][a-z]+\b", score=0.85),
        # "their aunt " = 11 chars
        Pattern(name="their_aunt_name", regex=r"(?i)(?<=their aunt )[a-z][a-z]+\b", score=0.85),
        # "their auntie " = 13 chars
        Pattern(name="their_auntie_name", regex=r"(?i)(?<=their auntie )[a-z][a-z]+\b", score=0.85),
        # "their uncle " = 12 chars
        Pattern(name="their_uncle_name", regex=r"(?i)(?<=their uncle )[a-z][a-z]+\b", score=0.85),
        # "their guardian " = 15 chars
        Pattern(name="their_guardian_name", regex=r"(?i)(?<=their guardian )[a-z][a-z]+\b", score=0.85),

        # --- patient's + relationship ---
        # "patient's mom " = 14 chars
        Pattern(name="patients_mom_name", regex=r"(?i)(?<=patient's mom )[a-z][a-z]+\b", score=0.85),
        # "patient's dad " = 14 chars
        Pattern(name="patients_dad_name", regex=r"(?i)(?<=patient's dad )[a-z][a-z]+\b", score=0.85),
        # "patient's mother " = 17 chars
        Pattern(name="patients_mother_name", regex=r"(?i)(?<=patient's mother )[a-z][a-z]+\b", score=0.85),
        # "patient's father " = 17 chars
        Pattern(name="patients_father_name", regex=r"(?i)(?<=patient's father )[a-z][a-z]+\b", score=0.85),
        # "patient's guardian " = 19 chars
        Pattern(name="patients_guardian_name", regex=r"(?i)(?<=patient's guardian )[a-z][a-z]+\b", score=0.85),

        # --- baby's + relationship ---
        # "baby's mom " = 11 chars
        Pattern(name="babys_mom_name", regex=r"(?i)(?<=baby's mom )[a-z][a-z]+\b", score=0.85),
        # "baby's dad " = 11 chars
        Pattern(name="babys_dad_name", regex=r"(?i)(?<=baby's dad )[a-z][a-z]+\b", score=0.85),

        # --- child's + relationship ---
        # "child's mom " = 12 chars
        Pattern(name="childs_mom_name", regex=r"(?i)(?<=child's mom )[a-z][a-z]+\b", score=0.85),
        # "child's dad " = 12 chars
        Pattern(name="childs_dad_name", regex=r"(?i)(?<=child's dad )[a-z][a-z]+\b", score=0.85),

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

        # =================================================================
        # Appositive patterns: "mom, Jessica", "dad - Mike" (score 0.85)
        # Punctuation sets off the name from relationship word
        # =================================================================

        # --- Comma appositives: "relationship, name" ---
        # "mom, " = 5 chars
        Pattern(name="mom_comma_name", regex=r"(?i)(?<=mom, )[a-z][a-z]+\b", score=0.85),
        # "mother, " = 8 chars
        Pattern(name="mother_comma_name", regex=r"(?i)(?<=mother, )[a-z][a-z]+\b", score=0.85),
        # "mommy, " = 7 chars
        Pattern(name="mommy_comma_name", regex=r"(?i)(?<=mommy, )[a-z][a-z]+\b", score=0.85),
        # "dad, " = 5 chars
        Pattern(name="dad_comma_name", regex=r"(?i)(?<=dad, )[a-z][a-z]+\b", score=0.85),
        # "father, " = 8 chars
        Pattern(name="father_comma_name", regex=r"(?i)(?<=father, )[a-z][a-z]+\b", score=0.85),
        # "daddy, " = 7 chars
        Pattern(name="daddy_comma_name", regex=r"(?i)(?<=daddy, )[a-z][a-z]+\b", score=0.85),
        # "grandma, " = 9 chars
        Pattern(name="grandma_comma_name", regex=r"(?i)(?<=grandma, )[a-z][a-z]+\b", score=0.85),
        # "grandmother, " = 13 chars
        Pattern(name="grandmother_comma_name", regex=r"(?i)(?<=grandmother, )[a-z][a-z]+\b", score=0.85),
        # "grandpa, " = 9 chars
        Pattern(name="grandpa_comma_name", regex=r"(?i)(?<=grandpa, )[a-z][a-z]+\b", score=0.85),
        # "grandfather, " = 13 chars
        Pattern(name="grandfather_comma_name", regex=r"(?i)(?<=grandfather, )[a-z][a-z]+\b", score=0.85),
        # "nana, " = 6 chars
        Pattern(name="nana_comma_name", regex=r"(?i)(?<=nana, )[a-z][a-z]+\b", score=0.85),
        # "papa, " = 6 chars
        Pattern(name="papa_comma_name", regex=r"(?i)(?<=papa, )[a-z][a-z]+\b", score=0.85),
        # "granny, " = 8 chars
        Pattern(name="granny_comma_name", regex=r"(?i)(?<=granny, )[a-z][a-z]+\b", score=0.85),
        # "aunt, " = 6 chars
        Pattern(name="aunt_comma_name", regex=r"(?i)(?<=aunt, )[a-z][a-z]+\b", score=0.85),
        # "auntie, " = 8 chars
        Pattern(name="auntie_comma_name", regex=r"(?i)(?<=auntie, )[a-z][a-z]+\b", score=0.85),
        # "uncle, " = 7 chars
        Pattern(name="uncle_comma_name", regex=r"(?i)(?<=uncle, )[a-z][a-z]+\b", score=0.85),
        # "guardian, " = 10 chars
        Pattern(name="guardian_comma_name", regex=r"(?i)(?<=guardian, )[a-z][a-z]+\b", score=0.85),

        # --- Dash appositives: "relationship - name" ---
        # "mom - " = 6 chars (space + dash + space)
        Pattern(name="mom_dash_name", regex=r"(?i)(?<=mom - )[a-z][a-z]+\b", score=0.85),
        # "mother - " = 9 chars
        Pattern(name="mother_dash_name", regex=r"(?i)(?<=mother - )[a-z][a-z]+\b", score=0.85),
        # "dad - " = 6 chars
        Pattern(name="dad_dash_name", regex=r"(?i)(?<=dad - )[a-z][a-z]+\b", score=0.85),
        # "father - " = 9 chars
        Pattern(name="father_dash_name", regex=r"(?i)(?<=father - )[a-z][a-z]+\b", score=0.85),
        # "grandma - " = 10 chars
        Pattern(name="grandma_dash_name", regex=r"(?i)(?<=grandma - )[a-z][a-z]+\b", score=0.85),
        # "grandpa - " = 10 chars
        Pattern(name="grandpa_dash_name", regex=r"(?i)(?<=grandpa - )[a-z][a-z]+\b", score=0.85),
        # "guardian - " = 11 chars
        Pattern(name="guardian_dash_name", regex=r"(?i)(?<=guardian - )[a-z][a-z]+\b", score=0.85),

        # --- Parenthesis appositives: "relationship (name)" ---
        # Note: escape the parenthesis in lookbehind
        # "mom (" = 5 chars
        Pattern(name="mom_paren_name", regex=r"(?i)(?<=mom \()[a-z][a-z]+\b", score=0.85),
        # "mother (" = 8 chars
        Pattern(name="mother_paren_name", regex=r"(?i)(?<=mother \()[a-z][a-z]+\b", score=0.85),
        # "dad (" = 5 chars
        Pattern(name="dad_paren_name", regex=r"(?i)(?<=dad \()[a-z][a-z]+\b", score=0.85),
        # "father (" = 8 chars
        Pattern(name="father_paren_name", regex=r"(?i)(?<=father \()[a-z][a-z]+\b", score=0.85),
        # "grandma (" = 9 chars
        Pattern(name="grandma_paren_name", regex=r"(?i)(?<=grandma \()[a-z][a-z]+\b", score=0.85),
        # "grandpa (" = 9 chars
        Pattern(name="grandpa_paren_name", regex=r"(?i)(?<=grandpa \()[a-z][a-z]+\b", score=0.85),
        # "guardian (" = 10 chars
        Pattern(name="guardian_paren_name", regex=r"(?i)(?<=guardian \()[a-z][a-z]+\b", score=0.85),
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
    # PEDIATRIC_AGE Recognizer - DISABLED (2026-01-24)
    # =========================================================================
    # Rationale: Ages are NOT PHI under HIPAA (unless 90+).
    # Ages preserved for clinical utility per project decision.
    # See: .planning/phases/04-pattern-improvements/04-03-SUMMARY.md
    #
    # Original recognizer would have redacted patterns like:
    # - "3 weeks 2 days old"
    # - "32 weeker" (gestational age)
    # - "5 day old"
    #
    # These are clinically important information that:
    # 1. Are NOT identifying under HIPAA (only ages 90+ are PHI)
    # 2. Are critical for pediatric clinical handoffs
    # 3. Had only 35.8% recall anyway (lowest of all entities)
    #
    # Decision made in Phase 4 Plan 03 after user review of options.
    # =========================================================================

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
