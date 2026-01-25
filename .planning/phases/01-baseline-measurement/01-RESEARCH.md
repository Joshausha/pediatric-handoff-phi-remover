# Research: Phase 1 - Baseline Measurement

**Phase**: 1 - Baseline Measurement
**Research Date**: 2026-01-23
**Purpose**: Answer "What do I need to know to PLAN this phase well?"

---

## Executive Summary

Phase 1 establishes the measurement infrastructure required for data-driven PHI detection improvement. The existing system has **evaluation tools already in place** (`tests/evaluate_presidio.py`, synthetic dataset generator, per-entity-type metrics) but lacks integration into the CI/CD workflow and a gold standard validation dataset. This phase focuses on **enhancing existing infrastructure** rather than building from scratch, with primary emphasis on creating a reproducible measurement baseline that blocks all subsequent optimization phases.

**Key Finding**: Infrastructure ~70% complete. Critical gaps are (1) gold standard dataset with human annotation, (2) F2 score calculation, and (3) CI integration for regression detection.

---

## Current State Analysis

### Existing Infrastructure ✅

The project already has substantial evaluation capabilities:

**1. Synthetic Dataset Generator** (`tests/generate_test_data.py`)
- 500 synthetic handoffs with ground truth PHI spans
- Faker-based with custom pediatric providers
- Template-driven with 8 PHI entity types
- JSON serialization for reproducibility
- **Status**: Production-ready, seed=42 for reproducibility

**2. Presidio Evaluator** (`tests/evaluate_presidio.py`)
- Overlap-based span matching (Jaccard similarity, threshold=0.5)
- Per-entity-type metrics (precision, recall, F1)
- False negative/positive classification
- CLI with verbose and JSON output modes
- **Status**: Production-ready, matches presidio-research methodology

**3. Test Suite** (`tests/test_deidentification.py`)
- 36 tests covering 8 entity types
- Parameterized synthetic tests with `@pytest.mark.bulk`
- Safety thresholds (recall ≥95%, precision ≥70%)
- **Status**: 13 tests failing, provides clear failure signals

**4. Current Baseline Metrics** (from `evaluate_presidio.py` output)
```
Overall: 77.9% recall, 66.3% precision, F1 71.7%
Per-entity breakdown:
  ❌ PEDIATRIC_AGE: 36.6% recall (weakest)
  ❌ ROOM: 34.4% recall (weakest)
  ❌ LOCATION: 19.4% recall (third weakest)
  ❌ MRN: 70.9% recall
  ❌ PHONE: 74.0% recall
  ❌ DATE_TIME: 96.8% recall
  ❌ PERSON: 98.8% recall
  ✅ EMAIL: 100.0% recall
```

### Critical Gaps 🚧

**1. No Gold Standard Human-Annotated Dataset** (MEAS-02)
- Synthetic data tests pattern matching, not real-world robustness
- No inter-rater reliability (kappa) measurement
- No validation against adversarial cases (speech artifacts, cultural diversity)
- **Risk**: 99% synthetic metrics, but real transcripts have PHI leaks

**2. F2 Score Not Calculated** (MEAS-03)
- Current evaluation uses F1 (equal precision/recall weighting)
- HIPAA compliance requires recall-weighted optimization
- F2 formula: `F2 = (1 + 2²) * (P * R) / (2² * P + R) = 5 * P * R / (4 * P + R)`
- **Gap**: Simple code change in `evaluate_presidio.py:EvaluationMetrics`

**3. No CI/CD Integration** (Deferred to v2, but document approach)
- Tests run manually, no automated regression detection
- Baseline metrics not tracked over time
- No threshold alerts on recall degradation
- **Note**: Not blocking Phase 1, but document strategy for future

**4. No Documentation of Baseline State** (MEAS-04)
- Need timestamped metrics snapshot before changes
- Must capture synthetic dataset composition (500 samples, template distribution)
- Document known limitations (synthetic-only, no real transcript validation)

---

## Technical Requirements for Phase 1

