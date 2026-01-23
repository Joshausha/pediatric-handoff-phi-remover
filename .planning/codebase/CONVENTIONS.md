# Coding Conventions

**Analysis Date:** 2026-01-23

## Naming Patterns

**Files:**
- `snake_case.py` for all Python modules
- Test files: `test_*.py` prefix (e.g., `test_deidentification.py`)
- Standalone test harnesses: `test_presidio.py` (directly runnable)
- Organizers/helpers: `*_templates.py`, `*_providers.py`, `generate_test_data.py`

**Functions:**
- `snake_case` for all function names
- Custom exception class: `TranscriptionError` (PascalCase for Exception subclasses)
- Private/internal functions: prefix with `_` (e.g., `_mask_text_preview`, `_get_engines`, `_clean_transcript`)
- Public functions: no prefix (e.g., `deidentify_text`, `transcribe_audio`, `validate_deidentification`)

**Variables:**
- `snake_case` for local/module-level variables
- Constants: `UPPER_SNAKE_CASE` (e.g., `HALLUCINATION_PATTERNS`, `TEST_CASES`)
- Global module variables (lazy-loaded): prefix with `_` (e.g., `_model`, `_analyzer`, `_anonymizer`)

**Types:**
- PascalCase for dataclasses: `EntityInfo`, `DeidentificationResult`, `AuditEvent`, `HealthResponse`, `ProcessResponse`
- PascalCase for custom exceptions: `TranscriptionError`
- Type hints used throughout: `def function(param: str) -> dict[str, int]:`

## Code Style

**Formatting:**
- Tool: Ruff (fast replacement for Black, flake8, isort)
- Line length: 100 characters (configured in `pyproject.toml`)
- Command: `ruff check --fix && ruff format`
- Pre-commit hook: automatic ruff-format on staged files

**Linting:**
- Tool: Ruff (configured in `pyproject.toml`)
- Enabled rule sets: E (errors), F (pyflakes), I (isort imports), B (flake8-bugbear), UP (pyupgrade)
- Ignored: E501 (line too long - formatter handles this)
- Pre-commit: `ruff` with `--fix` flag

**Security:**
- Tool: Bandit
- Configured in `pyproject.toml` with exclude for tests, allow assert in tests
- Runs via pre-commit hook

**Secrets Detection:**
- Tool: detect-secrets
- Runs via pre-commit hook with baseline

## Import Organization

**Order:**
1. Standard library (e.g., `logging`, `os`, `json`, `pathlib`, `dataclasses`, `tempfile`, `threading`)
2. Third-party libraries (e.g., `fastapi`, `pydantic`, `presidio_*`, `spacy`, `faster_whisper`)
3. Local application imports (e.g., `from .config import settings`, `from .deidentification import`)

**Path Aliases:**
- No path aliases configured; relative imports used within `app/` package
- Example: `from .config import settings` from `app/main.py`
- Example: `from .recognizers import get_medical_recognizers` from `app/deidentification.py`

**Barrel Files:**
- Used in `app/recognizers/__init__.py` to export recognizer functions
- Pattern: `from .medical import get_medical_recognizers` with `__all__` export

## Error Handling

**Patterns:**
- Custom exceptions inherit from `Exception` (e.g., `TranscriptionError`)
- Exceptions include context: `raise TranscriptionError(f"Failed to transcribe audio: {str(e)}") from e`
- HTTP endpoints catch domain-specific exceptions and convert to `HTTPException` with appropriate status codes
- Global exception handler for unexpected errors: `@app.exception_handler(Exception)`
- Validation errors wrapped with descriptive messages mentioning supported formats

**Specific patterns:**
- Transcription errors: Catch `TranscriptionError` → `HTTPException(status_code=500, detail=str(e))`
- File validation: Check size before processing → raise `HTTPException(status_code=413)`
- Missing files: Return `HTTPException(status_code=404)` with fallback message
- Presidio de-identification: Never raises exceptions (fail-safe design); validation is post-hoc

## Logging

**Framework:** Python `logging` module with standard formatters

**Setup pattern** (from `app/main.py`):
```python
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
```

**Patterns:**
- Use `logger.info()` for processing milestones (e.g., "Loading Presidio engines...", "Step 1: Transcribing audio...")
- Use `logger.debug()` for detailed flow (e.g., "Added recognizer: {name}", "Filtered out deny-listed LOCATION")
- Use `logger.warning()` for validation/safety issues (e.g., "Validation warnings: {warnings}")
- Use `logger.error()` for operational failures (e.g., "Transcription failed: {error}")
- Use `logger.exception()` for unexpected exceptions with full traceback

