# Phase 19: Provider Name Detection - Research

**Researched:** 2026-01-30
**Domain:** Presidio PatternRecognizer for clinical provider names
**Confidence:** HIGH

## Summary

Phase 19 implements detection and redaction of provider names (physicians, nurses, clinical staff) in pediatric handoff transcripts. The implementation follows the proven patterns from Phase 18 (Guardian Edge Cases), using Presidio PatternRecognizer with fixed-width lookbehind patterns.

Provider names appear in handoffs with context like "with Dr. Smith", "paged Dr. Chen", "his nurse is Sarah", "the attending is Rodriguez". The challenge is detecting names in various contexts while:
1. Preserving clinical role descriptors (Dr., RN, NP, attending)
2. Requiring capital letters to prevent false positives on verbs
3. Using deny lists to filter generic role references

**Primary recommendation:** Create a new `PROVIDER_NAME` entity type using the same pattern architecture as GUARDIAN_NAME (lookbehind patterns, 0.85 score, capital letter requirement).

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| presidio-analyzer | 2.2.x | Entity detection | Already in use, proven pattern system |
| spacy en_core_web_lg | 3.x | NER fallback | Already loaded for other recognizers |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python re module | built-in | Regex patterns | Fixed-width lookbehind patterns |

**Installation:** No new packages required - leverages existing Presidio infrastructure.

## Architecture Patterns

### Recommended Project Structure

Provider recognizers should be added to a new file or integrated into the existing recognizer structure:

```
app/recognizers/
    __init__.py          # Export get_provider_recognizers
    pediatric.py         # GUARDIAN_NAME patterns (template)
    medical.py           # MRN, ROOM, PHONE patterns
    provider.py          # NEW: PROVIDER_NAME patterns
```

**Recommendation:** Create `provider.py` to separate provider logic from pediatric/medical patterns. This follows the existing module organization.

### Pattern 1: Title-Prefixed Names (Dr., NP, PA, RN)

**What:** Detect names following professional titles (Dr., NP, PA, RN, MD suffix)
**When to use:** Most common provider mention pattern in handoffs
**Score:** 0.85 (high confidence - title provides strong context)

**Example patterns:**
```python
# Source: Phase 18 Guardian patterns - proven architecture

# "Dr. " + capitalized name = 4 chars lookbehind
# Note: Matches "Dr. Smith" but NOT "Dr. smith" (capital letter required)
Pattern(
    name="dr_name",
    regex=r"(?<=Dr\. )[A-Z][a-z]+\b",
    score=0.85
),

# "Dr " (no period) = 3 chars lookbehind
Pattern(
    name="dr_no_period_name",
    regex=r"(?<=Dr )[A-Z][a-z]+\b",
    score=0.85
),

# Multi-word names: "Dr. De La Cruz" requires first name detection
# Handle via spaCy PERSON fallback in context
```

### Pattern 2: Context-Based Names (attending, fellow, resident, nurse)

**What:** Detect names following role descriptor patterns like "the attending is [Name]"
**When to use:** When provider mentioned by role without formal title
**Score:** 0.85 (role context is strong signal)

**Example patterns:**
```python
# "the attending is " = 17 chars lookbehind
Pattern(
    name="attending_is_name",
    regex=r"(?<=the attending is )[A-Z][a-z]+\b",
    score=0.85
),

# "his nurse " = 10 chars lookbehind
Pattern(
    name="his_nurse_name",
    regex=r"(?<=his nurse )[A-Z][a-z]+\b",
    score=0.85
),

# "her doctor " = 11 chars lookbehind
Pattern(
    name="her_doctor_name",
    regex=r"(?<=her doctor )[A-Z][a-z]+\b",
    score=0.85
),
```

### Pattern 3: Action-Based Context (paged, called, spoke with)

**What:** Detect names following communication verbs
**When to use:** When handoff describes clinical communication
**Score:** 0.80 (slightly lower - action verbs are less specific)

