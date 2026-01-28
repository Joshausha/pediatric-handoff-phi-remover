# Pitfalls Research: Deny List Expansion

**Research Date**: 2026-01-28
**Project**: Pediatric Handoff PHI Remover - Deny List Expansion
**Focus**: Common mistakes when expanding deny lists for clinical NER/de-identification systems
**Confidence**: HIGH (based on project history + Presidio best practices + clinical NER research)

## Executive Summary

Deny list expansion for clinical PHI detection has a **unique failure profile**: the goal is reducing false positives (over-redaction) WITHOUT introducing false negatives (missed PHI). This creates an asymmetric risk where mistakes can either:
1. Allow PHI through (legal/compliance risk)
2. Over-redact clinical content (usability risk)

This research documents mistakes that cause both failure modes, with emphasis on **project-specific lessons learned** from Phases 3-6.

---

## Critical Pitfalls

### Pitfall 1: Substring Matching Without Boundary Checking

**What goes wrong**: Switching from exact match to substring match (e.g., `"months old" in detected_text`) causes unintended filtering of legitimate PHI that contains the substring.

**Real example from codebase**:
```python
# DATE_TIME deny list check (deidentification.py line 204-210)
# Uses SUBSTRING match for clinical timeline patterns
if result.entity_type == "DATE_TIME":
    detected_lower = detected_text.lower()
    if any(term.lower() in detected_lower for term in settings.deny_list_date_time):
        logger.debug(f"Filtered out deny-listed DATE_TIME: {detected_text}")
        continue
```

**Why it's dangerous**:
- "5 months old" matches "months old" → correctly filtered (age descriptor)
- BUT: "admitted 5 months ago" matches "months old" → INCORRECTLY filtered
- "birthday in 3 months" matches "months old" → INCORRECTLY filtered (missed PHI!)

**Warning signs**:
- Deny list term is multi-word phrase with generic words
- False negative rate increases after deny list expansion
- Test suite has exact matches but real transcripts have longer phrases
- Pattern appears in middle of sentences, not just at boundaries

**Prevention strategy**:
1. **Use exact match by default**: `detected_text.lower() in [w.lower() for w in deny_list]`
2. **Substring match ONLY when necessary**: Clinical timeline patterns like "5 months old" where numeric prefix varies
3. **Add boundary tokens**: Include spaces in deny list terms (`" months old "` not `"months old"`) to prevent mid-word matches
4. **Test negative cases**: For each deny list term, create test case where it appears IN a PHI phrase that should NOT be filtered

**Which phase addresses**:
- Phase 3 (Deny List Refinement): When expanding deny lists beyond exact abbreviations
- Phase 6 (Real Handoff Testing): When substring match bugs surface in production

**Project-specific lesson**: Phase 6 added "days old", "months old" to deny list. This REQUIRES substring matching because prefix changes ("3 days old", "7 months old"). But must verify it doesn't match "3 days ago" (which IS potential PHI).

---

### Pitfall 2: Adding Terms Without False Positive Evidence

**What goes wrong**: Expanding deny lists based on hypothetical false positives rather than actual documented errors leads to bloat and potential security gaps.

**Real example from project**:
- Phase 3 added "DKA", "CT", "MRI", "EEG" to PERSON deny list
- These were found through **evidence**: real false positives in test transcripts
- Contrast with temptation to pre-emptively add entire medical abbreviation dictionary

**Why it's dangerous**:
- **Security risk**: Adding "Art" because it's a medical abbreviation (ART = antiretroviral therapy) but "Art Smith" is a real name
- **Maintenance burden**: 500-item deny list is unmaintainable vs 50-item evidence-based list
- **False confidence**: "We have 500 terms in deny list" doesn't mean better coverage

**Warning signs**:
- Deny list grows >100 terms without proportional false positive reduction
- Terms added "just in case" without specific test failure
- Copy-pasting abbreviation dictionaries from external sources
- No comments documenting why each term was added

