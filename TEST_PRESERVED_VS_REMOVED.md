# Test: Preserved vs Removed Entity Display

## Issue
When using clinical mode with LOCATION entities preserved, the UI incorrectly showed "1 PHI elements removed" even though the LOCATION was kept (preserved), not removed.

## Fix
Added tracking for preserved vs removed entities:
- Backend: New fields `entities_removed_count`, `entities_preserved_count` in `DeidentificationResult`
- API: New `phi_detected` response field with removed/preserved breakdown
- Frontend: Updated to show accurate count and visual distinction

## Expected Behavior

### Conservative Mode (default)
**Input:** "Patient transferred from Children's Hospital. Contact Sarah at 555-1234."

**Expected API Response:**
```json
{
  "phi_detected": {
    "total_count": 3,
    "removed_count": 3,
    "preserved_count": 0,
    "removed_by_type": {
      "LOCATION": 1,
      "PERSON": 1,
      "PHONE_NUMBER": 1
    },
    "preserved_by_type": {}
  }
}
```

**Expected UI:**
- Header: "3 PHI elements removed"
- Badges:
  - `1 Location (removed)` - green background
  - `1 Person (removed)` - green background
  - `1 Phone Number (removed)` - green background

### Clinical Mode
**Input:** "Patient transferred from Children's Hospital. Contact Sarah at 555-1234."

**Expected API Response:**
```json
{
  "phi_detected": {
    "total_count": 3,
    "removed_count": 2,
    "preserved_count": 1,
    "removed_by_type": {
      "PERSON": 1,
      "PHONE_NUMBER": 1
    },
    "preserved_by_type": {
      "LOCATION": 1
    }
  }
}
```

**Expected UI:**
- Header: "2 PHI elements removed" (accurate - only 2 were actually removed)
- Badges:
  - `1 Person (removed)` - green background
  - `1 Phone Number (removed)` - green background
  - `1 Location (preserved)` - yellow/orange background

## Manual Testing Steps

1. Start server: `uvicorn app.main:app --reload`
2. Open http://localhost:8000
3. Record or upload audio with: "Patient transferred from Children's Hospital. Contact Sarah at 555-1234."
4. Test with **Conservative mode** (default):
   - Should show "3 PHI elements removed"
   - All badges should be green
5. Test with **Clinical mode**:
   - Should show "2 PHI elements removed" (not 3!)
   - Should show 2 green badges (removed) and 1 yellow badge (preserved)
   - Preserved badge should say "Location (preserved)"

## Verification
- [ ] Conservative mode shows correct count (all detected = all removed)
- [ ] Clinical mode shows correct count (only removed entities, not preserved)
- [ ] Visual distinction: green for removed, yellow/orange for preserved
- [ ] Labels accurately reflect action taken: "(removed)" vs "(preserved)"
