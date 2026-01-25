# Phase 3: Deny List Refinement - Research

**Researched:** 2026-01-23
**Domain:** Medical vocabulary deny lists and case-insensitive filtering for NER systems
**Confidence:** HIGH

## Summary

Phase 3 reduces false positives through expanded medical vocabulary deny lists with consistent case handling. Research confirms that deny lists are the **industry-standard approach** for filtering out domain-specific false positives in medical NLP, where clinical abbreviations (NC, OR, ER) are systematically misclassified as PHI by general-purpose NER models.

**Primary recommendation:** Fix case-insensitive matching bug in LOCATION deny list (currently exact match only), expand medical abbreviation coverage based on false positive evidence from testing, and create deny lists for GUARDIAN_NAME and PEDIATRIC_AGE entity types.

**Key finding:** The codebase already implements deny list filtering in `deidentification.py` (lines 185-192), but has an **inconsistency bug**: PERSON deny list uses case-insensitive matching (`detected_text.lower() in [w.lower() for w in settings.deny_list_person]`), while LOCATION deny list uses exact match (`detected_text in settings.deny_list_location`). This causes "NC" to be filtered but "nc" to leak through.

**Expected impact:** Precision improvement from 87.4% to >90% (reducing 354 DATE_TIME false positives and clinical abbreviation over-redaction).

## Standard Stack

### Core Approach

**Deny List Pattern (Medical NLP Standard):**
```python
# Source: Existing implementation in app/deidentification.py
# Pattern is standard across medical NER systems (2020-present)

# Step 1: Collect all detected entities from NER
raw_results = analyzer.analyze(text, threshold=0.0)

# Step 2: Filter by deny list BEFORE applying confidence threshold
filtered = []
for result in raw_results:
    detected_text = text[result.start:result.end].strip()

    # Case-insensitive matching (STANDARD)
    if result.entity_type == "LOCATION":
        if detected_text.lower() in [w.lower() for w in deny_list_location]:
            continue  # Skip this false positive

    if result.entity_type == "PERSON":
        if detected_text.lower() in [w.lower() for w in deny_list_person]:
            continue

    # Apply confidence threshold
    if result.score >= threshold:
        filtered.append(result)
```

**No external libraries needed** - Pure Python list/string operations are sufficient and performant.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| List-based deny lists | Regex patterns for abbreviations | More complex, harder to maintain, same performance |
| Case-insensitive matching | Exact match | Misses lowercase variants ("nc" vs "NC"), creates bugs |
| Hardcoded in config.py | External JSON/CSV file | Extra I/O overhead, no benefit for <50 terms |
| Per-entity deny lists | Global deny list | Type confusion (e.g., "OR" = operating room vs Oregon state) |

**Recommendation:** Keep current architecture (list-based, in config.py, per-entity) but fix case normalization bug.

## Architecture Patterns

### Pattern 1: Case-Insensitive Deny List Matching

**What:** Normalize both the detected text and deny list to lowercase before comparison

**When to use:** All deny list comparisons (standard practice in medical NLP)

**Why:** Clinical text uses inconsistent capitalization ("NC", "nc", "Nc" all mean nasal cannula)

**Current bug location:**
```python
# File: app/deidentification.py, line 185
# BUG: Exact match - misses lowercase variants
if result.entity_type == "LOCATION" and detected_text in settings.deny_list_location:
    logger.debug(f"Filtered out deny-listed LOCATION: {detected_text}")
    continue

# File: app/deidentification.py, line 190
# CORRECT: Case-insensitive
if result.entity_type == "PERSON" and detected_text.lower() in [w.lower() for w in settings.deny_list_person]:
    logger.debug(f"Filtered out deny-listed PERSON: {detected_text}")
    continue
```

**Fix:**
```python
# Standardize LOCATION deny list matching
if result.entity_type == "LOCATION":
    if detected_text.lower() in [w.lower() for w in settings.deny_list_location]:
        logger.debug(f"Filtered out deny-listed LOCATION: {detected_text}")
        continue
```

