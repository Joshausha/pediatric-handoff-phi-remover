# De-identification Investigation - Three Failure Cases

**Date:** 2026-01-23
**Investigator:** Claude Code
**Purpose:** Root cause analysis for three de-identification test failures

## Executive Summary

All three failures have been traced to specific root causes in the Presidio detection pipeline. Two are **false positives** (over-redaction), one is a **false negative** (missed PHI).

| Failure | Type | Root Cause | Design Trade-off |
|---------|------|------------|------------------|
| "high flow" → "[LOCATION]flow" | False Positive | spaCy NER misclassifies "on high" as location; deny list only filters exact matches | Balancing medical terminology preservation vs. location detection |
| "Ronald McDonald House" not detected | False Negative | Missing recognizer for charity housing; school recognizer only catches schools/daycares | Incomplete coverage of pediatric location patterns |
| "35 weeker" → "[AGE]" | Debatable (likely false positive) | Gestational age pattern explicitly includes "weeker" suffix | Medical terminology vs. potentially identifying age |

---

## Failure 1: "high flow" → "[LOCATION]flow"

### Test Case
**Input:** `"Patient on high flow oxygen"`
**Expected:** `"Patient on high flow oxygen"` (no redaction)
**Actual:** `"[LOCATION]flow oxygen"`

### Code Path

1. **Detection:** spaCy `en_core_web_lg` NER model detects `"Patient on high "` as a LOCATION entity (score: 0.60)
2. **Deny list filtering:** `app/deidentification.py` lines 156-158
   ```python
   if result.entity_type == "LOCATION" and detected_text in settings.deny_list_location:
       logger.debug(f"Filtered out deny-listed LOCATION: {detected_text}")
       continue
   ```
   - Detected text after `.strip()`: `"Patient on high"`
   - **NOT in deny list** - filtering fails
3. **Result:** Entity passes through, gets replaced with `[LOCATION]`

### Root Cause

**Primary:** spaCy NER model confuses "on high" (as in "on high alert" or the city "On High Point") with medical terminology "high flow"

**Secondary:** Deny list check at line 156 uses **exact string matching** after stripping:
```python
detected_text = text[result.start:result.end].strip()
if result.entity_type == "LOCATION" and detected_text in settings.deny_list_location:
```

The deny list (`app/config.py` lines 67-83) contains only uppercase medical abbreviations:
```python
deny_list_location: List[str] = Field(
    default=[
        "NC",    # Nasal cannula
        "RA",    # Room air
        "OR",    # Operating room
        # ... etc
    ]
)
```

**Why it fails:**
- Deny list expects exact matches like `"NC"` or `"RA"`
- Detected span is `"Patient on high"` - no match
- Even if deny list had `"high"`, it wouldn't match `"Patient on high"`

### Classification

**False Positive** - Medical terminology incorrectly flagged as PHI

### Design Questions

1. **Should "high flow" be in a deny list?**
   - Medical abbreviations (NC, RA) work because they're distinct tokens
   - "high flow" is a multi-word phrase that spaCy sees as part of a larger phrase "on high"

2. **Is substring matching the solution?**
   - Could check if detected text contains deny-listed terms
   - Risk: Too aggressive (e.g., "PORTLAND" contains "OR")

3. **Is case-insensitive matching needed?**
   - Current deny list is case-sensitive but only uppercase
   - Line 161 does case-insensitive for PERSON: `detected_text.lower() in [w.lower() for w in settings.deny_list_person]`
   - LOCATION deny list inconsistent (STATE.md already noted this)

### Recommended Approach

**Option A:** Add context-aware phrase filtering
- Add multi-word medical phrases to deny list: `"high flow"`, `"on high flow"`
- Use substring or phrase-boundary matching

**Option B:** Lower the LOCATION score threshold
- Current threshold: 0.35 (line 54 in config.py)
- This detection has score 0.60 - would need significant increase to filter
- Risk: Might miss real location PHI

**Option C:** Custom recognizer to preserve medical equipment terms
- Similar to school recognizer approach
- Pattern: `(?:high flow|low flow) (?:oxygen|nasal cannula)`
- Could add to PERSON/LOCATION deny list context

---

## Failure 2: "Ronald McDonald House" not detected

### Test Case
**Input:** `"Family staying at Ronald McDonald House"`
**Expected:** `"Family staying at [LOCATION]"`
**Actual:** `"Family staying at Ronald McDonald House"` (no redaction)

### Code Path

1. **Detection attempt:** spaCy NER model does NOT detect any entities (score threshold: 0.35)
2. **Custom recognizers:** School recognizer (`app/recognizers/pediatric.py` lines 213-243) does NOT match
   - Only patterns for: Elementary/Middle/High School, Daycare, Preschool
   - No pattern for charity housing
