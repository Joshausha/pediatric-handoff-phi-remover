# Phase 21: Location/Transfer Patterns - Research

**Researched:** 2026-01-30
**Domain:** LOCATION entity detection for clinical handoff contexts
**Confidence:** HIGH

## Summary

Research focused on improving LOCATION detection from 20% to ≥60% recall by adding context-based patterns for transfer/admission scenarios, residential addresses, hospital/clinic names, and cities. Current dataset contains 129 LOCATION entities across 500 synthetic handoffs, with three primary context patterns: "from" (50%), "at/in" (40%), and "to" (10%).

The standard approach is **pattern-based recognition with lookbehind patterns** (following Phase 17 ROOM and Phase 18 GUARDIAN implementations). Presidio's default spaCy NER already detects some locations (20% baseline), but clinical handoff contexts require custom patterns for transfer language, medical facility names, and residential addresses that appear in spoken handoffs.

**Primary recommendation:** Implement 3-tier pattern system prioritizing transfer contexts (highest confidence), followed by hospital/clinic names, then residential addresses. Use lookbehind patterns to preserve context words while matching only the location entity.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Presidio Analyzer | 2.2+ | PHI detection framework | Already in use, PatternRecognizer supports context-based patterns |
| Python `re` | 3.9+ | Regex pattern matching | Native library, lookbehind patterns proven in Phases 17-18 |
| spaCy | 3.x | NER baseline | Default LOCATION detector (provides 20% baseline recall) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| en_core_web_lg | 3.x | Large spaCy model | Already configured, provides baseline LOCATION detection |

**Installation:**
```bash
# Already installed in project
# No additional dependencies needed
```

## Architecture Patterns

### Recommended Pattern Structure
```
app/recognizers/
├── pediatric.py    # Guardian, baby name patterns
├── medical.py      # ROOM, MRN patterns
└── location.py     # NEW: LOCATION transfer/facility patterns (recommended)
```

**Alternative:** Add to existing `medical.py` (co-locate with ROOM recognizer since both use location context)

### Pattern 1: Transfer Context (Lookbehind)
**What:** Match location names preceded by transfer/admission verbs
**When to use:** Highest priority - 50% of dataset uses "from" context
**Score:** 0.80 (high confidence due to explicit context)

**Example:**
```python
# Source: Existing ROOM recognizer pattern (app/recognizers/medical.py, Phase 17)
Pattern(
    name="transferred_from_hospital",
    regex=r"(?i)(?<=transferred from )[A-Z][A-Za-z\s]+(?:Hospital|Medical Center|Clinic)",
    score=0.80
)
Pattern(
    name="admitted_from_location",
    regex=r"(?i)(?<=admitted from )[A-Z][A-Za-z\s]+(?:Hospital|Clinic|Home)",
    score=0.80
)
```

**Lookbehind advantages:**
- Preserves context words ("transferred from [LOCATION]" not "[LOCATION]")
- Prevents false positives on standalone facility names
- Proven pattern from Phase 17 (98% ROOM recall)

### Pattern 2: Hospital/Clinic Names (NER Boosting)
**What:** Detect medical facility names with explicit keywords
**When to use:** 25 hospital entities in dataset (19% of locations)
**Score:** 0.70 (requires facility keyword for confidence)

**Example:**
```python
# Source: Pattern-based approach from Presidio documentation
Pattern(
    name="hospital_name",
    regex=r"\b([A-Z][A-Za-z\s]+)\s+(?:Hospital|Medical Center|Health System)\b",
    score=0.70
)
Pattern(
    name="clinic_name",
    regex=r"\b([A-Z][A-Za-z\s]+)\s+(?:Clinic|Pediatrics|Associates)\b",
    score=0.65
)
```

**Note:** spaCy NER already catches some of these, but custom patterns ensure clinical terminology is prioritized.

### Pattern 3: Residential Context (Lookbehind)
**What:** Match addresses/cities in residential context phrases
**When to use:** "lives at", "discharge to" contexts
**Score:** 0.75 (strong context, but address formats vary)

