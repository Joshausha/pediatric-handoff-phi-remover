# Phase 7: Alternative Engine Benchmark - Research

**Researched:** 2026-01-25
**Domain:** PHI de-identification engines - evaluating Philter-UCSF and Stanford BERT alternatives
**Confidence:** MEDIUM

## Summary

Three de-identification engines were researched for benchmarking against the current Presidio + spaCy setup: Philter-UCSF (rule-based), Stanford BERT (transformer-based), and hybrid architectures combining both approaches.

**Key findings:**
- **Philter-UCSF**: State-of-the-art rule-based system (99.5% recall on i2b2 2006) with regex coordinate mapping, supports custom patterns but may not support lookbehind patterns
- **Stanford BERT**: Transformer model (97-99% F1 on written notes) integrates with Presidio via TransformersNlpEngine, requires entity mapping configuration
- **Current system**: 91.5% weighted recall (77.9% unweighted) on spoken handoffs - no direct benchmark exists for spoken vs written clinical text
- **Critical gap**: All benchmarks are on written clinical notes; spoken handoff performance is unknown territory

**Primary recommendation:** Benchmark all three engines on the same synthetic dataset using weighted metrics (spoken handoff relevance) as the primary decision criterion. Plan for pattern translation challenges, especially lookbehind patterns for Philter.

## Standard Stack

The established de-identification engines and frameworks:

### Core Engines
| Engine | Type | Performance (i2b2) | Why Standard |
|--------|------|-------------------|--------------|
| **Philter-UCSF** | Rule-based | 99.5% recall | State-of-the-art coordinate mapping, clinical focus |
| **Stanford BERT** | Transformer | 97.9-99.6% F1 | Best-in-class ML model, multi-institutional validation |
| **Presidio** | Hybrid | 90-93% recall | Microsoft-backed, modular architecture |

### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `philter-ucsf` | Latest | Standalone rule-based de-ID | Independent benchmark |
| `transformers` | 4.x | HuggingFace model loading | Stanford BERT integration |
| `presidio-analyzer` | 2.2.354 | Current NER framework | Baseline + BERT backend |
| `presidio-evaluator` | 0.2.4+ | Evaluation metrics | Benchmark comparison |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Philter-UCSF | Philter-lite (production fork) | Lighter weight but less documented |
| Stanford BERT | BioClinicalBERT | Similar performance, different training corpus |
| Presidio | NLM Scrubber | Simpler but lower recall (87.8%) |

**Installation:**
```bash
# Philter-UCSF
pip install philter-ucsf

# Stanford BERT + Presidio integration
pip install transformers torch
pip install presidio-analyzer presidio-anonymizer

# For evaluation
pip install presidio-evaluator numpy
```

## Architecture Patterns

### Philter-UCSF: Coordinate Mapping System

Philter uses a two-phase approach: **map coordinates** (dry-run pattern matching) then **transform** (apply redaction).

**Pattern definition structure:**
```json
{
  "patterns": [
    {
      "title": "guardian_names",
      "type": "regex",
      "filepath": "./patterns/guardian_regex.txt",
      "exclude": true,
      "phi_type": "GUARDIAN_NAME"
    },
    {
      "title": "clinical_abbreviations",
      "type": "set",
      "filepath": "./patterns/medical_abbrev.pkl",
      "exclude": false
    }
  ]
}
```

**Supported pattern types:**
- `regex` - Standard regex patterns (compiled from .txt files)
- `set` - Dictionary/word list matching (.pkl or .json files)
- `regex_context` - Regex patterns that require adjacent PHI context
- `stanford_ner` - Named entity recognition via Stanford NER tagger
- `pos_matcher` - Part-of-speech tag filtering
- `match_all` - Catch-all pattern