### Pattern 2: Evidence-Based Deny List Expansion

**What:** Add terms to deny list ONLY when false positive is documented in test cases

**When to use:** Expanding medical abbreviation coverage

**Why:** Prevents bloat, ensures every term has a clear rationale

**Process:**
1. Run evaluation on synthetic dataset
2. Review false positives (entities flagged as PHI but are clinical terms)
3. Add false positive to deny list
4. Add regression test case
5. Document rationale in config.py comment

**Example from Phase 2 calibration:**
```
DATE_TIME false positives (354 total):
- "q4h", "BID", "PRN" (dosing schedules, not timestamps)
- "today", "tonight", "yesterday" (generic time references)

LOCATION false positives (from testing):
- "NC" (nasal cannula, already in deny list)
- "OR" (operating room, already in deny list)
- "IV", "PO", "IM" (routes of administration, already in deny list)
```

**Phase 3 scope:** Verify existing deny lists are comprehensive, add any missing clinical abbreviations found in false positive analysis.

### Pattern 3: Per-Entity Deny Lists

**What:** Separate deny lists for each entity type (`deny_list_location`, `deny_list_person`, etc.)

**When to use:** When same term has different meanings in different contexts

**Why:** "OR" as location (operating room) vs "OR" as person name (hypothetical) need different handling

**Current implementation:**
```python
# app/config.py
deny_list_location: List[str] = Field(
    default=["NC", "RA", "OR", "ER", "ED", "IV", "PO", "IM", "SQ", "PR", "GT", "NG", "OG", "NJ"],
    description="Medical abbreviations that should not be flagged as LOCATION"
)

deny_list_person: List[str] = Field(
    default=["mom", "dad", "parent", "guardian", "nurse", "doctor", ...],
    description="Words that should not be flagged as PERSON"
)
```

**Phase 3 additions needed:**
```python
deny_list_guardian_name: List[str] = Field(
    default=[],  # TBD based on false positive analysis
    description="Terms that should not be flagged as GUARDIAN_NAME"
)

deny_list_pediatric_age: List[str] = Field(
    default=[],  # TBD based on false positive analysis
    description="Terms that should not be flagged as PEDIATRIC_AGE"
)

deny_list_date_time: List[str] = Field(
    default=["today", "tonight", "yesterday", "q4h", "BID", "TID", "QID", "PRN"],
    description="Generic time references and dosing schedules that should not be flagged as DATE_TIME"
)
```

### Pattern 4: Deny List Testing

**What:** Regression tests that verify deny list filtering works

**When to use:** Every time a deny list is expanded

**Why:** Ensure deny list entries actually prevent false positives

**Example test structure:**
```python
# tests/test_deidentification.py
class TestDenyLists:
    """Test deny list filtering."""

    @pytest.mark.parametrize("abbreviation", [
        "NC", "nc", "Nc",  # Case variants
        "RA", "OR", "ER", "IV", "PO"
    ])
    def test_medical_abbreviation_not_flagged_as_location(self, abbreviation):
        """Test that medical abbreviations are not flagged as LOCATION."""
        text = f"Patient on {abbreviation} oxygen at bedside."
        result = deidentify_text(text)

        # Abbreviation should be preserved (not redacted)
        assert abbreviation in result.clean_text or abbreviation.lower() in result.clean_text.lower()

        # Should not create a LOCATION entity
        location_entities = [e for e in result.entities_found if e.entity_type == "LOCATION"]
        assert len(location_entities) == 0

    @pytest.mark.parametrize("role_word", [
        "mom", "Mom", "MOM",  # Case variants
        "dad", "nurse", "doctor", "guardian"
    ])
    def test_role_words_not_flagged_as_person(self, role_word):
        """Test that standalone role words are not flagged as PERSON."""
        text = f"Contact {role_word} for updates on patient status."
        result = deidentify_text(text)

        # Role word should be preserved
        assert role_word in result.clean_text or role_word.lower() in result.clean_text.lower()

        # Should not create a PERSON entity for the role word
        # (Note: May still detect other names in sentence)
```

