# Testing Patterns

**Analysis Date:** 2026-01-23

## Test Framework

**Runner:**
- pytest 7.x
- Config: `pytest.ini` with custom markers and output settings

**Assertion Library:**
- pytest built-in assertions (standard `assert` statements)

**Run Commands:**
```bash
# Run all tests
pytest tests/test_deidentification.py -v

# Run fast tests only (skip bulk synthetic tests)
pytest tests/test_deidentification.py -v -k "not bulk"

# Run bulk synthetic dataset tests
pytest tests/test_deidentification.py -v -k "bulk"

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Isolated Presidio test harness (no pytest needed)
python test_presidio.py

# Interactive Presidio testing
python test_presidio.py -i

# Start development server for manual testing
uvicorn app.main:app --reload
```

**Async Support:**
- `pytest-asyncio==0.23.4` configured in `pyproject.toml`
- `asyncio_mode = "auto"` enables automatic async fixture/test detection
- HTTP client testing: `httpx` library for async HTTP calls

## Test File Organization

**Location:**
- Main test suite: `tests/test_deidentification.py` (co-located with source code's logical domain)
- Standalone harness: `test_presidio.py` at project root (directly runnable, no pytest needed)
- Test helpers/data generators: `tests/` directory (generate_test_data.py, sample_transcripts.py, etc.)

**Naming:**
- Test files: `test_*.py` prefix
- Test classes: `Test*` (e.g., `TestDeidentification`, `TestValidation`, `TestSyntheticDataset`)
- Test functions: `test_*` (e.g., `test_removes_person_names`, `test_bulk_person_detection`)
- Custom markers: `@pytest.mark.bulk` to separate synthetic dataset tests

**Structure:**
```
tests/
├── test_deidentification.py       # Main test suite with 4 test classes
├── sample_transcripts.py          # Curated samples with expected PHI/content
├── generate_test_data.py          # Synthetic handoff generator with templates
├── evaluate_presidio.py           # Presidio evaluation metrics (recall/precision)
├── handoff_templates.py           # Template strings for synthetic generation
├── medical_providers.py           # Medical provider data for generation
├── __init__.py
└── synthetic_handoffs.json        # Pre-generated synthetic dataset (committed)
```

## Test Structure

**Suite Organization** (from `app/deidentification.py`):

```python
class TestDeidentification:
    """Test PHI de-identification functionality."""

    def test_removes_person_names(self):
        """Test that person names are detected and removed."""
        text = "Patient Sarah Johnson presented to the ED."
        result = deidentify_text(text)

        assert "[NAME]" in result.clean_text or "[Name]" in result.clean_text
        assert "Sarah" not in result.clean_text
        assert "Johnson" not in result.clean_text
```

**Patterns:**
- Setup: Direct variable creation in test function (no `setUp()` method)
- Execution: Call the public function being tested
- Assertion: Multiple assertions per test to verify related aspects
- Teardown: Implicit (deidentify_text has no side effects needing cleanup)

**Fixture pattern** (synthetic tests):
```python
@pytest.fixture(scope="class")
def generator(self):
    """Create a generator with fixed seed for reproducibility."""
    return PediatricHandoffGenerator(seed=42)

@pytest.mark.bulk
def test_bulk_person_detection(self, generator, evaluator):
    """Test that all PERSON entities are detected in bulk samples."""
    # Use fixtures in test
    dataset = generator.generate_dataset(n_samples=50)
```

## Mocking

**Framework:** Not used
- All tests are integration tests against real Presidio engine
- No mocking of de-identification or transcription

**Why no mocking:**
- De-identification is the critical safety path; real Presidio behavior essential
- Tests validate actual entity detection (not logic branches)
- Performance is acceptable for full test suite

**What NOT to Mock:**
- Presidio engines (AnalyzerEngine, AnonymizerEngine) - must test real detection
- spaCy NER model - must test real named entity recognition
- Transcription - use actual Whisper model or skip transcription tests

## Fixtures and Factories

**Test Data** (from `tests/sample_transcripts.py`):
```python
SAMPLE_TRANSCRIPTS = [
    {
        "id": 1,
        "text": "Patient Sarah Johnson with phone 555-867-5309...",
        "expected_removed": ["Sarah", "Johnson", "555-867-5309"],
        "expected_preserved": ["Patient", "bronchiolitis"]
    },
    # ... more samples
]

EXPECTED_OUTPUTS = {
    1: {
        "input": "...",
        "should_contain": ["Patient", "bronchiolitis"]
    }
}
```

**Synthetic Generation** (from `tests/generate_test_data.py`):
```python
class PediatricHandoffGenerator:
    def __init__(self, seed=None):
        # Initialize faker with seed for reproducibility
        pass

    def generate_dataset(self, n_samples=100, templates=None):
        # Generate synthetic handoffs with labeled PHI spans
        pass
```

**Location:**
- Curated samples: `tests/sample_transcripts.py`
- Synthetic generator: `tests/generate_test_data.py`
- Medical provider data: `tests/medical_providers.py`
- Handoff templates: `tests/handoff_templates.py`
- Seed-based reproducibility for all generators

## Coverage

**Requirements:** Not formally enforced in CI
- Target: 80%+ coverage on `app/` modules
- Critical paths must have >90% coverage (de-identification, transcription)

**View Coverage:**
```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Types

**Unit Tests:**
- Scope: Individual functions with simple inputs
- Approach: Test single responsibility (name detection, phone detection, etc.)
- Examples:
  - `test_removes_person_names` - validates name entity removal
  - `test_preserves_medical_content` - validates clinical terms not over-redacted
  - `test_catches_mrn_patterns` - validates MRN recognition

**Integration Tests:**
- Scope: Multi-function workflows (transcription + de-identification)
- Approach: Full pipeline validation
- Example: `TestSampleTranscripts.test_sample_transcript` - end-to-end on real transcripts

**Synthetic/Bulk Tests:**
- Scope: Large-scale validation against generated data with labeled PHI
- Approach: Generate 50-100 synthetic handoffs, measure recall/precision
- Markers: `@pytest.mark.bulk` to skip in fast test runs
- Location: `TestSyntheticDataset` and `TestPHITypeSpecific` classes
- Safety validation: Recall must be >= 95% (critical for HIPAA compliance)
- Precision validation: Precision >= 70% (avoid excessive over-redaction)

**E2E Tests:**
- Framework: Not automated in test suite
- Approach: Manual testing via `test_presidio.py` (21 test cases) or server startup
- Standalone harness: `test_presidio.py` validates 21 scenarios without pytest

## Common Patterns

**Parameterized Testing:**
```python
@pytest.mark.parametrize("sample", SAMPLE_TRANSCRIPTS, ids=lambda s: f"transcript_{s['id']}")
def test_sample_transcript(self, sample):
    """Test each sample transcript for proper de-identification."""
    result = deidentify_text(sample["text"])

    for phi in sample["expected_removed"]:
        assert phi not in result.clean_text
```

**Marker-based Test Selection:**
```python
# Define marker in pytest.ini
# markers = bulk: marks tests as bulk tests

# Use marker in test
@pytest.mark.bulk
def test_bulk_person_detection(self, generator, evaluator):
    pass

# Run: pytest -k "not bulk" (skip bulk)
# Run: pytest -k "bulk" (run only bulk)
```

**Async Testing:**
- Async fixtures use `scope="class"` to avoid per-test reinitialization
- Async test functions work automatically with `asyncio_mode = "auto"`
- HTTP testing: Use `httpx` async client for testing FastAPI endpoints

**Error Testing:**
- Test exceptions are raised: `with pytest.raises(TranscriptionError):`
- Test validation catches leaks: `is_valid, warnings = validate_deidentification(original, cleaned)`

**Conditional Test Execution:**
```python
@pytest.mark.skipif(not SYNTHETIC_AVAILABLE, reason="Synthetic test data generators not available")
class TestSyntheticDataset:
    """Skip if dependencies not installed."""
    pass
```

## Preset Test Cases

**Standalone Presidio Harness** (`test_presidio.py` - 21 cases):

Test cases are structured with must-redact and must-preserve expectations:

1. Baby LastName patterns - "Baby Smith" (preserve "Baby", redact "Smith")
2. Standard patient names - "John Williams" (redact both)
3. Guardian + name - "Mom Jessica" (preserve "Mom", redact "Jessica")
4. Provider names - "Dr. Johnson" (preserve "Dr.", redact "Johnson")
5. Ages (detailed) - "3 week 2 day old" (redact pattern)
6. Ages (gestational) - "36 weeks gestation" (redact)
7. Ages (simple) - "5 year old" (may preserve)
8. MRN labeled - "MRN 12345678" (redact number)
9. MRN with hash - "Patient #87654321" (redact number)
10. Room numbers - "PICU bed 12" (preserve unit, redact number)
11. Admission dates - "January 15th" (redact)
12. Birth dates - "03/15/2024" (redact)
13. Phone numbers - "617-555-1234" (redact)
14. Email addresses (pattern in test data)
15. Addresses (pattern in test data)
16. Medical abbreviations preserved - "NC" (nasal cannula, should NOT redact)
17. Clinical values - "FiO2 60%" (preserve clinical content)
18. Medications - "albuterol, ceftriaxone" (preserve drug names)
19. Diagnosis terms - "bronchiolitis, cellulitis" (preserve diagnosis)
20. Standalone relationships - "Contact mom" (preserve standalone "mom")
21. Complex handoff excerpt (integration test)

**Bulk Synthetic Tests** (100+ generated samples per test):
- Person detection: 50 samples with person entities
- Phone detection: 30 samples with phone numbers
- MRN detection: 30 samples with MRN patterns
- Email detection: 20 samples with email addresses
- Location detection: 30 samples with location data
- Full dataset recall: 100 samples, require >= 95% recall
- Precision validation: 100 samples, require >= 70% precision

## Test Markers

**Custom Markers** (from `pytest.ini`):
- `@pytest.mark.bulk`: Marks test as bulk/expensive (synthetic dataset generation)

**Usage:**
```bash
pytest tests/test_deidentification.py -v -k "not bulk"  # Skip bulk tests
pytest tests/test_deidentification.py -v -k "bulk"      # Run only bulk tests
```

## Filter Warnings

**Configured in `pytest.ini`:**
```ini
filterwarnings =
    ignore::DeprecationWarning:urllib3
    ignore::PendingDeprecationWarning
```

Ignores deprecation warnings from urllib3 (dependency of requests/httpx) and general pending deprecation warnings to keep test output clean.

---

*Testing analysis: 2026-01-23*