**Python API:**
```python
from philter_ucsf import Philter

config = {
    "verbose": True,
    "finpath": "./input_notes/",
    "foutpath": "./output_filtered/",
    "filters": "./filters/phi_patterns.json",
    "outformat": "asterisk",  # or "i2b2"
    "cachepos": "./data/pos_cache/"
}

philter = Philter(config)
philter.map_coordinates()  # Identify PHI locations
philter.transform()         # Replace identified PHI
```

**Allow/Deny list support:**
- `"exclude": true` - Deny list (mark for removal/masking)
- `"exclude": false` - Allow list (preserve these terms)
- Coordinate mapping tracks overlapping regions and resolves conflicts

### Stanford BERT: TransformersNlpEngine Backend

Stanford BERT runs **inside Presidio** as an NLP engine replacement, not standalone.

**Configuration approach:**
```python
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer, AutoModelForTokenClassification

# Download Stanford model
snapshot_download(repo_id="StanfordAIMI/stanford-deidentifier-base")

# Configure TransformersNlpEngine
nlp_config = {
    "nlp_engine_name": "transformers",
    "models": [{
        "lang_code": "en",
        "model_name": {
            "spacy": "en_core_web_sm",  # For tokenization
            "transformers": "StanfordAIMI/stanford-deidentifier-base"
        }
    }]
}

# Entity mapping (Stanford labels → Presidio entities)
entity_mapping = {
    "PATIENT": "PERSON",
    "STAFF": "PERSON",
    "HOSP": "LOCATION",
    "HOSPITAL": "LOCATION",
    "FACILITY": "LOCATION",
    # ... more mappings
}

# Create analyzer with BERT backend
provider = NlpEngineProvider(nlp_configuration=nlp_config)
nlp_engine = provider.create_engine()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
```

**Entity mapping configuration:**
- `alignment_mode`: "strict" (exact match), "contract" (shorter span), "expand" (longer span)
- `aggregation_strategy`: "simple", "first", "average", or "max"
- `labels_to_ignore`: Entities to exclude (e.g., "O" for outside entities)

**Custom recognizers compatibility:**
- Custom PatternRecognizers work alongside TransformersNlpEngine
- Presidio merges BERT NER results with custom pattern results
- No modification needed to existing custom recognizers

### Hybrid Architecture: Multiple NER Engines

Presidio supports running **multiple NER models in parallel** for hybrid approaches.

**Pattern 1: BERT + Custom Patterns**
```python
# Use TransformersNlpEngine for general NER
nlp_engine = create_transformers_engine()

# Add custom recognizers for pediatric patterns
registry = RecognizerRegistry()
registry.load_predefined_recognizers(nlp_engine=nlp_engine)

# Add custom patterns (e.g., lookbehind patterns BERT can't handle)
registry.add_recognizer(GuardianNameRecognizer())
registry.add_recognizer(RoomNumberRecognizer())

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
```

**Pattern 2: Multiple Transformer Models**
```python
# Create separate recognizers for different transformer models
stanford_recognizer = TransformersRecognizer(
    model_path="StanfordAIMI/stanford-deidentifier-base"
)
bioclinical_recognizer = TransformersRecognizer(
    model_path="emilyalsentzer/Bio_ClinicalBERT"
)

# Add both to registry
registry.add_recognizer(stanford_recognizer)
registry.add_recognizer(bioclinical_recognizer)
```

**Pattern 3: Philter + Presidio Cascade**
```python
# Run Presidio first (fast, high precision)
presidio_result = presidio_analyzer.analyze(text)

# Run Philter on same text (slower, high recall)
philter_result = philter.map_coordinates()

# Merge results (union for maximum recall)
merged_spans = merge_phi_spans(presidio_result, philter_result)
```

### Anti-Patterns to Avoid

