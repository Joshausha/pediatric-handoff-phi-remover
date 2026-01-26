---
phase: 09-cicd-fixes
plan: 01
subsystem: infrastructure
tags: [ci, dependencies, lint, ruff, pip, numpy, typing]

# Dependency graph
requires:
  - phase: 08-weighted-recall-evaluation
    provides: v1.0 milestone complete, ready for v2.0 CI/CD fixes
provides:
  - Clean ruff linting (0 errors)
  - Resolved dependency conflicts (numpy, philter-ucsf)
  - Development dependencies file (requirements-dev.txt)
affects: [09-02-cicd-fixes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Annotated[T, File()] pattern for FastAPI file uploads (ruff B008)"
    - "Exception chaining with 'from e' for proper traceback (ruff B904)"

key-files:
  created:
    - requirements-dev.txt
  modified:
    - requirements.txt
    - app/config.py
    - app/main.py

key-decisions:
  - "Remove numpy<2.0 constraint - let pip resolve based on package needs"
  - "Use modern Python 3.9+ type hints (list/dict) instead of typing.List/Dict"
  - "Separate dev dependencies into requirements-dev.txt for cleaner CI"

patterns-established:
  - "Pattern: Use Annotated[UploadFile, File()] instead of = File(...) for ruff compliance"
  - "Pattern: Add 'from e' to exception re-raises for proper chaining"

# Metrics
duration: 6min
completed: 2026-01-26
---

# Phase 09 Plan 01: Fix CI Dependency and Lint Errors

**Clean ruff linting and resolved dependency conflicts for CI pipeline**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-26T20:25:38Z
- **Completed:** 2026-01-26T20:31:08Z

## One-Liner

Resolved numpy constraint conflict and fixed all ruff lint errors (F821, F401, I001, B008, B904, UP006, UP011, UP032) for clean CI pipeline.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 0 | Fix numpy version constraint (DEP-02) | 9e44003 | requirements.txt |
| 0B/0C | Fix lint errors (LINT-01/02/03) | 09f92fc | app/config.py, app/main.py |
| 3 | Commit requirements-dev.txt | bdf1b66 | requirements-dev.txt |

## Changes Made

### DEP-02: Removed numpy<2.0 Constraint
- **Problem:** numpy<2.0 conflicts with presidio-evaluator>=0.2.4 (requires numpy>=2.0.0)
- **Solution:** Remove constraint, let pip resolve version based on package requirements
- **File:** requirements.txt

### LINT-01: Fixed Missing Dict Import (F821)
- **Problem:** `Dict[str, int]` used without import in app/config.py:217
- **Solution:** Replace with modern `dict[str, int]` syntax (Python 3.9+)
- **File:** app/config.py

### LINT-02: Fixed Unused Import (F401)
- **Problem:** `DeidentificationResult` imported but unused in app/main.py
- **Solution:** Remove unused import
- **File:** app/main.py

### LINT-03: Fixed Import Sorting (I001)
- **Problem:** Import blocks unsorted in app/main.py
- **Solution:** Sort imports: stdlib, third-party, local
- **File:** app/main.py

### Additional Lint Fixes
- **B008:** Use `Annotated[UploadFile, File()]` instead of `= File(...)` in function defaults
- **B904:** Add `from e` to exception re-raises for proper chaining
- **UP006:** Use builtin `list`/`dict` instead of `typing.List`/`typing.Dict`
- **UP011:** Remove unnecessary parentheses from `@lru_cache()`
- **UP032:** Convert `.format()` to static text in docstring

## Deviations from Plan

### Additional Fixes Required
**1. [Rule 2 - Missing Critical] Additional ruff errors discovered**
- **Found during:** Task 0B/0C verification
- **Issue:** Plan only mentioned F821, F401, I001 but ruff also flagged B008, B904, UP006, UP011, UP032
- **Fix:** Fixed all errors for complete lint compliance
- **Files modified:** app/config.py, app/main.py

### Plan Scope Clarification
**2. TEST-02 Already Fixed**
- **Found during:** Task 1 investigation
- **Issue:** Plan said to fix "35 weeker" in should_contain, but commit ed10af5 already fixed this
- **Action:** Verified existing fix is correct, no changes needed

## Verification Results

```bash
# Lint check
$ ruff check app/
All checks passed!

# Dependency resolution
$ pip install -r requirements.txt --dry-run
No resolution conflict (GOOD)

# Presidio tests
$ python test_presidio.py
RESULTS: 18/21 passed (86%)
```

## Known Limitations

The following test failures are **pre-existing PHI detection limitations** (out of scope for this CI fix plan):

1. Phone detection: `555-0123` not detected
2. Age detection: `3 weeks 2 days` not detected
3. Address detection: `425 Oak Street` not detected
4. Hyphenated patterns: `3-5`, `9-12` false positives as ROOM

These require Pattern Improvements (future Phase 9 Plan 2).

## Success Criteria

- [x] DEP-01: requirements.txt verified clean (no philter-ucsf>=2.0.0)
- [x] DEP-02: numpy<2.0 constraint removed from requirements.txt
- [x] LINT-01: Dict imported in app/config.py (F821 fixed)
- [x] LINT-02: DeidentificationResult unused import removed from app/main.py (F401 fixed)
- [x] LINT-03: Import blocks sorted in app/main.py (I001 fixed)
- [x] ruff check app/ passes with 0 errors
- [x] requirements-dev.txt committed

## Next Phase Readiness

**Phase 09 Plan 02:** Fix remaining test expectations
- Address pre-existing PHI detection test failures
- Update SAMPLE_TRANSCRIPTS expectations to match v1.0 behavior
- Decision needed: Lower test expectations vs improve detection
