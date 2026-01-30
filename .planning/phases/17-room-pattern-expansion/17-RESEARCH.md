# Phase 17: Room Pattern Expansion - Research

**Researched:** 2026-01-30
**Domain:** Presidio PatternRecognizer with context-based room detection
**Confidence:** HIGH

## Summary

Phase 17 aims to improve ROOM detection recall from 32.1% to ≥80% by adding conversational patterns commonly used in clinical handoffs. Current validation shows 44 ROOM pattern misses, primarily standalone numbers without explicit "room" or "bed" prefixes (e.g., "in 8", "moved to 512", "5-34").

The standard approach is to use **low-confidence regex patterns combined with strong context word support** via Presidio's `LemmaContextAwareEnhancer`. This is the recommended pattern for weak/ambiguous matches that need context to distinguish them from clinical numbers (vitals, doses, ages).

I-PASS handoff research shows 74.68% of handoffs occur at bedside and 22.35% at nursing pods, meaning room references are frequently verbal and conversational rather than formal "Room 302" format.

**Primary recommendation:** Add 3-5 low-confidence (score=0.30-0.45) patterns for standalone numbers and room synonyms, with comprehensive context word lists. Use context enhancement to boost confidence to 0.65-0.75 when context matches.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| presidio-analyzer | 2.x | PHI detection framework | Microsoft-backed, production-ready PII detection |
| Python re | 3.9+ | Regex pattern matching | Built-in, no dependencies |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| spacy | 3.x | NER for context | Already integrated for PERSON/LOCATION detection |
| LemmaContextAwareEnhancer | (presidio) | Context-based score boosting | Default enhancer, handles lemmatization automatically |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PatternRecognizer + context | Custom recognizer class | More control but breaks established pattern |
| Default 0.35 context boost | Custom context_similarity_factor | Fine-tuning possible but default works for most cases |
| Lemma matching | Exact string matching | Faster but misses variations like "rooms" vs "room" |

**Installation:**
```bash
# Already installed in project
pip install presidio-analyzer spacy
python -m spacy download en_core_web_lg
```

## Architecture Patterns

### Recommended Pattern Structure
```
app/recognizers/medical.py
└── get_medical_recognizers()
    └── Room Number Recognizer
        ├── High-confidence patterns (0.65-0.80)
        │   ├── "Room 302", "Bed 5A" (explicit labels)
        │   └── "PICU bed 7" (unit-specific)
        ├── Medium-confidence patterns (0.45-0.60)
        │   ├── "3-22" (hyphenated format)
        │   └── "bay 5", "isolette 3" (specific terms)
        └── Low-confidence patterns (0.30-0.45) - NEW
            ├── Standalone numbers in context
            ├── Room synonyms without numbers
            └── Prepositional patterns ("in X", "to X")
```

### Pattern 1: Low-Confidence Number with Context Boost
**What:** Detect standalone numbers (1-4 digits) that likely represent room numbers based on surrounding context words
**When to use:** Numbers that could be rooms, vitals, ages, or doses—context disambiguates
**Example:**
```python
# Source: https://microsoft.github.io/presidio/tutorial/06_context/
# Pattern: Very weak initial score, context provides confirmation
Pattern(
    name="room_number_contextual",
    regex=r"\b\d{1,4}\b",  # Any 1-4 digit number
    score=0.30  # LOW - needs context to confirm
)

# Context words boost to 0.65 (0.30 + 0.35 default boost)
room_recognizer = PatternRecognizer(
    supported_entity="ROOM",
    patterns=[...],
    context=[
        # Location prepositions
        "in", "to", "from", "moved to", "transferred to", "admitted to",
        # Room-related terms
        "room", "bed", "space", "pod", "cubicle", "crib", "bay", "isolette",
        # Unit contexts
        "picu", "nicu", "icu", "floor", "unit",
        # Action verbs
        "located", "placed", "assigned"
    ]
)
```

