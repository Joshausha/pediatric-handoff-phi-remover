# Baseline Metrics: PHI Detection System

**Capture Date**: 2026-01-23 13:22:03 EST
**Dataset**: tests/synthetic_handoffs.json (500 samples, seed=42)
**Evaluation Script**: tests/evaluate_presidio.py (overlap threshold: 0.5)

## System Configuration

| Component | Version | Notes |
|-----------|---------|-------|
| Presidio Analyzer | 2.2.354 | Microsoft PHI detection engine |
| spaCy Model | 3.7.4 / en_core_web_lg | NER backbone |
| Python | 3.9.6 | Runtime environment |
| Detection Threshold | 0.35 | Score threshold for entity detection |
| Validation Threshold | 0.7 | Threshold for de-identification validation |

## Overall Performance

### Standard Dataset (500 samples)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Recall | 77.9% | >95% | ❌ BELOW TARGET |
| Precision | 66.3% | >70% | ❌ BELOW TARGET |
| F1 Score | 71.7% | - | - |
| **F2 Score** | **75.3%** | - | **PRIMARY METRIC** |

### Key Safety Metrics

- **Total PHI Leaks**: 369 spans not detected (out of 1,672 expected)
- **Safety Status**: ❌ FAILED - System is NOT safe for production use
- **False Positive Rate**: 662 false detections (over-redaction risk)

## Per-Entity Performance

### Standard Dataset (500 samples)

| Entity Type | TP | FN | FP | Precision | Recall | F1 | F2 | Status |
|-------------|----|----|----|-----------|---------|----|----|----- |
| EMAIL_ADDRESS | 24 | 0 | 0 | 100.0% | 100.0% | 100.0% | 100.0% | ✅ PERFECT |
| PERSON | 747 | 9 | 79 | 90.4% | 98.8% | 94.4% | 97.0% | ✅ EXCELLENT |
| PHONE_NUMBER | 142 | 50 | 1 | 99.3% | 73.9% | 84.8% | 77.9% | ⚠️ MODERATE |
| MEDICAL_RECORD_NUMBER | 90 | 37 | 12 | 88.2% | 70.9% | 78.6% | 73.8% | ⚠️ MODERATE |
| PEDIATRIC_AGE | 60 | 104 | 9 | 87.0% | 36.6% | 51.5% | 41.4% | ❌ CRITICAL |
| DATE_TIME | 184 | 6 | 334 | 35.5% | 96.8% | 52.0% | 72.0% | ❌ OVER-REDACTION |
| ROOM | 31 | 59 | 24 | 56.4% | 34.4% | 42.8% | 37.3% | ❌ CRITICAL |
| LOCATION | 25 | 104 | 6 | 80.6% | 19.4% | 31.3% | 22.9% | ❌ CRITICAL |
| GUARDIAN_NAME | 0 | 0 | 195 | 0.0% | 0.0% | 0.0% | 0.0% | ⚠️ NO DATA |
| MEDICAL_LICENSE | 0 | 0 | 2 | 0.0% | 0.0% | 0.0% | 0.0% | ⚠️ NO DATA |

## Adversarial Dataset Evaluation

**Dataset**: tests/adversarial_handoffs.json (100 samples, seed=43)
**Purpose**: Edge cases to stress-test PHI detection patterns

### Adversarial Performance vs Standard

| Metric | Standard (500 samples) | Adversarial (100 samples) | Delta |
|--------|------------------------|---------------------------|-------|
| Recall | 77.9% | 80.1% | +2.2% |
| Precision | 66.3% | 69.4% | +3.1% |
| F2 Score | 75.3% | 77.7% | +2.4% |
| PHI Leaks | 369 leaks | 31 leaks | Better on adversarial |

**Analysis**: Adversarial dataset shows slightly better performance, likely because:
1. Smaller sample size (100 vs 500) reduces statistical noise
2. Focused edge case templates may avoid certain common false negatives
3. Different entity type distribution

### Adversarial Per-Entity Performance

| Entity Type | Standard Recall | Adversarial Recall | Gap | Notes |
|-------------|-----------------|--------------------|----|-------|
| EMAIL_ADDRESS | 100.0% | 100.0% | 0% | Perfect detection maintained |
| PERSON | 98.8% | 100.0% | +1.2% | No missed persons in adversarial |
| PHONE_NUMBER | 73.9% | 86.7% | +12.8% | Improved on edge cases |
| MEDICAL_RECORD_NUMBER | 70.9% | 90.0% | +19.1% | Significant improvement |
| DATE_TIME | 96.8% | 69.2% | -27.6% | **DEGRADED** - edge case weakness |
| PEDIATRIC_AGE | 36.6% | 25.0% | -11.6% | **DEGRADED** - critical weakness |
| ROOM | 34.4% | 18.8% | -15.6% | **DEGRADED** - critical weakness |
| LOCATION | 19.4% | 100.0% | +80.6% | Huge improvement (only 1 expected) |

