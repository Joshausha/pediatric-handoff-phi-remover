# Pitfalls Research: PHI Detection Improvement

**Research Date**: 2026-01-23
**Project**: Pediatric Handoff PHI Remover Quality Improvement

## Executive Summary

PHI de-identification improvement projects face distinct failure modes that differ from general NLP tuning. The most critical distinction: **false negatives (missed PHI) carry legal/compliance risk, while false positives (over-scrubbing) degrade clinical utility**. This asymmetry drives many common mistakes.

---

## Regex Tuning Pitfalls

### 1. **Lexical Ambiguity - Over-Scrubbing Medical Terms**

**What goes wrong**: Regex patterns designed for one purpose inadvertently mask unrelated text due to lexical ambiguities. Medical terms that appear in proper name lists (e.g., "breast") cause over-scrubbing. Laboratory values with 4+ consecutive digits (e.g., platelet count "68,000") get flagged as PHI identifiers.

**Warning signs**:
- Clinical staff report "nonsensical" de-identified transcripts
- Medical abbreviations/terms appear as `[REDACTED]`
- Numeric lab values disappear from output

**Prevention strategy**:
- Maintain **deny lists** for medical terms (NC, RA, OR, ER, IV, PO, etc.)
- Test regex patterns against clinical vocabulary databases (e.g., SNOMED CT)
- Use lookbehind/lookahead patterns to preserve medical context: `(?<!platelet count: )\b\d{5,}\b`

**Phase mapping**: Phase 2 (Regex Refinement) - Build comprehensive medical term deny lists

---

### 2. **Case Sensitivity Inconsistencies**

**What goes wrong**: Inconsistent case handling across different entity types creates detection gaps. Current system has PERSON deny list case-insensitive but LOCATION exact match—"Mom Jessica" caught but "mom jessica" missed.

**Warning signs**:
- Detection works in test data (proper capitalization) but fails in real transcripts (variable case)
- Some entity types show significantly lower recall than others
- Case-normalized test suite passes but production detection fails

**Prevention strategy**:
- **Standardize**: All deny lists and pattern matching must use same case handling (recommend `.lower()` normalization)
- Test with **case-variation synthetic data**: "Mom", "mom", "MOM", "mOm"
- Document case sensitivity policy in `config.py` with enforcement

**Phase mapping**: Phase 1 (Case Normalization) - Critical foundation before regex refinement

**Reference**: Clinical NER systems use capitalization features (allCaps, upperInitial, lowercase, mixedCaps) as signal, but **deny list filtering must be case-insensitive** to avoid gaps.

---

### 3. **Context-Agnostic Pattern Matching**

**What goes wrong**: Regex patterns without contextual awareness create false positives. Patterns like `\bMom\b` flag "Contact mom" (instruction) as a name, when only "Mom [Name]" should be flagged.

**Warning signs**:
- High false positive rate for relationship words (Mom, Dad, Guardian)
- Standalone prepositions/articles flagged as entities ("to OR", "the ER")
- Numbers without medical context flagged as MRNs

**Prevention strategy**:
- Use **positive lookbehind** to require context: `(?<=Mom )[A-Z][a-z]+` matches "Mom Jessica" but not "Contact mom"
- Build **context-aware patterns**: Only flag "OR" when not preceded by medical verbs (go, transfer, admit)
- Test with **minimal pairs**: "Mom Jessica" (PHI) vs "Contact mom" (not PHI)

**Phase mapping**: Phase 2 (Regex Refinement) - After case normalization, before threshold tuning

---

### 4. **Overfitting to Test Data Format**

**What goes wrong**: Patterns optimized for structured test data fail on variable real-world transcription. Voice transcription produces "Jessica is mom" but test data only has "Mom Jessica"—lookbehind patterns miss reverse order.

**Warning signs**:
- High performance on synthetic data, low performance on real transcripts
- Detection works for "Baby Smith" but not "Smith is the baby"
- Patterns assume word order (lookbehind) that isn't stable in speech-to-text