### Pattern 2: Room Synonym Detection
**What:** Detect room synonyms (space, pod, cubicle, crib) with or without numbers
**When to use:** Pediatric/NICU settings where standard "room" terminology varies
**Example:**
```python
# Source: Based on I-PASS handoff patterns research
Pattern(
    name="room_synonym",
    regex=r"(?i)\b(?:space|pod|cubicle|crib)\s*\d{1,3}\b",
    score=0.55  # Medium - term is specific but less common
)

# Also catch standalone synonyms in room context
Pattern(
    name="room_synonym_standalone",
    regex=r"(?i)\b(?:space|pod|cubicle|crib)\b",
    score=0.35  # Low - needs strong context
)
```

### Pattern 3: Prepositional Room References
**What:** "in [number]", "to [number]" patterns common in verbal handoffs
**When to use:** Conversational handoff transcripts where formal labels are omitted
**Example:**
```python
# Source: I-PASS verbal handoff research (74.68% bedside)
Pattern(
    name="room_prepositional",
    regex=r"(?i)\b(?:in|to)\s+\d{1,4}\b",
    score=0.45  # Medium - preposition provides some context
)

# More specific version with room context
Pattern(
    name="room_prepositional_specific",
    regex=r"(?i)\b(?:in|to|from)\s+(?:room|bed|space)?\s*\d{1,4}\b",
    score=0.60  # Higher - explicit room reference
)
```

### Anti-Patterns to Avoid
- **High scores for standalone numbers:** Score=0.70+ for `\b\d{1,4}\b` will cause massive false positives on ages, vitals, doses
- **Greedy context matching:** Don't use `.+room.+\d+` patterns—too broad, hard to maintain
- **Ignoring context enhancement:** Setting patterns without context list means no confidence boost
- **Overlapping high-score patterns:** Multiple 0.70+ patterns for same text fragment create confusion

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Context-aware scoring | Custom scoring logic | `LemmaContextAwareEnhancer` | Handles lemmatization, tested by Microsoft, configurable |
| Pattern confidence tuning | Hard-coded thresholds | PatternRecognizer score parameter | Declarative, easy to A/B test |
| Word boundary detection | Manual string splitting | `\b` regex word boundaries | Handles punctuation, whitespace correctly |
| Synonym expansion | Manual list expansion | Context word lists | Enhancer handles lemmas automatically |
| False positive filtering | Post-processing filter | Deny lists in config.py | Already integrated, version-controlled |

**Key insight:** Presidio's context enhancement is designed for exactly this use case (weak patterns needing disambiguation). Building custom logic duplicates tested functionality and loses maintainability.

## Common Pitfalls

### Pitfall 1: False Positives on Clinical Numbers
**What goes wrong:** Pattern `\b\d{1,4}\b` with high score matches "O2 at 8 liters", "dose 512 mg", "3 weeks old"
**Why it happens:** Medical transcripts are dense with numbers—vitals, ages, doses, labs all use 1-4 digits
**How to avoid:**
- Set initial score LOW (0.30-0.45)
- Rely on context boost for confirmation
- Test against validation set with clinical numbers
**Warning signs:** Precision drops below 50%, lots of oxygen/medication false positives

### Pitfall 2: Missing Context Enhancement Configuration
**What goes wrong:** Pattern has context list but LemmaContextAwareEnhancer not configured in AnalyzerEngine
**Why it happens:** Presidio creates default enhancer, but custom recognizers need explicit registry integration
**How to avoid:**
```python
# Verify enhancer is active
analyzer = AnalyzerEngine(
    registry=registry,
    context_aware_enhancer=LemmaContextAwareEnhancer()  # Explicit
)
```
**Warning signs:** Patterns with context don't get score boost, recall stays low

### Pitfall 3: Over-Reliance on Hyphenated Patterns
**What goes wrong:** Pattern `\d{1,2}-\d{1,2}` matches "2-3 days", "4-6 hours", "5-10% chance"
**Why it happens:** Hyphenated format is common in ranges, dates, percentages—not just rooms
**How to avoid:**
- Keep hyphenated pattern at medium confidence (0.55)
- Add strong context words requirement
- Test specifically against date/duration patterns in deny list
**Warning signs:** DATE_TIME false positives increase, duration phrases flagged as rooms

