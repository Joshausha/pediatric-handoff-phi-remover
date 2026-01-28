# Stack Research: Over-Detection Quality Pass

**Research Date:** 2026-01-28
**Milestone:** v2.1 Over-Detection Quality Pass
**Focus:** Test script generation and deny list expansion methodology
**Confidence:** HIGH

## Executive Summary

This research focuses on **practical approaches for a single developer** to fix over-detection issues (duration phrases, medical terminology incorrectly flagged as PHI). The project already has excellent test infrastructure (Faker-based generation, 500+ synthetic handoffs, I-PASS templates). The goal is to enhance test coverage with realistic clinical language patterns and systematically expand deny lists—NOT to add complex tooling.

**Key Finding**: Extend existing Faker-based test generation with medical duration/timeline providers, and use pytest parameterization + corpus analysis for systematic deny list expansion. Keep it simple, practical, and integrated with existing pytest workflow.

---

## Test Script Generation

### Existing Infrastructure (DO NOT REBUILD)

**Already in place:**
- **Faker-based generation**: `tests/generate_test_data.py` with custom medical providers
- **I-PASS templates**: 27+ templates in `tests/handoff_templates.py` covering all I-PASS components
- **500+ synthetic handoffs**: `tests/synthetic_handoffs.json` with ground truth labels
- **Adversarial templates**: Speech artifacts, boundary cases, transcription errors

**What's working well:**
- Template-based approach ensures I-PASS structure compliance
- Faker providers generate diverse realistic PHI
- Ground truth span tracking for precise evaluation

### Gap: Clinical Language Patterns (Duration, Timeline, Medical Context)

**Current over-detection issues from STATE.md:**
- "Currently on high" flagged as LOCATION (should preserve "high flow" medical terminology)
- Duration phrases like "three days" flagged as DATE_TIME (clinical timeline, not PHI)

**Root cause:** Templates don't generate enough medical context phrases that look like PHI but aren't.

### RECOMMENDED: Extend Faker Providers (Minimal Effort, High Impact)

**Approach:** Add 2-3 new Faker providers to existing `tests/medical_providers.py`

#### 1. ClinicalTimelineProvider

Generate duration/timeline phrases that should NOT be flagged:

```python
class ClinicalTimelineProvider(BaseProvider):
    """Non-PHI clinical timeline phrases."""

    def duration_phrase(self) -> str:
        """Generate duration that looks like DATE but isn't PHI."""
        return self.random_element([
            "three days ago",
            "five hours prior",
            "two weeks of symptoms",
            "ongoing for days",
            "started yesterday",
            "since this morning",
        ])

    def day_of_illness(self) -> str:
        """Day X of illness (clinical timeline, not PHI)."""
        day = self.random_int(min=1, max=14)
        return f"day {day} of illness"

    def relative_timepoint(self) -> str:
        """Relative time references."""
        return self.random_element([
            "overnight",
            "this afternoon",
            "last night",
            "this morning",
            "earlier today",
        ])
```

**Rationale:** These are FALSE POSITIVES that need deny list coverage. By generating them in test scripts, you systematically identify what needs filtering.

#### 2. MedicalContextProvider

Generate phrases with medical abbreviations that look like LOCATION/PERSON but aren't:

```python
class MedicalContextProvider(BaseProvider):
    """Medical phrases that NER models commonly misclassify."""

    def respiratory_phrase(self) -> str:
        """Respiratory support phrases (NC, RA commonly flagged as LOCATION)."""
        return self.random_element([
            "on high flow nasal cannula",
            "currently on NC at 2 liters",
            "placed on high flow",
            "weaning from NC to RA",
            "stable on room air",
            "requiring NC support",
        ])

    def location_like_abbrev(self) -> str:
        """Medical abbreviations that look like locations."""
        return self.random_element([
            "transferred from OR",  # Operating Room
            "seen in ER",  # Emergency Room
            "IV access obtained",
            "given PO medications",
            "NG tube placement",
        ])

    def person_like_abbrev(self) -> str:
        """Medical abbreviations that look like person names."""
        return self.random_element([
            "CT scan ordered",
            "EKG changes noted",
            "MRI scheduled",
            "admit to ICU",
        ])
```

**Rationale:** Your existing deny lists have NC, RA, OR, etc., but templates don't test them in realistic contexts. This generates the edge cases.

#### 3. Integration: Add to Existing Templates

**Update `handoff_templates.py` with new placeholders:**

```python
# Add to CLINICAL_HEAVY_TEMPLATES
OVER_DETECTION_EDGE_CASES = [
    "{{pediatric_age}} admitted {{duration_phrase}} with {{condition}}. "
    "{{respiratory_phrase}}, sats stable.",

    "Patient stable overnight. {{relative_timepoint}} had temp spike. "
    "{{day_of_illness}}, improving trend.",

    "{{location_like_abbrev}} for {{condition}}. Now {{respiratory_phrase}}. "
    "Plan: {{person_like_abbrev}} tomorrow.",
]
```

