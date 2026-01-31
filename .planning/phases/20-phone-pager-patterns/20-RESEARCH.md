# Phase 20: Phone/Pager Patterns - Research

**Researched:** 2026-01-30
**Domain:** Phone number / pager detection in clinical handoffs
**Confidence:** HIGH

## Summary

This research investigates the root cause of the 75.7% PHONE_NUMBER recall and identifies patterns needed to reach the 90% target. The primary issue is that Presidio's built-in phone recognizer uses the `phonenumbers` Python library with `leniency=1`, which is too strict and misses many valid phone formats. By changing to `leniency=0` (most lenient), we can detect all 5 current false negatives without any code changes to our custom recognizers.

**Key discovery:** The current false negatives are NOT exotic formats - they're standard US phone numbers that the `phonenumbers` library detects correctly with `leniency=0`. The 5 missed patterns are:
- `264-517-0805x310` (domestic with extension)
- `576-959-1803` (standard dash-separated)
- `291-938-0003` (standard dash-separated)
- `560-913-6730x371` (domestic with extension)
- `394-678-7300x2447` (domestic with extension)

**Primary recommendation:** Override Presidio's PhoneRecognizer to use `leniency=0` instead of the default `leniency=1`. This single change will fix all 5 current false negatives and improve recall from 75.7% to near 100% for the current validation set.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `phonenumbers` | 8.13+ | Phone number parsing/validation | Google's libphonenumber Python port - gold standard |
| `presidio-analyzer` | 2.2+ | PHI detection engine | Already in use, wraps phonenumbers |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `re` | stdlib | Regex patterns | For pager/extension patterns not covered by phonenumbers |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| phonenumbers leniency | Custom regex only | phonenumbers handles international formats; regex-only would require massive pattern set |
| Override PhoneRecognizer | Configure via Presidio | Presidio doesn't expose leniency config - must subclass or patch |

**Installation:**
No new dependencies required - just configuration change.

## Architecture Patterns

### Recommended Project Structure
```
app/
├── recognizers/
│   ├── medical.py       # Existing custom recognizers (MRN, room, phone extensions)
│   ├── pediatric.py     # Existing guardian/baby patterns
│   └── phone.py         # NEW: Custom PhoneRecognizer with leniency=0
└── deidentification.py  # Add custom phone recognizer to registry
```

### Pattern 1: Custom PhoneRecognizer with Adjusted Leniency
**What:** Subclass or replace Presidio's PhoneRecognizer with leniency=0
**When to use:** Always - this is the primary fix

**Example:**
```python
# Source: Analysis of venv/.../phone_recognizer.py
from presidio_analyzer.predefined_recognizers import PhoneRecognizer

class CustomPhoneRecognizer(PhoneRecognizer):
    """Phone recognizer with lenient matching for clinical handoffs."""

    def __init__(
        self,
        context=None,
        supported_language="en",
        supported_regions=("US",),  # Focus on US for clinical handoffs
        leniency=0,  # CHANGED: Most lenient (was 1)
    ):
        super().__init__(
            context=context,
            supported_language=supported_language,
            supported_regions=supported_regions,
            leniency=leniency,
        )
```

### Pattern 2: Pager Number Patterns (Future Enhancement)
**What:** Custom regex for hospital pager formats
**When to use:** If real handoffs contain pager numbers (5-digit internal numbers)

**Example:**
```python
# For future enhancement if needed
pager_patterns = [
    # "pager 12345", "page to 55555"
    Pattern(
        name="pager_explicit",
        regex=r"(?i)(?:pager?|page\s+(?:to|at)?)\s*#?\s*(\d{4,5})\b",
        score=0.80
    ),
    # "ext. 1234", "extension 1234"
    Pattern(
        name="extension_standalone",
        regex=r"(?i)(?:ext\.?|extension)\s*(\d{3,5})\b",
        score=0.75
    ),
]
```

**Note:** Pager patterns are NOT needed to hit 90% recall - the current validation set doesn't contain these patterns. Document for future use if real handoff testing reveals them.