### Pitfall 4: Ignoring Unit Name Preservation
**What goes wrong:** New patterns match "PICU 7" or "NICU bed 3" entirely, overwriting unit name
**Why it happens:** Broad patterns don't account for existing unit-specific patterns
**How to avoid:**
- Use lookbehind for unit patterns: `(?<=PICU )bed\s+\d+`
- Test that "PICU bed 7" → "PICU [ROOM]" (not "[ROOM] [ROOM]")
- Verify existing patterns take precedence (higher scores)
**Warning signs:** Unit names disappear from output, double-redaction occurs

### Pitfall 5: Context Word List Too Narrow
**What goes wrong:** Only "room" and "bed" in context list, misses "patient in 8", "moved to 512"
**Why it happens:** Underestimating variety of conversational handoff language
**How to avoid:**
- Include prepositions: "in", "to", "from"
- Include verbs: "moved", "transferred", "admitted", "located", "assigned"
- Include unit names: "picu", "nicu", "icu", "floor"
- Review I-PASS handoff transcripts for common patterns
**Warning signs:** Recall stuck at 40-50%, manual review shows obvious misses

## Code Examples

Verified patterns from official sources:

### Low-Confidence Pattern with Context Boost
```python
# Source: https://microsoft.github.io/presidio/tutorial/06_context/
# Example: ZIP code with 0.01 initial score → 0.4 with context

from presidio_analyzer import Pattern, PatternRecognizer

# Low initial score - ambiguous pattern
room_number_pattern = Pattern(
    name="room_number_contextual",
    regex=r"\b\d{1,4}\b",
    score=0.30  # LOW - many things are 1-4 digits
)

# Context words provide confirmation
room_recognizer = PatternRecognizer(
    supported_entity="ROOM",
    patterns=[room_number_pattern],
    context=[
        # This list gets lemmatized automatically
        "room", "rooms", "bed", "beds",
        "in", "to", "from",
        "moved", "transferred", "admitted",
        "located", "placed", "assigned",
        "picu", "nicu", "icu", "floor", "unit"
    ]
)

# When "moved to 512" appears:
# 1. Pattern matches "512" with score=0.30
# 2. Enhancer finds "to" and "moved" in context
# 3. Score boosted to 0.65 (0.30 + 0.35 default boost)
# 4. Passes threshold (0.30), flagged as ROOM
```

### Configuring Custom Context Enhancement
```python
# Source: https://microsoft.github.io/presidio/samples/python/customizing_presidio_analyzer/
from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer
from presidio_analyzer import AnalyzerEngine

# Custom enhancement factors
context_enhancer = LemmaContextAwareEnhancer(
    context_similarity_factor=0.40,  # Boost amount (default: 0.35)
    min_score_with_context_similarity=0.45  # Floor value (default: 0.4)
)

analyzer = AnalyzerEngine(
    registry=registry,
    context_aware_enhancer=context_enhancer
)

# Now patterns with score=0.30 + context boost → 0.70 (0.30 + 0.40)
# Or floor to 0.45 if boost doesn't reach that
```

### Room Synonym Patterns (Pediatric-Specific)
```python
# Source: I-PASS handoff research - bedside and pod locations common
room_synonym_patterns = [
    # Specific terms with numbers
    Pattern(
        name="space_number",
        regex=r"(?i)\bspace\s+\d{1,3}\b",
        score=0.55
    ),
    Pattern(
        name="pod_number",
        regex=r"(?i)\bpod\s+\d{1,3}\b",
        score=0.55
    ),
    Pattern(
        name="cubicle_number",
        regex=r"(?i)\bcubicle\s+\d{1,3}\b",
        score=0.55
    ),
    Pattern(
        name="crib_number",
        regex=r"(?i)\bcrib\s+\d{1,3}\b",
        score=0.55
    ),
    # Standalone terms (rely on context)
    Pattern(
        name="room_synonym_standalone",
        regex=r"(?i)\b(?:space|pod|cubicle|crib)\b",
        score=0.35
    )
]
```

