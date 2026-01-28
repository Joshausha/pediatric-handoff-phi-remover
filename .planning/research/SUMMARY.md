# Research Summary: Over-Detection Quality Pass

**Project:** Pediatric Handoff PHI Remover v2.1
**Domain:** HIPAA-compliant clinical NER and PHI de-identification
**Researched:** 2026-01-28
**Confidence:** HIGH

## Executive Summary

The v2.1 Over-Detection Quality Pass aims to reduce false positives in PHI detection by expanding deny lists based on systematic testing. Research shows this is a **configuration and test integration problem, not an architecture problem**. The existing Presidio-based system has the right structure—the issue is inconsistent matching strategies (exact vs substring) across entity types and incomplete deny list coverage for medical context phrases.

**Recommended approach:** Extend existing Faker-based test generation with medical duration/timeline providers, normalize all deny lists to substring matching with word boundary checking, expand deny lists conservatively based on evidence (not hypothetically), and integrate the standalone test harness into the pytest framework. This approach leverages proven infrastructure (500+ synthetic handoffs, I-PASS templates, comprehensive evaluation framework) rather than introducing complex new tooling.

**Key risks:** Substring matching without word boundaries can over-filter legitimate PHI ("high" in "Higham"), server config caching can mask deny list changes (requires restart), and ambiguous terms (e.g., "Gene" as both name and medical term) create compliance gaps. Mitigation: word boundary regex, documented restart requirements, and strict evidence-based expansion with clinical validation.

## Key Findings

### Recommended Stack (from STACK.md)

**Testing infrastructure is excellent—extend, don't rebuild.** The project already has Faker-based synthetic data generation (500+ handoffs), I-PASS templates (27+ variants), and pytest evaluation framework. Gap: medical context phrases (duration expressions, respiratory flow terminology) that look like PHI but aren't.

**Core tools:**
- **pytest + parameterization**: Regression testing for deny list additions — standard practice, already in use
- **Faker medical providers**: Extend with ClinicalTimelineProvider and MedicalContextProvider — minimal effort (~50 lines)
- **collections.Counter**: Corpus frequency analysis to find false positive candidates — stdlib, no dependencies
- **Word boundary regex**: Safe substring matching that prevents over-filtering names — proven pattern

**What NOT to add:**
- LLM-based test generation (non-deterministic, no ground truth labels, expensive)
- Label Studio (only needed for spaCy fine-tuning, not in scope)
- Generic stopword lists (medical domain requires domain-specific deny lists with clinical validation)

### Expected Features (from FEATURES.md)

Research identified deny list patterns already implemented (table stakes) vs gaps needing attention (v2.1 focus).

**Must have (already implemented in Phases 3-6):**
- Age descriptors (✅ "18 year old", "3-month-old", "36 weeks gestation")
- Dosing schedules (✅ "q6h", "BID", "PRN")
- Clinical timeline references (✅ "day 3 of illness", "DOL 2", "today", "overnight")
- Medical abbreviations as LOCATION (✅ "NC", "RA", "OR", "IV", "PO")
- Role words as PERSON (✅ "mom", "dad", "nurse", "doctor", "baby")

**Should have (v2.1 targets):**
- **Duration phrases (P1-High):** "three days", "two weeks", "hours ago" — flagged as DATE but are non-PHI timelines
- **Respiratory flow terms (P1-High):** "high flow", "placed on high" — flagged as LOCATION but are oxygen delivery modalities
- Medical conditions as PERSON (P2-Medium): "bilirubin", "ARFID" — phonetically similar to names but medically unambiguous

**Defer (not v2.1):**
- Unit name preservation ("PICU bed 12" → "PICU bed [ROOM]") — requires recognizer modification, not deny list
- Standalone "high"/"low" filtering — risk of over-broad filtering, needs extensive testing

**Anti-features (NEVER add to deny lists):**
- City names ("Boston") — legitimate LOCATION PHI per HIPAA Safe Harbor
- Common first names ("Mike", "Sarah") — creates false negative risk
- Ambiguous terms ("Gene", "Art", "Ed") — both names and medical abbreviations, unsafe

### Architecture Approach (from ARCHITECTURE.md)

Current Presidio architecture is sound—**no fundamental changes needed.** Issue is implementation detail: inconsistent matching strategies across entity types.

**Major components working correctly:**
1. **Transcription (faster-whisper)** — local audio-to-text, no changes needed
2. **Presidio Analyzer (spaCy + custom recognizers)** — NER detection with confidence scores
3. **Deny list filtering (deidentification.py)** — post-processing to remove false positives

