# External Integrations

**Analysis Date:** 2026-01-23

## APIs & External Services

**Audio Transcription:**
- OpenAI Whisper (via faster-whisper) - Speech-to-text
  - SDK/Client: faster-whisper Python package
  - Auth: Not applicable (models run locally)
  - Type: Local inference only (no API calls)
  - Models downloaded from Hugging Face on first use

**Named Entity Recognition (NER):**
- spaCy - Linguistic NER models
  - SDK/Client: spacy Python package
  - Model: en_core_web_lg (English large model)
  - Auth: Not applicable (open-source model)
  - Type: Local inference
  - Purpose: Powers Presidio's entity detection

**PHI De-identification:**
- Microsoft Presidio - NER and anonymization engine
  - SDK/Client: presidio-analyzer, presidio-anonymizer packages
  - Auth: Not applicable (open-source framework)
  - Type: Local inference with custom recognizers
  - Purpose: Detects and removes Protected Health Information
  - Custom recognizers: Medical (MRN, room numbers) and pediatric-specific (guardian names, ages)

## Data Storage

**Databases:**
- None - Application is stateless
- No persistent database required
- All processing is in-memory

**File Storage:**
- Local filesystem only (temporary)
  - Temp directory: `/tmp/handoff-transcriber` (configurable via `TEMP_DIR` env var)
  - Audio files written to temp during transcription
  - Files deleted immediately after processing
  - No permanent audit trail stored locally

**Caching:**
- In-memory model caching (application lifetime)
  - Whisper model cached globally after first load (`app/transcription.py`)
  - Presidio analyzer/anonymizer engines cached globally (`app/deidentification.py`)
  - Thread-safe caching using threading locks
  - Models NOT persisted between application restarts

## Authentication & Identity

**Auth Provider:**
- None - Application assumes local/trusted network deployment
- CORS restricted to configured origins (default: localhost only)
- No user authentication required
- No API keys or secrets

**Authorization:**
- Not applicable
- Rate limiting enforced per IP address (10 requests per 60 seconds default)

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking service

**Logs:**
- Local HIPAA-compliant audit logging
  - Location: `logs/audit.log` (configurable via `AUDIT_LOG_FILE`)
  - Implementation: `app/audit.py`
  - Content: Request/response metadata, entity counts (no PHI stored)
  - HIPAA compliance: No Protected Health Information in logs
  - Sensitive info: Client IPs hashed, request IDs generated for tracing
  - Format: Structured logs with request_id, file_size, entity_counts

**Health Checks:**
- Built-in endpoint: `GET /health`
  - Returns: Whisper model status, Presidio engine status, application status
  - Used by Docker health check every 30 seconds

## CI/CD & Deployment

**Hosting:**
- Docker container deployment (GitHub Container Registry)
  - Registry: ghcr.io (GitHub Container Registry)
  - Image: Python 3.11-slim with ffmpeg
  - Non-root user for security

**CI Pipeline:**
- GitHub Actions (`.github/workflows/`)
  - `test.yml` - Tests on push/PR (Python 3.9, 3.10, 3.11)
    - Installs dependencies
    - Downloads spaCy model
    - Runs `test_presidio.py` (21 Presidio test cases)
    - Runs pytest test suite
    - Import checks
    - Ruff linting
  - `docker.yml` - Docker build on push/tags
    - Builds and pushes to ghcr.io
    - Semantic versioning via tags (v*)
    - Cache optimization with GitHub Actions Cache

## Environment Configuration

**Required env vars at runtime:**
- None - All have sensible defaults in `app/config.py`

**Optional env vars (healthcare-specific):**
- `WHISPER_MODEL` - Model size selection (default: medium.en)
- `WHISPER_DEVICE` - CPU or GPU (default: cpu)
- `PHI_SCORE_THRESHOLD` - NER confidence threshold (default: 0.35)
- `ENABLE_CUSTOM_RECOGNIZERS` - Use pediatric patterns (default: true)
- `CORS_ORIGINS` - Comma-separated list for production deployment
- `DEBUG` - Debug logging (default: false)
- `AUDIT_LOG_FILE` - Path to audit log (default: logs/audit.log)
- `ENABLE_AUDIT_LOGGING` - HIPAA audit logs (default: true)

**Secrets location:**
- No secrets required (no API keys or credentials)
- All configuration via environment variables or `.env` file

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None - Application makes no external API calls
- All processing is local and self-contained

## Third-Party Models & Resources

**Whisper Models:**
- Source: OpenAI (via Hugging Face Hub)
- License: MIT
- Download: automatic via faster-whisper on first use
- Cache location: `~/.cache/huggingface/hub/` (system-dependent)

**spaCy Model (en_core_web_lg):**
- Source: Explosion AI (spaCy)
- License: MIT
- Download: explicit via `python -m spacy download en_core_web_lg`
- Installation: In Python site-packages
- Size: ~745MB

**Presidio Patterns:**
- Source: Microsoft (open-source)
- License: MIT
- Usage: Custom recognizers defined in `app/recognizers/`
- Patterns: Pediatric-specific (guardian names, detailed ages, baby names)
- Medical patterns: MRN, room numbers, floor units

## Security & Compliance

**HIPAA Compliance:**
- No patient data transmission to external services ✓
- All processing local to user's machine ✓
- Audit logging without PHI ✓
- Temp files deleted immediately ✓
- Non-root container user ✓
- Security headers (CSP, X-Frame-Options, Cache-Control) ✓

**Data Flow:**
1. User uploads audio file (HTTPS in production)
2. Audio bytes buffered in memory
3. Written to temp file for Whisper processing
4. Temp file deleted after transcription
5. Transcript text processed by Presidio (in-memory)
6. PHI replaced with markers
7. Response returned to user
8. No data persisted

---

*Integration audit: 2026-01-23*
