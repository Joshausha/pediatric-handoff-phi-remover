# Codebase Structure

**Analysis Date:** 2026-01-23

## Directory Layout

```
pediatric-handoff-phi-remover/
├── app/                        # Backend application code
│   ├── __init__.py
│   ├── main.py                 # FastAPI application, route handlers
│   ├── config.py               # Pydantic settings, environment configuration
│   ├── transcription.py        # Whisper transcription service
│   ├── deidentification.py     # Presidio de-identification pipeline
│   ├── audit.py                # HIPAA-compliant audit logging
│   └── recognizers/            # Custom PHI pattern recognizers
│       ├── __init__.py
│       ├── pediatric.py        # Guardian names, baby names, pediatric ages
│       └── medical.py          # MRN patterns, room/bed numbers
├── static/                     # Frontend web application
│   ├── index.html              # Main HTML page
│   ├── app.js                  # Client-side JavaScript logic
│   └── styles.css              # Frontend styling
├── tests/                      # Test suite and utilities
│   ├── __init__.py
│   ├── test_deidentification.py # PHI de-identification test cases
│   ├── sample_transcripts.py   # Real medical handoff samples
│   ├── medical_providers.py    # Provider data for testing
│   ├── handoff_templates.py    # Handoff format templates
│   ├── synthetic_handoffs.json # Pre-generated test data
│   ├── generate_test_data.py   # Faker-based test data generator
│   └── evaluate_presidio.py    # Presidio performance evaluator
├── docs/                       # Documentation
│   ├── API.md                  # API endpoint reference
│   ├── HIPAA_COMPLIANCE.md     # HIPAA compliance details
│   └── ...
├── scripts/                    # Utility scripts
│   └── (deployment/setup scripts)
├── .github/                    # GitHub CI/CD
│   └── workflows/
│       └── test.yml            # GitHub Actions test pipeline
├── logs/                       # Runtime audit logs (created at runtime)
│   └── audit.log               # HIPAA-compliant audit events
├── pyproject.toml              # Python project metadata, tool configuration
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── .env                        # Environment variables (local dev, gitignored)
├── .env.example                # Template for environment variables
├── Dockerfile                  # Docker container specification
├── README.md                   # Project overview
├── PROJECT_STATUS.md           # Implementation status and completion tracking
└── CLAUDE.md                   # Project-specific Claude instructions
```

## Directory Purposes