**Critical fix required:** Normalize matching strategy across all entity types.

| Entity Type | Current | Recommended |
|-------------|---------|-------------|
| LOCATION | Exact match | Substring with word boundaries |
| DATE_TIME | Substring match ✅ | (no change) |
| PERSON | Exact match | Substring with word boundaries |
| GUARDIAN_NAME | Exact match | Substring with word boundaries |
| PEDIATRIC_AGE | Exact match | Substring with word boundaries |

**Implementation:** Add `_is_deny_listed_substring()` helper with regex word boundaries:
```python
pattern = r'\b' + re.escape(term.lower()) + r'\b'
```
This prevents "high" from matching "Higham" (name) while allowing "high" in "on high flow" (medical).

**Test integration:** Move standalone `test_presidio.py` → `tests/integration/test_presidio_harness.py`, convert to pytest parameterization, integrate known issues as `@pytest.mark.xfail`.

### Critical Pitfalls (from PITFALLS.md)

1. **Substring matching without boundary checking (CRITICAL)** — "high" deny list entry could filter "Higham" (patient name), creating PHI leak. **Mitigation:** Word boundary regex `\bhigh\b` ensures only whole-word matches.

2. **Adding terms without false positive evidence (HIGH)** — Hypothetical deny list additions create bloat and security gaps. "Art" as medical abbreviation (ART therapy) but "Art Smith" is a name. **Mitigation:** Evidence-driven expansion only—one term = one documented test failure = one regression test.

3. **Case sensitivity inconsistencies across files (HIGH)** — Fixed in Phase 3 but affected 3 files (deidentification.py, evaluate_presidio.py, calibrate_thresholds.py). Future: extract shared `apply_deny_lists()` function. **Mitigation:** grep before changes, update all locations simultaneously.

4. **Server configuration caching (MEDIUM)** — Config changes don't take effect due to `@lru_cache()` on `get_settings()`. Cost 21 handoffs of debugging in Phase 6. **Mitigation:** Document restart requirement prominently, consider cache-busting in development mode.

5. **Test scripts without negative cases (MEDIUM)** — Testing only "term should be filtered" without "term in PHI context should NOT be filtered" creates false confidence. **Mitigation:** Paired tests for each deny list entry—verify both filtering AND recall preservation.

## Recommended Approach

Based on combined research, implement deny list expansion using **three-step systematic methodology**:

### Step 1: Corpus Analysis (Find Candidates)
Extract frequently misclassified terms from test failures using `collections.Counter` on evaluation results. Example:
```python
def find_false_positive_patterns(dataset_path, entity_type):
    results = evaluate_on_dataset(dataset_path)
    false_positives = Counter()
    for result in results:
        if result.entity_type == entity_type and result.is_false_positive:
            false_positives[result.text.lower()] += 1
    return false_positives.most_common(20)
```

**Effort:** ~30 lines of code, outputs data-driven candidates

### Step 2: Clinical Validation (Verify Safety)
Manual review with clinical judgment using validation checklist:

| Term | Entity Type | Ever PHI? | Always Safe? | Decision | Rationale |
|------|-------------|-----------|--------------|----------|-----------|
| high | LOCATION | No | Yes | ADD | Medical context (high flow) |
| Boston | LOCATION | YES | No | REJECT | City names ARE PHI |

**HIPAA requirement:** Clinical validation mandatory, cannot automate safety decisions

### Step 3: Regression Test Suite (Prevent Over-Filtering)
Use pytest parameterization to lock in deny list behavior with BOTH positive and negative cases:
```python
@pytest.mark.parametrize("text,entity_type,should_flag", [
    ("Patient on NC at 2L", "LOCATION", False),     # Should NOT flag
    ("Lives in Boston", "LOCATION", True),          # Should STILL flag
])
```

**Time per iteration:** ~2 hours (30 min analysis, 1 hour validation, 30 min testing)

## Implications for Roadmap

Based on architecture analysis and test infrastructure readiness, recommended 4-phase structure:

### Phase 1: Extend Test Coverage
**Rationale:** Must have test cases that expose current gaps before fixing them. Existing infrastructure (Faker + I-PASS templates) makes this low-effort extension.

**Delivers:** 100+ new test cases with medical context phrases

**Actions:**
- Add `ClinicalTimelineProvider` to `tests/medical_providers.py` (duration phrases, day of illness, relative timepoints)
- Add `MedicalContextProvider` (respiratory phrases, location-like abbreviations)
- Create `OVER_DETECTION_EDGE_CASES` templates in `handoff_templates.py`
- Regenerate `tests/synthetic_handoffs.json` with new providers