3. **Result:** No entity detected, text passes through unchanged

### Root Cause

**Primary:** Incomplete recognizer coverage for pediatric-specific locations

The school recognizer patterns (lines 216-234) only catch:
```python
# Elementary/Middle/High School
Pattern(name="school_name",
    regex=r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:Elementary|Middle|High|Primary|Secondary)\s+(?:School)?\b")

# Daycare/Preschool
Pattern(name="daycare_name",
    regex=r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:Daycare|Day\s+Care|Preschool|Pre-school|Nursery)\b")

# "goes to [School]"
Pattern(name="attends_school",
    regex=r"\b(?:goes\s+to|attends|enrolled\s+at)\s+([A-Z][A-Za-z\s]+?)(?:\s+(?:school|daycare|preschool))?\b")
```

**Why it fails:**
- "Ronald McDonald House" doesn't contain school/daycare keywords
- spaCy NER alone detects it as PERSON (score 0.85) when isolated, but NOT when in sentence
- Context "Family staying at" suppresses spaCy's PERSON detection

### Interesting Finding

When testing in isolation:
```
"Ronald McDonald House" alone → PERSON (0.85 score)
"Family staying at Ronald McDonald House" → No detection
```

This suggests spaCy's NER is context-sensitive and the phrase "Family staying at" creates a context where "Ronald McDonald" is NOT interpreted as a person name.

### Classification

**False Negative** - PHI location missed

### Design Questions

1. **Is "Ronald McDonald House" actually PHI?**
   - YES - Reveals family's housing situation
   - Especially identifying in smaller cities with only one location
   - Similar sensitivity to school names (already being redacted)

2. **Should we rely on spaCy to catch this?**
   - spaCy's context sensitivity is a feature, not a bug
   - It's correctly NOT flagging "Ronald McDonald" as a person in this context
   - But we need it flagged as a LOCATION, which it's not doing

3. **What other pediatric locations are we missing?**
   - Charity housing: Ronald McDonald House, Hope Lodge, Family House
   - Foster care agencies
   - Group homes
   - Specific clinics/therapy centers

### Recommended Approach

**Option A:** Extend school recognizer to include charity housing
- Add patterns for "Ronald McDonald House", "Hope Lodge", "Family House", etc.
- Rename to "Pediatric Location Recognizer" (broader scope)
- Pattern example: `r"\b(?:Ronald McDonald|Hope|Family)\s+(?:House|Lodge)\b"`

**Option B:** Add to deny list (inverse - force detection)
- Create an "always detect" list for known PHI locations
- Requires different logic than current deny list (which filters out false positives)

**Option C:** Lower score threshold for LOCATION
- Current: 0.35
- Risk: More false positives like "high flow" issue

---

## Failure 3: "35 weeker" → "[AGE]"

### Test Case
**Input:** `"This is a 35 weeker with respiratory distress"`
**Expected:** Debatable - test expects `"This is a 35 weeker with respiratory distress"` (no redaction)
**Actual:** `"This is a [DATE] with respiratory distress"`

### Code Path

1. **Detection:** TWO entities detected:
   - DATE_TIME: `"35 weeker"` (score: 0.85) - from spaCy NER
   - PEDIATRIC_AGE: `"35 weeker"` (score: 0.50) - from custom recognizer
2. **Custom recognizer:** `app/recognizers/pediatric.py` lines 190-195
   ```python
   Pattern(
       name="gestational_age",
       regex=r"\b(\d{2})[\s-]?(?:week|wk)(?:er|s)?(?:\s+(?:gestation|gestational|GA))?\b",
       score=0.5
   )
   ```
   - Pattern explicitly includes `(?:er|s)?` suffix - matches "weeker"
   - Optional gestation keywords at end
3. **Replacement:** DATE_TIME wins (higher score 0.85), replaced with `[DATE]`

### Root Cause

**Primary:** Gestational age pattern intentionally includes "weeker" suffix

The regex pattern at line 193:
```python
r"\b(\d{2})[\s-]?(?:week|wk)(?:er|s)?(?:\s+(?:gestation|gestational|GA))?\b"
```

Breakdown:
- `\b(\d{2})` - Two digits (gestational age weeks)
- `[\s-]?` - Optional space or hyphen
- `(?:week|wk)` - "week" or "wk"
- `(?:er|s)?` - **Optional "er" or "s" suffix** ← This matches "weeker"
- `(?:\s+(?:gestation|gestational|GA))?` - Optional clarifying keywords

**Design intent:** Catch variations like:
- "28 week gestation"
- "32 weeks"
- "35 weeker" ← Caught
- "30 wk GA"

### Classification

**Debatable** - Could be false positive OR appropriate detection depending on PHI definition

### Design Questions

