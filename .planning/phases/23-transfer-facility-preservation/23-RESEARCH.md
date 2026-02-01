# Phase 23: Transfer Facility Preservation - Research

**Researched:** 2026-01-31
**Domain:** HIPAA de-identification, clinical handoff communication
**Confidence:** HIGH

## Summary

Transfer facility names present a unique challenge at the intersection of HIPAA privacy requirements and clinical care coordination. Under HIPAA Safe Harbor, facility names that reveal geographic locations smaller than state-level are classified as identifiers requiring removal. However, clinical handoff literature demonstrates that transfer context (including originating facility) is a standard component of patient handoff communication (I-PASS "Patient Summary").

This phase will implement **configurable selective preservation** allowing users to choose between:
1. **Conservative mode** (default): Redact all facility names per HIPAA Safe Harbor
2. **Clinical mode**: Preserve transfer facility names for care coordination while continuing to redact patient addresses

The technical implementation leverages Presidio's "keep" operator to selectively skip anonymization for specific entity patterns.

**Primary recommendation:** Implement two-mode configuration using existing LOCATION patterns with conditional anonymization based on user setting, defaulting to conservative HIPAA compliance.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| presidio-anonymizer | 2.x | Selective anonymization | Built-in "keep" operator enables selective preservation |
| Pydantic Settings | 2.x | Configuration management | Already used for settings.py, natural fit for mode configuration |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| presidio-analyzer | 2.x | Entity detection | Already integrated, provides pattern confidence scores |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Two-mode config | Post-processing re-insertion | Would require storing detected entities, higher complexity |
| Presidio keep operator | Custom filter before anonymization | More code, duplicates Presidio's filtering logic |
| Config-based | Hard-coded behavior | Users cannot choose compliance level based on use case |

**Installation:**
```bash
# No new dependencies - leveraging existing Presidio stack
# Configuration only via Pydantic Settings
```

## Architecture Patterns

### Recommended Configuration Structure
```
app/
├── config.py              # Add transfer_facility_mode setting
├── deidentification.py    # Conditional operator assignment
└── recognizers/
    └── medical.py         # Existing LOCATION patterns (no changes needed)
```

### Pattern 1: Conditional Operator Assignment
**What:** Use Presidio's "keep" operator for LOCATION entities when in clinical mode
**When to use:** User has explicitly chosen clinical mode for care coordination workflows
**Example:**
```python
# Source: Presidio documentation + project architecture
# app/deidentification.py

def _get_operators_for_mode(strategy: str, transfer_mode: str) -> dict:
    """
    Build operator configuration based on anonymization strategy and transfer mode.

    Args:
        strategy: "type_marker", "redact", "mask"
        transfer_mode: "conservative" or "clinical"

    Returns:
        Operators dict for AnonymizerEngine
    """
    operators = {}

    # Base operator configuration (type_marker example)
    if strategy == "type_marker":
        operators["PERSON"] = OperatorConfig("replace", {"new_value": "[NAME]"})
        operators["PHONE_NUMBER"] = OperatorConfig("replace", {"new_value": "[PHONE]"})
        # ... other entities

        # LOCATION handling depends on mode
        if transfer_mode == "clinical":
            # Clinical mode: preserve LOCATION for transfer contexts
            # (keep operator preserves text unmodified)
            operators["LOCATION"] = OperatorConfig("keep", {})
        else:
            # Conservative mode (default): redact all locations
            operators["LOCATION"] = OperatorConfig("replace", {"new_value": "[LOCATION]"})

    return operators
```