**Effort:** 2-3 hours
**Research needed:** None (extends proven patterns)

### Phase 2: Deny List Expansion + Matching Strategy Fix
**Rationale:** Core fix for over-detection—address both configuration (missing deny list entries) and logic (inconsistent matching). Can be done in single session as both touch `deidentification.py`.

**Delivers:** Consistent substring matching with word boundaries across all entity types, expanded deny lists for duration/respiratory terminology

**Actions:**
- Implement `_is_deny_listed_substring()` helper with word boundary regex
- Update LOCATION, PERSON, GUARDIAN_NAME, PEDIATRIC_AGE filters to use substring matching
- Add to `deny_list_location`: "high", "low", "air", "flow"
- Add to `deny_list_date_time`: duration word patterns (extend existing)
- Document restart requirement prominently

**Effort:** 3-4 hours
**Risk:** Medium (changes core filtering logic)
**Avoids pitfall:** Substring matching without boundary checking (CRITICAL from PITFALLS.md)

### Phase 3: Regression Prevention
**Rationale:** Lock in deny list behavior to prevent future regressions. Integration with CI/CD ensures automated validation.

**Delivers:** Comprehensive test suite with 50+ parameterized cases covering positive (should filter) and negative (should still detect) scenarios

**Actions:**
- Create `tests/test_deny_lists.py` with parameterized tests
- Test edge cases: "Higham" (name), "high flow" (medical), "Boston" (location PHI)
- Move `test_presidio.py` → `tests/integration/test_presidio_harness.py`
- Convert to pytest format with `@pytest.mark.xfail` for known issues
- Integrate with existing CI/CD

**Effort:** 2-4 hours
**Research needed:** None (organizational change)
**Avoids pitfall:** Test scripts without negative cases (MEDIUM from PITFALLS.md)

### Phase 4: Validation
**Rationale:** Verify deny list expansion resolved over-detection without introducing false negatives (PHI leaks)

**Delivers:** Validation report with precision/recall metrics, updated documentation

**Actions:**
- Run full evaluation on 500+ synthetic handoffs (before/after comparison)
- Verify over-detection issues resolved from milestone context
- Check precision/recall metrics (target: recall ≥90%, precision ≥70%)
- Test with real handoff transcripts (Session 3) for clinical usability
- Update documentation with deny list rationale

**Effort:** 1-2 hours
**Success criteria:**
- [ ] DATE_TIME false positives reduced (duration phrase filtering)
- [ ] LOCATION false positives reduced (respiratory flow filtering)
- [ ] Zero new false negatives (PHI still detected)
- [ ] Clinical utility preserved (usable transcripts)

### Phase Ordering Rationale

1. **Test coverage first:** Can't fix what you can't measure—generate test cases that expose gaps
2. **Deny list + matching strategy together:** Both in same file, addressing same root cause (over-detection)
3. **Regression tests after fix:** Validates Phase 2 worked, prevents future regressions
4. **Validation last:** Comprehensive evaluation of complete milestone

**Parallel work opportunity:** Phase 1 and Phase 2 can overlap (test generation while implementing fixes)

**Total estimated effort:** 8-12 hours for complete milestone

### Research Flags

**No deep research needed for any phase** — all phases use established patterns:
- Phase 1: Extends existing Faker provider pattern (proven in Phases 3-6)
- Phase 2: Applies substring matching already used for DATE_TIME to other entity types
- Phase 3: Standard pytest parameterization (documented in Phase 0 research)
- Phase 4: Uses existing evaluation framework from Phase 2

**Confidence:** This milestone has narrow scope, excellent infrastructure, and clear implementation path.

## Deny List Patterns to Add

Based on FEATURES.md analysis and milestone context:

### Duration Phrases (DATE_TIME deny list)
```python
# Generic duration words
"minutes", "hours", "days", "weeks", "months",

# Specific durations (common in handoffs)
"three minutes", "two hours", "five days", "two weeks",

# Relative durations
"minutes ago", "hours ago", "days ago", "weeks ago",
```

**Rationale:** Duration expressions are not specific dates per HIPAA. "Fever for three days" is timeline, not PHI.

**Caution:** Use existing substring matching (already implemented for DATE_TIME) to catch variants.

### Respiratory Flow Terms (LOCATION deny list)
```python
# Oxygen delivery modalities
"high",      # "high flow", "on high", "high risk"
"low",       # "low flow", "low risk"
"air",       # "room air", "on air"
"flow",      # "high flow", "low flow"
```

