# Pitfalls Research: Dual-Weight Recall Framework for NER Evaluation

**Domain**: Adding multi-dimensional weighting to existing NER evaluation system
**Researched**: 2026-01-29
**Context**: PHI detection system with existing unweighted metrics, adding frequency-weighted and risk-weighted evaluation

---

## Critical Pitfalls

### Pitfall 1: Zero-Weight Entities Completely Ignored in Aggregation

**What goes wrong**: Entities with weight=0 (like EMAIL_ADDRESS, PEDIATRIC_AGE) contribute nothing to weighted metrics, even if they have perfect or terrible performance. This can mask serious detection failures.

**Why it happens**:
- Weighted calculations multiply by weight before summing: `weighted_tp += stats["tp"] * weight`
- When weight=0, `0 * anything = 0`, completely eliminating that entity from the metric
- This is mathematically correct for "spoken handoff frequency" but dangerous if misinterpreted

**Consequences**:
- EMAIL_ADDRESS could have 0% recall (leaking PHI) but weighted recall shows 100%
- Stakeholders might think the system is safe when it's leaking zero-weight PHI
- Zero-weight entities become invisible to monitoring and alerts

**Prevention**:
- **Always report both weighted AND unweighted metrics** side-by-side
- Document that zero-weight entities are excluded from weighted calculations
- Add explicit safety check: unweighted recall must still be 100% for HIPAA compliance
- Consider separate "safety floor" metric that weights all PHI types equally at minimum 1.0

**Detection**:
- Warning sign: Weighted recall significantly higher than unweighted
- Warning sign: Zero-weight entity has FN>0 but doesn't appear in alerts
- Test: Add test case where only zero-weight entity fails, verify it's caught

**Which phase should address it**: Phase 1 (initial implementation) - Add dual reporting and safety floor checks

**Reference**: Existing test `test_weighted_metrics_zero_weight_entities_ignored()` validates calculation but doesn't address the safety risk

---

### Pitfall 2: Weight Scheme Confusion - Using Wrong Weights for Wrong Purpose

**What goes wrong**: Using frequency weights (how often spoken) when you need risk weights (severity if leaked), or vice versa. Results in misleading evaluation that doesn't match the decision context.

**Why it happens**:
- Two weight schemes look similar (both dict[str, float])
- Similar function signatures: `weighted_recall(weights)` accepts either
- No type distinction between frequency and risk weights
- Function names like `weighted_recall()` don't indicate which weighting to use

**Consequences**:
- Optimizing for frequency weights might ignore critical but rare PHI (MRN)
- Using risk weights for handoff evaluation overweights never-spoken PHI
- Dashboard shows wrong metric for the decision being made
- Threshold tuning uses wrong objective function

**Prevention**:
- **Use explicit function names**: `frequency_weighted_recall()` vs `risk_weighted_recall()`
- Add enum or type alias: `FrequencyWeights` vs `RiskWeights` with type hints
- Document in config: which weight scheme to use for which decision
- Add validation: warn if weights don't sum to expected range (frequency: ~17, risk: ~29)

**Detection**:
- Code review: Check weight dict name matches function intent
- Test: Verify frequency and risk weights produce different results
- Documentation audit: Each weighted metric call has rationale for weight choice

**Which phase should address it**: Phase 1 - Use separate function names from the start to prevent confusion

---

### Pitfall 3: Integer vs Float Division (Already Fixed, But Fragile)

**What goes wrong**: Python 2-style integer division (`/`) used with integer weights causes incorrect calculations. Even in Python 3, mixing int and float types can cause subtle precision issues.

**Why it happens**:
- Weights in config defined as `int` (0-5 range)
- Counters (TP, FN, FP) are integers
- Integer math: `100 / 3 = 33.333...` but `int(100) / int(3)` behavior varies by Python version
- Python 3 fixed this, but type confusion remains

**Consequences**:
- Weighted recall calculated as 91% instead of 91.5% (example)
- Test expectations hardcoded to wrong values, masking the bug
- Precision loss accumulates across multiple entity types

**Prevention**:
- **Declare weights as `float` in Pydantic Field**: `dict[str, float]` not `dict[str, int]`
- Use explicit float conversion in calculations: `float(stats["tp"]) * weight`
- Add type hints everywhere: `def weighted_recall(weights: dict[str, float]) -> float`
- Test with values that expose integer division: 1/3, 2/3 (should be 0.333, 0.666)