### Pattern 2: Configuration with Pydantic Settings
**What:** Add transfer_facility_mode to existing Pydantic Settings
**When to use:** User needs to configure default behavior via environment variables or .env
**Example:**
```python
# Source: Existing app/config.py pattern
# app/config.py

class Settings(BaseSettings):
    # ... existing settings

    transfer_facility_mode: str = Field(
        default="conservative",
        description="Transfer facility handling: 'conservative' (redact per HIPAA) or 'clinical' (preserve for care coordination)"
    )

    # Validation
    @field_validator("transfer_facility_mode")
    def validate_transfer_mode(cls, v):
        allowed = ["conservative", "clinical"]
        if v not in allowed:
            raise ValueError(f"transfer_facility_mode must be one of {allowed}")
        return v
```

### Pattern 3: Context-Aware Detection (Already Implemented)
**What:** Existing LOCATION patterns detect transfer contexts with high confidence
**When to use:** Pattern-based detection for "transferred from", "admitted from", etc.
**Example:**
```python
# Source: app/recognizers/medical.py lines 349-390
# These patterns already exist and work correctly:

Pattern(
    name="transferred_from",
    regex=r"(?i)(?<=transferred from )(home|(?-i:[A-Z])[a-z']*(?:\s+(?-i:[A-Z])[a-z']*)*(?:\s+(?:Hospital|Medical Center|Clinic|Urgent Care))?)",
    score=0.80
),
Pattern(
    name="admitted_from",
    regex=r"(?i)(?<=admitted from )(home|(?-i:[A-Z])[a-z']*(?:\s+(?-i:[A-Z])[a-z']*)*(?:\s+(?:Hospital|Clinic))?)",
    score=0.80
),
# ... 3 more transfer context patterns
# + 6 facility name patterns (hospital_name, medical_center_name, etc.)
# + 4 residential address patterns (lives_at_address, lives_in_city, etc.)
```

### Anti-Patterns to Avoid
- **Don't filter analyzer results before anonymization**: Presidio's keep operator is the correct mechanism; pre-filtering loses entity information
- **Don't use score-based filtering for mode selection**: Transfer patterns and facility patterns have different scores; mode should control all LOCATION entities uniformly
- **Don't create duplicate LOCATION recognizers**: One LOCATION recognizer with keep/replace operator choice is cleaner than two separate entity types

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Selective anonymization | Custom post-processing filter | Presidio "keep" operator | Built-in, tested, handles edge cases (overlapping entities, score thresholds) |
| Configuration validation | Manual string checks | Pydantic field_validator | Type safety, automatic error messages, consistent with existing code |
| Transfer context detection | New regex patterns | Existing LOCATION patterns | Already validated in Phase 21 with 0.80 score, covers 5 transfer contexts |
| HIPAA vs clinical modes | Hard-coded if/else | Pydantic Settings enum | Environment variable override, .env support, validation |

**Key insight:** Presidio was designed for this use case. The "keep" operator exists specifically to exclude certain entities from anonymization while keeping detection metadata. Custom filtering loses the framework's edge-case handling.

## Common Pitfalls

### Pitfall 1: Applying "keep" to All LOCATION Patterns
**What goes wrong:** Clinical mode would preserve patient home addresses, not just transfer facilities
**Why it happens:** All LOCATION patterns (transfer, facility, residential) use the same entity type
**How to avoid:** Accept this tradeoff. Clinical mode = user explicitly choosing care coordination over Safe Harbor. Document clearly.
**Warning signs:**
- Test case: "lives at 123 Main Street" preserved in clinical mode
- Expected behavior: User accepts this (chose clinical mode)
- Alternative: Split LOCATION into TRANSFER_FACILITY and RESIDENTIAL_ADDRESS entity types (high complexity, requires rework of all patterns)

### Pitfall 2: Mode Selection Without Clear Documentation
**What goes wrong:** Users don't understand HIPAA implications of clinical mode
**Why it happens:** Technical setting without regulatory context
**How to avoid:**
- Default to conservative mode
- Add clear warning in UI when selecting clinical mode
- Document: "Clinical mode preserves transfer facility names for care coordination but does not meet HIPAA Safe Harbor requirements"
**Warning signs:** User complains facility preserved but didn't understand choice