**Prevention strategy**:
1. **Evidence-driven expansion**: Add term ONLY after documenting false positive
2. **One term = one test case**: Each deny list entry should have corresponding regression test
3. **Comment rationale**: Document which test case or production error drove each addition
4. **Periodic pruning**: Review deny list quarterly, remove terms with no recent matches

**Which phase addresses**:
- Phase 3 (Deny List Refinement): Establish evidence-driven process
- Phase 6 (Real Handoff Testing): Document production errors that drive additions
- Maintenance: Quarterly review of deny list effectiveness

**Project-specific lesson**: Phase 6 found "bilirubin" → [NAME] false positive. Rather than adding all medical terms, added specific evidence-based terms: bilirubin, ARFID, citrus, diuresis.

---

### Pitfall 3: Case Sensitivity Inconsistencies Across Files

**What goes wrong**: Fixing case-insensitive matching bug in `deidentification.py` but missing duplicate logic in `evaluate_presidio.py` and `calibrate_thresholds.py` causes test/production divergence.

**Real example from project** (Phase 3 fix):
```python
# Bug existed in 3 files simultaneously:
# - app/deidentification.py line 185 (production)
# - tests/evaluate_presidio.py line 173 (evaluation)
# - tests/calibrate_thresholds.py line 135 (calibration)

# BEFORE (broken):
if detected_text in settings.deny_list_location:  # "nc" won't match "NC"

# AFTER (fixed):
if detected_text.lower() in [w.lower() for w in settings.deny_list_location]:
```

**Why it's dangerous**:
- Tests pass ("NC" filtered) but production fails ("nc" leaks through)
- Threshold calibration uses different filtering than production
- Metrics become unreliable - can't trust precision/recall numbers

**Warning signs**:
- Deny list logic copy-pasted across multiple files
- Test performance differs significantly from production performance
- Case variants ("NC" vs "nc" vs "Nc") show different behavior
- Changes to deidentification.py require parallel changes elsewhere

**Prevention strategy**:
1. **Grep before changes**: `grep -r "deny_list" app/ tests/` before modifying filtering logic
2. **Shared function**: Extract deny list filtering to shared utility function (DRY principle)
3. **Integration test**: Test that deidentification.py and evaluate_presidio.py produce identical results on same input
4. **Code review checklist**: "Did you update all 3 files?"

**Which phase addresses**:
- Phase 3 (Deny List Refinement): Fix inconsistency across all files
- Maintenance: Refactor to eliminate duplication

**Project-specific lesson**: Phase 3 research identified this bug and documented all 3 locations requiring fix. Future: Extract shared `apply_deny_lists()` function.

---

### Pitfall 4: Server Configuration Caching

**What goes wrong**: Config changes don't take effect because server uses `@lru_cache()` and wasn't restarted.

