# Research Summary: PHI Detection Quality Improvement

**Project**: Pediatric Handoff PHI Remover - Quality Overhaul
**Research Date**: 2026-01-23
**Baseline Performance**: 77.9% recall, 87.4% precision, F1 0.82
**Target**: >95% recall for clinical deployment

---

## Current State

The existing Presidio-based system achieves **77.9% recall** and **87.4% precision** (F1: 0.82) on 500 synthetic I-PASS handoff transcripts. This aligns with published benchmarks for out-of-the-box Presidio on clinical text (Kotevski et al.: 80.6% recall), but falls **17 percentage points short** of the >95% recall required for safe clinical deployment.

**Critical gaps identified**:
- **PEDIATRIC_AGE**: 36.6% recall (weakest entity type)
- **ROOM**: 34.4% recall (weakest entity type)
- **MRN**: 70.9% recall (F1: 0.74)
- **PHONE**: 74.0% recall (F1: 0.78)

**Root causes** (from architecture and pitfalls research):
1. Detection threshold too low (0.35) → excessive false positives
2. Regex lookbehind patterns miss edge cases ("Baby LastName" at start of line)
3. Case sensitivity inconsistencies between entity types
4. Deny lists applied post-detection (wastes computation)
5. No systematic threshold calibration methodology

---

## Key Findings

### Stack: Evaluation Tools for Systematic Improvement

**Top Recommendation**: Use **presidio-research** toolkit as primary evaluation framework.

| Tool | Purpose | Priority | Confidence |
|------|---------|----------|------------|
| **presidio-research** | Official Presidio evaluation with token-based precision/recall/F1 | HIGH | 95% |
| **scikit-learn metrics** | Threshold calibration via precision-recall curves | HIGH | 98% |
| **pytest parameterized tests** | Regex pattern validation and regression testing | HIGH | 98% |
| **nervaluate** | Entity-level evaluation for debugging partial matches | MEDIUM | 80% |
| **Manual P-R curve analysis** | Visual threshold selection with domain expertise | MEDIUM | 95% |

**Critical insight from STACK.md**: The issue is **configuration** (thresholds, deny lists) and **pattern quality** (regex edge cases), NOT fundamental stack replacement. Presidio's architecture is sound—improvements should focus on tuning recognizers, not swapping out core components.

**Installation requirements**:
```bash
pip install presidio-evaluator  # Microsoft's official evaluation toolkit
# scikit-learn already in project
# pytest already in project
```

**Anti-patterns to avoid**:
- ❌ LLM-based de-identification (sends PHI to cloud, violates HIPAA)
- ❌ spaCy model fine-tuning (premature optimization—fix configs first)
- ❌ Complex calibration libraries (overkill for 500 samples)

---

### Features: Quality Metrics and Success Criteria

**Table Stakes** (HIPAA compliance):
- All 18 HIPAA Safe Harbor identifiers covered ✓
- Age 89+ redaction ✓
- Pediatric-specific PHI (guardian names, baby names, pediatric ages) ⚠ (partial)

**Differentiators** (clinical quality):
- **High recall (>95% F1)**: State-of-the-art systems achieve 96%+ (John Snow Labs, i2b2 2014 winner). **Gap: 17 points.**
- **Context-aware precision**: Deny lists + lookbehind patterns preserve clinical utility ("PICU bed [ROOM]" not "[LOCATION] [ROOM]")
- **Performance <100ms per request**: Presidio guideline for 100 tokens. **Status: Unknown (need benchmarking).**

**Primary Metrics** (must prioritize recall over precision for HIPAA):
- **Recall (sensitivity)**: TP / (TP + FN) → **Target: ≥98%** (current: 77.9%)
- **Precision (PPV)**: TP / (TP + FP) → **Target: ≥90%** (current: 87.4%)
- **F2 Score**: Weighs recall 2x precision → **Optimization target for PHI**
- **Token-level F1**: More forgiving than entity-level (accepts partial matches)

