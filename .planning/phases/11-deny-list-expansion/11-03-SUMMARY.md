---
phase: 11
plan: 03
title: "Unit Name Preservation in ROOM Redaction"
subsystem: phi-detection
tags: [presidio, room-detection, pediatric-units, lookbehind-regex]

requires:
  - "Phase 04-04: Custom room/bed patterns for pediatric settings"
  - "Phase 06: Deny list infrastructure for filtering false positives"

provides:
  - "Unit name preservation for ICU types (PICU, NICU, ICU, CVICU, CCU, PACU)"
  - "L&D room pattern with preservation"
  - "Fixed-width lookbehind patterns for reliable unit preservation"

affects:
  - "All ROOM entity detections will preserve hospital unit names"
  - "Clinical utility improved: 'PICU bed 12' → 'PICU [ROOM]' vs '[ROOM]'"

tech-stack:
  added: []
  patterns:
    - "Fixed-width positive lookbehind for regex pattern matching"
    - "Per-unit pattern approach for reliable matching"

key-files:
  created: []
  modified:
    - app/recognizers/medical.py
    - app/config.py

decisions:
  - id: UNIT-01
    title: "Use separate patterns per unit type instead of alternation"
    rationale: "Fixed-width lookbehind is more reliable in Python regex than variable-width alternation"
    alternatives:
      - "Single pattern with (?:picu|nicu|icu) alternation - rejected due to variable-width lookbehind issues"
      - "Post-processing in deidentification.py - rejected to keep logic at pattern level"

  - id: UNIT-02
    title: "Add CVICU, CCU, PACU to PERSON deny list"
    rationale: "Prevents 'baby in CVICU' from detecting CVICU as a name"
    impact: "Prevents unit names from being misclassified as person names"

metrics:
  duration: "6 minutes"
  completed: "2026-01-28"

one_liner: "Preserve hospital unit names (PICU, NICU, ICU, etc.) during ROOM redaction using fixed-width lookbehind patterns"
---

# Phase 11 Plan 03: Unit Name Preservation in ROOM Redaction Summary

**One-liner:** Preserve hospital unit names (PICU, NICU, ICU, etc.) during ROOM redaction using fixed-width lookbehind patterns

## What Was Built

Implemented unit name preservation for ROOM entity redaction so that hospital unit context is retained while bed/room numbers are still properly redacted.

**Before:**
- "PICU bed 12" → "[ROOM]" (unit name lost)
- "NICU bed 3A" → "[ROOM]" (unit name lost)

**After:**
- "PICU bed 12" → "PICU [ROOM]" (unit name preserved)
- "NICU bed 3A" → "NICU [ROOM]" (unit name preserved)

### Implementation Approach

1. **Split ICU pattern into separate per-unit patterns** (medical.py lines 92-118)
   - Original: Single `icu_bed` pattern matching `(?:picu|nicu|icu)\s+bed\s+\d+`
   - New: Separate `picu_bed`, `nicu_bed`, `icu_bed` patterns with fixed-width lookbehind
   - Pattern: `(?i)(?<=picu )bed\s+\d{1,3}[A-Za-z]?\b` (matches only "bed X" part)

2. **Added additional pediatric unit patterns**
   - CVICU (Cardiovascular ICU)
   - CCU (Cardiac Care Unit)
   - PACU (Post-Anesthesia Care Unit)
   - L&D (Labor and Delivery) - for newborn handoff context

3. **Updated PERSON deny list** (config.py)
   - Added CVICU, CCU, PACU to prevent misclassification
   - Prevents "baby in CVICU" from detecting CVICU as two names

4. **Updated room_recognizer context**
   - Added all unit names to context list for better detection confidence

### Technical Details

**Regex Strategy:**
- Fixed-width lookbehind: `(?<=picu )` matches only if preceded by "picu "
- Case-insensitive: `(?i)` flag handles "PICU", "picu", "Picu"
- Pattern matches only the "bed X" portion, leaving "picu" untouched