### Anti-Patterns to Avoid

- **Global deny list for all entity types:** Causes type confusion (e.g., "NC" = nasal cannula vs North Carolina state)
- **Regex-based deny lists:** Over-engineered for simple exact-match filtering, harder to maintain
- **External file storage for deny lists:** Adds I/O complexity for <100 total terms
- **Adding terms without false positive evidence:** Bloats deny lists, reduces transparency
- **Case-sensitive matching:** Creates edge case bugs when clinical text uses inconsistent capitalization

## Current State Analysis

### Existing Deny Lists (from app/config.py)

**LOCATION deny list (14 terms):**
```python
["NC", "RA", "OR", "ER", "ED", "IV", "PO", "IM", "SQ", "PR", "GT", "NG", "OG", "NJ"]
```
- All medical routes/abbreviations
- **BUG:** Uses exact match (line 185 in deidentification.py)
- Coverage appears comprehensive for common abbreviations

**PERSON deny list (19 terms):**
```python
["mom", "dad", "Mom", "Dad", "parent", "parents", "guardian", "caregiver",
 "nurse", "doctor", "attending", "resident", "fellow", "intern",
 "NP", "PA", "RN", "LPN", "CNA"]
```
- Relationship words + medical roles
- **CORRECT:** Uses case-insensitive match (line 190)
- Has redundant entries ("mom"/"Mom", "dad"/"Dad") that can be simplified with case-insensitive matching

### Missing Deny Lists

**GUARDIAN_NAME:** No deny list exists
- Entity type defined in `phi_entities` (config.py line 48)
- Custom recognizer exists (`app/recognizers/pediatric.py`)
- No deny list filtering in deidentification.py
- **Impact:** May flag generic guardian terms as PHI

**PEDIATRIC_AGE:** No deny list exists
- Entity type defined in `phi_entities` (config.py line 49)
- Custom recognizer exists (`app/recognizers/pediatric.py`)
- No deny list filtering in deidentification.py
- **Impact:** Unknown (requires false positive analysis)

**DATE_TIME:** No deny list exists
- Standard Presidio entity type
- **Known issue from Phase 2:** 354 false positives (35.3% precision)
- Likely over-redacting dosing schedules ("q4h", "BID", "PRN")

**MEDICAL_RECORD_NUMBER, ROOM, PHONE_NUMBER, EMAIL_ADDRESS:** No deny lists
- Lower priority (fewer false positives expected)
- Can add in Phase 3 if false positive analysis reveals need

### Code Locations Requiring Updates

**1. app/config.py (Settings class)**
- Add `deny_list_guardian_name` field
- Add `deny_list_pediatric_age` field
- Add `deny_list_date_time` field
- Normalize PERSON deny list (remove redundant "Mom"/"Dad" entries)

**2. app/deidentification.py (deidentify_text function)**
- Fix LOCATION deny list case-insensitive bug (line 185)
- Add GUARDIAN_NAME deny list check (new)
- Add PEDIATRIC_AGE deny list check (new)
- Add DATE_TIME deny list check (new)

**3. tests/calibrate_thresholds.py (analyze_text_raw function)**
- Fix LOCATION deny list case-insensitive bug (line 135)
- Add new deny list checks to match deidentification.py

**4. tests/evaluate_presidio.py (PresidioEvaluator class)**
- Fix LOCATION deny list case-insensitive bug (line 173)
- Add new deny list checks to match deidentification.py

**5. tests/test_deidentification.py**
- Add regression tests for case-insensitive matching
- Add tests for new deny lists (GUARDIAN_NAME, PEDIATRIC_AGE, DATE_TIME)

## Common Pitfalls

