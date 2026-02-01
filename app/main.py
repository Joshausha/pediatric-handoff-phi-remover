"""
FastAPI application for Pediatric Handoff PHI Remover.

All processing happens locally - no patient data leaves the server.
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .audit import audit_logger, generate_request_id, hash_client_ip
from .config import settings
from .deidentification import deidentify_text, is_engines_loaded, validate_deidentification
from .transcription import (
    TranscriptionError,
    estimate_transcription_time,
    is_model_loaded,
    transcribe_audio,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


# =============================================================================
# Security Headers Middleware
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"  # Don't cache PHI-related responses

        # Content Security Policy - restrictive for healthcare
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )

        return response


# =============================================================================
# Pydantic Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    whisper_model: str
    whisper_loaded: bool
    presidio_loaded: bool


class ProcessResponse(BaseModel):
    original_transcript: str
    clean_transcript: str
    phi_removed: dict
    entities: list
    audio_duration_seconds: Optional[float]
    warnings: list
    request_id: str
    processing_timestamp: str


class DeidentifyResponse(BaseModel):
    clean_text: str
    entities_found: int
    entities: list
    entity_counts_by_type: dict


class EstimateResponse(BaseModel):
    estimated_seconds: float
    breakdown: dict


# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Models are loaded lazily on first request, not at startup,
    to avoid slow startup times during development.
    """
    logger.info("Starting Pediatric Handoff PHI Remover")
    logger.info(f"Whisper model: {settings.whisper_model}")
    logger.info(f"Debug mode: {settings.debug}")

    yield

    logger.info("Shutting down...")


# =============================================================================
# FastAPI Application
# =============================================================================

API_DESCRIPTION = """
## Pediatric Handoff PHI Remover

HIPAA-compliant web application for transcribing pediatric patient handoff
recordings and removing Protected Health Information (PHI).

### Key Features

- **100% Local Processing**: All transcription and de-identification happens
  on your machine. No patient data ever leaves the server.
- **Pediatric-Optimized**: Custom recognizers for guardian names ("Mom Sarah"),
  baby names ("Baby Smith"), detailed ages ("3 weeks 2 days old"), and more.
- **Audit Logging**: HIPAA-compliant logs with entity counts (no PHI stored).

### PHI Detection

Automatically detects and removes:
- Patient names (including "Baby LastName" patterns)
- Guardian names ("Mom/Dad [Name]")
- Phone numbers, email addresses
- Dates (admission dates, birth dates)
- Locations and addresses
- Medical record numbers (MRN)
- Room/bed numbers
- Detailed ages (e.g., "3 weeks 2 days old")

### Security

- Rate limiting to prevent abuse
- CORS restricted to configured origins
- Security headers (CSP, X-Frame-Options, etc.)
- Non-persistent processing (no storage of audio or transcripts)

### Usage

1. Upload audio file (webm, wav, mp3, m4a)
2. Wait for transcription (~1 minute per minute of audio on CPU)
3. Review de-identified transcript

For full documentation, see [GitHub](https://github.com/Joshausha/pediatric-handoff-phi-remover).
"""

tags_metadata = [
    {
        "name": "processing",
        "description": "Audio transcription and PHI de-identification endpoints",
    },
    {
        "name": "health",
        "description": "Health check and system status",
    },
    {
        "name": "utilities",
        "description": "Helper endpoints for testing and estimation",
    },
]