**Rationale:** Medical context terms, not geographic locations. NER commonly misclassifies due to capitalization.

**Caution:** Word boundary checking CRITICAL here to avoid filtering names like "Higham" or "Highland Park".

### Medical Conditions (PERSON deny list - optional P2)
```python
# Phonetically similar to names but medically unambiguous
"bilirubin",  # "Billy Rubin" phonetic, but clearly medical in context
"ARFID",      # Eating disorder acronym
"citrus",     # Dietary term
"diuresis",   # Fluid status term
```

**Rationale:** Documented false positives from Phase 6 real handoff testing. Not common names (verified against SSA database).

## Success Criteria

v2.1 milestone is complete when:

**Measurement approach:**
1. Run evaluation on synthetic dataset BEFORE Phase 2 changes (baseline metrics)
2. Capture false positive counts by entity type
3. Implement deny list expansion + matching strategy fix
4. Run evaluation AFTER changes
5. Verify improvement without regression

**Quantitative targets:**
- [ ] DATE_TIME false positives reduced by ≥20% (duration phrase filtering)
- [ ] LOCATION false positives reduced by ≥15% (respiratory flow filtering)
- [ ] Zero new false negatives introduced (recall ≥90% maintained)
- [ ] Precision improved without sacrificing recall (precision ≥70%)

**Qualitative validation:**
- [ ] Real handoff transcript test (Session 3) produces clinically usable output
- [ ] "three days" and "two weeks" preserved in duration contexts
- [ ] "placed on high flow" preserves medical terminology
- [ ] No patient names leaked (Higham, Highland, etc. still redacted)

**Infrastructure criteria:**
- [ ] All tests integrated into pytest framework (`pytest tests/ -v`)
- [ ] CI/CD passes with new regression tests
- [ ] Documentation updated with deny list rationale and restart requirement

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| **Stack** | HIGH | Existing infrastructure proven (500+ handoffs, Faker, pytest). Simple extensions only. |
| **Features** | HIGH | Deny list patterns documented from real handoff testing (Phase 6). Evidence-based additions. |
| **Architecture** | HIGH | No fundamental changes needed. Substring matching already proven for DATE_TIME entity. |
| **Pitfalls** | HIGH | Project experienced key pitfalls (caching, case sensitivity) in Phases 3-6. Mitigation documented. |

**Overall confidence: HIGH (94%)**

### Gaps to Address

**Word boundary regex with punctuation:** Standard `\b` word boundaries don't match hyphenated terms ("high-flow"). May need `(?<!\w)term(?!\w)` pattern for non-alphanumeric boundaries. **Resolution:** Test with punctuation variants in Phase 3, expand deny list with explicit entries if needed.

**Optimal deny list term specificity:** Trade-off between "high flow" (multi-word, precise) vs "high" (single word, broader). **Resolution:** Start with single words for v2.1, monitor for over-filtering, add multi-word variants if issues arise.

**Server restart requirement visibility:** Config caching caused 21 handoffs of debugging in Phase 6. **Resolution:** Add prominent documentation in README and config.py comments. Consider cache-busting for development mode in future phase.

## Sources

### Primary (HIGH confidence)
- **Existing codebase analysis** — `app/config.py` (lines 95-197 deny lists), `app/deidentification.py` (lines 185-210 filtering logic), `test_presidio.py` (21-case harness)
- **Phase 3 Research (03-RESEARCH.md)** — Evidence-based deny list expansion methodology, case-insensitive bug documentation
- **Phase 6 Pattern Analysis (REAL_HANDOFF_VALIDATION.md)** — Session 1 (21 handoffs, 65 false positives), Session 2 (6 handoffs, 0 errors)
- **HIPAA Safe Harbor Guidance** — Ages <90 not PHI, dates except year must be removed, geographic locations are PHI
- **Presidio Official Documentation** — Deny list best practices, recognizer development patterns

### Secondary (MEDIUM confidence)
- **Clinical NLP temporal expression research** — SUTime temporal types (DATE, TIME, DURATION, SET), duration vs date distinction
- **Presidio deny list tutorial** — Case-insensitive matching, per-entity deny lists
- **Python regex word boundaries** — `\b` syntax, lookahead/lookbehind patterns

### Tertiary (LOW confidence)
- **Medical abbreviation dictionaries** — General clinical NLP challenges (not deny list specific)
- **String matching methods** — Exact vs substring vs fuzzy matching trade-offs

---

*Research completed: 2026-01-28*
*Ready for roadmap: yes*
