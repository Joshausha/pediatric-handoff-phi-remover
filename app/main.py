"""
FastAPI application for Pediatric Handoff PHI Remover.

All processing happens locally - no patient data leaves the server.
"""

import logging
import time
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .transcription import (
    transcribe_audio,
    is_model_loaded,
    estimate_transcription_time,
    TranscriptionError
)
from .deidentification import (
    deidentify_text,
    validate_deidentification,
    is_engines_loaded,
    DeidentificationResult
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

app = FastAPI(
    title="Pediatric Handoff PHI Remover",
    description="HIPAA-compliant local transcription with PHI de-identification",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check application health and model status."""
    return HealthResponse(
        status="healthy",
        whisper_model=settings.whisper_model,
        whisper_loaded=is_model_loaded(),
        presidio_loaded=is_engines_loaded()
    )


@app.post("/api/transcribe")
async def transcribe_only(file: UploadFile = File(...)):
    """
    Transcribe audio without de-identification.

    For testing transcription independently.
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/deidentify", response_model=DeidentifyResponse)
async def deidentify_only(
    text: str = Query(..., description="Text to de-identify"),
    strategy: str = Query("type_marker", description="Replacement strategy")
):
    """
    De-identify text without transcription.

    For testing de-identification independently.
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


@app.post("/api/process", response_model=ProcessResponse)
async def process_audio(file: UploadFile = File(...)):
    """
    Main endpoint: Transcribe audio and remove PHI.

    Accepts audio file, returns de-identified transcript with statistics.
    """
    start_time = time.time()

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    logger.info(f"Processing audio: {file.filename} ({size_mb:.2f}MB)")

    if size_mb > settings.max_audio_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f}MB). Maximum size is {settings.max_audio_size_mb}MB."
        )

    # Get file extension
    extension = Path(file.filename).suffix or ".webm"

    try:
        # Step 1: Transcribe
        logger.info("Step 1: Transcribing audio...")
        transcript, metadata = transcribe_audio(content, extension)

        if not transcript.strip():
            return ProcessResponse(
                original_transcript="",
                clean_transcript="",
                phi_removed={"total_count": 0, "by_type": {}},
                entities=[],
                audio_duration_seconds=metadata.get("duration"),
                warnings=["No speech detected in audio"]
            )

        # Step 2: De-identify
        logger.info("Step 2: De-identifying PHI...")
        result = deidentify_text(transcript, "type_marker")

        # Step 3: Validate
        logger.info("Step 3: Validating de-identification...")
        is_valid, warnings = validate_deidentification(transcript, result.clean_text)

        if not is_valid:
            logger.warning(f"Validation warnings: {warnings}")

        processing_time = time.time() - start_time
        logger.info(f"Processing complete in {processing_time:.2f}s")

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
            warnings=warnings
        )

    except TranscriptionError as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}. Please ensure the audio format is supported (webm, wav, mp3, m4a)."
        )

    except Exception as e:
        logger.exception("Unexpected error during processing")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@app.get("/api/estimate-time", response_model=EstimateResponse)
async def estimate_time(file_size_bytes: int = Query(..., gt=0)):
    """
    Estimate processing time for a given file size.

    Helps frontend show realistic progress expectations.
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
