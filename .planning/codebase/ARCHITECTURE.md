# Architecture

**Analysis Date:** 2026-01-23

## Pattern Overview

**Overall:** Layered pipeline architecture with three independent processing stages and local-first constraints

**Key Characteristics:**
- **Local processing only** - No external APIs; all computation on user's machine
- **Lazy initialization** - Models load on first request, not at startup
- **Thread-safe singletons** - Model and engine caching with thread locks for concurrency
- **HIPAA audit compliance** - Structured logging without PHI, no persistent storage
- **Defensive de-identification** - Multi-stage validation with deny lists and custom recognizers

## Layers

**Frontend Layer:**
- Purpose: Web interface for audio upload and transcript display
- Location: `static/` (index.html, app.js, styles.css)
- Contains: HTML forms, JavaScript handlers, real-time feedback
- Depends on: FastAPI HTTP endpoints
- Used by: End users uploading audio files

**API Layer:**
- Purpose: HTTP request handling, input validation, response formatting
- Location: `app/main.py`
- Contains: FastAPI route handlers, security middleware, rate limiting
- Depends on: Transcription and deidentification services
- Used by: Frontend JavaScript, external testing tools

**Transcription Service:**
- Purpose: Audio-to-text conversion using local Whisper model
- Location: `app/transcription.py`
- Contains: Lazy model loading, VAD filtering, hallucination cleanup
- Depends on: faster-whisper library, temporary file storage
- Used by: Main processing endpoint

**De-identification Service:**
- Purpose: PHI detection and removal using Presidio + custom recognizers
- Location: `app/deidentification.py`
- Contains: Engine management, analysis pipeline, anonymization operators
- Depends on: Presidio libraries, spaCy NLP engine, custom recognizer modules
- Used by: Main processing endpoint, standalone de-identification endpoint

**Custom Recognizers:**
- Purpose: Pediatric and medical-specific PHI patterns
- Location: `app/recognizers/pediatric.py`, `app/recognizers/medical.py`
- Contains: Pattern definitions, lookbehind assertions, confidence scores
- Depends on: Presidio's PatternRecognizer framework
- Used by: De-identification service engine setup

**Configuration Layer:**
- Purpose: Centralized settings management
- Location: `app/config.py`
- Contains: Pydantic settings, environment variables, deny lists
- Depends on: pydantic-settings library, .env files
- Used by: All service layers for configuration access

**Audit Logging:**
- Purpose: HIPAA-compliant event logging without PHI
- Location: `app/audit.py`
- Contains: Structured audit events, request tracking, anonymized client info
- Depends on: Built-in logging library, JSON serialization
- Used by: Main processing endpoint for compliance tracking

## Data Flow

**Standard Processing Flow (POST /api/process):**

1. **Input Stage** - Frontend uploads audio file
   - Browser captures audio or accepts file upload
   - FormData sends binary audio + filename to `/api/process`
   - FastAPI receives file, validates size and format

2. **Transcription Stage** - Convert audio to text
   - `transcribe_audio()` writes audio bytes to temp file
   - Loads Whisper model (lazy, on first request)
   - Runs transcription with VAD filtering (500ms silence detection)
   - Cleans hallucinations (YouTube phrases, standalone artifacts)
   - Returns transcript + metadata (duration, language, segment count)

3. **De-identification Stage** - Remove PHI
   - `deidentify_text()` loads Presidio engines (lazy, thread-safe)
   - Analyzer scans text against configured PHI entities
   - Custom pediatric recognizers catch guardian names, baby names, ages
   - Custom medical recognizers catch MRN patterns, room/bed numbers
   - Deny lists filter false positives (medical abbreviations like "NC", "RA")
   - Anonymizer replaces PHI with markers: `[NAME]`, `[PHONE]`, `[ROOM]`, etc.

4. **Validation Stage** - Catch remaining PHI
   - `validate_deidentification()` re-scans cleaned text with high threshold (0.7)
   - Skips replacement markers in validation
   - Flags high-confidence (0.8+) PHI leaks as warnings
   - Returns is_valid flag and warning list

5. **Response Stage** - Return results to frontend
   - Package: original_transcript, clean_transcript, entity counts, warnings
   - Log audit event with PHI counts (no actual text)
   - Respond with JSON containing statistics
   - Clean up temporary files

**Standalone De-identification Flow (GET /api/deidentify):**
- Accepts plain text via query parameter
- Runs only de-identification stage (no transcription)
- Returns clean text + entity details
- Used for testing and text-only workflows

**State Management:**
- Whisper model: Lazy singleton loaded on first transcription request
- Presidio engines: Lazy singletons loaded on first de-identification request
- Configuration: Singleton loaded once via `@lru_cache()`
- Thread safety: All singletons use `threading.Lock()` with double-check pattern
- No request state persistence: Each request is independent, no session storage

## Key Abstractions

**Recognizers Framework:**
- Purpose: Extensible PHI pattern matching
- Examples: `PatternRecognizer` for regex patterns, `guardian_patterns` for family relationships
- Pattern: Lookbehind assertions preserve context ("Mom" in "Mom [NAME]"), capture only PHI portion