**Real example from project** (Phase 6, Session 1):
```python
# app/config.py line 286
@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

**Timeline**:
- Phase 5: Added age patterns to DATE_TIME deny list (commit cfbd5b1)
- Phase 6 Session 1: "18 year old" still redacted to `[DATE]`
- Root cause: Server started Saturday, never restarted, running with stale config
- Fix: Restart server → "18 year old" preserved correctly

**Why it's dangerous**:
- **False negative detection**: Config has correct deny list but production uses old config with missing entries
- **Wasted debugging time**: Investigate code when problem is cached config
- **False confidence**: "I added the term but it's still detected" leads to wrong conclusions

**Warning signs**:
- Deny list changes don't affect production behavior
- Restarting server "magically" fixes issues
- Different behavior between test environment and production
- Config file timestamps are recent but behavior unchanged

**Prevention strategy**:
1. **Document restart requirement**: "After changing config.py, restart server to pick up changes"
2. **Add cache busting**: Development mode should disable `@lru_cache` or use short TTL
3. **Health check endpoint**: `/health` endpoint shows config file timestamp vs server start time
4. **Automated testing**: CI/CD should test with fresh config load (no cached settings)

**Which phase addresses**:
- Phase 6 (Real Handoff Testing): When discovered
- CI/CD improvements: Add config cache detection to test suite

**Project-specific lesson**: This cost 21 handoffs of false positive errors. Root cause was NOT code but cached config. Document restart requirement prominently.

---

### Pitfall 5: Ambiguous Terms That Are Sometimes PHI

**What goes wrong**: Adding terms to deny list that are context-dependent - sometimes PHI, sometimes not.

**Hypothetical dangerous examples**:
```python
# DON'T ADD THESE:
deny_list_person = [
    "gene",    # Gene Smith (name) vs gene therapy (medical)
    "ed",      # Ed Johnson (name) vs ED (emergency dept)
    "art",     # Art Williams (name) vs ART (antiretroviral therapy)
    "bill",    # Bill Jones (name) vs medical bill
]
```

**Why it's dangerous**:
- "Contact Gene for updates" → Gene (person name) incorrectly preserved
- "Patient Art Smith" → Art (name) incorrectly preserved
- Creates **false negatives** (missed PHI) - the worst outcome for compliance

**Warning signs**:
- Deny list term is common English word
- Term appears in name databases (US Census names, SSA baby names)
- Term has multiple meanings in medical vs general context
- Capitalization changes meaning ("Bill" name vs "bill" invoice)

**Prevention strategy**:
1. **Never add ambiguous terms**: If term could be BOTH abbreviation AND name, don't add it
2. **Rely on NER context**: Presidio's spaCy model uses sentence context - trust it for ambiguous cases
3. **Check name databases**: Before adding term, search US SSA baby names database
4. **Document non-ambiguous requirement**: Deny list policy: "Only add terms that are NEVER PHI in medical context"

**Which phase addresses**:
- Phase 3 (Deny List Refinement): Establish deny list inclusion criteria
- Code review: Reject deny list additions for ambiguous terms

**Project-specific lesson**: "bilirubin", "ARFID", "DKA" are safe - not common names. "Gene", "Art", "Ed" are unsafe - common names. Document this distinction.

---

### Pitfall 6: Test Script Generation Without Negative Cases

**What goes wrong**: When generating test scripts to validate deny list expansion, only creating positive cases ("term should be filtered") without negative cases ("term in PHI context should NOT be filtered").

**Example of incomplete test**:
```python
# INCOMPLETE - Only tests positive case
def test_months_old_not_redacted():
    """Test that age descriptor is preserved."""
    text = "This is a 5 months old infant."
    result = deidentify_text(text)
    assert "months old" in result.clean_text  # ✓ Tests preservation

# MISSING - Negative case
def test_months_ago_IS_redacted():
    """Test that timeframe reference IS still caught as PHI."""
    text = "Patient admitted 3 months ago on December 15th."
    result = deidentify_text(text)
    # Should redact "December 15th" even though "months ago" is present
    assert "December" not in result.clean_text  # ✗ Not tested!
```

**Why it's dangerous**:
- Deny list expansion can inadvertently create false negatives
- Substring matching can filter too broadly
- False sense of security - "All tests pass" but PHI leaks through

**Warning signs**:
- Test suite only validates deny list filtering works
- No tests for "this term SHOULD be detected despite deny list"
- Real handoff testing finds false negatives not caught in test suite
- Tests focus on precision improvement but don't verify recall maintained

**Prevention strategy**:
1. **Paired tests**: For each deny list term, write BOTH positive (filter) and negative (don't filter) test cases
2. **Adversarial test generation**: "How could this deny list entry cause a false negative?"
3. **Recall regression testing**: After deny list expansion, run full recall evaluation to detect false negatives
4. **Real-world validation**: Test against actual PHI-containing transcripts (de-identified for testing)

**Which phase addresses**:
- Phase 3 (Deny List Refinement): When creating test cases for new deny lists
- Phase 6 (Real Handoff Testing): Validates no false negatives introduced

**Project-specific lesson**: When adding "months old" to deny list, must also test "admitted 3 months ago on January 15" to ensure date still detected.

---

## Medium Risk Pitfalls

### Pitfall 7: Deny List Ordering Dependencies

**What goes wrong**: Deny list filtering order matters if one term is substring of another.

**Example**:
```python
deny_list_date_time = [
    "day old",        # Matches "3 day old"
    "days old",       # Matches "3 days old"
    "day of life",    # Matches "day of life 5"
    "dol",            # Matches "DOL 3"
]

