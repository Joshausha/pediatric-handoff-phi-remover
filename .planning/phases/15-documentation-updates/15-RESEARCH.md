# Phase 15: Documentation Updates - Research

**Researched:** 2026-01-29
**Domain:** Technical documentation for dual-weighting PHI evaluation system
**Confidence:** HIGH

## Summary

This phase documents the dual-weighting evaluation system implemented in v2.2. Research reveals two existing documentation files requiring updates (SPOKEN_HANDOFF_ANALYSIS.md and PROJECT.md) and clear source material in app/config.py and tests/evaluate_presidio.py.

The dual-weighting system separates two distinct metrics:
- **Frequency weights**: How often each PHI type appears in spoken I-PASS handoffs (operational reality)
- **Risk weights**: Severity if each PHI type leaks (HIPAA compliance perspective)

**Primary recommendation:** Update SPOKEN_HANDOFF_ANALYSIS.md with a new "Dual-Weighting Methodology" section explaining the rationale, then add a single row to PROJECT.md Key Decisions table documenting the design choice.

## Standard Stack

This is a **documentation-only phase** — no build tools or libraries required.

### Core Tools
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Markdown | - | Documentation format | Industry standard for technical docs |
| Git | 2.x | Version control for doc updates | Track changes with commit messages |

### Source Material
| File | Purpose | Confidence |
|------|---------|------------|
| `app/config.py` | Defines frequency/risk weights and explanatory comments | HIGH |
| `tests/evaluate_presidio.py` | Implements three-metric report with explanations | HIGH |
| `docs/SPOKEN_HANDOFF_ANALYSIS.md` | Existing analysis document to update | HIGH |
| `.planning/PROJECT.md` | Key Decisions table to update | HIGH |

## Architecture Patterns

### Pattern 1: Update Existing Docs (Don't Create New Files)
**What:** Add sections to existing documentation files rather than creating new standalone docs
**When to use:** When context already exists in a related file
**Example:**
```markdown
# Existing: SPOKEN_HANDOFF_ANALYSIS.md

## Executive Summary
[existing content]

## NEW SECTION: Dual-Weighting Methodology
[explanation of frequency vs risk weights]

## PHI Categories in Spoken Handoffs
[existing content continues]
```

**Why this pattern:**
- User explicitly requested documentation decisions be delegated to Claude
- Existing SPOKEN_HANDOFF_ANALYSIS.md already documents weighted metrics (frequency-only)
- Adding dual-weighting explanation is a natural extension
- Avoids file proliferation

### Pattern 2: Table-Based Decision Documentation
**What:** Use Key Decisions table format from PROJECT.md for design choices
**When to use:** For architectural/design decisions with rationale
**Example from existing PROJECT.md:**
```markdown
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| F2 as primary metric | False negatives more dangerous than false positives | ✓ Good |
| Dual-weighting (frequency + risk) | [NEW ROW TO ADD] | ✓ Good |
```

**Pattern structure:**
- **Decision column:** Brief statement of what was decided (5-10 words)
- **Rationale column:** Why this was chosen (10-20 words)
- **Outcome column:** Always "✓ Good" (decisions table only tracks approved choices)

### Pattern 3: Inline Explanatory Comments in Config
**What:** Document weights directly in config.py with comments explaining purpose
**Example from app/config.py (lines 306-344):**
```python
# Frequency weights: Based on how often each PHI type is spoken in I-PASS handoffs
spoken_handoff_weights: dict[str, float] = Field(
    default={
        "PERSON": 5.0,              # Constantly - patient name every handoff
        "GUARDIAN_NAME": 4.0,       # Commonly - "mom Jessica at bedside"
        ...
    },
    description="Frequency weights: how often each PHI type is spoken in handoffs"
)

# Risk weights: Severity if this PHI type leaks (how identifying is it?)
spoken_handoff_risk_weights: dict[str, float] = Field(
    default={
        "MEDICAL_RECORD_NUMBER": 5.0,  # THE unique identifier - most critical
        "PERSON": 5.0,              # Directly identifies patient
        ...
    },
    description="Risk weights: severity if each PHI type leaks (how identifying)"
)
```

**Why this works:**
- Config is source of truth for weight values
- Comments explain each weight's reasoning
- Pydantic `description` provides programmatic documentation

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Documentation generation | Custom markdown generators | Manual markdown editing | 5 requirements only, automation overhead not justified |
| Weight tables | Programmatic table formatters | Copy from evaluate_presidio.py output | Tables already generated in report code |
| Metric calculations | Recalculate examples | Reference existing test outputs | Tests validate correctness |

**Key insight:** This phase is about EXPLAINING existing code, not building new tools. The dual-weighting system is already implemented and tested — documentation just makes it understandable.

## Common Pitfalls

### Pitfall 1: Creating Redundant Documentation Files
**What goes wrong:** Creating a new "DUAL_WEIGHTING_GUIDE.md" when content belongs in existing docs
**Why it happens:** Instinct to organize by creating new files
**How to avoid:**
- Check existing docs first (SPOKEN_HANDOFF_ANALYSIS.md already covers weighting)
- Add sections to existing files rather than creating new ones
- User delegated doc structure decisions to Claude — choose simplest approach
**Warning signs:** Creating files not mentioned in requirements (DOCS-01 through DOCS-05)

### Pitfall 2: Documenting Implementation Details Instead of Rationale
**What goes wrong:** Explaining *how* the code works instead of *why* dual-weighting was chosen
**Why it happens:** Developer tendency to document mechanics
**How to avoid:**
- Focus on **design rationale** (why two weight schemes?)
- Focus on **user guidance** (when to trust which metric?)
- Skip code walkthrough (developers can read the code)
**Warning signs:** Documentation reads like code comments instead of decision explanation

