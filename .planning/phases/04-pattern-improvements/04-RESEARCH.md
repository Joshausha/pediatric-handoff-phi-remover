# Phase 4: Pattern Improvements - Research

**Researched:** 2026-01-23
**Domain:** Regex pattern engineering for medical PHI detection (Presidio-based)
**Confidence:** HIGH

## Summary

Phase 4 addresses the fundamental limitation discovered in Phase 2: **threshold tuning cannot fix pattern gaps**. Presidio confidence scores cluster at extremes (0.0 for missed, 0.85+ for detected), meaning entities are either caught or completely missed based solely on whether patterns match. Five of eight entity types require pattern work to achieve 90% recall: PEDIATRIC_AGE (35.8% → 90%), ROOM (32.1% → 90%), LOCATION (20.0% → 90%), PHONE_NUMBER (75.7% → 90%), and MRN (72.3% → 90%).

The research reveals three critical pattern engineering challenges: (1) **Lookbehind edge cases** at start-of-line and after punctuation where lookbehind assertions fail, (2) **Bidirectional relationship patterns** where "Jessica is Mom" is missed despite catching "Mom Jessica", and (3) **Speech-to-text artifacts** from Whisper transcription (stutters, corrections, hesitations) that break pattern matches. User decisions constrain scope: ages remain un-redacted for clinical utility, room patterns require keywords to avoid false positives, and fuzzy matching is deferred.

**Primary recommendation:** Use Python's `re.IGNORECASE` flag with word boundary anchors (`\b`) and optional punctuation patterns to handle edge cases. Implement alternation patterns for bidirectional matching. Build pytest parameterized test suites covering all adversarial edge cases from existing templates.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| presidio-analyzer | 2.2.x | Pattern-based PII detection | Microsoft official library, designed for extensible custom recognizers |
| Python re module | stdlib | Regex pattern matching | Native Python, no dependencies, full Unicode support |
| pytest | 7.x+ | Testing framework | Industry standard for Python testing, excellent parameterization |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| spacy | 3.x | NER model fallback | Already integrated in Presidio for PERSON/LOCATION entities |
| faker | Latest | Synthetic test data | Already used for generating test handoffs with ground truth |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Presidio PatternRecognizer | Custom regex + spaCy NER | Presidio provides context support, deny lists, scoring framework for free |
| Python re | regex library | `regex` supports variable-length lookbehinds, but adds dependency for marginal gain |
| Pytest parametrize | unittest | Pytest parameterization is significantly more readable and maintainable |

**Installation:**
```bash
# Already installed in project
pip install presidio-analyzer pytest faker spacy
python -m spacy download en_core_web_lg
```

## Architecture Patterns

### Recommended Pattern Structure for Each Entity Type

```python
# Pattern Engineering Template
Pattern(
    name="descriptive_name",
    regex=r"(?i)\b(?:keyword1|keyword2)\s+([A-Z][a-z]+)\b",  # Case-insensitive with word boundaries
    score=0.85  # High for specific patterns, 0.5-0.6 for broader patterns
)
```

### Pattern 1: Lookbehind with Edge Case Handling
**What:** Handle start-of-line, punctuation, and word boundary cases
**When to use:** Guardian names, baby names, room numbers with keyword prefixes

**Example:**
```python
# PROBLEM: Lookbehind fails at start of line
Pattern(
    name="mom_name_lookbehind",
    regex=r"(?<=Mom )[A-Z][a-z]+\b",  # Fails for "Mom Jessica" at line start
    score=0.85
)

# SOLUTION 1: Use case-insensitive flag with word boundaries (no lookbehind)
Pattern(
    name="mom_name_no_lookbehind",
    regex=r"(?i)\bmom\s+([A-Z][a-z]+)\b",  # Captures "Mom Jessica" anywhere
    score=0.85
)

# SOLUTION 2: Keep lookbehind but add alternative pattern for start-of-line
patterns = [
    Pattern(name="mom_name_mid", regex=r"(?<=Mom )[A-Z][a-z]+\b", score=0.85),
    Pattern(name="mom_name_start", regex=r"^Mom ([A-Z][a-z]+)\b", score=0.85),
]
```