**Detection**:
- Warning sign: Weighted metrics come out as exact integers (91% not 91.5%)
- Warning sign: Test expectations use integers: `assert recall == 91` not `assert abs(recall - 0.915) < 0.01`
- Static analysis: mypy catches type mismatches if hints present

**Which phase should address it**: Phase 1 - Define types correctly from start, add precision tests

**Reference**: Existing project has weights as `int` in config (line 315-344 of config.py) but calculations use `float` return types - this type mismatch is risky

---

### Pitfall 4: Missing Entities in Weight Dictionary (Silent Failure)

**What goes wrong**: New entity type added to detection (e.g., "US_SSN") but not added to weight dictionaries. Code silently treats it as weight=0, hiding its performance.

**Why it happens**:
- Weight dicts are manually maintained in config
- Entity list (`phi_entities`) separate from weight dicts
- `weights.get(entity_type, 0.0)` defaults to 0 instead of raising error
- No validation that all detected entities have weights

**Consequences**:
- New entity types invisible in weighted metrics
- Performance regression not caught until manual review
- Weight misconfiguration goes unnoticed (typo: "PERSON" vs "PERSONS")

**Prevention**:
- **Add Pydantic validator**: Check that all entities in `phi_entities` have weights
- At runtime: Log warning if detected entity not in weights
- In tests: Assert that weight keys match entity list exactly
- Consider: Single source of truth - derive entity list from weight keys

**Detection**:
- Test: Add entity to `phi_entities`, run without adding weights, verify error
- CI check: Compare `phi_entities` list with weight dict keys
- Runtime logging: "Entity X detected but has no weight assigned"

**Which phase should address it**: Phase 1 - Add validation before weights are used in production

---

## High-Risk Pitfalls

### Pitfall 5: Backwards Compatibility - Existing Tests Break

**What goes wrong**: Adding weighted metrics changes function signatures, return types, or report formats. Existing tests and dashboards break, requiring extensive rework.

**Why it happens**:
- Weighted metrics added as new parameters to existing functions
- Report format changes to include weighted metrics
- Test fixtures hardcoded to old metric output format
- Downstream consumers (CI checks, dashboards) expect specific format

**Consequences**:
- Test suite fails after weighted metrics added
- CI pipeline blocks deployment
- Dashboard parsing breaks, losing monitoring
- Time wasted updating test expectations instead of adding features

**Prevention**:
- **Keep existing functions unchanged**, add new weighted versions
- Old: `metrics.recall`, New: `metrics.weighted_recall(weights)`
- Old: `generate_report()`, New: `generate_report(weighted=False)` (opt-in)
- Add deprecation warnings if old functions need changes
- Version report format: include format_version field

**Detection**:
- Run existing test suite before/after weighted metric implementation
- Check: Do unweighted metrics still match previous values?
- Integration test: Does CI parsing still work?

**Which phase should address it**: Phase 1 - Design API to preserve backwards compatibility

**Reference**: Project already has some good patterns - `weighted=False` parameter in `generate_report()` (line 439)

---

### Pitfall 6: Weight Validation - Invalid Weight Values Accepted

**What goes wrong**: Invalid weights (negative, NaN, Inf, out-of-range) silently accepted, causing nonsensical results or crashes.

**Why it happens**:
- Pydantic validation checks type (`int`) but not value range
- No validation that weights are non-negative
- No check that weight scale makes sense (0-5 expected, but 0-100 provided)
- Float operations can produce NaN if division by zero occurs

**Consequences**:
- Negative weights flip interpretation (high TP reduces recall)
- NaN weights propagate through calculations, producing NaN metrics
- Weights on wrong scale (0-100 instead of 0-5) make comparison meaningless
- Silent failures that surface in production

**Prevention**:
- **Add Pydantic validators**:
  ```python
  @field_validator('spoken_handoff_weights')
  def validate_weights(cls, v):
      for entity, weight in v.items():
          assert 0 <= weight <= 5, f"{entity} weight {weight} out of range [0-5]"
      return v
  ```
- Add range checks in weighted calculation functions
- Validate that denominator > 0 before division
- Test edge cases: all zeros, all max, mixed, negative

