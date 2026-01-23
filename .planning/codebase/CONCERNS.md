# Codebase Concerns

**Analysis Date:** 2026-01-23

## Tech Debt

**Pattern Recognition False Negatives - Lookbehind Limitation:**
- Issue: Regex lookbehind assertions in `app/recognizers/pediatric.py` and `app/recognizers/medical.py` only capture names AFTER relationship/context words, missing edge cases
- Files: `app/recognizers/pediatric.py` (lines 33-110), `app/recognizers/medical.py` (lines 69-106)
- Impact: Guardian names at sentence boundaries (e.g., "Jessica is Mom") won't be caught; medical terms in unusual formats may slip through
- Fix approach: Add additional lookaround patterns for prefix variations; consider hybrid regex + NER fallback for low-confidence matches

**Hallucination Pattern List - Manual Maintenance Burden:**
- Issue: `app/transcription.py` lines 61-72 contain hardcoded hallucination patterns that must be manually updated as Whisper evolves
- Files: `app/transcription.py`
- Impact: New Whisper hallucination types won't be filtered; list may grow unmanageably
- Fix approach: Implement a learned hallucination detector or dynamic pattern discovery from test corpus

**Deny List Maintenance - Growing List Fragility:**
- Issue: `app/config.py` lines 66-108 maintain two separate deny lists (LOCATION, PERSON) that must stay synchronized with false positive discoveries
- Files: `app/config.py`
- Impact: As system is used in production, false positives won't be discovered systematically; inconsistent filtering across entity types
- Fix approach: Implement feedback mechanism to log false positives; create systematic testing for deny list effectiveness

**Arbitrary Score Thresholds - No Calibration:**
- Issue: `app/config.py` line 54 sets `phi_score_threshold: float = 0.35` and validation uses hardcoded 0.7 (line 272 `app/deidentification.py`), with no tuning methodology
- Files: `app/config.py`, `app/deidentification.py` (line 272)
- Impact: Threshold may be inappropriate for production data; no clear path to optimize recall vs precision trade-offs
- Fix approach: Implement threshold calibration against test dataset; expose threshold tuning as configuration parameter

---

## Known Bugs

**Temp File Cleanup Race Condition - Minor:**
- Symptoms: Temp files in `/tmp/handoff-transcriber/` may persist if process crashes between write and cleanup
- Files: `app/transcription.py` (lines 120-189)
- Trigger: Server process killed during transcription step
- Workaround: Implement cron job to clean files older than 1 hour; test cleanup on interruption signal

**Audio Duration Estimation Inaccuracy:**
- Symptoms: Frontend progress bar doesn't match actual transcription time, especially for highly compressed audio
- Files: `app/transcription.py` (lines 192-227); used in `app/main.py` line 491
- Trigger: Audio files with compression ratios >2MB/minute or very short files (<10 seconds)
- Workaround: Add 20% buffer to estimates; display estimate ranges rather than point estimates

**Empty Transcript Not Logged as PHI Event:**
- Symptoms: When audio contains no speech, audit log shows 0 entities removed but no warning about failed transcription
- Files: `app/main.py` (lines 388-406)
- Trigger: Silence-only audio files that pass VAD filter but produce empty text
- Workaround: Treat empty transcript as special case in audit log (event_type: "transcription_empty"); improve VAD parameters

---

## Security Considerations

**Frontend XSS Risk - Unescaped Entity Display:**
- Risk: Detected PHI entities are displayed in HTML with `text_preview` that could contain malicious markup if transcription model outputs HTML tags
- Files: `static/app.js` (lines ~200-250 in results display)
- Current mitigation: `innerText` used instead of `innerHTML` in most places, but worth verifying all entity display
- Recommendations:
  - Add HTML sanitization library (DOMPurify) as precaution
  - Validate all entity text matches `^[a-zA-Z0-9\s\-()]+$` pattern before display
  - Add Content Security Policy frame for results panel

**CORS Configuration Too Permissive in Development:**
- Risk: Default CORS_ORIGINS includes both `http://localhost:8000` and `http://127.0.0.1:8000`, creating unnecessary attack surface
- Files: `app/config.py` (lines 149-152), `app/main.py` (lines 213-219)
- Current mitigation: Well-intentioned CSP headers (line 68-76 `app/main.py`), but doesn't prevent cross-origin requests from same-origin policy bypass
- Recommendations:
  - Default to single origin only (localhost:8000)
  - Document environment variable override clearly with HIPAA implications warning
  - Add logging for CORS rejections to detect probing attempts

