# Phase 18 Research: Guardian Edge Cases

**Research Date:** 2026-01-30
**Researcher:** Claude (GSD research agent)
**Phase Goal:** Catch possessive and appositive guardian name patterns

## Executive Summary

Phase 18 targets three guardian name patterns currently missed:
1. **Possessive patterns**: "his mom Sarah", "her dad Tom" (possessive pronoun + relationship + name)
2. **Appositive patterns**: "the mom, Jessica" (relationship word + comma/dash + name)
3. **Cross-sentence patterns**: "Grandma's here. Her name is Maria" (immediately following sentence)

All three can be implemented using Presidio's `PatternRecognizer` with regex patterns. The main technical challenges are:
- Presidio lookbehind requires **fixed width** (cannot use quantifiers like `+` or `*`)
- Cross-sentence detection may require sentence boundary awareness
- Must preserve context words in output (pronoun + relationship word)

**Recommendation:** Implement possessive and appositive patterns first (straightforward regex). Defer cross-sentence patterns if they require significant refactoring (may need sentence tokenization or context preservation state).

---

## Current Guardian Implementation Analysis

### Existing Pattern Strategy (from `app/recognizers/pediatric.py`)

The current guardian recognizer uses three pattern types:

1. **Forward patterns** (score 0.85): `"Mom Jessica"`, `"dad mike"`
   - Uses **fixed-width lookbehind** to match ONLY the name
   - Example: `(?i)(?<=mom )[a-z][a-z]+\b` matches "Jessica" but preserves "Mom"
   - Separate patterns for each relationship word due to lookbehind width constraint

2. **Bidirectional patterns** (score 0.80): `"Jessica is Mom"`
   - Uses **lookahead** to match ONLY the name before "is [relationship]"
   - Example: `(?i)\b[a-z][a-z]+(?= is (?:mom|mother|mommy)\b)`

3. **Speech artifact patterns** (score 0.75): `"mom uh Jessica"`, `"mom mom Jessica"`
   - Handles filler words ("uh", "um") and repetition
   - Fixed-width lookbehind: `(?i)(?<=mom uh )[a-z][a-z]+\b` (7 chars)

**Key Insights:**
- All patterns are case-insensitive (`(?i)` flag)
- Lookbehind matches ONLY the name part (preserves relationship word in output)
- Fixed-width lookbehind requirement drives separate pattern per relationship word
- Context words provided to recognizer: `["parent", "guardian", "family", "caregiver", "at bedside", "reached at", "contact"]`

---

## Edge Case Pattern Research

### 1. Possessive Patterns

**Target:** `"his mom Sarah"`, `"her dad Tom"`, `"the patient's mom Jessica"`

**Challenge:** Lookbehind must be fixed width, but possessive pronouns vary in length:
- `his` (3 chars)
- `her` (3 chars)
- `their` (5 chars)
- `the patient's` (13 chars)
- `baby's` (6 chars)
- `child's` (7 chars)

**Solution:** Create separate patterns for each possessive pronoun length.

**Pattern Examples:**

```python
# "his mom " = 8 chars (3 + space + 3 + space)
Pattern(
    name="his_mom_name",
    regex=r"(?i)(?<=his mom )[a-z][a-z]+\b",
    score=0.85
)

# "her dad " = 8 chars (3 + space + 3 + space)
Pattern(
    name="her_dad_name",
    regex=r"(?i)(?<=her dad )[a-z][a-z]+\b",
    score=0.85
)

# "their mom " = 10 chars (5 + space + 3 + space)
Pattern(
    name="their_mom_name",
    regex=r"(?i)(?<=their mom )[a-z][a-z]+\b",
    score=0.85
)

# "the patient's mom " = 19 chars
Pattern(
    name="the_patients_mom_name",
    regex=r"(?i)(?<=the patient's mom )[a-z][a-z]+\b",
    score=0.85
)
```

