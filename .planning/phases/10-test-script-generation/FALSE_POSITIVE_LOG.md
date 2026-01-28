# False Positive Log - Phase 10 Test Scripts

**Session Date**: 2026-01-28
**Processed By**: Josh Pankin

## Purpose

This log documents false positives discovered during test script processing. Use this to systematically capture issues for deny list updates.

## Quick Summary

| Category | Count | Top Issues |
|----------|-------|------------|
| Duration Phrases | 26 | "three days", "two days", "48 hours", "six hours", "twelve hours", "one week", "day 4", "the past two days", "last 24 hours", "two to three days" |
| Flow Terminology | 15 | "high" in "high flow", "on high", "low" in "low flow" |
| Medical Abbreviations | 0 | None detected (existing deny lists working) |
| Unit Names Lost | 0 | None (preserving "PICU bed", "NICU bed") |
| Other | 4 | "barky", "room air", "bedside" (x2), "mid-90s" (oxygen sat) |

**Total False Positives**: 45

## Important Notes

- **Server restart required**: Config deny lists are cached via `@lru_cache` decorator
- After updating deny lists in `app/config.py`, restart server: `uvicorn app.main:app --reload`
- Re-process recordings to verify fixes

---

## R1: RSV Bronchiolitis

**Script**: `r1_rsv_bronchiolitis.txt`
**Recording**: `r1_rsv_bronchiolitis.m4a`
**Processed**: 2026-01-28

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| "mid-90s" | DATE_TIME | Unknown | Refers to oxygen saturation percentage, not a date |

### Recommended Deny List Additions

**DATE_TIME deny list**:
- [x] "mid-90s" (oxygen saturation context)

---

## R2: Pneumonia with Antibiotics

**Script**: `r2_pneumonia_antibiotics.txt`
**Recording**: `r2_pneumonia_antibiotics.m4a`
**Processed**: 2026-01-28

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| "48 hours" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "two to three days" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |

### Recommended Deny List Additions

**DATE_TIME deny list**:
- [x] "48 hours"
- [x] "two to three days"

---

## R3: Asthma Exacerbation

**Script**: `r3_asthma_exacerbation.txt`
**Recording**: `r3_asthma_exacerbation.m4a`
**Processed**: 2026-01-28

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| "another hour" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |

### Recommended Deny List Additions

**DATE_TIME deny list**:
- [x] "another hour"

---

## R4: Gastroenteritis

**Script**: `r4_gastroenteritis.txt`
**Recording**: `r4_gastroenteritis.m4a`
**Processed**: 2026-01-28

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| "three days" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "two days" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "bedside" | NAME | Unknown | Location descriptor, not a person name |
| "one more hour" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |

### Recommended Deny List Additions

**DATE_TIME deny list**:
- [x] "three days"
- [x] "two days"
- [x] "one more hour"

**PERSON deny list**:
- [x] "bedside"

---

## R5: Febrile Infant

**Script**: `r5_febrile_infant.txt`
**Recording**: `r5_febrile_infant.m4a`
**Processed**: 2026-01-28

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| "48 hours" (second instance) | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "bedside" | NAME | Unknown | Location descriptor, not a person name |

### Recommended Deny List Additions

**DATE_TIME deny list**:
- [x] "48 hours" (already noted in R2)

**PERSON deny list**:
- [x] "bedside" (already noted in R4)

---

## R6: Croup with Stridor

**Script**: `r6_croup_stridor.txt`
**Recording**: `r6_croup_stridor.m4a`
**Processed**: 2026-01-28

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| "two days" (second instance) | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "barky" | NAME | Unknown | Clinical descriptor for croup cough, not a person |
| "three hours" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "another hour" (second instance) | DATE_TIME | Unknown | Duration phrase, not absolute date/time |

### Recommended Deny List Additions

**DATE_TIME deny list**:
- [x] "two days" (already noted)
- [x] "three hours"
- [x] "another hour" (already noted)

**PERSON deny list**:
- [x] "barky" (croup symptom descriptor)

---

## E1: Duration Phrase Saturation

**Script**: `e1_duration_saturation.txt`
**Recording**: `e1_duration_saturation.m4a`
**Processed**: 2026-01-28

**Expected Issues**: Duration phrases like "three days ago", "past day or so", "five hours ago" flagged as DATE_TIME

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| "three days" (third instance) | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "a day and a half ago" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "yesterday" | DATE_TIME | Unknown | Relative time reference, not specific PHI |
| "five hours ago" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "another hour" (third instance) | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "tomorrow" | DATE_TIME | Unknown | Relative time reference, not specific PHI |