# Substring match with first match wins:
"3 days old infant" → matches "day old" first (wrong!)
```

**Prevention strategy**:
- Use exact match by default (order doesn't matter)
- For substring match, sort deny list by length descending (longest first)
- Document that order matters for substring matching
- Test with terms that are substrings of each other

**Which phase addresses**: Phase 3 (Deny List Refinement)

---

### Pitfall 8: Unicode and Accent Normalization

**What goes wrong**: Medical terms with accents or special characters don't match deny list.

**Example**:
- "Café-au-lait spots" vs "Cafe-au-lait spots"
- "José" (name) vs "Jose" (deny list entry - hypothetically)

**Prevention strategy**:
- Use Unicode normalization (NFKC) before comparison if multi-cultural patient population
- Document whether deny list supports accented characters
- For this project: English-only transcription, accents rare, accept limitation

**Which phase addresses**: Phase 6 (Real Handoff Testing) - if non-English names appear

---

### Pitfall 9: Over-Reliance on Deny Lists vs Threshold Tuning

**What goes wrong**: Using deny lists to compensate for poor threshold calibration instead of fixing root cause.

**Example**:
- DATE_TIME threshold too low (0.3) → detects "today" as PHI
- Add "today" to deny list instead of raising threshold to 0.4

**Why it's problematic**:
- Deny lists treat symptom, not disease
- Hides underlying model performance issues
- Deny list grows unbounded as more false positives discovered

**Prevention strategy**:
- Threshold tuning FIRST (Phase 2), deny lists SECOND (Phase 3)
- Deny lists should be for domain-specific terms (medical abbreviations), not general words
- If adding common English words to deny list, consider threshold adjustment instead

**Which phase addresses**: Phase 2 (Threshold Calibration) before Phase 3

---

### Pitfall 10: Deny List vs Recognizer Pattern Conflicts

**What goes wrong**: Adding term to deny list that conflicts with custom recognizer pattern.

**Example from project**:
```python
# Custom recognizer pattern (pediatric.py):
# Matches "Baby [NAME]" with lookbehind

# Hypothetically adding to deny list:
deny_list_person = ["baby"]  # DON'T DO THIS