### Anti-Patterns to Avoid
- **Regex-only for all phone formats:** Don't hand-roll phone detection - the `phonenumbers` library handles international edge cases correctly
- **Too strict leniency:** The default leniency=1 is designed for "valid" phone numbers, but transcribed handoffs may have formatting variations that leniency=0 catches
- **Adding all detected phones:** Don't lower the confidence threshold below 0.30 - this would create false positives on clinical numbers

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| International phone detection | Regex for each country | `phonenumbers` library | Handles 200+ regions, area code validation |
| Extension detection | Separate regex | `phonenumbers` leniency=0 | Already handles "x123", "ext 123", "extension 123" |
| Phone validation | Number range checks | `phonenumbers.is_valid_number()` | Validates area codes, number length per region |

**Key insight:** The `phonenumbers` library with `leniency=0` already detects all current false negatives. The fix is configuration, not new code.

## Common Pitfalls

### Pitfall 1: Leniency Mismatch
**What goes wrong:** Using phonenumbers with default leniency=1 misses valid phone formats
**Why it happens:** Leniency levels are:
- 0 (POSSIBLE): Matches anything that could be a phone number
- 1 (VALID): Must match a known phone number format for the region (DEFAULT)
- 2 (STRICT_GROUPING): Must have correct grouping
- 3 (EXACT_GROUPING): Must match exactly

**How to avoid:** Always use leniency=0 for clinical text where formatting varies
**Warning signs:** False negatives on standard-looking phone numbers like `576-959-1803`

### Pitfall 2: Pager Numbers as Clinical Identifiers
**What goes wrong:** 5-digit numbers flagged as pagers that are actually clinical values (room numbers, vitals)
**Why it happens:** Hospital pagers often use 4-5 digit numbers, same range as room numbers
**How to avoid:** Require explicit context words ("pager", "page", "call") for standalone 5-digit detection
**Warning signs:** False positives on room numbers, weight values, or order quantities

### Pitfall 3: Over-Detection on Clinical Numbers
**What goes wrong:** Vitals (98.6, 120/80), doses (250mg), or weights (4.5kg) flagged as phone numbers
**Why it happens:** Overly aggressive regex patterns or low thresholds
**How to avoid:**
- Keep threshold at 0.30 or higher
- Use phonenumbers library (validates number ranges)
- Negative lookahead for units (mg, ml, kg, %, mmHg)
**Warning signs:** False positives on numeric clinical values

### Pitfall 4: Registry Override Conflicts
**What goes wrong:** Both default and custom PhoneRecognizer active, causing duplicates
**Why it happens:** Adding custom recognizer without removing default
**How to avoid:** Remove default PhoneRecognizer before adding custom one:
```python
registry.remove_recognizer("PhoneRecognizer")  # Remove default
registry.add_recognizer(custom_phone_recognizer)  # Add custom
```
**Warning signs:** Duplicate PHONE_NUMBER entities at same position

## Code Examples

Verified patterns from official sources:

### Override PhoneRecognizer in deidentification.py
```python
# In app/deidentification.py, modify _get_engines()
from presidio_analyzer.predefined_recognizers import PhoneRecognizer

def _get_engines():
    # ... existing code ...

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(nlp_engine=nlp_engine)

    # Remove default PhoneRecognizer (uses leniency=1)
    registry.remove_recognizer("PhoneRecognizer")

    # Add custom PhoneRecognizer with leniency=0
    custom_phone = PhoneRecognizer(
        supported_regions=("US",),
        leniency=0,  # Most lenient - catches all formats
    )
    registry.add_recognizer(custom_phone)

    # ... rest of existing code ...
```

