# Requirements: v2.0 CI/CD Pipeline Fix

## v2.0 Requirements

### Dependencies

- [ ] **DEP-01**: Remove `philter-ucsf>=2.0.0` from requirements.txt (only 1.0.3 exists on PyPI)

### Tests

- [ ] **TEST-01**: Update test expectation for "Ronald McDonald House" — v1.0 preserves it (not PHI)
- [ ] **TEST-02**: Update test expectation for "35 weeker" — v1.0 redacts as [AGE]

### CI/CD Verification

- [ ] **CI-01**: GitHub Actions test workflow passes
- [ ] **CI-02**: GitHub Actions Docker build workflow passes

## Out of Scope

- Performance optimizations — separate milestone
- New PHI detection features — separate milestone
- Security hardening — separate milestone
- Age pattern architecture refactoring — deferred (deny list working)

## Traceability

| Requirement | Phase | Verified |
|-------------|-------|----------|
| DEP-01      | —     | —        |
| TEST-01     | —     | —        |
| TEST-02     | —     | —        |
| CI-01       | —     | —        |
| CI-02       | —     | —        |

---
*Generated: 2026-01-26*
