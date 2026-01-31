"""
Provider name recognizers for clinical handoffs.

Detects provider names in common clinical patterns:
- Title-prefixed: "Dr. Smith", "NP Johnson", "PA Williams"
- Title-suffixed: "Smith MD", "Jones RN"

Pattern Design Notes (Phase 19):
- Lookbehind patterns match ONLY the name (not the title) so "Dr." is preserved
- Lookahead patterns for suffix forms match ONLY the name before title
- All patterns require [A-Z][a-z]+ to prevent matching verbs like "is", "at"
- Score 0.85 for title-prefixed (common in speech), 0.80 for title-suffixed (less common)
- CRITICAL: Presidio applies IGNORECASE by default, so we use (?-i:...) inline flag
  to make the name portion case-sensitive (requires uppercase first letter)
"""

from presidio_analyzer import Pattern, PatternRecognizer


def get_provider_recognizers() -> list[PatternRecognizer]:
    """
    Create provider-specific PHI recognizers.

    These catch provider names that are PHI in clinical handoffs.

    Returns:
        List of PatternRecognizer instances
    """
    recognizers = []

    # =========================================================================
    # Provider Name Recognizer
    # =========================================================================
    # In clinical handoffs, provider names like "Dr. Smith" are PHI.
    # We use lookbehind/lookahead to match ONLY the name, preserving the title.
    #
    # Pattern strategy:
    # 1. Lookbehind (?<=) matches ONLY the name - preserves "Dr.", "NP", etc.
    # 2. Lookahead (?=) for suffix patterns - "Smith MD" matches "Smith"
    # 3. All patterns use (?-i:[A-Z][a-z]+) to require uppercase first letter
    #    (Presidio applies IGNORECASE by default, so we override with inline flag)
    # 4. Title-prefixed patterns score 0.85 (very common in speech)
    # 5. Title-suffixed patterns score 0.80 (less common in speech)

    provider_patterns = [
        # =================================================================
        # Title-prefixed patterns (score 0.85) - most common in speech
        # Using lookbehind to match ONLY the name
        # =================================================================

        # "Dr. " (4 chars: D-r-.-space)
        Pattern(
            name="dr_period_name",
            regex=r"(?<=Dr\. )(?-i:[A-Z][a-z]+)\b",
            score=0.85
        ),
        # "Dr " (3 chars: D-r-space, no period)
        Pattern(
            name="dr_name",
            regex=r"(?<=Dr )(?-i:[A-Z][a-z]+)\b",
            score=0.85
        ),
        # "Doctor " (7 chars)
        Pattern(
            name="doctor_name",
            regex=r"(?<=Doctor )(?-i:[A-Z][a-z]+)\b",
            score=0.85
        ),
        # "NP " (3 chars: nurse practitioner)
        Pattern(
            name="np_name",
            regex=r"(?<=NP )(?-i:[A-Z][a-z]+)\b",
            score=0.85
        ),
        # "PA " (3 chars: physician assistant)
        Pattern(
            name="pa_name",
            regex=r"(?<=PA )(?-i:[A-Z][a-z]+)\b",
            score=0.85
        ),
        # "RN " (3 chars: registered nurse)
        Pattern(
            name="rn_name",
            regex=r"(?<=RN )(?-i:[A-Z][a-z]+)\b",
            score=0.85
        ),
        # "Nurse " (6 chars)
        Pattern(
            name="nurse_name",
            regex=r"(?<=Nurse )(?-i:[A-Z][a-z]+)\b",
            score=0.85
        ),

        # =================================================================
        # Title-suffixed patterns (score 0.80) - less common in speech
        # Using lookahead to match ONLY the name before title
        # =================================================================

        # " MD" suffix - match name before " MD"
        Pattern(
            name="name_md",
            regex=r"\b(?-i:[A-Z][a-z]+)(?= MD\b)",
            score=0.80
        ),
        # " RN" suffix - match name before " RN" (as suffix)
        Pattern(
            name="name_rn_suffix",
            regex=r"\b(?-i:[A-Z][a-z]+)(?= RN\b)",
            score=0.80
        ),
        # " NP" suffix - match name before " NP" (as suffix)
        Pattern(
            name="name_np_suffix",
            regex=r"\b(?-i:[A-Z][a-z]+)(?= NP\b)",
            score=0.80
        ),
        # " PA" suffix - match name before " PA" (as suffix)
        Pattern(
            name="name_pa_suffix",
            regex=r"\b(?-i:[A-Z][a-z]+)(?= PA\b)",
            score=0.80
        ),
    ]

    provider_recognizer = PatternRecognizer(
        supported_entity="PROVIDER_NAME",
        name="Provider Name Recognizer",
        patterns=provider_patterns,
        context=[
            "doctor", "physician", "attending", "fellow", "resident",
            "nurse", "Dr", "NP", "PA", "RN", "primary", "consult"
        ]
    )
    recognizers.append(provider_recognizer)

    return recognizers
