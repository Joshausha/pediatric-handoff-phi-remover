"""Custom Presidio recognizers for pediatric PHI patterns."""

from .medical import get_medical_recognizers
from .pediatric import get_pediatric_recognizers

__all__ = ["get_pediatric_recognizers", "get_medical_recognizers"]
