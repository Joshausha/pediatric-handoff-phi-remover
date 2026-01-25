# Error Documentation Template

**Purpose:** Structured documentation matching APHL laboratory validation standards

**Usage:** Copy this template for each error detected during real handoff testing and fill in all fields.

---

## ⚠️ PHI Safety Warning

**CRITICAL: Describe patterns generically - do NOT copy actual PHI into this template.**

- Use de-identified descriptions: "phone number format", "baby + last name pattern"
- Reference handoff by sample number only: "Handoff 03 (8mo bronchiolitis)"
- If examples needed, use system de-identified output or generic placeholders

---

## Error Template

### Error #[N]: [Brief description]

**Sample ID:** Handoff [N] ([patient context - de-identified, e.g., "8mo bronchiolitis"])
**Error Type:**
- [ ] False Negative (PHI leaked)
- [ ] False Positive (over-redaction)

**Entity Type:** [PERSON | PHONE_NUMBER | EMAIL_ADDRESS | DATE_TIME | LOCATION | ROOM | MRN | GUARDIAN_NAME | PEDIATRIC_AGE | Other: ___________]

**Severity:**
- [ ] Critical - Patient directly identifiable from output
- [ ] High - PHI leaked or major clinical context lost
- [ ] Medium - Minor PHI leak or moderate clinical impact
- [ ] Low - Minor inconvenience only

---

### Details

**Original Text (Generic Description - NO REAL PHI):**
[Describe what was spoken using generic patterns or placeholders]
Example: "Phone number in format XXX-XXX-XXXX preceded by 'mom's cell'"

**System Output:**
[What the de-identified output showed - actual redaction result]
Example: "mom's cell is 555-867-5309" (unchanged - false negative)

**Expected Behavior:**
[What should have happened]
Example: "mom's cell is [PHONE]"

---

### Impact Assessment

**Clinical Impact:**
- [ ] Patient identifiable from output (name, contact info, specific identifiers visible)
- [ ] Clinical decision-making impaired (timeline lost, ages unclear, context missing)
- [ ] Minor inconvenience only (preference issue, no safety or utility impact)

**Explanation:**
[Describe why this matters in the clinical context]

---

### Pattern Analysis

**Pattern Hypothesis:**
[Is this error part of a larger pattern? e.g., "Phone numbers preceded by possessive pronouns", "Baby + LastName format"]

**Frequency Expectation:**
- [ ] Likely isolated case
- [ ] May occur occasionally (1-5% of handoffs)
- [ ] Likely common pattern (>5% of handoffs)

**Root Cause Hypothesis:**
- [ ] Deny list gap (term missing from deny list)
- [ ] Pattern recognition gap (regex pattern doesn't cover this case)
- [ ] Context issue (entity not detected in this linguistic context)
- [ ] Threshold issue (score too low, entity filtered out)
- [ ] Other: ___________

---

### Recommended Fix

**Proposed Solution:**
[Specific fix recommendation]
Examples:
- Add "cell" to PHONE_NUMBER context deny list
- Update PERSON regex to include "Baby [LastName]" pattern
- Adjust DATE_TIME threshold from X to Y

**Trade-off Analysis:**
[Does fixing this create new problems?]
Example: "Adding 'cell' to deny list might cause false negatives if 'cell' appears in other medical contexts (e.g., 'cell count')"

**Priority:**
- [ ] High - Fix before production use
- [ ] Medium - Fix in next iteration
- [ ] Low - Monitor for frequency before deciding

---

### Testing Notes

**Re-test Required:**
- [ ] Yes - verify fix on this handoff and 2-3 similar cases
- [ ] No - monitoring only

**Related Errors:**
[Link to other errors if part of same pattern]
Example: "See Error #3 - similar phone number context issue"

---

## Template Usage Example

### Error #1: Phone number with possessive context missed

**Sample ID:** Handoff 03 (infant with bronchiolitis)
**Error Type:**
- [x] False Negative (PHI leaked)
- [ ] False Positive (over-redaction)

**Entity Type:** PHONE_NUMBER

**Severity:**
- [ ] Critical
- [x] High - contact number visible
- [ ] Medium
- [ ] Low

---

### Details

**Original Text (Generic Description - NO REAL PHI):**
Phone number in standard format XXX-XXX-XXXX preceded by "mom's cell is"

**System Output:**
"mom's cell is 555-867-5309" (phone number not redacted)

**Expected Behavior:**
"mom's cell is [PHONE]"

---

### Impact Assessment

**Clinical Impact:**
- [x] Patient identifiable from output (contact tracing possible with phone number)
- [ ] Clinical decision-making impaired
- [ ] Minor inconvenience only

**Explanation:**
Phone number visible in output allows potential patient identification through reverse lookup or contact database correlation. High severity PHI leak.

---

### Pattern Analysis

**Pattern Hypothesis:**
Phone numbers preceded by possessive pronouns ("mom's cell", "dad's phone") may not be detected. Presidio PHONE_NUMBER recognizer may require standalone context.

**Frequency Expectation:**
- [ ] Likely isolated case
- [x] May occur occasionally (1-5% of handoffs)
- [ ] Likely common pattern (>5% of handoffs)

**Root Cause Hypothesis:**
- [ ] Deny list gap
- [x] Context issue (entity not detected in this linguistic context)
- [ ] Pattern recognition gap
- [ ] Threshold issue
- [ ] Other

---

### Recommended Fix

**Proposed Solution:**
Review Presidio PHONE_NUMBER recognizer context patterns. May need to add custom context pattern for "[relationship]'s [contact_type] is [PHONE]" structure.

**Trade-off Analysis:**
Expanding context patterns may increase false positives if medical terms coincidentally match pattern structure. Monitor after fix.

**Priority:**
- [x] High - Fix before production use
- [ ] Medium
- [ ] Low

---

### Testing Notes

**Re-test Required:**
- [x] Yes - test with "mom's cell", "dad's phone", "parent contact" variations

**Related Errors:**
None yet - first phone number error detected
