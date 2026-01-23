# Architecture Research: PHI Detection Pipeline

**Research Date:** 2026-01-23
**Project:** Pediatric Handoff PHI Remover - Quality Overhaul
**Focus:** Hybrid regex+NER de-identification system structure

---

## Executive Summary

High-quality PHI de-identification systems use a **layered pipeline architecture** where regex recognizers, NER models, deny lists, and validation passes each operate at distinct stages. Improvements should be applied **in reverse order of the data flow** (validation first, then filtering, then detection) to catch issues early without rebuilding the entire pipeline.

**Key Finding:** Presidio's architecture already provides the right structure—the issues are in **configuration** (thresholds, deny lists) and **pattern quality** (regex edge cases), not fundamental design.

---

## Current Flow

### 1. Audio Processing Stage
```
Audio File (WAV/MP3/M4A)
    ↓
faster-whisper (local transcription)
    ↓
Raw Transcript (text)
```

**Current State:** ✅ Working well
**Improvement Opportunity:** None needed

---

### 2. PHI Detection Stage (Presidio Analyzer)

```
Raw Transcript
    ↓
┌─────────────────────────────────────────┐
│   Presidio Analyzer (Parallel)          │
│                                          │
│   ┌───────────────┐  ┌────────────────┐ │
│   │   spaCy NER   │  │ Regex Patterns │ │
│   │  (en_core_    │  │  (Custom       │ │
│   │   web_lg)     │  │   Recognizers) │ │
│   └───────┬───────┘  └────────┬───────┘ │
│           │                   │          │
│           └────────┬──────────┘          │
│                    ↓                     │
│         Combined Entity Results          │
│         (with confidence scores)         │
└─────────────────────────────────────────┘
    ↓
Raw Entity List (PERSON, LOCATION, GUARDIAN_NAME, etc.)
    score_threshold = 0.35 (detection)
```

**Current State:** ⚠️ Needs improvement
**Issues:**
- Threshold too low (0.35) causes false positives
- Regex patterns use lookbehind, miss edge cases (e.g., "Baby LastName" at start of sentence)
- No confidence score adjustment for context

---

### 3. Deny List Filtering Stage

```
Raw Entity List
    ↓
┌─────────────────────────────────────────┐
│   Deny List Filter (in deidentify_text) │
│                                          │
│   for each detected entity:              │
│     if LOCATION and in deny_list:        │
│       SKIP (e.g., "NC", "RA")            │
│     if PERSON and in deny_list:          │
│       SKIP (e.g., "mom", "dad")          │
└─────────────────────────────────────────┘
    ↓
Filtered Entity List
```

**Current State:** ⚠️ Needs improvement
**Issues:**
- Case sensitivity inconsistent (LOCATION uses exact match, PERSON uses case-insensitive)
- Deny lists applied **after** detection (wastes computation)
- No deny lists for other entity types (GUARDIAN_NAME, PEDIATRIC_AGE)

---

### 4. Anonymization Stage

```
Filtered Entity List + Original Text
    ↓
Presidio Anonymizer
    ↓
Anonymized Text ([NAME], [PHONE], [ROOM], etc.)
```

**Current State:** ✅ Working well
**Improvement Opportunity:** None needed

---

### 5. Validation Stage

```
Anonymized Text
    ↓
Presidio Analyzer (re-run)
    score_threshold = 0.7 (validation)
    ↓
Remaining Entity List
    ↓
Check for leaks (score >= 0.8)
    ↓
Validation Result (pass/fail + warnings)
```

**Current State:** ⚠️ Needs improvement
**Issues:**
- Arbitrary thresholds (0.7 detection, 0.8 leak threshold)
- No automated test harness integration
- Validation doesn't inform threshold tuning

---

## Hybrid Regex+NER Patterns

### How Presidio Combines Approaches

Presidio uses a **parallel detection** model where regex and NER run simultaneously, then results are merged:

1. **Regex Recognizers** (custom patterns)
   - Fast, deterministic
   - High precision for structured PHI (MRN, phone numbers)
   - Can use context patterns (e.g., "MRN: 12345678")
   - **Confidence scores are fixed** (set in Pattern definition)

