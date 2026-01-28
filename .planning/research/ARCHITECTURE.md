# Architecture Research: Deny List Integration

**Research Date:** 2026-01-28
**Project:** Pediatric Handoff PHI Remover - Over-Detection Fix
**Researcher:** GSD Project Researcher
**Confidence:** HIGH

---

## Executive Summary

The existing Presidio-based architecture already has the right structure for deny list expansion. The current issue is **inconsistent matching strategies** across entity types (exact vs substring) and **incomplete deny list coverage** for medical abbreviations. The fix is straightforward: normalize to substring matching for LOCATION (like DATE_TIME), expand deny lists with medical context terms, and integrate test scripts into existing pytest framework.

**Key Finding:** No fundamental architecture changes needed. This is a configuration and test integration problem, not a design problem.

---

## 1. Matching Strategy Analysis

### Current Implementation (Inconsistent)

From `deidentification.py` lines 185-210:

| Entity Type | Current Match | Code Example |
|-------------|---------------|--------------|
| **LOCATION** | **Exact match** | `detected_text.lower() in [w.lower() for w in deny_list]` |
| **DATE_TIME** | **Substring match** | `any(term.lower() in detected_lower for term in deny_list)` |
| **PERSON** | **Exact match** | `detected_text.lower() in [w.lower() for w in deny_list]` |
| **GUARDIAN_NAME** | **Exact match** | `detected_text.lower() in [w.lower() for w in deny_list]` |
| **PEDIATRIC_AGE** | **Exact match** | `detected_text.lower() in [w.lower() for w in deny_list]` |

### Problem: "placed on high" Won't Match "high" Deny List Entry

The user's example perfectly illustrates the issue:
- Presidio detects "high" as LOCATION (lowercase)
- "placed on high" contains "high" but isn't an exact match
- Current LOCATION deny list uses exact matching: `"high" in ["high", "nc", "ra"]` = **False**
- Should use substring: `"high" in "placed on high"` = **True**

### Recommendation: Normalize to Substring Matching

**Change LOCATION, PERSON, GUARDIAN_NAME, PEDIATRIC_AGE to substring matching like DATE_TIME.**

**Rationale:**
1. **Medical abbreviations appear in phrases**: "on high flow", "placed on NC", "patient high risk"
2. **Consistency**: All deny lists use same logic (easier to understand, maintain)
3. **Precedent**: DATE_TIME already uses substring successfully (lines 204-210)
4. **Safety**: Over-filtering is safer than false positives in HIPAA context

**Implementation:**

```python
# Current (LOCATION) - EXACT MATCH
if result.entity_type == "LOCATION" and detected_text.lower() in [w.lower() for w in settings.deny_list_location]:
    continue

# Proposed (LOCATION) - SUBSTRING MATCH
if result.entity_type == "LOCATION":
    detected_lower = detected_text.lower()
    if any(term.lower() in detected_lower for term in settings.deny_list_location):
        logger.debug(f"Filtered out deny-listed LOCATION: {detected_text}")
        continue

# Same pattern for PERSON, GUARDIAN_NAME, PEDIATRIC_AGE
```

### Risk Analysis: Substring Matching Concerns

**Potential Issue:** Could substring matching over-filter legitimate PHI?

**Example Risk Scenario:**
- Deny list contains "high" (for "high flow")
- Patient last name is "Higham"
- Substring match: "high" in "higham" = True → Would filter out PHI ❌

**Mitigation Strategy:**
1. **Word boundary checking**: Use regex `\bhigh\b` instead of substring
2. **Length filtering**: Only filter if detected text ≥ X chars longer than deny term
3. **Case preservation**: Only filter if detected is lowercase or uppercase (not Title Case for names)

**Recommended Approach (Safest):**

