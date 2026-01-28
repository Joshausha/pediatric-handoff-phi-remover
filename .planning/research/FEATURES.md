# Features Research: Deny List Patterns for Over-Detection Prevention

**Domain:** Clinical PHI de-identification deny list patterns
**Researched:** 2026-01-28
**Confidence:** HIGH

## Executive Summary

This research identifies clinical phrase patterns commonly misclassified as PHI by general-purpose NER models, documenting the deny list patterns needed to prevent over-detection in pediatric handoff transcription. Based on analysis of existing codebase implementation, real handoff testing results (27 handoffs), and clinical NLP best practices, this document categorizes deny list needs into table stakes (essential for clinical utility), differentiators (nice-to-have precision improvements), and anti-features (patterns that should remain detected).

**Key Finding:** The project has already implemented comprehensive deny lists across all major categories through iterative real-world testing (Phases 3-6). Current deny lists include:
- DATE_TIME: 38 patterns (dosing schedules, age descriptors, duration phrases)
- LOCATION: 14 medical abbreviations
- PERSON: 21 role words and medical abbreviations
- GUARDIAN_NAME: 4 generic relationship terms
- PEDIATRIC_AGE: 7 generic age categories

**Gap Identified:** Current implementation lacks duration word patterns ("three days", "two weeks") and respiratory flow terminology ("high flow", "placed on high") that cause over-detection in clinical text.

## Table Stakes - Must Have for Clinical Utility

These deny list patterns are essential for preserving clinical decision-making information. Missing any of these renders transcripts clinically unusable.

### 1. Age Descriptors (✅ IMPLEMENTED)

**Pattern Category:** DATE_TIME entity over-detection of patient ages

| Pattern | Clinical Context | Why Essential | Status |
|---------|------------------|---------------|--------|
| `X year old`, `X month old`, `X week old`, `X day old` | "18 year old male" | Age determines treatment protocols | ✅ Phase 5 |
| Hyphenated variants: `X-year-old`, `X-month-old` | "7-year-old female" | Common transcription format | ✅ Phase 6 |
| Compound ages: `X week X day old` | "3 week 2 day old" | Neonatal precision required | ✅ Existing |
| Gestational age: `X weeks gestation` | "Born at 36 weeks gestation" | Determines NICU care level | ✅ Existing |

**Evidence from Testing:**
- Session 1 (21 handoffs): 100% affected (42 age redactions)
- Root cause: DATE_TIME recognizer matching age patterns
- Fix: Substring matching in deny list (`"years old" in "18 year old"`)
- Result: Session 2 (6 handoffs) - 0 errors

**Implementation Note:** Ages under 90 are NOT PHI under HIPAA Safe Harbor method. Only ages 90+ require redaction.

### 2. Dosing Schedules (✅ IMPLEMENTED)

**Pattern Category:** DATE_TIME entity over-detection of medication timing

| Pattern | Clinical Context | Why Essential | Status |
|---------|------------------|---------------|--------|
| `q4h`, `q6h`, `q8h`, `q12h` | "Tylenol q6h" | Determines medication timing | ✅ Phase 3 |
| `BID`, `TID`, `QID` | "Amoxicillin BID" | Dosing frequency critical | ✅ Phase 3 |
| `PRN`, `prn` | "Albuterol PRN" | As-needed vs scheduled | ✅ Phase 3 |
| `daily`, `nightly`, `qd`, `qhs` | "Melatonin nightly" | Timing affects compliance | ✅ Phase 3 |

**Evidence:** Phase 2 baseline found 354 DATE_TIME false positives (35.3% precision). Dosing schedules are NOT timestamps under HIPAA.

### 3. Clinical Timeline References (✅ IMPLEMENTED)

**Pattern Category:** DATE_TIME entity over-detection of relative time

| Pattern | Clinical Context | Why Essential | Status |
|---------|------------------|---------------|--------|
| `today`, `tonight`, `yesterday`, `tomorrow`, `overnight` | "Started today" | Disease progression tracking | ✅ Phase 3 |
| `day 1`, `day 2`, ... `day 14` | "Day 3 of illness" | Clinical course timeline | ✅ Phase 3 |
| `day of life` (DOL), `dol 1`, ... `dol 7` | "DOL 2" (neonatal) | Neonatal timeline critical | ✅ Phase 3 |
| `this morning`, `this afternoon`, `this evening`, `last night` | "Vomited this morning" | Symptom timing | ✅ Phase 6 |