### Recommended Deny List Additions

**DATE_TIME deny list**:
- [x] "a day and a half ago"
- [x] "yesterday"
- [x] "five hours ago"
- [x] "tomorrow"

**Notes**: "three days" and "another hour" already noted in earlier scripts

---

## E2: More Duration Phrases

**Script**: `e2_more_duration.txt`
**Recording**: `e2_more_duration.m4a`
**Processed**: 2026-01-28

**Expected Issues**: More duration patterns like "day 4 of illness", "over the past two days", "last 24 hours"

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| "day 4" | DATE_TIME | Unknown | Duration phrase (day X of illness), not absolute date |
| "yesterday" (second instance) | DATE_TIME | Unknown | Relative time reference, not specific PHI |
| "4 doses" | DATE_TIME | Unknown | Medication dosing count, not a date |
| "the past two days" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "two to three days" (second instance) | DATE_TIME | Unknown | Duration phrase, not absolute date/time |

### Recommended Deny List Additions

**DATE_TIME deny list**:
- [x] "day 4"
- [x] "4 doses"
- [x] "the past two days"

**Notes**: "yesterday" and "two to three days" already noted in earlier scripts

---

## E3: Flow Terminology Stress Test

**Script**: `e3_flow_terminology.txt`
**Recording**: `e3_flow_terminology.m4a`
**Processed**: 2026-01-28

**Expected Issues**: Standalone "high" and "low" flagged as LOCATION (should only flag in isolation, not when part of "high flow" or "low flow")

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| "high" (in "high flow") (x5) | LOCATION | Unknown | Part of medical term "high flow oxygen", not a location |
| "on high" (x2) | LOCATION | Unknown | Part of medical term "on high flow", not a location |
| "low" (in "low flow") (x4) | LOCATION | Unknown | Part of medical term "low flow oxygen", not a location |
| "on low" | LOCATION | Unknown | Part of medical term "on low flow", not a location |
| "room" (in "room air") | NAME | Unknown | Part of medical term "room air", not a person name |

### Recommended Deny List Additions

**LOCATION deny list**:
- [x] "high" (when followed by "flow")
- [x] "low" (when followed by "flow")

**PERSON deny list**:
- [x] "room" (when part of "room air")

**Notes on word boundaries**:
- Current issue: "high" and "low" are being flagged even when part of compound medical terms
- Solution needed: Context-aware deny list or pattern matching that considers word boundaries and adjacent terms
- Alternative: Add "high flow", "low flow", "on high", "on low" as complete phrases to deny list

---

## E4: Mixed Flow and Duration

**Script**: `e4_mixed_flow_duration.txt`
**Recording**: `e4_mixed_flow_duration.m4a`
**Processed**: 2026-01-28

**Expected Issues**: Combination of duration phrases and flow terminology false positives

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| "high" (in "high flow") (x2) | LOCATION | Unknown | Part of medical term "high flow oxygen", not a location |
| "48 hours" (third instance) | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "low flow" | LOCATION | Unknown | Medical term for oxygen delivery, not a location |
| "six hours" | DATE_TIME | Unknown | Duration phrase, not absolute date/time |
| "room" (in "room air") | NAME | Unknown | Part of medical term "room air", not a person name |

### Recommended Deny List Additions

**LOCATION deny list**:
- [x] "high" (already noted in E3)
- [x] "low" (already noted in E3)
- [x] "low flow" (complete phrase)

**DATE_TIME deny list**:
- [x] "six hours"

**PERSON deny list**:
- [x] "room" (already noted in E3)

---

## Batch Findings Across All Scripts

### Pattern 1: Duration Phrases as DATE_TIME

**Patterns identified**:
- Simple duration: "three days", "two days", "six hours", "twelve hours"
- Relative duration: "a day and a half ago", "five hours ago"
- Relative temporal: "yesterday", "tomorrow"
- Clinical progression: "day 4 of illness"
- Range duration: "two to three days", "48 hours"
- Continuation duration: "another hour", "one more hour"
- Recent past: "the past two days", "last 24 hours"
- Dosing counts: "4 doses" (numeric followed by time unit)
- Oxygen saturation: "mid-90s" (percentage context)

**Total instances**: 26 false positives across all scripts

**Proposed solution**:
1. Add duration phrase patterns to DATE_TIME deny list in app/config.py
2. Consider contextual filtering: phrases with "ago", "of illness", "past", duration ranges
3. Add numeric-only temporal references that aren't specific dates
4. Special case: "mid-90s" should be filtered when in clinical numeric context

