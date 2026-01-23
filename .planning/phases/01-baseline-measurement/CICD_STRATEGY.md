# CI/CD Integration Strategy for PHI Detection

**Status:** v2 Implementation (Not Blocking Phase 1)
**Document Date:** 2026-01-23
**Purpose:** Document GitHub Actions workflow for automated PHI detection threshold validation

---

## Overview

This strategy outlines how to integrate PHI detection metrics validation into the continuous integration pipeline using GitHub Actions. The goal is to prevent deployment of code that degrades PHI detection performance below safety thresholds.

**Implementation Timeline:**
- **Phase 1 (Current):** Manual validation using `check_thresholds.py` script
- **Phase 2 (v2):** Automated CI/CD integration with GitHub Actions

---

## Trigger Strategy

### When to Run PHI Detection Evaluation

**Primary Triggers:**
- Pull requests that modify PHI detection code
- Pushes to `main` branch
- Manual workflow dispatch (for on-demand validation)

**File Patterns to Watch:**
```yaml
paths:
  - 'app/deidentification.py'
  - 'app/recognizers/**'
  - 'app/config.py'
  - 'tests/synthetic_handoffs.json'
  - 'tests/evaluate_presidio.py'
  - 'tests/check_thresholds.py'
```

**Skip Triggers:**
- Documentation-only changes
- Frontend changes (HTML/CSS/JS in `static/`)
- CI/CD configuration changes (except PHI-related tests)

---

## GitHub Actions Workflow

### Workflow YAML Example

```yaml
name: PHI Detection Validation

on:
  pull_request:
    paths:
      - 'app/deidentification.py'
      - 'app/recognizers/**'
      - 'app/config.py'
      - 'tests/synthetic_handoffs.json'
      - 'tests/evaluate_presidio.py'
      - 'tests/check_thresholds.py'
  push:
    branches:
      - main
    paths:
      - 'app/deidentification.py'
      - 'app/recognizers/**'
      - 'app/config.py'
      - 'tests/synthetic_handoffs.json'
  workflow_dispatch:
    inputs:
      recall_min:
        description: 'Minimum recall threshold'
        required: false
        default: '0.95'
      precision_min:
        description: 'Minimum precision threshold'
        required: false
        default: '0.70'
      f2_min:
        description: 'Minimum F2 score threshold'
        required: false
        default: '0.90'

jobs:
  phi-detection-validation:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python -m spacy download en_core_web_lg

      - name: Run PHI detection evaluation
        run: |
          python tests/evaluate_presidio.py --json > metrics.json
          cat metrics.json

      - name: Check thresholds
        run: |
          python tests/check_thresholds.py \
            --recall-min ${{ github.event.inputs.recall_min || '0.95' }} \
            --precision-min ${{ github.event.inputs.precision_min || '0.70' }} \
            --f2-min ${{ github.event.inputs.f2_min || '0.90' }} \
            metrics.json

      - name: Upload metrics artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: phi-metrics-${{ github.sha }}
          path: metrics.json
          retention-days: 90

      - name: Comment PR with results
        if: github.event_name == 'pull_request' && failure()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const metrics = JSON.parse(fs.readFileSync('metrics.json', 'utf8'));
            const m = metrics.metrics;

            const comment = `## ⚠️ PHI Detection Threshold Check Failed

            **Metrics:**
            - Recall: ${(m.recall * 100).toFixed(1)}% (threshold: 95%)
            - Precision: ${(m.precision * 100).toFixed(1)}% (threshold: 70%)
            - F2 Score: ${(m.f2 * 100).toFixed(1)}% (threshold: 90%)

            **Action Required:** Improve PHI detection patterns before merging.

            See the [workflow run](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}) for details.`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

---

## Threshold Configuration

### Default Thresholds

| Metric | Default | Rationale | Override Scenario |
|--------|---------|-----------|-------------------|
| **Recall** | 95% | HIPAA compliance: catch >95% of PHI to minimize leak risk | Research projects with low-risk synthetic data may use 90% |
| **Precision** | 70% | Clinical utility: balance redaction with readability | High-security scenarios may accept 60% for more aggressive redaction |
| **F2 Score** | 90% | Recall-weighted: prioritize catching PHI over avoiding false positives | Experimental features may use 85% during development |

### How to Override Thresholds

**Manual workflow dispatch:**
1. Go to Actions tab → PHI Detection Validation workflow
2. Click "Run workflow"
3. Enter custom thresholds (e.g., `0.90` for 90%)

**In PR/push (requires workflow file edit):**
```yaml
- name: Check thresholds (relaxed for experiment)
  run: |
    python tests/check_thresholds.py \
      --recall-min 0.90 \
      --precision-min 0.65 \
      metrics.json
```

**⚠️ Warning:** Lowering thresholds increases PHI leak risk. Document justification in PR description.

---

## Integration with Existing CI

### Current CI Workflow

The project already has a `test.yml` workflow that runs pytest. The PHI detection validation should be added as a separate job to avoid coupling concerns:

```yaml
jobs:
  unit-tests:
    # Existing pytest job
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run pytest
        run: pytest tests/

  phi-detection-validation:
    # New job (runs in parallel)
    needs: []  # No dependency on unit-tests
    runs-on: ubuntu-latest
    steps:
      # ... (see workflow YAML above)
