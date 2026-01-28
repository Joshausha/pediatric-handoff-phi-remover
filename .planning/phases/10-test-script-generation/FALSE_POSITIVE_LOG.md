# False Positive Log - Phase 10 Test Scripts

**Session Date**: _________________
**Processed By**: _________________

## Purpose

This log documents false positives discovered during test script processing. Use this to systematically capture issues for deny list updates.

## Quick Summary

| Category | Count | Top Issues |
|----------|-------|------------|
| Duration Phrases | | |
| Flow Terminology | | |
| Medical Abbreviations | | |
| Unit Names Lost | | |
| Other | | |

**Total False Positives**: _______

## Important Notes

- **Server restart required**: Config deny lists are cached via `@lru_cache` decorator
- After updating deny lists in `app/config.py`, restart server: `uvicorn app.main:app --reload`
- Re-process recordings to verify fixes

---

## R1: RSV Bronchiolitis

**Script**: `r1_rsv_bronchiolitis.txt`
**Recording**: `r1_rsv_bronchiolitis.m4a`
**Processed**: _______________

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| | | | |

### Recommended Deny List Additions

**LOCATION deny list**:
- [ ]

**PERSON deny list**:
- [ ]

**DATE_TIME deny list**:
- [ ]

---

## R2: Pneumonia with Antibiotics

**Script**: `r2_pneumonia_antibiotics.txt`
**Recording**: `r2_pneumonia_antibiotics.m4a`
**Processed**: _______________

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| | | | |

### Recommended Deny List Additions

**LOCATION deny list**:
- [ ]

**PERSON deny list**:
- [ ]

**DATE_TIME deny list**:
- [ ]

---

## R3: Asthma Exacerbation

**Script**: `r3_asthma_exacerbation.txt`
**Recording**: `r3_asthma_exacerbation.m4a`
**Processed**: _______________

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| | | | |

### Recommended Deny List Additions

**LOCATION deny list**:
- [ ]

**PERSON deny list**:
- [ ]

**DATE_TIME deny list**:
- [ ]

---

## R4: Gastroenteritis

**Script**: `r4_gastroenteritis.txt`
**Recording**: `r4_gastroenteritis.m4a`
**Processed**: _______________

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| | | | |

### Recommended Deny List Additions

**LOCATION deny list**:
- [ ]

**PERSON deny list**:
- [ ]

**DATE_TIME deny list**:
- [ ]

---

## R5: Febrile Infant

**Script**: `r5_febrile_infant.txt`
**Recording**: `r5_febrile_infant.m4a`
**Processed**: _______________

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| | | | |

### Recommended Deny List Additions

**LOCATION deny list**:
- [ ]

**PERSON deny list**:
- [ ]

**DATE_TIME deny list**:
- [ ]

---

## R6: Croup with Stridor

**Script**: `r6_croup_stridor.txt`
**Recording**: `r6_croup_stridor.m4a`
**Processed**: _______________

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| | | | |

### Recommended Deny List Additions

**LOCATION deny list**:
- [ ]

**PERSON deny list**:
- [ ]

**DATE_TIME deny list**:
- [ ]

---

## E1: Duration Phrase Saturation

**Script**: `e1_duration_saturation.txt`
**Recording**: `e1_duration_saturation.m4a`
**Processed**: _______________

**Expected Issues**: Duration phrases like "three days ago", "past day or so", "five hours ago" flagged as DATE_TIME

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| | | | |

### Recommended Deny List Additions

**DATE_TIME deny list**:
- [ ]

---

## E2: More Duration Phrases

**Script**: `e2_more_duration.txt`
**Recording**: `e2_more_duration.m4a`
**Processed**: _______________

**Expected Issues**: More duration patterns like "day 4 of illness", "over the past two days", "last 24 hours"

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| | | | |

### Recommended Deny List Additions

**DATE_TIME deny list**:
- [ ]

---

## E3: Flow Terminology Stress Test

**Script**: `e3_flow_terminology.txt`
**Recording**: `e3_flow_terminology.m4a`
**Processed**: _______________

**Expected Issues**: Standalone "high" and "low" flagged as LOCATION (should only flag in isolation, not when part of "high flow" or "low flow")

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| | | | |

### Recommended Deny List Additions

**LOCATION deny list**:
- [ ]

**Notes on word boundaries**:


---

## E4: Mixed Flow and Duration

**Script**: `e4_mixed_flow_duration.txt`
**Recording**: `e4_mixed_flow_duration.m4a`
**Processed**: _______________

**Expected Issues**: Combination of duration phrases and flow terminology false positives

### False Positives Found

| Original Phrase | Entity Type | Score | Should NOT Be Flagged Because |
|-----------------|-------------|-------|-------------------------------|
| | | | |

### Recommended Deny List Additions

**LOCATION deny list**:
- [ ]

**DATE_TIME deny list**:
- [ ]

---

## Batch Findings Across All Scripts

### Pattern 1: Duration Phrases as DATE_TIME

**Patterns identified**:


**Proposed solution**:


### Pattern 2: Flow Terminology as LOCATION

**Patterns identified**:


**Proposed solution**:


### Pattern 3: Medical Abbreviations

**Patterns identified**:


**Proposed solution**:


### Pattern 4: Other Issues

**Patterns identified**:


**Proposed solution**:


---

## Next Steps

After completing this log:

1. [ ] Review all documented false positives
2. [ ] Update deny lists in `app/config.py`
3. [ ] Restart server to clear `@lru_cache`
4. [ ] Re-process all recordings
5. [ ] Verify false positives are eliminated
6. [ ] Document any remaining issues for future work

---

**Log Completed**: _________________