**Detection**:
- Test: Try to load config with invalid weights, verify error
- Runtime check: Log warning if weighted_total == 0
- Unit test: Pass invalid weights to functions, verify graceful handling

**Which phase should address it**: Phase 1 - Add validation before any weighted calculations

**Reference**: Existing test `test_weight_values_in_valid_range()` (line 222) validates range, but only for already-loaded weights - need Pydantic validation at load time

---

### Pitfall 7: Per-Entity Stats Not Tracked (Can't Calculate Weighted Metrics)

**What goes wrong**: Weighted metrics require per-entity TP/FN/FP counts, but evaluation only tracks global totals. Weighted calculations impossible.

**Why it happens**:
- Original design: aggregate metrics (total TP, total FN, total FP)
- Weighted metrics need: per-entity breakdown for weighting
- Adding `entity_stats` dict requires refactoring evaluation loop
- Easy to forget to populate `entity_stats` in evaluation

**Consequences**:
- Weighted metric functions exist but always return 0.0 (no data)
- Must refactor entire evaluation pipeline to add tracking
- Can't retrospectively analyze past results (no per-entity data)

**Prevention**:
- **Track per-entity stats from day one**, even before weights added
- Structure: `entity_stats: dict[str, dict[str, int]]` with keys "tp", "fn", "fp"
- Populate in evaluation loop, not post-processing
- Add test: Verify entity_stats sum equals total metrics

**Detection**:
- Test: Call weighted_recall() on empty entity_stats, verify returns 0.0
- Test: Populate entity_stats, verify weighted != unweighted
- Code review: Check evaluation loop populates entity_stats

**Which phase should address it**: Already addressed in existing code (lines 399-413 of evaluate_presidio.py), but critical to verify for other evaluation paths

---

### Pitfall 8: Confusion Between Micro, Macro, and Weighted Averaging

**What goes wrong**: Weighted averaging confused with macro or micro averaging from sklearn. Different aggregation methods produce different results, causing misinterpretation.

**Why it happens**:
- Three distinct aggregation approaches in ML evaluation:
  - **Micro**: Global TP/FN/FP (current unweighted approach)
  - **Macro**: Average per-entity metrics (unweighted mean)
  - **Weighted**: Average per-entity metrics weighted by support or custom weights
- sklearn's `average='weighted'` weights by support (TP+FN), not custom weights
- Custom weighting (by frequency/risk) is non-standard
- Terminology overloaded: "weighted" means different things

**Consequences**:
- Stakeholder expects sklearn-style weighted (support-based)
- System implements custom weighted (frequency-based)
- Results don't match expectations or other tools
- Can't compare to benchmarks using standard weighted metrics

**Prevention**:
- **Use explicit terminology**: "frequency-weighted", "risk-weighted", not just "weighted"
- Document difference from sklearn's `average='weighted'`
- Consider adding standard macro/micro metrics for comparison
- In reports: Label metrics clearly ("Frequency-weighted recall", not "Weighted recall")

**Detection**:
- Compare custom weighted to sklearn `classification_report(average='weighted')`
- If they match, you're doing support-weighting not custom-weighting
- Test: Create scenario where support-weighted != frequency-weighted

**Which phase should address it**: Phase 1 - Use unambiguous naming from the start

**Reference**: [sklearn weighted average](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html) uses support, not custom weights

---

## Medium-Risk Pitfalls

### Pitfall 9: Over-Optimization on Weighted Metrics Hurts Unweighted Safety Floor

**What goes wrong**: Tuning detection thresholds to maximize weighted recall improves high-weight entities but degrades low-weight entities. Overall safety (unweighted recall) decreases.

**Why it happens**:
- Weighted objective function doesn't penalize low-weight entity failures
- Optimizer finds local maximum: boost PERSON recall, let EMAIL drop
- Zero-weight entities can drop to 0% recall without affecting weighted metric
- Single-objective optimization ignores multi-objective tradeoffs

**Consequences**:
- EMAIL_ADDRESS recall drops from 100% to 50% (leaking PHI)
- Weighted recall improves, but system is HIPAA-unsafe
- Real PHI leaks in production from ignored entity types