**Anti-features to avoid**:
- ❌ Accuracy as sole metric (misleading for rare PHI)
- ❌ Aggressive redaction without context (destroys clinical utility)
- ❌ One-size-fits-all approach (ignores pediatric vs. geriatric differences)
- ❌ No transparency (can't debug black box systems)
- ❌ Ignoring quasi-identifiers (rare diseases increase re-identification risk)

**Key insight from FEATURES.md**: In de-identification, **privacy relies exclusively on recall**—missing even 5% of PHI exposes patients to re-identification risk. Precision matters for clinical utility, but recall is non-negotiable for HIPAA compliance.

---

### Architecture: Layered Pipeline with Reverse Improvement Order

**Current pipeline flow** (5 stages):
```
Audio → faster-whisper → Presidio Analyzer (spaCy NER + Regex)
  → Deny List Filter → Presidio Anonymizer → Validation
```

**Status by stage**:
- ✅ Stage 1 (Audio transcription): Working well, no changes needed
- ⚠ Stage 2 (PHI detection): Threshold too low, lookbehind edge cases
- ⚠ Stage 3 (Deny list filtering): Case inconsistencies, post-detection (inefficient)
- ✅ Stage 4 (Anonymization): Working well
- ⚠ Stage 5 (Validation): Arbitrary thresholds (0.7 detection, 0.8 leak), no test integration

**Critical architectural insight**: Apply improvements **in reverse order** (validation → filtering → detection) to catch issues early without rebuilding entire pipeline.

**Threshold architecture recommendations**:

| Threshold | Current | Recommended | Rationale |
|-----------|---------|-------------|-----------|
| Detection (analyzer entry) | 0.35 | 0.5-0.6 | Based on P-R curve, prioritize recall |
| Entity-specific (recognizers) | 0.5-0.85 | Keep as-is | Reasonable range, document reasoning |
| Validation (re-analysis) | 0.7 | **Same as detection** | Validation must be ≥ strict as initial |
| Leak warning | 0.8 | Remove or align | Inconsistent with detection threshold |

**Deny list design best practices**:
- Normalize all deny lists to **lowercase** (currently LOCATION is case-sensitive, PERSON is case-insensitive)
- Move deny list filtering **into recognizer context** (currently post-detection filter wastes computation)
- Add deny lists for GUARDIAN_NAME, PEDIATRIC_AGE (currently only LOCATION, PERSON)

**Hybrid regex+NER patterns**:
- Use **regex for structured PHI** (MRN, phone, email)—fast, deterministic
- Use **NER for unstructured PHI** (names, locations)—context-aware
- **Avoid over-reliance on lookbehind/lookahead**—they miss edge cases (start/end of line, punctuation variations)

**Build order** (sequential dependencies):
1. **Phase 1: Validation & Testing** (foundation) → **Blocks all others**
2. **Phase 2: Threshold Optimization** (configuration) → **Blocks Phases 3-4**
3. **Phases 3-4: Deny Lists + Regex** (can work in parallel after Phase 2)
4. **Phase 5: NER Tuning** (optional, advanced—only if Phases 1-4 insufficient)

**Integration risk levels**:
- Low risk: Phases 1-3 (testing, thresholds, deny lists)
- Medium risk: Phase 4 (regex patterns—could introduce new false positives)
- High risk: Phase 5 (NER model swap—architectural change)

---

### Pitfalls: Critical Failure Modes to Avoid

**Most critical pitfalls** (prioritized by impact):

#### 1. **Ignoring Precision-Recall Tradeoffs** (CRITICAL)
- **Risk**: Improving precision (reduce over-scrubbing) degrades recall (increases missed PHI)
- **Healthcare context**: Recall takes precedence—missed PHI has legal consequences
- **Prevention**: Define risk tolerance ("99% recall minimum"), use F2 score (weighs recall 2x), monitor BOTH metrics
- **Phase impact**: Phase 4 (Threshold Optimization)—must define constraints BEFORE calibration

#### 2. **Case Sensitivity Inconsistencies** (CRITICAL - Easiest to fix)
- **Risk**: "Mom Jessica" caught but "mom jessica" missed
- **Current state**: PERSON deny list case-insensitive, LOCATION exact match
- **Prevention**: Standardize ALL deny lists to `.lower()` normalization
- **Phase impact**: Phase 1 (Case Normalization)—foundation before regex refinement

#### 3. **Testing Only on Synthetic Data** (CRITICAL)
- **Risk**: 99% metrics on test suite but users report missed PHI in production
- **Current gap**: 500 synthetic cases, no real transcript validation
- **Prevention**: Create adversarial test cases, obtain de-identified real transcripts, external validation
- **Phase impact**: Phase 3 (Validation)—create gold standard before declaring success

#### 4. **Context-Agnostic Pattern Matching** (HIGH)
- **Risk**: "Contact mom" flagged as person name, "NC 2L" flagged as location
- **Prevention**: Positive lookbehind (`(?<=Mom )[A-Z][a-z]+`), deny lists, minimal pairs testing
- **Phase impact**: Phase 2 (Regex Refinement)

#### 5. **Arbitrary Dual-Threshold Systems** (HIGH)
- **Risk**: Detection 0.35, validation 0.7, no documented calibration methodology
- **Prevention**: Generate P-R curve, document threshold selection, use F2 for optimization
- **Phase impact**: Phase 4 (Threshold Optimization)

#### 6. **Lexical Ambiguity - Over-Scrubbing Medical Terms** (HIGH)
- **Risk**: "NC" (nasal cannula) flagged as North Carolina, platelet counts flagged as MRNs
- **Prevention**: Medical term deny lists from SNOMED CT, lookbehind to preserve context
- **Phase impact**: Phase 2 (Regex Refinement)

#### 7. **Error Proximity Analysis Neglect** (MEDIUM)
- **Finding**: 78% of false negatives are adjacent to correct detections (NCBI study)
- **Risk**: Multi-word entities partially detected ("Jessica" caught, "Smith" missed)
- **Prevention**: Analyze false negative proximity, test multi-token entities, consider span expansion logic
- **Phase impact**: Phase 3 (Validation)

**Other significant pitfalls**:
- Overfitting to test data format (lookbehind assumes word order stable in speech-to-text)
- Single-point threshold optimization (ignores per-entity-type variance)
- No ground truth for real transcripts (can't measure recall without knowing actual PHI)
- Insufficient edge case coverage (nicknames, transcription errors, cultural diversity)
- Ignoring computational performance (complex regex can cause timeouts)
- No residual risk measurement (can't claim HIPAA compliance without statistical evidence)

**Prevention checklist** (from PITFALLS.md):
- Phase 0 (Planning): Define metrics (P/R/F2), risk tolerance, de-identification strategy
- Phase 1 (Case Normalization): Standardize case handling, document policy
- Phase 2 (Regex Refinement): Medical deny lists, context-aware patterns, performance benchmarking
- Phase 3 (Validation): Gold standard dataset (inter-rater reliability), edge case taxonomy, external validation
- Phase 4 (Threshold Optimization): P-R curve, documented selection, per-entity metrics, F2 optimization
- Phase 5 (Compliance): Residual risk with 95% CI, external review, HIPAA documentation

---

## Recommended Approach

### Phase Structure (Sequential Dependencies)

Based on architecture research, improvements must follow this order:

```
Phase 1: Establish Baseline Measurement
  ├─ Install presidio-research toolkit
  ├─ Create annotated gold standard (50-100 transcripts, kappa > 0.8)
  ├─ Build threshold sweep testing (0.3-0.7 range)
  └─ Generate per-entity-type precision/recall metrics

Phase 2: Case Normalization & Threshold Calibration
  ├─ Standardize all deny lists to lowercase
  ├─ Generate precision-recall curves per entity type
  ├─ Select thresholds that achieve ≥95% recall with best precision
  ├─ Update config.py with data-driven values + documentation
  └─ Define F2 score as optimization target (prioritizes recall)

Phase 3: Deny List Refinement
  ├─ Build medical term deny lists from SNOMED CT / clinical vocabulary
  ├─ Add deny lists for GUARDIAN_NAME, PEDIATRIC_AGE
  ├─ Move deny list filtering into recognizer context (performance)
  └─ Track false positives systematically for continuous improvement

Phase 4: Regex Pattern Improvements
  ├─ Fix lookbehind edge cases (start of line, punctuation)
  ├─ Add bidirectional patterns ("Mom Jessica" AND "Jessica is mom")
  ├─ Enhance context word lists for confidence boosting
  ├─ Create pytest parameterized test suite for all patterns
  └─ Benchmark performance (catastrophic backtracking check)

Phase 5: External Validation & Compliance
  ├─ Test on real de-identified transcripts (not just synthetic)
  ├─ Adversarial testing with unusual patterns
  ├─ Error proximity analysis (identify boundary detection issues)
  ├─ Calculate residual risk with 95% confidence interval
  └─ External expert review (human-in-the-loop sample)

Phase 6 (Optional): Advanced NER Tuning
  ├─ Benchmark transformer-based models vs. spaCy
  ├─ Evaluate domain-specific medical NER models
  ├─ Cost-benefit analysis (accuracy vs. speed vs. complexity)
  └─ Only pursue if Phases 1-5 insufficient to reach 95% recall
```

### Why This Order

**Sequential dependencies**:
- Phase 1 establishes measurement framework → **blocks all improvements**
- Phase 2 calibrates thresholds → **blocks pattern tuning** (can't optimize patterns without knowing thresholds)
- Phases 3-4 can run in parallel after Phase 2

**Reverse pipeline improvement** (catch issues early):
- Fix validation thresholds (Phase 2) before tuning detection patterns (Phase 4)
- Improve filtering (Phase 3) before adding complex regex (Phase 4)
- Measure baseline (Phase 1) before any changes

**Risk management**:
- Low-risk changes first (testing, thresholds, deny lists)
- Medium-risk changes later (regex patterns)
- High-risk changes only if needed (NER model swap)

### Quick Wins (Low-Effort, High-Impact)

From research analysis, these should be prioritized in Phase 2:

1. **Standardize case handling** (1-2 hours)
   - Normalize all deny lists to lowercase
   - Fix LOCATION deny list to use case-insensitive matching
   - **Expected impact**: Catch edge cases currently missed due to capitalization

2. **Align validation threshold with detection** (30 minutes)
   - Change validation threshold from 0.7 → 0.5 (same as detection)
   - **Expected impact**: Catch PHI leaks that current validation misses

3. **Add medical abbreviation deny lists** (2-4 hours)
   - Build LOCATION deny list from common abbreviations (NC, RA, OR, ER, IV, PO, IM, SQ, PR, GT, NG, OG, NJ)
   - **Expected impact**: Reduce false positives for medical terms

4. **Run threshold sweep with presidio-research** (4-6 hours)
   - Test 0.3, 0.4, 0.5, 0.6, 0.7 thresholds on all 500 synthetic transcripts
   - Generate P-R curves per entity type
   - **Expected impact**: Data-driven threshold selection (could improve recall 5-10 points)

---

## Success Criteria

### Quantitative Targets

| Metric | Current | Target | Rationale |
|--------|---------|--------|-----------|
| **Overall Recall** | 77.9% | **≥95%** | Clinical deployment safety threshold |
| **Overall Precision** | 87.4% | **≥90%** | Maintain clinical utility |
| **F2 Score** | — | **≥0.93** | Weighted recall priority (β=2) |
| **PEDIATRIC_AGE Recall** | 36.6% | **≥90%** | Critical pediatric PHI gap |
| **ROOM Recall** | 34.4% | **≥90%** | Critical pediatric PHI gap |
| **MRN Recall** | 70.9% | **≥95%** | High-risk identifier |
| **PHONE Recall** | 74.0% | **≥95%** | High-risk identifier |

**Benchmark comparison**:
- Healthcare-tuned models: 96%+ F1 (John Snow Labs, i2b2 2014 winner)
- Out-of-box Presidio on clinical text: 80.6% recall (Kotevski et al.)
- **Our target**: Match healthcare-tuned performance (96% F1) through systematic tuning

### Qualitative Criteria

1. **Threshold calibration methodology documented** in config.py with supporting metrics
2. **All deny lists use consistent case handling** (standardized to lowercase)
3. **External validation** on real de-identified transcripts (not just synthetic)
4. **Residual risk calculated** with 95% confidence interval for HIPAA compliance
5. **Per-entity-type metrics** tracked for targeted improvement
6. **Regression test suite** covers edge cases (nicknames, transcription errors, cultural diversity)
7. **Performance benchmarking** confirms <100ms per 100 tokens per recognizer

### Phase Completion Criteria

**Phase 1 complete when**:
- presidio-research installed and integrated
- Gold standard dataset created (50-100 transcripts, inter-rater kappa > 0.8)
- Threshold sweep testing implemented (0.3-0.7 range)
- Per-entity precision/recall baseline established

**Phase 2 complete when**:
- All deny lists standardized to lowercase
- Precision-recall curves generated for all entity types
- Thresholds selected with documented rationale and metrics
- config.py updated with data-driven values

**Phase 3 complete when**:
- Medical term deny lists built from clinical vocabulary
- Deny lists added for all custom entity types
- Deny list filtering moved to recognizer context
- False positive tracking system operational

**Phase 4 complete when**:
- Lookbehind edge cases resolved
- Bidirectional patterns implemented
- pytest parameterized test suite covers all patterns
- Performance benchmarking confirms no regressions

**Phase 5 complete when**:
- External validation on real transcripts completed
- Error proximity analysis performed
- Residual risk calculated with 95% CI
- External expert review completed
- **Overall recall ≥95%** on validation set

---

## Confidence Assessment

| Research Area | Confidence | Notes |
|---------------|------------|-------|
| **Stack** | HIGH (95%) | presidio-research is official Microsoft tool, directly applicable. scikit-learn and pytest are industry standards. |
| **Features** | HIGH (90%) | HIPAA requirements well-documented. Benchmarks from peer-reviewed studies (Kotevski, i2b2 2014). |
| **Architecture** | HIGH (90%) | Presidio architecture well-documented. Improvement order based on engineering principles. |
| **Pitfalls** | MEDIUM-HIGH (85%) | Research-backed patterns (error proximity, precision-recall tradeoffs) but some project-specific risks unknown. |

**Overall confidence**: HIGH (90%)—Research is comprehensive, recommendations are evidence-based, and approach is aligned with published best practices.

**Key assumptions**:
1. Synthetic test data reasonably represents real handoff patterns (requires Phase 5 external validation to confirm)
2. Current 500 test cases provide sufficient statistical power for threshold calibration
3. Presidio's architecture supports proposed improvements without major refactoring
4. Target 95% recall is achievable through configuration tuning without NER model replacement

**Gaps requiring validation**:
1. **Real transcript performance**: Unknown if synthetic data overfits to assumptions
2. **Processing speed**: No current benchmarking of ms/token performance
3. **Inter-annotator reliability**: Need to measure human agreement on PHI in handoffs
4. **Quasi-identifier analysis**: Haven't assessed rare disease re-identification risk beyond direct identifiers

**Risks**:
1. **Configuration tuning may be insufficient**: If recall plateaus below 95% after Phase 4, will require Phase 6 (NER model tuning or replacement)
2. **Performance degradation**: Complex regex patterns could slow processing beyond 100ms budget
3. **Clinical vocabulary coverage**: Medical abbreviation deny lists may need continuous expansion as new terms emerge

---

## Sources

### Stack Research
- [Microsoft presidio-research GitHub](https://github.com/microsoft/presidio-research)
- [Presidio Evaluation Documentation](https://microsoft.github.io/presidio/evaluation/)
- [scikit-learn Precision-Recall Curves](https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html)
- [nervaluate: Entity-Level NER Evaluation](https://github.com/MantisAI/nervaluate)

### Features Research
- [HHS HIPAA De-identification Guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html)
- [i2b2 2014 De-identification Challenge](https://pmc.ncbi.nlm.nih.gov/articles/PMC4989908/)
- [John Snow Labs Clinical De-identification](https://www.johnsnowlabs.com/deidentification/)
- [Deep Learning Framework for PHI De-identification](https://www.mdpi.com/1999-5903/17/1/47)

### Architecture Research
- [Presidio Analyzer Documentation](https://microsoft.github.io/presidio/analyzer/)
- [Presidio Best Practices](https://microsoft.github.io/presidio/analyzer/developing_recognizers/)
- [Databricks: Automating PHI Removal with NLP](https://www.databricks.com/blog/2022/06/22/automating-phi-removal-from-healthcare-data-with-natural-language-processing.html)
- [IntuitionLabs: Open Source PHI De-Identification Review](https://intuitionlabs.ai/articles/open-source-phi-de-identification-tools)

### Pitfalls Research
- [De-identification of clinical notes with pseudo-labeling - BMC](https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/s12911-025-02913-z)
- [Software Tool for Removing Patient Identifying Information - PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2528047/)
- [Precision/Recall Tradeoff - Medium](https://medium.com/analytics-vidhya/precision-recall-tradeoff-79e892d43134)
- [NIST De-identification Guidelines](https://nvlpubs.nist.gov/nistpubs/ir/2015/nist.ir.8053.pdf)

### Benchmarks
- **Kotevski DP, Smee RI, Field M, et al.** Evaluation of an automated Presidio anonymisation model for unstructured radiation oncology electronic medical records in an Australian setting. *Int J Med Inform*. 2022;168:104880. (80.6% recall baseline)

---

## Ready for Roadmap Creation

This research summary provides:
- ✅ Clear baseline metrics and gaps
- ✅ Prioritized phase structure with dependencies
- ✅ Specific tools and techniques for each phase
- ✅ Success criteria (quantitative and qualitative)
- ✅ Risk assessment and confidence levels
- ✅ Evidence-based recommendations from peer-reviewed literature

**Next step**: The gsd-roadmapper agent can use this summary to create detailed implementation tasks with acceptance criteria, time estimates, and dependency ordering.

**Critical insights for roadmapper**:
1. **Phase 1 (Baseline Measurement) blocks all other work**—must complete first
2. **Quick wins exist in Phase 2**—case normalization and threshold alignment are low-effort, high-impact
3. **Weakest entities need targeted attention**—PEDIATRIC_AGE (36.6%), ROOM (34.4%) require custom recognizer improvements
4. **Recall must be prioritized over precision**—F2 score (not F1) is the optimization target for HIPAA compliance
5. **External validation is mandatory**—synthetic data alone creates false confidence

---

*Research synthesized: 2026-01-23 02:01:01 EST*