**Rate Limiting May Not Prevent Abuse - Low Threshold:**
- Risk: Default 10 requests/60s (line 155 `app/config.py`) may allow coordinated attacks to enumerate valid request patterns
- Files: `app/config.py` (lines 153-160), `app/main.py` (line 47)
- Current mitigation: slowapi rate limiter is applied, but threshold is conservative
- Recommendations:
  - Add exponential backoff on repeated violations
  - Implement IP-based blocking after N violations
  - Log rate limit violations as security events

**Audit Log Path Traversal - Misconfiguration Risk:**
- Risk: `audit_log_file` path is user-configurable via environment variable with no validation
- Files: `app/config.py` (line 165), `app/audit.py` (line 64)
- Current mitigation: None; path is used directly
- Recommendations:
  - Validate path is within designated logs directory
  - Use `Path.resolve()` to prevent `../` traversal
  - Create logs/ directory at startup with restrictive permissions

**CSP Header - Unsafe-Inline Script Source:**
- Risk: CSP policy includes `'unsafe-inline'` for script-src (line 70 `app/main.py`), defeating most XSS protections
- Files: `app/main.py` (line 70)
- Current mitigation: Frontend is simple single-file app
- Recommendations:
  - Extract inline scripts to external file with hash/nonce CSP validation
  - Test with strict CSP: `script-src 'self'`
  - Document why unsafe-inline is necessary if it must remain

---

## Performance Bottlenecks

**Model Loading - 30+ Second Startup Latency:**
- Problem: Whisper model and spaCy NER model are lazy-loaded on first request, causing first upload to hang 30-60 seconds
- Files: `app/transcription.py` (lines 31-52), `app/deidentification.py` (lines 73-115)
- Cause: Large model files (>3GB for medium.en, ~200MB for en_core_web_lg) loaded in-process on first API call
- Improvement path:
  - Pre-load models in Docker entrypoint or background task
  - Implement `/health/ready` endpoint that waits for models; use for readiness probe
  - Consider model-as-service architecture if latency critical for production

**Presidio Analysis - O(n) Scan Per Recognizer:**
- Problem: Each recognizer runs full text scan; 10+ recognizers means 10+ full passes through transcript
- Files: `app/deidentification.py` (lines 100-108, 142-148)
- Cause: Presidio's architecture; no aggregation optimization
- Improvement path:
  - Profile to measure actual impact on 30-minute handoff (typical size)
  - Consider implementing custom analyzer that batches recognizer calls
  - Cache NER results across validation passes (line 268 re-analyzes after de-identification)

**Validation Re-scan - Duplicate Analysis:**
- Problem: `validate_deidentification()` re-runs full Presidio analysis on cleaned text to detect leaks
- Files: `app/deidentification.py` (lines 250-295)
- Cause: Safety requirement to catch missed PHI, but runs analyzer twice per request
- Improvement path:
  - Profile 30-minute handoff to measure cost (likely <5% of transcription time)
  - If significant, implement delta-analysis (only check regions where PHI was removed)
  - Consider async validation that doesn't block response

**Transcription Speed - 2x Realtime on CPU:**
- Problem: Medium.en model processes ~1 minute audio per 2 seconds wall-clock on CPU
- Files: `app/transcription.py` (line 220)
- Cause: Fundamental model inference speed without GPU
- Improvement path:
  - Document GPU requirements in README if acceleration needed
  - Implement batch processing for multiple files
  - Consider lightweight model for non-critical fields (timestamps, speaker identification)

---

## Fragile Areas

**Pattern Recognizers - Regex Brittleness:**
- Files: `app/recognizers/pediatric.py` (lines 33-244), `app/recognizers/medical.py` (lines 25-106)
- Why fragile:
  - Lookbehind patterns assume exact spacing and capitalization
  - "mom jessica" (lowercase) won't match `(?<=Mom )` pattern
  - Hyphenated names like "Mary-Jane" only partially captured by `[a-z]+` regex
  - Medical term regex like `\bMRN[:\s]?` is sensitive to formatting variations
- Safe modification:
  - Test new patterns against 50-example corpus before committing
  - Use case-insensitive flag (`(?i)`) where clinically appropriate
  - Document each regex with example matches and intentional non-matches
- Test coverage: Limited; `test_deidentification.py` has ~10 specific test cases per recognizer type, but no systematic regex validation