**Relationship Words to Cover:**
- Mom, mother, mommy
- Dad, father, daddy
- Grandma, grandmother, grandpa, grandfather, nana, papa, granny
- Aunt, auntie, uncle
- Guardian

**Possessive Pronouns to Cover:**
- `his`, `her`, `their` (standard)
- `the patient's`, `baby's`, `child's`, `infant's` (clinical context)

**Estimated Patterns:** ~50 patterns (6 possessive forms × 8-10 relationship words)

**Output Preservation:** The lookbehind matches ONLY the name, so "his mom Sarah" → "his mom [NAME]" ✓

---

### 2. Appositive Patterns

**Target:** `"the mom, Jessica"`, `"his dad - Mike"`, `"their guardian (Sarah)"`

**Punctuation Markers:**
- Comma: `, `
- Dash: ` - `, ` – `, ` — ` (hyphen, en-dash, em-dash)
- Parentheses: ` (`, ` (`

**Pattern Examples:**

```python
# "mom, " = 5 chars (3 + comma + space)
Pattern(
    name="mom_comma_name",
    regex=r"(?i)(?<=mom, )[a-z][a-z]+\b",
    score=0.85
)

# "mom - " = 6 chars (3 + space + dash + space)
Pattern(
    name="mom_dash_name",
    regex=r"(?i)(?<=mom - )[a-z][a-z]+\b",
    score=0.85
)

# "mom (" = 5 chars (3 + space + paren)
# Note: Need to escape the paren in lookbehind
Pattern(
    name="mom_paren_name",
    regex=r"(?i)(?<=mom \()[a-z][a-z]+\b",
    score=0.85
)
```

**Relationship Words to Cover:** Same as forward patterns (mom, dad, grandma, etc.)

**Punctuation to Cover:** `, `, ` - `, ` (` (3 variations)

**Estimated Patterns:** ~30 patterns (10 relationship words × 3 punctuation types)

**Output Preservation:** Lookbehind matches ONLY the name, so "the mom, Jessica" → "the mom, [NAME]" ✓

---

### 3. Cross-Sentence Patterns

**Target:** `"Grandma's here. Her name is Maria"`

**Challenge:** Standard Presidio patterns operate on single text blocks without sentence awareness.

**Two Approaches:**

#### Approach A: Single-Pattern with Optional Sentence Boundary

Use a pattern that allows an optional period/newline before "her name is":

```python
# Pattern allowing sentence break before "her name is"
Pattern(
    name="cross_sentence_guardian_name",
    regex=r"(?i)(?:grandma|mom|dad|guardian)(?:'s| is) (?:here|present|available)[.\s]+(?:her|his|their) name is ([a-z][a-z]+)\b",
    score=0.75  # Lower score due to complexity
)
```

**Issues:**
- This pattern captures the entire phrase, not just the name
- Difficult to preserve context words cleanly
- May not work with Presidio's entity extraction (expects name to be matched, not full phrase)

#### Approach B: Pre-processing with Sentence Detection

1. Use spaCy sentence segmentation to identify sentence boundaries
2. For adjacent sentences, check if second sentence contains "her name is [NAME]"
3. If previous sentence contains guardian reference, flag the name

**Issues:**
- Requires custom recognizer logic (not pure regex `PatternRecognizer`)
- More complex implementation
- May need to subclass `EntityRecognizer` instead of using `PatternRecognizer`

**Recommendation:** **DEFER cross-sentence patterns** to future phase if needed. Focus on possessive and appositive patterns first (simpler, higher ROI).

---

## Presidio PatternRecognizer Capabilities

### Key Features Used in Current Implementation

1. **Case-insensitive matching:** `(?i)` flag at pattern start
2. **Lookbehind assertions:** `(?<=pattern)` matches only after pattern (preserves context)
3. **Lookahead assertions:** `(?=pattern)` matches only before pattern
4. **Word boundaries:** `\b` ensures complete word match
5. **Score calibration:** Different confidence scores for different pattern types

### Technical Constraints