### Pitfall 1: Incomplete Case Normalization

**What goes wrong:** Deny list uses lowercase entries but comparison is case-sensitive

**Why it happens:** Copy-paste inconsistency, missing `.lower()` call

**Example from codebase:**
```python
# BUG (line 185):
if detected_text in settings.deny_list_location:  # "nc" won't match "NC"

# CORRECT (line 190):
if detected_text.lower() in [w.lower() for w in settings.deny_list_person]:
```

**How to avoid:**
- Standardize ALL deny list comparisons to case-insensitive
- Add test cases with mixed case variants
- Document case handling in docstrings

### Pitfall 2: Over-Broad Deny Lists

**What goes wrong:** Adding common words that are sometimes PHI

**Why it happens:** False positive fear leads to overly aggressive filtering

**Example (hypothetical bad idea):**
```python
# DON'T DO THIS:
deny_list_person = ["and", "the", "a", "is"]  # Too broad!
```

**How to avoid:**
- Require documented false positive for each entry
- Review deny list additions with medical expert
- Test against adversarial dataset (rare names)

**Context decision:** "Only add abbreviations with clear false positive evidence from testing"

### Pitfall 3: Not Updating All Code Paths

**What goes wrong:** Fix deny list bug in `deidentification.py` but miss `evaluate_presidio.py` and `calibrate_thresholds.py`

**Why it happens:** Deny list logic duplicated across 3 files

**Current duplication:**
- `app/deidentification.py` line 185-192 (production)
- `tests/evaluate_presidio.py` line 173-175 (evaluation)
- `tests/calibrate_thresholds.py` line 135-137 (calibration)

**How to avoid:**
- Grep for "deny_list" before making changes
- Update all 3 files in same commit
- Add integration test that compares behavior across files

### Pitfall 4: Ambiguous Terms

**What goes wrong:** Adding "Art" to deny list (Art as name vs "art" as abbreviation)

**Why it happens:** Not considering capitalization context

**Example edge cases:**
- "Gene" (name) vs "gene" (biology)
- "Ed" (name) vs "ED" (emergency department)
- "Al" (name) vs "AL" (Alabama)

**How to avoid:**
- Only add terms that are NEVER PHI in medical context
- For ambiguous terms, rely on Presidio's context analysis
- Document why each term is safe to filter

**Context decision:** "Don't add terms that could be both abbreviations AND names—let Presidio's context analysis handle them"

## Expected Deny List Additions

### High Priority (Known False Positives)

**DATE_TIME deny list (dosing schedules):**
```python
deny_list_date_time: List[str] = Field(
    default=[
        # Generic time references
        "today", "tonight", "yesterday", "tomorrow",
        # Dosing schedules (not PHI timestamps)
        "q4h", "q6h", "q8h", "q12h",  # Every X hours
        "BID", "TID", "QID",           # Twice/three/four times daily
        "PRN", "prn",                   # As needed
        "daily", "nightly",
        # Shift times (generic)
        "AM", "PM", "am", "pm",
    ],
    description="Generic time references and dosing schedules not flagged as DATE_TIME PHI"
)
```

**Rationale:** Phase 2 found 354 DATE_TIME false positives (35.3% precision). Dosing schedules are clinical content, not PHI.

### Medium Priority (Potential False Positives)

**GUARDIAN_NAME deny list (relationship words):**
```python
deny_list_guardian_name: List[str] = Field(
    default=[
        # Generic relationship terms (not specific names)
        "parent", "guardian", "caregiver", "family",
    ],
    description="Generic relationship terms not flagged as GUARDIAN_NAME PHI"
)
```

**Rationale:** Custom recognizer uses lookbehind patterns ("Mom [NAME]") but may still flag standalone "parent" or "guardian".