### Pitfall 3: Inconsistent Weight Values Between Docs and Code
**What goes wrong:** Documenting example weights that don't match app/config.py
**Why it happens:** Creating examples without checking source of truth
**How to avoid:**
- Always reference app/config.py for actual weight values
- Copy weight values directly from config (don't paraphrase)
- Link documentation to config location for verification
**Warning signs:** Documentation shows "PERSON: 4" but config.py has "PERSON: 5.0"

### Pitfall 4: Over-Explaining Metrics Already Covered in Report
**What goes wrong:** Duplicating the divergence explanation that already appears in evaluate_presidio.py output
**Why it happens:** Not realizing the report itself is documentation
**How to avoid:**
- Reference the report output as the primary explanation
- SPOKEN_HANDOFF_ANALYSIS.md should explain DESIGN, not repeat report content
- User sees report every time they run evaluation — docs should add context, not duplicate
**Warning signs:** Documentation includes example report output that matches evaluate_presidio.py

## Code Examples

### Example 1: Adding Section to Existing Markdown Doc
```markdown
# Existing document structure preserved

## Dual-Weighting Methodology

**Introduced:** v2.2 (2026-01-29)

The evaluation system uses **two separate weight schemes** to capture different perspectives on PHI detection performance:

### Frequency Weights: Operational Reality
Weights reflect how often each PHI type is spoken during I-PASS handoffs:
- **PERSON (5.0)**: Patient names spoken constantly ("This is Sarah...")
- **ROOM (4.0)**: Primary patient identifier ("PICU bed 3")
- **MEDICAL_RECORD_NUMBER (0.5)**: Almost never spoken aloud (displayed on screen)

See `app/config.py` (lines 315-328) for complete frequency weight definitions.

### Risk Weights: HIPAA Compliance
Weights reflect severity if each PHI type leaks:
- **MEDICAL_RECORD_NUMBER (5.0)**: THE unique identifier across systems
- **PERSON (5.0)**: Directly identifies patient
- **ROOM (2.0)**: Semi-identifying (hospital context only)

See `app/config.py` (lines 330-344) for complete risk weight definitions.

### Why Two Weight Schemes?

A PHI type that's **rarely spoken** (low frequency weight) can still be **highly identifying** if leaked (high risk weight). Example:

- **MRN**: Frequency weight = 0.5 (almost never spoken), Risk weight = 5.0 (uniquely identifying)

Without dual-weighting, a system that fails to detect MRNs would appear acceptable (high frequency-weighted recall) while missing critical identifiers (low risk-weighted recall).

**Guidance:**
- **Unweighted recall**: Your HIPAA compliance floor (all entities treated equally)
- **Frequency-weighted recall**: Operational reality (what's actually spoken)
- **Risk-weighted recall**: Critical vulnerabilities (severity if leaked)

## [Existing sections continue...]
```

Source: Based on app/config.py lines 306-344 and tests/evaluate_presidio.py lines 557-574

### Example 2: Adding Row to Key Decisions Table
```markdown
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| [existing rows...] |
| Dual-weighting (frequency + risk) | Frequency measures spoken prevalence; risk measures leak severity; both needed for complete evaluation | ✓ Good |
```

Source: PROJECT.md Key Decisions table format (lines 113-134)

## State of the Art

| Documentation Approach | Current Project | Industry Standard | Notes |
|------------------------|-----------------|-------------------|-------|
| Config documentation | Inline comments + Pydantic descriptions | Separate docs or docstrings | Inline approach works well for small config |
| Metric explanation | In-report guidance (evaluate_presidio.py) | Separate methodology doc | Report-embedded explanation is more visible |
| Decision tracking | Key Decisions table | ADR (Architecture Decision Records) | Table format simpler for small projects |

**Current approach is appropriate:**
- Small project (single config file, single evaluation script)
- Active development (inline docs stay synchronized with code)
- Single user (no need for formal ADR process)

## Open Questions

**None.** All source material exists and requirements are clear:

1. **What to document**: Dual-weighting rationale, frequency vs risk purpose ✓
2. **Where to document**: SPOKEN_HANDOFF_ANALYSIS.md and PROJECT.md ✓
3. **Source of truth**: app/config.py weights, evaluate_presidio.py report ✓
4. **Format**: Markdown sections and table rows ✓

## Sources

### Primary (HIGH confidence)
- `app/config.py` lines 306-344 - Defines both weight schemes with inline comments
- `tests/evaluate_presidio.py` lines 484-574 - Implements three-metric report with divergence explanation
- `docs/SPOKEN_HANDOFF_ANALYSIS.md` - Existing documentation file to update
- `.planning/PROJECT.md` lines 113-134 - Key Decisions table format
- `.planning/REQUIREMENTS.md` lines 34-40 - Documentation requirements (DOCS-01 through DOCS-05)

### Secondary (MEDIUM confidence)
- `.planning/phases/14-report-refinement/14-01-PLAN.md` - Report refinement plan showing design intent
- `.planning/ROADMAP.md` lines 161-171 - Phase 15 definition and success criteria

## Metadata

**Confidence breakdown:**
- Existing documentation structure: HIGH - Files exist, formats clear
- Weight definitions: HIGH - Source code is definitive
- Requirements: HIGH - DOCS-01 through DOCS-05 explicitly stated
- User decisions: HIGH - Context shows all doc choices delegated to Claude

**Research date:** 2026-01-29
**Valid until:** Stable (documentation phase, no external dependencies)