2. **NER Models** (spaCy, transformers)
   - Slower, probabilistic
   - High recall for unstructured PHI (names, locations)
   - Context-aware (understands "Mom Jessica" vs "Jessica came to visit")
   - **Confidence scores are model-generated** (0.0-1.0)

3. **Context Enhancement**
   - Presidio's internal mechanism increases confidence when context words appear
   - Example: "contact" before a phone number → +0.2 confidence boost
   - Applied to **both regex and NER results**

### Best Practices from Research

From [Presidio documentation](https://microsoft.github.io/presidio/analyzer/developing_recognizers/) and [Databricks PHI removal](https://www.databricks.com/blog/2022/06/22/automating-phi-removal-from-healthcare-data-with-natural-language-processing.html):

- **Use regex for structured PHI** (MRN, phone, email) where patterns are predictable
- **Use NER for unstructured PHI** (names, locations) where context matters
- **Avoid over-reliance on lookbehind/lookahead** in regex—they miss edge cases (start/end of line, punctuation variations)
- **Test each recognizer independently** on representative data before integration
- **Performance target:** <100ms per 100 tokens per recognizer

---

## Threshold Architecture

### Where Thresholds Should Be Applied

From [IntuitionLabs review](https://intuitionlabs.ai/articles/open-source-phi-de-identification-tools) and [AWS Comprehend Medical](https://docs.aws.amazon.com/comprehend-medical/latest/dev/textanalysis-phi.html):

#### 1. Detection Threshold (Analyzer Entry Point)
**Location:** `analyzer.analyze(score_threshold=X)`
**Purpose:** Filter out low-confidence detections
**Current Value:** 0.35 (too low)
**Recommendation:** 0.5-0.6 for production use

**Rationale:**
- Lower thresholds (0.3-0.4) increase **recall** (catch more PHI) but also increase **false positives**
- Higher thresholds (0.6-0.8) increase **precision** (fewer false positives) but risk missing PHI
- Medical use case (HIPAA compliance) requires **high recall**, so threshold should be tuned based on test data

#### 2. Entity-Specific Thresholds (Recognizer Level)
**Location:** Pattern definitions in custom recognizers
**Purpose:** Set minimum confidence per pattern
**Current Values:** 0.5-0.85 (reasonable range)
**Recommendation:** Keep as-is, but document reasoning

**Example from current code:**
```python
Pattern(name="mrn_labeled", regex=r"\b(?:MRN|mrn)[:\s#]?\s*(\d{6,10})\b", score=0.85)  # High confidence
Pattern(name="mrn_prefix", regex=r"\b[A-Z]{2}\d{6,8}\b", score=0.6)  # Lower confidence (ambiguous)
```

#### 3. Validation Threshold (Re-analysis)
**Location:** `validate_deidentification()` function
**Purpose:** Catch high-confidence PHI leaks after anonymization
**Current Value:** 0.7 (detection), 0.8 (leak warning)
**Recommendation:** Use **same threshold as detection** (0.5-0.6) for consistency

**Rationale:**
- Using a *higher* threshold in validation (0.7) misses entities that would have been detected initially (0.35)
- Validation should be **at least as strict** as initial detection

#### 4. Deny List Application
**Location:** Between analyzer and anonymizer
**Purpose:** Remove known false positives
**Current Implementation:** Post-detection filter
**Recommendation:** Move to **recognizer context** for better performance

---

### Threshold Tuning Process

From [Databricks guide](https://www.databricks.com/blog/2022/06/22/automating-phi-removal-from-healthcare-data-with-natural-language-processing.html):

1. **Establish Ground Truth**
   - Manually annotate 50-100 representative transcripts
   - Include edge cases (abbreviations, pediatric terms, incomplete sentences)

2. **Test Threshold Range**
   - Run analyzer at 0.3, 0.4, 0.5, 0.6, 0.7 thresholds
   - Measure precision, recall, F1 score at each level

3. **Optimize for HIPAA Compliance**
   - Prioritize **recall** (minimize false negatives = PHI leaks)
   - Accept higher **false positive** rate (over-redaction is safer than under-redaction)

4. **Document Decision**
   - Record chosen threshold and justification in config.py
   - Include performance metrics in documentation

---

## Deny List Design

### Best Practices from Research

From [Nature article on Philter](https://www.nature.com/articles/s41746-020-0258-y) and [IntuitionLabs review](https://intuitionlabs.ai/articles/open-source-phi-de-identification-tools):

#### 1. Organization by Entity Type
**Current Implementation:** ✅ Good
- `deny_list_location` for medical abbreviations (NC, RA, OR)
- `deny_list_person` for generic relationships (mom, dad, nurse)

**Recommendation:** Extend to all custom entity types
- Add `deny_list_guardian_name` for generic guardian terms
- Add `deny_list_pediatric_age` for non-identifying age ranges

#### 2. Case Handling
**Current Implementation:** ⚠️ Inconsistent
- LOCATION: exact match (case-sensitive)
- PERSON: case-insensitive match

**Recommendation:** Normalize to lowercase for all deny lists
```python
# In deidentify_text()
if result.entity_type == "LOCATION" and detected_text.upper() in [w.upper() for w in settings.deny_list_location]:
    continue
```

#### 3. Performance Optimization
**Current Implementation:** ⚠️ Post-detection filter (inefficient)
**Recommendation:** Move to recognizer context

**Before (current):**
```python
# In deidentify_text() - runs AFTER analysis
results = analyzer.analyze(text=text)
for result in results:
    if detected_text in deny_list:
        skip
```

**After (recommended):**
```python
# In recognizer definition - PREVENTS detection
PatternRecognizer(
    supported_entity="LOCATION",
    deny_list=settings.deny_list_location  # Built into Presidio
)
```

#### 4. Maintenance Strategy
**Recommendation:** Track false positives and update deny lists systematically

**Process:**
1. Run test harness (`test_presidio.py`)
2. Identify false positives (e.g., "OR" flagged as location)
3. Add to deny list in `config.py`
4. Re-run tests to confirm fix
5. Document in deny list comments

---

## Improvement Integration Points

### Where Each Type of Improvement Fits

Based on current architecture and research findings, here's the **recommended order** for improvements:

#### Phase 1: Validation & Testing (Foundation)
**Location:** `tests/` directory, `test_presidio.py`
**Changes:**
- Expand test harness with ground truth annotations
- Add threshold sweep testing (0.3-0.7 range)
- Integrate validation into CI/CD pipeline

**Rationale:** Can't improve what you can't measure. Build robust testing first.

**Dependencies:** None (can start immediately)

---

#### Phase 2: Threshold Optimization (Configuration)
**Location:** `app/config.py`, `app/deidentification.py`
**Changes:**
- Update `phi_score_threshold` from 0.35 → 0.5 (based on test results)
- Make validation threshold configurable (remove hardcoded 0.7)
- Ensure validation uses same threshold as detection

**Rationale:** Quick wins with minimal code changes. Tests from Phase 1 inform optimal values.

**Dependencies:** Requires Phase 1 (test harness) for data-driven tuning

---

#### Phase 3: Deny List Refinement (Filtering)
**Location:** `app/config.py`, `app/deidentification.py`
**Changes:**
- Normalize case handling (all deny lists use case-insensitive)
- Add deny lists for GUARDIAN_NAME, PEDIATRIC_AGE
- Move deny list filtering to recognizer context (performance)

**Rationale:** Reduces false positives without changing detection logic.

**Dependencies:** Requires Phase 1 (test harness) to identify false positives

---

#### Phase 4: Regex Pattern Improvements (Detection)
**Location:** `app/recognizers/pediatric.py`, `app/recognizers/medical.py`
**Changes:**
- Fix lookbehind patterns to handle edge cases (start of line, punctuation)
- Add alternative patterns for common variations
- Increase context words for confidence boosting

**Rationale:** Most invasive changes. Should be validated with Phases 1-3 in place.

**Dependencies:** Requires Phases 1-3 (testing, thresholds, deny lists) to measure impact

---

#### Phase 5: NER Model Tuning (Optional, Advanced)
**Location:** `app/config.py` (spacy_model selection)
**Changes:**
- Evaluate transformer-based models (HuggingFace) vs spaCy
- Consider domain-specific medical NER models
- Benchmark performance (accuracy vs speed)

**Rationale:** Highest impact but most complex. Only pursue if Phases 1-4 insufficient.

**Dependencies:** Requires Phases 1-4 complete to establish baseline

---

## Build Order Implications

### Sequential vs Parallel Work

**Sequential (Must Complete First):**
1. Phase 1 (Validation & Testing) → **Blocks all other phases**
2. Phase 2 (Threshold Optimization) → **Blocks Phases 3-4**

**Parallel (Can Work Simultaneously):**
- Phase 3 (Deny List Refinement) and Phase 4 (Regex Patterns) can be developed in parallel **after Phase 2 complete**
- Phase 5 (NER Tuning) is independent research track

### Integration Risk

**Low Risk (Safe to Deploy Incrementally):**
- Phase 1: Testing (no production changes)
- Phase 2: Thresholds (configuration only)
- Phase 3: Deny lists (improves precision, minimal side effects)

**Medium Risk (Requires Careful Testing):**
- Phase 4: Regex patterns (could introduce new false positives/negatives)

**High Risk (Major Architectural Change):**
- Phase 5: NER model swap (performance, compatibility, retraining required)

---

## Recommended Roadmap

Based on this architecture research, here's the suggested phase structure:

```
Milestone: PHI Detection Quality Overhaul

Phase 1: Establish Ground Truth & Testing Framework
  - Create annotated test dataset (50-100 transcripts)
  - Build threshold sweep testing
  - Integrate validation into test harness

Phase 2: Optimize Thresholds
  - Run threshold analysis (0.3-0.7 range)
  - Update config.py with data-driven values
  - Document threshold selection rationale

Phase 3: Refine Deny Lists
  - Normalize case handling across all deny lists
  - Add deny lists for custom entities
  - Move filtering to recognizer context

Phase 4: Improve Regex Patterns
  - Fix lookbehind edge cases
  - Add alternative pattern variations
  - Enhance context word lists

Phase 5 (Optional): Evaluate Advanced NER
  - Benchmark transformer models
  - Test domain-specific medical NER
  - Cost-benefit analysis vs current spaCy
```

---

## Key Architectural Principles

1. **Fail-Safe Design:** Over-redaction is safer than PHI leaks in HIPAA context
2. **Measurement-Driven:** All improvements must be validated with test harness
3. **Incremental Changes:** Small, testable improvements over big rewrites
4. **Performance Budget:** <100ms per 100 tokens per recognizer
5. **Documentation:** Every threshold and pattern must have documented rationale

---

## Sources

- [Microsoft Presidio GitHub](https://github.com/microsoft/presidio)
- [Presidio Analyzer Documentation](https://microsoft.github.io/presidio/analyzer/)
- [Presidio Best Practices](https://microsoft.github.io/presidio/analyzer/developing_recognizers/)
- [Databricks: Automating PHI Removal with NLP](https://www.databricks.com/blog/2022/06/22/automating-phi-removal-from-healthcare-data-with-natural-language-processing.html)
- [IntuitionLabs: Open Source PHI De-Identification Review](https://intuitionlabs.ai/articles/open-source-phi-de-identification-tools)
- [AWS Comprehend Medical PHI Detection](https://docs.aws.amazon.com/comprehend-medical/latest/dev/textanalysis-phi.html)
- [Nature: Philter PHI De-Identification](https://www.nature.com/articles/s41746-020-0258-y)
- [HHS: De-identification Methods for PHI](https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html)
- [HIPAA Journal: De-identification 2026 Update](https://www.hipaajournal.com/de-identification-protected-health-information/)
- [Censinet: 18 HIPAA Identifiers](https://censinet.com/perspectives/18-hipaa-identifiers-for-phi-de-identification)

---

**End of Research Document**