**PEDIATRIC_AGE deny list:**
```python
deny_list_pediatric_age: List[str] = Field(
    default=[
        # Generic age ranges (not specific identifying ages)
        "infant", "toddler", "child", "adolescent", "teen",
        "newborn", "neonate",
    ],
    description="Generic age categories not flagged as PEDIATRIC_AGE PHI"
)
```

**Rationale:** Prevent flagging "infant" or "newborn" as PHI when not part of specific age pattern.

### Low Priority (Unlikely False Positives)

**LOCATION, MEDICAL_RECORD_NUMBER, ROOM, PHONE_NUMBER, EMAIL_ADDRESS:**
- No clear false positive patterns identified in Phase 2
- Can add if false positive analysis in Phase 3 reveals need
- Start with empty deny lists, expand based on evidence

## Code Changes Required

### 1. Fix Case-Insensitive Bug (3 files)

**app/deidentification.py:**
```python
# Line 185 - BEFORE:
if result.entity_type == "LOCATION" and detected_text in settings.deny_list_location:

# Line 185 - AFTER:
if result.entity_type == "LOCATION" and detected_text.lower() in [w.lower() for w in settings.deny_list_location]:
```

**tests/evaluate_presidio.py:**
```python
# Line 173 - Same fix
if result.entity_type == "LOCATION" and detected_text.lower() in [w.lower() for w in settings.deny_list_location]:
```

**tests/calibrate_thresholds.py:**
```python
# Line 135 - Same fix
if result.entity_type == "LOCATION" and detected_text.lower() in [w.lower() for w in settings.deny_list_location]:
```

### 2. Add New Deny Lists (app/config.py)

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Add after deny_list_person (line 141)
    deny_list_guardian_name: List[str] = Field(
        default=["parent", "guardian", "caregiver", "family"],
        description="Generic relationship terms not flagged as GUARDIAN_NAME"
    )

    deny_list_pediatric_age: List[str] = Field(
        default=["infant", "toddler", "child", "adolescent", "teen", "newborn", "neonate"],
        description="Generic age categories not flagged as PEDIATRIC_AGE"
    )

    deny_list_date_time: List[str] = Field(
        default=[
            "today", "tonight", "yesterday", "tomorrow",
            "q4h", "q6h", "q8h", "q12h", "BID", "TID", "QID", "PRN", "prn",
            "daily", "nightly", "AM", "PM", "am", "pm",
        ],
        description="Generic time references and dosing schedules not flagged as DATE_TIME"
    )
```

### 3. Add Deny List Filtering (app/deidentification.py)

```python
# After line 192 (after PERSON deny list check), add:

# Check GUARDIAN_NAME deny list
if result.entity_type == "GUARDIAN_NAME" and detected_text.lower() in [w.lower() for w in settings.deny_list_guardian_name]:
    logger.debug(f"Filtered out deny-listed GUARDIAN_NAME: {detected_text}")
    continue

# Check PEDIATRIC_AGE deny list
if result.entity_type == "PEDIATRIC_AGE" and detected_text.lower() in [w.lower() for w in settings.deny_list_pediatric_age]:
    logger.debug(f"Filtered out deny-listed PEDIATRIC_AGE: {detected_text}")
    continue

# Check DATE_TIME deny list
if result.entity_type == "DATE_TIME" and detected_text.lower() in [w.lower() for w in settings.deny_list_date_time]:
    logger.debug(f"Filtered out deny-listed DATE_TIME: {detected_text}")
    continue