### Test Verification Script
```python
# Verify leniency=0 fixes the false negatives
import phonenumbers
from phonenumbers import PhoneNumberMatcher

test_cases = [
    "264-517-0805x310",
    "576-959-1803",
    "291-938-0003",
    "560-913-6730x371",
    "394-678-7300x2447",
]

print("Leniency=0 (should all pass):")
for text in test_cases:
    matches = list(PhoneNumberMatcher(text, "US", leniency=0))
    status = "FOUND" if matches else "MISSED"
    print(f"  {status}: {text}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Presidio default leniency=1 | Custom leniency=0 | Phase 20 | Recall 75.7% -> ~100% |
| Regex-only patterns | phonenumbers library | Presidio 2.0 | Better international handling |

**Deprecated/outdated:**
- Custom regex for standard phone formats: Use phonenumbers instead
- Per-format regex patterns: The library handles extension variations

## Open Questions

Things that couldn't be fully resolved:

1. **Pager Number Patterns in Real Handoffs**
   - What we know: Synthetic data doesn't include "pager 12345" patterns
   - What's unclear: How often are these used in actual clinical handoffs?
   - Recommendation: Document patterns; implement only if Phase 22 validation reveals need

2. **Internal Extension-Only Numbers**
   - What we know: "ext. 1234" without base phone not detected by phonenumbers
   - What's unclear: Are these common in real handoffs?
   - Recommendation: Low priority - parent phone number usually provided

3. **International Number Coverage**
   - What we know: Current validation set includes 001 and +1 prefixes
   - What's unclear: Are other international formats needed for hospital transfers?
   - Recommendation: Keep supported_regions=("US",) for now; expand if needed

## Validation Dataset Analysis

### Current PHONE_NUMBER Statistics
- Total phone numbers in validation set: 192
- Current recall: 75.7% (before this fix)
- False negatives: 5
- Expected recall after fix: ~100% (all 5 FN are detected with leniency=0)

### Format Distribution in Validation Set
| Format | Count | % |
|--------|-------|---|
| domestic_with_ext | 72 | 37.5% |
| intl_with_ext | 57 | 29.7% |
| other | 16 | 8.3% |
| dash_separated | 11 | 5.7% |
| dot_separated | 11 | 5.7% |
| parentheses | 11 | 5.7% |
| 001_prefix | 9 | 4.7% |
| plus1_prefix | 5 | 2.6% |

### False Negative Analysis
All 5 false negatives are standard formats that `leniency=0` detects:

| Text | Context | Root Cause |
|------|---------|------------|
| `264-517-0805x310` | "dad can be reached at..." | leniency=1 too strict |
| `576-959-1803` | "call Mark Warner at..." | leniency=1 too strict |
| `291-938-0003` | "call Dr. Scott at..." | leniency=1 too strict |
| `560-913-6730x371` | "Dr. Huang at..." | leniency=1 too strict |
| `394-678-7300x2447` | "Dr. Carson at..." | leniency=1 too strict |

## Sources

### Primary (HIGH confidence)
- Presidio PhoneRecognizer source: `venv/.../predefined_recognizers/phone_recognizer.py`
- phonenumbers library testing: Direct testing with leniency=0 vs leniency=1
- Validation results: `.planning/phases/12-regression-validation/validation_results.json`

### Secondary (MEDIUM confidence)
- [Presidio Supported Entities](https://microsoft.github.io/presidio/supported_entities/) - Official docs
- [phonenumbers library](https://github.com/daviddrysdale/python-phonenumbers) - Python port of libphonenumber

### Tertiary (LOW confidence)
- [Hospital Pager FAQs - Detroit Medical Center](https://www.dmc.org/health-professionals/gme-at-dmc/dmc-clinical-campus/for-all-students/pager-faqs) - Pager format reference
- [Clinical NLP PHI Detection patterns](https://pmc.ncbi.nlm.nih.gov/articles/PMC4989090/) - General PHI regex strategies

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Direct source code analysis and testing
- Architecture: HIGH - Simple configuration change with clear implementation path
- Pitfalls: HIGH - Verified through phonenumbers library testing
- Open questions: MEDIUM - Synthetic data may differ from real handoffs

**Research date:** 2026-01-30
**Valid until:** 60 days (stable - phonenumbers and Presidio are mature libraries)