app = FastAPI(
    title="Pediatric Handoff PHI Remover",
    description=API_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware (applied first, runs last)
app.add_middleware(SecurityHeadersMiddleware)

# CORS - configurable origins (default: localhost only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Static files (frontend)
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")


# =============================================================================
# Routes
# =============================================================================

@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the frontend HTML."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse(
        status_code=404,
        content={"detail": "Frontend not found. Ensure static/index.html exists."}
    )


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Check application health and model status.

    Returns the current status of the application including whether
    the Whisper and Presidio models are loaded and ready.
    """
    return HealthResponse(
        status="healthy",
        whisper_model=settings.whisper_model,
        whisper_loaded=is_model_loaded(),
        presidio_loaded=is_engines_loaded()
    )


@app.post("/api/transcribe", tags=["utilities"])
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window_seconds}seconds")
async def transcribe_only(request: Request, file: Annotated[UploadFile, File()]):
    """
    Transcribe audio without de-identification.

    For testing transcription independently. Rate limited.

    ⚠️ **WARNING**: Returns raw transcript which may contain PHI.
    Use /api/process for production to ensure PHI is removed.
    """
    # Validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > settings.max_audio_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_audio_size_mb}MB."
        )

    # Get file extension
    extension = Path(file.filename or "audio.webm").suffix or ".webm"

    try:
        transcript, metadata = transcribe_audio(content, extension)

        return {
            "transcript": transcript,
            "duration_seconds": metadata.get("duration"),
            "language": metadata.get("language"),
            "segments_count": metadata.get("segments_count")
        }

    except TranscriptionError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/deidentify", response_model=DeidentifyResponse, tags=["utilities"])
async def deidentify_only(
    text: str = Query(..., description="Text to de-identify"),
    strategy: str = Query("type_marker", description="Replacement strategy: 'type_marker' (default) or 'redact'")
):
    """
    De-identify text without transcription.

    For testing de-identification independently. Useful for verifying
    PHI detection on sample text before processing audio.

    **Strategies**:
    - `type_marker`: Replace PHI with `[ENTITY_TYPE]` (e.g., `[PERSON]`)
    - `redact`: Replace PHI with `[REDACTED]`
    """
    result = deidentify_text(text, strategy)

    return DeidentifyResponse(
        clean_text=result.clean_text,
        entities_found=result.entity_count,
        entities=[
            {
                "type": e.entity_type,
                "score": round(e.score, 2),
                "text_preview": e.text_preview
            }
            for e in result.entities_found
        ],
        entity_counts_by_type=result.entity_counts_by_type
    )


@app.post("/api/process", response_model=ProcessResponse, tags=["processing"])
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window_seconds}seconds")
async def process_audio(
    request: Request,
    file: Annotated[UploadFile, File()],
    transfer_mode: Annotated[str, Form()] = "conservative"  # NEW: Phase 23
):
    """
    **Main endpoint**: Transcribe audio and remove all PHI.

    This is the primary endpoint for production use. It:
    1. Transcribes audio using local Whisper model
    2. Detects and removes all PHI using Presidio + custom pediatric recognizers
    3. Returns the clean transcript with statistics

    **Supported formats**: webm, wav, mp3, m4a, ogg, flac

    **Processing time**: ~1 minute per minute of audio on CPU

    **Rate limited**: 10 requests per 60 seconds (configurable)

    **Returns**:
    - `clean_transcript`: De-identified text safe for sharing
    - `original_transcript`: Raw transcript (for verification only)
    - `phi_removed`: Count of PHI entities removed by type
    - `entities`: Details of each detected entity
    - `audio_duration_seconds`: Length of the audio file
    - `warnings`: Any validation warnings
    """
    start_time = time.time()
    request_id = generate_request_id()
    client_ip_hash = hash_client_ip(get_remote_address(request) or "unknown")

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    file_size = len(content)
    size_mb = file_size / (1024 * 1024)

    logger.info(f"[{request_id}] Processing audio: {file.filename} ({size_mb:.2f}MB)")

    # Log request start
    audit_logger.log_request_start(request_id, file_size, client_ip_hash)

    # Validate transfer mode (Phase 23)
    allowed_modes = ["conservative", "clinical"]
    if transfer_mode not in allowed_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transfer_mode '{transfer_mode}'. Must be one of: {allowed_modes}"
        )

    logger.info(f"[{request_id}] Transfer facility mode: {transfer_mode}")

    if size_mb > settings.max_audio_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f}MB). Maximum size is {settings.max_audio_size_mb}MB."
        )

    # Get file extension
    extension = Path(file.filename).suffix or ".webm"

    try:
        # Step 1: Transcribe
        logger.info(f"[{request_id}] Step 1: Transcribing audio...")
        transcript, metadata = transcribe_audio(content, extension)

        if not transcript.strip():
            processing_time = time.time() - start_time
            audit_logger.log_request_complete(
                request_id=request_id,
                file_size_bytes=file_size,
                audio_duration_seconds=metadata.get("duration"),
                phi_entities_removed=0,
                phi_by_type={},
                processing_time_seconds=processing_time,
                client_ip_hash=client_ip_hash
            )
            return ProcessResponse(
                original_transcript="",
                clean_transcript="",
                phi_removed={"total_count": 0, "by_type": {}},
                entities=[],
                audio_duration_seconds=metadata.get("duration"),
                warnings=["No speech detected in audio"],
                request_id=request_id,
                processing_timestamp=datetime.utcnow().isoformat()
            )

        # Step 2: De-identify
        logger.info(f"[{request_id}] Step 2: De-identifying PHI...")
        result = deidentify_text(transcript, "type_marker", transfer_facility_mode=transfer_mode)

        # Step 3: Validate
        logger.info(f"[{request_id}] Step 3: Validating de-identification...")
        is_valid, warnings = validate_deidentification(transcript, result.clean_text)

        if not is_valid:
            logger.warning(f"[{request_id}] Validation warnings: {warnings}")

        processing_time = time.time() - start_time
        logger.info(f"[{request_id}] Processing complete in {processing_time:.2f}s")

        # Log successful completion
        audit_logger.log_request_complete(
            request_id=request_id,
            file_size_bytes=file_size,
            audio_duration_seconds=metadata.get("duration"),
            phi_entities_removed=result.entity_count,
            phi_by_type=result.entity_counts_by_type,
            processing_time_seconds=processing_time,
            client_ip_hash=client_ip_hash
        )

        return ProcessResponse(
            original_transcript=transcript,
            clean_transcript=result.clean_text,
            phi_removed={
                "total_count": result.entity_count,
                "by_type": result.entity_counts_by_type
            },
            entities=[
                {
                    "type": e.entity_type,
                    "score": round(e.score, 2),
                    "text_preview": e.text_preview
                }
                for e in result.entities_found
            ],
            audio_duration_seconds=metadata.get("duration"),
            warnings=warnings,
            request_id=request_id,
            processing_timestamp=datetime.utcnow().isoformat()
        )

    except TranscriptionError as e:
        processing_time = time.time() - start_time
        logger.error(f"[{request_id}] Transcription failed: {e}")
        audit_logger.log_request_failed(
            request_id=request_id,
            file_size_bytes=file_size,
            error_type="TranscriptionError",
            processing_time_seconds=processing_time,
            client_ip_hash=client_ip_hash
        )
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {e!s}. Please ensure the audio format is supported (webm, wav, mp3, m4a)."
        ) from e

    except Exception as e:
        processing_time = time.time() - start_time
        logger.exception(f"[{request_id}] Unexpected error during processing")
        audit_logger.log_request_failed(
            request_id=request_id,
            file_size_bytes=file_size,
            error_type=type(e).__name__,
            processing_time_seconds=processing_time,
            client_ip_hash=client_ip_hash
        )
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {e!s}"
        ) from e


@app.get("/api/estimate-time", response_model=EstimateResponse, tags=["utilities"])
async def estimate_time(file_size_bytes: int = Query(..., gt=0, description="Audio file size in bytes")):
    """
    Estimate processing time for a given file size.

    Helps frontend show realistic progress expectations before upload.
    Estimate is based on the configured Whisper model and device (CPU/GPU).
    """
    estimate = estimate_transcription_time(file_size_bytes)

    return EstimateResponse(
        estimated_seconds=estimate["estimated_seconds"],
        breakdown=estimate
    )


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected errors gracefully."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",
            "error_type": type(exc).__name__
        }
    )