- **Don't run engines sequentially on redacted text** - Each engine should analyze the original text independently, then merge results
- **Don't assume written note patterns transfer** - Spoken handoffs have different PHI distributions (no addresses, more informal names)
- **Don't skip deny list filtering for BERT** - Transformer models still flag common words (e.g., "NC" as North Carolina)
- **Don't forget model size** - BERT models (~110M parameters, ~210MB VRAM) require GPU or slow CPU inference

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| **Span overlap resolution** | Custom merge logic | Presidio's built-in span merger | Handles nested/overlapping entities, priority ordering |
| **Entity mapping** | Manual label conversion | TransformersNlpEngine config | Standardized mapping with alignment modes |
| **Benchmark metrics** | Custom precision/recall | presidio-evaluator | Bootstrap CI, per-entity metrics, weighted scoring |
| **Coordinate tracking** | Index arithmetic | Philter coordinate maps | Handles multi-byte chars, resolves conflicts |
| **Pattern file management** | Inline regex | Philter JSON config | Separation of patterns from code, reusable filters |

**Key insight:** De-identification engines have mature ecosystems. Custom benchmark code is needed for weighted metrics and spoken handoff evaluation, but core engine functionality should never be reimplemented.

## Common Pitfalls

### Pitfall 1: Lookbehind Pattern Translation

**What goes wrong:** Philter may not support lookbehind patterns (e.g., `(?<=mom )[a-z]+`) used extensively in current pediatric recognizers.

**Why it happens:** Philter's regex engine may be limited to standard Python `re` module features, and lookbehind patterns are complex.

**How to avoid:**
- Test lookbehind support early with simple pattern (e.g., `(?<=test )\w+`)
- If unsupported, rewrite patterns to capture full match: `\b(?:mom|dad)\s+([a-z]+)\b` and extract group 1
- Document pattern limitations in BENCH-02 (engine configuration)

**Warning signs:**
- Philter config JSON accepts pattern but produces zero matches
- Error messages about "unsupported regex feature"
- Patterns work in Python `re.search()` but not in Philter

### Pitfall 2: Benchmark Dataset Annotation Quality

**What goes wrong:** Benchmarking on low-quality synthetic data produces misleading comparisons.

**Why it happens:** Ground truth annotations may have errors, missing entities, or inconsistent labeling.

**How to avoid:**
- Spot-check 10-20 samples manually before full benchmark (CONTEXT.md decision)
- Look for annotation consistency (all "Mom Jessica" instances labeled?)
- Verify adversarial cases are properly labeled (edge cases like "#12345678" MRN)
- Fix discovered annotation issues for ALL engines to keep comparison fair

**Warning signs:**
- Engine detects PHI not in ground truth (false positive or annotation gap?)
- High FN rate on patterns that should work (missing ground truth annotations?)
- Per-entity metrics show unexpected patterns (e.g., 100% EMAIL recall on 0 examples)

### Pitfall 3: BERT Entity Type Mismatch

**What goes wrong:** Stanford BERT outputs entity types that don't map cleanly to Presidio's standard types.

**Why it happens:** BERT was trained on radiology reports with domain-specific labels (PATIENT, STAFF, HOSP) rather than HIPAA categories.

**How to avoid:**
- Create comprehensive entity mapping dict upfront
- Test mapping with sample text before full benchmark
- Map multiple BERT entities to single Presidio entity (PATIENT + STAFF → PERSON)
- Document mapping decisions in benchmark report

**Warning signs:**
- Unknown entity types in BERT output
- Expected entities missing (BERT detected but mapping dropped them)
- Lower recall than expected (mapping too strict, dropping valid detections)

### Pitfall 4: Written vs Spoken Performance Gap

**What goes wrong:** Engines with 99% recall on i2b2 (written notes) may perform worse on spoken transcripts.

**Why it happens:**
- Spoken: stutters, repetitions ("mom mom Jessica"), filler words ("mom uh Sarah")
- Informal: "Baby Smith" not "Patient: Smith, Baby Girl"
- Missing PHI types: no addresses, no email addresses (weight 0 in spoken metric)
- Extra noise: ASR errors, non-standard capitalization

**How to avoid:**
- Use weighted metrics as primary evaluation (spoken handoff relevance)
- Don't assume i2b2 performance transfers directly
- Test on both clean synthetic and adversarial datasets
- Document spoken-specific challenges in benchmark report

