# Phase 6: Real Handoff Testing - Research

**Researched:** 2026-01-25
**Domain:** Real-world clinical validation and user acceptance testing
**Confidence:** HIGH

## Summary

Phase 6 validates the PHI detection system on actual clinical handoff content by having the user (a pediatric resident) read real text handoffs aloud and reviewing the de-identified output. This differs from Phase 5's synthetic data validation and represents true user acceptance testing (UAT) in the clinical context.

The research identified established UAT methodologies from clinical software validation (2-week cycles with focused risk-based testing), error analysis frameworks from laboratory validation (false positive/negative documentation templates), and real-world validation best practices from medical speech recognition systems (minimum 15 hours of diverse recordings, continuous performance monitoring).

Key findings indicate that Phase 6 serves multiple purposes: (1) external validation on real data (VALD-01), (2) error pattern identification (VALD-02), (3) confirmation of expert review findings on actual content, and (4) usability assessment of the complete workflow. The phase should produce structured documentation of false negatives and false positives encountered, with qualitative analysis of patterns missed.

**Primary recommendation:** Implement a lightweight testing protocol where user reads 10-15 real text handoffs (varied patient populations and clinical scenarios), documents each PHI leak or over-redaction immediately in a structured template, performs qualitative error analysis to identify patterns, and updates configuration or deny lists as needed before declaring production readiness.

## Standard Stack

### Core Testing Infrastructure (Already Exists)
| Component | Version | Purpose | Status |
|-----------|---------|---------|--------|
| FastAPI app | Latest | HTTP server with /process endpoint | Complete |
| Frontend (HTML/CSS/JS) | - | Recording + upload + results display | Complete |
| faster-whisper | medium.en | Audio transcription (local only) | Complete |
| Presidio | Latest | PHI detection with custom recognizers | Complete |

### Testing Support Tools (Needed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None required | - | Manual testing via web UI | Phase 6 is hands-on validation |
| Markdown/JSON | - | Error documentation template | Structured findings capture |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual reading | Pre-recorded handoffs | Manual reading tests full audio→text→PHI pipeline as user will use it |
| Structured template | Ad-hoc notes | Template ensures complete error taxonomy capture per APHL standards |
| 10-15 handoffs | 50+ handoffs | Diminishing returns after pattern saturation; 10-15 balances thoroughness with time |

**Installation:**
```bash
# No new dependencies - use existing application
uvicorn app.main:app --reload
# Open http://localhost:8000 in browser
```

## Architecture Patterns

### Recommended Test Session Structure
```
.planning/phases/06-real-handoff-testing/
├── REAL_HANDOFF_VALIDATION.md       # Main findings document
├── error_log.json                    # Structured error capture
├── handoff_metadata.json             # Session, patient demographics (de-identified)
└── patterns_identified.md            # Qualitative error analysis
```

### Pattern 1: User Acceptance Testing Protocol (Clinical Software)
**What:** Focused, risk-based validation by actual end-user in real-world scenario
**When to use:** After automated validation shows acceptable baseline performance
**Key insight from research:** UAT is not complete revalidation but focused determination of whether system meets protocol requirements and key user expectations

**Best Practice Protocol (adapted from ISPOR ePRO Systems Validation Task Force):**
1. **Test Plan (2-hour session):**
   - User identifies 10-15 real text handoffs from recent clinical work
   - Handoffs should cover diverse scenarios: newborn, PICU, floor patients, ED admissions
   - Each handoff read aloud into recording interface
   - User immediately reviews de-identified output for PHI leaks and clinical utility

2. **Error Documentation (per handoff):**
   - False negatives: PHI visible in output (document entity type, text, severity)
   - False positives: Over-redacted clinical content (document loss, impact)
   - Usability issues: Workflow friction, UI confusion, unclear errors

3. **Acceptance Criteria:**
   - Zero high-severity PHI leaks (patient names, MRNs spoken in handoffs)
   - Clinical utility preserved (timeline, ages, clinical context readable)
   - User confidence in system for personal use

**Example workflow:**
```bash
# For each handoff:
1. Open web app → Start recording → Read handoff text → Stop
2. Review de-identified output side-by-side with original text
3. Document findings in REAL_HANDOFF_VALIDATION.md
4. If patterns emerge, update config and re-test subset
```

