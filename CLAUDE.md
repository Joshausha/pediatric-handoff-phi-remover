# Pediatric Handoff PHI Remover - Claude Code Configuration

**Johnny Decimal ID**: 12.09
**Type**: Development (HIPAA-compliant medical tool)
**Last Updated**: 2026-01-21

## Project Context

HIPAA-compliant web application that transcribes pediatric patient handoff recordings and removes all Protected Health Information (PHI) before displaying the transcript. All processing happens locally—no patient data ever leaves the user's machine.

## Project Status

- **Backend**: Complete (FastAPI + faster-whisper + Presidio)
- **Frontend**: Complete (HTML/CSS/JS with recording + upload)
- **PHI Detection**: Refined and tested (21/21 tests passing)
- **Tested**: Successfully processed 27-minute handoff recording

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
# Run Presidio test harness (fast, no audio)
python test_presidio.py

# Interactive Presidio testing
python test_presidio.py -i

# Run full test suite
pytest tests/ -v

# Start development server
uvicorn app.main:app --reload

# Download spacy model (first time setup)
python -m spacy download en_core_web_lg
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

## PHI Entity Types

**Standard Presidio**: `PERSON`, `PHONE_NUMBER`, `EMAIL_ADDRESS`, `DATE_TIME`, `LOCATION`

**Custom pediatric** (using lookbehind patterns to preserve context):
- `GUARDIAN_NAME` - "Mom [NAME]", "Dad [NAME]" (preserves relationship word)
- `PERSON` - "Baby [NAME]", "Infant [NAME]" (preserves descriptor)
- `MEDICAL_RECORD_NUMBER` - MRN patterns including `#12345678`
- `ROOM` - Room/bed numbers (preserves unit names like PICU/NICU)
- `PEDIATRIC_AGE` - Detailed ages like "3 weeks 2 days old"

## Deny Lists

Medical abbreviations that should NOT be flagged as PHI:
- **LOCATION deny list**: NC, RA, OR, ER, ED, IV, PO, IM, SQ, PR, GT, NG, OG, NJ
- **PERSON deny list**: mom, dad, parent, guardian, nurse, doctor, attending, resident, fellow, NP, PA, RN

## Recent Improvements (2026-01-21)

1. **Baby LastName detection** - Added patterns for "Baby Smith", "Infant Jones"
2. **Guardian name preservation** - "Dad Mike" → "Dad [NAME]" (keeps relationship word)
3. **Medical abbreviation filtering** - NC (nasal cannula) no longer flagged as location
4. **Standalone relationship words** - "Contact mom" no longer flagged as person name
5. **MRN hash pattern** - "#12345678" now detected
6. **Unit name preservation** - "PICU bed 12" → "PICU bed [ROOM]"
7. **30-minute timeout** - Frontend handles long audio files