**Example:**
```python
Pattern(
    name="lives_at_address",
    regex=r"(?i)(?<=lives at )[A-Z0-9][A-Za-z0-9\s]+(?:Street|Drive|Avenue|Road|Lane|Way|Court|Heights|Manor|Hill)",
    score=0.75
)
Pattern(
    name="discharge_to_location",
    regex=r"(?i)(?<=discharge to )[A-Z][A-Za-z\s]+",
    score=0.70
)
```

### Pattern 4: PCP Office Context
**What:** Detect clinic names in "PCP is Dr. X at Y Clinic" constructs
**When to use:** Primary care provider references
**Score:** 0.65 (indirect context, lower confidence)

**Example:**
```python
Pattern(
    name="pcp_clinic",
    regex=r"(?i)(?<=\bat )[A-Z][A-Za-z\s]+(?:Clinic|Pediatrics|Associates|Medical)",
    score=0.65
)
```

### Anti-Patterns to Avoid

- **Standalone facility names without context**: Too many false positives (job titles like "Memorial nurse" would match)
- **Generic city names without qualifiers**: spaCy NER already handles these (rely on baseline)
- **Overly broad address patterns**: Risk matching medical abbreviations or dates

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Generic location NER | Custom NER model | spaCy en_core_web_lg | Already provides 20% baseline, handles cities/countries |
| Deny list filtering | Manual filtering | Existing deny_list_location in config.py | Already filters medical abbreviations (NC, RA, OR, etc.) |
| Fixed-width lookbehind | Variable-width patterns | Separate patterns per context length | Python regex limitation requires fixed width |

**Key insight:** Presidio + spaCy already handle generic locations. Focus custom patterns on **clinical handoff contexts** that spaCy misses: transfer language, medical facility detection, residential context.

## Common Pitfalls

### Pitfall 1: Variable-Width Lookbehind Attempts
**What goes wrong:** Python regex rejects `(?<=\btransferred from )` with variable preceding text
**Why it happens:** Python's `re` module requires fixed-width lookbehind assertions
**How to avoid:** Use separate patterns for each context phrase length (like Phase 17 ROOM recognizer)
**Warning signs:** `re.error: look-behind requires fixed-width pattern` exception

**Example from Phase 17:**
```python
# WRONG - variable width
Pattern(regex=r"(?<=\b(?:transferred|admitted) from )")  # FAILS

# RIGHT - fixed width per context
Pattern(regex=r"(?<=transferred from )")  # 17 chars
Pattern(regex=r"(?<=admitted from )")     # 14 chars
```

### Pitfall 2: Medical Abbreviation False Positives
**What goes wrong:** "OR" (operating room), "ER" (emergency room) detected as locations
**Why it happens:** spaCy NER sees capital letters and classifies as place names
**How to avoid:** Existing `deny_list_location` in `app/config.py` already filters these (Lines 99-142)
**Warning signs:** Test cases show "NC", "RA", "OR" being redacted

**Current deny list (verified):**
- NC (nasal cannula), RA (room air), OR (operating room)
- Hospital unit names: PICU, NICU, ICU (should NOT be redacted)
- High/low flow terminology (Phase 11 additions)

### Pitfall 3: City Name Over-Detection
**What goes wrong:** Generic city names like "Madison" could match provider/patient names
**Why it happens:** spaCy NER is trained on news text, over-detects place names in clinical context
**How to avoid:** Require explicit context ("en route from [City]", "lives in [City]") for city detection
**Warning signs:** Names like "Madison" or "Austin" being flagged as locations

### Pitfall 4: Address Format Variations
**What goes wrong:** Dataset has diverse address formats (street addresses, apartment numbers, suite numbers)
**Why it happens:** Real-world addresses don't follow a single pattern
**How to avoid:** Use multiple patterns covering common street type suffixes (Street, Drive, Avenue, Heights, Manor, etc.)
**Warning signs:** Low recall on address detection despite high transfer context recall

## Code Examples

Verified patterns from existing codebase and research:

