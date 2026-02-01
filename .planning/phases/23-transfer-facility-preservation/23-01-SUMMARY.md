---
phase: 23-transfer-facility-preservation
plan: 01
subsystem: deidentification
tags: [presidio, pydantic, phi-detection, hipaa]

# Dependency graph
requires:
  - phase: 21-transfer-facility-detection
    provides: LOCATION patterns for transfer contexts
provides:
  - Configurable transfer facility mode (conservative/clinical)
  - Conditional Presidio operator selection (keep vs replace)
  - Environment variable configuration support
affects:
  - 23-02-frontend-mode-selection
  - future-phases-requiring-location-customization

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Conditional Presidio operator based on mode (keep vs replace)"
    - "Pydantic field_validator for enum-style validation"
    - "Optional parameter with settings fallback pattern"

key-files:
  created:
    - tests/test_transfer_facility_mode.py
  modified:
    - app/config.py
    - app/deidentification.py

key-decisions:
  - "Default to conservative mode (HIPAA Safe Harbor compliant)"
  - "Use Presidio keep operator for clinical mode (preserves all LOCATION entities)"
  - "Accept tradeoff: clinical mode preserves both transfer facilities AND home addresses"
  - "Parameter override allows per-call mode selection independent of config"

patterns-established:
  - "Mode-based conditional operator assignment in deidentification.py"
  - "Pydantic validation with clear error messages for invalid mode values"
  - "Settings fallback pattern: parameter defaults to None, resolved from settings if not specified"

# Metrics
duration: 3min
completed: 2026-01-31
---

# Phase 23 Plan 01: Transfer Facility Preservation Summary

**Configurable LOCATION preservation with conservative (HIPAA) and clinical (care coordination) modes using Presidio keep operator**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-01T00:48:48Z
- **Completed:** 2026-02-01T00:52:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- transfer_facility_mode configuration with Pydantic validation (conservative/clinical)
- Conditional Presidio operator selection (keep vs replace for LOCATION)
- 15 comprehensive unit tests covering all scenarios (config, conservative, clinical, deny list, override)
- Environment variable override support (TRANSFER_FACILITY_MODE)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add transfer_facility_mode setting to config.py** - `92ddc9d` (feat)
2. **Task 2: Implement conditional LOCATION operator in deidentification.py** - `261f30c` (feat)
3. **Task 3: Create unit tests for transfer facility mode** - `96032d9` (test)

## Files Created/Modified
- `app/config.py` - Added transfer_facility_mode Field with validation, default conservative
- `app/deidentification.py` - Added transfer_facility_mode parameter, conditional LOCATION operator logic
- `tests/test_transfer_facility_mode.py` - 15 unit tests covering config validation, both modes, deny list interaction, parameter override

## Decisions Made

**1. Default to conservative mode**
- Rationale: HIPAA Safe Harbor compliance should be default, clinical mode requires explicit opt-in

**2. Use Presidio keep operator (not custom filtering)**
- Rationale: Leverages built-in framework capability, handles edge cases, cleaner than post-processing

**3. Accept all LOCATION preservation tradeoff in clinical mode**
- Rationale: Splitting LOCATION into TRANSFER_FACILITY and RESIDENTIAL_ADDRESS would require pattern rework across all recognizers. Clinical mode is explicit user choice - they accept this tradeoff for care coordination.

**4. Parameter override pattern**
- Rationale: Allows per-call mode selection independent of config setting for testing and mixed-mode workflows

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Python 3.9 type annotation compatibility**
- **Found during:** Task 3 (test execution)
- **Issue:** Python 3.9 doesn't support `str | None` syntax (PEP 604), causing TypeError on import
- **Fix:** Changed to `Optional[str]` (compatible with Python 3.9+)
- **Files modified:** app/deidentification.py
- **Verification:** All 15 tests pass in venv with Python 3.9.6
- **Committed in:** 96032d9 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential for Python 3.9 compatibility. No scope creep.

## Issues Encountered

**numpy compatibility warning in system Python**
- Issue: System Python 3.9 has numpy dtype size mismatch preventing Presidio import
- Resolution: Used venv with correct numpy version. This is a known environment issue, not code issue.

## User Setup Required

None - no external service configuration required.

Configuration can be set via environment variable:
```bash
export TRANSFER_FACILITY_MODE=clinical  # or conservative (default)
```

## Next Phase Readiness

Ready for Phase 23-02 (frontend mode selection):
- Backend configuration complete and validated
- Both modes tested and working correctly
- Deny list filtering confirmed working in both modes
- Parameter override pattern enables easy frontend integration

No blockers. Frontend can now add radio button selection and pass mode to transcription endpoint.

---
*Phase: 23-transfer-facility-preservation*
*Completed: 2026-01-31*