**Effort:** ~50 lines of code in existing files. No new dependencies.

**Expected outcome:**
- Generate 100+ test cases with medical context phrases
- Systematically identify gaps in deny lists
- Validate deny list fixes prevent regressions

### ALTERNATIVE CONSIDERED: LLM-based Generation (NOT RECOMMENDED)

**Approach:** Use GPT-4/Claude to generate realistic handoffs

**Why NOT:**
- **Inconsistent output:** LLMs hallucinate, produce non-deterministic results
- **No ground truth labels:** Would need manual annotation (time-consuming)
- **External dependency:** API costs, rate limits
- **Your existing system is better:** Faker generates diverse, labeled, reproducible data

**When to reconsider:** If you need 10,000+ test cases (current 500 is sufficient for v2.1)

**Confidence:** 95% - Your Faker approach is superior for this use case

---

## Deny List Expansion Methodology

### Current State

**Existing deny lists in `app/config.py`:**
- `deny_list_location`: 14 medical abbreviations (NC, RA, OR, etc.)
- `deny_list_person`: 20+ relationship terms (mom, dad, doctor, etc.)
- `deny_list_date_time`: 30+ relative time phrases (today, yesterday, etc.)
- `deny_list_guardian_name`: Speech artifacts (uh, um)
- `deny_list_pediatric_age`: Generic age terms (infant, toddler)

**What's working:**
- Deny lists are entity-specific (different lists for different PHI types)
- Case-insensitive substring matching for DATE_TIME (catches "5 months old")
- Well-documented rationale for each entry

**Gap:** No systematic process for discovering NEW terms to add

### RECOMMENDED: pytest Parameterization + Corpus Analysis

**3-step systematic approach for deny list expansion:**

#### Step 1: Corpus Analysis (Find Candidates)

**Extract frequently misclassified terms from test failures:**

```python
# tests/analyze_false_positives.py
from collections import Counter
from tests.evaluate_presidio import evaluate_on_dataset

def find_false_positive_patterns(dataset_path, entity_type):
    """Find commonly misclassified non-PHI terms."""
    results = evaluate_on_dataset(dataset_path)

    # Extract false positives (flagged but shouldn't be)
    false_positives = Counter()
    for result in results:
        if result.entity_type == entity_type and result.is_false_positive:
            false_positives[result.text.lower()] += 1

    # Return top 20 candidates
    return false_positives.most_common(20)

# Usage
candidates = find_false_positive_patterns("tests/synthetic_handoffs.json", "LOCATION")
# Output: [('high', 15), ('flow', 12), ('iv', 8), ...]
```

**Effort:** ~30 lines of code using existing evaluation infrastructure
**Output:** Data-driven list of deny list candidates

#### Step 2: Clinical Validation (Verify Safety)

**Manual review with clinical judgment:**

For each candidate term, ask:
1. **Is this EVER PHI?** (e.g., "NC" is NEVER a location in pediatrics)
2. **Is this ALWAYS safe to preserve?** (e.g., "High Street" IS a location)
3. **Context-dependent?** (needs pattern-based filtering, not deny list)

**Create validation checklist:**

```markdown
| Term | Entity Type | Ever PHI? | Always Safe? | Decision | Rationale |
|------|-------------|-----------|--------------|----------|-----------|
| high | LOCATION | No | Yes | ADD | Medical context (high flow) |
| flow | LOCATION | No | Yes | ADD | Always medical in handoffs |
| iv | LOCATION | No | Yes | ADD | IV (intravenous) never location |
| boston | LOCATION | YES | No | REJECT | City names ARE PHI |
```

**Effort:** 15 minutes per 10 candidates (clinical resident expertise)
**Rationale:** HIPAA compliance requires clinical judgment, not automated decisions

#### Step 3: Regression Test Suite (Prevent Over-Filtering)

**Use pytest parameterization to lock in deny list behavior:**