**Warning signs:**
- High performance on standard dataset, poor on adversarial
- Pattern-based engines outperform BERT (BERT trained on written text)
- Guardian name patterns fail (speech artifacts not in training data)

### Pitfall 5: Model Size and Inference Speed

**What goes wrong:** BERT models are slow without GPU acceleration, making benchmark impractical.

**Why it happens:** Stanford BERT is ~110M parameters, requires ~210MB VRAM, inference is 10-100x slower than spaCy on CPU.

**How to avoid:**
- Check available GPU before starting BERT benchmark
- Batch processing for BERT (process multiple handoffs per model call)
- Use smaller test subset for initial BERT testing (50 samples before full 600)
- Document inference time alongside accuracy metrics

**Warning signs:**
- Benchmark script times out or takes hours
- High CPU usage, system unresponsive
- Out-of-memory errors on large handoffs

## Code Examples

Verified patterns from official sources:

### Philter Configuration: Custom Pattern File

```python
# configs/pediatric_patterns.json
{
  "patterns": [
    {
      "title": "guardian_names_mom",
      "type": "regex",
      "filepath": "./patterns/guardian_mom.txt",
      "exclude": true,
      "phi_type": "GUARDIAN_NAME"
    },
    {
      "title": "room_numbers",
      "type": "regex",
      "filepath": "./patterns/room_patterns.txt",
      "exclude": true,
      "phi_type": "ROOM"
    },
    {
      "title": "medical_abbreviations_allow",
      "type": "set",
      "filepath": "./patterns/med_abbrev.json",
      "exclude": false  # Allow list - preserve these
    }
  ]
}

# patterns/guardian_mom.txt (regex file - one pattern per line)
(?i)\bmom\s+[a-z]{2,}\b
(?i)\bmother\s+[a-z]{2,}\b
(?i)\bmommy\s+[a-z]{2,}\b

# patterns/med_abbrev.json (set file)
["NC", "RA", "OR", "ER", "IV", "PO", "PICU", "NICU"]
```

### Stanford BERT: Presidio Integration

```python
# Source: https://microsoft.github.io/presidio/analyzer/nlp_engines/transformers/
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

# Configuration for Stanford BERT
nlp_config = {
    "nlp_engine_name": "transformers",
    "models": [{
        "lang_code": "en",
        "model_name": {
            "spacy": "en_core_web_sm",
            "transformers": "StanfordAIMI/stanford-deidentifier-base"
        }
    }],
    "transformers_config": {
        "alignment_mode": "expand",
        "aggregation_strategy": "simple",
        "labels_to_ignore": ["O"]
    }
}

provider = NlpEngineProvider(nlp_configuration=nlp_config)
nlp_engine = provider.create_engine()

# Create analyzer with BERT backend
analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

# Analyze text (same API as spaCy-based Presidio)
results = analyzer.analyze(
    text="Mom Jessica brought Baby Smith to PICU bed 3",
    language="en",
    entities=["PERSON", "LOCATION"]
)
```

### Weighted Metrics Evaluation

```python
# Source: Current codebase (tests/evaluate_presidio.py)
from tests.evaluate_presidio import EvaluationMetrics
from app.config import settings

# After running evaluation and populating entity_stats
metrics = EvaluationMetrics()
metrics.entity_stats = {
    "PERSON": {"tp": 747, "fn": 9, "fp": 79},
    "ROOM": {"tp": 31, "fn": 59, "fp": 24},
    "PHONE_NUMBER": {"tp": 142, "fn": 50, "fp": 1},
    "DATE_TIME": {"tp": 184, "fn": 6, "fp": 334},
    # ... more entities
}

# Get spoken handoff weights
weights = settings.spoken_handoff_weights
# {
#   "PERSON": 5,
#   "GUARDIAN_NAME": 5,
#   "ROOM": 4,
#   "PHONE_NUMBER": 2,
#   "DATE_TIME": 2,
#   "MEDICAL_RECORD_NUMBER": 1,
#   "EMAIL_ADDRESS": 0,
#   "LOCATION": 0,
#   "PEDIATRIC_AGE": 0
# }

# Calculate weighted metrics
weighted_recall = metrics.weighted_recall(weights)     # 91.5%
weighted_precision = metrics.weighted_precision(weights)  # 79.7%
weighted_f2 = metrics.weighted_f2(weights)             # 88.8%

print(f"Weighted recall: {weighted_recall:.1%}")
print(f"Unweighted recall: {metrics.recall:.1%}")
print(f"Improvement: +{(weighted_recall - metrics.recall):.1%}")
```

