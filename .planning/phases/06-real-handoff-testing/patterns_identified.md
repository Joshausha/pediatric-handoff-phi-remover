# Pattern Analysis: Session 1

**Date:** 2026-01-25
**Handoffs analyzed:** 21
**Total errors:** ~65 false positives, 0 false negatives

## Root Cause Identified

**CRITICAL FINDING:** The DATE_TIME deny list was correctly configured in code (commit cfbd5b1, Phase 5 fix) but **the server was not restarted** to pick up changes.

The config module uses `@lru_cache()` to cache settings at startup. The server (PID 36698) was started Saturday and running with stale config that lacked the age pattern deny list entries.

**Proof:**
- Before restart: `"18 year old"` → `[DATE]` (redacted)
- After restart: `"18 year old"` → `"18 year old"` (preserved ✓)

**Resolution:** Server restarted 2026-01-25 to pick up current config. No code changes required.

## Error Distribution

| Entity Type | Count | Severity | Fixable? | Root Cause |
|-------------|-------|----------|----------|------------|
| DATE_TIME | 42 | Critical | ✅ FIXED | Server needed restart |
| PERSON | 5 | Medium | Partial | NER model limitation |
| LOCATION | 11 | Low | Accept | Working as intended |
| GUARDIAN_NAME | 2 | Low | Accept | Over-detection acceptable |

## Pattern Descriptions

### Pattern 1: Patient Ages Over-Redacted (FIXED)

- **Examples:** "18 year old", "2 month old", "10 day old"
- **Root cause:** Stale server config (lru_cache)
- **Recommended fix:** ✅ COMPLETE - Server restart
- **Priority:** P1-Critical → RESOLVED

**Verification:**
```
Before: "18 year old male" → "[DATE] male"
After:  "18 year old male" → "18 year old male" ✓
```

### Pattern 2: Medical Terms as PERSON Names

- **Examples:**
  - "bilirubin" → [NAME] (NER detects as "Billy Rubin")
  - "ARFID" → [NAME] (acronym detected as name)
  - "Citrus" → [NAME] (capitalized word)
- **Root cause:** NER model limitation - medical terms phonetically similar to names
- **Recommended fix:** Add to PERSON deny list (bilirubin, ARFID, citrus, diuresis)
- **Priority:** P3-Medium (clinical utility, not safety)

### Pattern 3: Generic Locations Redacted

- **Examples:** "Boston" (city where family wants to go)
- **Root cause:** Working as intended - locations ARE potentially PHI
- **Recommended fix:** Accept - better safe than sorry
- **Priority:** P4-Low (no fix needed)

## Recommendations

### Immediate (Before Session 2)

1. **✅ COMPLETE:** Server restarted with current config - ages now preserved

### Optional Improvements (P3)

2. **Add medical terms to PERSON deny list:**
   ```python
   # In config.py deny_list_person:
   "bilirubin",
   "ARFID",
   "citrus",
   "diuresis",
   "stable"  # Already added per earlier phases
   ```

### Accept as Limitations

3. LOCATION over-detection: Generic cities like "Boston" - accept as working correctly
4. Occasional NER false positives on proper nouns - acceptable for safety

## Session 2 Approach

**Hypothesis:** With server restart complete, Session 2 should show:
- Zero critical age over-redaction errors
- Possibly some minor medical term detection (low priority)
- Continued excellent PHI safety (zero false negatives)

**Focus areas:**
- Verify age patterns now preserved across all formats
- Confirm no regression on actual PHI detection
- Document any remaining minor issues

---
*Analysis complete: 2026-01-25*
*Root cause: Server restart required for config changes*