### Pitfall 3: Validation Failures on Deployment
**What goes wrong:** Invalid mode value crashes application on startup
**Why it happens:** Environment variable typo ("clincal" instead of "clinical")
**How to avoid:** Pydantic validation with clear error messages, fail-fast on startup
**Warning signs:** Missing validation, silent fallback to default

### Pitfall 4: Forgetting deny_list_location Still Applies
**What goes wrong:** In clinical mode, "NC" or "ER" get flagged as LOCATION
**Why it happens:** deny_list_location filtering happens before keep operator
**How to avoid:** No changes needed - deny list filtering in deidentification.py (lines 200-211) already removes false positives before anonymization
**Warning signs:** Test "Transferred from ER" → "Transferred from [LOCATION]" (should preserve "ER")

## Code Examples

Verified patterns from official sources and existing codebase:

### Conditional Operator Configuration
```python
# Source: app/deidentification.py (existing pattern, lines 266-286) + Presidio keep operator
# Modified to add transfer_facility_mode support

def deidentify_text(
    text: str,
    strategy: str = "type_marker",
    transfer_facility_mode: str = "conservative"  # NEW parameter
) -> DeidentificationResult:
    """
    Remove PHI from text using Presidio.

    Args:
        text: The transcript to de-identify
        strategy: Replacement approach ("type_marker", "redact", "mask")
        transfer_facility_mode: "conservative" (redact all) or "clinical" (preserve transfers)

    Returns:
        DeidentificationResult with clean text and entity details
    """
    analyzer, anonymizer = _get_engines()

    # ... existing analysis code (lines 176-242)

    # Configure replacement operator based on strategy AND mode
    if strategy == "type_marker":
        operators = {}
        for entity_type in settings.phi_entities:
            marker = f"[{entity_type.replace('_', ' ').title()}]"
            # Simplify markers
            marker_map = {
                "[Person]": "[NAME]",
                "[Phone Number]": "[PHONE]",
                # ... existing mappings
            }
            marker = marker_map.get(marker, marker)

            # LOCATION handling: conditional on mode
            if entity_type == "LOCATION":
                if transfer_facility_mode == "clinical":
                    # Clinical mode: preserve LOCATION (for transfer facilities)
                    operators[entity_type] = OperatorConfig("keep", {})
                else:
                    # Conservative mode: redact LOCATION (HIPAA Safe Harbor)
                    operators[entity_type] = OperatorConfig("replace", {"new_value": marker})
            else:
                # All other entities: normal replacement
                operators[entity_type] = OperatorConfig("replace", {"new_value": marker})

    # ... existing anonymization code (lines 309-314)
```

### Settings Configuration
```python
# Source: app/config.py (existing Pydantic pattern, lines 13-96)
# Add transfer_facility_mode field

class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # ... existing settings (whisper_model, phi_entities, etc.)

    # =========================================================================
    # Transfer Facility Configuration (Phase 23)
    # =========================================================================
    transfer_facility_mode: str = Field(
        default="conservative",
        description=(
            "Transfer facility handling mode:\n"
            "- 'conservative' (default): Redact all locations per HIPAA Safe Harbor\n"
            "- 'clinical': Preserve transfer facility names for care coordination\n"
            "WARNING: Clinical mode does not meet HIPAA Safe Harbor requirements"
        )
    )

    @field_validator("transfer_facility_mode")
    def validate_transfer_mode(cls, v):
        allowed = ["conservative", "clinical"]
        if v not in allowed:
            raise ValueError(
                f"transfer_facility_mode must be one of {allowed}, got '{v}'"
            )
        return v
```

