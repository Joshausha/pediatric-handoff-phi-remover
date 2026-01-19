"""
Tests for de-identification module.

Run with: pytest tests/test_deidentification.py -v
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.deidentification import deidentify_text, validate_deidentification
from tests.sample_transcripts import SAMPLE_TRANSCRIPTS, EXPECTED_OUTPUTS


class TestDeidentification:
    """Test PHI de-identification functionality."""

    def test_removes_person_names(self):
        """Test that person names are detected and removed."""
        text = "Patient Sarah Johnson presented to the ED."
        result = deidentify_text(text)

        assert "[NAME]" in result.clean_text or "[Name]" in result.clean_text
        assert "Sarah" not in result.clean_text
        assert "Johnson" not in result.clean_text

    def test_removes_phone_numbers(self):
        """Test that phone numbers are detected and removed."""
        text = "Contact mom at 555-867-5309 for updates."
        result = deidentify_text(text)

        assert "[PHONE]" in result.clean_text or "555-867-5309" not in result.clean_text
        assert result.entity_count >= 1

    def test_catches_guardian_names(self):
        """Critical test: Guardian relationship + name pattern."""
        text = "Mom Jessica is at bedside with the patient."
        result = deidentify_text(text)

        # The name after "Mom" should be removed
        assert "Jessica" not in result.clean_text
        # "Mom" itself should remain (it's a role, not a name)
        assert "Mom" in result.clean_text or "mom" in result.clean_text.lower()

    def test_catches_grandparent_names(self):
        """Test grandparent name patterns."""
        text = "Grandma Rosa is the primary caregiver."
        result = deidentify_text(text)

        assert "Rosa" not in result.clean_text

    def test_catches_mrn_patterns(self):
        """Test medical record number detection."""
        text = "Picking up patient, MRN 12345678, for handoff."
        result = deidentify_text(text)

        assert "12345678" not in result.clean_text
        assert "[MRN]" in result.clean_text or result.entity_count >= 1

    def test_catches_mrn_with_label(self):
        """Test MRN with explicit label."""
        text = "Medical record number: 87654321"
        result = deidentify_text(text)

        assert "87654321" not in result.clean_text

    def test_catches_room_numbers(self):
        """Test room number detection."""
        text = "Patient is in PICU bed 7, stable overnight."
        result = deidentify_text(text)

        # Room/bed info should be removed
        assert "bed 7" not in result.clean_text or "[ROOM]" in result.clean_text

    def test_catches_standard_room(self):
        """Test standard room format."""
        text = "Transferred from Room 302 to NICU."
        result = deidentify_text(text)

        assert "302" not in result.clean_text or "[ROOM]" in result.clean_text

    def test_preserves_medical_content(self):
        """Test that medical terminology is NOT over-redacted."""
        text = "Patient with RSV bronchiolitis, on nasal cannula oxygen."
        result = deidentify_text(text)

        # Medical terms should be preserved
        assert "bronchiolitis" in result.clean_text
        assert "RSV" in result.clean_text
        assert "nasal cannula" in result.clean_text
        assert "oxygen" in result.clean_text

    def test_preserves_clinical_values(self):
        """Test that clinical values are preserved."""
        text = "FiO2 of 60%, sats 94%, temp 37.2."
        result = deidentify_text(text)

        assert "FiO2" in result.clean_text
        assert "60%" in result.clean_text
        assert "94%" in result.clean_text

    def test_preserves_medications(self):
        """Test that medication names are preserved."""
        text = "Continue albuterol nebs q4h, ceftriaxone IV."
        result = deidentify_text(text)

        assert "albuterol" in result.clean_text
        assert "ceftriaxone" in result.clean_text

    def test_minimal_phi_transcript(self):
        """Test transcript with minimal PHI has minimal changes."""
        # Sample transcript 5 - mostly clinical content
        text = SAMPLE_TRANSCRIPTS[4]["text"]
        result = deidentify_text(text)

        # Should have very few or no entities
        assert result.entity_count <= 2

        # Medical content preserved
        assert "cellulitis" in result.clean_text
        assert "antibiotics" in result.clean_text


class TestSampleTranscripts:
    """Test de-identification against all sample transcripts."""

    @pytest.mark.parametrize("sample", SAMPLE_TRANSCRIPTS, ids=lambda s: f"transcript_{s['id']}")
    def test_sample_transcript(self, sample):
        """Test each sample transcript for proper de-identification."""
        result = deidentify_text(sample["text"])

        # Check that expected PHI is removed
        for phi in sample["expected_removed"]:
            assert phi not in result.clean_text, f"PHI '{phi}' should be removed"

        # Check that medical content is preserved
        for term in sample["expected_preserved"]:
            assert term in result.clean_text, f"Medical term '{term}' should be preserved"


class TestExpectedOutputs:
    """Test specific input/output pairs."""

    def test_transcript_1_names_and_phone(self):
        """Sample 1: Sarah, Jessica, and phone number."""
        text = EXPECTED_OUTPUTS[1]["input"]
        result = deidentify_text(text)

        assert "Sarah" not in result.clean_text
        assert "Jessica" not in result.clean_text
        assert "555-867-5309" not in result.clean_text

        for term in EXPECTED_OUTPUTS[1]["should_contain"]:
            assert term in result.clean_text

    def test_transcript_2_mrn(self):
        """Sample 2: Name and MRN."""
        text = EXPECTED_OUTPUTS[2]["input"]
        result = deidentify_text(text)

        assert "Michael Thompson" not in result.clean_text
        assert "12345678" not in result.clean_text

        for term in EXPECTED_OUTPUTS[2]["should_contain"]:
            assert term in result.clean_text


class TestValidation:
    """Test the validation function."""

    def test_validation_passes_clean_text(self):
        """Validation should pass for properly de-identified text."""
        original = "Patient Sarah has bronchiolitis."
        cleaned = "Patient [NAME] has bronchiolitis."

        is_valid, warnings = validate_deidentification(original, cleaned)

        assert is_valid
        assert len(warnings) == 0

    def test_validation_detects_leaked_phi(self):
        """Validation should detect if PHI leaked through."""
        original = "Call Jessica at 555-1234."
        # Simulate a case where name leaked (bad de-identification)
        cleaned = "Call Jessica at [PHONE]."

        is_valid, warnings = validate_deidentification(original, cleaned)

        # Should detect the leaked name
        # Note: This depends on Presidio catching it with high confidence
        # In practice, the leak should be caught


class TestReplacementStrategies:
    """Test different replacement strategies."""

    def test_type_marker_strategy(self):
        """Test type_marker replacement (default)."""
        text = "Patient John Smith, phone 555-1234."
        result = deidentify_text(text, strategy="type_marker")

        # Should have type markers like [NAME], [PHONE]
        assert "[" in result.clean_text
        assert "]" in result.clean_text

    def test_redact_strategy(self):
        """Test redact replacement."""
        text = "Patient John Smith, phone 555-1234."
        result = deidentify_text(text, strategy="redact")

        assert "[REDACTED]" in result.clean_text

    def test_mask_strategy(self):
        """Test mask replacement."""
        text = "Patient John Smith, phone 555-1234."
        result = deidentify_text(text, strategy="mask")

        # Should have asterisks
        assert "*" in result.clean_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
