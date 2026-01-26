# Phase 9: CI/CD Fixes - Research

**Researched:** 2026-01-26 14:52:55 EST
**Domain:** Python CI/CD, GitHub Actions, pytest, dependency management
**Confidence:** HIGH

## Summary

This phase addresses straightforward CI/CD failures with well-established solutions. The root causes are already identified: (1) a non-existent PyPI package version in requirements.txt, and (2) test expectations misaligned with v1.0 behavior. Both are common CI/CD issues with clear resolution patterns.

The research validates that the planned fixes follow industry best practices: remove unused dependencies to prevent build failures, update test expectations to match actual code behavior after refactoring, and ensure CI pipelines accurately reflect production behavior.

**Primary recommendation:** Execute fixes in sequence (dependency → test expectations → verify CI) to isolate any unexpected issues.

## Standard Stack

The project already uses established CI/CD tools:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 7.x | Test framework | Industry standard for Python testing, parameterization support |
| GitHub Actions | N/A | CI/CD platform | Native GitHub integration, matrix builds, caching |
| pip | Latest | Dependency management | Built-in Python package installer |
| Docker | Latest | Containerization | Industry standard for reproducible deployments |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-asyncio | 0.23.4 | Async test support | FastAPI testing |
| httpx | 0.26.0 | HTTP client for testing | API endpoint tests |
| actions/setup-python | v5 | Python version matrix | Cross-version testing |
| actions/cache | Latest | Dependency caching | Speed up CI runs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest | unittest | pytest offers better parametrization and fixtures |
| GitHub Actions | CircleCI/Jenkins | GitHub Actions has better GitHub integration |
| requirements.txt | poetry/pipenv | requirements.txt simpler for established projects |

**Current Setup:**
```bash
# Already in requirements.txt - no new installations needed
pytest>=7.0.0,<8.0.0
pytest-asyncio==0.23.4
httpx==0.26.0
```

## Architecture Patterns

### Recommended CI/CD Structure
```
.github/workflows/
├── test.yml           # Test suite execution
└── docker.yml         # Container build verification

Project Testing Structure:
tests/
├── sample_transcripts.py  # Test data with expected PHI elements
├── test_deidentification.py  # PHI detection tests
└── test_weighted_metrics.py  # Evaluation metrics
```

### Pattern 1: Dependency Version Pinning
**What:** Pin exact versions (==) for core dependencies, flexible ranges (>=,<) for testing tools
**When to use:** Production applications requiring reproducibility
**Example:**
```python
# From project requirements.txt
fastapi==0.109.2          # Exact pin for API stability
pytest>=7.0.0,<8.0.0      # Flexible range for testing tool
```