```python
# tests/test_deny_lists.py

import pytest
from app.deidentification import deidentify_text

@pytest.mark.parametrize("text,entity_type,should_flag", [
    # LOCATION deny list - should NOT flag
    ("Patient on NC at 2L", "LOCATION", False),  # NC = nasal cannula
    ("Placed on high flow", "LOCATION", False),  # high = medical context
    ("Transferred from OR", "LOCATION", False),  # OR = operating room

    # LOCATION - should STILL flag
    ("Lives in Boston", "LOCATION", True),  # City names ARE PHI
    ("Transferred from MGH", "LOCATION", True),  # Hospital names ARE PHI

    # DATE_TIME deny list - should NOT flag
    ("Day 3 of illness", "DATE_TIME", False),  # Clinical timeline
    ("Started three days ago", "DATE_TIME", False),  # Duration phrase

    # DATE_TIME - should STILL flag
    ("Admitted on January 15", "DATE_TIME", True),  # Specific date IS PHI
])
def test_deny_list_filtering(text, entity_type, should_flag):
    """Verify deny lists filter correctly without over-filtering."""
    result = deidentify_text(text)

    if should_flag:
        # Should detect PHI
        assert any(e.entity_type == entity_type for e in result.entities_found), \
            f"Expected {entity_type} detection in: {text}"
    else:
        # Should NOT detect (filtered by deny list)
        assert not any(e.entity_type == entity_type for e in result.entities_found), \
            f"False positive {entity_type} in: {text}"
```

**Benefits:**
- **Prevents regressions:** Adding "high" to deny list won't break "Highland Park" detection
- **Documents intent:** Each test case explains WHY something is/isn't PHI
- **Fast feedback:** Runs in <1s, integrated with existing pytest suite

**Effort:** ~10 test cases per deny list addition (5 negative, 5 positive)

### Complete Workflow (Practical for Single Developer)

```
1. Generate test scripts → Faker providers create edge cases
2. Run evaluation → Identify false positives
3. Corpus analysis → Extract candidate terms
4. Clinical validation → Manual review with checklist
5. Add to deny list → Update app/config.py
6. Write regression tests → pytest parameterization
7. Verify → Run full test suite
8. Iterate → Repeat for next batch
```

**Time per iteration:** ~2 hours (30 min corpus analysis, 1 hour validation, 30 min testing)

---

## Tools

### Use What You Already Have

| Tool | Purpose | Already Installed? | Verdict |
|------|---------|-------------------|---------|
| **pytest** | Regression testing, parameterization | YES | USE ✓ |
| **Faker** | Test data generation | YES | EXTEND ✓ |
| **collections.Counter** | Corpus frequency analysis | YES (stdlib) | USE ✓ |
| **scikit-learn metrics** | Precision/recall (from v1.0 research) | YES | USE ✓ |

### DO NOT ADD

| Tool | Why Not |
|------|---------|
| **Label Studio** | Annotation tool—only needed if fine-tuning spaCy (not in scope) |
| **NLTK stopwords** | Generic English stopwords; medical domain needs custom deny lists |
| **spaCy displaCy** | Visualization—nice for debugging but not systematic |
| **Jupyter notebooks** | Exploratory analysis—your pytest workflow is more reproducible |

**Rationale:** Over-tooling creates maintenance burden. Your pytest + Faker stack is sufficient.

---

## What NOT to Do

### 1. DON'T: Use Generic Stopword Lists

**Anti-pattern:** Import NLTK medical stopwords directly

**Why bad:**
- Generic lists include terms that ARE PHI in context ("Dr.", "Hospital")
- Missing domain-specific terms ("NC", "high flow")
- No clinical validation

**Instead:** Build deny lists incrementally from actual false positives in YOUR data

**Confidence:** 98% - Medical domain requires domain-specific deny lists

### 2. DON'T: Automate Deny List Additions Without Validation

**Anti-pattern:** Automatically add all terms with >5 false positives to deny list

**Why bad:**
- "Boston" might have 10 false positives but IS PHI
- Automated approach could create HIPAA compliance gaps
- No accountability for safety decisions

**Instead:** Require clinical validation for each deny list addition (manual checklist)

**Confidence:** 100% - HIPAA compliance demands human oversight

### 3. DON'T: Add Context-Aware Filtering to Deny Lists

**Anti-pattern:** Deny list with rules like "ignore 'High' if followed by 'flow'"

**Why bad:**
- Deny lists are simple substring matching (by design)
- Context-aware logic belongs in custom recognizers (already have `app/recognizers/`)
- Mixing concerns makes debugging harder

**Instead:**
- Simple terms → deny lists
- Context-dependent patterns → custom recognizers with lookbehind/lookahead

**Confidence:** 95% - Separation of concerns principle

### 4. DON'T: Generate Adversarial Examples with LLMs

**Anti-pattern:** Use GPT-4 to "find edge cases that break the system"

