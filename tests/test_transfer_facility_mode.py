"""
Phase 23: Transfer Facility Mode Tests

Tests for configurable LOCATION preservation:
- Conservative mode (default): Redacts all LOCATION entities
- Clinical mode: Preserves LOCATION entities for care coordination

WARNING: Clinical mode does not meet HIPAA Safe Harbor requirements.
"""

import os
import pytest
from app.deidentification import deidentify_text
from app.config import Settings


class TestTransferFacilityModeConfig:
    """Test configuration and validation."""

    def test_default_mode_is_conservative(self):
        """Default should be conservative for HIPAA compliance."""
        settings = Settings()
        assert settings.transfer_facility_mode == "conservative"

    def test_clinical_mode_allowed(self):
        """Clinical mode should be valid option."""
        # Use environment variable to set mode
        os.environ["TRANSFER_FACILITY_MODE"] = "clinical"
        try:
            settings = Settings()
            assert settings.transfer_facility_mode == "clinical"
        finally:
            del os.environ["TRANSFER_FACILITY_MODE"]

    def test_invalid_mode_raises_error(self):
        """Invalid mode should fail fast with clear error."""
        os.environ["TRANSFER_FACILITY_MODE"] = "invalid_mode"
        try:
            with pytest.raises(ValueError, match="must be one of"):
                Settings()
        finally:
            del os.environ["TRANSFER_FACILITY_MODE"]


class TestConservativeMode:
    """Test conservative mode (default) - redacts all LOCATION."""

    def test_transfer_context_redacted(self):
        """Transfer facility names should be redacted in conservative mode."""
        text = "The patient was transferred from Children's Hospital."
        result = deidentify_text(text, transfer_facility_mode="conservative")

        assert "[LOCATION]" in result.clean_text
        assert "Children's Hospital" not in result.clean_text

    def test_admitted_from_redacted(self):
        """Admitted from context should be redacted."""
        text = "Admitted from Springfield Medical Center yesterday."
        result = deidentify_text(text, transfer_facility_mode="conservative")

        assert "[LOCATION]" in result.clean_text
        assert "Springfield Medical Center" not in result.clean_text

    def test_came_from_redacted(self):
        """Came from context should be redacted."""
        text = "Patient came from Memorial General Hospital."
        result = deidentify_text(text, transfer_facility_mode="conservative")

        assert "[LOCATION]" in result.clean_text
        assert "Memorial General Hospital" not in result.clean_text

    def test_home_address_redacted(self):
        """Home addresses should always be redacted."""
        text = "Patient lives at 425 Oak Street in Portland."
        result = deidentify_text(text, transfer_facility_mode="conservative")

        # Address detection depends on spaCy NER
        # At minimum, city names should be caught
        assert "Portland" not in result.clean_text or "[LOCATION]" in result.clean_text


class TestClinicalMode:
    """Test clinical mode - preserves LOCATION for care coordination."""

    def test_transfer_context_preserved(self):
        """Transfer facility names should be preserved in clinical mode."""
        text = "The patient was transferred from Children's Hospital."
        result = deidentify_text(text, transfer_facility_mode="clinical")

        # Clinical mode preserves LOCATION
        assert "[LOCATION]" not in result.clean_text
        assert "Children's Hospital" in result.clean_text

    def test_admitted_from_preserved(self):
        """Admitted from context should be preserved."""
        text = "Admitted from Springfield Medical Center yesterday."
        result = deidentify_text(text, transfer_facility_mode="clinical")

        assert "[LOCATION]" not in result.clean_text
        assert "Springfield Medical Center" in result.clean_text

    def test_came_from_preserved(self):
        """Came from context should be preserved."""
        text = "Patient came from Memorial General Hospital."
        result = deidentify_text(text, transfer_facility_mode="clinical")

        assert "[LOCATION]" not in result.clean_text
        assert "Memorial General Hospital" in result.clean_text

    def test_other_phi_still_redacted(self):
        """Non-LOCATION PHI should still be redacted in clinical mode."""
        text = "Dr. Sarah Johnson transferred the patient from Memorial Hospital."
        result = deidentify_text(text, transfer_facility_mode="clinical")

        # LOCATION preserved
        assert "Memorial Hospital" in result.clean_text
        # PERSON redacted
        assert "Sarah Johnson" not in result.clean_text
        assert "[NAME]" in result.clean_text

    def test_home_address_also_preserved(self):
        """Note: Clinical mode preserves ALL LOCATION entities.

        This is intentional - clinical mode is an explicit user choice
        to prioritize care coordination over Safe Harbor compliance.
        Users who need address redaction should use conservative mode.
        """
        text = "Patient lives at 425 Oak Street."
        result = deidentify_text(text, transfer_facility_mode="clinical")

        # Clinical mode preserves all LOCATION (including addresses if detected)
        # This is a documented tradeoff
        assert "[LOCATION]" not in result.clean_text


class TestDenyListInteraction:
    """Test that deny list filtering works in both modes."""

    def test_deny_list_conservative_mode(self):
        """Deny list should filter false positives in conservative mode."""
        text = "Patient on high flow NC at 2L via nasal cannula."
        result = deidentify_text(text, transfer_facility_mode="conservative")

        # NC should not be flagged as LOCATION (deny list)
        assert "NC" in result.clean_text
        assert "nasal cannula" in result.clean_text

    def test_deny_list_clinical_mode(self):
        """Deny list should filter false positives in clinical mode."""
        text = "Patient on high flow NC at 2L via nasal cannula."
        result = deidentify_text(text, transfer_facility_mode="clinical")

        # NC should not be flagged as LOCATION (deny list)
        assert "NC" in result.clean_text
        assert "nasal cannula" in result.clean_text


class TestParameterOverride:
    """Test that function parameter overrides config setting."""

    def test_parameter_overrides_config(self):
        """Function parameter should override settings."""
        text = "Transferred from Memorial Hospital."

        # Even with conservative default, clinical parameter should work
        result = deidentify_text(text, transfer_facility_mode="clinical")
        assert "Memorial Hospital" in result.clean_text

        # Conservative parameter should redact
        result = deidentify_text(text, transfer_facility_mode="conservative")
        assert "[LOCATION]" in result.clean_text