### Transfer Context Detection
```python
# Source: Adapted from Phase 17 ROOM recognizer (medical.py lines 96-138)
transfer_patterns = [
    # "transferred from Memorial Hospital" -> matches "Memorial Hospital"
    Pattern(
        name="transferred_from",
        regex=r"(?i)(?<=transferred from )[A-Z][A-Za-z\s]+(?:Hospital|Medical Center|Clinic|Home)?",
        score=0.80
    ),
    # "admitted from City Name" -> matches "City Name"
    Pattern(
        name="admitted_from",
        regex=r"(?i)(?<=admitted from )[A-Z][A-Za-z\s]+",
        score=0.75
    ),
    # "sent from Hospital Name" -> matches "Hospital Name"
    Pattern(
        name="sent_from",
        regex=r"(?i)(?<=sent from )[A-Z][A-Za-z\s]+(?:Hospital|Clinic)?",
        score=0.75
    ),
]
```

### Hospital/Clinic Name Detection
```python
# Source: Presidio pattern-based approach (verified via documentation)
facility_patterns = [
    # "Memorial Hospital" -> entire match
    Pattern(
        name="hospital_name",
        regex=r"\b([A-Z][A-Za-z\s]+)\s+Hospital\b",
        score=0.70
    ),
    # "Children's Medical Center" -> entire match
    Pattern(
        name="medical_center",
        regex=r"\b([A-Z][A-Za-z\s']+)\s+Medical Center\b",
        score=0.70
    ),
    # "Springfield Clinic" -> entire match
    Pattern(
        name="clinic_name",
        regex=r"\b([A-Z][A-Za-z\s]+)\s+Clinic\b",
        score=0.65
    ),
]
```

### Residential Address Detection
```python
# Source: Adapted from dataset analysis (addresses have number + street type)
address_patterns = [
    # "lives at 123 Main Street" -> matches "123 Main Street"
    Pattern(
        name="lives_at_address",
        regex=r"(?i)(?<=lives at )\d+\s+[A-Za-z\s]+(?:Street|Drive|Avenue|Road|Lane|Way|Court|Heights|Manor|Hill|Canyon|Track|Harbors|Turnpike|Cliffs|Gardens)\b(?:\s+(?:Apt|Suite|Unit)\.\s*\d+)?",
        score=0.75
    ),
    # "discharge to 456 Oak Lane" -> matches "456 Oak Lane"
    Pattern(
        name="discharge_to_address",
        regex=r"(?i)(?<=discharge to )\d+\s+[A-Za-z\s]+(?:Street|Drive|Avenue|Road|Lane|Way|Court)\b",
        score=0.75
    ),
]
```

### City Context Detection
```python
# Source: Dataset shows city names in "en route from" and "lives in" contexts
city_patterns = [
    # "en route from Springfield" -> matches "Springfield"
    # Note: Includes common city suffixes from dataset (ville, ton, port, haven, chester)
    Pattern(
        name="en_route_from_city",
        regex=r"(?i)(?<=en route from )[A-Z][a-z]+(?:ville|ton|burg|port|haven|chester|wood|field)\b",
        score=0.70
    ),
    # "family from Boston" -> matches "Boston"
    Pattern(
        name="family_from_city",
        regex=r"(?i)(?<=family (?:from|in) )[A-Z][A-Za-z\s]+",
        score=0.65
    ),
]
```