**Example patterns:**
```python
# "paged Dr. " = 10 chars lookbehind
Pattern(
    name="paged_dr_name",
    regex=r"(?<=paged Dr\. )[A-Z][a-z]+\b",
    score=0.80
),

# "with Dr. " = 9 chars lookbehind
Pattern(
    name="with_dr_name",
    regex=r"(?<=with Dr\. )[A-Z][a-z]+\b",
    score=0.80
),

# "called Dr. " = 11 chars lookbehind
Pattern(
    name="called_dr_name",
    regex=r"(?<=called Dr\. )[A-Z][a-z]+\b",
    score=0.80
),
```

### Anti-Patterns to Avoid

- **Variable-width lookbehind:** `(?<=(?:Dr|NP|PA) )` fails - use separate patterns per title
- **Capturing groups:** Don't use `(Dr\. )([A-Z][a-z]+)` - lookbehind is cleaner
- **Lowercase-only names:** Require `[A-Z][a-z]+` to prevent matching verbs like "is"
- **Over-broad context:** Don't match just "with " + name - too many false positives

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Name detection | Custom NER model | Presidio + spaCy | Already loaded, proven accuracy |
| Pattern matching | Python string ops | Regex with lookbehind | Preserves context words automatically |
| Entity registry | Custom class | Presidio PatternRecognizer | Standard API, integrates with anonymizer |
| Threshold calibration | Manual tuning | Follow Phase 18 scores | Validated on real handoffs |

**Key insight:** Phase 18 established that lookbehind patterns with 0.85 score and capital letter requirement work well. Reuse this architecture exactly.

## Common Pitfalls

### Pitfall 1: Matching Generic Role References

**What goes wrong:** Patterns like `(?<=nurse )` match "nurse is here" and flag "is" as a name
**Why it happens:** Common words follow role descriptors without being names
**How to avoid:** Require `[A-Z][a-z]+` (capital first letter) in all patterns
**Warning signs:** Test fails with lowercase words being redacted

### Pitfall 2: Variable-Width Lookbehind

**What goes wrong:** Pattern `(?<=(?:his|her) nurse )` causes regex compilation error
**Why it happens:** Python regex requires fixed-width lookbehind assertions
**How to avoid:** Create separate patterns for each pronoun length
**Warning signs:** Python `re.error: look-behind requires fixed-width pattern`

### Pitfall 3: Over-Detection with Broad Context

**What goes wrong:** "with Dr. Smith" pattern also matches "with medication"
**Why it happens:** Context patterns too broad (just "with ")
**How to avoid:** Always require title (Dr., NP, PA) or explicit role word
**Warning signs:** Clinical terms flagged as provider names

### Pitfall 4: Failing to Add Entity Type to Config

**What goes wrong:** New `PROVIDER_NAME` patterns never fire
**Why it happens:** Entity type not added to `settings.phi_entities` list
**How to avoid:** Add `"PROVIDER_NAME"` to config.py and set threshold
**Warning signs:** Patterns exist but entities never detected

### Pitfall 5: Missing Deny List Integration

**What goes wrong:** Generic role words flagged as names
**Why it happens:** No deny list for PROVIDER_NAME entity type
**How to avoid:** Add `deny_list_provider_name` with role titles and clinical abbreviations
**Warning signs:** "the nurse" flagged with "nurse" as provider name

## Code Examples

### Provider Recognizer Module Structure

