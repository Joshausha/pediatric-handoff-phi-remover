"""
Transcription module using faster-whisper.

All transcription happens locally - no cloud APIs.
"""

import os
import re
import tempfile
import logging
from typing import Tuple, Dict, Any, Optional
from pathlib import Path
import threading

from faster_whisper import WhisperModel

from .config import settings

logger = logging.getLogger(__name__)

# Thread-safe model loading
_model: Optional[WhisperModel] = None
_model_lock = threading.Lock()


class TranscriptionError(Exception):
    """Raised when transcription fails."""
    pass


def get_model() -> WhisperModel:
    """
    Lazy-load and cache the Whisper model. Thread-safe.

    Returns:
        WhisperModel: The loaded Whisper model
    """
    global _model

    if _model is None:
        with _model_lock:
            # Double-check after acquiring lock
            if _model is None:
                logger.info(f"Loading Whisper model: {settings.whisper_model}")
                _model = WhisperModel(
                    settings.whisper_model,
                    device=settings.whisper_device,
                    compute_type=settings.whisper_compute_type
                )
                logger.info("Whisper model loaded successfully")

    return _model


def is_model_loaded() -> bool:
    """Check if the Whisper model is loaded."""
    return _model is not None


# Common Whisper hallucination artifacts to remove
HALLUCINATION_PATTERNS = [
    r"Thanks for watching[.!]?",
    r"Thank you for watching[.!]?",
    r"Please subscribe[.!]?",
    r"Subscribe to my channel[.!]?",
    r"Like and subscribe[.!]?",
    r"Don't forget to subscribe[.!]?",
    r"See you in the next video[.!]?",
    r"Bye[.!]?$",
    r"^\s*you\s*$",  # Standalone "you" (common hallucination)
    r"^\s*\.\s*$",   # Standalone period
]


def _clean_transcript(text: str) -> str:
    """
    Remove common Whisper hallucination artifacts.

    Args:
        text: Raw transcription text

    Returns:
        Cleaned text with hallucinations removed
    """
    cleaned = text

    for pattern in HALLUCINATION_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


def transcribe_audio(
    audio_bytes: bytes,
    file_extension: str = ".webm"
) -> Tuple[str, Dict[str, Any]]:
    """
    Transcribe audio bytes to text using local Whisper.

    Args:
        audio_bytes: Raw audio file content
        file_extension: Hint for audio format (e.g., ".webm", ".wav", ".mp3")

    Returns:
        Tuple of (transcript_text, metadata_dict)
        metadata includes: duration, language, language_probability, segments_count

    Raises:
        TranscriptionError: If transcription fails
    """
    # Ensure temp directory exists
    temp_dir = Path(settings.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Write audio to temp file (faster-whisper requires file path)
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(
            suffix=file_extension,
            dir=temp_dir,
            delete=False
        )
        temp_file.write(audio_bytes)
        temp_file.close()

        logger.info(f"Transcribing audio file: {temp_file.name}")

        model = get_model()

        # Transcribe with VAD filtering
        segments, info = model.transcribe(
            temp_file.name,
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 500,
                "threshold": 0.5,
            }
        )

        # Collect segments
        segment_list = []
        text_parts = []

        for segment in segments:
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            text_parts.append(segment.text.strip())

        # Combine text
        raw_text = " ".join(text_parts)

        # Clean hallucinations
        clean_text = _clean_transcript(raw_text)

        metadata = {
            "duration": info.duration,
            "language": info.language,
            "language_probability": info.language_probability,
            "segments_count": len(segment_list),
            "raw_length": len(raw_text),
            "clean_length": len(clean_text),
        }

        logger.info(
            f"Transcription complete: {metadata['duration']:.1f}s audio, "
            f"{metadata['segments_count']} segments, "
            f"{metadata['clean_length']} chars"
        )

        return clean_text, metadata

    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise TranscriptionError(f"Failed to transcribe audio: {str(e)}") from e

    finally:
        # Always clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


def estimate_transcription_time(file_size_bytes: int) -> Dict[str, float]:
    """
    Estimate transcription time based on file size.

    Args:
        file_size_bytes: Size of the audio file in bytes

    Returns:
        Dict with estimated_seconds and breakdown
    """
    # Rough estimates based on medium.en model on CPU
    # ~1MB of compressed audio ≈ 1 minute ≈ 15-30 seconds to transcribe

    size_mb = file_size_bytes / (1024 * 1024)

    # Estimate audio duration (compressed audio ~1MB per minute)
    estimated_audio_duration = size_mb * 60  # seconds

    # Transcription speed depends on model
    model_speeds = {
        "tiny.en": 0.05,    # ~20x realtime
        "base.en": 0.1,     # ~10x realtime
        "small.en": 0.3,    # ~3x realtime
        "medium.en": 0.5,   # ~2x realtime
        "large-v3": 1.0,    # ~1x realtime
    }

    speed_factor = model_speeds.get(settings.whisper_model, 0.5)
    estimated_transcription = estimated_audio_duration * speed_factor

    return {
        "estimated_seconds": estimated_transcription,
        "estimated_audio_duration": estimated_audio_duration,
        "model": settings.whisper_model,
        "speed_factor": speed_factor,
    }