1. **Fixed-width lookbehind:** Python regex requires lookbehind to have fixed width
   - Cannot use `+`, `*`, `{n,m}` quantifiers
   - Cannot use alternation `|` with different lengths
   - Solution: Create separate patterns for each variation

2. **Entity type mapping:** All patterns in a recognizer map to same entity type
   - Guardian patterns → `GUARDIAN_NAME`
   - This is correct for our use case

3. **Context words:** Presidio can boost scores when context words appear nearby
   - Current: `["parent", "guardian", "family", "caregiver", "at bedside", "reached at", "contact"]`
   - Consider adding: `"his", "her", "their"` for possessive context

4. **Deny list filtering:** Applied AFTER pattern matching (from `app/config.py`)
   - Current guardian deny list: `["parent", "guardian", "caregiver", "family", "uh", "um", "at"]`
   - No changes needed for new patterns

---

## Implementation Recommendations

### Pattern Organization Strategy

Follow the current pattern organization in `pediatric.py`:

```python
guardian_patterns = [
    # =================================================================
    # Forward patterns: "Mom Jessica" (existing - score 0.85)
    # =================================================================
    # ... existing patterns ...

    # =================================================================
    # Possessive patterns: "his mom Sarah" (NEW - score 0.85)
    # =================================================================
    # Group 1: Standard possessive pronouns (his, her, their)
    Pattern(
        name="his_mom_name",
        regex=r"(?i)(?<=his mom )[a-z][a-z]+\b",
        score=0.85
    ),
    # ... (continue for all combinations) ...

    # Group 2: Clinical possessive forms (patient's, baby's, child's)
    Pattern(
        name="patients_mom_name",
        regex=r"(?i)(?<=patient's mom )[a-z][a-z]+\b",
        score=0.85
    ),
    # ... (continue for all combinations) ...

    # =================================================================
    # Appositive patterns: "mom, Jessica" (NEW - score 0.85)
    # =================================================================
    # Group 1: Comma appositives
    Pattern(
        name="mom_comma_name",
        regex=r"(?i)(?<=mom, )[a-z][a-z]+\b",
        score=0.85
    ),
    # ... (continue for all relationship words) ...

    # Group 2: Dash appositives
    Pattern(
        name="mom_dash_name",
        regex=r"(?i)(?<=mom - )[a-z][a-z]+\b",
        score=0.85
    ),
    # ... (continue for all relationship words) ...

    # Group 3: Parenthesis appositives
    Pattern(
        name="mom_paren_name",
        regex=r"(?i)(?<=mom \()[a-z][a-z]+\b",
        score=0.85
    ),
    # ... (continue for all relationship words) ...

    # =================================================================
    # Bidirectional patterns: "Jessica is Mom" (existing - score 0.80)
    # =================================================================
    # ... existing patterns ...

    # =================================================================
    # Speech artifacts: "mom uh Jessica" (existing - score 0.75)
    # =================================================================
    # ... existing patterns ...
]
```

### Score Calibration

**Recommended scores:**
- **Possessive patterns:** 0.85 (same as forward patterns)
  - Clear grammatical structure
  - Possessive pronoun + relationship word is strong signal
  - Example: "his mom Sarah" is unambiguous

- **Appositive patterns:** 0.85 (same as forward patterns)
  - Punctuation makes intent clear
  - Comma/dash after relationship word indicates name follows
  - Example: "the mom, Jessica" is unambiguous

- **Cross-sentence patterns (if implemented):** 0.75 (same as speech artifacts)
  - More complex pattern
  - Higher chance of false positives
  - Only implement if needed after testing possessive/appositive

### Context Words

Consider adding possessive pronouns to context list:

```python
guardian_recognizer = PatternRecognizer(
    supported_entity="GUARDIAN_NAME",
    name="Guardian Name Recognizer",
    patterns=guardian_patterns,
    context=[
        "parent", "guardian", "family", "caregiver",
        "at bedside", "reached at", "contact",
        # NEW: possessive context
        "his", "her", "their", "patient's", "baby's"
    ]
)
```