**Prevention strategy**:
- **Bidirectional patterns**: Match both "Mom Jessica" and "Jessica is Mom"
- Test against **speech-to-text artifacts**: filler words, incomplete sentences, hesitations
- Use **N-gram analysis** of real transcripts to identify actual patterns before writing regex

**Phase mapping**: Phase 3 (Validation) - Real transcript testing reveals overfitting

**Reference**: Research shows "one set of vocabularies that work well on one source of clinical notes may not work well on another set of notes"—domain-specific overfitting is a recognized NLP problem.

---

## Threshold Calibration Pitfalls

### 5. **Arbitrary Dual-Threshold Systems**

**What goes wrong**: Current system has detection threshold 0.35 and validation threshold 0.7 with **no documented calibration methodology**. Unclear why these values, unclear what they optimize for.

**Warning signs**:
- Threshold values chosen by intuition or copied from examples
- No documented precision/recall metrics at chosen thresholds
- Different thresholds for different stages without justification

**Prevention strategy**:
- Generate **Precision-Recall curve** using 500 synthetic transcripts
- Define **business requirements**: "Must achieve 99% recall (catch 99% of PHI) with acceptable precision"
- Use **F-beta score** (β=2 for recall priority, β=0.5 for precision priority) to select optimal threshold
- Document calibration: "Threshold 0.35 achieves 99.2% recall, 82% precision on validation set"

**Phase mapping**: Phase 4 (Threshold Optimization) - After regex refinement, use metrics to select thresholds

**Reference**: "A higher threshold will increase precision but decrease recall—A Precision-Recall Curve is a great tool for visualizing the trade-off."

---

### 6. **Ignoring Precision-Recall Tradeoffs**

**What goes wrong**: Improving one metric (e.g., precision to reduce over-scrubbing) degrades the other (recall), increasing missed PHI risk. In healthcare, **recall takes precedence** because missed PHI has legal consequences, but excessive false positives make transcripts clinically useless.

**Warning signs**:
- "Fixed" over-scrubbing by raising threshold, now missing PHI in spot checks
- Focused only on F1 score (equal weighting) when recall should be prioritized
- No documentation of acceptable false positive rate

**Prevention strategy**:
- Define **risk tolerance**: "No more than 1% missed PHI (99% recall minimum)"
- Set **secondary optimization**: "Maximize precision while maintaining 99% recall"
- Use **F2 score** (weighs recall 2x precision) as optimization target for PHI detection
- Monitor **both metrics** in production: alert if recall drops below 99% OR precision drops below 75%

**Phase mapping**: Phase 4 (Threshold Optimization) - Define risk tolerance before calibration

**Reference**: "Recall takes precedence when the cost of missing a positive instance (false negatives) is substantial, with a classic example being in healthcare."

---

### 7. **Single-Point Threshold Optimization**

**What goes wrong**: Choosing single optimal threshold ignores that different entity types may need different thresholds. PERSON names might need higher confidence than LOCATION to reduce false positives.

**Warning signs**:
- Some entity types have much higher false positive rates than others
- Per-entity precision/recall metrics show large variance
- Uniform threshold applied to all recognizers

**Prevention strategy**:
- Calculate **per-entity-type metrics**: Precision/recall for PERSON, LOCATION, MRN, etc.
- Consider **entity-specific thresholds** if variance is high (>10% difference in F2 score)
- Test ensemble approach: Conservative threshold (0.3) for high-risk entities (PERSON, MRN), higher threshold (0.5) for lower-risk (LOCATION)

**Phase mapping**: Phase 4 (Threshold Optimization) - After evaluating per-entity metrics

---

## Metrics Pitfalls

### 8. **Testing Only on Synthetic Data**

**What goes wrong**: Synthetic data created by project team reflects **assumptions about PHI patterns**, not reality. Validation on synthetic data gives false confidence—real transcripts contain edge cases not imagined during synthetic data generation.

**Warning signs**:
- 99% metrics on test suite but users report missed PHI in production
- Synthetic data all follows same grammatical patterns ("Mom [Name]" format)
- Test cases don't include speech-to-text artifacts (stutters, corrections, fragments)