**Prevention**:
- **Add hard constraint: unweighted recall >= 100%** (safety floor)
- Use multi-objective optimization: maximize weighted subject to unweighted >= threshold
- Report both metrics, make safety floor visible in tuning
- Test: Verify threshold tuning doesn't degrade any entity below minimum

**Detection**:
- Monitor both weighted and unweighted recall over time
- Alert if unweighted recall decreases even if weighted increases
- Test: Optimize on weighted, verify unweighted didn't drop

**Which phase should address it**: Phase 2 (threshold tuning) - Add constraints before optimization

---

### Pitfall 10: Weight Scheme Changes Break Historical Comparisons

**What goes wrong**: Updating weight values (e.g., ROOM: 4→3) makes new results incomparable to old results. Historical trend analysis breaks.

**Why it happens**:
- Weights are subjective and may need adjustment based on real-world usage
- No versioning of weight schemes
- Old results don't store which weights were used
- Trend dashboards assume same weights over time

**Consequences**:
- Can't tell if recall improved or weights changed
- A/B tests invalid (different weight schemes)
- Historical regression analysis meaningless

**Prevention**:
- **Version weight schemes**: Add `weight_scheme_version: str` to config
- Store weight scheme version with evaluation results
- When comparing results, verify same weight scheme or recompute
- Changelog: Document when/why weights changed

**Detection**:
- Sudden jump/drop in weighted metrics with no code change = weight change
- Check: Do old result files store weight values?

**Which phase should address it**: Phase 1 - Add versioning before any weight changes occur

---

### Pitfall 11: Test Expectations Hardcoded to Specific Values

**What goes wrong**: Tests check `assert weighted_recall == 0.915` with exact values. Small changes (new data, weight adjustments) break tests even though behavior is correct.

**Why it happens**:
- Easy to write: run code, copy output value into test
- Feels rigorous: exact value matching
- Doesn't account for: floating-point precision, data changes, weight updates

**Consequences**:
- Every weight change requires updating dozens of test expectations
- Fragile tests that fail for wrong reasons
- Developers start ignoring test failures ("just update the number")

**Prevention**:
- **Use tolerance-based assertions**: `assert abs(weighted_recall - 0.915) < 0.01`
- Test properties, not exact values: `assert weighted_recall > unweighted_recall`
- Test invariants: `assert 0.0 <= weighted_recall <= 1.0`
- Only use exact values for synthetic data with known-correct answers

**Detection**:
- Count: How many tests have `==` for float metrics?
- Try: Change a weight by 0.1, do tests break?

**Which phase should address it**: Phase 1 - Write flexible tests from the start

**Reference**: Existing test (line 54) uses `assert abs(weighted_recall - 0.915) < 0.01` - good pattern! But should be applied consistently.

---

### Pitfall 12: Bootstrap CI Calculation Incompatible with Weighted Metrics

**What goes wrong**: Existing bootstrap confidence interval code works on binary arrays (TP/FN), but weighted metrics need per-entity data. CI calculation undefined for weighted metrics.

**Why it happens**:
- Bootstrap CI (lines 136-204) samples from flat TP/FN/FP arrays
- Weighted metrics aggregate across entities with different weights
- Sampling flattened data doesn't preserve per-entity structure
- No clear definition of "confidence interval for weighted recall"

**Consequences**:
- Can't report CI for weighted metrics (uncertainty unknown)
- Users compare weighted point estimate to unweighted CI (apples/oranges)
- Weighted metrics appear more certain than they are

**Prevention**:
- **Option 1**: Bootstrap at handoff level (resample entire handoffs, recalculate weighted metrics)
- **Option 2**: Don't compute CI for weighted metrics, only unweighted safety floor
- **Option 3**: Use stratified bootstrap (preserve entity proportions)
- Document which metrics have CIs and why

**Detection**:
- Try: Call `bootstrap_recall_ci()` with weighted metric, does it make sense?
- Test: Verify bootstrap of weighted metric converges with increasing n_bootstrap

**Which phase should address it**: Phase 2 (after basic weighted metrics work) - Add CI support for weighted if needed

---

### Pitfall 13: Report Format Changes Break Parsing

**What goes wrong**: Adding weighted metrics to report changes line numbers, section headers, or metric order. Downstream parsers (CI scripts, dashboards) break.

