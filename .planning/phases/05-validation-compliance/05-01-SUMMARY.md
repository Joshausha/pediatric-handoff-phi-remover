---
phase: 05-validation-compliance
plan: 01
subsystem: validation
tags: [presidio, validation, annotation, dataset, external-validation]

# Dependency graph
requires:
  - phase: 04-pattern-improvements
    provides: Improved PHI detection patterns tested on synthetic data
provides:
  - ValidationHandoff class compatible with PresidioEvaluator
  - Annotation schema for human PHI labeling
  - Stratified sampling infrastructure for real transcript validation
  - Dataset configuration for 200-sample validation target
affects: [05-02, 05-03, validation, compliance]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ValidationHandoff with phi_spans property for PresidioEvaluator compatibility"
    - "Stratified sampling by dominant PHI type distribution"
    - "Annotation schema compatible with Presidio entity types"

key-files:
  created:
    - tests/annotation_schema.py
    - tests/validation_dataset.py
    - .planning/phases/05-validation-compliance/datasets/validation_config.json
  modified: []

key-decisions:
  - "Target sample size: 200 transcripts (minimum viable: 50)"
  - "Stratification by dominant PHI type to preserve entity distribution"
  - "70/30 val/test split (no training - using existing model)"
  - "Single annotator acceptable (target IAA kappa >0.8 for double-coded subset)"

patterns-established:
  - "ValidationHandoff.phi_spans property returns list[PHISpan] for evaluator compatibility"
  - "PHIAnnotation extends AnnotationSchema with validation metadata"
  - "stratified_sample() function preserves PHI type distribution across validation sets"

# Metrics
duration: 3min
completed: 2026-01-24
---

# Phase 05 Plan 01: Validation Data Pipeline Summary

**Validation dataset infrastructure with annotation schema, PHISpan compatibility, and stratified sampling for 200-transcript external validation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-24T16:17:29Z
- **Completed:** 2026-01-24T16:20:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Annotation schema with 9 Presidio-compatible PHI entity types and validation guidelines
- ValidationHandoff class with phi_spans property returning PHISpan objects (PresidioEvaluator-compatible)
- Stratified sampling by dominant PHI type distribution for balanced validation sets
- Dataset configuration targeting 200 transcripts with 70/30 val/test split

## Task Commits

Each task was committed atomically:

1. **Task 1: Create annotation schema and validation dataset loader** - `0c43f5e` (feat)
2. **Task 2: Create validation dataset configuration** - `29f0675` (feat)

## Files Created/Modified
- `tests/annotation_schema.py` - PHI entity types, AnnotationSchema dataclass, validate_annotations function
- `tests/validation_dataset.py` - ValidationHandoff, PHIAnnotation, load_validation_set, export_for_annotation, stratified_sample
- `.planning/phases/05-validation-compliance/datasets/validation_config.json` - Sample size targets, stratification config, data sources
- `.planning/phases/05-validation-compliance/datasets/real_handoffs/.gitkeep` - Placeholder for real transcript data
- `.planning/phases/05-validation-compliance/datasets/annotated/.gitkeep` - Placeholder for annotated validation data

## Decisions Made

**ValidationHandoff compatibility approach:**
- Added `phi_spans` property that converts PHIAnnotation list to PHISpan list
- Enables direct use with `PresidioEvaluator.evaluate_handoff()` without wrapper code
- Maintains consistency with SyntheticHandoff interface

**Stratification strategy:**
- Stratify by dominant PHI type (most common entity in each handoff)
- Preserves entity type distribution from synthetic data to validation data
- Ensures coverage of all PHI types in smaller samples

**Sample size targets:**
- Target: 200 transcripts for narrow confidence intervals
- Minimum viable: 50 transcripts for initial validation
- Entity type targets specified for coverage tracking (e.g., 100 PERSON, 80 MRN)

**Annotation workflow:**
- Single expert annotator acceptable (clinician with PHI knowledge)
- 20% double-coded for IAA measurement (target kappa >0.8)
- export_for_annotation() function supports text-only initial annotation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all modules loaded successfully, PHISpan conversion verified.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 05-02 (Real Transcript Annotation):**
- Annotation schema documented with entity type definitions
- ValidationHandoff format specified for JSON serialization
- load_validation_set() ready to ingest annotated transcripts
- stratified_sample() ready to create balanced validation sets

**Data collection next:**
- Need to populate .planning/phases/05-validation-compliance/datasets/real_handoffs/
- Two sources configured: existing de-identified transcripts + IRB-approved prospective collection
- Annotation guidelines documented in ANNOTATION_GUIDELINES constant

**No blockers:**
- Infrastructure complete for validation pipeline
- Compatible with existing PresidioEvaluator framework
- Ready to begin real transcript collection and annotation

---
*Phase: 05-validation-compliance*
*Completed: 2026-01-24*
