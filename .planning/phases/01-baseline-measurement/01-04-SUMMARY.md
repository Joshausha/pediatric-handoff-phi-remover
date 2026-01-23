---
phase: 01-baseline-measurement
plan: 04
subsystem: testing
tags: [ci-cd, thresholds, validation, github-actions]
requires:
  - 01-01  # Metrics output from evaluation script
provides:
  - Threshold validation script (check_thresholds.py)
  - CI/CD integration strategy document
  - Manual pre-commit validation workflow
affects:
  - Phase 2+ (threshold refinement will use this script)
  - v2 implementation (GitHub Actions workflow)
tech-stack:
  added: []
  patterns:
    - Threshold validation with configurable limits
    - Exit code signaling for CI integration
    - JSON metrics consumption from stdin/file
decisions:
  - id: threshold-defaults
    what: Set default thresholds (recall 95%, precision 70%, F2 90%)
    why: Balance HIPAA compliance (high recall) with clinical utility (reasonable precision)
    alternatives: [Stricter 98/75/95, Relaxed 90/65/85]
  - id: ci-cd-v2
    what: Defer GitHub Actions workflow to v2 implementation
    why: Manual validation sufficient for Phase 1 research focus
    alternatives: [Implement immediately, Skip CI entirely]
  - id: separate-ci-jobs
    what: Run PHI validation as separate job from unit tests
    why: Enables parallel execution and independent failure analysis
    alternatives: [Combined job, Sequential dependency]
metrics:
  duration: 178 seconds
  completed: 2026-01-23
---

# Phase 1 Plan 04: Threshold Validation & CI/CD Strategy Summary

**One-liner:** Threshold check script (recall ≥95%, precision ≥70%) with GitHub Actions integration strategy for v2

---

## What Was Built

### Core Deliverables

1. **Threshold Check Script** (`tests/check_thresholds.py`)
   - Validates PHI metrics against configurable safety thresholds
   - Supports both stdin (piped) and file input
   - Exit 0 on pass, exit 1 on fail (CI-ready)
   - Configurable thresholds via CLI args

2. **CI/CD Integration Strategy** (`.planning/phases/01-baseline-measurement/CICD_STRATEGY.md`)
   - GitHub Actions workflow YAML for automated validation
   - Threshold configuration rationale and override procedures
   - Integration approach with existing pytest workflow
   - Metrics artifact storage and historical tracking plan
   - Security considerations (no PHI in CI logs)

### Key Features

**Threshold Script:**
- Default thresholds: recall ≥95%, precision ≥70%, F2 ≥90%
- Clear failure messages with PHI leak risk quantification
- Quiet mode for scripting (`-q` flag)
- Help documentation with usage examples

**CI/CD Strategy:**
- File pattern triggers (only run on PHI-related changes)
- PR comment automation on threshold failures
- 90-day metrics artifact retention
- Manual workflow dispatch with custom thresholds
- Future v3 metrics dashboard and regression detection

---

## Decisions Made

### 1. Threshold Defaults (recall 95%, precision 70%, F2 90%)

**Why these values?**
- **Recall 95%:** HIPAA compliance requires catching >95% of PHI (minimizes leak risk to <5%)
- **Precision 70%:** Clinical utility requires readable transcripts (balance redaction with usability)
- **F2 90%:** Recall-weighted metric prioritizes safety over false positives

**Trade-offs:**
- Stricter thresholds (98/75/95) reduce risk but harder to maintain
- Relaxed thresholds (90/65/85) easier to pass but higher PHI leak risk

**Override mechanism:** CLI args allow per-run customization for experimental work

### 2. CI/CD as v2 Implementation

**Current state:** Manual validation using `check_thresholds.py`
**Future state:** Automated GitHub Actions workflow

**Rationale:**
- Phase 1 focus is baseline measurement, not deployment automation
- Manual pre-commit checks sufficient for research iteration
- v2 implementation (post-Phase 5) adds automation for production readiness

