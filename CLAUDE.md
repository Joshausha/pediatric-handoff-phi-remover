# Pediatric Handoff PHI Remover - Claude Code Configuration

**Johnny Decimal ID**: 12.09
**Type**: Development (HIPAA-compliant medical tool)
**Last Updated**: 2026-01-18

## Project Context

HIPAA-compliant web application that transcribes pediatric patient handoff recordings and removes all Protected Health Information (PHI) before displaying the transcript. All processing happens locally—no patient data ever leaves the user's machine.

## Critical Rules

- **NEVER** make external API calls with any text that might contain PHI
- **ALWAYS** use faster-whisper for transcription (local only)
- **ALWAYS** run Presidio de-identification before displaying any transcript
- When uncertain if something is PHI, treat it as PHI and remove it
- Audio files should never be committed to git

## Code Style

- Use Python type hints for all function signatures
- Use dataclasses or Pydantic models for structured data
- Include docstrings for all public functions
- Log all major operations (transcription start/end, PHI detection counts)

## Testing

```bash
# Run tests
pytest tests/ -v

# Start development server
uvicorn app.main:app --reload

# Download spacy model (first time setup)
python -m spacy download en_core_web_lg
```

## Key Files

| File | Purpose |
|------|---------|
| `app/config.py` | Pydantic settings, environment variables |
| `app/transcription.py` | Whisper audio-to-text |
| `app/deidentification.py` | Presidio PHI removal |
| `app/recognizers/pediatric.py` | Custom recognizers for guardian names, ages |
| `app/main.py` | FastAPI application |
| `static/` | Frontend HTML/CSS/JS |

## PHI Entity Types

Standard Presidio: `PERSON`, `PHONE_NUMBER`, `EMAIL_ADDRESS`, `DATE_TIME`, `LOCATION`

Custom pediatric:
- `GUARDIAN_NAME` - "Mom Jessica", "Dad Mike"
- `MEDICAL_RECORD_NUMBER` - MRN patterns
- `ROOM` - Room numbers, PICU/NICU beds
- `PEDIATRIC_AGE` - Detailed ages like "3 weeks 2 days old"