### Hybrid Approach: BERT + Custom Patterns

```python
# Source: https://microsoft.github.io/presidio/analyzer/nlp_engines/transformers/
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from app.recognizers import get_pediatric_recognizers, get_medical_recognizers

# Create BERT-based NLP engine
nlp_config = {
    "nlp_engine_name": "transformers",
    "models": [{
        "lang_code": "en",
        "model_name": {
            "spacy": "en_core_web_sm",
            "transformers": "StanfordAIMI/stanford-deidentifier-base"
        }
    }]
}

provider = NlpEngineProvider(nlp_configuration=nlp_config)
nlp_engine = provider.create_engine()

# Create registry with BERT + custom pediatric patterns
registry = RecognizerRegistry()
registry.load_predefined_recognizers(nlp_engine=nlp_engine)

# Add custom recognizers (handle patterns BERT misses)
for recognizer in get_pediatric_recognizers():
    registry.add_recognizer(recognizer)

for recognizer in get_medical_recognizers():
    registry.add_recognizer(recognizer)

# Create analyzer with hybrid approach
analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)

# Analyze with both BERT and custom patterns
results = analyzer.analyze(
    text="Mom Jessica brought Baby Smith to PICU bed 3",
    language="en"
)
# Results include:
# - BERT detections (general person names)
# - Custom pattern detections (guardian context, room numbers)
```

## State of the Art

| Approach | Recall (i2b2) | Precision (i2b2) | Notes |
|----------|---------------|------------------|-------|
| **Philter-UCSF** | 99.5% | ~90% | State-of-the-art rule-based, i2b2 2006 |
| **Stanford BERT** | 99.1-99.6% | ~95% | Best transformer model, multi-institutional |
| **This system (weighted)** | 91.5% | 79.7% | Spoken handoffs (no direct benchmark) |
| **Presidio baseline** | 90-93% | 85-90% | General-purpose de-ID framework |
| **BioClinicalBERT** | 97-98% | ~95% | Alternative transformer option |
| **NLM Scrubber** | 87.8% | ~85% | Older rule-based baseline |

### Written Notes vs Spoken Handoffs

**Critical context:** All benchmarks above are for **written clinical notes** (discharge summaries, progress notes, radiology reports). No published benchmark exists for **spoken pediatric handoffs**.

| Dimension | Written Notes (i2b2) | Spoken Handoffs (This Project) |
|-----------|---------------------|--------------------------------|
| **Structure** | Formatted, complete sentences | Conversational, informal |
| **PHI types** | Full addresses common | Addresses never spoken |
| **Capitalization** | Proper nouns capitalized | ASR may miss capitalization |
| **Artifacts** | Typos, abbreviations | Stutters, fillers ("um", "uh") |
| **Name formats** | "Patient: Smith, John" | "Baby Smith", "Mom Jessica" |
| **Benchmark** | i2b2 2006/2014 (1,304 notes) | No standard (custom synthetic) |

**Implication:** Engines with 99% recall on written notes may perform **worse** on spoken handoffs due to:
1. Speech artifacts not in training data
2. Missing PHI types (no addresses to pad recall)
3. Informal naming patterns ("Baby LastName")
4. ASR errors and non-standard formatting

### Recent Advances (2024-2025)

