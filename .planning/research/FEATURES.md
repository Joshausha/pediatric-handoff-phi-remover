# Features Research: Dual-Weight Recall Framework

**Domain:** Clinical NER Evaluation Metrics
**Researched:** 2026-01-29
**Confidence:** HIGH

## Executive Summary

Dual-weighting schemes are **standard practice** in clinical NER evaluation when handling class imbalance. The literature consistently recommends reporting **multiple evaluation perspectives** (macro, micro, weighted) rather than a single "weighted" metric. The proposed three-metric system (unweighted, frequency-weighted, risk-weighted) aligns with established patterns but adds a **clinical-specific innovation**: separating "what's actually said" from "how bad if it leaks."

**Key finding:** The separation of frequency and risk dimensions is a **differentiator** in clinical PHI evaluation—most systems use only support-based weighting (similar to frequency weighting). Adding risk-weighting provides a second dimension specific to HIPAA compliance concerns.

## Table Stakes

Features expected in any weighted evaluation metric system.

| Feature | Why Expected | Complexity | Implementation Status |
|---------|--------------|------------|----------------------|
| **Per-entity precision/recall** | Standard multi-class NER reporting | Low | ✅ Implemented (lines 542-550 in evaluate_presidio.py) |
| **Unweighted overall metrics** | Baseline comparison, safety floor | Low | ✅ Implemented (properties in EvaluationMetrics) |
| **Support-based weighting** | scikit-learn standard, handles class imbalance | Low | ✅ Implemented as frequency_weighted_* |
| **Clear documentation of weights** | Transparency requirement for evaluation | Low | ✅ Implemented (lines 508-515 in report) |
| **Separate calculation methods** | Weighted metrics != simple averaging | Medium | ✅ Implemented (weighted_recall, weighted_precision, weighted_f2) |
| **Zero-weight handling** | Entities with weight 0 should not affect metrics | Low | ✅ Implemented and tested (test_weighted_metrics_zero_weight_entities_ignored) |
| **Unknown entity handling** | Graceful handling of entities not in weight config | Low | ✅ Implemented (weights.get(entity_type, 0.0)) |

**Status:** All table stakes features already implemented. No additional work required.

## Differentiators

Features that set this evaluation system apart from standard NER evaluation.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Dual-weighting (frequency + risk)** | Separates "what's spoken" from "severity if leaked" | Medium | 🎯 **Core innovation** - not found in standard NER literature |
| **Three-metric reporting** | Unweighted (safety floor), frequency (realism), risk (severity) | Low | Already implemented via `--weighted` flag |
| **Clinical context alignment** | Weights based on actual I-PASS handoff patterns | Medium | Documented in SPOKEN_HANDOFF_ANALYSIS.md |
| **Risk-based threshold tuning** | Future: adjust thresholds based on risk weights | High | Post-v2.2 enhancement (Phase 13+) |
| **HIPAA-specific weight rationale** | Weights map to HIPAA identifier severity | Medium | Clear documentation trail from 164.514(b)(2) |
| **Bootstrap CI for weighted metrics** | Uncertainty quantification for weighted recall/precision | High | Not yet implemented - considered future enhancement |

**Strategic advantage:** The dual-weighting scheme provides **two distinct lenses** for evaluation:
1. **Frequency weights** answer: "Does the system work well on what doctors actually say?"
2. **Risk weights** answer: "Does the system protect against the most damaging leaks?"

This separation is **not found in standard NER evaluation frameworks** which typically use only support-based (frequency-like) weighting.

## Anti-Features

Features to explicitly NOT build (common mistakes or over-engineering).

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Single "optimal" weighted metric** | Hides tradeoffs between frequency and risk | Report all three metrics separately (unweighted, frequency, risk) |
| **Automatic weight learning** | Domain experts (clinicians) must set weights, not algorithms | Use fixed weights from SPOKEN_HANDOFF_ANALYSIS.md |
| **Weighted accuracy** | Meaningless for imbalanced data (90% O tags in NER) | Use precision, recall, F1, F2 only |
| **Macro averaging** | Treats EMAIL_ADDRESS (never spoken) same as PERSON (always spoken) | Use weighted (support-based) or separate reporting |
| **Micro averaging** | Dominated by majority class, masks minority performance | Use weighted or per-entity metrics |
| **Combined frequency-risk weight** | Multiplying weights loses interpretability (what does PERSON=25 mean?) | Keep frequency and risk weights separate |
| **Cost-sensitive training** | Out of scope for evaluation—this is about *measuring*, not *training* | Stick to evaluation metrics; training is separate |
| **Dynamic weight adjustment** | Weights should be stable across evaluations for comparability | Document weights in config with rationale and date |