**Why bad:**
- LLM output is non-deterministic (can't reproduce failures)
- No ground truth labels (manual annotation required)
- Expensive and slow
- Your Faker + templates approach is deterministic and labeled

**Instead:** Use Faker providers to systematically generate edge cases (see above)

**Confidence:** 90% - Deterministic testing > stochastic testing for regression prevention

---

## Integration with Existing System

### Your Current Architecture (Don't Change)

```
Transcription (faster-whisper)
    ↓
Text with potential PHI
    ↓
Presidio Analyzer (spaCy NER + custom recognizers)
    ↓
Confidence scores + entity spans
    ↓
Deny list filtering (app/deidentification.py lines 205-210)
    ↓
[REDACTED] output
```

### Where New Components Fit

**Test generation:**
- **Location:** `tests/medical_providers.py` (add 2-3 providers)
- **Integration point:** `tests/handoff_templates.py` (add template set)
- **Output:** `tests/synthetic_handoffs.json` (regenerate with new templates)

**Deny list expansion:**
- **Analysis:** New file `tests/analyze_false_positives.py` (corpus analysis)
- **Configuration:** `app/config.py` (add terms to existing deny lists)
- **Validation:** New file `tests/test_deny_lists.py` (regression suite)

**No changes to:**
- Core Presidio integration
- Custom recognizers (unless pattern-based filtering needed)
- Transcription pipeline
- FastAPI endpoints

---

## Confidence Assessment

| Area | Confidence | Rationale |
|------|------------|-----------|
| **Faker provider approach** | 95% | Your existing system proves this works; simple extension |
| **pytest parameterization** | 98% | Standard practice, already using pytest |
| **Corpus analysis** | 90% | Straightforward Counter() logic on existing evaluation results |
| **Clinical validation checklist** | 100% | Required for HIPAA compliance, manual but necessary |
| **Deny list regression testing** | 95% | pytest makes this trivial, prevents regressions |
| **NOT using LLMs for generation** | 95% | Deterministic Faker > non-deterministic LLM for testing |
| **NOT auto-adding to deny lists** | 100% | HIPAA requires human validation |

**Overall confidence: HIGH (94%)**

---

## Sources

### I-PASS Handoff Structure
- [I-PASS Mnemonic to Standardize Verbal Handoffs - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9923540/)
- [Boston Children's I-PASS Implementation Guide](https://answers.childrenshospital.org/i-pass-handoffs/)
- [I-PASS Adherence and Implications - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6570451/)

### Medical NLP and Abbreviations
- [Deciphering clinical abbreviations with ML - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9718734/)
- [Deep database of medical abbreviations - Nature Scientific Data](https://www.nature.com/articles/s41597-021-00929-4)
- [Processing of Short-Form Content in Clinical Narratives - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11467596/)

### NER False Positive Reduction
- [Custom NER evaluation metrics - Azure AI](https://learn.microsoft.com/en-us/azure/ai-services/language-service/custom-named-entity-recognition/concepts/evaluation-metrics)
- [Named Entity Recognition Complete Guide 2026](https://www.articsledge.com/post/named-entity-recognition-ner)

### Testing Best Practices
- [pytest parametrize documentation](https://docs.pytest.org/en/stable/parametrize.html) (from v1.0 research)

---

## Next Steps for Roadmap Creation

Based on this research, the roadmap should include:

**Phase 1: Extend Test Coverage**
- Add ClinicalTimelineProvider to `tests/medical_providers.py`
- Add MedicalContextProvider to `tests/medical_providers.py`
- Create OVER_DETECTION_EDGE_CASES templates
- Regenerate `tests/synthetic_handoffs.json` with new providers
- **Effort:** 2-3 hours
- **Output:** 100+ new test cases covering duration/medical context

**Phase 2: Systematic Deny List Expansion**
- Implement `tests/analyze_false_positives.py` (corpus analysis)
- Run analysis on current test suite
- Create clinical validation checklist (markdown table)
- Validate top 20 candidates with medical judgment
- Add validated terms to `app/config.py` deny lists
- **Effort:** 3-4 hours (includes clinical validation)
- **Output:** 10-15 new deny list entries with rationale

**Phase 3: Regression Prevention**
- Create `tests/test_deny_lists.py` with parameterized tests
- Add 50+ test cases (positive and negative examples)
- Integrate with CI/CD (already passing, add new tests)
- **Effort:** 2 hours
- **Output:** Comprehensive regression suite preventing over-filtering

**Phase 4: Validation**
- Run full evaluation on 500+ synthetic handoffs
- Verify over-detection issues resolved
- Check precision/recall metrics (target: recall ≥90%, precision ≥70%)
- Update documentation with deny list rationale
- **Effort:** 1 hour
- **Output:** Validation report, updated metrics

**Total estimated effort:** 8-10 hours for complete over-detection quality pass

---

*Research date: 2026-01-28*

**Researcher Notes**: This milestone has a clear, narrow scope (fix over-detection via test coverage + deny lists). The existing infrastructure is excellent—just needs targeted extensions. The 3-step deny list methodology (corpus analysis → clinical validation → regression tests) balances automation with required human oversight for HIPAA compliance. Resist the urge to over-engineer with LLMs or complex tooling; your pytest + Faker stack is perfect for this.