```

### 4. Mirror Changes in Test Files

**tests/evaluate_presidio.py (line 175):** Add same 3 deny list checks
**tests/calibrate_thresholds.py (line 137):** Add same 3 deny list checks

## Success Criteria Verification

From ROADMAP.md Phase 3 success criteria:

| Criteria | Implementation | Verification Method |
|----------|---------------|---------------------|
| 1. All deny lists use case-insensitive matching | Fix lines 185, 173, 135 in 3 files | Regression test with "NC" vs "nc" |
| 2. Medical abbreviation deny list expanded | Add DATE_TIME deny list (q4h, BID, etc.) | False positive count reduction |
| 3. Deny lists exist for all custom entity types | Add deny_list_guardian_name, deny_list_pediatric_age | Config validation test |
| 4. False positive rate reduced by >20% | Precision 87.4% → >90% | Run evaluation on synthetic dataset |

**Measurement approach:**
1. Run `python tests/evaluate_presidio.py --input tests/synthetic_handoffs.json` BEFORE changes
2. Capture baseline: Precision 87.4%, False positives by entity type
3. Implement deny list changes
4. Run evaluation AFTER changes
5. Compare: Target precision >90% (12.6 percentage point improvement = >20% reduction in FP rate)

## Open Questions

### 1. Should we add deny lists for MEDICAL_RECORD_NUMBER, ROOM, PHONE_NUMBER?

**What we know:**
- Phase 2 found these entities have low recall (72.3%, 32.1%, 75.7%)
- Low recall suggests under-detection, not over-detection
- Deny lists help with false positives, not false negatives

**Recommendation:**
- Start with empty deny lists for these entity types
- Run false positive analysis in Phase 3
- Add deny list entries only if clear false positives emerge

### 2. How aggressive should DATE_TIME deny list be?

**What we know:**
- 354 false positives (35.3% precision) from Phase 2
- Dosing schedules ("q4h", "BID") are definitely clinical content
- Generic time references ("today", "tonight") may or may not be PHI

**Trade-off:**
- Too aggressive: Miss actual PHI timestamps in clinical notes
- Too conservative: Continue over-redacting clinical schedules

**Recommendation:**
- Phase 3: Add dosing schedules only (conservative)
- Phase 4: Analyze false negative impact, expand if safe

### 3. Should deny lists be case-sensitive or case-insensitive?

**Resolved:** Case-insensitive is the correct approach

**Rationale:**
- Clinical text has inconsistent capitalization
- "NC" (nasal cannula) appears as "nc", "Nc", "NC" in transcripts
- Context decision: "Case-insensitive deny lists (Consistency prevents edge case bugs)"

## Sources

### Primary (HIGH confidence)

**Medical NLP Deny List Patterns:**
- [Presidio Customization Guide](https://microsoft.github.io/presidio/samples/python/customizing_presidio_analyzer/) - Official deny list implementation
- Existing codebase implementation (app/deidentification.py lines 185-192) - Working production code

**Medical Abbreviation References:**
- [Medical Abbreviations - Johns Hopkins Medicine](https://www.hopkinsmedicine.org/health/treatment-tests-and-therapies/common-medical-abbreviations) - Authoritative abbreviation list
- Phase 2 calibration results (354 DATE_TIME false positives documented)

### Secondary (MEDIUM confidence)

**Case Handling Best Practices:**
- Python string methods documentation (`.lower()`, case-insensitive comparison)
- Phase 2 research findings (case normalization pattern)

## Metadata

**Confidence breakdown:**
- Current state analysis: HIGH - Direct codebase inspection, bug clearly documented
- Deny list additions: MEDIUM - Based on Phase 2 metrics but need false positive analysis
- Implementation approach: HIGH - Straightforward Python list operations, existing working pattern
- Expected impact: MEDIUM - Precision target >90% assumes DATE_TIME false positives are main driver

**Research date:** 2026-01-23
**Valid until:** 60 days (stable domain - medical abbreviations don't change frequently)

**Key assumptions:**
1. DATE_TIME false positives (354) are primarily dosing schedules, not diverse patterns
2. Case-insensitive matching is sufficient (no unicode/accent normalization needed)
3. Deny list expansion can achieve 20%+ false positive reduction
4. Existing deny lists (LOCATION, PERSON) are comprehensive for their domains
5. False positive analysis in Phase 3 won't reveal major new categories of clinical terms

---

**RESEARCH COMPLETE** - Ready for planning Phase 3 tasks.