**Best practice:** Pin all transitive dependencies for deterministic builds. Using exact version pinning (==) protects from bugs or incompatibilities in newly released versions. [Source: Pin Your Packages](https://nvie.com/posts/pin-your-packages/)

### Pattern 2: Test Expectation Alignment After Refactoring
**What:** When code behavior changes (intentionally), update test assertions to match new behavior
**When to use:** After refactoring that changes output (but preserves correctness)
**Example:**
```python
# BEFORE v1.0: Expected RMH to be redacted
assert "Ronald McDonald House" not in result.clean_text

# AFTER v1.0: RMH is NOT PHI (well-known charity)
assert "Ronald McDonald House" in result.clean_text
```

**Best practice:** Work on either the code or the tests, but not both at once. When refactoring code, always review and update corresponding unit tests. [Source: Testing and Refactoring With pytest](https://dev.to/cwprogram/testing-and-refactoring-with-pytest-and-pytest-cov-22d6)

### Pattern 3: GitHub Actions Python Matrix Testing
**What:** Test across multiple Python versions using matrix strategy
**When to use:** Libraries supporting multiple Python versions
**Example:**
```yaml
# From .github/workflows/test.yml
strategy:
  matrix:
    python-version: ["3.9", "3.10", "3.11"]
```

**Best practice:** Use setup-python action with caching for faster runs. The action searches for dependency files (requirements.txt, Pipfile.lock, poetry.lock) in the repository automatically. [Source: Building and testing Python](https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-python)

### Pattern 4: Docker Build Verification in CI
**What:** Build Docker image and run smoke test in pull requests
**When to use:** Projects with Docker deployment
**Example:**
```yaml
# From .github/workflows/docker.yml
- name: Test Docker image
  run: |
    docker build -t test-image .
    docker run --rm test-image python -c "from app.main import app; print('Container OK')"
```

### Anti-Patterns to Avoid
- **Using pip freeze directly**: Pollutes requirements with development dependencies; use pip-tools instead [Source: Quickly Pin Python Package Versions](https://emmer.dev/blog/quickly-pin-python-package-versions/)
- **Keeping unused dependencies**: Increases attack surface and maintenance burden; remove unused packages
- **Not updating tests after behavior changes**: Creates "false failures" that waste developer time
- **Testing implementation details**: Test behavior, not internal mechanics

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dependency caching | Custom cache logic | actions/cache@v4 | Built-in GitHub Actions support, handles cache keys automatically |
| Dependency pinning | Manual version tracking | pip-tools (pip-compile) | Automatically pins transitive dependencies, separates input (.in) from output (.txt) |
| Test annotations | Custom failure formatter | pytest-github-actions-annotate-failures | Annotates failed tests directly in GitHub UI [Source: pytest-github-actions-annotate-failures](https://pypi.org/project/pytest-github-actions-annotate-failures/) |
| Python version matrix | Duplicate job definitions | GitHub Actions matrix strategy | Built-in parallelization, consistent environment setup |
| Automated dependency updates | Manual PR creation | Dependabot | Scans weekly, auto-creates PRs with dependency updates [Source: Optimizing your CI/CD GitHub Actions](https://medium.com/@george_bakas/optimizing-your-ci-cd-github-actions-a-comprehensive-guide-f25ea95fd494) |

**Key insight:** GitHub Actions and pytest ecosystems have mature solutions for common CI/CD patterns. Use platform features rather than custom implementations.

## Common Pitfalls

### Pitfall 1: Package Not Found on PyPI
**What goes wrong:** Docker build fails with "Could not find a version that satisfies the requirement"
**Why it happens:** Specified version doesn't exist on PyPI, or package was removed/renamed
**How to avoid:**
- Search PyPI before adding dependencies: `pip index versions <package>`
- Pin versions that actually exist: `philter-ucsf>=2.0.0` fails because only 1.0.3 exists
- Remove unused dependencies from requirements.txt

**Warning signs:** Docker build failures in CI that don't reproduce locally (if package was cached locally)

**Resolution:** Verify package versions on PyPI, update requirements.txt, remove if unused. [Source: Fix the pip error: Couldn't find a version that satisfies the requirement](https://bhch.github.io/posts/2017/04/fix-the-pip-error-couldnt-find-a-version-that-satisfies-the-requirement/)

### Pitfall 2: Tests Pass Locally, Fail in CI
**What goes wrong:** Tests succeed on developer machine but fail in GitHub Actions
**Why it happens:** Environment differences (dependencies, Python version, file permissions, cached data)
**How to avoid:**
- Use same Python version locally as CI matrix
- Clear pytest cache before critical tests: `pytest --cache-clear`
- Check for missing dependencies in CI environment
- Avoid relying on local files not in git

**Warning signs:** "Works on my machine" syndrome, inconsistent CI failures

**Resolution:** Enable debug logging (ACTIONS_STEP_DEBUG=true), explicitly install all dependencies, use consistent Python versions. [Source: Troubleshooting GitHub Actions](https://www.mindfulchase.com/explore/troubleshooting-tips/ci-cd-continuous-integration-continuous-deployment/troubleshooting-github-actions-fixing-workflow-failures,-secrets-issues,-matrix-errors,-caching-bugs,-and-runtime-problems-in-ci-cd-pipelines.html)

### Pitfall 3: Test Expectations Frozen in Time
**What goes wrong:** Tests fail after intentional behavior changes (refactoring, bug fixes, feature additions)
**Why it happens:** Tests written for old behavior, not updated with code changes
**How to avoid:**
- Document WHY behavior changed (commit message, code comment)
- Update test expectations immediately after behavior change
- Use descriptive test names that explain expected behavior
- Add comments explaining non-obvious test expectations

**Warning signs:** Test failures with correct code output, confusion about what behavior is "right"

**Resolution:** Review test expectations against current code behavior. If code is correct, update tests to match. [Source: Python Testing – Unit Tests, Pytest, and Best Practices](https://dev.to/nkpydev/python-testing-unit-tests-pytest-and-best-practices-45gl)

### Pitfall 4: Over-Aggressive Dependency Pinning
**What goes wrong:** Security vulnerabilities accumulate, compatibility issues with other packages
**Why it happens:** Pinning exact versions (==) without regular updates
**How to avoid:**
- Use Dependabot for automated security updates
- Pin production dependencies exactly, use ranges for dev dependencies
- Separate requirements.in (flexible) from requirements.txt (pinned)
- Review and test dependency updates in staging

**Warning signs:** Years-old package versions, security scanner alerts, compatibility conflicts

**Resolution:** Regular dependency audits, automated update PRs, security scanning integration. [Source: Best Practices for Managing Python Dependencies](https://www.geeksforgeeks.org/python/best-practices-for-managing-python-dependencies/)

### Pitfall 5: Flaky Tests in CI
**What goes wrong:** Tests pass sometimes, fail other times without code changes
**Why it happens:** Non-deterministic behavior (timing, randomness, network calls)
**How to avoid:**
- Avoid real network calls in tests (use fixtures/mocks)
- Set random seeds for reproducibility
- Avoid timing-dependent assertions
- Use pytest-timeout to catch hanging tests

**Warning signs:** "Rerun succeeded" pattern, intermittent failures on same commit

**Resolution:** Identify non-deterministic factors, add explicit seeds/mocks, increase timeouts if needed.

## Code Examples

Verified patterns from official sources:

### Removing Unused Dependencies
```bash
# Check if package is actually used in code
grep -r "philter" app/ tests/
# If no results, safe to remove

# Update requirements.txt
# BEFORE:
philter-ucsf>=2.0.0

# AFTER:
# (line removed entirely)
```

### Updating Test Expectations After Behavior Change
```python
# From tests/sample_transcripts.py

# BEFORE v1.0: Expected RMH redacted
SAMPLE_TRANSCRIPTS = [
    {
        "id": 2,
        "expected_removed": ["Ronald McDonald House"],  # Old expectation
    }
]

# AFTER v1.0: RMH is NOT PHI (well-known charity, not personally identifying)
SAMPLE_TRANSCRIPTS = [
    {
        "id": 2,
        "expected_removed": [],  # Removed - RMH not PHI
        "expected_preserved": ["Ronald McDonald House"],  # Added
    }
]
```

### Verifying Package Versions on PyPI
```bash
# Check available versions before adding to requirements.txt
pip index versions philter-ucsf

# Output:
# philter-ucsf (1.0.3)
# Available versions: 1.0.3, 1.0.2, 1.0.1
#   LATEST:    1.0.3

# Conclusion: philter-ucsf>=2.0.0 will fail (only 1.0.3 exists)
```

### GitHub Actions Dependency Caching
```yaml
# From .github/workflows/test.yml
- name: Set up Python ${{ matrix.python-version }}
  uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
    cache: 'pip'  # Automatically caches pip dependencies

# Speeds up subsequent runs by reusing downloaded packages
```

### Pytest Parametrized Test Expectations
```python
# From tests/test_deidentification.py
import pytest
from tests.sample_transcripts import SAMPLE_TRANSCRIPTS

@pytest.mark.parametrize("sample", SAMPLE_TRANSCRIPTS,
                         ids=lambda s: f"transcript_{s['id']}")
def test_sample_transcript(sample):
    """Test each sample transcript for proper de-identification."""
    result = deidentify_text(sample["text"])

    # Check that expected PHI is removed
    for phi in sample["expected_removed"]:
        assert phi not in result.clean_text, f"PHI '{phi}' should be removed"

    # Check that medical content is preserved
    for term in sample["expected_preserved"]:
        assert term in result.clean_text, f"Medical term '{term}' should be preserved"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual requirements.txt | pip-tools/uv with .in files | 2024-2026 | Separates input constraints from pinned output |
| No dependency updates | Dependabot automation | 2020+ | Weekly automated security update PRs |
| Single Python version | Matrix testing | 2019+ | Catch version-specific bugs early |
| actions/cache@v2 | actions/cache@v4 | 2023 | Better caching strategies, faster restores |
| pytest-cov standalone | pytest-cov + GH annotations | 2022+ | Coverage reports visible in PR UI |

**Deprecated/outdated:**
- **Manual pip freeze**: Use pip-compile from pip-tools to separate high-level dependencies (.in) from fully pinned output (.txt)
- **actions/setup-python@v2**: Upgrade to v5 for better caching and performance [Source: Building and testing Python](https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-python)
- **Implicit test expectations**: Always document WHY a test expects specific behavior (especially after refactoring)

## Open Questions

Things that couldn't be fully resolved:

1. **Should "35 weeker" be redacted as AGE?**
   - What we know: v1.0 redacts it, original test expected preservation
   - What's unclear: HIPAA ambiguity—ages <90 technically not PHI, but gestational age patterns can be identifying in small units
   - Recommendation: Keep v1.0 behavior (redact) per safety-first principle; update test expectation to match

2. **Is "Ronald McDonald House" PHI?**
   - What we know: v1.0 preserves it, original test expected redaction
   - What's unclear: It's a location, but well-known charity (not personally identifying)
   - Recommendation: Keep v1.0 behavior (preserve) per medical utility principle; update test expectation to match

3. **Should we use requirements-dev.txt or combined requirements.txt?**
   - What we know: Project has requirements-dev.txt (uncommitted), CI installs from both
   - What's unclear: Best practice for small projects vs. large teams
   - Recommendation: Keep current approach (separate files) for clarity; commit requirements-dev.txt for reproducibility

## Sources

### Primary (HIGH confidence)
- [GitHub Docs: Building and testing Python](https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-python) - Official GitHub Actions Python guide
- [pytest documentation: Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) - Official pytest best practices
- [pip documentation: Repeatable Installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/) - Official pip version pinning guide

### Secondary (MEDIUM confidence)
- [Real Python: Effective Python Testing With pytest](https://realpython.com/pytest-python-testing/) - Comprehensive pytest tutorial
- [nvie.com: Pin Your Packages](https://nvie.com/posts/pin-your-packages/) - Authoritative dependency pinning guide
- [Medium: The Ultimate Guide to Python CI/CD (Jan 2026)](https://medium.com/hydroinformatics/the-ultimate-guide-to-python-ci-cd-mastering-github-actions-composite-actions-for-modern-python-0d7730c17b9e) - Recent CI/CD patterns
- [GeeksforGeeks: Best Practices for Managing Python Dependencies](https://www.geeksforgeeks.org/python/best-practices-for-managing-python-dependencies/) - Dependency management strategies
- [Mindful Chase: Troubleshooting GitHub Actions](https://www.mindfulchase.com/explore/troubleshooting-tips/ci-cd-continuous-integration-continuous-deployment/troubleshooting-github-actions-fixing-workflow-failures,-secrets-issues,-matrix-errors,-caching-bugs,-and-runtime-problems-in-ci-cd-pipelines.html) - CI troubleshooting guide

### Tertiary (LOW confidence)
- [Emmer.dev: Quickly Pin Python Package Versions](https://emmer.dev/blog/quickly-pin-python-package-versions/) - pip-tools usage (blog post)
- [DEV Community: Testing and Refactoring With pytest](https://dev.to/cwprogram/testing-and-refactoring-with-pytest-and-pytest-cov-22d6) - Test refactoring patterns (community article)
- [Baeldung: Docker Container pip DNS Troubleshooting](https://www.baeldung.com/ops/docker-container-pip-dns-troubleshooting) - Docker networking issues

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools already in use, well-established
- Architecture patterns: HIGH - Official documentation and proven practices
- Common pitfalls: HIGH - Root causes already identified, fixes straightforward
- Code examples: HIGH - Taken directly from project files and official docs

**Research date:** 2026-01-26 14:52:55 EST
**Valid until:** 2026-02-26 (30 days for stable CI/CD practices)

**Project-specific notes:**
- Root causes already identified in PROJECT.md, reducing research scope
- All fixes are non-controversial (remove unused dep, align test expectations)
- No architectural changes needed—purely maintenance work
- CI workflows already well-configured, just need fixes applied