---

## Testing Strategy

### Unit Tests (Add to `test_presidio.py`)

```python
# Possessive patterns
{
    "name": "Guardian - possessive his mom",
    "input": "His mom Sarah is at bedside.",
    "must_redact": ["Sarah"],
    "must_preserve": ["His", "mom", "bedside"],
},
{
    "name": "Guardian - possessive her dad",
    "input": "Her dad Tom works nights.",
    "must_redact": ["Tom"],
    "must_preserve": ["Her", "dad", "works"],
},
{
    "name": "Guardian - possessive their grandma",
    "input": "Their grandma Maria helps with care.",
    "must_redact": ["Maria"],
    "must_preserve": ["Their", "grandma", "care"],
},
{
    "name": "Guardian - possessive patient's mom",
    "input": "The patient's mom Jessica brought supplies.",
    "must_redact": ["Jessica"],
    "must_preserve": ["patient's", "mom", "brought"],
},

# Appositive patterns
{
    "name": "Guardian - appositive comma",
    "input": "The mom, Jessica, is at bedside.",
    "must_redact": ["Jessica"],
    "must_preserve": ["The", "mom", "bedside"],
},
{
    "name": "Guardian - appositive dash",
    "input": "His dad - Mike - works nights.",
    "must_redact": ["Mike"],
    "must_preserve": ["His", "dad", "works"],
},
{
    "name": "Guardian - appositive paren",
    "input": "Their guardian (Sarah) is available.",
    "must_redact": ["Sarah"],
    "must_preserve": ["Their", "guardian", "available"],
},
```

### Integration Tests (Add to `test_deidentification.py`)

Test realistic clinical handoffs:

```python
def test_guardian_possessive_patterns():
    """Test possessive guardian patterns in realistic context."""
    text = "Patient admitted with his mom Sarah at bedside. Her phone is 617-555-1234."
    result = deidentify_text(text)

    assert "Sarah" not in result.clean_text
    assert "his mom" in result.clean_text.lower()
    assert "[NAME]" in result.clean_text or "[GUARDIAN_NAME]" in result.clean_text
    assert len(result.phi_entities) >= 2  # Guardian name + phone

def test_guardian_appositive_patterns():
    """Test appositive guardian patterns with punctuation."""
    text = "The mom, Jessica, brought medications from home."
    result = deidentify_text(text)

    assert "Jessica" not in result.clean_text
    assert "the mom" in result.clean_text.lower()
    assert "[NAME]" in result.clean_text or "[GUARDIAN_NAME]" in result.clean_text
```

---

## Pitfalls to Avoid

### 1. Variable-Width Lookbehind

**WRONG:**
```python
# This will fail - alternation in lookbehind has different widths
Pattern(
    regex=r"(?i)(?<=(?:his|her|their) mom )[a-z]+\b",  # ❌ INVALID
    ...
)
```

**RIGHT:**
```python
# Create separate patterns for each possessive length
Pattern(regex=r"(?i)(?<=his mom )[a-z][a-z]+\b", ...),  # 8 chars
Pattern(regex=r"(?i)(?<=her mom )[a-z][a-z]+\b", ...),  # 8 chars
Pattern(regex=r"(?i)(?<=their mom )[a-z][a-z]+\b", ...), # 10 chars
```

### 2. Capturing Groups in Patterns

**WRONG:**
```python
# Capturing group changes what Presidio extracts
Pattern(
    regex=r"(?i)his mom ([a-z]+)\b",  # ❌ Captures "his mom Sarah"
    ...
)
```

**RIGHT:**
```python
# Lookbehind ensures only name is matched
Pattern(
    regex=r"(?i)(?<=his mom )[a-z][a-z]+\b",  # ✓ Matches only "Sarah"
    ...
)
```

### 3. Overly Aggressive Patterns

**WRONG:**
```python
# This would flag "his name is Mike" even without relationship word
Pattern(
    regex=r"(?i)(?<=his )[a-z][a-z]+\b",  # ❌ Too broad
    ...
)
```