# Result: "Baby Smith" → neither custom recognizer fires (filtered)
#         nor standard NER catches "Smith" (depends on context)
```

**Prevention strategy**:
- Review custom recognizer patterns before expanding deny lists
- Ensure deny list doesn't filter terms that trigger custom recognizers
- Integration test: Custom recognizers should still fire after deny list expansion

**Which phase addresses**: Phase 3 (Deny List Refinement) - review custom recognizers

---

## Prevention Checklist by Phase

### Before Adding ANY Deny List Term

- [ ] **Evidence documented**: False positive test case or production error documented
- [ ] **Rationale comment**: Code comment explains why term was added
- [ ] **Ambiguity check**: Term is not a common English name (check SSA database)
- [ ] **Boundary check**: If substring match needed, verified it won't match PHI phrases
- [ ] **Negative test case**: Created test where term SHOULD be detected (don't over-filter)
- [ ] **All files updated**: Checked `deidentification.py`, `evaluate_presidio.py`, `calibrate_thresholds.py`
- [ ] **Case normalization**: Uses `.lower()` comparison consistently
- [ ] **Recognizer review**: Verified no conflict with custom recognizer patterns

### After Deny List Expansion

- [ ] **Recall regression test**: Run full evaluation to check false negative rate unchanged
- [ ] **Precision improvement**: Verify false positive rate decreased as expected
- [ ] **Server restart**: If config.py changed, restart server to pick up changes
- [ ] **Integration test**: Same behavior across deidentification and evaluation code paths
- [ ] **Real handoff validation**: Test with actual clinical handoff transcripts

### Maintenance

- [ ] **Quarterly review**: Review deny list effectiveness, remove unused terms
- [ ] **Performance check**: Ensure deny list size (<100 terms) doesn't impact performance
- [ ] **Documentation update**: Keep rationale comments current with test evidence

---

## Key Takeaways

1. **Substring matching is dangerous** - Use exact match by default, substring only when necessary with careful boundary checking
2. **Evidence-driven expansion** - Never add terms without documented false positive
3. **Test negative cases** - Ensure deny list doesn't create false negatives (missed PHI)
4. **Case consistency across files** - Fix in all 3 code paths: production, evaluation, calibration
5. **Server restart required** - Config changes don't take effect until server restart due to `@lru_cache`
6. **Ambiguous terms are unsafe** - Don't add terms that could be both names and abbreviations
7. **Recall is non-negotiable** - Deny list expansion must NOT reduce recall (missed PHI)

---

## Project-Specific Lessons Learned

### Phase 3 Success
- Fixed case-insensitive bug across 3 files simultaneously
- Added DATE_TIME, GUARDIAN_NAME, PEDIATRIC_AGE deny lists
- Evidence-based: Only added terms with documented false positives

### Phase 6 Discovery
- **Server restart requirement** caused 21 handoffs of false errors
- Root cause: `@lru_cache()` on config meant changes didn't load
- Lesson: Document restart requirement prominently

### Phase 6 Medical Terms
- Added "bilirubin", "ARFID", "citrus", "diuresis" to PERSON deny list
- Evidence: Real false positives in handoff transcripts
- Safe: Not common English names (checked SSA database)

---

## Sources

**HIGH Confidence:**
- [Presidio Deny List Documentation](https://microsoft.github.io/presidio/tutorial/01_deny_list/) - Official guidance on deny list implementation
- [Presidio Best Practices](https://microsoft.github.io/presidio/analyzer/developing_recognizers/) - Recognizer development and false positive management
- Project codebase analysis - Direct inspection of `deidentification.py`, `config.py`, test files
- Phase 3 Research (03-RESEARCH.md) - Documented case-insensitive bug and deny list expansion
- Phase 6 Pattern Analysis (patterns_identified.md) - Real production errors documented

**MEDIUM Confidence:**
- [Clinical NER Challenges](https://pmc.ncbi.nlm.nih.gov/articles/PMC10651400/) - Named Entity Recognition in Electronic Health Records methodological review
- [String Matching Methods](https://note.nkmk.me/en/python-str-compare/) - Python string comparison best practices
- [NER Evaluation Metrics](https://github.com/MantisAI/nervaluate) - Exact vs partial matching in NER evaluation
- [Sensitive Data Discovery](https://www.docontrol.io/blog/sensitive-data-discovery-tools) - Why exact matching causes false negatives

**LOW Confidence (general guidance):**
- Web search results on medical abbreviation misinterpretation (general issues, not deny list specific)
- HIPAA guidance on de-identification (legal requirements, not technical implementation)

---

## Confidence Assessment

| Area | Confidence | Rationale |
|------|------------|-----------|
| Substring matching pitfalls | HIGH | Project experienced this issue, well-documented in research |
| Evidence-driven expansion | HIGH | Phase 3 established this pattern, Phase 6 validated it |
| Case sensitivity bugs | HIGH | Found and fixed in Phase 3 across 3 files |
| Server caching issue | HIGH | Phase 6 Session 1 documented this root cause |
| Ambiguous terms | MEDIUM | General best practice, not project-specific experience yet |
| Test negative cases | MEDIUM | General testing principle, project hasn't had false negative incidents |
| Unicode normalization | LOW | Not yet encountered in English-only transcripts |

---

*Research completed: 2026-01-28*
*Document version: 2.0 (Deny List Expansion Focus)*
*Primary researcher: Claude Code (Research Agent)*
