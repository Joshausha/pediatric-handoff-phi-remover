# Phase 21 Plan 02: Facility Names and Address Patterns Summary

**Phase:** 21-location-transfer-patterns
**Plan:** 02
**Subsystem:** PHI Detection / LOCATION Entity
**Tags:** presidio, recognizer, location, facility, address

## Status: Absorbed into Plan 21-01

All patterns originally planned for 21-02 were implemented as part of Plan 21-01's execution due to pattern interdependencies. See 21-01-SUMMARY.md for complete details.

## Patterns Implemented (in 21-01)

### Facility Name Patterns (6)
- `hospital_name` - "[Name] Hospital"
- `medical_center_name` - "[Name] Medical Center"
- `clinic_name` - "[Name] Clinic"
- `pediatrics_office` - "[Name] Pediatrics"
- `health_system` - "[Name] Health System/Center"
- `urgent_care` - "[Name] Urgent Care"

### Residential Address Patterns (4)
- `lives_at_address` - "lives at 123 Main Street"
- `lives_in_city` - "lives in Boston"
- `discharge_to` - "discharge to home"
- `from_city` - "from [City]ville/ton/burg"

### PCP Context Pattern (1)
- `pcp_at_facility` - "at Springfield Pediatrics"

## One-liner

Work absorbed into 21-01; facility and address patterns implemented with (?-i:[A-Z]) case-sensitivity

## Success Criteria Met

- [x] 6 facility name patterns added (via 21-01)
- [x] 4 residential address patterns added (via 21-01)
- [x] 1 PCP context pattern added (via 21-01)
- [x] Medical abbreviations (PICU, NICU, OR) NOT flagged as LOCATION
- [x] No regressions on existing tests

---
*Generated: 2026-01-31*
*Note: Plan work completed in 21-01 commit 61bfacd*