**HIPAA Rationale:** Generic time references without specific dates are not identifiable under Safe Harbor. "Day 3 of illness" does not reveal admission date.

### 4. Medical Abbreviations as LOCATION (✅ IMPLEMENTED)

**Pattern Category:** LOCATION entity over-detection of routes/modalities

| Abbreviation | Medical Meaning | Why Essential | Status |
|--------------|-----------------|---------------|--------|
| `NC` | Nasal cannula | Respiratory support type | ✅ Phase 3 |
| `RA` | Room air | Baseline oxygenation | ✅ Phase 3 |
| `OR`, `ER`, `ED` | Operating/Emergency room (generic) | Generic locations, not patient-identifying | ✅ Phase 3 |
| `IV`, `PO`, `IM`, `SQ`, `PR` | Routes of administration | Medication route critical | ✅ Phase 3 |
| `GT`, `NG`, `OG`, `NJ` | Feeding tube types | Nutrition delivery method | ✅ Phase 3 |

**Evidence:** These are medical abbreviations, not geographic locations. NER models commonly misclassify due to capitalization patterns.

### 5. Role Words as PERSON (✅ IMPLEMENTED)

**Pattern Category:** PERSON entity over-detection of generic relationships

| Pattern | Clinical Context | Why Essential | Status |
|---------|------------------|---------------|--------|
| `mom`, `dad`, `parent`, `guardian`, `caregiver` | "Contact mom" | Relationship, not name | ✅ Phase 3 |
| `nurse`, `doctor`, `attending`, `resident`, `fellow` | "Nurse administered" | Generic role | ✅ Phase 3 |
| `NP`, `PA`, `RN`, `LPN`, `CNA` | "RN called" | Professional abbreviations | ✅ Phase 3 |
| `baby`, `infant`, `newborn`, `neonate` | "Baby is stable" | Generic descriptor | ✅ Phase 4 |

**Evidence:** Session 1 found "stable" detected as person name. Generic relationship words are not PHI.

## Differentiators - Nice to Have Precision Improvements

These patterns improve precision and user experience but are not critical for clinical decision-making. System is usable without these.

### 6. Duration Phrases (⚠️ GAP - MISSING)

**Pattern Category:** DATE_TIME entity over-detection of time spans

| Pattern | Clinical Context | Why Helpful | Priority |
|---------|------------------|-------------|----------|
| `three days`, `two weeks`, `five minutes` | "Fever for three days" | Duration vs specific date | **P1-High** |
| `X hours ago`, `X minutes ago` | "Started two hours ago" | Relative timing | **P1-High** |
| `X hours`, `X minutes`, `X seconds` | "Lasted five minutes" | Event duration | P2-Medium |

**Evidence from Milestone Context:**
- "three days", "two weeks" being flagged as DATE
- These are duration expressions, not specific dates
- Not PHI under HIPAA (no identifiable timestamp)

**Clinical Impact:** Medium - Loses precision of symptom timeline but doesn't prevent diagnosis

**Research Finding:** SUTime (Stanford temporal NER) identifies 4 temporal types: DATE, TIME, DURATION, and SET. DURATION expressions like "three days" should not be treated as DATE entities.

**Recommended Implementation:**
```python
deny_list_date_time: list[str] = Field(
    default=[
        # ... existing patterns ...
        # Duration phrases (not specific dates)
        "minutes", "hours", "days", "weeks", "months",  # Generic durations
        "three minutes", "two hours", "five days", "two weeks",  # Specific durations
        "minutes ago", "hours ago", "days ago", "weeks ago",  # Relative durations
    ]
)
```

**Caution:** Use substring matching (existing implementation) to catch variants. Pattern "hours ago" should match "two hours ago".

### 7. Respiratory Therapy Terms as LOCATION (⚠️ GAP - MISSING)

**Pattern Category:** LOCATION entity over-detection of oxygen delivery methods

| Pattern | Clinical Context | Why Helpful | Priority |
|---------|------------------|-------------|----------|
| `high flow`, `high-flow` | "On high flow oxygen" | Respiratory modality | **P1-High** |
| `placed on high` | "Placed on high flow" | Common phrasing | **P1-High** |
| `low flow` | "Transitioned to low flow" | Oxygen titration | P2-Medium |