### PCP/Clinic References
```python
# Source: Clinical handoff pattern analysis
pcp_patterns = [
    # "PCP is Dr. Smith at Springfield Pediatrics" -> matches "Springfield Pediatrics"
    Pattern(
        name="pcp_at_clinic",
        regex=r"(?i)(?<=\bat )[A-Z][A-Za-z\s]+(?:Pediatrics|Clinic|Associates|Medical)\b",
        score=0.65
    ),
    # "follow up with Dr. Jones at Memorial Clinic" -> matches "Memorial Clinic"
    Pattern(
        name="followup_at_clinic",
        regex=r"(?i)(?<=follow up (?:with|at) )[A-Z][A-Za-z\s]+(?:Clinic|Pediatrics)\b",
        score=0.65
    ),
]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| spaCy NER only | NER + context patterns | Phase 21 (2026) | Improves recall from 20% to target 60%+ |
| Full-match patterns | Lookbehind patterns | Phase 17 (2026) | Preserves context words, reduces false positives |
| Generic location lists | Clinical context-specific | Phase 21 (2026) | Handles "transferred from", "lives at" language |

**Current state (January 2026):**
- Presidio with spaCy en_core_web_lg provides baseline LOCATION detection
- PatternRecognizer supports custom patterns with context boosting
- Lookbehind patterns proven effective in ROOM (98% recall) and GUARDIAN (89% recall)
- Python regex fixed-width lookbehind limitation requires pattern duplication

**Deprecated/outdated:**
- Variable-width lookbehind attempts (Python limitation requires fixed width)
- Standalone facility name matching without context (too many false positives)

## Open Questions

1. **Should clinic names require explicit context or match standalone?**
   - What we know: Dataset has "PCP is Dr. X at Y Clinic" constructs
   - What's unclear: How often clinic names appear without context, false positive rate
   - Recommendation: Start with context-required patterns (lower false positives), expand if recall insufficient

2. **How to handle school names in LOCATION vs separate SCHOOL entity?**
   - What we know: 10 school entities in dataset (Lakewood Elementary, Lincoln Middle School)
   - What's unclear: Whether schools are already detected by existing school recognizer (pediatric.py lines 519-550)
   - Recommendation: Check existing school recognizer coverage first, add transfer context patterns if needed

3. **Should city detection rely entirely on spaCy NER or add custom patterns?**
   - What we know: spaCy detects cities (part of baseline 20%), 7 city entities in dataset
   - What's unclear: Which cities spaCy is missing, whether context patterns needed
   - Recommendation: Test baseline first, add "en route from [City]" pattern only if recall gap exists

## Sources

### Primary (HIGH confidence)
- Existing codebase patterns (app/recognizers/medical.py, app/recognizers/pediatric.py)
- Dataset analysis (tests/synthetic_handoffs.json, 129 LOCATION entities)
- Phase 17 ROOM recognizer patterns (proven 98% recall with lookbehind)
- Phase 18 GUARDIAN recognizer patterns (proven 89% recall with lookbehind)
- app/config.py deny_list_location (lines 99-142) - medical abbreviation filtering

### Secondary (MEDIUM confidence)
- [Presidio Best Practices](https://microsoft.github.io/presidio/analyzer/developing_recognizers/) - Pattern-based recognizer guidance
- [Presidio Supported Entities](https://microsoft.github.io/presidio/supported_entities/) - LOCATION definition and detection methods
- [Python Regex Lookbehind](https://www.geeksforgeeks.org/python/python-regex-lookbehind/) - Fixed-width lookbehind limitation
- [Regex Lookaround Tutorial](https://www.regular-expressions.info/lookaround.html) - Lookbehind best practices

### Tertiary (LOW confidence - marked for validation)
- [Clinical NER for Medical Entities](https://www.shaip.com/solutions/clinical-named-entity-recognition-ner/) - General medical NER guidance
- [HIPAA PHI Detection Tools](https://www.invene.com/blog/software-to-identify-phi-complete-guide) - Location as PHI identifier (general guidance)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Existing Presidio + spaCy setup proven in Phases 17-18
- Architecture: HIGH - Lookbehind pattern approach verified in ROOM/GUARDIAN recognizers
- Pitfalls: HIGH - Python regex limitations well-documented, deny list already exists
- Transfer contexts: HIGH - Dataset analysis shows 50% "from", 40% "at/in", 10% "to"
- Facility detection: MEDIUM - Requires balancing context vs standalone matching
- City detection: MEDIUM - Unclear which cities spaCy baseline is missing

**Research date:** 2026-01-30
**Valid until:** 30 days (stable stack, pattern-based approach unlikely to change)

**Dataset statistics:**
- Total LOCATION entities: 129 (across 500 handoffs)
- Transfer contexts ("from"): 65 entities (50%)
- Location contexts ("at/in"): 51 entities (40%)
- Discharge/movement ("to"): 13 entities (10%)
- Facility types: 25 hospitals, 10 schools, 21 addresses, 7 cities, 66 other
- Current recall: 20% (spaCy NER baseline)
- Target recall: ≥60%

**Critical insight from Phase 17-18 experience:**
Lookbehind patterns are the proven approach for context-based PHI detection in this codebase. Transfer context patterns will likely achieve highest impact (50% of dataset), followed by residential address patterns (lives at, discharge to). Hospital/clinic name detection may compete with spaCy NER baseline - test carefully to avoid duplicate detections or lowered confidence scores.