```python
# Source: app/recognizers/provider.py (new file)
"""
Provider name recognizers for clinical handoff de-identification.

Detects provider names in patterns like:
- "Dr. Smith", "with Dr. Chen" (title-prefixed)
- "the attending is Rodriguez" (role-based)
- "his nurse Sarah" (possessive role)
- "paged Dr. Johnson" (action-based)

Pattern Design (follows Phase 18 Guardian patterns):
- All patterns use lookbehind to match ONLY the name (preserves context)
- Capital letter requirement [A-Z][a-z]+ prevents verb false positives
- Score 0.85 for high-confidence patterns, 0.80 for action-based
"""

from presidio_analyzer import Pattern, PatternRecognizer


def get_provider_recognizers() -> list[PatternRecognizer]:
    """Create provider-specific PHI recognizers."""
    recognizers = []

    provider_patterns = [
        # =================================================================
        # Title-prefixed patterns: "Dr. Smith", "NP Johnson" (score 0.85)
        # =================================================================
        # "Dr. " = 4 chars lookbehind
        Pattern(name="dr_period_name", regex=r"(?<=Dr\. )[A-Z][a-z]+\b", score=0.85),
        # "Dr " = 3 chars lookbehind (without period)
        Pattern(name="dr_name", regex=r"(?<=Dr )[A-Z][a-z]+\b", score=0.85),
        # Note: Case-insensitive NOT used - "Dr" should be capitalized

        # =================================================================
        # Role context patterns: "the attending is [Name]" (score 0.85)
        # =================================================================
        # "the attending is " = 17 chars
        Pattern(name="attending_is_name", regex=r"(?<=the attending is )[A-Z][a-z]+\b", score=0.85),
        # "the fellow is " = 14 chars
        Pattern(name="fellow_is_name", regex=r"(?<=the fellow is )[A-Z][a-z]+\b", score=0.85),
        # "the resident is " = 16 chars
        Pattern(name="resident_is_name", regex=r"(?<=the resident is )[A-Z][a-z]+\b", score=0.85),

        # =================================================================
        # Possessive patterns: "his nurse Sarah" (score 0.85)
        # Following Phase 18 pattern architecture
        # =================================================================
        # "his nurse " = 10 chars
        Pattern(name="his_nurse_name", regex=r"(?<=his nurse )[A-Z][a-z]+\b", score=0.85),
        # "her nurse " = 10 chars
        Pattern(name="her_nurse_name", regex=r"(?<=her nurse )[A-Z][a-z]+\b", score=0.85),
        # "their nurse " = 12 chars
        Pattern(name="their_nurse_name", regex=r"(?<=their nurse )[A-Z][a-z]+\b", score=0.85),
        # ... (expand for doctor, attending, etc.)

        # =================================================================
        # Action context patterns: "paged Dr. Smith" (score 0.80)
        # =================================================================
        # "paged Dr. " = 10 chars
        Pattern(name="paged_dr_name", regex=r"(?<=paged Dr\. )[A-Z][a-z]+\b", score=0.80),
        # "with Dr. " = 9 chars
        Pattern(name="with_dr_name", regex=r"(?<=with Dr\. )[A-Z][a-z]+\b", score=0.80),
        # "called Dr. " = 11 chars
        Pattern(name="called_dr_name", regex=r"(?<=called Dr\. )[A-Z][a-z]+\b", score=0.80),
    ]

    provider_recognizer = PatternRecognizer(
        supported_entity="PROVIDER_NAME",
        name="Provider Name Recognizer",
        patterns=provider_patterns,
        context=[
            "doctor", "physician", "attending", "fellow", "resident",
            "nurse", "nursing", "RN", "NP", "PA", "Dr",
            "paged", "called", "spoke", "discussed",
        ]
    )
    recognizers.append(provider_recognizer)

    return recognizers
```

### Config Integration

```python
# Source: app/config.py - additions needed

# Add to phi_entities list:
phi_entities: list[str] = Field(
    default=[
        # ... existing entities ...
        "PROVIDER_NAME",  # NEW: Phase 19
    ],
)

# Add to phi_score_thresholds:
phi_score_thresholds: dict[str, float] = Field(
    default={
        # ... existing thresholds ...
        "PROVIDER_NAME": 0.30,  # Same as PERSON/GUARDIAN_NAME
    },
)

# Add deny list:
deny_list_provider_name: list[str] = Field(
    default=[
        # Generic role references (not names)
        "attending", "fellow", "resident", "intern",
        "doctor", "nurse", "nursing",
        "physician", "provider", "clinician",
        # Titles (preserve but don't flag as names)
        "Dr", "NP", "PA", "RN", "LPN", "CNA", "MD",
        # Speech artifacts
        "uh", "um",
    ],
    description="Words that should not be flagged as PROVIDER_NAME"
)
```

### Deidentification Integration