**No blocker:** Script design is CI-ready (exit codes, JSON input, configurable thresholds)

### 3. Separate CI Jobs for PHI vs Unit Tests

**Workflow design:**
```yaml
jobs:
  unit-tests:      # Fast pytest (existing)
  phi-detection:   # Integration test (new)
```

**Benefits:**
- Parallel execution (saves CI time)
- Independent failure analysis (PHI regression vs code bug)
- Clear separation of concerns (unit vs integration testing)

**Trade-off:** Slightly more complex workflow file vs clearer failure diagnosis

---

## Technical Implementation

### Threshold Check Script

**Input formats:**
```bash
# Piped from evaluation
python tests/evaluate_presidio.py --json | python tests/check_thresholds.py

# From file
python tests/check_thresholds.py metrics.json

# Custom thresholds
python tests/check_thresholds.py --recall-min 0.90 --precision-min 0.65 metrics.json
```

**Output (passing):**
```
============================================================
PHI DETECTION THRESHOLD CHECK: PASSED
============================================================
  Recall:    99.0% >= 95%
  Precision: 80.0% >= 70%
  F2 Score:  95.0% >= 90%
============================================================
```

**Output (failing):**
```
============================================================
PHI DETECTION THRESHOLD CHECK: FAILED
============================================================
  RECALL: 70.0% < 95% threshold (PHI LEAK RISK: 30.0% of PHI may be missed)
  F2 SCORE: 75.0% < 90% threshold (OVERALL: recall-weighted performance below target)

Action required: Improve PHI detection before deployment.
============================================================
```

### GitHub Actions Workflow (v2)

**Key components:**
1. **Trigger on file patterns:** Only run when PHI code changes
2. **Install dependencies:** Python 3.11, spacy model download
3. **Generate metrics:** `evaluate_presidio.py --json`
4. **Validate thresholds:** `check_thresholds.py metrics.json`
5. **Upload artifacts:** 90-day retention for historical comparison
6. **PR comments:** Automated failure notifications

**Security:**
- No PHI in logs (synthetic test data only)
- Threshold changes require PR review (CODEOWNERS)
- Override justification required in PR description

---

## Testing & Validation

### Threshold Script Verification

**Passing metrics (exit 0):**
```bash
echo '{"recall": 0.99, "precision": 0.80, "f2": 0.95}' | python3 tests/check_thresholds.py
# ✅ PASSED
```

**Failing metrics (exit 1):**
```bash
echo '{"recall": 0.70, "precision": 0.80, "f2": 0.75}' | python3 tests/check_thresholds.py
# ❌ FAILED (recall too low)
```

**Help documentation:**
```bash
python3 tests/check_thresholds.py --help
# Shows usage, arguments, exit codes
```

### CI/CD Strategy Document

**Content checklist:**
- ✅ GitHub Actions workflow YAML (163 lines)
- ✅ Threshold configuration table
- ✅ Integration with existing CI approach
- ✅ Metrics tracking and artifact storage plan
- ✅ Security considerations (no PHI exposure)
- ✅ Manual validation commands
- ✅ Failure handling procedures
- ✅ Implementation timeline (Phase 1 done, Phase 2 v2, Phase 3 v3)

---

## Integration Points

### Consumes From

1. **Plan 01-01** (Evaluation Script)
   - JSON output format with `metrics` object
   - Keys: `recall`, `precision`, `f2`

### Provides To

1. **Phase 2+** (Threshold Refinement)
   - Validation tool for testing threshold adjustments
   - Manual pre-commit check workflow

2. **v2 Implementation** (CI/CD Automation)
   - Complete GitHub Actions workflow template
   - Threshold override procedures documented
   - Security considerations addressed

### File Links