**Evidence from Milestone Context:**
- "placed on high", "on high flow" being flagged as LOCATION
- "high" detected as geographic location (common NER error)

**Clinical Impact:** Medium - Loses respiratory support detail but diagnosis still clear

**Recommended Implementation:**
```python
deny_list_location: list[str] = Field(
    default=[
        # ... existing abbreviations ...
        # Respiratory therapy terms
        "high flow", "low flow",  # Oxygen delivery modalities
        "high", "low",  # May be too broad - needs testing
    ]
)
```

**Caution:** Adding standalone "high" or "low" may be too aggressive. Consider multi-word patterns only ("high flow" but not "high" alone) or require context analysis.

### 8. Medical Conditions as PERSON (✅ PARTIALLY IMPLEMENTED)

**Pattern Category:** PERSON entity over-detection of phonetically similar medical terms

| Term | Why Misclassified | Clinical Impact | Status |
|------|-------------------|-----------------|--------|
| `bilirubin` | "Billy Rubin" (phonetic name) | Jaundice assessment lost | ⚠️ Not in deny list |
| `ARFID` | Acronym pattern | Eating disorder obscured | ⚠️ Not in deny list |
| `citrus` | Capitalized word | Dietary context lost | ⚠️ Not in deny list |
| `diuresis` | Phonetic similarity | Fluid status obscured | ⚠️ Not in deny list |
| `DKA`, `CT`, `MRI`, `EEG`, `ICU` | Medical abbreviations | Diagnosis/location lost | ✅ Phase 6 |

**Evidence:** Session 1 (real handoff testing) found 5 medical terms detected as person names.

**Priority:** P3-Medium (clinical utility affected but not patient safety)

**Recommendation:** Add to PERSON deny list based on documented false positives from real handoff testing.

### 9. Unit Name Preservation During ROOM Redaction (⚠️ PARTIAL GAP)

**Pattern Category:** ROOM entity pattern needs context-aware redaction

| Pattern | Desired Behavior | Current Behavior | Priority |
|---------|------------------|------------------|----------|
| `PICU bed 12` | `PICU bed [ROOM]` (preserve unit) | `[ROOM] bed [ROOM]` (loses unit) | P2-Medium |
| `NICU room 4B` | `NICU room [ROOM]` | `[ROOM] room [ROOM]` | P2-Medium |

**Evidence:** Test case "Patient name - Baby LastName" over-redacts both 'bed' and unit name.

**Clinical Impact:** Low - Unit names like PICU/NICU are generic locations (not patient-identifying)

**Technical Challenge:** Requires pattern-aware redaction, not simple deny list. ROOM recognizer uses regex patterns that may capture unit name.

**Recommendation:** Modify ROOM recognizer patterns to use lookbehind (preserve unit prefix). This is a recognizer fix, not a deny list addition.

### 10. Generic Age Categories (✅ IMPLEMENTED)

**Pattern Category:** PEDIATRIC_AGE entity over-detection

| Pattern | Why Not PHI | Status |
|---------|-------------|--------|
| `infant`, `toddler`, `child`, `adolescent`, `teen` | Generic developmental stage | ✅ Phase 3 |
| `newborn`, `neonate` | Generic descriptor | ✅ Phase 3 |

**Evidence:** Existing implementation correct. These are broad categories, not specific identifying ages.

## Anti-Features - Patterns That Should Remain Detected

These patterns should NOT be added to deny lists. They are legitimate PHI or have high risk of missing actual identifiers.

### Anti-Feature 1: Specific City Names

**Example:** "Boston", "New York", "Los Angeles"

