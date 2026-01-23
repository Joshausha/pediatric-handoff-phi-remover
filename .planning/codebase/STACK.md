# Technology Stack

**Analysis Date:** 2026-01-23

## Languages

**Primary:**
- Python 3.9+ - Backend application, all business logic
  - Type hints required (enforced via ruff linter)
  - Async/await patterns for FastAPI endpoints
  - Dataclass and Pydantic models for structured data

**Frontend:**
- HTML/CSS/JavaScript - Frontend UI (no framework)
  - Located in `static/` directory
  - Handles audio recording, file upload, progress tracking

## Runtime

**Environment:**
- Python 3.9, 3.10, 3.11 (tested in CI matrix via GitHub Actions)
- Recommended: Python 3.11 for production (latest stable)

**Package Manager:**
- pip with requirements.txt
- Lockfile: requirements.txt (pinned versions for reproducibility)

**Dependency Caching:**
- GitHub Actions uses `cache: 'pip'` in workflow (`/.github/workflows/test.yml`)

## Frameworks

**Web/API:**
- FastAPI 0.109.2 - REST API framework with async support
  - Uses Uvicorn 0.27.1 as ASGI server
  - Security middleware for HIPAA compliance (security headers, CSP)
  - Rate limiting via slowapi (10 requests per 60 seconds default)
  - CORS configurable via environment variables

**Audio Processing:**
- faster-whisper >=1.0.0 - Local speech-to-text transcription
  - Uses OpenAI's Whisper model family
  - Models: tiny.en, base.en, small.en, medium.en (default), large-v3
  - Device support: CPU (int8) or GPU (float16)
  - Thread-safe lazy loading with global model cache

**PHI De-identification:**
- presidio-analyzer 2.2.354 - Named Entity Recognition for PHI detection
  - Standard entities: PERSON, PHONE_NUMBER, EMAIL_ADDRESS, DATE_TIME, LOCATION, US_SSN, MEDICAL_LICENSE, US_DRIVER_LICENSE
  - Custom entities: MEDICAL_RECORD_NUMBER, ROOM, GUARDIAN_NAME, PEDIATRIC_AGE
- presidio-anonymizer 2.2.354 - De-identification engine
  - Replacement strategies: type_marker (default), redact, mask
- spacy 3.7.4 - NLP engine for Presidio
  - Model: en_core_web_lg (used for NER)
  - Downloaded at build/startup time

**Configuration Management:**
- pydantic 2.6.1 - Settings validation
- pydantic-settings 2.1.0 - Environment variable binding
- python-dotenv 1.0.1 - .env file loading

## Key Dependencies

**Critical (PHI handling):**
- presidio-analyzer 2.2.354 - PHI entity detection, must be kept current for security
- presidio-anonymizer 2.2.354 - PHI removal, paired with analyzer version
- faster-whisper >=1.0.0 - Local audio transcription (no external APIs)
- spacy 3.7.4 - NLP engine, required for Presidio context

**Infrastructure:**
- uvicorn[standard] 0.27.1 - ASGI server with uvloop/httptools for performance
- fastapi 0.109.2 - Web framework with OpenAPI documentation
- python-multipart 0.0.9 - Multipart form data parsing for file uploads
- slowapi 0.1.9 - Rate limiting middleware

**Data Validation:**
- pydantic 2.6.1 - Model validation (BaseModel, BaseSettings)
- pydantic-settings 2.1.0 - Settings from environment

**Testing:**
- pytest >=7.0.0,<8.0.0 - Unit testing framework
- pytest-asyncio 0.23.4 - Async test support
- httpx 0.26.0 - HTTP client for testing FastAPI endpoints
- faker >=19.0.0 - Test data generation for PHI evaluation
- presidio-evaluator >=0.2.4 - Presidio evaluation metrics

## Configuration

**Environment Variables:**
- `.env` file loaded at runtime via python-dotenv
- See `app/config.py` for all configurable settings
- Key vars (can override defaults):
  - `WHISPER_MODEL` - Model size (default: medium.en)
  - `WHISPER_DEVICE` - Device type (default: cpu)
  - `WHISPER_COMPUTE_TYPE` - Inference type (default: int8)
  - `PHI_SCORE_THRESHOLD` - NER confidence threshold (default: 0.35)
  - `ENABLE_CUSTOM_RECOGNIZERS` - Enable pediatric/medical patterns (default: true)
  - `DEBUG` - Debug logging (default: false)
  - `MAX_AUDIO_SIZE_MB` - Max upload size (default: 50)
  - `CORS_ORIGINS` - Allowed origins (default: localhost:8000)
  - `ENABLE_AUDIT_LOGGING` - HIPAA audit logs (default: true)

**Build Configuration:**
- `pyproject.toml` - Ruff linter config (line-length=100, target-version=py39)
- `Dockerfile` - Python 3.11-slim base, ffmpeg system dependency
- `requirements.txt` - All pip dependencies with pinned versions

## Platform Requirements

**Development:**
- Python 3.9+ with pip
- ffmpeg (for audio processing) - installed at build time
- ~2GB RAM minimum (for spaCy model + Whisper model)
- 4+ GB disk space (Whisper medium.en + spaCy model cache)

**Production:**
- Deployment target: Docker container (multi-stage possible via Dockerfile)
- Docker image: python:3.11-slim + ffmpeg
- Non-root user `appuser` for security
- Port: 8000 (configurable in docker CMD)
- Health check endpoint: `/health` (30s interval, 60s startup grace period)

**System Dependencies:**
- ffmpeg - Required in both development and Docker for audio processing
- Installed via: `apt-get install ffmpeg` (Linux) or equivalent

## Build & Development

**Build Process:**
1. Copy requirements.txt
2. Install pip dependencies
3. Download spaCy model (`python -m spacy download en_core_web_lg`)
4. Copy application code
5. Create log and temp directories
6. Optional: Preload Whisper model via `scripts/preload_models.py`
7. Switch to non-root user
8. Expose port 8000

**Development Server:**
```bash
uvicorn app.main:app --reload
```
Runs on http://localhost:8000 with hot reload

**Testing:**
```bash
pytest tests/ -v              # Run all tests
python test_presidio.py       # Run Presidio harness (21 test cases)
ruff check app/ --ignore E501 # Linting
```

## Model Downloads

**Whisper Models (lazy-loaded on first request):**
- tiny.en: ~39MB
- base.en: ~140MB
- small.en: ~466MB
- medium.en: ~1.5GB (default)
- large-v3: ~2.9GB

**spaCy Model:**
- en_core_web_lg: ~745MB
- Downloaded during build: `python -m spacy download en_core_web_lg`
- Cached in Python site-packages

---

*Stack analysis: 2026-01-23*