**RIGHT:**
```python
# Require relationship word to reduce false positives
Pattern(
    regex=r"(?i)(?<=his mom )[a-z][a-z]+\b",  # ✓ More specific
    ...
)
```

### 4. Minimum Name Length

All current patterns use `[a-z][a-z]+` which requires **minimum 2 characters**. This is good for avoiding single-letter false positives (e.g., initials).

**Keep this constraint:**
```python
regex=r"(?i)(?<=mom )[a-z][a-z]+\b",  # Minimum 2 chars
```

### 5. Escape Special Characters in Lookbehind

When using punctuation in lookbehind, escape regex special characters:

```python
# Parenthesis must be escaped
Pattern(regex=r"(?i)(?<=mom \()[a-z][a-z]+\b", ...),  # ✓ Escaped paren

# Dash is safe (not special in lookbehind context)
Pattern(regex=r"(?i)(?<=mom - )[a-z][a-z]+\b", ...),  # ✓ Dash OK
```

---

## Pattern Coverage Matrix

### Possessive Patterns

| Possessive Pronoun | Relationship Word | Fixed Width | Priority |
|-------------------|------------------|-------------|----------|
| his | mom, dad, grandma, etc. | 8-12 chars | **HIGH** |
| her | mom, dad, grandma, etc. | 8-12 chars | **HIGH** |
| their | mom, dad, grandma, etc. | 10-14 chars | **HIGH** |
| patient's | mom, dad, guardian | 14-18 chars | MEDIUM |
| baby's | mom, dad | 11-13 chars | MEDIUM |
| child's | mom, dad | 12-14 chars | LOW |

**Total:** ~50 patterns for comprehensive coverage

### Appositive Patterns