```python
def _is_deny_listed_substring(detected: str, deny_list: list[str]) -> bool:
    """
    Check if detected text contains deny-listed term as whole word.

    Uses word boundaries to avoid over-filtering (e.g., "high" in "Higham").
    """
    import re
    detected_lower = detected.lower()

    for term in deny_list:
        # Exact match (fast path)
        if detected_lower == term.lower():
            return True

        # Word boundary match (e.g., "on high flow" matches "high")
        pattern = r'\b' + re.escape(term.lower()) + r'\b'
        if re.search(pattern, detected_lower):
            return True

    return False
```

**This approach:**
- ✅ Matches "high" in "on high flow" (word boundary)
- ❌ Does NOT match "high" in "Higham" (no word boundary)
- ✅ Matches "NC" in "placed on NC" (word boundary)
- ❌ Does NOT match "NC" in "NICU" (no word boundary)

---

## 2. Deny List Expansion Strategy

### Current Deny Lists (from config.py)

| Entity Type | Count | Examples |
|-------------|-------|----------|
| **deny_list_location** | 14 | NC, RA, OR, ER, ED, IV, PO, IM, SQ, PR, GT, NG, OG, NJ |
| **deny_list_person** | 24 | mom, dad, baby, infant, DKA, CT, MRI, ICU, PICU, NICU |
| **deny_list_guardian_name** | 6 | parent, guardian, caregiver, family, uh, um |
| **deny_list_pediatric_age** | 7 | infant, toddler, child, adolescent, teen, newborn, neonate |
| **deny_list_date_time** | 32 | today, yesterday, q4h, BID, TID, day 1, dol 1, weeks old |

### Proposed Additions (from user context + medical domain knowledge)