### Frontend UI (Radio Button Selection)
```javascript
// Source: Existing static/script.js pattern for controls
// Add mode selection before transcription

// HTML addition to static/index.html
<div class="form-group">
  <label for="transfer-mode">Transfer Facility Handling:</label>
  <div class="radio-group">
    <label>
      <input type="radio" name="transfer-mode" value="conservative" checked>
      Conservative (HIPAA Safe Harbor - redact all locations)
    </label>
    <label>
      <input type="radio" name="transfer-mode" value="clinical">
      Clinical (Preserve transfer facilities for care coordination)
      <span class="warning">⚠️ Does not meet Safe Harbor requirements</span>
    </label>
  </div>
</div>

// JavaScript handling in script.js
const formData = new FormData();
formData.append('audio', audioFile);
const transferMode = document.querySelector('input[name="transfer-mode"]:checked').value;
formData.append('transfer_mode', transferMode);

fetch('/transcribe', {
  method: 'POST',
  body: formData
})
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| All-or-nothing LOCATION redaction | Mode-based selective preservation | Phase 23 (2026-01-31) | Users can choose HIPAA compliance vs care coordination |
| Hard-coded anonymization strategy | Configurable via Pydantic Settings | Phase 2 (threshold calibration) | Environment variable control |
| Custom filtering pre-anonymization | Presidio keep operator | Never implemented custom (good) | Leverage framework capabilities |

**Deprecated/outdated:**
- N/A - this is a new feature, no existing functionality is deprecated

## Open Questions

1. **Should we split LOCATION into separate entity types?**
   - What we know: Single LOCATION entity type is simple, matches Presidio standard entities
   - What's unclear: Whether clinical users need finer control (preserve transfer, redact residential)
   - Recommendation: Start with single LOCATION toggle, gather user feedback, consider entity split in Phase 24 if needed

2. **Should clinical mode have sub-modes (transfer-only, all-facilities)?**
   - What we know: Current implementation is binary (all LOCATION or none)
   - What's unclear: Whether users want "transfer context only" vs "all facility names"
   - Recommendation: Defer to Phase 24. UAT will reveal if binary choice is sufficient.

3. **Should we log mode selection for audit purposes?**
   - What we know: HIPAA audit logging exists (config.py line 402-409)
   - What's unclear: Whether mode selection is audit-worthy event
   - Recommendation: Yes, add to audit log. Mode affects PHI handling, should be tracked.

## Sources

### Primary (HIGH confidence)
- [Presidio Anonymizer Documentation](https://microsoft.github.io/presidio/anonymizer/) - Keep operator, conditional anonymization
- [Presidio Context Enhancement](https://microsoft.github.io/presidio/tutorial/06_context/) - Context-aware detection patterns
- Project codebase: app/config.py, app/deidentification.py, app/recognizers/medical.py - Existing architecture patterns

### Secondary (MEDIUM confidence)
- [HIPAA Safe Harbor Geographic Requirements](https://www.accountablehq.com/post/hipaa-de-identification-safe-harbor-method-a-practical-guide) - Facility names as geographic identifiers
- [HIPAA PHI Identifiers 2026](https://www.hipaajournal.com/considered-phi-hipaa/) - Updated identifier list
- [I-PASS Patient Handoff Best Practices](https://pmc.ncbi.nlm.nih.gov/articles/PMC7382547/) - Transfer context in clinical handoffs
- [HIPAA Minimum Necessary for Care Coordination](https://www.hipaajournal.com/hipaa-continuity-of-care/) - Treatment vs Safe Harbor requirements

### Tertiary (LOW confidence)
- WebSearch consensus: Transfer facility names are identifiers under Safe Harbor (multiple sources agree)
- Clinical literature: Transfer facility is standard handoff component (I-PASS "Patient Summary")

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Presidio keep operator is documented, Pydantic Settings already in use
- Architecture: HIGH - Configuration pattern matches existing code, minimal changes required
- Pitfalls: MEDIUM - Clinical mode implications need clear documentation, user education critical

**Research date:** 2026-01-31
**Valid until:** 90 days (2026-05-01) - HIPAA regulations stable, Presidio API stable, but clinical guidelines may evolve
