# Stack Research: PHI Detection Quality Improvement

## Executive Summary

This research focuses on **evaluation and improvement tools** for an existing Presidio-based PHI detection system. The project already has core stack (Presidio 2.2.354, spaCy en_core_web_lg, faster-whisper, FastAPI) and 500+ synthetic test cases. The goal is to add tools for systematic evaluation, threshold calibration, and quality improvement—NOT to replace the core stack.

**Key Finding**: Microsoft's own `presidio-research` toolkit provides the most aligned solution for Presidio evaluation, with additional support from standard ML libraries for threshold calibration and regex testing.

---

## Evaluation Tools

### 1. **presidio-research** (RECOMMENDED - High Confidence)
- **Version**: Latest from GitHub (actively maintained as of 2025)
- **Source**: [microsoft/presidio-research](https://github.com/microsoft/presidio-research)
- **Purpose**: Official Microsoft toolkit designed specifically for Presidio evaluation
- **Key Features**:
  - Token-based precision/recall/F1 evaluation for PII detection
  - Synthetic data generator for creating test datasets
  - Built-in evaluation notebooks showing 30% F-score boost techniques
  - Span-level evaluation with configurable overlap thresholds
  - Direct integration with Presidio Analyzer API
- **Requirements**: Python 3.9+ (matches project requirement)
- **Rationale**:
  - Purpose-built for Presidio evaluation workflows
  - Understands Presidio's entity structure and scoring semantics
  - Proven to identify configuration improvements (notebooks show optimization paths)
  - Your project already has `PresidioEvaluator` in `tests/evaluate_presidio.py` - this library formalizes that approach
- **Installation**: `pip install presidio-evaluator`
- **Confidence Level**: 95% - Official tool, actively maintained, directly applicable

**References**:
- [Microsoft Presidio Evaluation Documentation](https://microsoft.github.io/presidio/evaluation/)
- [Presidio Research GitHub Repository](https://github.com/microsoft/presidio-research)
- [Evaluation Notebook](https://github.com/microsoft/presidio-research/blob/master/notebooks/4_Evaluate_Presidio_Analyzer.ipynb)

### 2. **nervaluate** (RECOMMENDED - Medium-High Confidence)
- **Version**: 0.1.8+ (available on PyPI, actively used 2024-2025)
- **Source**: [MantisAI/nervaluate](https://github.com/MantisAI/nervaluate)
- **Purpose**: Entity-level NER evaluation beyond simple token tagging
- **Key Features**:
  - Multiple evaluation modes: strict, exact, partial, type-matching
  - Precision, recall, F1 at entity level (not just token level)
  - Handles partial entity matches (critical for PHI where "John Smith" might be detected as just "John")
  - Based on SemEval 2013 evaluation standards
- **Rationale**:
  - Complements presidio-research with more nuanced entity matching
  - Better for debugging edge cases where entity boundaries are unclear
  - Industry-standard evaluation methodology
- **Use Case**: Secondary validation after presidio-research, especially for debugging partial entity detection
- **Installation**: `pip install nervaluate`
- **Confidence Level**: 80% - Well-established library, but presidio-research is more directly applicable

**References**:
- [nervaluate PyPI Package](https://pypi.org/project/nervaluate/)
- [nervaluate GitHub Repository](https://github.com/MantisAI/nervaluate)
- [nervaluate Benchmarking Guide](https://rumn.medium.com/nervaluate-the-ultimate-way-for-benchmarking-ner-models-b29e83fbae95)

### 3. **scikit-learn metrics** (RECOMMENDED - High Confidence)
- **Version**: 1.8.0+ (latest stable as of 2025)
- **Purpose**: Standard ML evaluation metrics for binary classification per entity type
- **Key Features**:
  - `precision_recall_curve()` for threshold tuning
  - `classification_report()` for per-entity-type breakdowns
  - `confusion_matrix()` for understanding error patterns
  - `f1_score()`, `fbeta_score()` with configurable β for recall-weighted metrics
- **Rationale**:
  - Already a common Python dependency
  - Essential for threshold calibration (see next section)
  - β=2 F-score recommended for PHI (prioritizes recall over precision)
- **Installation**: Already in most Python environments
- **Confidence Level**: 98% - Industry standard, directly applicable

**References**:
- [scikit-learn Precision-Recall Documentation](https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html)
- [Classification Threshold Tuning](https://scikit-learn.org/stable/modules/classification_threshold.html)

---

## Threshold Calibration

### 1. **TunedThresholdClassifierCV** from scikit-learn (RECOMMENDED - High Confidence)
- **Version**: scikit-learn 1.8.0+
- **Purpose**: Systematic threshold optimization for binary classifiers
- **Key Features**:
  - Cross-validated threshold tuning
  - Multiple optimization strategies (maximize F1, F2, precision at fixed recall, etc.)
  - Grid search over threshold values
  - Integrated with scikit-learn pipelines
- **Rationale**:
  - Presidio entity recognizers output confidence scores that can be thresholded
  - Your `app/config.py` has hardcoded thresholds (e.g., `PHI_CONFIDENCE_THRESHOLD`)
  - This tool systematically finds optimal thresholds per entity type
  - For PHI: optimize for F2 (β=2) to prioritize recall
- **Use Case**:
  1. Extract Presidio confidence scores from recognition results
  2. Use TunedThresholdClassifierCV to find optimal thresholds per entity type
  3. Update `app/config.py` with calibrated thresholds
- **Confidence Level**: 90% - Standard tool, requires adapting Presidio outputs

**References**:
- [Tuning Classification Thresholds](https://scikit-learn.org/stable/modules/classification_threshold.html)
- [Optimal Threshold for Imbalanced Classification](https://towardsdatascience.com/optimal-threshold-for-imbalanced-classification-5884e870c293/)
- [Evidently AI: Classification Threshold Balancing](https://www.evidentlyai.com/classification-metrics/classification-threshold)

### 2. **Manual Precision-Recall Curve Analysis** (RECOMMENDED - High Confidence)
- **Purpose**: Visual and analytical threshold selection
- **Method**:
  1. Use `sklearn.metrics.precision_recall_curve()` on your 500 synthetic transcripts
  2. Plot precision vs. recall at different thresholds
  3. Select threshold that achieves target recall (e.g., ≥95%) with best precision
  4. Per-entity-type calibration (different thresholds for PERSON vs. MEDICAL_RECORD_NUMBER)
- **Rationale**:
  - More transparent than automated tuning
  - Allows domain expertise input (e.g., "we MUST catch 100% of MRNs")
  - Better for medical safety requirements
- **Implementation**: 50-100 lines of Python with matplotlib
- **Confidence Level**: 95% - Standard practice, full control

**References**:
- [Google ML Crash Course: Classification Metrics](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall)
- [Optimal F1 Threshold Research](https://pmc.ncbi.nlm.nih.gov/articles/PMC4442797/)

### 3. **Presidio Score Recalibration** (PROJECT-SPECIFIC)
- **Purpose**: Adjust Presidio's internal scoring logic
- **Method**:
  - Presidio recognizers have `confidence` parameters
  - Custom recognizers (your `app/recognizers/pediatric.py`) can implement custom scoring
  - Use evaluation results to adjust pattern weights
- **Example**:
  ```python
  # In custom recognizer
  class GuardianNameRecognizer:
      def analyze(self, text, entities):
          # Boost confidence for high-risk patterns
          if "Mom" in match.context:
              match.score *= 1.2  # Increase confidence
          return match
  ```
- **Rationale**: Project-specific tuning based on pediatric handoff patterns
- **Confidence Level**: 70% - Requires experimentation, no standard library

---

## Regex Testing & Validation

### 1. **pytest with parameterized tests** (RECOMMENDED - High Confidence)
- **Version**: pytest 8.0+ (already in your project)
- **Purpose**: Systematic regression testing for regex patterns
- **Method**:
  - Create parameterized test cases for each regex pattern
  - Test positive cases (should match) and negative cases (should not match)
  - Include edge cases from deny lists
- **Example**:
  ```python
  @pytest.mark.parametrize("text,should_match", [
      ("MRN 12345678", True),
      ("#12345678", True),
      ("NC 2L", False),  # Deny list: nasal cannula
      ("12345", False),  # Too short
  ])
  def test_mrn_pattern(text, should_match):
      pattern = MRN_PATTERN
      assert bool(re.search(pattern, text)) == should_match
  ```
- **Rationale**:
  - Already using pytest in project
  - Clear pass/fail per regex pattern
  - Easy to add cases as bugs are found
- **Confidence Level**: 98% - Standard practice

**References**:
- [pytest parametrize documentation](https://docs.pytest.org/en/stable/parametrize.html)

### 2. **regex library** (RECOMMENDED - Medium Confidence)
- **Version**: 2025.1.24 (PyPI, supports Unicode 17.0.0)
- **Purpose**: Enhanced regex with better debugging and features
- **Key Features**:
  - More informative error messages
  - Fuzzy matching for typo-resilient patterns
  - Named group validation
  - Better Unicode handling (important for international names)
- **Rationale**:
  - Your patterns use lookbehinds/lookaheads extensively
  - Better error messages during development
  - Drop-in replacement for `re` module
- **Installation**: `pip install regex`
- **Confidence Level**: 75% - Nice-to-have, not essential

**References**:
- [regex PyPI Package](https://pypi.org/project/regex/)

### 3. **Online Tools for Development** (INFORMATIONAL)
- **regex101.com**: Real-time testing with Python flavor
- **pythex.org**: Python-specific regex tester
- **Use Case**: Development and debugging, NOT automated testing
- **Confidence Level**: N/A - Not for production testing

**References**:
- [regex101 Online Tester](https://regex101.com/)
- [Pythex Python Regex Editor](https://pythex.org/)

---

## Recommendations

### Immediate Additions (Phase 1)
1. **Install presidio-research** for systematic evaluation
   ```bash
   pip install presidio-evaluator
   ```
   - Use evaluation notebooks as templates
   - Integrate with existing `tests/evaluate_presidio.py`
   - Run against all 500 synthetic transcripts

2. **Add threshold calibration workflow**
   - Extract confidence scores from Presidio results
   - Use `sklearn.metrics.precision_recall_curve()` per entity type
   - Generate plots showing precision/recall tradeoffs
   - Update `app/config.py` with calibrated thresholds

3. **Expand regex test coverage**
   - Add pytest parameterized tests for all patterns in `app/recognizers/`
   - Include deny list cases (NC, RA, etc.)
   - Test edge cases from recent bug fixes

### Phase 2 Enhancements
4. **Add nervaluate** for entity-level debugging
   - Focus on partial match analysis
   - Identify entity boundary issues

5. **Consider spaCy's built-in evaluation**
   - Use `spacy.scorer.Scorer` for NER component evaluation
   - Generate confusion matrices for entity types
   - Useful if you fine-tune the spaCy model later

**References**:
- [spaCy Scorer API](https://spacy.io/api/scorer)
- [spaCy Training Documentation](https://spacy.io/usage/training)

### Maintenance Tasks
6. **Continuous evaluation**
   - Run presidio-research evaluation weekly during development
   - Track precision/recall trends over time
   - Set CI/CD thresholds (recall ≥95%, precision ≥70%)

---

## Not Recommended

### 1. **LLM-based De-identification** (e.g., GPT-4, Claude)
- **Why Not**:
  - Sends PHI to external APIs (HIPAA violation)
  - Your project's core value is LOCAL processing
  - Inconsistent, non-deterministic results
  - Expensive at scale
- **Exception**: Could use for synthetic data generation (no real PHI)
- **Confidence**: 100% - Fundamentally incompatible with project requirements

**References**:
- [Comparing Medical Text De-identification Performance](https://www.johnsnowlabs.com/comparing-medical-text-de-identification-performance-john-snow-labs-openai-azure-health-data-services-and-amazon-comprehend-medical/)

### 2. **spaCy Model Fine-tuning** (at this stage)
- **Why Not**:
  - Presidio + deny lists already achieving good results
  - Fine-tuning requires large annotated datasets (you have 500 synthetic)
  - Adds complexity and training overhead
  - Current issues are regex/threshold calibration, not model quality
- **Reconsider If**:
  - Recall drops below 90% after threshold tuning
  - New PHI types require detection (e.g., hospital-specific jargon)
- **Confidence**: 80% - Premature optimization at this stage

**References**:
- [Fine-Tuning spaCy Models](https://medium.com/ubiai-nlp/fine-tuning-spacy-models-customizing-named-entity-recognition-for-domain-specific-data-3d17c5fc72ae)
- [spaCy Training Guide](https://spacy.io/usage/training)

### 3. **Alternative PII Detection Frameworks** (e.g., Azure Health Data Services, AWS Comprehend Medical)
- **Why Not**:
  - Cloud-based (violates local processing requirement)
  - Subscription costs
  - Already invested in Presidio stack
  - Not necessarily better for pediatric domain
- **Confidence**: 95% - Not aligned with project goals

**References**:
- [Comparing John Snow Labs vs. Presidio](https://www.johnsnowlabs.com/comparing-john-snow-labs-medical-text-de-identification-with-microsoft-presidio/)

### 4. **Label Studio / UBIAI for Annotation** (not yet)
- **Why Not**:
  - Annotation tools are for creating training data
  - Only needed if fine-tuning spaCy (not recommended yet)
  - Synthetic data already covers test cases
- **Reconsider If**: You collect real de-identified handoffs for evaluation
- **Confidence**: 70% - Useful later, but not now

**References**:
- [Label Studio](https://labelstud.io/)
- [UBIAI Annotation Tool](https://ubiai.tools/)

### 5. **Complex Calibration Libraries** (e.g., Platt scaling, isotonic regression)
- **Why Not**:
  - Overkill for threshold tuning on 500 samples
  - Presidio scores are already reasonably calibrated
  - Simple precision-recall curves are sufficient
- **Reconsider If**: Dataset grows to 10,000+ samples
- **Confidence**: 85% - Unnecessary complexity

---

## Summary Table

| Tool | Purpose | Priority | Confidence | Install |
|------|---------|----------|------------|---------|
| **presidio-research** | Presidio evaluation | HIGH | 95% | `pip install presidio-evaluator` |
| **sklearn metrics** | Precision/recall/F1 | HIGH | 98% | (included with scikit-learn) |
| **pytest + parametrize** | Regex testing | HIGH | 98% | (already in project) |
| **Manual P-R curves** | Threshold calibration | MEDIUM | 95% | (sklearn + matplotlib) |
| **nervaluate** | Entity-level evaluation | MEDIUM | 80% | `pip install nervaluate` |
| **regex library** | Enhanced regex | LOW | 75% | `pip install regex` |
| **spaCy Scorer** | NER evaluation | LOW | 70% | (included with spaCy) |

---

## Next Steps for Roadmap

Based on this research, the roadmap should include:

1. **Phase 1: Establish Baseline**
   - Install presidio-research
   - Run evaluation on all 500 synthetic transcripts
   - Generate precision/recall metrics per entity type
   - Document current performance

2. **Phase 2: Calibrate Thresholds**
   - Extract confidence scores from Presidio
   - Plot precision-recall curves per entity type
   - Select thresholds that achieve ≥95% recall
   - Update `app/config.py` with calibrated values

3. **Phase 3: Systematic Regex Testing**
   - Create parameterized pytest suite for all patterns
   - Test deny list filtering
   - Add edge cases from production issues

4. **Phase 4: Continuous Evaluation**
   - Set up CI/CD to run evaluation on every commit
   - Track precision/recall trends
   - Alert on regressions

5. **Phase 5: Consider Fine-tuning** (only if needed)
   - If recall < 90% after threshold tuning
   - If new PHI types emerge
   - If false positive rate is unacceptable

---

*Research date: 2026-01-23*

**Researcher Notes**: This project already has excellent infrastructure (500 synthetic cases, custom recognizers, comprehensive tests). The focus should be on **measurement and tuning**, not rebuilding. The presidio-research toolkit is the most aligned tool since it's built specifically for this workflow. Threshold calibration will likely provide the biggest quality boost with the least effort.