### Edge Case Categories Analysis

Based on adversarial dataset construction (6 categories, 100 samples):

| Category | Template Count | Recall | Critical Failures |
|----------|----------------|--------|-------------------|
| Speech Artifacts | ~17 | ~80% | Stuttered words, fillers mishandled |
| Diverse Names | ~17 | ~100% | PERSON detection robust |
| Boundary Edges | ~17 | ~70% | ROOM/AGE at start/end missed |
| Transcription Errors | ~17 | ~75% | Misspellings break patterns |
| Compound Patterns | ~17 | ~60% | Complex multi-word entities fail |
| Age Edges | ~15 | ~25% | **CRITICAL** - Abbreviations (17yo, 22mo) missed |

### Priority Gaps for Phase 4

Based on adversarial dataset failures (31 PHI leaks across 100 samples):

1. **PEDIATRIC_AGE abbreviation patterns (25% recall)**
   - Missing: "17yo", "4 yo", "8yo", "22mo", "15yo", "19 month old"
   - Impact: 9 of 12 age entities missed in adversarial dataset
   - Root cause: Patterns only match full word forms "years old", "months old"
   - Fix: Add abbreviation patterns to pediatric_age_recognizer.py

2. **ROOM single-digit and multi-part identifiers (19% recall)**
   - Missing: "Bay 3", "910", "8", "bed 9", "4-11", "bay 15", "isolette 35"
   - Impact: 13 of 16 room entities missed in adversarial dataset
   - Root cause: Patterns require "Room X" format, miss standalone numbers and unit prefixes
   - Fix: Expand room_recognizer.py patterns for "bed X", "bay X", "isolette X", standalone digits

3. **PHONE_NUMBER international formats (87% recall)**
   - Missing: "001-359-886-6201", "+1-496-268-9139", "594.480.2422", "001-885-221-6484x1298"
   - Impact: 4 of 30 phone entities missed
   - Root cause: Some international prefixes and dot separators not covered
   - Fix: Expand phone number regex patterns

4. **DATE_TIME partial dates (69% recall)**
   - Missing: "January 04", "January 21", "January 09", "January 08"
   - Impact: 4 of 13 date entities missed
   - Root cause: Month+day without year not detected
   - Fix: Add partial date patterns to datetime detection

5. **MEDICAL_RECORD_NUMBER bare numbers (90% recall)**
   - Missing: "7018128" (single 7-digit MRN without label)
   - Impact: 1 of 10 MRN entities missed
   - Fix: Add bare number pattern with length constraints (7-8 digits)

## Critical Gaps Analysis

### Weakest Performers (Recall <80%)

#### 1. LOCATION: 19.4% recall (standard) / 100% recall (adversarial)
**Standard dataset issues:**
- 104 false negatives out of 129 expected entities
- Only 25 true positives detected
- Misses: City names ("Daviston", "Port Eric", "Maldonadoport"), hospital names ("Memorial Hospital", "General Hospital", "University Medical Center"), addresses ("6270 Stanton Track", "703 Dunn Heights Suite 710")

**Why adversarial performed better:**
- Only 1 LOCATION entity in entire adversarial dataset
- Not a reliable indicator - insufficient test coverage