### 1. Enhance Evaluation Script (`evaluate_presidio.py`)

**Add F2 Score Calculation**
```python
# In EvaluationMetrics class
@property
def f2(self) -> float:
    """F2 score (recall-weighted): beta=2 emphasizes recall 2x precision"""
    beta = 2.0
    if self.precision + self.recall == 0:
        return 0.0
    return (1 + beta**2) * (self.precision * self.recall) / (beta**2 * self.precision + self.recall)
```

**Add Per-Entity F2 Scores**
- Current report shows per-entity precision/recall/F1
- Need to add F2 column for optimization target visibility

**Add Confusion Matrix Export**
- True positives, false negatives, false positives by entity type
- Export as JSON for downstream analysis (threshold calibration in Phase 2)

**Estimated effort**: 2-3 hours

### 2. Create Gold Standard Validation Dataset (MEAS-02)

**Two approaches** (recommend parallel execution):

**Option A: Manually Annotate Real Transcripts** (preferred for clinical relevance)
- Source: De-identified pediatric handoffs from clinical pilot
- Tool: Label Studio or brat for PHI span annotation
- Process:
  1. Obtain 50+ transcripts from hospital IT (de-identified by external system)
  2. Two independent annotators label PHI spans
  3. Calculate inter-rater reliability (Cohen's kappa, target >0.8)
  4. Resolve disagreements through adjudication
  5. Export as JSON matching `SyntheticHandoff` schema

**Challenges**:
- Requires IRB approval or QI project classification
- Time-intensive (10-15 min per transcript × 2 annotators × 50 = 16-25 hours)
- Privacy concerns even with de-identified transcripts

**Option B: Adversarial Synthetic Dataset** (faster, lower clinical validity)
- Extend `generate_test_data.py` with edge cases
- Add templates for:
  - Speech artifacts ("um", "uh", stutters, corrections)
  - Cultural name diversity (Hispanic, Asian, African names)
  - Transcription errors ("mom" → "um", numbers misheard)
  - Start/end-of-line edge cases (lookbehind failures)
  - Punctuation variations ("mom, Jessica" vs "mom Jessica")
- Generate 100-200 adversarial samples
- Manual review to confirm ground truth labels

**Recommended hybrid approach**:
1. Start with **Option B** (adversarial synthetic) for immediate progress (2-4 hours)
2. Pursue **Option A** (real transcripts) in parallel if hospital access available
3. Document both datasets in evaluation reports

**Estimated effort**:
- Option B: 4-6 hours (template creation + validation)
- Option A: 20-30 hours (annotation + IRB/QI process)

### 3. Document Baseline Performance (MEAS-04)

**Create baseline report** (`.planning/phases/01-baseline-measurement/BASELINE_METRICS.md`):

```markdown
# Baseline Metrics: PHI Detection System

**Date**: 2026-01-23
**Dataset**: synthetic_handoffs.json (500 samples, seed=42)
**Presidio Version**: 2.2.354
**spaCy Model**: en_core_web_lg 3.7.1
**Detection Threshold**: 0.35

## Overall Performance
- Recall: 77.9%
- Precision: 66.3%
- F1: 71.7%
- F2: [TO BE CALCULATED]

## Per-Entity Performance
[Table with recall/precision/F1/F2 for all 8 entity types]

## Known Limitations
1. Synthetic-only validation (no real transcript testing)
2. Template diversity: 50 unique templates, may not cover all edge cases
3. No speech artifact testing (stutters, corrections)
4. Cultural name diversity limited to Faker defaults
5. Threshold not calibrated (arbitrary 0.35 setting)

## Critical Gaps (77.9% → 95% recall)
1. PEDIATRIC_AGE: 36.6% recall → Need pattern improvements
2. ROOM: 34.4% recall → Need pattern improvements
3. LOCATION: 19.4% recall → Over-aggressive deny list
4. MRN: 70.9% recall → Pattern edge cases
5. PHONE: 74.0% recall → Non-standard formats

## Test Failures (13/36 failing)
- test_catches_mrn_with_label: MRN with label not detected
- test_minimal_phi_transcript: Over-redacting clinical terms
- test_bulk_person_detection: 2 missed persons
- test_bulk_phone_detection: 5 missed phones
- test_bulk_mrn_detection: 4 missed MRNs
- test_bulk_location_detection: 50% miss rate
- test_full_dataset_recall: 77.3% < 95% threshold
- test_precision_not_too_low: 66.9% < 70% threshold
```

**Estimated effort**: 2-3 hours (data collection + documentation)

### 4. Integration Strategy (Document Only - v2)

**Approach for future CI/CD integration**:

```yaml
# .github/workflows/phi-detection-metrics.yml
name: PHI Detection Metrics

on:
  pull_request:
    paths:
      - 'app/recognizers/**'
      - 'app/deidentification.py'
      - 'app/config.py'

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python -m spacy download en_core_web_lg
      - name: Run evaluation
        run: |
          python tests/evaluate_presidio.py --json > metrics.json
      - name: Check thresholds
        run: |
          python tests/check_thresholds.py metrics.json
          # Fail if recall < 95% or precision < 70%
      - name: Upload metrics
        uses: actions/upload-artifact@v3
        with:
          name: phi-metrics
          path: metrics.json
```

**Threshold check script** (`tests/check_thresholds.py`):
```python
#!/usr/bin/env python3
"""Check PHI detection metrics against thresholds."""
import json
import sys

def check_thresholds(metrics_file: str) -> bool:
    with open(metrics_file) as f:
        data = json.load(f)

    metrics = data['metrics']
    recall = metrics['recall']
    precision = metrics['precision']

    # Safety thresholds
    RECALL_MIN = 0.95  # HIPAA compliance
    PRECISION_MIN = 0.70  # Clinical utility

    passed = True
    if recall < RECALL_MIN:
        print(f"❌ RECALL FAILURE: {recall:.1%} < {RECALL_MIN:.0%}")
        passed = False
    if precision < PRECISION_MIN:
        print(f"❌ PRECISION FAILURE: {precision:.1%} < {PRECISION_MIN:.0%}")
        passed = False

    return passed

if __name__ == "__main__":
    if not check_thresholds(sys.argv[1]):
        sys.exit(1)
```

**Estimated effort**: 1-2 hours documentation (actual implementation deferred to v2)

---

## Dependencies & Blockers

### No External Dependencies ✅
- All evaluation infrastructure exists in codebase
- Synthetic dataset already generated (`tests/synthetic_handoffs.json`)
- Python dependencies already installed in venv

### Potential Blockers 🚧

**1. Hospital Access for Real Transcripts**
- **Impact**: Can't create gold standard dataset (MEAS-02)
- **Mitigation**: Use adversarial synthetic dataset as Phase 1 deliverable, document real transcript validation as Phase 5 requirement
- **Likelihood**: Medium (depends on hospital IT collaboration)

**2. Time for Manual Annotation**
- **Impact**: 20-30 hours for 50 transcripts × 2 annotators
- **Mitigation**: Start with adversarial synthetic (4-6 hours), defer real annotation to Phase 5
- **Likelihood**: Low (can work around with synthetic)

### No Technical Blockers
- Python 3.9+ ✓
- pytest, Faker, Presidio dependencies ✓
- spaCy en_core_web_lg model ✓
- Existing evaluation scripts functional ✓

---

## Success Criteria Validation

### MEAS-01: Per-Entity-Type Metrics ✅
**Status**: Already implemented in `evaluate_presidio.py`
- Precision, recall, F1 calculated for all 8 entity types
- Report shows per-type performance breakdown
- **Gap**: Need to add F2 score (simple code change)

**Plan deliverable**: Update `EvaluationMetrics` class with `f2` property

### MEAS-02: Gold Standard Dataset ⚠️
**Status**: Partially complete (synthetic only)
- 500 synthetic transcripts with ground truth labels
- No human-annotated real transcripts
- No inter-rater reliability measurement

**Plan deliverable**: Create adversarial synthetic dataset (100-200 samples) with edge cases, document real transcript annotation as Phase 5 requirement

### MEAS-03: F2 Score Optimization Target 🚧
**Status**: Not implemented
- Current system uses F1 (equal weighting)
- F2 emphasizes recall 2x precision (appropriate for PHI)
- Simple formula addition needed

**Plan deliverable**: Add F2 calculation to evaluation script, update report to show F2 as primary metric

### MEAS-04: Baseline Documentation 🚧
**Status**: Metrics exist but not documented
- Evaluation script outputs current performance
- No timestamped baseline snapshot
- No known limitations documentation

**Plan deliverable**: Create `BASELINE_METRICS.md` with comprehensive baseline state before any changes

---

## Recommended Approach

### Execution Order (Sequential)

**Plan 01-01: Enhance Evaluation Infrastructure** (2-3 hours)
- Add F2 score calculation to `evaluate_presidio.py`
- Add per-entity F2 scores to report
- Export confusion matrix as JSON
- Add command-line flag `--export-confusion-matrix`

**Plan 01-02: Document Baseline State** (2-3 hours)
- Run evaluation on current system
- Create `BASELINE_METRICS.md` with timestamped results
- Document synthetic dataset composition
- Capture test failure patterns (13/36 failing tests)
- List known limitations (synthetic-only, no speech artifacts)

**Plan 01-03: Create Adversarial Synthetic Dataset** (4-6 hours)
- Extend `tests/handoff_templates.py` with edge case templates
- Add speech artifacts (stutters, corrections, hesitations)
- Add cultural name diversity (Hispanic, Asian, African names)
- Add transcription error templates (misheard words, numbers)
- Add punctuation variations and start/end-of-line cases
- Generate 100-200 adversarial samples (seed=43 for separation)
- Validate ground truth labels manually
- Document adversarial dataset composition

**Plan 01-04: Document CI/CD Integration Strategy** (1-2 hours)
- Write GitHub Actions workflow pseudocode
- Create threshold check script skeleton
- Document regression detection approach
- Mark as v2 requirement (not blocking Phase 1)

**Total Phase 1 Effort**: 10-14 hours (adversarial synthetic path)
**Alternative with Real Transcripts**: 30-40 hours (includes annotation time)

### Parallel vs. Sequential Work

**Can be parallelized**:
- Plan 01-01 (code changes) + Plan 01-04 (documentation)
- Plan 01-02 (baseline docs) can overlap with 01-01 testing

**Must be sequential**:
- Plan 01-01 must complete before 01-02 (need F2 metrics in baseline)
- Plan 01-03 depends on 01-01 (use enhanced evaluation script)

---

## Alternative Approaches Considered

### Alternative 1: Use presidio-evaluator Package
**Description**: Microsoft's official evaluation toolkit (https://github.com/microsoft/presidio-research)

**Pros**:
- Official Microsoft support
- Token-based evaluation (more forgiving than span-based)
- Built-in dataset converters

**Cons**:
- Additional dependency (presidio-evaluator package)
- Our custom implementation already functional
- Token-based vs span-based evaluation mismatch (our ground truth is span-based)
- Would require rewriting dataset format

**Decision**: Keep existing implementation, consider presidio-evaluator for Phase 5 external validation

### Alternative 2: Start with Real Transcripts Only
**Description**: Skip adversarial synthetic, focus exclusively on hospital transcript annotation

**Pros**:
- Highest clinical validity
- Tests real-world edge cases
- Gold standard for publication

**Cons**:
- 20-30 hour annotation burden
- Requires hospital IT coordination (potential blocker)
- Delays Phase 2 start (blocks entire roadmap)

**Decision**: Start with adversarial synthetic for immediate progress, pursue real transcripts in parallel

### Alternative 3: Fine-Tune spaCy NER Model
**Description**: Train custom spaCy NER model on annotated transcripts

**Pros**:
- Could improve PERSON/LOCATION detection
- Domain-specific medical NER

**Cons**:
- Premature optimization (threshold/pattern fixes not yet attempted)
- Requires large training dataset (hundreds of annotated transcripts)
- Training time and computational cost
- Maintenance burden (model updates, versioning)

**Decision**: Defer to Phase 5 (NER tuning) only if Phases 2-4 insufficient. Research shows configuration issues, not model issues.

---

## Risk Assessment

### Low Risk ✅
- **Enhancing evaluation script**: Simple code changes, existing tests validate correctness
- **Documenting baseline**: Read-only operation, no system changes
- **CI/CD documentation**: Planning only, no implementation

### Medium Risk ⚠️
- **Adversarial synthetic dataset**: New templates could introduce bugs in ground truth labels
  - **Mitigation**: Manual review of generated samples, separate seed (43) from main dataset (42)
- **F2 score calculation**: Formula complexity could introduce bugs
  - **Mitigation**: Unit tests for F2 calculation, compare against sklearn.metrics.fbeta_score

### High Risk 🚨
- **Real transcript annotation**: HIPAA privacy concerns, IRB requirements
  - **Mitigation**: Defer to Phase 5, use adversarial synthetic for Phase 1

### No Integration Risk
- Phase 1 is measurement-only (no changes to deidentification logic)
- All code changes isolated to test infrastructure
- No risk of introducing new PHI leaks

---

## Open Questions for Planning

1. **Gold standard dataset priority**: Should we block Phase 2 waiting for real transcripts, or proceed with adversarial synthetic?
   - **Recommendation**: Proceed with adversarial synthetic, document real transcript validation as Phase 5 requirement

2. **F2 vs F1 as primary metric**: Should we completely replace F1 with F2, or report both?
   - **Recommendation**: Report both (F1 for comparison, F2 for optimization), document F2 as primary

3. **CI/CD integration timing**: Should we implement CI checks in Phase 1, or defer to v2?
   - **Recommendation**: Document strategy in Phase 1, implement in v2 (not blocking optimization work)

4. **Adversarial dataset size**: 100 samples? 200? 500?
   - **Recommendation**: Start with 100 samples (2-3 hours generation + review), expand to 200 if time permits

5. **Baseline documentation granularity**: Should we include confusion matrices, or just summary metrics?
   - **Recommendation**: Include summary metrics + per-entity breakdown in markdown, export full confusion matrix as JSON for Phase 2 analysis

---

## Key Takeaways for Planning

### What Makes This Phase Successful
1. **Reproducible baseline**: Timestamped metrics snapshot before any changes
2. **F2 score as optimization target**: Recall-weighted metric appropriate for PHI
3. **Enhanced evaluation tools**: Per-entity F2, confusion matrix export
4. **Adversarial synthetic dataset**: Edge case coverage beyond template-driven generation
5. **Clear documentation**: Known limitations, test failures, critical gaps

### What Blocks Phase 2
- **Missing baseline documentation**: Can't measure improvement without baseline
- **No F2 calculation**: Can't optimize for recall-weighted metric
- **No confusion matrix**: Can't perform threshold calibration in Phase 2

### What Can Be Deferred
- **Real transcript annotation**: Move to Phase 5 (validation)
- **CI/CD implementation**: Document strategy, implement in v2
- **presidio-evaluator integration**: Consider for Phase 5 external validation

### Quick Wins (High Value, Low Effort)
1. **F2 score calculation**: 1 hour, unblocks Phase 2 optimization
2. **Baseline documentation**: 2 hours, provides clear success criteria
3. **Adversarial synthetic dataset**: 4-6 hours, improves test coverage significantly

### Effort-to-Value Ratio
- **Highest value**: Adversarial synthetic dataset (catches edge cases, 4-6 hours)
- **Lowest effort**: F2 score calculation (simple formula, 1 hour)
- **Best ROI**: Baseline documentation (2 hours, unblocks entire roadmap)

---

**Research Complete**: Ready for phase planning.
**Next Step**: Create `01-PLAN.md` with detailed implementation steps.
