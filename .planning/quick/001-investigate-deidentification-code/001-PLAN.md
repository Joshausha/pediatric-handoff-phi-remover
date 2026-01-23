---
phase: quick-001
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: true

must_haves:
  truths:
    - "Root cause identified for High being flagged as LOCATION"
    - "Root cause identified for Ronald McDonald House not being detected as PHI"
    - "Root cause identified for 35 weeker being flagged as AGE"
  artifacts:
    - path: ".planning/quick/001-investigate-deidentification-code/INVESTIGATION.md"
      provides: "Documented findings for all 3 test failures"
---

<objective>
Investigate three deidentification test failures to identify root causes.

Purpose: Understand WHY these failures occur before attempting fixes
Output: INVESTIGATION.md documenting root cause analysis for each failure
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@app/deidentification.py
@app/config.py
@app/recognizers/pediatric.py
@app/recognizers/medical.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Trace all three failure cases through the code</name>
  <files>None (investigation only)</files>
  <action>
  For each of the three failures, trace through the code to identify the exact mechanism causing the issue:

  **Failure 1: "high flow" becomes "[Location]flow"**
  - Input: "high flow" (as in "high flow nasal cannula")
  - Observed: "High" is being flagged as LOCATION entity
  - Investigate: Why is spaCy/Presidio classifying "High" as a location? Is this the en_core_web_lg model's NER? Check if "High" matches any location patterns. Check deny_list_location in config.py - note it's case-sensitive and only has uppercase abbreviations.

  **Failure 2: "Ronald McDonald House" not detected as PHI**
  - Input: "Ronald McDonald House" (specific charity housing for families)
  - Observed: Not being redacted, but should be LOCATION since it reveals patient's housing situation
  - Investigate: Check if any recognizer patterns would catch this. Standard Presidio LOCATION detection relies on spaCy NER - does it recognize this as an organization/location? Check school_recognizer in pediatric.py - it only catches schools/daycares, not charity housing.

  **Failure 3: "35 weeker" becomes "[AGE]"**
  - Input: "35 weeker" (medical shorthand for 35 weeks gestational age)
  - Observed: Being flagged as PEDIATRIC_AGE
  - Investigate: Check gestational_age pattern in pediatric.py: `r"\b(\d{2})[\s-]?(?:week|wk)(?:er|s)?(?:\s+(?:gestation|gestational|GA))?\b"` - this pattern explicitly includes "weeker" suffix. The question is: should "35 weeker" be considered PHI? It's standard medical terminology that doesn't identify a specific patient without additional context.

  Run test commands to confirm behavior:
  ```bash
  python -c "from app.deidentification import deidentify_text; print(deidentify_text('Patient on high flow oxygen').clean_text)"
  python -c "from app.deidentification import deidentify_text; print(deidentify_text('Family staying at Ronald McDonald House').clean_text)"
  python -c "from app.deidentification import deidentify_text; print(deidentify_text('This is a 35 weeker with respiratory distress').clean_text)"
  ```
  </action>
  <verify>Commands run successfully and confirm the described behavior</verify>
  <done>Each failure's code path traced and mechanism identified</done>
</task>

<task type="auto">
  <name>Task 2: Document findings in INVESTIGATION.md</name>
  <files>.planning/quick/001-investigate-deidentification-code/INVESTIGATION.md</files>
  <action>
  Create INVESTIGATION.md with structured findings for each failure:

  For each failure document:
  1. **Test case**: Exact input and expected vs actual output
  2. **Code path**: Which recognizer/model triggers the detection (or misses it)
  3. **Root cause**: Specific line(s) of code or configuration causing the issue
  4. **Classification**: Is this a false positive, false negative, or debatable case?
  5. **Design question**: Does fixing this align with project goals (balanced precision/recall)?

  Include code snippets showing the relevant patterns/logic.
  Note any trade-offs (e.g., fixing "35 weeker" might miss actual identifying ages).
  </action>
  <verify>INVESTIGATION.md exists and contains analysis for all 3 failures</verify>
  <done>Root cause documented for all three failures with actionable findings</done>
</task>

</tasks>

<verification>
- [ ] All three failure cases reproduced via command line
- [ ] Each failure traced to specific code/pattern
- [ ] INVESTIGATION.md created with complete analysis
- [ ] No code changes made (investigation only)
</verification>

<success_criteria>
Three documented root causes with:
- Specific code/pattern references
- Classification (false positive, false negative, or debatable)
- Clear explanation a developer could act on
</success_criteria>

<output>
After completion, create `.planning/quick/001-investigate-deidentification-code/001-SUMMARY.md`
</output>