**Root cause:**
- spaCy NER misses generic hospital names (deny list doesn't help here)
- Street addresses with suite numbers often only partially detected
- City names without context words not recognized

#### 2. PEDIATRIC_AGE: 36.6% recall (standard) / 25.0% recall (adversarial)
**Systematic failures:**
- 104 false negatives in standard dataset (out of 164 expected)
- 9 false negatives in adversarial dataset (out of 12 expected)
- Abbreviation forms completely missed: "4yo", "17yo", "12mo", "22mo"
- Verbose forms with spaces missed: "4 yo", "2 yo", "3 yo"
- "Day of life" forms missed: "DOL 6", "DOL 2", "day of life 7"
- Specific numeric forms missed: "13 years old", "16 months old", "22 month old"

**Root cause:**
- Current patterns in pediatric_age_recognizer.py too narrow
- Only catches format like "[digit]+ (years?|months?|days?) old"
- Missing abbreviation patterns (yo, mo) and "DOL" clinical shorthand

#### 3. ROOM: 34.4% recall (standard) / 18.8% recall (adversarial)
**Systematic failures:**
- 59 false negatives in standard dataset (out of 90 expected)
- 13 false negatives in adversarial dataset (out of 16 expected)
- Multi-part formats missed: "3-22", "5-34", "2-25", "4-11"
- Unit-prefixed formats missed: "Bay 10", "Bay 5", "bed 14", "isolette 21"
- Standalone numbers missed: "512", "937", "711", "335", "5", "8"
- Capitalization variants missed: "Bed 14" vs "bed 14"

**Root cause:**
- Current patterns in room_recognizer.py only match "Room [number]" format
- Missing patterns for clinical unit formats (bed, bay, isolette, pod)
- No standalone digit detection (risk of false positives, but needed for recall)

### Root Causes Summary

1. **Regex lookbehind patterns only catch "Mom Jessica", miss "Jessica is Mom"**
   - Applies to: PERSON, GUARDIAN_NAME patterns
   - Impact: Moderate - most persons detected via spaCy NER

2. **Deny list case sensitivity inconsistent**
   - PERSON deny list: case-insensitive (correctly filters "mom", "Mom", "MOM")
   - LOCATION deny list: exact match (misses "NC" in different contexts)
   - Impact: Low - minor edge cases

3. **Detection threshold (0.35) and validation threshold (0.7) not calibrated**
   - Current values arbitrary, not data-driven
   - Impact: Unknown - Phase 2 will measure via precision-recall curves

4. **Pattern coverage gaps**
   - PEDIATRIC_AGE: Missing abbreviations, DOL format, space variations
   - ROOM: Missing unit prefixes, multi-part formats, standalone digits
   - Impact: Critical - 64-66% of age/room entities missed

## Test Suite Status

**Tests Passing**: 23/36
**Tests Failing**: 13/36

### Failing Tests (13 total)

#### Unit Tests (2 failures)
1. `test_catches_mrn_with_label` - MRN with label prefix not detected
2. `test_minimal_phi_transcript` - Over-redacting clinical abbreviations

#### Sample Transcript Tests (5 failures)
3. `test_sample_transcript[transcript_2]` - Multiple PHI leaks in realistic handoff
4. `test_sample_transcript[transcript_4]` - Room numbers and ages missed
5. `test_sample_transcript[transcript_5]` - Hospital names and phone numbers missed
6. `test_transcript_1_names_and_phone` - Expected output validation failed
7. `test_transcript_2_mrn` - MRN detection expected output mismatch

#### Bulk Dataset Tests (6 failures)
8. `test_bulk_person_detection` - Missed persons in bulk test (9 FN out of 756)
9. `test_bulk_phone_detection` - Missed phone numbers (50 FN out of 192)
10. `test_bulk_mrn_detection` - Missed MRNs (37 FN out of 127)
11. `test_bulk_location_detection` - Missed locations (104 FN out of 129)
12. `test_full_dataset_recall` - Overall recall below 95% target (77.9% actual)
13. `test_precision_not_too_low` - Precision below 70% target (66.3% actual)

### Test Failure Impact

- **23 passing tests**: Basic detection works for common cases
- **13 failing tests**: Edge cases and bulk validation expose systematic weaknesses
- **Primary concern**: Recall target (95%) missed by 17.1 percentage points
- **Secondary concern**: Precision target (70%) missed by 3.7 percentage points

## Known Limitations

1. **Synthetic-only validation**: Dataset is programmatically generated from 50 templates, not from real transcripts
   - Impact: May not represent actual clinical language patterns
   - Mitigation: Adversarial dataset (01-03) adds edge case coverage
   - Resolution: Phase 5 validation on real transcripts

2. **Template diversity**: 50 unique templates may not cover all clinical scenarios
   - Impact: Unknown clinical patterns may have different performance
   - Mitigation: Adversarial dataset provides 100 additional edge cases
   - Resolution: Expand template library in future work

3. **Human annotation deferred**: MEAS-02 (human-annotated gold standard) deferred to Phase 5
   - Impact: Cannot validate against expert clinical judgment yet
   - Rationale: Real transcript annotation requires IRB coordination (out of scope for Phase 1)
   - Resolution: Phase 5 will coordinate IRB approval and expert annotation

4. **Limited name diversity**: Faker library defaults may not represent diverse patient populations
   - Impact: May over-perform on Western names, under-perform on non-Western names
   - Mitigation: Adversarial dataset includes international name patterns
   - Resolution: Expand name templates with diverse cultural backgrounds

5. **Threshold not calibrated**: Detection threshold (0.35) and validation threshold (0.7) set arbitrarily
   - Impact: Unknown - may be sub-optimal for precision/recall tradeoff
   - Rationale: Phase 1 focuses on measurement, Phase 2 focuses on calibration
   - Resolution: Phase 2 will generate precision-recall curves and optimize thresholds

6. **No multi-token entity handling**: Current patterns assume single-token or simple multi-word entities
   - Impact: Complex entities like "Mom Jessica at Memorial Hospital" may only partially redact
   - Mitigation: Lookbehind patterns help preserve context words
   - Resolution: Phase 4 pattern improvements will address multi-token cases

7. **Case sensitivity inconsistencies**: Some deny lists case-insensitive, others exact match
   - Impact: Minor edge cases where "NC" (nasal cannula) vs "nc" handled differently
   - Resolution: Phase 3 deny list refinement will standardize case handling

## Improvement Roadmap

Based on baseline analysis:

### Phase 2: Threshold Calibration (precision-recall curves)
- Generate precision-recall curves for detection threshold (currently 0.35)
- Generate precision-recall curves for validation threshold (currently 0.7)
- Identify optimal operating point for clinical use case (balance HIPAA compliance with utility)
- Expected impact: +5-10% precision, +2-5% recall

### Phase 3: Deny List Refinement
- Standardize case normalization (all deny lists case-insensitive)
- Expand medical abbreviation deny list (NC, RA, OR, IV, PO, etc.)
- Add clinical context patterns to preserve essential medical terms
- Expected impact: +3-5% precision (fewer false positives on medical terms)

### Phase 4: Pattern Improvements
**Priority 1: PEDIATRIC_AGE patterns**
- Add abbreviation patterns: "Xyo", "Xmo", "X yo", "X mo"
- Add "DOL X" and "day of life X" patterns
- Add verbose forms with flexible spacing
- Expected impact: +40-50% recall for PEDIATRIC_AGE

**Priority 2: ROOM patterns**
- Add unit prefix patterns: "bed X", "bay X", "isolette X", "pod X"
- Add multi-part formats: "X-Y", "X/Y"
- Add standalone 1-3 digit detection (with context constraints to avoid false positives)
- Handle capitalization variants
- Expected impact: +40-50% recall for ROOM

**Priority 3: PHONE_NUMBER patterns**
- Expand international prefix patterns
- Add dot separator support ("XXX.XXX.XXXX")
- Add extension variations ("xXXXXX", "ext XXXXX")
- Expected impact: +10-15% recall for PHONE_NUMBER

**Priority 4: LOCATION patterns**
- Add hospital name patterns (Memorial Hospital, General Hospital, etc.)
- Improve address detection for multi-part addresses with suites
- Add city name context patterns
- Expected impact: +30-40% recall for LOCATION

### Phase 5: Validation on Real Transcripts
- Coordinate IRB approval for real transcript access
- Expert clinical annotation of PHI in real handoffs
- Re-run evaluation on human-annotated gold standard
- Measure performance on actual clinical language patterns
- Expected outcome: Defensible evidence for research publication and clinical deployment

## Raw Data References

**Evaluation commands:**
```bash
# Full evaluation report (verbose)
python tests/evaluate_presidio.py --verbose

# JSON metrics for programmatic access
python tests/evaluate_presidio.py --json

# Confusion matrix export
python tests/evaluate_presidio.py --export-confusion-matrix confusion.json

# Adversarial dataset evaluation
python tests/evaluate_presidio.py --input tests/adversarial_handoffs.json --verbose
```

**Dataset files:**
- Standard dataset: `tests/synthetic_handoffs.json` (500 samples, seed=42)
- Adversarial dataset: `tests/adversarial_handoffs.json` (100 samples, seed=43)
- Test suite: `tests/test_deidentification.py` (36 tests)

**Configuration files:**
- Detection thresholds: `app/config.py` (Settings class)
- Deny lists: `app/config.py` (LOCATION_DENY_LIST, PERSON_DENY_LIST)
- Custom recognizers: `app/recognizers/` (pediatric.py, medical.py)

---
*Baseline captured before any PHI detection improvements.*
*Next step: Phase 2 (Threshold Calibration)*