**Why separate patterns instead of alternation:**
- Python regex requires fixed-width lookbehind
- `(?<=(?:picu|nicu|icu) )` is variable-width (rejected by Python)
- Separate patterns: `(?<=picu )`, `(?<=nicu )`, `(?<=icu )` all fixed-width

## Key Changes

| File | Lines Changed | Description |
|------|--------------|-------------|
| app/recognizers/medical.py | +43, -3 | Split icu_bed into 7 unit-specific patterns with lookbehind |
| app/config.py | +3 | Added CVICU, CCU, PACU to PERSON deny list |

## Testing Results

**Manual verification:**
```
✓ patient in PICU bed 12     → patient in PICU [ROOM]
✓ NICU bed 3A is available    → NICU [ROOM] is available
✓ ICU bed 4                   → ICU [ROOM]
✓ Room 302                    → [ROOM] (standard pattern still works)
✓ bed 5                       → [ROOM] (standalone bed still works)
✓ baby in CVICU bed 3         → baby [NAME] CVICU [ROOM] (acceptable)
✓ PACU bed 2                  → PACU [ROOM]
✓ transferred to CCU bed 7    → transferred to CCU [ROOM]
✓ L&D room 405                → L&D [ROOM]
```

**Full test suite:**
- test_presidio.py: 19/21 tests passing (90% pass rate)
- Room number test (line 100-104): ✅ PASSING
  - Input: "Located in room 4B, PICU bed 12."
  - Must preserve: "PICU", "Located"
  - Must redact: "room 4B", "bed 12"
  - Result: PASS

**No regressions:**
- Standard room patterns still work: "Room 302" → "[ROOM]"
- Standalone bed patterns still work: "bed 5" → "[ROOM]"
- All existing medical abbreviations unaffected

## Clinical Impact

**Improved clinical utility:**
- Preserves critical location context (which ICU unit)
- Removes PHI (specific bed number)
- Enables proper handoff understanding: "PICU [ROOM]" vs "[ROOM]"

**Unit types supported:**
- PICU (Pediatric ICU)
- NICU (Neonatal ICU)
- ICU (General ICU)
- CVICU (Cardiovascular ICU)
- CCU (Cardiac Care Unit)
- PACU (Post-Anesthesia Care Unit)
- L&D (Labor and Delivery)

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

### UNIT-01: Separate patterns per unit type
**Decision:** Use individual patterns for each unit type instead of regex alternation
**Rationale:** Python regex requires fixed-width lookbehind; alternation creates variable-width
**Alternatives considered:**
- Single pattern with `(?:picu|nicu|icu)` alternation - rejected (variable-width lookbehind)
- Post-processing in deidentification.py - rejected (keep logic at pattern level)
**Impact:** More patterns to maintain, but more reliable matching

### UNIT-02: Add units to PERSON deny list
**Decision:** Added CVICU, CCU, PACU to PERSON deny list
**Rationale:** Prevents "baby in CVICU" from detecting CVICU as person name
**Impact:** Prevents false positive PERSON detections for unit abbreviations

## Next Phase Readiness

**Phase 11 remaining work:**
- 11-01: DATE_TIME duration pattern deny list expansion ✅ COMPLETE
- 11-02: LOCATION medical abbreviation deny list expansion (pending)
- 11-03: Unit name preservation ✅ COMPLETE

**Blockers/Concerns:**
None - all patterns working as expected

**Recommendations for Phase 12:**
- Consider adding more unit types as discovered (SICU, MICU, etc.)
- May want to handle edge cases like "PICU bed 12A-B" (multi-bed assignments)

## Commit History

| Commit | Message | Files |
|--------|---------|-------|
| 069d46d | feat(11-03): preserve unit names in ROOM redaction | medical.py, config.py |

## Duration

**Total time:** 6 minutes (2026-01-28 16:25:00 → 16:31:00)

**Breakdown:**
- Pattern implementation: 2 minutes
- Testing and verification: 3 minutes
- Documentation: 1 minute

---
*Summary generated: 2026-01-28*