**Why it happens**:
- Report format defined implicitly (list of strings)
- Parsers use line numbers or regex to extract metrics
- Adding 3 new lines shifts everything
- No schema or contract for report format

**Consequences**:
- CI script can't find recall metric (looks at wrong line)
- Dashboard shows wrong values (parsed wrong section)
- Have to update multiple consumers, high coordination cost

**Prevention**:
- **Use structured output (JSON) for parsing**, human text for reading
- Separate `generate_report_json()` from `generate_report_text()`
- Version text format if needed for parsing
- Add `--json` flag (already exists, line 593!) - good pattern
- Keep text format flexible, don't parse it programmatically

**Detection**:
- Check: What consumes the report output? (CI, dashboard, human)
- Test: Parse report with mock parser, verify it extracts correct values
- Integration test: Run with weighted=True, verify CI still works

**Which phase should address it**: Already addressed with `--json` flag, but verify CI uses JSON not text parsing

---

### Pitfall 14: Weighted Metrics Hide Class Imbalance Issues

**What goes wrong**: Large weight on rare entity (MRN: weight=5, only 10 samples) causes high variance. Small data fluctuations swing weighted metric dramatically.

**Why it happens**:
- Weighted metrics amplify influence of high-weight entities
- Small sample sizes have high variance
- One MRN detection failure (-1 TP) = five PERSON failures in weighted calculation
- Weighted metric becomes noisy, hard to interpret

**Consequences**:
- Weighted recall jumps from 85% to 92% with one fix (MRN detection)
- Can't tell if system improved or got lucky
- Optimization unstable (chasing noise)

**Prevention**:
- **Report sample sizes** alongside weighted metrics
- Weight by importance AND reliability: `effective_weight = weight * sqrt(sample_size)`
- Use confidence intervals to show uncertainty
- Consider: Cap maximum weight ratio (no entity >3x another)

**Detection**:
- Check: What's the sample size for highest-weighted entities?
- Test: Flip one MRN detection, how much does weighted metric change?
- Monitor: Is weighted metric more volatile than unweighted over time?

**Which phase should address it**: Phase 2 (after observing metric behavior) - Add sample size reporting

---

### Pitfall 15: Config Caching (@lru_cache) Prevents Weight Updates

**What goes wrong**: Settings loaded once with `@lru_cache` on `get_settings()` (line 400). Changing weights in config doesn't take effect until restart.

**Why it happens**:
- `@lru_cache` decorator caches first `Settings()` instance
- Subsequent calls return cached instance (for performance)
- Config changes require cache clear or restart
- Easy to forget during development/testing

**Consequences**:
- Update weight in config, re-run evaluation, results unchanged
- Confusion: "Why didn't my weight change work?"
- Tests that modify settings affect other tests (global state)
- Production: Need restart to apply weight updates (not hot-reloadable)

**Prevention**:
- **Document**: "Changing weights requires restart due to @lru_cache"
- Add: `clear_settings_cache()` function for testing
- Consider: Remove `@lru_cache` if hot-reload needed (test performance impact)
- Alternative: Pass weights as parameters, don't cache in config

**Detection**:
- Test: Modify weight, reload module, verify change takes effect
- Warning in docs: "Config is cached, changes need restart"

**Which phase should address it**: Phase 1 - Document behavior, add cache clear for tests

**Reference**: Existing project has this pattern (line 400), documented as "prior pitfall" in project context

---

## Low-Risk Pitfalls

### Pitfall 16: Unclear Documentation - Which Metric Should I Use?

**What goes wrong**: Users see three metrics (unweighted, frequency-weighted, risk-weighted) and don't know which one to use for their decision. Each person picks different metric, can't align.

**Why it happens**:
- Multiple metrics presented without clear guidance
- Context-dependent: different metrics for different questions
- No decision tree: "Use X when deciding Y"

**Consequences**:
- Meetings waste time debating which metric is "right"
- Different stakeholders optimize for different metrics (misalignment)
- Incorrect metric used for high-stakes decision (threshold tuning)