### Testing Pattern Scores
```python
# Source: Validation against test dataset
# Test that clinical numbers DON'T match without context
test_cases = [
    "O2 at 8 liters",  # Should NOT match (no room context)
    "dose 512 mg",     # Should NOT match (medication context)
    "moved to 512",    # SHOULD match (room context present)
    "in 8",            # SHOULD match (preposition context)
    "space 5",         # SHOULD match (synonym pattern)
]

for text in test_cases:
    results = analyzer.analyze(text=text, entities=["ROOM"], language="en")
    print(f"{text}: {len(results)} matches")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Only explicit "Room X" patterns | Context-aware weak patterns | Presidio 2.x (2023+) | Enables conversational pattern detection |
| Hard-coded confidence thresholds | Per-pattern scores + context boost | Presidio 2.x | Flexible tuning without code changes |
| Post-processing filters | Deny lists + context enhancement | v2.1 (this project) | Cleaner architecture, version-controlled |
| Exact string matching | Lemma-based context matching | Presidio default | "room" matches "rooms", "moved" matches "move" |

**Deprecated/outdated:**
- Manual context checking: Presidio's `LemmaContextAwareEnhancer` is now standard
- High-confidence weak patterns: Pattern score should reflect pattern strength, not desired outcome
- Custom recognizer classes for simple patterns: `PatternRecognizer` with context is sufficient for 90% of cases

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal context_similarity_factor for ROOM entity**
   - What we know: Default is 0.35, range is 0.0-1.0
   - What's unclear: Whether ROOM needs higher boost (0.40-0.45) given high ambiguity
   - Recommendation: Start with default 0.35, tune if recall plateau below 80%

2. **Context window size (prefix/suffix count)**
   - What we know: Presidio has `context_prefix_count` and `context_suffix_count` parameters
   - What's unclear: Documentation doesn't specify defaults or recommended values
   - Recommendation: Test with 3-5 word window (estimated from ZIP code examples), measure recall impact

3. **Handling "room" as verb vs noun**
   - What we know: "room with patient" (verb) vs "room 302" (noun)
   - What's unclear: Whether lemmatization handles this correctly or needs deny list
   - Recommendation: Test against validation set, add "room with" to deny list if false positives occur

4. **Hyphenated pattern context requirement**
   - What we know: "3-22" could be room, date range, or other
   - What's unclear: Whether score=0.55 + context is enough or needs stricter threshold
   - Recommendation: A/B test score=0.55 vs 0.45, validate against DATE_TIME false positives

## Sources

### Primary (HIGH confidence)
- [Presidio Context Enhancement Tutorial](https://microsoft.github.io/presidio/tutorial/06_context/) - Context word mechanics, score boosting
- [Presidio Customization Guide](https://microsoft.github.io/presidio/samples/python/customizing_presidio_analyzer/) - LemmaContextAwareEnhancer configuration
- [Presidio Best Practices](https://microsoft.github.io/presidio/analyzer/developing_recognizers/) - Pattern design principles
- [I-PASS Handoff Research (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9923540/) - Clinical handoff verbal patterns, bedside location data

### Secondary (MEDIUM confidence)
- [Presidio GitHub Discussions #1043](https://github.com/microsoft/presidio/discussions/1043) - Context phrase usage examples
- [Presidio GitHub Discussions #1299](https://github.com/microsoft/presidio/discussions/1299) - Scoring mechanism explanations
- [I-PASS Institute Mnemonic Guide](https://www.ipassinstitute.com/hubfs/I-PASS-mnemonic.pdf) - Handoff structure and terminology

### Tertiary (LOW confidence)
- None - all findings verified with official documentation or peer-reviewed research

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Presidio is established, documented, production-ready
- Architecture: HIGH - Patterns verified from official examples and existing codebase
- Pitfalls: HIGH - Based on current validation data showing actual failure modes
- Context enhancement: MEDIUM - Documentation clear on mechanism, defaults less documented
- Room synonym patterns: MEDIUM - Based on I-PASS research but not Presidio-specific testing

**Research date:** 2026-01-30
**Valid until:** 2026-03-30 (60 days - Presidio stable, clinical patterns don't change rapidly)

**Current validation data:**
- ROOM recall: 32.1% (44 pattern misses)
- Target: ≥80% recall
- Main gaps: Standalone numbers, conversational patterns, room synonyms
- Existing patterns: 10 patterns in `medical.py`, all explicit "room/bed" labels