**app/**
- Purpose: All backend application logic
- Contains: FastAPI routes, transcription service, de-identification pipeline, configuration, audit logging
- Key files: `main.py` (entry point), `config.py` (settings)

**app/recognizers/**
- Purpose: Custom Presidio recognizers for domain-specific PHI patterns
- Contains: Pediatric patterns (guardian names, baby names, ages), medical patterns (MRN, room numbers)
- Pattern: Each module exports `get_pediatric_recognizers()` or `get_medical_recognizers()` functions

**static/**
- Purpose: Frontend web application served at `/`
- Contains: HTML interface for audio upload, JavaScript request handling, CSS styling
- Key files: `index.html` (main page), `app.js` (request logic)

**tests/**
- Purpose: Test suite for PHI de-identification and transcription
- Contains: Unit tests, sample transcripts, test data generators, evaluation tools
- Key files: `test_deidentification.py` (main test suite), `sample_transcripts.py` (medical samples)

**docs/**
- Purpose: Project documentation
- Contains: API documentation, HIPAA compliance guide, architecture notes
- Key files: `API.md` (endpoint reference), `HIPAA_COMPLIANCE.md` (compliance details)

**scripts/**
- Purpose: Utility and deployment scripts
- Contains: Database setup, model download, deployment helpers
- Usage: `python scripts/setup.py` (first-time setup)

**logs/**
- Purpose: Runtime audit logs (created dynamically at startup)
- Contains: HIPAA-compliant audit events in JSON format
- Key file: `audit.log` (one entry per request, no PHI stored)

## Key File Locations

**Entry Points:**
- `app/main.py`: FastAPI application with route handlers (lines 195-203 for app initialization)
- `static/index.html`: Frontend page served at `/`

**Configuration:**
- `app/config.py`: All settings with environment variable overrides
- `.env`: Local environment variables (gitignored)
- `.env.example`: Template showing all available variables
- `pyproject.toml`: Tool configuration (ruff, pytest, bandit)
- `pytest.ini`: Pytest runner settings

**Core Logic:**
- `app/transcription.py`: Whisper transcription service with lazy model loading
- `app/deidentification.py`: Presidio de-identification pipeline with validation
- `app/recognizers/pediatric.py`: Pediatric-specific PHI patterns (guardian names, baby names, ages)
- `app/recognizers/medical.py`: Medical PHI patterns (MRN, room numbers)
- `app/audit.py`: HIPAA-compliant audit event logging

**Testing:**
- `tests/test_deidentification.py`: Main test suite (21+ test cases)
- `tests/sample_transcripts.py`: Real pediatric handoff excerpts for testing
- `tests/generate_test_data.py`: Synthetic handoff generator using Faker
- `tests/evaluate_presidio.py`: Presidio performance metrics

## Naming Conventions

**Files:**
- Snake case for Python files: `app/transcription.py`, `tests/test_deidentification.py`
- Kebab case for markdown: `PROJECT_STATUS.md`, `HIPAA_COMPLIANCE.md`
- Lowercase for static assets: `static/app.js`, `static/styles.css`

**Directories:**
- Lowercase plural for collections: `app/`, `tests/`, `docs/`, `scripts/`, `logs/`
- Lowercase with underscores for multi-word: `app/recognizers/`

**Python Functions:**
- Snake case: `transcribe_audio()`, `deidentify_text()`, `validate_deidentification()`
- Internal helpers prefixed with underscore: `_clean_transcript()`, `_mask_text_preview()`

**Python Classes:**
- Pascal case: `Settings`, `DeidentificationResult`, `EntityInfo`, `AuditEvent`
- Route handler functions named after action: `process_audio()`, `deidentify_only()`, `transcribe_only()`

**HTTP Endpoints:**
- Kebab case in paths: `/api/process`, `/api/deidentify`, `/api/transcribe`, `/api/estimate-time`
- Root path is just `/` for frontend
- Health check at `/health`

## Where to Add New Code

**New Feature (e.g., speaker identification, language detection):**
- Primary code: Create new module in `app/` following existing pattern (e.g., `app/speaker_detection.py`)
- Import and integrate: Add to pipeline in `app/main.py:process_audio()` or new route handler
- Tests: Add test cases to `tests/test_deidentification.py` or create new test file
- Config: Add settings to `app/config.py` if configurable

**New Custom Recognizer (e.g., social security numbers):**
- Implementation: Add function in `app/recognizers/medical.py` or create `app/recognizers/additional.py`
- Pattern: Follow existing pattern in `get_medical_recognizers()` - return list of `PatternRecognizer` objects
- Integration: Add to `deidentification.py:_get_engines()` call at lines 102-108
- Testing: Add pattern test case to `tests/test_deidentification.py`

**New HTTP Endpoint (e.g., batch processing):**
- Implementation: Add route handler to `app/main.py` with `@app.post()` or `@app.get()` decorator
- Model: Define Pydantic request/response model at top of file (lines 85-111 show examples)
- Documentation: Add OpenAPI tags and docstring for automatic API docs at `/docs`
- Logging: Call `audit_logger.log_request_*()` methods for HIPAA compliance
- Rate limiting: Add `@limiter.limit()` decorator if needed

**Testing Utilities:**
- Test data: Add samples to `tests/sample_transcripts.py` or `tests/synthetic_handoffs.json`
- Generators: Extend `tests/generate_test_data.py` for new test data types
- Evaluation: Add metrics to `tests/evaluate_presidio.py`

**Configuration Addition:**
- Settings field: Add to `Settings` class in `app/config.py` with `Field()` and description
- Default value: Provide sensible default
- Environment variable: Automatically supported via Pydantic (snake_case → SNAKE_CASE)
- .env template: Document in `.env.example`

## Special Directories

**static/**
- Purpose: Frontend web application (served by FastAPI)
- Generated: No, manually maintained
- Committed: Yes
- Handling: Mounted at `/static` route, root `/` serves index.html

**logs/**
- Purpose: Runtime audit logs
- Generated: Yes, created at startup if directory doesn't exist
- Committed: No (gitignored)
- Path: `logs/audit.log` (configurable via `AUDIT_LOG_FILE` env var)
- Format: JSON, one event per line

**/tmp/handoff-transcriber/**
- Purpose: Temporary audio file storage during transcription
- Generated: Yes, created during transcription
- Committed: No (system temp directory)
- Cleanup: Automatic via finally block in `transcribe_audio()`
- Path: Configurable via `TEMP_DIR` env var (default `/tmp/handoff-transcriber`)

**venv/**
- Purpose: Python virtual environment
- Generated: Yes, via `python -m venv venv`
- Committed: No (gitignored)
- Activation: `source venv/bin/activate` (macOS/Linux)

**.venv/**
- Purpose: Alternative virtual environment location (for IDE compatibility)
- Generated: Optional, via `python -m venv .venv`
- Committed: No (gitignored)

**tests/__pycache__/** and **app/__pycache__/**
- Purpose: Python bytecode cache
- Generated: Yes, automatically by Python
- Committed: No (gitignored)
- Impact: Safe to delete, regenerated on import

---

*Structure analysis: 2026-01-23*