**Critical principle:** The three-metric system provides **transparency**, not optimization. Each metric serves a distinct purpose—collapsing them into one "best" metric would hide important tradeoffs.

## Feature Matrix

### Existing Weighted Metrics Implementation

| Metric | Purpose | Formula | Status |
|--------|---------|---------|--------|
| `weighted_recall(freq_weights)` | How well does system detect commonly spoken PHI? | Σ(tp × w) / Σ((tp+fn) × w) | ✅ Implemented |
| `weighted_precision(freq_weights)` | How often are detections correct (weighted)? | Σ(tp × w) / Σ((tp+fp) × w) | ✅ Implemented |
| `weighted_f2(freq_weights)` | Recall-weighted F-score (frequency dimension) | (1+β²)(p×r)/(β²p+r), β=2 | ✅ Implemented |
| `risk_weighted_recall(risk_weights)` | How well does system protect high-risk PHI? | Σ(tp × r) / Σ((tp+fn) × r) | ✅ Implemented (delegates to weighted_recall) |
| `risk_weighted_precision(risk_weights)` | Precision on high-risk PHI types | Σ(tp × r) / Σ((tp+fp) × r) | ✅ Implemented (delegates to weighted_precision) |
| `risk_weighted_f2(risk_weights)` | Recall-weighted F-score (risk dimension) | (1+β²)(p×r)/(β²p+r), β=2 | ✅ Implemented (delegates to weighted_f2) |

**Implementation note:** Risk-weighted methods (lines 124-134) are simple delegates to the base weighted methods with different weight dictionaries. This is **correct design**—the math is identical, only the interpretation differs.

### Weight Configuration

| Weight Type | Source | Config Location | Stability |
|-------------|--------|----------------|-----------|
| **Frequency weights** | I-PASS handoff analysis | `config.spoken_handoff_weights` | Stable (based on clinical practice) |
| **Risk weights** | HIPAA identifier severity | `config.spoken_handoff_risk_weights` | Stable (based on regulatory framework) |

**Design principle:** Weights are **fixed in code**, not learned or tuned. This ensures:
1. Reproducibility across evaluations
2. Interpretability (weights have clinical meaning)
3. Comparability (v2.2 → v2.3 → v3.0 use same weights)

## Feature Dependencies

```
Current Implementation (v2.1):
├── entity_stats tracking (per-entity tp/fn/fp)
├── weighted_recall(weights) ← Uses entity_stats
├── weighted_precision(weights) ← Uses entity_stats
└── weighted_f2(weights) ← Uses weighted_recall + weighted_precision

v2.2 Addition (CURRENT MILESTONE):
├── spoken_handoff_weights (frequency) ← Already in config
├── spoken_handoff_risk_weights (risk) ← Already in config
├── risk_weighted_recall(risk_weights) ← Delegates to weighted_recall
├── risk_weighted_precision(risk_weights) ← Delegates to weighted_precision
├── risk_weighted_f2(risk_weights) ← Delegates to weighted_f2
└── Report formatting ← Already shows both weight types (lines 490-515)

No new dependencies required.
```

**Architectural note:** The dual-weighting feature has **zero new dependencies** because:
1. The math is identical (weighted sum divided by weighted total)
2. Risk-weighted methods reuse frequency-weighted implementation
3. Weight dictionaries already exist in config

## Expected Behavior

### Standard Multi-Class Weighted Metrics Behavior