### Pattern 2: Error Analysis Template (APHL Validation Standards)
**What:** Structured documentation matching laboratory validation best practices
**When to use:** For each detected error during real-world testing
**Source:** [APHL Laboratory Test Verification and Validation Toolkit](https://www.aphl.org/aboutAPHL/publications/Documents/QSA-VV-Toolkit.pdf)

**Template per error:**
```markdown
### Error #[N]: [Brief description]

**Sample ID:** Handoff [N] ([patient context - de-identified])
**Error Type:** [ ] False Negative (PHI leaked) [ ] False Positive (over-redaction)
**Entity Type:** [PERSON | PHONE | DATE_TIME | ROOM | MRN | etc.]
**Severity:** [ ] Critical [ ] High [ ] Medium [ ] Low

**Original Text:** [snippet showing expected detection]
**System Output:** [actual detection result]
**Expected Behavior:** [what should have happened]

**Clinical Impact:**
- [ ] Patient identifiable from output
- [ ] Clinical decision-making impaired
- [ ] Minor inconvenience only

**Pattern Hypothesis:** [is this part of larger pattern?]
**Recommended Fix:** [deny list | pattern update | threshold adjustment]
```

### Pattern 3: Qualitative Error Pattern Analysis
**What:** After testing all handoffs, aggregate errors to identify systemic issues
**When to use:** End of testing session, before declaring production ready
**Research basis:** Validation in real-world settings reveals performance gaps not visible in synthetic data

**Analysis Framework:**
1. **Group errors by entity type** - Are misses concentrated in specific PHI types?
2. **Identify linguistic patterns** - Do errors share syntactic structure? (e.g., "contact mom at 555-1234")
3. **Check coverage gaps** - Are errors in deny lists, or are patterns missing entirely?
4. **Assess severity distribution** - How many are critical (patient identifiable) vs minor (over-redaction)?

**Output:** `patterns_identified.md` with:
- Pattern descriptions with example cases
- Root cause analysis (deny list gap vs NER limitation vs threshold issue)
- Recommended fixes with priority ranking
- Trade-off analysis (fixing X may worsen Y)

### Anti-Patterns to Avoid

**Anti-pattern 1: Testing with synthetic examples**
- Phase 6 goal is real-world validation - synthetic data was Phase 5
- Real clinical text has variations synthetic generators miss
- User must read actual handoffs from their clinical work

**Anti-pattern 2: Batch processing without immediate review**
- Record all handoffs first, then review later
- Why it's bad: Context loss, pattern detection delayed, inefficient debugging
- Instead: Record → Review → Document → Next handoff

**Anti-pattern 3: Ignoring over-redaction as "safe"**
- Phase 5 expert review found over-redaction unacceptable (clinical utility lost)
- False positives matter for user acceptance, not just safety
- Document both PHI leaks AND clinical content loss

**Anti-pattern 4: Testing without error taxonomy**
- Ad-hoc notes like "missed a phone number" lack structure
- Prevents pattern analysis and systematic improvement
- Use structured template matching APHL validation standards

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Speech recording interface | Custom audio capture | Existing FastAPI frontend (static/app.js) | MediaRecorder API already integrated, file upload working |
| Error tracking database | SQLite for error logs | JSON files + markdown template | Lightweight validation doesn't need DB overhead; 10-15 handoffs manageable in files |
| Statistical analysis | Custom recall/precision calculations | Manual counts with confidence intervals | Small sample (10-15) doesn't need automated stats; qualitative patterns more valuable |
| Automated pattern detection | NLP pipeline for error clustering | Manual qualitative analysis | Human pattern recognition superior for small samples; captures nuance automated systems miss |

**Key insight:** Phase 6 is hands-on validation, not infrastructure building. User should spend time testing real handoffs and analyzing patterns, not building tools.

## Common Pitfalls

### Pitfall 1: Insufficient Sample Diversity
**What goes wrong:** Testing only one patient type (e.g., all newborns) misses PHI patterns in other populations
**Why it happens:** User defaults to most common handoff type from recent shifts
**How to avoid:** Deliberately select diverse scenarios:
- Age ranges: newborn, infant, toddler, school-age, adolescent
- Units: ED, floor, PICU, NICU
- Complexity: simple admission vs multi-problem chronic patient
- Speech patterns: clear dictation vs natural conversational pace
**Warning signs:** All handoffs similar length/structure, no errors detected (suspiciously clean)

### Pitfall 2: Confirmation Bias in Error Detection
**What goes wrong:** User subconsciously overlooks PHI leaks because expert review said "approved for personal use"
**Why it happens:** Prior validation creates expectation system works correctly
**How to avoid:**
- Assume errors exist until proven otherwise
- Read de-identified output WITHOUT reference to original first
- Ask: "Could I identify patient from this output alone?"
- Have fresh perspective (e.g., co-resident review output blind)
**Warning signs:** Zero errors found, user declares success immediately, no documentation of suspicious patterns

### Pitfall 3: Over-redaction Tolerance Creep
**What goes wrong:** User accepts clinical utility loss because "at least PHI is gone"
**Why it happens:** PHI safety emphasized over usability in previous phases
**How to avoid:**
- Phase 5 established over-redaction is unacceptable (commit cfbd5b1)
- Test: Can user write clinical notes from de-identified output?
- Document every instance where clinical context is lost
- Clinical timeline must be preserved (ages, day-of-illness, etc.)
**Warning signs:** Statements like "I can live with [AGE] being redacted," "I'll just remember the numbers"

### Pitfall 4: Single-Session Testing Fatigue
**What goes wrong:** Recording 15 handoffs back-to-back leads to sloppy documentation
**Why it happens:** UAT timelines suggest 2-week cycles, but user rushes single session
**How to avoid:**
- Split into 2-3 sessions: initial 5 handoffs, pattern analysis, follow-up 5-10
- Take breaks between handoffs for documentation
- If patterns emerge early, pause to update config before continuing
- Quality over quantity - 10 well-documented handoffs > 20 rushed
**Warning signs:** Error documentation becomes terse, patterns noted but not analyzed, user fatigue visible in notes

### Pitfall 5: Real PHI in Planning Files
**What goes wrong:** User copies original handoff text into validation documents
**Why it happens:** Convenient for comparison, but violates HIPAA even in local files
**How to avoid:**
- NEVER copy real PHI into any planning or documentation files
- Reference handoffs by sample number only: "Handoff 03 (8mo bronchiolitis)"
- Documentation should describe patterns, not reproduce PHI
- If examples needed, use system de-identified output or generic pattern descriptions
**Warning signs:** Exact patient names in markdown files, specific MRNs documented, planning folder contains identifiable information

## Code Examples

### Example 1: Error Documentation Workflow
```markdown
# Source: This research document, Pattern 2
# Error captured during real handoff testing

### Error #1: Phone number with context word missed

**Sample ID:** Handoff 03 (infant with bronchiolitis)
**Error Type:** [x] False Negative (PHI leaked)
**Entity Type:** PHONE_NUMBER
**Severity:** [x] High - contact number visible

**Original Text:** "mom's cell is 555-867-5309"
**System Output:** "mom's cell is 555-867-5309" (unchanged)
**Expected Behavior:** "mom's cell is [PHONE]"

**Clinical Impact:**
- [x] Patient identifiable from output (contact tracing possible)
- [ ] Clinical decision-making impaired
- [ ] Minor inconvenience only

**Pattern Hypothesis:** Phone numbers preceded by possessive "mom's" not detected
**Recommended Fix:** Check PHONE_NUMBER recognizer context patterns
```

### Example 2: Testing Session Structure
```bash
# Source: UAT best practices from research
# 2-hour real handoff validation session

# Session 1 (Day 1, ~1 hour)
1. Test 5 diverse handoffs
2. Document errors immediately
3. Review patterns at end

# Analysis (Day 1, ~30 min)
1. Review error_log.json
2. Identify common patterns
3. Update deny lists or patterns if needed

# Session 2 (Day 2, ~1 hour)
1. Test updated system with 5-10 new handoffs
2. Verify fixes didn't introduce regressions
3. Final pattern analysis

# Decision
- If <2 high-severity errors in Session 2: Approve for production
- If >=2 high-severity errors: Additional pattern work needed
```

### Example 3: Real Handoff Metadata (De-identified)
```json
{
  "session_date": "2026-01-25",
  "tester": "Josh (PGY-3)",
  "total_handoffs": 12,
  "demographics": {
    "age_ranges": ["newborn", "infant", "toddler", "school-age"],
    "units": ["NICU", "PICU", "floor", "ED"],
    "complexity": ["simple_admission", "chronic_multi_problem", "acute_critical"]
  },
  "system_version": {
    "presidio_config": "2026-01-25 (post Phase 5 fixes)",
    "weighted_recall": 0.944,
    "deny_lists": ["DATE_TIME substring matching", "clinical timeline preservation"]
  },
  "results": {
    "total_errors": 3,
    "false_negatives": 1,
    "false_positives": 2,
    "high_severity": 1,
    "patterns_identified": 2
  }
}
```

## State of the Art

| Validation Approach | Current Best Practice | Phase 6 Implementation | Impact |
|---------------------|----------------------|----------------------|--------|
| Synthetic-only testing | Deprecated for production | Phase 5 used synthetic + expert review | Real-world validation required per 2026 standards |
| Large-scale automated UAT | Batch 1000+ records | 10-15 hands-on handoffs | Small samples sufficient for pattern detection in personal-use context |
| Statistical validation | 95% CI, sample size calculations | Qualitative error pattern analysis | Personal use + iterative improvement focus prioritizes patterns over statistics |
| Error-only documentation | Capture failures | Document successes AND failures | Confirms system works correctly on diverse scenarios, not just edge cases |

**Recent shifts (2025-2026):**
- Clinical software UAT emphasizes focused risk-based testing over exhaustive revalidation (ISPOR ePRO guidelines)
- Medical speech recognition shifted from clean audio benchmarks to real-world performance with "minimum 15 hours diverse recordings" standard (Deepgram 2026)
- PHI de-identification validation requires external validation beyond synthetic corpus with human quality review (Censinet 2025 benchmark)

## Open Questions

1. **Sample Size Sufficiency**
   - What we know: 10-15 handoffs recommended based on UAT literature (2-week cycles), APHL suggests 40 samples minimum for statistical validation
   - What's unclear: Is 10-15 sufficient for pattern saturation in pediatric handoffs, or should Phase 6 require 20+?
   - Recommendation: Start with 10, extend if new patterns still emerging past handoff #8-10; personal use context allows flexibility

2. **Regression Testing Scope**
   - What we know: If configuration changes made during testing, some prior cases should be re-tested
   - What's unclear: How many prior handoffs need re-testing after deny list updates?
   - Recommendation: Re-test 3-5 representative samples after each config change to ensure no regressions

3. **Multi-Session vs Single-Session**
   - What we know: UAT best practices suggest 2-week cycles; fatigue is real concern
   - What's unclear: Can Phase 6 be single 2-hour session or must be split across multiple days?
   - Recommendation: Plan for 2-3 sessions (initial test, analysis/fixes, validation) but allow flexibility based on error rates

4. **Success Threshold**
   - What we know: Phase 5 expert review approved system for personal use; VALD-04 targets >95% recall
   - What's unclear: What error rate in Phase 6 triggers additional work before production?
   - Recommendation: Zero high-severity PHI leaks in Session 2 (post-fixes); up to 2-3 low-severity over-redactions acceptable if user confirms clinical utility preserved

## Sources

### Primary (HIGH confidence)
- [User Acceptance Testing for Systems Designed to Collect Clinical Outcome Assessment Data Electronically - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8964567/) - ISPOR UAT best practices
- [APHL Laboratory Test Verification and Validation Toolkit - Qualitative Assays](https://www.aphl.org/aboutAPHL/publications/Documents/QSA-VV-Toolkit-Qualitative.pdf) - Error documentation templates, sample size guidance
- [Benchmark Medical Speech Recognition Accuracy for Clinical Use - Deepgram](https://deepgram.com/learn/benchmark-medical-speech-recognition-accuracy-production) - Real-world validation requirements (15+ hours diverse recordings)
- [2025 Benchmark: De-Identification Tools - Censinet](https://www.censinet.com/perspectives/2025-benchmark-de-identification-tools) - PHI validation with human quality review

### Secondary (MEDIUM confidence)
- [Best Practice Recommendations: User Acceptance Testing - PubMed](https://pubmed.ncbi.nlm.nih.gov/35233726/) - UAT 2-week cycle guidance, focused risk-based approach
- [Clinical De-Identification at Scale - John Snow Labs](https://www.johnsnowlabs.com/clinical-de-identification-at-scale-pipeline-design-and-speed-accuracy-trade-offs-across-infrastructures/) - Real dataset validation approach
- [Validation of Qualitative Research in the Real World - ResearchGate](https://www.researchgate.net/publication/9054078_Validation_of_Qualitative_Research_in_the_Real_World) - Qualitative validation methodology

### Tertiary (LOW confidence - general context)
- [False Positives in AI Detection: Complete Guide 2026 - Proofademic](https://proofademic.ai/blog/false-positives-ai-detection-guide/) - General false positive/negative analysis concepts
- [Speech Recognition Accuracy: Production Metrics & Optimization 2025 - Deepgram](https://deepgram.com/learn/speech-recognition-accuracy-production-metrics) - Production validation framework concepts

## Metadata

**Confidence breakdown:**
- UAT methodology: HIGH - Multiple authoritative sources (ISPOR, clinical software standards) with specific protocols
- Error analysis templates: HIGH - APHL laboratory validation toolkit provides standardized approach applicable to PHI detection
- Sample size recommendations: MEDIUM - Literature suggests 40+ for statistics but 10-15 for pattern-based qualitative analysis; context-dependent
- Real-world validation necessity: HIGH - 2025-2026 de-identification standards explicitly require testing beyond synthetic data

**Research date:** 2026-01-25
**Valid until:** 60 days (validation methodologies are stable; UAT best practices mature)

**Phase 6 context:**
- Phase 5 achieved APPROVED FOR PERSONAL USE status (weighted recall 94.4%)
- DATE_TIME over-redaction fixed (commit cfbd5b1)
- No show-stopping issues in expert review beyond over-redaction (now resolved)
- Phase 6 confirms system works on real clinical content user will encounter

**Key differentiation from Phase 5:**
- Phase 5: Synthetic data → Automated metrics → Expert review of de-identified samples
- Phase 6: Real handoffs → User reads aloud → Full pipeline test → Error pattern documentation → Production readiness decision
