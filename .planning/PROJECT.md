# PHI Detection Overhaul

## What This Is

A comprehensive quality improvement project to strengthen PHI detection in the Pediatric Handoff PHI Remover. Addresses regex edge cases, inconsistent deny list logic, and uncalibrated score thresholds identified in codebase analysis. Success measured by precision/recall metrics against a 500-transcript synthetic corpus.

## Core Value

Reliable PHI detection with balanced precision/recall — catch all PHI without over-redacting clinically useful content.

## Requirements

### Validated

<!-- Existing functionality that's working and relied upon -->

- ✓ Core transcription pipeline (faster-whisper) — existing
- ✓ Presidio de-identification integration — existing
- ✓ Guardian name detection ("Mom [NAME]", "Dad [NAME]") — existing
- ✓ Baby name detection ("Baby [NAME]", "Infant [NAME]") — existing
- ✓ MRN pattern detection (including #12345678) — existing
- ✓ Room/bed number detection with unit preservation — existing
- ✓ Pediatric age detection — existing
- ✓ Medical abbreviation deny lists (NC, RA, OR, etc.) — existing
- ✓ Security hardening (CORS, rate limiting, audit logging) — existing
- ✓ Docker deployment with health checks — existing
- ✓ CI/CD pipeline (GitHub Actions) — existing

### Active

<!-- Current scope for this milestone -->

- [ ] Establish baseline precision/recall metrics against synthetic corpus
- [ ] Fix regex lookbehind edge cases (lowercase, reversed patterns like "Jessica is Mom")
- [ ] Standardize deny list comparison logic (case-insensitive across all entity types)
- [ ] Calibrate detection threshold (currently 0.35) against corpus data
- [ ] Calibrate validation threshold (currently 0.7) with clear rationale
- [ ] Add regression tests for each fixed edge case
- [ ] Document threshold calibration methodology
- [ ] Achieve measurable improvement in precision/recall metrics

### Out of Scope

<!-- Explicit boundaries for this milestone -->

- Performance optimizations (model loading, Presidio scan efficiency) — separate concern, not PHI accuracy
- Additional security hardening (XSS, CSP, path traversal) — separate milestone
- Test coverage for non-PHI paths (concurrency, large files, error handling) — separate milestone
- New features (speaker diarization, batch processing, GPU support) — future enhancement
- Unicode/international name support — low priority for pediatric handoffs

## Context

**Data available:**
- 500 synthetic transcripts generated via Presidio research script (tests/evaluate_presidio.py)
- Real PHI-free recordings used during development (no actual PHI present)

**Setting:**
- Research/QI project — metrics provide defensible evidence of improvement
- Preemptive cleanup before hospital pilot deployment
- Potential for publication as QI poster/paper

**Known issues from codebase analysis:**
- Lookbehind patterns only catch "Mom Jessica", miss "Jessica is Mom" and "mom jessica"
- PERSON deny list: case-insensitive; LOCATION deny list: exact match — inconsistent
- Detection threshold (0.35) and validation threshold (0.7) set arbitrarily, no calibration

## Constraints

- **Trade-off**: Balanced — minimize both false positives (over-redaction) and false negatives (PHI leaks)
- **HIPAA**: All changes must maintain compliance; when uncertain, treat as PHI
- **Testability**: Every fix must have corresponding regression test
- **Documentation**: Threshold choices must be justified with data

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Metrics-based success criteria | Research setting needs defensible evidence; 500 synthetic transcripts enable measurement | — Pending |
| Balanced precision/recall trade-off | Clinical utility requires readable transcripts; pure aggressive approach over-redacts | — Pending |
| Case-insensitive deny lists | Consistency prevents edge case bugs; clinical terms appear in various cases | — Pending |

---
*Last updated: 2026-01-23 after initialization*
