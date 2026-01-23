---
type: project-status
title: PROJECT_STATUS.md - Pediatric Handoff PHI Remover
project_id: "12.09"
project_name: Pediatric_Handoff_PHI_Remover
status: active
health: on-track
created: 2026-01-18
modified: 2026-01-22
next_review: 2026-01-29
tags: [project-status, development, hipaa, phi, transcription, pediatrics]
category: Projects
project_type: development
complexity: medium
---

## Quick Summary

Web application for transcribing pediatric handoff recordings with automatic PHI de-identification. All processing local—no cloud APIs with patient data.

**Current Phase**: Security Hardening & Deployment Prep
**Health**: On Track
**Next Milestone**: Hospital network deployment readiness
**Blockers**: None

## Completed ✅

- [x] Core transcription pipeline (faster-whisper)
- [x] PHI de-identification (Presidio + custom recognizers)
- [x] Pediatric-specific recognizers (guardian names, baby names, ages, MRNs, room numbers)
- [x] Frontend with recording + upload
- [x] 21/21 Presidio tests passing
- [x] Successfully tested on 27-minute recording
- [x] Medical abbreviation deny lists (NC, RA, etc.)

## In Progress

- [ ] Security hardening (CORS, rate limiting, audit logging)
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Deployment documentation

## Next Actions

1. ~~Complete transcription module~~ ✓
2. ~~Implement custom recognizers~~ ✓
3. ~~Build FastAPI endpoints~~ ✓
4. ~~Create frontend interface~~ ✓
5. ~~Test with sample transcripts~~ ✓
6. **Security hardening** (CORS, rate limiting, audit logging)
7. **Docker deployment** (Dockerfile, docker-compose)
8. **CI/CD** (GitHub Actions)
9. **Hospital IT documentation**

## Architecture

```
Audio → faster-whisper (local) → Raw transcript → Presidio → Clean transcript
                                                       ↓
                                             Custom recognizers:
                                             - Guardian names (Mom [NAME])
                                             - Baby names (Baby [NAME])
                                             - MRN patterns (#12345678)
                                             - Room numbers (PICU bed [ROOM])
                                             - Pediatric ages ([PEDIATRIC_AGE])

                                             Deny lists:
                                             - Medical abbreviations (NC, RA, OR...)
                                             - Relationship words (mom, dad, nurse...)
```

## Key Files

| File | Purpose |
|------|---------|
| `app/config.py` | Pydantic settings, deny lists, PHI thresholds |
| `app/transcription.py` | Whisper audio-to-text |
| `app/deidentification.py` | Presidio PHI removal with deny list filtering |
| `app/recognizers/pediatric.py` | Guardian names, baby names, pediatric ages |
| `app/recognizers/medical.py` | MRN patterns, room numbers |
| `app/main.py` | FastAPI application |
| `static/` | Frontend HTML/CSS/JS |
| `test_presidio.py` | Isolated Presidio test harness (21 test cases) |

## Notes

See CLAUDE.md for detailed development context.
GitHub: https://github.com/Joshausha/pediatric-handoff-phi-remover