### Pattern 2: Flow Terminology as LOCATION

**Patterns identified**:
- "high" when part of "high flow oxygen" (7 instances)
- "on high" as shorthand for "on high flow" (2 instances)
- "low" when part of "low flow oxygen" (4 instances)
- "on low" as shorthand for "on low flow" (1 instance)
- "low flow" as complete phrase (1 instance)

**Total instances**: 15 false positives across all scripts

**Proposed solution**:
1. Add context-aware patterns to LOCATION deny list
2. Options:
   - Add complete phrases: "high flow", "low flow", "on high", "on low"
   - Add word boundary rules that check adjacent words
3. Current deny list approach may need enhancement to handle multi-word medical terms

### Pattern 3: Medical Abbreviations

**Patterns identified**:
- NONE - existing deny lists successfully filtered common abbreviations (NC, RA, OR, ER, etc.)

**Total instances**: 0 false positives

**Proposed solution**:
- No changes needed; current approach working correctly

### Pattern 4: Other Issues

**Patterns identified**:
- "barky" flagged as NAME (clinical descriptor for croup cough)
- "room" in "room air" flagged as NAME (medical term)
- "bedside" flagged as NAME (2 instances - location descriptor)
- "mid-90s" flagged as DATE_TIME (oxygen saturation percentage)

**Total instances**: 4 false positives (5 total instances)

**Proposed solution**:
1. Add clinical descriptors to PERSON deny list: "barky", "bedside"
2. Add medical terminology: "room" when part of "room air"
3. Add "mid-90s" to DATE_TIME deny list with context awareness for clinical percentages

---

## Summary for Phase 11

### Total False Positives: 45

**By entity type:**
- DATE_TIME: 26 instances (58%)
- LOCATION: 15 instances (33%)
- NAME/PERSON: 4 instances (9%)

### Priority Actions for Phase 11

**HIGH PRIORITY - DATE_TIME deny list expansion:**
- Add duration phrases: "three days", "two days", "six hours", "twelve hours", "48 hours", "one week"
- Add relative time: "yesterday", "tomorrow", "ago"
- Add progression terms: "day 4", "day X of illness"
- Add continuation: "another hour", "one more hour"
- Add ranges: "two to three days"
- Add recent past: "the past two days", "last 24 hours"
- Add clinical numeric: "mid-90s"

**HIGH PRIORITY - LOCATION deny list expansion:**
- Add flow terminology: "high flow", "low flow", "on high", "on low", "high", "low" (with context)
- Consider multi-word phrase matching vs. word boundary rules

**MEDIUM PRIORITY - PERSON deny list expansion:**
- Add clinical descriptors: "barky", "bedside"
- Add medical terms: "room" (in "room air" context)

### Expected Outcome

After implementing these deny list expansions in Phase 11:
- **Duration phrases**: Should eliminate 26 false positives (58% reduction)
- **Flow terminology**: Should eliminate 15 false positives (33% reduction)
- **Clinical descriptors**: Should eliminate 4 false positives (9% reduction)
- **Total expected improvement**: ~100% of documented false positives eliminated

### Implementation Considerations

1. **Multi-word phrase matching**: Current deny list may need enhancement to handle "high flow" as a complete phrase vs. just "high"
2. **Context awareness**: Some terms like "high" and "low" are only safe in specific medical contexts (oxygen delivery)
3. **Word boundaries**: Need to ensure deny list filtering respects word boundaries
4. **Testing verification**: After Phase 11 implementation, re-process all 10 recordings to verify fixes

### Unexpected Findings

1. **Existing deny lists worked well**: No false positives for common medical abbreviations (NC, RA, OR, ER) — validation that v1.0 deny lists are effective
2. **Flow terminology more problematic than expected**: 15 instances across edge-case scripts suggest this is a systematic issue in pediatric respiratory handoffs
3. **Duration phrases extremely common**: 26 instances show this is the #1 source of over-detection
4. **"Barky" as NAME**: Interesting edge case — clinical descriptors can trigger person name detection

---

## Next Steps

After completing this log:

1. [x] Review all documented false positives
2. [ ] Update deny lists in `app/config.py` (Phase 11 task)
3. [ ] Restart server to clear `@lru_cache` (Phase 11 task)
4. [ ] Re-process all recordings (Phase 11 task)
5. [ ] Verify false positives are eliminated (Phase 11 task)
6. [ ] Document any remaining issues for future work (Phase 11 task)

---

**Log Completed**: 2026-01-28