**Why Not Add:**
- Geographic locations ARE HIPAA identifiers (Safe Harbor element #4: cities/towns/zip codes)
- Context matters: "Family wants to go to Boston" (not PHI) vs "Patient lives in Boston" (PHI)
- Better to over-redact than leak location data

**Decision:** Accept LOCATION over-detection for city names. Presidio's conservative approach is correct.

**Evidence from Testing:** Session 1 found "Boston" → [LOCATION]. Documented as "Accept as working as intended" (P4-Low priority).

### Anti-Feature 2: Common First Names

**Example:** "Mike", "Sarah", "John"

**Why Not Add:**
- These are actual person names in most contexts
- Risk of missing guardian names: "Dad Mike" should redact "Mike"
- Guardian name recognizer uses lookbehind to preserve relationship word ("Dad [NAME]")

**Decision:** Do NOT add common names to deny list. Rely on Presidio's context analysis.

### Anti-Feature 3: Numeric Patterns

**Example:** Standalone "12", "4", "36"

**Why Not Add:**
- Could be room numbers, bed numbers, MRNs, ages
- Context-dependent: "room 12" (PHI) vs "12 mg" (clinical)
- Adding numbers to deny list would break all numeric PHI detection

**Decision:** Do NOT add numeric patterns to deny list. Handle via entity-specific recognizers.

### Anti-Feature 4: Time Words That Could Be Dates

**Example:** "Monday", "January", "summer"

**Why Not Add:**
- "Admitted Monday" could identify patient if combined with other data
- Safe Harbor requires removing "all elements of dates" except year
- Better to over-redact temporal information

**Decision:** Do NOT add month names, day names, or season names to DATE_TIME deny list.

**Exception:** Generic relative time ("today", "tomorrow") already in deny list because they lack specific date information.

### Anti-Feature 5: Medical Facility Names

**Example:** "MGH", "Children's Hospital"

**Why Not Add:**
- Facility names are LOCATION identifiers under HIPAA
- "Transferred from MGH" could narrow patient population
- Generic "hospital" is acceptable, but specific names are PHI

**Decision:** Do NOT add hospital/facility names to LOCATION deny list.

### Anti-Feature 6: Ages 90 and Above

**Example:** "92 year old", "95-year-old"

**Why Not Add:**
- HIPAA Safe Harbor specifically requires redacting ages 90+
- Small population makes ages 90+ potentially identifying
- Age deny list should NOT include high ages

**Decision:** Current deny list correctly preserves ages <90, redacts 90+. Do not expand to cover 90+ ages.

## Implementation Priorities

### Phase 9 (Current Milestone) - Over-Detection Fixes

**Goal:** Fix duration phrases and respiratory terminology over-detection

| Priority | Pattern Category | Impact | Effort | Status |
|----------|------------------|--------|--------|--------|
| **P1-High** | Duration phrases ("three days", "two weeks") | Medium clinical utility | Low (deny list addition) | 🔴 Missing |
| **P1-High** | Respiratory flow terms ("high flow", "placed on high") | Medium clinical utility | Low-Medium (needs testing) | 🔴 Missing |
| P2-Medium | Medical conditions as PERSON (bilirubin, ARFID) | Low-Medium precision | Low (deny list addition) | 🟡 Optional |
| P2-Medium | Unit name preservation (PICU/NICU during ROOM redaction) | Low clinical utility | Medium (recognizer modification) | 🟡 Optional |

### Post-Phase 9 Backlog

| Priority | Pattern Category | Reason to Defer |
|----------|------------------|-----------------|
| P3-Low | Additional medical abbreviations | No documented false positives yet |
| P3-Low | Standalone "high"/"low" in LOCATION deny list | Risk of over-broad filtering |
| P4-Accepted | City name over-detection | Working as intended per HIPAA |
| P4-Accepted | Medical facility names as LOCATION | Correct PHI detection |

## Research Methodology

### Sources Analyzed

**HIGH Confidence:**
1. **Existing Codebase Implementation** (`app/config.py`, `app/deidentification.py`)
   - Lines 96-197: Complete deny list implementation with 38 DATE_TIME patterns, 14 LOCATION, 21 PERSON
   - Proven through 27 real handoff tests (Phase 6 validation)

2. **Real Handoff Testing Results** (`.planning/phases/06-real-handoff-testing/REAL_HANDOFF_VALIDATION.md`)
   - Session 1: 21 handoffs, 65 false positives documented
   - Session 2: 6 handoffs, 0 errors (validates deny list fixes)
   - Patterns identified: age over-redaction, medical terms as PERSON

3. **Phase 3 Research** (`.planning/phases/03-deny-list-refinement/03-RESEARCH.md`)
   - Evidence-based deny list expansion methodology
   - Case-insensitive matching standard
   - Documented false positive categories

4. **HIPAA Safe Harbor Guidance** ([HHS.gov De-identification Guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html))
   - Ages <90 are NOT PHI (can be preserved)
   - Dates except year must be removed
   - Geographic locations smaller than state are PHI

**MEDIUM Confidence:**
5. **Clinical NLP Temporal Expression Research** ([ClinicalNLP 2025 Workshop](https://aclanthology.org/2025.clinicalnlp-1.pdf))
   - SUTime temporal types: DATE, TIME, DURATION, SET
   - Duration expressions ("three days") distinct from dates
   - Temporal information crucial for disease progression tracking

6. **Presidio Documentation** ([Microsoft Presidio Deny List Best Practices](https://microsoft.github.io/presidio/tutorial/01_deny_list/))
   - Deny lists standard for domain-specific false positives
   - Case-insensitive matching recommended
   - Per-entity deny lists avoid type confusion

**LOW Confidence:**
7. **WebSearch Results** (no specific duration phrase deny list patterns found in 2026 literature)
   - General clinical NLP challenges documented
   - Specific duration phrase patterns inferred from temporal NER research
   - Respiratory flow terminology gap identified through milestone context, not published research

### Gap Analysis

**What's Missing from Current Implementation:**
1. Duration word patterns (number + time unit: "three days", "two weeks")
2. Respiratory flow terminology ("high flow", "placed on high")
3. Medical condition phonetic false positives (bilirubin, ARFID) - documented but not yet added

**What's Covered Well:**
1. Age descriptors (space and hyphenated variants)
2. Dosing schedules (q4h, BID, PRN)
3. Clinical timeline (day of illness, DOL)
4. Medical abbreviations (routes, locations)
5. Role words and relationships

### Confidence Assessment

| Category | Confidence | Rationale |
|----------|------------|-----------|
| Age descriptors | **HIGH** | Validated with 27 real handoffs, HIPAA guidance clear |
| Dosing schedules | **HIGH** | 354 false positives documented, medical standard |
| Clinical timeline | **HIGH** | Real handoff testing, HIPAA safe harbor compliant |
| Medical abbreviations | **HIGH** | Existing implementation proven in production |
| Duration phrases | **MEDIUM** | Inferred from milestone context + temporal NER research |
| Respiratory flow terms | **MEDIUM** | Milestone context + common clinical phrasing |
| Medical conditions as PERSON | **HIGH** | Documented in Session 1 testing (5 false positives) |
| Unit name preservation | **MEDIUM** | Test case evidence, technical solution needed |

## Success Criteria for Phase 9

**Measurement Approach:**
1. Run evaluation on synthetic dataset BEFORE Phase 9 changes
2. Capture baseline false positive counts by entity type
3. Add duration phrase and respiratory flow deny list patterns
4. Run evaluation AFTER changes
5. Verify:
   - [ ] DATE_TIME false positives reduced by duration phrase filtering
   - [ ] LOCATION false positives reduced by respiratory flow term filtering
   - [ ] No new false negatives introduced (PHI still detected)
   - [ ] Clinical utility preserved (test with sample handoff)

**Target:** Reduce over-detection errors while maintaining 0 false negatives (PHI leaks).

**Validation:** Test with real handoff transcripts (Session 3) to confirm clinical usability.

---

## Sources

**HIPAA Guidance:**
- [De-identification of Protected Health Information: 2026 Update](https://www.hipaajournal.com/de-identification-protected-health-information/)
- [HHS.gov HIPAA Safe Harbor Guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html)

**Clinical NLP Research:**
- [ClinicalNLP 2025 Workshop Proceedings](https://aclanthology.org/2025.clinicalnlp-1.pdf)
- [Stanford SUTime Temporal Tagger](https://nlp.stanford.edu/software/sutime.shtml)

**Presidio Best Practices:**
- [Presidio Deny-list Recognizers Tutorial](https://microsoft.github.io/presidio/tutorial/01_deny_list/)
- [Presidio Best Practices - Developing Recognizers](https://microsoft.github.io/presidio/analyzer/developing_recognizers/)

**Medical NLP Comparison:**
- [John Snow Labs Medical De-identification vs Microsoft Presidio](https://www.johnsnowlabs.com/comparing-john-snow-labs-medical-text-de-identification-with-microsoft-presidio/)

---

**RESEARCH COMPLETE** - Ready for Phase 9 requirements definition and implementation planning.