**Deny List Filtering - Logic Vulnerability:**
- Files: `app/deidentification.py` (lines 151-165)
- Why fragile:
  - PERSON deny list uses case-insensitive comparison (line 161) but LOCATION uses exact match (line 156)
  - Inconsistent logic could lead to over-redaction if entry case varies
  - Deny list is not version-controlled per entity, making reproduction of old behavior hard
- Safe modification:
  - Standardize all deny list comparisons to case-insensitive lower()
  - Add comment in deny_list entries showing variations encountered
  - Create regression test when new deny list entry added
- Test coverage: `test_preserves_medical_content()` and `test_preserves_clinical_values()` test preservation but don't specifically test deny list logic

**Score Threshold Inconsistency:**
- Files: `app/config.py` (line 54), `app/deidentification.py` (line 272)
- Why fragile:
  - Default threshold (0.35) used for detection is very permissive
  - Validation uses hardcoded 0.7 for leak detection, which is unrelated to main threshold
  - No clear relationship between the two thresholds; changing one doesn't affect the other
  - If settings.phi_score_threshold is changed, validation threshold isn't updated
- Safe modification:
  - Add validation configuration to settings (keep 0.7 but make it configurable)
  - Add unit test that confirms threshold values are sensible: detection_threshold < validation_threshold
  - Document why 0.35 vs 0.7 split exists
- Test coverage: No specific tests for threshold behavior; bulk tests use defaults

**Temporary File Handling - Resource Leak Risk:**
- Files: `app/transcription.py` (lines 114-189)
- Why fragile:
  - File is created and marked delete=False, requiring manual cleanup in finally block
  - If process crashes during write, file persists
  - No monitoring for accumulation of temp files
  - Concurrent requests could theoretically fill /tmp if cleanup fails
- Safe modification:
  - Add `atexit` handler to clean up any remaining temp files on shutdown
  - Use `tempfile.TemporaryFile()` context manager instead if API allows in-memory buffering
  - Add startup check to clean stale temp files >1 hour old
- Test coverage: No test for temp file cleanup; only happy path tested

---

## Scaling Limits

**Memory Usage - Full Model Resident:**
- Current capacity: ~2-3GB for model weights in memory
- Limit: System will page to swap or OOM if memory <4GB available
- Scaling path:
  - Profile actual peak memory during 30-minute transcription (expected ~2.5GB)
  - Test on 2GB-memory systems; may require smaller model (base.en ~1.5GB)
  - Consider model quantization (int8 already used) or distilled models

**Concurrent Request Handling - Single-Process Bottleneck:**
- Current capacity: Limited by Uvicorn worker pool (default 1 on CPU)
- Limit: 2-3 concurrent transcriptions will block on Whisper inference (not parallelizable on single GPU)
- Scaling path:
  - Deploy multiple Uvicorn workers with shared queue
  - Implement job queue (Redis/RabbitMQ) for transcription tasks
  - Use process pool for CPU-bound transcription (faster-whisper supports multiprocessing)

**Disk I/O - Temp File Bottleneck:**
- Current capacity: Limited by disk I/O during audio write/read in transcription step
- Limit: High I/O contention on shared storage (NFS, cloud disks)
- Scaling path:
  - Profile actual I/O usage (likely insignificant; model loading is bigger bottleneck)
  - Consider in-memory temp storage if reliable
  - Test on cloud deployments (AWS EBS, GCP Persistent Disks) for I/O characteristics

---

## Dependencies at Risk

**Presidio Version Pinned - Minor Update Risk:**
- Risk: `presidio-analyzer==2.2.354` and `presidio-anonymizer==2.2.354` are pinned to specific version; new versions may have breaking changes or better PHI detection
- Impact: Security improvements may not be applied; custom recognizers could break on minor updates
- Migration plan:
  - Test new Presidio versions in CI before upgrading
  - Validate that test suite (especially false negatives) passes with new version
  - Consider semi-pinning to `~=2.2.354` to allow patch updates only

**spaCy Model Download - Runtime Dependency:**
- Risk: `python -m spacy download en_core_web_lg` executed at Docker build time and at startup; if server fails, model won't be available
- Impact: Application won't start without internet connection; model updates won't be automatic
- Migration plan:
  - Download model into Docker image (currently optional, line 33 `Dockerfile`)
  - Create fallback to smaller model (en_core_web_sm) if large model unavailable
  - Add health check that confirms spaCy model loaded successfully