**DeidentificationResult Dataclass:**
- Purpose: Structured return value from de-identification pipeline
- Contains: `clean_text`, `original_text`, `entities_found` list, `entity_counts_by_type`
- Used by: All de-identification stages to pass data through pipeline

**AuditEvent Dataclass:**
- Purpose: Structured audit event without PHI
- Contains: Timestamp, request_id, file_size, PHI entity counts (not values)
- Constraint: No PHI fields allowed, only counts and metadata

**Settings (Pydantic):**
- Purpose: Type-safe configuration from environment variables
- Examples: `whisper_model`, `phi_entities`, `deny_list_location`, `enable_audit_logging`
- Pattern: Defaults provided, overrideable via .env or environment variables

## Entry Points

**HTTP /api/process (Main Production Endpoint):**
- Location: `app/main.py:process_audio()` (lines 329-480)
- Triggers: POST request with audio file upload
- Responsibilities: Three-stage processing (transcribe → deidentify → validate), audit logging, error handling

**HTTP /api/deidentify (Testing Endpoint):**
- Location: `app/main.py:deidentify_only()` (lines 297-326)
- Triggers: GET request with text query parameter
- Responsibilities: De-identification only, entity reporting

**HTTP /api/transcribe (Testing Endpoint):**
- Location: `app/main.py:transcribe_only()` (lines 259-294)
- Triggers: POST request with audio file upload
- Responsibilities: Transcription only (raw output, may contain PHI)

**HTTP / (Frontend):**
- Location: `app/main.py:serve_frontend()` (lines 231-240)
- Triggers: GET request for root path
- Responsibilities: Serve static/index.html

**HTTP /health (Health Check):**
- Location: `app/main.py:health_check()` (lines 243-256)
- Triggers: GET request
- Responsibilities: Return model load status and application health

## Error Handling

**Strategy:** Explicit error types, comprehensive logging, graceful degradation

**Patterns:**

1. **TranscriptionError** - Audio processing failures
   - Raised by: `app/transcription.py:transcribe_audio()`
   - Caught by: `app/main.py:process_audio()` at lines 452-465
   - Response: HTTP 500 with user-friendly message

2. **HTTPException** - Request validation failures
   - File size exceeds limit: HTTP 413 Payload Too Large
   - No file provided: HTTP 400 Bad Request
   - Model loading failures: HTTP 500 Internal Server Error

3. **Global Exception Handler** - Unexpected errors (lines 503-513)
   - Catches: Any unhandled exception in request context
   - Logs: Full exception traceback at ERROR level
   - Response: HTTP 500 with generic message (no exception details to user)

4. **Rate Limiting** - Abuse prevention
   - Library: slowapi (lines 46-47, 260, 330)
   - Config: `settings.rate_limit_requests` (default 10 per 60 seconds)
   - Response: HTTP 429 Too Many Requests

5. **Validation Warnings** - Non-fatal PHI concerns
   - Returned in response: `warnings` list (line 448)
   - Logged: Warning level if `validate_deidentification()` finds issues
   - Not blocking: Response succeeds even with warnings

## Cross-Cutting Concerns

**Logging:**
- Framework: Python built-in logging module
- Config: `logging.basicConfig()` at lines 40-43
- Levels: DEBUG (when `settings.debug=true`), INFO for major operations, WARNING for validation issues, ERROR for failures
- Pattern: Request IDs inserted into logs for correlation: `f"[{request_id}] Step 1: Transcribing..."`

**Validation:**
- Input validation: File size, format, presence checks at HTTP layer
- PHI validation: Two-pass analysis (primary detection, secondary high-confidence validation)
- Deny list filtering: Prevent false positives on medical abbreviations (lines 156-163 in deidentification.py)

**Authentication:**
- CORS policy: Restricted to `settings.cors_origins` (default localhost only) - lines 213-219
- Security headers: Content-Security-Policy, X-Frame-Options, X-Content-Type-Options - lines 54-77
- Rate limiting: Per-IP request throttling

**Security Headers:**
- `X-Content-Type-Options: nosniff` - Prevent MIME sniffing
- `X-Frame-Options: DENY` - Prevent clickjacking
- `Cache-Control: no-store` - Don't cache PHI-related responses (line 65)
- Content-Security-Policy: Restrictive policy, self-sourced only, no external resources

**Temporary File Management:**
- Location: `/tmp/handoff-transcriber` (configurable via `settings.temp_dir`)
- Cleanup: Always deleted in `finally` block (lines 184-189 in transcription.py)
- Naming: Unnamed temp files via `tempfile.NamedTemporaryFile(delete=False)` (lines 121-125)

**Model Caching:**
- Whisper model: Global singleton at module level, lazy-loaded on first request
- Presidio engines: Global singletons at module level, lazy-loaded on first de-identification
- Thread safety: Double-check locking pattern (lines 40-52 in transcription.py, 82-114 in deidentification.py)

---

*Architecture analysis: 2026-01-23*