**Prevention strategy**:
- Create **adversarial test cases**: Deliberately unusual patterns ("the mother, Jessica she said", "baby boy, Smith is his name")
- Use **real de-identified transcripts** for validation (obtain from other medical centers if possible)
- **External validation**: Have independent clinician review sample of de-identified transcripts
- **Bootstrap confidence intervals**: Calculate 95% CI for recall metric using resampling

**Phase mapping**: Phase 3 (Validation) - Before declaring success, test on external data

**Reference**: "Rigorous validation of synthetic data is necessary to confirm clinical utility and reliability. Organizations should conduct external validation and re-identification testing."

---

### 9. **Ignoring Class Imbalance**

**What goes wrong**: PHI entities are **rare** in transcripts (maybe 2-5% of tokens). Accuracy metric is misleading: 95% accuracy could mean catching 0% of PHI if you just label everything as "not PHI". Precision/recall are mandatory metrics.

**Warning signs**:
- Reporting "98% accuracy" as main metric
- No calculation of prevalence (what % of tokens are actually PHI)
- Test data has unrealistically high PHI density

**Prevention strategy**:
- **Never use accuracy** as primary metric for PHI detection
- Report **precision, recall, F2 score** as standard metrics
- Calculate **PHI prevalence** in test data: should match real transcripts (~2-5%)
- Use **stratified sampling** when creating test sets (ensure rare entity types represented)

**Phase mapping**: Phase 0 (Planning) - Choose correct metrics from start

---

### 10. **Neglecting Error Proximity Analysis**

**What goes wrong**: Research shows **78% of false negative tokens were either directly preceded by or followed by a correctly classified PHI token**. This pattern indicates boundary detection errors—missed the last name when you caught the first name.

**Warning signs**:
- False negatives cluster near true positives
- Multi-word entities partially detected ("Jessica" caught but "Smith" missed)
- Span boundary errors in output

**Prevention strategy**:
- Analyze **false negative proximity**: Are misses adjacent to correct detections?
- Test **multi-token entities** explicitly: "Jessica Lynn Smith" (should detect all 3)
- Consider **BIO tagging** (Beginning, Inside, Outside) for better boundary detection
- Add **span expansion logic**: If detecting "Mom", check next 1-2 tokens for names

**Phase mapping**: Phase 3 (Validation) - Error analysis should include proximity metrics

**Reference**: "78% of false negative tokens were either directly preceded by or followed by a correctly classified PHI token" (NCBI study)

---

## Testing Pitfalls

### 11. **No Ground Truth for Real Transcripts**

**What goes wrong**: You can't measure recall on real transcripts if you don't know what PHI is actually present. Spot-checking by humans is unreliable—humans miss PHI too, creating false confidence.

**Warning signs**:
- "Manually reviewed 10 transcripts, looks good" as validation evidence
- No inter-rater reliability measurement for human reviewers
- No gold-standard annotated dataset