```

**Why separate jobs?**
- **Independence:** PHI metrics are integration tests; unit tests are faster
- **Parallelization:** Both jobs run simultaneously, saving CI time
- **Clarity:** Failed PHI detection doesn't obscure unit test failures

---

## Metrics Tracking Over Time

### Artifact Storage

GitHub Actions artifacts provide 90-day retention:
- Each run uploads `metrics.json` with SHA-tagged name
- Enables historical comparison: "Did this PR improve recall?"

### Future Enhancement: Metrics Dashboard

**v3 Feature (Post-Phase 5):**
- Store metrics in GitHub repo as CSV/JSON time series
- Generate trend charts (recall/precision over time)
- Alert on degradation (e.g., recall drops >2% in single PR)

**Example metrics CSV:**
```csv
date,commit,recall,precision,f2
2026-01-23,13b521b,0.993,0.813,0.945
2026-01-24,a1b2c3d,0.995,0.820,0.950
```

---

## Implementation Timeline

### Phase 1 (Current) - DONE ✅
- [x] Create `check_thresholds.py` script
- [x] Document CI/CD strategy
- [x] Manual validation workflow established

### Phase 2 (v2) - Planned
- [ ] Add GitHub Actions workflow file
- [ ] Test workflow with sample PR
- [ ] Configure PR comment automation
- [ ] Document override procedures

### Phase 3 (v3) - Future
- [ ] Implement metrics time series storage
- [ ] Build trend visualization dashboard
- [ ] Add regression detection alerts

---

## Security Considerations

### No PHI in CI Logs

**Critical:** The `synthetic_handoffs.json` test data contains NO real PHI. All test cases are synthetic.

**Safeguards:**
1. Never log full transcript text in CI
2. Only log aggregate metrics (recall, precision, F2)
3. Artifact uploads contain only JSON metrics, not raw transcripts

### Threshold Bypass Protection

**Prevent accidental threshold lowering:**
- Require PR review for any changes to `check_thresholds.py`
- CODEOWNERS file ensures PHI detection expert reviews threshold changes
- Document threshold overrides in PR description

**Example CODEOWNERS entry:**
```
tests/check_thresholds.py @your-username
app/recognizers/** @your-username
```

---

## Manual Validation Commands

While v2 implementation is pending, use these commands for manual pre-commit checks:

### Basic Validation
```bash
# Run evaluation and check thresholds
python tests/evaluate_presidio.py --json | python tests/check_thresholds.py

# Save metrics to file
python tests/evaluate_presidio.py --json > metrics.json
python tests/check_thresholds.py metrics.json
```

### Custom Thresholds
```bash
# Relaxed thresholds for experimental feature
python tests/check_thresholds.py \
  --recall-min 0.90 \
  --precision-min 0.65 \
  metrics.json

# Strict thresholds for production deployment
python tests/check_thresholds.py \
  --recall-min 0.98 \
  --precision-min 0.75 \
  metrics.json
```

### Quiet Mode (for scripts)
```bash
# Only show output if thresholds fail
python tests/check_thresholds.py --quiet metrics.json && echo "Ready to deploy"
```

---

## Failure Handling

### What to Do When Thresholds Fail

**Step 1: Identify the cause**
```bash
# Run verbose evaluation to see per-entity performance
python tests/evaluate_presidio.py --verbose
```

**Step 2: Check entity-level metrics**
- Low recall on `PERSON`? → Review deny lists (e.g., "mom", "dad")
- Low precision on `LOCATION`? → Add medical abbreviations to deny list (e.g., "NC", "RA")
- Low recall on `PEDIATRIC_AGE`? → Improve age pattern regex

**Step 3: Add test cases**
```python
# In tests/synthetic_handoffs.json, add failing examples
{
  "transcript": "The patient is a 3-week-old infant...",
  "phi": [
    {"text": "3-week-old", "entity_type": "PEDIATRIC_AGE", "start": 18, "end": 28}
  ]
}
```

**Step 4: Iterate and retest**
```bash
# After fixing patterns
python tests/evaluate_presidio.py --json | python tests/check_thresholds.py
```

**Step 5: Document the fix**
- Commit message: `fix(recognizers): improve PEDIATRIC_AGE recall for N-week-old pattern`
- PR description: "Addresses threshold failure by adding regex for week-based ages"

---

## Summary

This CI/CD strategy provides:
1. **Automated validation:** Prevent PHI detection regressions
2. **Flexible thresholds:** Override for experimental work
3. **Historical tracking:** Metrics artifacts for trend analysis
4. **Security:** No PHI exposure in CI logs
5. **Clear failure handling:** Actionable steps when thresholds fail

**Current Status:** Manual validation available (Phase 1 complete)
**Next Steps:** Implement GitHub Actions workflow (Phase 2 / v2)
**Future:** Metrics dashboard and regression alerts (Phase 3 / v3)