```python
# Source: app/deidentification.py - additions needed

# Add deny list check after existing GUARDIAN_NAME check (around line 198):
# Check PROVIDER_NAME deny list
if result.entity_type == "PROVIDER_NAME" and detected_text.lower() in [w.lower() for w in settings.deny_list_provider_name]:
    logger.debug(f"Filtered out deny-listed PROVIDER_NAME: {detected_text}")
    continue

# Add marker mapping (around line 257):
marker_map = {
    # ... existing mappings ...
    "[Provider Name]": "[NAME]",  # Map to generic [NAME] marker
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Generic PERSON entity only | Custom entity per context | Phase 18 (2026-01) | Higher recall with preserved context |
| Case-insensitive patterns | Capital letter requirement | Phase 18-03 (2026-01-30) | Eliminates verb false positives |
| Single score for all patterns | Context-based scores | Phase 18 | Better precision tuning |

**Current best practice:**
- Create context-specific entity types (GUARDIAN_NAME, PROVIDER_NAME) rather than relying solely on generic PERSON
- Use lookbehind patterns to preserve context words
- Require capital letters to prevent false positives
- Use 0.85 score for high-confidence patterns, 0.80 for action-based

## Open Questions

### 1. MD Suffix Patterns

**What we know:** Providers may have "MD" after name: "John Smith MD"
**What's unclear:** How common is this in spoken handoffs vs written notes?
**Recommendation:** Add patterns for "Smith MD" but lower priority - title prefix more common in speech

### 2. Multi-Word Names

**What we know:** Some providers have multi-word names: "Dr. De La Cruz"
**What's unclear:** Pattern complexity for variable-length name components
**Recommendation:** Focus on single-word detection; spaCy PERSON fallback will catch multi-word

### 3. Informal References

**What we know:** Handoffs may say "Sarah the nurse" without last name
**What's unclear:** Whether this pattern is PHI-worthy vs acceptable given context
**Recommendation:** Implement conservatively per CONTEXT.md decision; patterns like "Sarah the nurse" should be detected

### 4. First Name Only

**What we know:** "Paged Sarah about labs" may refer to provider by first name only
**What's unclear:** How to distinguish provider first name from patient first name
**Recommendation:** Use context (paged, called, spoke with) to increase confidence; map to PERSON if uncertain

## Sources

### Primary (HIGH confidence)

- `app/recognizers/pediatric.py` - Guardian pattern implementation (lines 45-500)
- `app/recognizers/medical.py` - Room/MRN pattern implementation (lines 70-290)
- Phase 18 Research and Plans - Proven architecture
- `app/config.py` - Entity types and deny list patterns

### Secondary (MEDIUM confidence)

- Presidio documentation - PatternRecognizer API
- Python re module documentation - Lookbehind assertions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing Presidio infrastructure
- Architecture: HIGH - Following proven Phase 18 Guardian patterns
- Pitfalls: HIGH - Documented from Phase 18 implementation experience

**Research date:** 2026-01-30
**Valid until:** 60 days (stable domain, patterns unlikely to change)

---

## Implementation Phases (Recommendation for Planner)

### Plan 19-01: Title-Prefixed Patterns

**Scope:** Implement "Dr. [Name]", "NP [Name]", "PA [Name]" patterns
**Why first:** Most common provider reference pattern in handoffs
**Estimated patterns:** ~10-15 (titles with/without period)
**Test cases:** 3-4

### Plan 19-02: Role Context Patterns

**Scope:** Implement "the attending is [Name]", "his nurse [Name]" patterns
**Why second:** Catches informal references without titles
**Estimated patterns:** ~30-40 (possessive × role combinations)
**Test cases:** 3-4

### Plan 19-03: Action Context Patterns

**Scope:** Implement "paged Dr. [Name]", "with Dr. [Name]" patterns
**Why third:** Catches action-based references
**Estimated patterns:** ~15-20 (action verbs × title combinations)
**Test cases:** 2-3

### Plan 19-04: Validation and Recall Measurement

**Scope:** Run full validation, measure PERSON recall improvement
**Why last:** Confirm patterns work before declaring phase complete
**Deliverable:** Recall improvement report

---

**Research complete.** Ready for planning phase.