1. **Is "35 weeker" identifying information?**

   **Arguments FOR redacting (current behavior):**
   - Combined with other clinical details, could identify patient
   - Very specific gestational age + diagnosis might be rare
   - "35 weeker" is more specific than "preterm infant"
   - Consistent with redacting other detailed ages ("3 weeks 2 days old")

   **Arguments AGAINST redacting:**
   - "35 weeker" is standard medical shorthand used in handoffs
   - Gestational age ranges are common (34-36 weeks = late preterm)
   - No different from "term infant" or "preterm" which we don't redact
   - Doesn't identify patient without additional context
   - Over-redaction reduces clinical utility

2. **What's the threshold for "detailed age" becoming PHI?**
   - "Preterm infant" - clearly NOT PHI (too general)
   - "3 weeks 2 days old" - clearly PHI (very specific)
   - "35 weeker" - **Gray area** (somewhat specific, but common terminology)
   - "35 weeks 2 days gestation" - clearly PHI (very detailed)

3. **Does this align with project goals?**
   From STATE.md: "Clinical utility requires readable transcripts; pure aggressive approach over-redacts"
   - Current behavior: Aggressive (redacts standard terminology)
   - Balance: Precision vs. recall trade-off

### Current Pattern Coverage

The gestational age pattern catches:
- ✅ "28 week gestation"
- ✅ "32 weeks GA"
- ✅ "35 weeker" ← **This case**
- ✅ "30 wk"

Does NOT catch (requires explicit "weeker" or gestation keywords):
- ❌ "term infant"
- ❌ "preterm"
- ❌ "35-36 weeks" (range, different pattern)

### Recommended Approach

**Option A:** Remove "weeker" from pattern (preserve medical terminology)
- Change regex to: `r"\b(\d{2})[\s-]?(?:week|wk)(?:s)?(?:\s+(?:gestation|gestational|GA))?\b"`
- Would still catch: "35 weeks gestation", "35 weeks GA"
- Would NOT catch: "35 weeker" (preserved as medical shorthand)
- Alignment: Better balance with clinical utility goal

**Option B:** Require explicit "gestation" keywords for "weeker"
- Keep pattern but make gestation keywords required for "-er" suffix
- More complex regex with conditional logic
- Example: Only flag "35 weeker gestation", not standalone "35 weeker"

**Option C:** Keep current behavior (conservative/aggressive)
- Argue that any specific gestational age is potentially identifying
- Prioritize safety over clinical utility
- Accept over-redaction as acceptable trade-off

**Option D:** Add to deny list
- Add "weeker" patterns to PEDIATRIC_AGE deny list
- Similar to how "mom" is in PERSON deny list
- Challenge: Pattern-based deny list vs. exact matching

---

## Summary

| Failure | Priority | Complexity | Recommended Fix |
|---------|----------|------------|-----------------|
| "high flow" false positive | **High** | Medium | Add multi-word medical phrases to deny list with phrase-boundary matching |
| "Ronald McDonald House" false negative | **High** | Low | Extend school recognizer with charity housing patterns |
| "35 weeker" false positive | **Medium** | Low | Remove "er" suffix from gestational age pattern OR add deny list for common medical shorthand |

### Trade-offs Summary

All three failures involve the **core tension** of the project:
- **High recall** (catch all PHI) → More false positives, over-redaction
- **High precision** (preserve clinical content) → More false negatives, PHI leaks

Current system: **Optimized for high recall** (conservative/aggressive)
- "35 weeker" redacted (prioritizing safety)
- But also "high flow" redacted (unintended over-redaction)
- And "Ronald McDonald House" missed (gap in coverage)

### Next Steps

1. **Investigate deny list architecture:** Can we support phrase matching and substring checks without breaking existing filters?
2. **Expand location recognizer:** Add pediatric housing patterns (Ronald McDonald House, etc.)
3. **Define policy on medical shorthand:** When is terminology "identifying" vs. "standard medical language"?
4. **Add test cases:** These three cases should become regression tests after fixes

---

## Code References

**De-identification pipeline:** `app/deidentification.py`
- Lines 142-148: Main analysis call
- Lines 151-165: Deny list filtering
- Lines 189-209: Replacement strategy

**Configuration:** `app/config.py`
- Lines 66-84: LOCATION deny list (case-sensitive, uppercase only)
- Lines 85-108: PERSON deny list (case-insensitive)
- Line 54: PHI score threshold (0.35)

**Pediatric recognizers:** `app/recognizers/pediatric.py`
- Lines 190-195: Gestational age pattern (includes "weeker")
- Lines 213-243: School/location recognizer (missing charity housing)

**Medical recognizers:** `app/recognizers/medical.py`
- No relevant patterns for these failures

---

**Investigation complete.** Ready for Phase 1 baseline measurement and systematic improvement.