**faster-whisper - Unstable API:**
- Risk: `faster-whisper>=1.0.0` is pinned to major version only; API may change between minor versions
- Impact: Transcription could fail on version upgrade; custom parameters might not be recognized
- Migration plan:
  - Pin to `~=1.0.0` to avoid breaking changes in 2.x
  - Add version check in startup to log actual version used
  - Test new versions in CI before pinning update

---

## Missing Critical Features

**No Retry Logic for Transient Failures:**
- Problem: Transcription or de-identification fails completely if any single step fails; no exponential backoff or retry mechanism
- Blocks: Cannot recover from temporary Presidio engine load failures or OOM conditions
- Example scenario: System briefly OOMs due to memory pressure, entire request fails with no retry

**No Progress Reporting for Long Operations:**
- Problem: Frontend shows generic "Processing..." for 30+ minute audio files; no feedback on transcription progress
- Blocks: User can't tell if system is hung vs. genuinely processing
- Example scenario: 60-minute handoff takes 60+ seconds on CPU; user thinks it crashed

**No Streaming/Chunked Processing:**
- Problem: Entire audio file must be loaded into memory before transcription
- Blocks: Cannot process audio files larger than available RAM; no support for live streaming
- Example scenario: Cannot support 2+ hour handoff recordings on systems with <8GB RAM

**No de-identification Verification/Review Interface:**
- Problem: System always returns cleaned transcript; no way for user to review PHI detection before committing to cleaned version
- Blocks: Cannot catch false positives (over-redaction) without manual text diff
- Example scenario: Important clinical term incorrectly flagged as PHI; cannot be easily recovered

---

## Test Coverage Gaps

**Untested Area: Concurrent Request Handling:**
- What's not tested: Multiple requests processed simultaneously; thread safety of lazy-loaded models
- Files: `app/transcription.py` (lines 21-52), `app/deidentification.py` (lines 26-28)
- Risk: Race conditions in model loading; cache coherency issues if models modified during concurrent access
- Priority: High - Concurrency bugs are difficult to reproduce; should test with 5+ concurrent requests

**Untested Area: Large Audio File Edge Cases:**
- What's not tested: 60+ minute handoffs; edge cases in VAD filtering on very long silence
- Files: `app/transcription.py` (lines 134-142)
- Risk: VAD parameters tuned for typical 5-10 minute handoffs; may over-filter or under-filter long recordings
- Priority: Medium - Real handoffs could be longer than test data

**Untested Area: Error Handling Paths:**
- What's not tested: Disk full during temp file write; out-of-memory during model loading; network timeouts (if future cloud integration added)
- Files: `app/transcription.py` (lines 120-189), `app/main.py` (lines 452-480)
- Risk: Error messages may leak PHI if exception context captured; partial files may accumulate
- Priority: Medium - Affects production stability

**Untested Area: Deny List Edge Cases:**
- What's not tested: Deny list entries that are substrings of legitimate PHI (e.g., "PA" is in deny list but also in "PAPI" patient name)
- Files: `app/deidentification.py` (lines 151-165)
- Risk: False negatives if substring matching accidentally catches PHI; false positives if deny list entry is prefix of real term
- Priority: Medium - Over-redaction could limit clinical utility

**Untested Area: Unicode/Encoding in PHI:**
- What's not tested: Non-ASCII characters in names (e.g., "José", "Müller"), emojis in transcription errors
- Files: `app/deidentification.py`, `app/recognizers/`
- Risk: Regex patterns assume ASCII letters `[a-zA-Z]`; non-ASCII names will not be caught
- Priority: Low - Unlikely in pediatric handoffs but possible with international patients

**Untested Area: Frontend Browser Compatibility:**
- What's not tested: Audio recording in Safari, Firefox; fallback for unsupported MIME types
- Files: `static/app.js` (lines 98-115)
- Risk: Users on unsupported browsers get cryptic error messages
- Priority: Low - Mostly works but edge browsers might have issues

---

## Additional Observations

**Documentation Clarity - Production Deployment:**
- Issue: README emphasizes "local processing" but deployment guidance is minimal
- Files: `README.md`
- Recommendation: Add section documenting production security checklist (CORS configuration, HTTPS enforcement, audit log retention)

**Logging Verbosity - Debug vs. Info:**
- Issue: `app/main.py` line 41 uses DEBUG level based on settings, but many operations log at INFO level (lines 369, 385, 409)
- Files: `app/main.py`, all app modules
- Recommendation: Consider using DEBUG for request-specific logs; reserve INFO for application events

---

*Concerns audit: 2026-01-23*