**Key insight:** Python regex lookbehind cannot step back from position 0, so negative lookbehind `(?<!.)` succeeds at start-of-string, but positive lookbehind fails. Use `^` anchor or non-lookbehind alternatives for start-of-line cases.

**Source:** [Regex Tutorial: Lookaround](https://www.regular-expressions.info/lookaround.html)

### Pattern 2: Bidirectional Relationship Patterns
**What:** Catch both "Mom Jessica" and "Jessica is Mom" patterns
**When to use:** Guardian names where relationship word can appear before or after the name

**Example:**
```python
# Standard pattern: "Mom Jessica" (relationship before name)
Pattern(
    name="relationship_before_name",
    regex=r"(?i)\b(?:mom|dad|grandma|grandpa)\s+([A-Z][a-z]+)\b",
    score=0.85
)

# Bidirectional pattern: "Jessica is Mom" (name before relationship)
Pattern(
    name="name_before_relationship",
    regex=r"(?i)\b([A-Z][a-z]+)\s+is\s+(?:mom|dad|grandma|grandpa)\b",
    score=0.80  # Slightly lower score due to broader pattern
)

# Combined with alternation for both orders
Pattern(
    name="guardian_bidirectional",
    regex=r"(?i)(?:\b(?:mom|dad)\s+([A-Z][a-z]+)\b|\b([A-Z][a-z]+)\s+is\s+(?:mom|dad)\b)",
    score=0.85
)
```

**Key insight:** Place more specific alternations first (SetValue before Set) due to eager matching. Use non-capturing groups `(?:pattern)` to reduce memory unless backreferencing needed.

**Source:** [Regex Alternation Tutorial](https://www.regular-expressions.info/alternation.html)

### Pattern 3: Case Normalization
**What:** Handle lowercase relationship words ("mom jessica" not just "Mom Jessica")
**When to use:** All guardian/relationship patterns, room keywords, age descriptors

**Example:**
```python
# PROBLEM: Only catches capitalized relationship words
Pattern(
    name="mom_name_case_sensitive",
    regex=r"\bMom\s+([A-Z][a-z]+)\b",  # Misses "mom Jessica"
    score=0.85
)

# SOLUTION: Use re.IGNORECASE flag
Pattern(
    name="mom_name_case_insensitive",
    regex=r"(?i)\bmom\s+([A-Z][a-z]+)\b",  # Catches "Mom", "mom", "MOM"
    score=0.85
)

# In Python code:
import re
re.findall(r"(?i)\bmom\s+([A-Z][a-z]+)\b", text)  # Case-insensitive matching
```

**Key insight:** `(?i)` flag makes character classes and literals match case-insensitively. For Unicode text, `[a-z]` with IGNORECASE matches 52 ASCII letters plus 4 non-ASCII letters (İ, ı, ſ, K).

**Source:** [Python Regex IGNORECASE](https://docs.python.org/3/howto/regex.html)

### Pattern 4: Speech Artifact Tolerance
**What:** Handle stutters, repetitions, corrections in Whisper transcripts
**When to use:** All patterns, especially guardian names and contact info

**Example:**
```python
# PROBLEM: Stutters break pattern matching
text = "Um, this is uh Jessica"  # "uh" breaks "this is Jessica" match

# SOLUTION 1: Make filler words optional with lookahead
Pattern(
    name="person_with_fillers",
    regex=r"(?i)\bthis\s+is\s+(?:uh\s+|um\s+)?([A-Z][a-z]+)\b",  # Optional fillers
    score=0.85
)

# SOLUTION 2: Handle repetitions (NOT stuttered partials, Whisper produces complete words)
text = "Room room 12"  # Repetition artifact
Pattern(
    name="room_with_repetition",
    regex=r"(?i)(?:room\s+)?room\s+(\d{1,4}[A-Za-z]?)\b",  # Optional repeated word
    score=0.70  # Lower score for looser pattern
)

# SOLUTION 3: Handle corrections
text = "Patient is John no wait Jessica"
# Defer complex correction parsing - rely on spaCy NER catching both names
# Phase 4 focus: complete words only, not partial transcription errors
```

**Key insight:** Whisper produces complete words, not partial stutters. Handle word-level repetitions with optional prefixes, defer fuzzy name matching to future phases.

**Source:** [Transcription Guidelines: Stutters](https://reduct.video/transcribe/guidelines/stutters-and-repetitions/), [StutterZero Research](https://arxiv.org/html/2510.18938)

### Pattern 5: Room/Bed Number Keyword Requirement
**What:** Conservative pattern requiring "room" or "bed" keywords before numbers
**When to use:** ROOM entity type to avoid false positives on standalone numbers

**Example:**
```python
# User decision: Require keywords to avoid flagging dosages, ages, weights
patterns = [
    # Standard formats with keywords
    Pattern(
        name="room_standard",
        regex=r"(?i)(?:room|rm)\s+(\d{1,4}[A-Za-z]?)\b",  # "room 302", "Room 5A"
        score=0.70
    ),
    Pattern(
        name="bed_standard",
        regex=r"(?i)bed\s+(\d{1,2}[A-Za-z]?)\b",  # "bed 12", "Bed 3A"
        score=0.65
    ),
    # ICU patterns preserving unit names
    Pattern(
        name="picu_bed",
        regex=r"(?i)PICU\s+bed\s+(\d{1,3}[A-Za-z]?)\b",  # "PICU bed 7"
        score=0.85  # Higher confidence with unit context
    ),
    # Handle lowercase with lookbehind alternative
    Pattern(
        name="unit_bed_lowercase",
        regex=r"(?i)(?:picu|nicu|icu)\s+bed\s+(\d{1,3}[A-Za-z]?)\b",
        score=0.85
    ),
]
```

**Key insight:** User decision prioritizes precision over recall for ROOM. Accept some missed rooms rather than flagging "continue 3 days of antibiotics" as room number. Target 90% recall with keyword-constrained patterns.

### Pattern 6: Pediatric Age Abbreviations
**What:** Support both full notation ("3 weeks old") and abbreviations ("3wo", "17yo", "22mo")
**When to use:** PEDIATRIC_AGE entity type, but review if entity should be disabled entirely

**Example:**
```python
# User decision context: Ages are NOT PHI under HIPAA (unless 90+)
# Pattern improvements may not be needed if entity is disabled

# IF keeping entity, expand patterns:
patterns = [
    # Abbreviations: "17yo", "4 yo", "22mo", "3 mo"
    Pattern(
        name="age_abbreviated",
        regex=r"\b(\d{1,2})\s*(?:yo|y\.o\.|years?\s+old)\b",  # "17yo", "4 yo", "3 years old"
        score=0.60
    ),
    Pattern(
        name="age_months",
        regex=r"\b(\d{1,2})\s*(?:mo|months?\s+old)\b",  # "22mo", "3 mo"
        score=0.60
    ),
    Pattern(
        name="age_weeks",
        regex=r"\b(\d{1,2})\s*(?:wo|weeks?\s+old)\b",  # "3wo", "6 weeks old"
        score=0.60
    ),
    # Gestational notation: "34 weeker", "ex-28 weeker", "36+3"
    Pattern(
        name="gestational_weeks_plus_days",
        regex=r"\b(\d{2})\+(\d)\b",  # "36+3", "28+5"
        score=0.65
    ),
    Pattern(
        name="gestational_weeker",
        regex=r"\b(?:ex-)?(\d{2})\s*weeker\b",  # "34 weeker", "ex-28 weeker"
        score=0.65
    ),
]
```

**Key insight:** User discretion on whether PEDIATRIC_AGE should exist at all. If kept, support clinical shorthand (yo/mo/wo) and gestational notation (weeks+days, "ex-X weeker"). If removed, focus pattern work on high-risk entities (names, MRN, room).

**Source:** [Gestational Age Terminology](https://neonataltherapists.com/using-correct-terminology-in-the-nicu/)

### Anti-Patterns to Avoid

**Don't: Over-broad patterns without context**
```python
# BAD: Catches every capitalized word as PERSON
Pattern(name="any_capitalized", regex=r"\b[A-Z][a-z]+\b", score=0.5)

# GOOD: Use context words and relationship indicators
Pattern(name="person_with_context", regex=r"(?i)\bpatient\s+([A-Z][a-z]+)\b", score=0.7)
```

**Don't: Fixed-width expectations in variable text**
```python
# BAD: Assumes single space between words
Pattern(name="mom_name_fixed", regex=r"Mom [A-Z][a-z]+", score=0.85)

# GOOD: Use \s+ for flexible whitespace
Pattern(name="mom_name_flexible", regex=r"(?i)\bmom\s+([A-Z][a-z]+)\b", score=0.85)
```

**Don't: Rely on capitalization from speech-to-text**
```python
# BAD: Requires "Mom" with capital M
Pattern(name="needs_capital", regex=r"\bMom\s", score=0.85)

# GOOD: Case-insensitive with (?i)
Pattern(name="case_insensitive", regex=r"(?i)\bmom\s", score=0.85)
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PII detection framework | Custom regex + filtering | Presidio PatternRecognizer | Context support, deny lists, scoring, validation all built-in |
| Test data generation | Manual test cases | Faker + templates | Reproducible synthetic PHI with ground truth spans |
| Regex performance testing | Custom timing loops | Presidio evaluator + pytest benchmarks | Overlap-based matching, F2 scoring, confusion matrices |
| Pattern overlap detection | Manual span checking | Presidio analyzer handles it | Automatic de-duplication and span merging |

**Key insight:** Presidio's PatternRecognizer provides context-aware scoring (nearby keywords boost confidence), deny list filtering, and span overlap handling. Don't reimplement this infrastructure—extend it with custom patterns.

**Source:** [Presidio Best Practices](https://microsoft.github.io/presidio/analyzer/developing_recognizers/)

## Common Pitfalls

### Pitfall 1: Lookbehind Failure at String Start
**What goes wrong:** Pattern `(?<=Mom )[A-Z][a-z]+` fails to match "Mom Jessica" at line start
**Why it happens:** Regex engine cannot step back from position 0 for positive lookbehind
**How to avoid:** Use `^` anchor alternative OR switch to non-lookbehind pattern with capture group
**Warning signs:** Tests pass for mid-sentence cases but fail for sentence-initial cases

**Example:**
```python
# Add separate pattern for start-of-line
patterns = [
    Pattern(name="mom_mid", regex=r"(?<=Mom )[A-Z][a-z]+\b", score=0.85),
    Pattern(name="mom_start", regex=r"^Mom ([A-Z][a-z]+)\b", score=0.85),
]

# OR use word boundary approach (no lookbehind)
Pattern(name="mom_any", regex=r"(?i)\bmom\s+([A-Z][a-z]+)\b", score=0.85)
```

**Source:** [Lookaround Assertions](https://www.regular-expressions.info/lookaround.html)

### Pitfall 2: Alternation Order Matters
**What goes wrong:** Pattern `Get|GetValue` always matches "Get" from "GetValue", never "GetValue"
**Why it happens:** Regex engine is eager—first match wins, even if longer alternative exists
**How to avoid:** Place longer/more-specific alternatives before shorter/broader ones
**Warning signs:** Precision drops because broad patterns match before specific ones

**Example:**
```python
# BAD: Broader pattern first
regex=r"(?i)\b(mom|mother)\b"  # "mother" never matches, "mom" within "mother" matches

# GOOD: Longer pattern first
regex=r"(?i)\b(mother|mom)\b"  # "mother" gets chance before "mom"
```

**Source:** [Regex Alternation Tutorial](https://www.regular-expressions.info/alternation.html)

### Pitfall 3: Case Sensitivity in Speech Transcripts
**What goes wrong:** Pattern matches "Mom Jessica" but misses "mom jessica" from speech-to-text
**Why it happens:** Whisper transcription may lowercase common words, capitalize at sentence starts
**How to avoid:** Use `(?i)` flag on all patterns, test with both capitalized and lowercase variants
**Warning signs:** Tests with manually-typed text pass, real Whisper transcripts fail

**Example:**
```python
# Add to all patterns
Pattern(name="any_pattern", regex=r"(?i)\bpattern\b", score=0.85)

# Test with both cases
test_cases = [
    "Mom Jessica at bedside",  # Capitalized
    "mom jessica at bedside",  # Lowercase
    "MOM JESSICA AT BEDSIDE",  # All caps
]
```

### Pitfall 4: Forgetting Word Boundaries
**What goes wrong:** Pattern `\d+` matches "12" within "A1234567" (MRN), causing false positive
**Why it happens:** Without `\b` anchors, pattern matches substrings within larger tokens
**How to avoid:** Use `\b` word boundary assertions for all number/word patterns
**Warning signs:** High false positive rate on medical abbreviations and codes

**Example:**
```python
# BAD: Matches within words
Pattern(name="room_no_boundary", regex=r"room\s+\d+", score=0.7)  # Matches "bedroom 5"

# GOOD: Word boundaries prevent substring matches
Pattern(name="room_bounded", regex=r"(?i)\broom\s+\d+\b", score=0.7)
```

### Pitfall 5: Over-Reliance on Threshold Tuning
**What goes wrong:** Expecting lowering threshold from 0.35 to 0.30 to improve recall
**Why it happens:** Misunderstanding of Presidio score distribution (clusters at 0.0 or 0.85+, not between)
**How to avoid:** Accept that threshold tuning has minimal impact; focus on pattern coverage
**Warning signs:** Phase 2 calibration showed <2% recall change across threshold range

**Key insight from Phase 2:** Presidio scores cluster at extremes. Entities are either detected (0.85+ score) or completely missed (0.0 score). Threshold changes don't help—only better patterns help.

### Pitfall 6: Treating Pediatric Ages as PHI
**What goes wrong:** Redacting ages that aren't PHI under HIPAA, losing clinical utility
**Why it happens:** Over-conservative interpretation of 18 identifiers list
**How to avoid:** Review HIPAA Safe Harbor guidance—ages <90 are NOT PHI
**Warning signs:** User feedback: "Why is '3 month old' redacted? That's critical info!"

**User decision:** Keep ages for clinical utility. Consider disabling PEDIATRIC_AGE recognizer entirely or limiting to ages 90+.

## Code Examples

Verified patterns from current implementation and Presidio documentation:

### Guardian Name Pattern (Current Implementation)
```python
# Source: app/recognizers/pediatric.py lines 34-110
from presidio_analyzer import Pattern, PatternRecognizer

guardian_patterns = [
    Pattern(
        name="mom_name",
        regex=r"(?<=Mom )[A-Z][a-z]+\b",  # Current: lookbehind preserves "Mom"
        score=0.85
    ),
    Pattern(
        name="dad_name",
        regex=r"(?<=Dad )[A-Z][a-z]+\b",
        score=0.85
    ),
    # ... 10 more relationship patterns
]

guardian_recognizer = PatternRecognizer(
    supported_entity="GUARDIAN_NAME",
    name="Guardian Name Recognizer",
    patterns=guardian_patterns,
    context=["parent", "guardian", "family", "caregiver", "at bedside"]
)
```

**Phase 4 improvements needed:**
1. Add case-insensitive flag `(?i)` to all patterns
2. Add bidirectional patterns for "Jessica is Mom"
3. Add start-of-line alternatives for lookbehind edge case
4. Add filler word tolerance ("uh", "um") patterns

### Room Number Pattern (Current Implementation)
```python
# Source: app/recognizers/medical.py lines 69-106
room_patterns = [
    Pattern(
        name="room_standard",
        regex=r"(?<=Room |room |Rm |rm )\d{1,4}[A-Za-z]?\b",  # Current: lookbehind
        score=0.6
    ),
    Pattern(
        name="bed_number",
        regex=r"(?<=bed |Bed )\d{1,2}[A-Za-z]?\b",
        score=0.55
    ),
    Pattern(
        name="picu_bed",
        regex=r"(?<=PICU bed |PICU Bed )\d{1,3}[A-Za-z]?\b",
        score=0.7
    ),
]
```

**Phase 4 improvements needed:**
1. Case-insensitive flag to catch "picu bed 7" not just "PICU bed 7"
2. Start-of-line alternatives for sentences beginning with room numbers
3. Multi-part room numbers ("3-22", "4/11") per calibration results
4. Bay/isolette alternatives ("bay 5", "isolette 21")

### Pediatric Age Pattern (Current Implementation)
```python
# Source: app/recognizers/pediatric.py lines 165-202
age_patterns = [
    Pattern(
        name="age_days",
        regex=r"\b(\d{1,3})[\s-]?(?:day|d)[\s-]?(?:s)?[\s-]?old\b",
        score=0.5
    ),
    Pattern(
        name="age_weeks",
        regex=r"\b(\d{1,2})[\s-]?(?:week|wk)[\s-]?(?:s)?[\s-]?old\b",
        score=0.5
    ),
    Pattern(
        name="gestational_age",
        regex=r"\b(\d{2})[\s-]?(?:week|wk)(?:er|s)?(?:\s+(?:gestation|gestational|GA))?\b",
        score=0.5
    ),
]
```

**Phase 4 improvements needed (IF keeping entity):**
1. Abbreviation formats: "17yo", "4 yo", "22mo", "3 mo", "6wo"
2. Gestational weeks+days: "36+3", "28+5"
3. "Ex-X weeker" format: "ex-28 weeker"
4. Day of life: "DOL 6", "day of life 7"

**OR:** Disable entity entirely per user discretion (ages aren't PHI).

### Pytest Parameterized Test Example
```python
# Source: tests/test_deidentification.py lines 140-152
import pytest
from tests.sample_transcripts import SAMPLE_TRANSCRIPTS

@pytest.mark.parametrize("sample", SAMPLE_TRANSCRIPTS, ids=lambda s: f"transcript_{s['id']}")
def test_sample_transcript(sample):
    """Test each sample transcript for proper de-identification."""
    result = deidentify_text(sample["text"])

    # Check that expected PHI is removed
    for phi in sample["expected_removed"]:
        assert phi not in result.clean_text, f"PHI '{phi}' should be removed"

    # Check that medical content is preserved
    for term in sample["expected_preserved"]:
        assert term in result.clean_text, f"Medical term '{term}' should be preserved"
```

**Phase 4 expansion needed:**
Create parameterized tests from adversarial templates (handoff_templates.py lines 198-326):
- Speech artifact templates (stutters, corrections)
- Boundary edge templates (start-of-line, punctuation-adjacent)
- Reversed relationship patterns
- Case sensitivity variants

### Presidio Context Support Example
```python
# Source: Official Presidio docs
from presidio_analyzer import Pattern, PatternRecognizer

# Weak pattern benefits from context boosting
zip_pattern = Pattern(
    name="us_zip",
    regex=r"\b\d{5}(?:-\d{4})?\b",  # Matches any 5 digits - too broad
    score=0.3  # LOW initial score
)

zip_recognizer = PatternRecognizer(
    supported_entity="ZIP_CODE",
    patterns=[zip_pattern],
    context=["zip", "zipcode", "postal", "address", "mailing"]  # Boost confidence if nearby
)

# When "zip code: 12345" appears, score boosts from 0.3 to higher confidence
# When "room 12345" appears, score stays 0.3 (may be filtered by threshold)
```

**Key insight:** Use context words to distinguish ambiguous patterns. Low base score + context boost prevents false positives while catching true positives.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Threshold tuning for recall | Pattern engineering for recall | Phase 2 (2026-01-23) | Threshold changes have <2% impact; patterns are necessary |
| Case-sensitive patterns | `(?i)` case-insensitive | Phase 4 (pending) | Whisper produces variable capitalization; case-insensitive essential |
| Unidirectional patterns | Bidirectional alternation | Phase 4 (pending) | Catches "Jessica is Mom" and "Mom Jessica" with same pattern |
| Lookbehind-only | Lookbehind + start-of-line alternatives | Phase 4 (pending) | Fixes edge cases where lookbehind fails at position 0 |
| ML-only speech artifact handling | Rule-based + ML hybrid | 2026 trend | StutterZero research shows ML for explicit stutters, rules for simple fillers |

**Deprecated/outdated:**
- **Threshold-first optimization** (pre-Phase 2): Assumption that threshold tuning could fix recall. Phase 2 proved this wrong—scores cluster at extremes (0.0 or 0.85+), no entities score in 0.30-0.85 range.
- **Capitalization reliance**: Early patterns assumed "Mom Jessica" capitalization from manual entry. Speech-to-text produces "mom jessica", "Mom Jessica", "MOM JESSICA" unpredictably.
- **Single-direction relationship patterns**: Original implementation only caught "Mom Jessica", missed "Jessica is Mom".

**Current 2026 trends:**
- **Hybrid ML + rules** for speech artifacts: ML models (StutterZero, StutterFormer) for complex stutters, simple regex for "um/uh" fillers
- **Conservative HIPAA interpretation**: User preference for preserving clinical utility (keep ages) while removing true identifiers (names, MRN, room)
- **F2 score optimization**: Recall weighted 2x precision, reflecting safety priority (missed PHI worse than over-redaction)

**Sources:**
- [StutterZero Research](https://arxiv.org/html/2510.18938) (Oct 2024)
- Phase 2 Calibration Results (2026-01-23)
- [Presidio Developing Recognizers](https://microsoft.github.io/presidio/analyzer/developing_recognizers/)

## Open Questions

### 1. Should PEDIATRIC_AGE recognizer be disabled entirely?
**What we know:**
- Ages <90 are NOT PHI under HIPAA Safe Harbor
- User decision: "Keep ages for clinical utility"
- Current recall: 35.8%, requires significant pattern work to reach 90%

**What's unclear:**
- Is there ANY value in redacting detailed ages like "3 weeks 2 days old"?
- Could rare condition + specific age be quasi-identifier?
- Is pattern engineering effort worth it for non-PHI entity?

**Recommendation:**
- **Option A (RECOMMENDED):** Disable PEDIATRIC_AGE recognizer, keep ages in transcripts
- **Option B:** Keep recognizer but only for ages 90+ (HIPAA requirement)
- **Option C:** Keep recognizer but downgrade to score=0.3 (only redact if high-confidence match with context)

### 2. What is acceptable recall floor for LOCATION entity?
**What we know:**
- Current recall: 20.0% (worst performing entity)
- spaCy NER misses generic hospital names, addresses without strong NER signals
- Phase 2: "No threshold achieves 90% floor; pattern gaps"

**What's unclear:**
- Is 90% recall achievable for LOCATION without comprehensive hospital/clinic name lists?
- Should we lower recall target for LOCATION to 70-80% given NER limitations?
- Trade-off: Adding location keywords increases false positives (e.g., "NC" for North Carolina vs nasal cannula)

**Recommendation:**
- Target 80% recall for LOCATION (not 90%) given NER limitations
- Add pattern for explicit address formats (street numbers + names)
- Maintain medical abbreviation deny list to prevent false positives

### 3. How to handle lettered beds ("bed A", "bed B")?
**What we know:**
- User decision: "Claude's discretion based on HIPAA minimum necessary"
- Current patterns catch alphanumeric beds: "bed 3A", "room 12B"
- Single-letter beds: "bed A", "bed B" are just letters—high false positive risk

**What's unclear:**
- In how many hospitals would "bed A" alone identify a patient?
- Is "PICU bed A" more identifying than "bed A" in general ward?
- Would removing single-letter beds create unacceptable over-redaction?

**Recommendation:**
- **Redact multi-character beds:** "bed 3A", "room 12B" (likely identifying)
- **Preserve single-letter beds:** "bed A", "bed B" alone (minimal identifying value, high false positive risk)
- **Context-dependent:** Redact "PICU bed A" (small unit, more identifying), preserve "bed A" without unit

## Sources

### Primary (HIGH confidence)
- [Presidio Analyzer Documentation](https://microsoft.github.io/presidio/analyzer/) - Official Microsoft library docs
- [Presidio Developing Recognizers](https://microsoft.github.io/presidio/analyzer/developing_recognizers/) - Best practices verified
- [Presidio Regex Tutorial](https://microsoft.github.io/presidio/tutorial/02_regex/) - Pattern examples
- [Python Regex HOWTO](https://docs.python.org/3/howto/regex.html) - Official Python docs (2026-01-23)
- [Pytest Parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html) - Official pytest docs
- Phase 2 Calibration Results (2026-01-23) - Internal project data

### Secondary (MEDIUM confidence)
- [Regex Lookaround Tutorial](https://www.regular-expressions.info/lookaround.html) - Comprehensive regex reference
- [Regex Alternation](https://www.regular-expressions.info/alternation.html) - Pattern ordering best practices
- [Python Case-Insensitive Regex](https://www.geeksforgeeks.org/python/python-case-insensitive-string-replacement/) - IGNORECASE flag usage
- [Gestational Age Terminology](https://neonataltherapists.com/using-correct-terminology-in-the-nicu/) - Medical notation standards
- [Transcription Guidelines: Stutters](https://reduct.video/transcribe/guidelines/stutters-and-repetitions/) - Speech-to-text best practices

### Tertiary (LOW confidence)
- [StutterZero Research](https://arxiv.org/html/2510.18938) - 2024 research, not production-ready
- [Hospital Room Numbering Standards](https://policymanual.nih.gov/1212) - NIH-specific, may not generalize
- [Regex Optional Groups 2026](https://copyprogramming.com/howto/regex-optional-group) - Blog post, not authoritative

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Presidio is Microsoft official, pytest is Python standard
- Architecture patterns: HIGH - Verified with official Presidio docs and Python regex docs
- Pitfalls: HIGH - Derived from Phase 2 calibration data and regex documentation
- Speech artifacts: MEDIUM - Research papers not yet production-proven, defer complex cases
- Age/room conventions: MEDIUM - Medical notation documented, but hospital-specific variations exist

**Research date:** 2026-01-23
**Valid until:** 2026-04-23 (90 days - regex standards stable, Presidio updates minor)

**What might I have missed:**
- Hospital-specific room numbering systems beyond standard formats
- Cultural name patterns beyond Western conventions (Chinese, Arabic, etc.)
- Whisper transcription quirks for medical terminology (needs live testing)
- Presidio performance degradation with 20+ custom recognizers (needs benchmarking)