```
tests/check_thresholds.py
  ├── Consumes: JSON from tests/evaluate_presidio.py --json
  ├── Validates: recall, precision, f2 against thresholds
  └── Outputs: Exit 0 (pass) or 1 (fail) with detailed messages

.planning/phases/01-baseline-measurement/CICD_STRATEGY.md
  ├── References: tests/check_thresholds.py
  ├── Defines: GitHub Actions workflow
  └── Documents: v2 implementation plan
```

---

## Deviations from Plan

**None** — Plan executed exactly as written.

All must-haves delivered:
- ✅ Threshold check script exists and is executable
- ✅ Script exits 1 if recall < 95% or precision < 70%
- ✅ CI/CD strategy document outlines GitHub Actions workflow
- ✅ Strategy marked as v2 implementation (not blocking Phase 1)

---

## Next Phase Readiness

### Blockers

**None.** Phase 1 can continue with:
- Plan 05: Comprehensive Research Summary (synthesis of all baseline work)

### Manual Validation Workflow Ready

**Pre-commit checks:**
```bash
# Quick validation
python tests/evaluate_presidio.py --json | python tests/check_thresholds.py

# Save metrics for analysis
python tests/evaluate_presidio.py --json > metrics.json
python tests/check_thresholds.py metrics.json
```

**Phase 2+ will use this script to:**
- Validate threshold refinement experiments
- Test impact of deny list changes
- Measure improvement from pattern enhancements

### v2 Implementation Prerequisites

**Before implementing GitHub Actions workflow:**
1. Complete Phase 1-5 (all baseline measurements)
2. Establish production deployment pipeline
3. Review threshold defaults based on real-world validation (Phase 5)

**v2 implementation is straightforward:**
- Copy YAML from CICD_STRATEGY.md to `.github/workflows/phi-detection.yml`
- Test with sample PR
- Configure CODEOWNERS for threshold change reviews

---

## Key Files Modified

### Created

| File | Purpose | Lines |
|------|---------|-------|
| `tests/check_thresholds.py` | Threshold validation script | 162 |
| `.planning/phases/01-baseline-measurement/CICD_STRATEGY.md` | CI/CD integration strategy | 373 |

### Modified

None (all new files)

---

## Metrics

**Execution Time:** 178 seconds (~3 minutes)

**Commits:**
1. `13b521b` - feat(01-04): add threshold check script for PHI metrics
2. `5d08538` - docs(01-04): create CI/CD integration strategy

**Task Breakdown:**
- Task 1 (Script): ~90 seconds (implementation + testing)
- Task 2 (Strategy): ~88 seconds (documentation)

---

## Lessons Learned

### What Went Well

1. **Clear requirements:** Plan specified exact script behavior (exit codes, thresholds, input formats)
2. **CI-ready design:** Script works with both stdin and file input (flexible for CI/manual use)
3. **Comprehensive strategy:** CICD_STRATEGY.md covers implementation, security, and future enhancements

### What Could Be Improved

**Initial script bug:** Python 3.9 incompatibility with `%` formatting in argparse help strings
- **Fix:** Changed `.0%` (percentage) to `.0f` (float) in help text
- **Lesson:** Test with target Python version (system default vs project version)

### Future Considerations

**v3 Metrics Dashboard:**
- Store metrics as time series (CSV/JSON in repo)
- Generate trend charts (recall/precision over time)
- Alert on regression (e.g., recall drops >2% in single PR)

**Threshold Refinement (Phase 2):**
- Use this script to validate threshold adjustments
- Document rationale for any changes to defaults
- Consider entity-specific thresholds (e.g., PERSON vs ROOM)

---

## References

**Related Plans:**
- 01-01: Evaluation script (provides JSON metrics input)
- 01-05: Comprehensive research summary (will reference this strategy)

**Related Files:**
- `tests/evaluate_presidio.py` - Generates metrics consumed by threshold script
- `tests/synthetic_handoffs.json` - Test data for PHI detection evaluation

**External Resources:**
- GitHub Actions documentation: https://docs.github.com/en/actions
- pytest-github-actions-annotate-failures: https://github.com/utgwkk/pytest-github-actions-annotate-failures