**LOCATION additions (medical context terms):**
- `"high"` - "high flow", "high risk" (user's specific issue)
- `"low"` - "low flow", "low risk"
- `"room"` - "room air" abbreviation (already have "RA")
- `"bed"` - "bed rest", "bed assignment" (context-dependent, may be room number)
- `"unit"` - "unit policy" (but could be "PICU bed 3" context - SKIP)
- `"air"` - "room air"
- `"flow"` - "high flow", "low flow"

**CAUTION:** Terms like "bed" and "room" can be PHI context (room numbers). Need careful testing.

**DATE_TIME additions (clinical timeline terms):**
- `"day"` - Generic day references (already have "day 1", "days old")
- `"week"` - Generic week references (already have "weeks old")
- `"month"` - Generic month references (already have "months old")
- These are already covered by existing patterns ("days old", "weeks old", etc.)

**PERSON additions (more medical abbreviations):**
- Already comprehensive (24 entries)
- Consider: `"PT"` (Physical Therapy vs patient initials - context-dependent)
- Consider: `"OT"` (Occupational Therapy vs other - context-dependent)

### Recommendation: Conservative Expansion

**Add to deny_list_location:**
```python
deny_list_location: list[str] = Field(
    default=[
        # Medical abbreviations (existing)
        "NC", "RA", "OR", "ER", "ED", "IV", "PO", "IM", "SQ", "PR", "GT", "NG", "OG", "NJ",
        # Descriptive terms (Phase 6 expansion - 2026-01-28)
        "high",      # "high flow", "on high", "high risk"
        "low",       # "low flow", "low risk"
        "air",       # "room air", "on air"
        "flow",      # "high flow", "low flow"
    ],
    description="Medical abbreviations and context terms not flagged as LOCATION"
)
```

**Rationale:**
- Addresses user's specific "placed on high" issue
- Adds symmetric "low" for consistency
- Adds "air" and "flow" to catch full phrases
- Word boundary matching (recommended above) prevents over-filtering

---

## 3. Test Script Organization

### Existing Test Infrastructure

**From Glob results:**
```
tests/
├── __init__.py
├── test_deidentification.py      # Pytest unit tests
├── test_weighted_metrics.py      # Phase 8 metrics
├── test_presidio.py               # Root-level isolated harness
├── generate_test_data.py          # Synthetic handoff generator
├── validation_dataset.py          # Real transcript loader
├── evaluate_presidio.py           # Evaluation framework
├── error_taxonomy.py              # False negative classification
├── calibrate_thresholds.py        # Threshold optimization
├── check_thresholds.py            # Threshold validation
├── run_validation.py              # Validation runner
├── annotation_schema.py           # Human annotation format
├── handoff_templates.py           # I-PASS templates
├── medical_providers.py           # Synthetic provider data
└── sample_transcripts.py          # Sample test data
```

**Root-level test harness:**
```
test_presidio.py                   # Isolated test (21 cases)
```

### Integration Approach: pytest Framework

**Current Status:**
- ✅ `pytest tests/` runs unit tests
- ✅ `test_presidio.py` runs isolated harness (21 test cases)
- ⚠️ `test_presidio.py` is NOT in `tests/` directory (inconsistent location)

**Recommendation: Move to pytest framework**

**Actions:**
1. **Move** `test_presidio.py` → `tests/test_presidio_harness.py`
2. **Convert** standalone script to pytest format
3. **Integrate** known issues as `pytest.mark.xfail` fixtures

**Before (standalone script):**
```python
# test_presidio.py (root level)
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-i":
        interactive_test()
    else:
        success = run_tests(strict=False)
        sys.exit(0 if success else 1)
```

**After (pytest integration):**
```python
# tests/test_presidio_harness.py
import pytest
from app.deidentification import deidentify_text

# Known issues tracked as xfail
@pytest.mark.xfail(reason="Over-redacts 'bed' - tracked in Phase 6")
def test_baby_lastname_with_bed():
    """Patient name - Baby LastName (known issue)"""
    result = deidentify_text("This is Baby Smith in bed 4.")
    clean = result.clean_text

    # Must redact
    assert "Smith" not in clean.lower()
    assert "4" not in clean  # Bed number is PHI

    # Must preserve
    assert "Baby" in clean
    assert "bed" in clean.lower()  # Currently fails - over-redacts

@pytest.mark.parametrize("input_text,must_redact,must_preserve", [
    # Standard patient name
    ("Patient John Williams admitted today.",
     ["John Williams"],
     ["Patient", "admitted"]),

    # Guardian with name
    ("Mom Jessica is at bedside.",
     ["Jessica"],
     ["Mom", "bedside"]),

    # ... etc.
])
def test_presidio_cases(input_text, must_redact, must_preserve):
    """Parametrized test for all harness cases"""
    result = deidentify_text(input_text)
    clean = result.clean_text

    for item in must_redact:
        assert item.lower() not in clean.lower(), f"Missed redacting: {item}"

    for item in must_preserve:
        assert item.lower() in clean.lower(), f"Over-redacted: {item}"
```

**Benefits:**
- ✅ Single test command: `pytest tests/ -v`
- ✅ Known issues tracked with `@pytest.mark.xfail`
- ✅ Parametrized tests reduce duplication
- ✅ Integrates with CI/CD (GitHub Actions already runs pytest)
- ✅ Coverage reporting: `pytest --cov=app tests/`

### Test File Organization (Recommended)

```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures (add if needed)
│
├── unit/                          # Unit tests
│   ├── test_deidentification.py  # Core de-ID logic
│   └── test_weighted_metrics.py  # Metrics calculations
│
├── integration/                   # Integration tests
│   ├── test_presidio_harness.py  # 21-case harness (MOVE HERE)
│   ├── test_validation.py        # Validation workflow
│   └── test_e2e_transcription.py # Full pipeline test
│
├── fixtures/                      # Test data and helpers
│   ├── generate_test_data.py     # Synthetic handoff generator
│   ├── validation_dataset.py     # Real transcript loader
│   ├── sample_transcripts.py     # Sample test data
│   ├── handoff_templates.py      # I-PASS templates
│   └── medical_providers.py      # Synthetic provider data
│
└── evaluation/                    # Evaluation scripts (not tests)
    ├── evaluate_presidio.py       # Evaluation framework
    ├── calibrate_thresholds.py    # Threshold optimization
    ├── check_thresholds.py        # Threshold validation
    ├── run_validation.py          # Validation runner
    ├── error_taxonomy.py          # False negative classification
    └── annotation_schema.py       # Human annotation format
```

**Rationale:**
- Clear separation: unit vs integration vs evaluation
- Fixtures in separate directory (not tests)
- Evaluation scripts stay as scripts (not pytest tests)
- Consistent `pytest tests/` command runs all tests

---

## 4. Build Order Recommendation

Based on architecture analysis, here's the optimal sequence:

### Phase 1: Deny List Expansion (2-3 hours)
**Location:** `app/config.py`
**Changes:**
1. Add new terms to `deny_list_location` ("high", "low", "air", "flow")
2. Document rationale in field description

**Testing:**
- Manual: `python test_presidio.py` (current location)
- Should see "placed on high" case pass

**Risk:** LOW (additive change, no logic changes)

---

### Phase 2: Matching Strategy Fix (3-4 hours)
**Location:** `app/deidentification.py` lines 185-210
**Changes:**
1. Implement `_is_deny_listed_substring()` helper with word boundary checking
2. Update LOCATION filter to use substring matching (line 185)
3. Update PERSON filter to use substring matching (line 190)
4. Update GUARDIAN_NAME filter (line 195)
5. Update PEDIATRIC_AGE filter (line 200)
6. Keep DATE_TIME as-is (already substring)

**Testing:**
- Unit test new `_is_deny_listed_substring()` function
- Run `test_presidio.py` to verify no regressions
- Specific tests:
  - "placed on high" → filters "high"
  - "Patient Higham" → does NOT filter (word boundary)
  - "on NC" → filters "NC"
  - "NICU bed 3" → does NOT filter "NC" (no word boundary in "NICU")

**Risk:** MEDIUM (changes core filtering logic)

---

### Phase 3: Test Integration to pytest (4-6 hours)
**Location:** `tests/` directory structure
**Changes:**
1. Create `tests/integration/` directory
2. Move `test_presidio.py` → `tests/integration/test_presidio_harness.py`
3. Convert to pytest format:
   - Replace `if __name__ == "__main__"` with pytest functions
   - Convert TEST_CASES list to `@pytest.mark.parametrize`
   - Mark KNOWN_ISSUES as `@pytest.mark.xfail`
4. Update README/documentation with new test command
5. (Optional) Reorganize other test files per recommended structure

**Testing:**
- `pytest tests/ -v` (all tests pass)
- `pytest tests/integration/ -v` (harness tests pass)
- `pytest -m xfail` (known issues marked correctly)

**Risk:** LOW (organizational change, not logic changes)

---

### Recommended Sequence (Why This Order)

1. **Deny List First:** Quick win, addresses user's immediate issue, low risk
2. **Matching Strategy Second:** Enables deny list expansion to work properly
3. **Test Integration Last:** Organizational improvement, validates Phases 1-2

**Parallel Work Opportunity:**
- Phase 1 and Phase 2 can be done in same session (both in `deidentification.py`)
- Phase 3 is independent organizational work

**Integration Points:**
- After Phase 1: User can manually test "placed on high" case
- After Phase 2: All deny list filtering consistent, easier to reason about
- After Phase 3: CI/CD catches regressions automatically

---

## 5. Risks and Mitigation

### Risk 1: Substring Matching Over-Filters PHI

**Scenario:** "high" deny list entry filters "Higham" (patient last name)

**Likelihood:** MEDIUM (common issue with substring matching)

**Impact:** HIGH (PHI leak if name doesn't get redacted elsewhere)

**Mitigation:**
1. ✅ **Word boundary checking** (recommended approach above)
2. ✅ **Case checking**: Only filter lowercase/uppercase, not TitleCase (names)
3. ✅ **Comprehensive testing**: Add "Higham", "Hickman", "Highland" test cases
4. ✅ **Fallback to spaCy**: Even if deny list filters, spaCy NER should catch names

**Implementation:**
```python
def _is_deny_listed_substring(detected: str, deny_list: list[str]) -> bool:
    """Safe substring matching with word boundaries."""
    import re
    detected_lower = detected.lower()

    for term in deny_list:
        # Exact match
        if detected_lower == term.lower():
            return True

        # Word boundary match only
        pattern = r'\b' + re.escape(term.lower()) + r'\b'
        if re.search(pattern, detected_lower):
            return True

    return False
```

---

### Risk 2: Word Boundary Logic Misses Edge Cases

**Scenario:** "high-flow" (hyphenated) doesn't match "high" word boundary

**Likelihood:** MEDIUM (punctuation variations are common)

**Impact:** LOW (false positive, not PHI leak)

**Mitigation:**
1. ✅ **Test with punctuation**: "high-flow", "high/low", "high:flow"
2. ✅ **Expand deny list**: Add "high-flow" as explicit entry if needed
3. ✅ **Regex improvement**: `\b` doesn't work with hyphens, consider `(?<!\w)high(?!\w)`

**Alternative regex for non-alphanumeric boundaries:**
```python
# Instead of \b (word boundary)
pattern = r'(?<!\w)' + re.escape(term.lower()) + r'(?!\w)'
```

This matches:
- ✅ "high flow" (space boundary)
- ✅ "high-flow" (hyphen boundary)
- ✅ "(high)" (parenthesis boundary)
- ❌ "Higham" (alphanumeric, no boundary)

---

### Risk 3: Test Migration Breaks CI/CD

**Scenario:** Moving `test_presidio.py` breaks existing test commands in CI/CD

**Likelihood:** LOW (assuming CI/CD uses `pytest tests/`)

**Impact:** LOW (CI/CD pipeline fails, easy to fix)

**Mitigation:**
1. ✅ Check `.github/workflows/` for existing test commands
2. ✅ Keep both locations during migration (deprecate old one)
3. ✅ Update documentation first, then move file
4. ✅ Run CI/CD locally with `act` (GitHub Actions local runner) before pushing

---

## 6. Success Criteria

### Phase 1 Success (Deny List Expansion)
- [ ] `deny_list_location` contains "high", "low", "air", "flow"
- [ ] Field description documents rationale
- [ ] Manual test: "placed on high" → "high" filtered
- [ ] No regressions: All existing test cases still pass

---

### Phase 2 Success (Matching Strategy Fix)
- [ ] `_is_deny_listed_substring()` implemented with word boundary checking
- [ ] All 5 entity types use substring matching (LOCATION, PERSON, GUARDIAN_NAME, PEDIATRIC_AGE, DATE_TIME)
- [ ] Unit tests for word boundary logic pass
- [ ] Edge case tests pass:
  - [ ] "placed on high" → "high" filtered (substring match)
  - [ ] "Patient Higham" → "Higham" NOT filtered (word boundary)
  - [ ] "on NC" → "NC" filtered (substring match)
  - [ ] "NICU bed 3" → "NICU" NOT filtered (no word boundary)
  - [ ] "high-flow" → "high" filtered (non-alphanumeric boundary)
- [ ] Zero PHI leaks in validation run

---

### Phase 3 Success (Test Integration)
- [ ] `tests/integration/test_presidio_harness.py` exists
- [ ] Root-level `test_presidio.py` deprecated (README updated)
- [ ] `pytest tests/ -v` runs all tests (21+ cases)
- [ ] Known issues marked with `@pytest.mark.xfail`
- [ ] CI/CD integration verified (GitHub Actions passes)
- [ ] Coverage report includes harness tests
- [ ] README documents: `pytest tests/integration/` command

---

## 7. Alternative Approaches Considered

### Alternative 1: Move Deny Lists to Presidio Recognizer Context

**From existing ARCHITECTURE.md research (lines 263-279):**

Presidio's `PatternRecognizer` supports built-in deny lists:
```python
PatternRecognizer(
    supported_entity="LOCATION",
    deny_list=settings.deny_list_location  # Built-in Presidio feature
)
```

**Pros:**
- ✅ Better performance (filter during detection, not post-processing)
- ✅ Cleaner architecture (deny list owned by recognizer)

**Cons:**
- ❌ More invasive change (modifies recognizer definitions)
- ❌ Requires testing all custom recognizers
- ❌ Less flexible (can't easily A/B test deny lists)

**Decision:** DEFER to Phase 7 (Performance Optimization)
**Rationale:** Current post-filter approach works and is easier to test. Optimization can come later after correctness proven.

---

### Alternative 2: Regex-Based Deny Lists in Recognizers

**Approach:** Define deny list patterns directly in regex patterns with negative lookahead:
```python
Pattern(
    name="location_no_medical_abbrev",
    regex=r"\b(?!NC|RA|OR|ER|high|low)[A-Z][a-z]+\b",
    score=0.5
)
```

**Pros:**
- ✅ Maximum performance (single regex pass)
- ✅ No post-filtering needed

**Cons:**
- ❌ Complex regex maintenance (negative lookahead for every term)
- ❌ Case sensitivity handling in regex
- ❌ Hard to understand and debug

**Decision:** REJECT
**Rationale:** Maintainability trumps micro-optimization. Current deny list in `config.py` is clear and testable.

---

### Alternative 3: Machine Learning Classifier for False Positives

**Approach:** Train a binary classifier (e.g., logistic regression) on:
- Input: (detected_text, entity_type, context_words, confidence_score)
- Output: is_false_positive (True/False)

**Pros:**
- ✅ Learns from data (no manual deny list maintenance)
- ✅ Handles novel patterns automatically

**Cons:**
- ❌ Requires labeled training data (100+ examples)
- ❌ Inference latency (model prediction per detection)
- ❌ Explainability issues (hard to debug false positive decisions)
- ❌ Overkill for current problem size (14-term deny list)

**Decision:** REJECT (for now)
**Rationale:** Rule-based deny lists are sufficient for current scale. ML approach could be Phase 9+ research spike.

---

## 8. Confidence Assessment

| Area | Confidence | Rationale |
|------|------------|-----------|
| **Matching Strategy** | HIGH | Substring with word boundaries is proven approach (DATE_TIME already uses it successfully) |
| **Deny List Expansion** | HIGH | Conservative additions ("high", "low") address user's issue with minimal risk |
| **Word Boundary Logic** | MEDIUM | Edge cases with punctuation need thorough testing |
| **Test Integration** | HIGH | Standard pytest patterns, existing CI/CD infrastructure in place |
| **Risk Assessment** | HIGH | Identified key risks (over-filtering names) with clear mitigation (word boundaries) |

**Overall Confidence:** HIGH

---

## 9. Sources

**Internal Documentation:**
- `.planning/research/ARCHITECTURE.md` (Phase 0 research, 2026-01-23)
- `app/config.py` (lines 95-197, deny list definitions)
- `app/deidentification.py` (lines 185-210, current filtering logic)
- `test_presidio.py` (lines 1-287, test harness structure)
- `tests/error_taxonomy.py` (false negative classification patterns)
- `app/recognizers/pediatric.py` (lookbehind pattern examples)

**External Research (from previous ARCHITECTURE.md):**
- [Presidio Best Practices](https://microsoft.github.io/presidio/analyzer/developing_recognizers/)
- [Databricks PHI Removal Guide](https://www.databricks.com/blog/2022/06/22/automating-phi-removal-from-healthcare-data-with-natural-language-processing.html)
- [Python regex word boundaries](https://docs.python.org/3/library/re.html#regular-expression-syntax)

---

**End of Research Document**