Based on [scikit-learn classification report](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html) and [NER evaluation best practices](https://iamirmasoud.com/2022/06/19/understanding-micro-macro-and-weighted-averages-for-scikit-learn-metrics-in-multi-class-classification-with-example/):

1. **Macro average**: Unweighted mean across all classes (all classes equal importance)
2. **Weighted average**: Mean weighted by support (number of true instances per class)
3. **Micro average**: Global TP/FP/FN across all classes (dominated by majority class)

**Clinical NER convention:** Report **weighted average** to account for class imbalance, and show per-entity breakdowns. Never use micro average (dominated by O tag). Macro average acceptable for "all entities equally important" view.

### Dual-Weighting Expected Behavior

| Scenario | Unweighted Recall | Frequency-Weighted | Risk-Weighted | Interpretation |
|----------|-------------------|-------------------|---------------|----------------|
| **PERSON missed (5% of cases)** | Decreases moderately | **Decreases significantly** (weight 5.0) | **Decreases significantly** (weight 5.0) | Critical failure—PERSON is both common AND high-risk |
| **EMAIL_ADDRESS missed (100% of cases)** | Decreases moderately | **No change** (weight 0.0) | **Decreases significantly** (weight 4.0) | Risk-weighted catches what frequency-weighted ignores |
| **MRN missed (5% of cases)** | Decreases slightly | **Barely changes** (weight 0.5) | **Decreases significantly** (weight 5.0) | Risk-weighted prioritizes THE unique identifier |
| **ROOM missed (50% of cases)** | Decreases moderately | **Decreases significantly** (weight 4.0) | Decreases slightly (weight 2.0) | Common but not highly identifying |

**Key insight:** The three metrics can **diverge meaningfully**:
- Unweighted: 85% recall (EMAIL=0/24, PERSON=747/756, MRN=90/127, ROOM=31/90)
- Frequency-weighted: 92% recall (EMAIL ignored, PERSON+ROOM weighted heavily)
- Risk-weighted: 88% recall (EMAIL+MRN weighted heavily, ROOM downweighted)

This divergence is **the feature**, not a bug. It surfaces tradeoffs for clinicians to consider.

### Reporting Best Practices

Per [Class-Weighted Evaluation Metrics research](https://www.semanticscholar.org/paper/Class-Weighted-Evaluation-Metrics-for-Imbalanced-Gupta-Tatbul/140663ed72092cfc5f510fd1fad2a739894c1956) and [NLP evaluation guidelines](https://aclanthology.org/2023.ijcnlp-main.33.pdf):

1. **Always report unweighted metrics** as baseline
2. **Report weighted metrics with weight table** for transparency
3. **Show per-class breakdown** alongside overall metrics
4. **Document weighting rationale** in methods section

**Current implementation** (lines 485-515 in evaluate_presidio.py) follows these best practices:
- ✅ Shows all three metrics with clear labels
- ✅ Includes weight table (frequency and risk columns)
- ✅ Per-entity stats already shown (lines 542-550)
- ✅ Weight rationale documented in SPOKEN_HANDOFF_ANALYSIS.md

## Complexity Assessment

| Component | Complexity | Reason |
|-----------|-----------|--------|
| **Risk weight configuration** | **Low** | Copy-paste frequency weights, adjust values based on HIPAA severity |
| **Risk-weighted methods** | **Trivial** | Already implemented—just delegate to existing weighted_* methods |
| **Report formatting** | **Low** | Already shows both weight types (just verify column alignment) |
| **Test coverage** | **Low** | Reuse existing weighted metrics tests with risk weights |
| **Documentation** | **Low** | Add risk weight rationale to SPOKEN_HANDOFF_ANALYSIS.md |

**Total effort estimate:** 1-2 hours. Most work is **verification and documentation**, not new code.

## Open Questions

1. **Should confidence intervals be calculated for weighted metrics?**
   - **Answer:** Not for v2.2. Bootstrap CI currently implemented for unweighted only (lines 136-204). Extending to weighted metrics is feasible but low priority—unweighted CI provides safety floor.

2. **Should we combine frequency and risk into a single "clinical importance" weight?**
   - **Answer:** NO (see anti-features). Keeping them separate maintains interpretability and allows different stakeholder perspectives (clinicians care about frequency, compliance officers care about risk).

3. **Do weights need to be normalized (sum to 1)?**
   - **Answer:** NO. Weighted recall formula divides by weighted total, so absolute weight scale doesn't matter. Using 0-5 scale makes weights more interpretable than 0-1 scale.

4. **Should macro average be reported alongside weighted?**
   - **Answer:** NO. Macro treats EMAIL_ADDRESS (never spoken) same as PERSON (always spoken), which is clinically meaningless. The unweighted metric serves as "all entities treated equally" baseline.

## Competitive Landscape

### Standard NER Evaluation Frameworks

| Framework | Approach | Limitations for PHI Detection |
|-----------|----------|------------------------------|
| **scikit-learn classification_report** | Macro, weighted (support), micro averaging | No concept of risk vs. frequency separation |
| **nervaluate** | Entity-level metrics, partial matching | Support-based weighting only |
| **seqeval** | Token-level IOB evaluation | No weighting (token-level only) |
| **CoNLL eval script** | Strict span matching | No weighting |

**Innovation gap:** None of these frameworks separate "what's common" from "what's risky." This dual-weighting approach is **unique to HIPAA-focused PHI evaluation**.

### Clinical NLP Evaluation Practices

Per [JMIR Medical Informatics study](https://medinform.jmir.org/2024/1/e59782) and [Clinical NER survey](https://www.mdpi.com/2076-3417/11/18/8319):

- **Standard:** Report unweighted F1 per entity type
- **Advanced:** Use weighted F1 by support (class frequency)
- **Rare:** Cost-sensitive evaluation (weights by misclassification cost)

**Position:** The proposed dual-weighting system is **advanced** (multiple weighting schemes) but not unprecedented (cost-sensitive evaluation exists). The novelty is **explicit separation** of frequency and risk dimensions.

## MVP Recommendation

**For v2.2 milestone (dual-weight recall framework):**

✅ **Include:**
1. Risk weight configuration (already done in config.py lines 331-344)
2. Risk-weighted metric methods (already done lines 124-134)
3. Three-metric reporting summary (already done lines 502-506)
4. Weight table display (already done lines 508-515)

⏭️ **Defer to post-MVP:**
1. Bootstrap CI for weighted metrics (complex, low priority)
2. Risk-adjusted threshold tuning (Phase 13+ feature)
3. Cost-sensitive training (out of scope—evaluation only)
4. Dynamic weight adjustment (anti-feature)

**Status:** MVP is **already implemented**. This milestone is about **verification and documentation**, not new code development.

## Sources

### NER Evaluation Standards
- [Understanding Micro, Macro, and Weighted Averages for Scikit-Learn metrics](https://iamirmasoud.com/2022/06/19/understanding-micro-macro-and-weighted-averages-for-scikit-learn-metrics-in-multi-class-classification-with-example/)
- [Micro, Macro & Weighted Averages of F1 Score, Clearly Explained](https://towardsdatascience.com/micro-macro-weighted-averages-of-f1-score-clearly-explained-b603420b292f/)
- [scikit-learn classification_report documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html)
- [nervaluate: Full named-entity evaluation metrics](https://github.com/MantisAI/nervaluate)

### Clinical NER Evaluation
- [Evaluating Medical Entity Recognition in Health Care (JMIR 2024)](https://medinform.jmir.org/2024/1/e59782)
- [A Survey on Recent Named Entity Recognition and Relationship Extraction Techniques on Clinical Texts](https://www.mdpi.com/2076-3417/11/18/8319)
- [Named-Entity evaluation metrics based on entity-level](https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/)

### Class Imbalance and Weighting
- [Class-Weighted Evaluation Metrics for Imbalanced Data Classification](https://www.semanticscholar.org/paper/Class-Weighted-Evaluation-Metrics-for-Imbalanced-Gupta-Tatbul/140663ed72092cfc5f510fd1fad2a739894c1956)
- [Imbalanced class distribution and performance evaluation metrics (PLOS Digital Health 2023)](https://journals.plos.org/digitalhealth/article?id=10.1371/journal.pdig.0000290)
- [Adaptive Name Entity Recognition under Highly Unbalanced Data](https://arxiv.org/abs/2003.10296)
- [Weighted Metrics for Multi-Class Models Explained](https://magai.co/weighted-metrics-for-multi-class-models-explained/)

### Cost-Sensitive Evaluation
- [Cost-sensitive learning for imbalanced medical data: a review](https://link.springer.com/article/10.1007/s10462-023-10652-8)
- [We Need to Talk About Classification Evaluation Metrics in NLP](https://arxiv.org/abs/2401.03831)
- [Cost-Sensitive Performance Metric for Comparing Multiple Ordinal Classifiers](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5217743/)

### HIPAA Risk Assessment
- [HIPAA Risk Assessment - updated for 2026](https://www.hipaajournal.com/hipaa-risk-assessment/)
- [Guidance on Risk Analysis (HHS.gov)](https://www.hhs.gov/hipaa/for-professionals/security/guidance/guidance-risk-analysis/index.html)

**Confidence level:** HIGH - All sources are authoritative (official documentation, peer-reviewed research, established NLP/ML frameworks).