**Request tracking:**
- Prefix logs with `[{request_id}]` for traceability across async requests
- Example: `logger.info(f"[{request_id}] Step 1: Transcribing audio...")`

**HIPAA compliance:**
- Separate audit logger in `app/audit.py` logs no PHI (only counts and metadata)
- Application logger can reference PHI entity types (safe) but never actual PHI values

## Comments

**When to Comment:**
- Complex regex patterns: explain what they match and why
- Disable rules: `# ignore: E501` (line too long)
- Non-obvious constants: Document units or rationale
- Lookbehind/lookahead: Explain the pattern intent

**JSDoc/TSDoc:**
- Not applicable (Python uses docstrings)
- Module-level docstrings: Triple-quoted at top of file
- Function docstrings: Always present for public functions and classes
- Format: Google/NumPy style with `Args:`, `Returns:`, `Raises:` sections

**Docstring example** (from `app/deidentification.py`):
```python
def deidentify_text(
    text: str,
    strategy: str = "type_marker"
) -> DeidentificationResult:
    """
    Remove PHI from text using Presidio.

    Args:
        text: The transcript to de-identify
        strategy: Replacement approach
            - "type_marker": [NAME], [PHONE], [DATE], etc. (default, most readable)
            - "redact": [REDACTED] for all PHI
            - "mask": **** asterisks

    Returns:
        DeidentificationResult with clean text and entity details
    """
```

## Function Design

**Size:** Functions stay focused on single responsibility
- Small utilities: 10-30 lines (e.g., `_mask_text_preview`)
- Orchestration endpoints: 30-70 lines (e.g., `process_audio` spanning analysis, de-id, validation)
- Complex analysis: 50-100 lines acceptable if focused (e.g., de-identification with entity filtering)

**Parameters:**
- Type hints always provided: `def func(param: str, count: int = 5) -> dict[str, int]:`
- Default arguments used for optional configuration (e.g., `strategy: str = "type_marker"`)
- Complex objects passed as dataclasses or Pydantic models
- Variadic args used sparingly; prefer explicit parameters

**Return Values:**
- Dataclasses for structured returns: `DeidentificationResult`, `EntityInfo`, `AuditEvent`
- Dictionaries for simple key-value returns with type hints: `dict[str, Any]`
- Tuples for related multiple values: `tuple[str, dict[str, Any]]` from `transcribe_audio`
- `Optional` types when None is valid return: `Optional[float]`

## Module Design

**Exports:**
- Public module interface via functions (not classes, except dataclasses)
- `app/config.py`: Exports `Settings` class and `settings` instance via `get_settings()`
- `app/transcription.py`: Public functions `transcribe_audio()`, `is_model_loaded()`, `estimate_transcription_time()`; custom `TranscriptionError` exception
- `app/deidentification.py`: Public functions `deidentify_text()`, `validate_deidentification()`, `is_engines_loaded()` and dataclasses `EntityInfo`, `DeidentificationResult`
- `app/recognizers/`: Public factory functions `get_medical_recognizers()`, `get_pediatric_recognizers()` returning lists

**Barrel Files:**
- `app/recognizers/__init__.py` exports recognizer factories for clean imports

**Lazy Loading Pattern:**
- Thread-safe lazy initialization for expensive resources (models, engines)
- Example: `_model` in `transcription.py` loaded on first `get_model()` call with `_model_lock`
- Example: `_analyzer`, `_anonymizer` in `deidentification.py` loaded on first `_get_engines()` call

## Security Patterns

**Secrets/Configuration:**
- All sensitive config via environment variables or `.env` file
- Pydantic Settings validates and provides defaults
- Never hardcode credentials or sensitive paths

**CORS:**
- Configurable per environment: default localhost only, configurable via `CORS_ORIGINS` env var
- Applied via `CORSMiddleware` with restrictive defaults

**Rate Limiting:**
- Implemented via `slowapi` library with configurable window
- Default: 10 requests per 60 seconds (configurable via settings)
- Applied to endpoints that accept file uploads: `/api/transcribe`, `/api/process`

**Security Headers:**
- Applied via custom `SecurityHeadersMiddleware`
- Headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Cache-Control, Content-Security-Policy

---

*Convention analysis: 2026-01-23*