**Transformer dominance:** BERT-based models now outperform rule-based systems on written notes, but rule-based systems remain competitive for:
- Local deployment (no cloud API)
- Interpretability (know why it flagged)
- Speed (CPU-friendly)
- Custom pattern control

**Hybrid approaches:** State-of-the-art systems combine transformers (high recall on general names) with rule-based patterns (specific contexts like guardian relationships).

## Open Questions

Things that couldn't be fully resolved:

1. **Philter lookbehind support**
   - What we know: Philter supports standard Python regex patterns
   - What's unclear: Whether lookbehind patterns (`(?<=mom )[a-z]+`) are supported
   - Recommendation: Test early with simple lookbehind, have fallback rewrite plan

2. **Stanford BERT inference speed without GPU**
   - What we know: BERT models are ~110M parameters, require ~210MB VRAM
   - What's unclear: Practical CPU inference time on 600 handoffs (could be hours)
   - Recommendation: Benchmark on 50-sample subset first, estimate full runtime

3. **Entity mapping completeness**
   - What we know: Stanford BERT outputs PATIENT, STAFF, HOSP, FACILITY labels
   - What's unclear: Complete list of output labels and edge cases
   - Recommendation: Run on sample text, document all observed labels before mapping

4. **Philter pattern file format**
   - What we know: Regex patterns stored in .txt files (one per line), sets in .pkl/.json
   - What's unclear: Whether regex files support comments, escaping, multi-line patterns
   - Recommendation: Review example pattern files in Philter GitHub repo before translation

5. **Hybrid architecture decision criteria**
   - What we know: Can run multiple engines in parallel or cascade
   - What's unclear: When hybrid beats single best engine (added complexity vs accuracy gain)
   - Recommendation: If no engine beats Presidio by >5%, prototype simple hybrid (BERT for PERSON, Presidio for custom)

## Sources

### Primary (HIGH confidence)
- Philter-UCSF GitHub: https://github.com/BCHSI/philter-ucsf (code review, API structure)
- Presidio Transformers docs: https://microsoft.github.io/presidio/analyzer/nlp_engines/transformers/ (BERT integration)
- Stanford model on HuggingFace: https://huggingface.co/StanfordAIMI/stanford-deidentifier-base (performance metrics)
- Current codebase: `tests/evaluate_presidio.py`, `app/recognizers/` (benchmark framework, custom patterns)

### Secondary (MEDIUM confidence)
- Presidio TransformersRecognizer sample: https://microsoft.github.io/presidio/samples/python/transformers_recognizer/ (verified with official docs)
- i2b2 de-identification challenge: https://pmc.ncbi.nlm.nih.gov/articles/PMC4989908/ (benchmark context)
- BERT model performance article: https://huggingface.co/google-bert/bert-base-uncased/discussions/53 (model size estimates)

### Tertiary (LOW confidence - requires validation)
- Philter performance claims: Multiple blog posts cite 99.5% recall, but original Nature paper paywall-blocked
- BERT inference speed: General estimates from community posts, not Stanford model specifically
- Spoken vs written de-ID: No published research found comparing performance on these domains

## Metadata

**Confidence breakdown:**
- Philter installation/API: HIGH - Verified via GitHub code review
- Stanford BERT integration: HIGH - Official Presidio documentation with code examples
- Pattern translation feasibility: MEDIUM - Lookbehind support needs testing
- Benchmark methodology: HIGH - Current codebase provides proven framework
- Hybrid architectures: MEDIUM - Presidio supports it, but optimal design unclear

**Research date:** 2026-01-25
**Valid until:** 60 days (transformer models evolving fast, but established engines stable)

**Critical gaps requiring validation during implementation:**
1. Philter lookbehind pattern support (test in BENCH-02)
2. Stanford BERT CPU inference time (test in BENCH-03)
3. Annotation quality in synthetic dataset (spot-check before full benchmark)
4. Complete Stanford BERT entity label set (document during integration)