| Punctuation | Relationship Words | Fixed Width | Priority |
|------------|-------------------|-------------|----------|
| , (comma) | mom, dad, grandma, etc. | 5-9 chars | **HIGH** |
| - (dash) | mom, dad, grandma, etc. | 6-10 chars | MEDIUM |
| ( (paren) | mom, dad, guardian | 5-9 chars | LOW |

**Total:** ~30 patterns for comprehensive coverage

### Cross-Sentence Patterns

**Recommendation:** DEFER to future phase. Requires more complex implementation.

---

## Performance Considerations

### Pattern Count

Current guardian recognizer has **~40 patterns**. Adding:
- Possessive: +50 patterns
- Appositive: +30 patterns
- **Total: ~120 patterns** in guardian recognizer

**Impact:** Presidio evaluates patterns sequentially. 120 patterns is manageable (still < 200).

### Regex Compilation

Presidio compiles all patterns once at startup. No runtime performance impact.

### False Positive Risk

**Mitigation strategies:**
1. Require relationship word (prevents "his Sarah" without context)
2. Maintain deny list filtering (prevents "his at" or "mom uh")
3. Use same confidence scores as existing patterns (0.85)
4. Test extensively with realistic handoffs

---

## Success Metrics

### Recall Improvement Target

Current GUARDIAN_NAME recall: Unknown (not in Phase 2 baseline report)

**Expected improvement:**
- Possessive patterns: +10-15% recall (common in clinical speech)
- Appositive patterns: +5-10% recall (less common, but unambiguous when present)
- **Total expected: +15-25% recall improvement**

### Precision Maintenance

**Target:** No new false positives

**Validation:**
- Run full test suite (21 existing tests + new tests)
- Validate on 27 real handoff transcripts
- Check deny list coverage

### Test Coverage

**Minimum test cases:**
- 3-4 possessive pattern tests (different pronouns)
- 2-3 appositive pattern tests (different punctuation)
- 1-2 integration tests with realistic handoffs
- **Total: 6-9 new tests**

---

## Implementation Phases (Recommendation for Planner)

### Phase 18-01: Possessive Pattern Implementation
**Scope:** Implement "his mom Sarah" style patterns
**Why first:** Highest ROI, most common in clinical speech
**Estimated patterns:** ~50
**Test cases:** 3-4

### Phase 18-02: Appositive Pattern Implementation
**Scope:** Implement "mom, Jessica" style patterns
**Why second:** Lower frequency, but unambiguous signal
**Estimated patterns:** ~30
**Test cases:** 2-3

### Phase 18-03: Validation & Recall Measurement
**Scope:** Run full validation, measure recall improvement
**Why third:** Confirm patterns work before considering cross-sentence
**Deliverable:** Recall improvement report

### Phase 18-04 (Optional): Cross-Sentence Patterns
**Scope:** Only if recall gap still exists after 18-03
**Why last:** Most complex, lowest ROI
**Decision gate:** Defer if recall targets met

---

## Code Examples

### Pattern Template for Possessive

```python
# Template for generating possessive patterns
POSSESSIVE_PRONOUNS = ["his", "her", "their"]
RELATIONSHIP_WORDS = ["mom", "dad", "grandma", "grandpa", "guardian"]

# Calculate lookbehind width
def generate_possessive_pattern(pronoun: str, relationship: str) -> Pattern:
    """Generate a possessive guardian pattern."""
    lookbehind = f"{pronoun} {relationship} "
    width = len(lookbehind)

    return Pattern(
        name=f"{pronoun}_{relationship}_name",
        regex=f"(?i)(?<={lookbehind})[a-z][a-z]+\\b",
        score=0.85
    )

# Generate all combinations
possessive_patterns = [
    generate_possessive_pattern(p, r)
    for p in POSSESSIVE_PRONOUNS
    for r in RELATIONSHIP_WORDS
]
```

### Pattern Template for Appositive

```python
# Template for generating appositive patterns
PUNCTUATION = [", ", " - ", " ("]
RELATIONSHIP_WORDS = ["mom", "dad", "grandma", "grandpa", "guardian"]

def generate_appositive_pattern(relationship: str, punct: str) -> Pattern:
    """Generate an appositive guardian pattern."""
    # Escape special regex characters in punctuation
    escaped_punct = punct.replace("(", r"\(").replace(")", r"\)")
    lookbehind = f"{relationship}{escaped_punct}"

    punct_name = {", ": "comma", " - ": "dash", " (": "paren"}[punct]

    return Pattern(
        name=f"{relationship}_{punct_name}_name",
        regex=f"(?i)(?<={lookbehind})[a-z][a-z]+\\b",
        score=0.85
    )

# Generate all combinations
appositive_patterns = [
    generate_appositive_pattern(r, p)
    for r in RELATIONSHIP_WORDS
    for p in PUNCTUATION
]
```

---

## Next Steps for Planner

1. **Create Plan 18-01:** Implement possessive patterns
   - Add ~50 patterns to `app/recognizers/pediatric.py`
   - Add 3-4 unit tests to `test_presidio.py`
   - Add 1-2 integration tests to `test_deidentification.py`

2. **Create Plan 18-02:** Implement appositive patterns
   - Add ~30 patterns to `app/recognizers/pediatric.py`
   - Add 2-3 unit tests to `test_presidio.py`
   - Update context words if needed

3. **Create Plan 18-03:** Validation and recall measurement
   - Run full test suite
   - Validate on 27 real handoffs
   - Measure GUARDIAN_NAME recall improvement
   - Document results

4. **Decision:** Cross-sentence patterns needed?
   - If recall gap still exists, create Plan 18-04
   - Otherwise, mark Phase 18 complete

---

## References

- **Presidio Pattern Recognizer docs:** Uses Python `re` module regex syntax
- **Python regex lookbehind:** Must be fixed width (no `+`, `*`, `{n,m}`)
- **Current implementation:** `app/recognizers/pediatric.py` lines 45-231
- **Test harness:** `test_presidio.py` for fast validation
- **Full test suite:** `test_deidentification.py` for integration tests

---

**Research complete.** Ready for planning phase.
