"""
HIPAA-compliant audit logging module.

Logs processing events WITHOUT any PHI. Only captures:
- Timestamps and request IDs
- File sizes and durations
- PHI entity counts (not the actual PHI)
- Success/failure status
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
import json

from .config import settings


@dataclass
class AuditEvent:
    """Structured audit event - no PHI fields allowed."""

    timestamp: str
    request_id: str
    event_type: str  # "transcription_start", "transcription_complete", "transcription_failed"

    # File metadata (no content)
    file_size_bytes: Optional[int] = None
    audio_duration_seconds: Optional[float] = None

    # PHI statistics (counts only, no actual PHI)
    phi_entities_removed: Optional[int] = None
    phi_by_type: Optional[dict] = None

    # Status
    success: bool = True
    error_type: Optional[str] = None  # Error class name only, no message (may contain PHI)
    processing_time_seconds: Optional[float] = None

    # Client metadata (anonymized)
    client_ip_hash: Optional[str] = None  # Hashed, not raw IP


class AuditLogger:
    """Thread-safe audit logger for HIPAA compliance."""

    def __init__(self):
        self._logger = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of the file logger."""
        if self._initialized:
            return

        if not settings.enable_audit_logging:
            self._initialized = True
            return

        # Create logs directory if needed
        log_path = Path(settings.audit_log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure dedicated audit logger
        self._logger = logging.getLogger("audit")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False  # Don't propagate to root logger

        # File handler for audit logs
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)

        self._initialized = True

    def log(self, event: AuditEvent):
        """Log an audit event as JSON."""
        self._ensure_initialized()

        if self._logger is None:
            return

        self._logger.info(json.dumps(asdict(event), default=str))

    def log_request_start(
        self,
        request_id: str,
        file_size_bytes: int,
        client_ip_hash: Optional[str] = None
    ):
        """Log the start of a processing request."""
        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_id=request_id,
            event_type="transcription_start",
            file_size_bytes=file_size_bytes,
            client_ip_hash=client_ip_hash
        )
        self.log(event)

    def log_request_complete(
        self,
        request_id: str,
        file_size_bytes: int,
        audio_duration_seconds: Optional[float],
        phi_entities_removed: int,
        phi_by_type: dict,
        processing_time_seconds: float,
        client_ip_hash: Optional[str] = None
    ):
        """Log successful completion of a processing request."""
        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_id=request_id,
            event_type="transcription_complete",
            file_size_bytes=file_size_bytes,
            audio_duration_seconds=audio_duration_seconds,
            phi_entities_removed=phi_entities_removed,
            phi_by_type=phi_by_type,
            processing_time_seconds=processing_time_seconds,
            success=True,
            client_ip_hash=client_ip_hash
        )
        self.log(event)

    def log_request_failed(
        self,
        request_id: str,
        file_size_bytes: int,
        error_type: str,
        processing_time_seconds: float,
        client_ip_hash: Optional[str] = None
    ):
        """Log a failed processing request."""
        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_id=request_id,
            event_type="transcription_failed",
            file_size_bytes=file_size_bytes,
            success=False,
            error_type=error_type,
            processing_time_seconds=processing_time_seconds,
            client_ip_hash=client_ip_hash
        )
        self.log(event)


def generate_request_id() -> str:
    """Generate a unique request ID for audit correlation."""
    return str(uuid.uuid4())


def hash_client_ip(ip: str) -> str:
    """
    Hash client IP for audit logging.

    Uses a simple hash - enough for correlation without storing raw IPs.
    """
    import hashlib
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


# Singleton instance
audit_logger = AuditLogger()