**Prevention strategy**:
- Create **gold-standard dataset**: Have 2-3 independent clinicians annotate same 50 transcripts, measure inter-rater agreement (Cohen's kappa)
- Use only **high-agreement transcripts** (kappa > 0.8) as ground truth
- For production monitoring, use **expert panel**: 3 reviewers, majority vote
- Implement **human-in-the-loop checks** for random sample of transcripts

**Phase mapping**: Phase 3 (Validation) - Create gold standard before declaring metrics

**Reference**: "Embedding human-in-the-loop checks especially for free-text and edge cases" recommended as best practice.

---

### 12. **Insufficient Coverage of Edge Cases**

**What goes wrong**: Test suite focuses on common patterns (standard names, phone numbers) but misses edge cases that appear in real transcripts (nicknames, informal speech, transcription errors).

**Warning signs**:
- Test suite has 500 cases but only 10-15 distinct PHI patterns
- All names in test data are standard English names
- No test cases for transcription errors ("Doctor Jen—uh, Jennifer")

**Prevention strategy**:
- **Taxonomy of edge cases**: Nicknames, initials, titles, hyphenated names, transcription corrections, multiple entities in one phrase
- **Adversarial testing**: Try to break system with unusual but realistic inputs
- **Cultural diversity**: Test non-English names common in local population
- **Speech artifacts**: Stutters ("J-J-Jessica"), corrections ("Mom—I mean the mother"), hesitations ("uh", "um")

**Phase mapping**: Phase 3 (Validation) - Expand test suite with edge cases

---

### 13. **Ignoring Computational Performance**

**What goes wrong**: Regex tuning adds complexity (lookbehinds, alternations), increasing processing time. Presidio's NER models are already slow—if regex preprocessing adds 2x overhead, 30-minute transcripts might timeout.

**Warning signs**:
- Frontend already increased timeout from 10min to 30min
- Complex regex patterns with nested alternations and lookarounds
- No performance benchmarking before deploying changes

**Prevention strategy**:
- **Benchmark processing time**: Measure ms/token before and after regex changes
- Set **performance budget**: "Regex preprocessing must complete in <10% of total processing time"
- **Profile regex patterns**: Some patterns are expensive (catastrophic backtracking)
- Test with **realistic transcript lengths**: 5,000-10,000 word transcripts

**Phase mapping**: Phase 2 (Regex Refinement) - Profile each new pattern

---

### 14. **Surrogation vs. Redaction Confusion**

**What goes wrong**: Surrogation (replacing PHI with plausible synthetic values) is **stronger privacy protection** than redaction (`[NAME]`) because false negatives are hidden. Current system uses redaction—any missed PHI is exposed.

**Warning signs**:
- System uses `[NAME]`, `[DATE]` placeholder approach
- No consideration of surrogation option
- False negative PHI remains visible in output

**Prevention strategy**:
- **Evaluate surrogation**: Replace "Jessica" with synthetic name "Emma Johnson" (preserves clinical utility, hides false negatives)
- If sticking with redaction, **must achieve very high recall** (>99.5%) since misses are visible
- Consider **hybrid approach**: Surrogation for names/dates, redaction for phone numbers
- Document rationale for redaction vs surrogation choice

**Phase mapping**: Phase 0 (Planning) - Choose de-identification strategy before building

**Reference**: "Surrogation strengthens privacy protections as any false-negative PHI values are hidden within a document."

---

### 15. **No Residual Risk Measurement**

**What goes wrong**: HIPAA Safe Harbor method requires removing 18 identifiers, but regex-based systems have **inherent miss rate**. Without measuring residual risk (probability PHI remains), you can't claim HIPAA compliance.

**Warning signs**:
- No formal risk assessment documentation
- Claiming "HIPAA-compliant" without statistical evidence
- No confidence intervals on recall metric

**Prevention strategy**:
- Calculate **95% confidence interval** for recall using bootstrap resampling
- Report **upper bound on miss rate**: "95% confident that ≤1.2% of PHI is missed"
- Compare against **HIPAA Expert Determination** requirements (statistician must certify risk)
- Consider formal **Safe Harbor audit**: External expert validates 18 identifier removal

**Phase mapping**: Phase 5 (Compliance Validation) - Final step before production

**Reference**: "Organizations should monitor de-identification performance by measuring residual risk and computing confidence intervals to capture sampling uncertainty."

---

## Prevention Checklist

Use this checklist during planning and review:

### Phase 0: Planning
- [ ] Chosen metrics appropriate for imbalanced data (precision/recall/F2, not accuracy)
- [ ] Defined risk tolerance (e.g., "99% recall minimum")
- [ ] Selected de-identification strategy (redaction vs surrogation) with documented rationale
- [ ] Identified external validation data source

### Phase 1: Case Normalization
- [ ] All deny lists use consistent case handling (recommend lowercase normalization)
- [ ] Case sensitivity policy documented in `config.py`
- [ ] Test suite includes case variation examples

### Phase 2: Regex Refinement
- [ ] Medical term deny lists built from clinical vocabulary databases
- [ ] Context-aware patterns use lookahead/lookbehind appropriately
- [ ] Bidirectional patterns handle both "Mom Jessica" and "Jessica is mom"
- [ ] Each new pattern benchmarked for performance (catastrophic backtracking check)
- [ ] Patterns tested against minimal pairs (PHI vs non-PHI)

### Phase 3: Validation
- [ ] Gold-standard dataset created with inter-rater reliability (kappa > 0.8)
- [ ] Edge case taxonomy covers nicknames, transcription errors, cultural diversity
- [ ] Error proximity analysis performed (are false negatives adjacent to true positives?)
- [ ] External validation on real transcripts (not just synthetic data)
- [ ] Adversarial testing with deliberately unusual patterns

### Phase 4: Threshold Optimization
- [ ] Precision-recall curve generated using validation set
- [ ] Threshold selection documented with supporting metrics
- [ ] Both precision and recall monitored (not just F1)
- [ ] Per-entity-type metrics calculated (consider entity-specific thresholds)
- [ ] F2 score used as optimization target (prioritizes recall)

### Phase 5: Compliance Validation
- [ ] Residual risk calculated with 95% confidence interval
- [ ] External expert review (human-in-the-loop sample)
- [ ] HIPAA Safe Harbor or Expert Determination compliance documented
- [ ] Production monitoring plan defined (alert thresholds for recall/precision)

---

## Key Takeaways

1. **Recall is non-negotiable** in PHI detection—legal/compliance risk outweighs clinical utility degradation from over-scrubbing
2. **Case sensitivity inconsistencies** are the most common preventable error—standardize early
3. **Synthetic data validation** creates false confidence—external validation is mandatory
4. **Context-agnostic regex** generates high false positive rates—use lookbehind/lookahead patterns
5. **Threshold optimization without business requirements** is guessing—define risk tolerance first

---

## References

- [PHI De-Identification at HHS](https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html)
- [18 HIPAA Identifiers - Censinet](https://censinet.com/perspectives/18-hipaa-identifiers-for-phi-de-identification)
- [De-identification of clinical notes with pseudo-labeling - BMC](https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/s12911-025-02913-z)
- [Open Source PHI De-Identification Review - IntuitionLabs](https://intuitionlabs.ai/articles/open-source-phi-de-identification-tools)
- [Software Tool for Removing Patient Identifying Information - PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2528047/)
- [Deidentification using pre-trained transformers - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8330601/)
- [Automated de-identification of free-text medical records - BMC](https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/1472-6947-8-32)
- [Comparing Medical Text De-identification - John Snow Labs](https://www.johnsnowlabs.com/comparing-john-snow-labs-medical-text-de-identification-with-microsoft-presidio/)
- [Precision/Recall Tradeoff - Medium](https://medium.com/analytics-vidhya/precision-recall-tradeoff-79e892d43134)
- [Machine Learning Classification Metrics - Google Developers](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall)
- [Threshold Dilemma in Machine Learning - Medium](https://medium.com/@ibezimchike/threshold-dilemma-in-machine-learning-balancing-precision-and-recall-for-optimal-model-performance-eb3dc01e162e)
- [Medical Image De-Identification: Synthetic DICOM Data - arXiv](https://arxiv.org/html/2508.01889)
- [Synthesizing Healthcare Data for AI with HIPAA - Tonic.ai](https://www.tonic.ai/guides/hipaa-ai-compliance)
- [Evaluating GPT models for clinical note de-identification - Nature](https://www.nature.com/articles/s41598-025-86890-3)
- [De-Identification of Personal Information - NIST](https://nvlpubs.nist.gov/nistpubs/ir/2015/nist.ir.8053.pdf)
- [Recent Advances in Named Entity Recognition - arXiv](https://arxiv.org/html/2401.10825v3)
- [Clinical NER and Relation Extraction: Systematic Review - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1386505623001405)
- [Clinical Named Entity Recognition Using Deep Learning - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5977567/)

---

*Research completed: 2026-01-23*
*Document Version: 1.0*