**Prevention**:
- **Add decision guide to docs**:
  - Safety compliance (HIPAA): Use unweighted recall (must be 100%)
  - Handoff improvement: Use frequency-weighted (what's actually spoken)
  - Leak severity assessment: Use risk-weighted (how bad if leaked)
- In report: Label each metric with use case
- Default to safety floor in production alerts

**Detection**:
- Ask stakeholders: Which metric do you use? Why?
- Check: Is there a decision guide in the docs?

**Which phase should address it**: Phase 1 - Document alongside metric implementation

---

### Pitfall 17: Weight Schemes Not Validated Against Domain Expert Feedback

**What goes wrong**: Weights assigned based on intuition ("MRN seems important"), but domain experts (pediatric residents) disagree. Weights don't reflect actual handoff practice.

**Why it happens**:
- Initial weights from analyst's best guess
- No formal elicitation process with clinicians
- Weights never reviewed after initial implementation
- Assumption that analyst knows handoff better than practitioners

**Consequences**:
- ROOM weighted too high (actually varies by unit culture)
- DATE_TIME weighted too low (illness onset critical for triage)
- Weighted metrics don't align with clinical priorities

**Prevention**:
- **Survey domain experts**: "How often do you say [entity] in handoffs?" (1-5 scale)
- Use expert consensus, not single person's opinion
- Document rationale for each weight assignment
- Review weights quarterly with clinical users

**Detection**:
- Present weights to clinician, ask "Does this match your experience?"
- Compare to recorded handoff transcripts (if available)

**Which phase should address it**: Phase 3 (after initial implementation, before optimization)

---

## Sources

### NER Evaluation Challenges
- [nervaluate - Entity-level NER evaluation](https://github.com/MantisAI/nervaluate)
- [Skeptric - How not to Evaluate NER Systems](https://skeptric.com/ner-evaluate/)
- [David's Batista - Named-Entity Evaluation Metrics](https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/)
- [ScienceDirect - Statistical dataset evaluation for NER](https://www.cambridge.org/core/journals/natural-language-processing/article/statistical-dataset-evaluation-a-case-study-on-named-entity-recognition/BF7FA3EF95004830F233CF5D743D98B2)

### Weighted Metrics and Zero Division
- [scikit-learn precision_score documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_score.html)
- [scikit-learn f1_score documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html)
- [scikit-learn precision_recall_fscore_support](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html)
- [Number Analytics - F1 Score for Imbalanced Classes](https://www.numberanalytics.com/blog/f1-score-imbalanced-classes-guide)

### Implementation Integration Pitfalls
- [Deepchecks - Evaluating Agentic Workflows](https://www.deepchecks.com/agentic-workflow-evaluation-key-metrics-methods/)
- [MIT Press - Classification Evaluation Metrics](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00675/122720/A-Closer-Look-at-Classification-Evaluation-Metrics)
- [Savio - Weighted Scoring Model Guide](https://www.savio.io/product-roadmap/weighted-scoring-model/)
- [R-bloggers - Weighting Confusion Matrices](https://www.r-bloggers.com/2020/12/weighting-confusion-matrices-by-outcomes-and-observations/)

### Backward Compatibility
- [TutorialsPoint - Backward Compatibility Testing](https://www.tutorialspoint.com/software_testing_dictionary/backward_compatibility_testing.htm)
- [Medium - API Versioning and Backward Compatibility](https://medium.com/qualitynexus/api-versioning-and-backward-compatibility-complete-testing-guide-for-quality-engineers-669d46d204d7)

---

## Phase-Specific Risk Summary

| Phase | Critical Pitfalls | High-Risk Pitfalls | Mitigation Priority |
|-------|-------------------|---------------------|---------------------|
| **Phase 1: Implementation** | #1 (Zero-weight safety), #2 (Weight confusion), #3 (Int/float), #4 (Missing entities) | #5 (Backwards compat), #6 (Weight validation), #8 (Terminology) | HIGH - Must solve before production |
| **Phase 2: Threshold Tuning** | #9 (Over-optimization hurts safety floor) | #12 (Bootstrap CI), #14 (Class imbalance) | MEDIUM - Affects optimization quality |
| **Phase 3: Production Deploy** | #15 (Config caching) | #10 (Weight versioning), #13 (Report parsing) | MEDIUM - Operational concerns |
| **Phase 4: Maintenance** | None | #17 (Domain expert validation) | LOW - Continuous improvement |

**Highest Priority**: Pitfalls #1, #2, #4 must be addressed in Phase 1 to prevent PHI leaks from zero-weight entities and weight scheme confusion.
