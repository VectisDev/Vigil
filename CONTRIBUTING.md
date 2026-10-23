# Contributing to VIGIL

**ES: Contribuyendo a Centinel Engine**

## Development Setup

### Prerequisites

- Python **3.11+**
- **Poetry** (`pip install poetry`)
- Git

### Initial Setup

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
poetry install
```

## Running Tests

### Core Tests (Custody, Hashing, Transparency)

```bash
poetry run pytest tests/test_custody.py -v
poetry run pytest tests/test_anomaly_detector.py -v
```

Expected: All core tests pass. These verify cryptographic integrity.

### Full Test Suite

```bash
poetry run pytest tests/ -q
```

Expected output (or similar):
```
37 passed in 0.45s
```

Some tests may be skipped if optional dependencies (e.g., `fastapi` for API tests) are not installed, but core security tests must pass.

### Quick Sanity Check

```bash
poetry run pytest tests/test_custody.py -q
```

This should complete in < 1 second.

## Code Standards

### Python Style

- Use **type hints** on all functions and class methods
- Follow **PEP 8** (verified by `flake8`)
- Use **f-strings** for string formatting
- Prefer **dataclasses** for data structures
- Keep **docstrings** short (1–2 sentences); explain the "why", not "what"

### Example

```python
def verify_benford(values: list[int]) -> dict[str, Any]:
    """Check if first digits follow Benford's Law via χ² test.
    
    Returns dict with 'valid' (bool), 'chi2' (float), 'detail' (str).
    """
    # Implementation...
    return {"valid": chi2 < threshold, "chi2": chi2, "detail": f"..."}
```

### Imports

- Organize: standard library → third-party → local
- Avoid circular imports
- Use `from __future__ import annotations` for forward references

### Testing

- Add tests for new features (`tests/test_*.py`)
- Test both happy path and edge cases
- Use fixtures for setup (see `tests/conftest.py`)
- Aim for >80% coverage on security-critical code

## Common Tasks

### Add a New Anomaly Detection Rule

1. Create `src/centinel/core/rules/<name>_rule.py` with an `apply(current_data, previous_data, config)` function decorated with `@rule(name=..., severity=..., description=..., config_key=...)`
2. Add the module name to `_RULE_MODULES` in `src/centinel/core/rules_engine.py` so it registers at startup
3. Add its thresholds to `config/prod/rules.yaml` under the same `config_key`
4. Add tests under `tests/` and run them: `poetry run pytest tests/<your_test>.py -v`
5. Document the technique and its limitations in `docs/research/METHODOLOGY.md`

### Fix a Test

1. Read the error message carefully
2. Check if the test fixture (setup) matches production code structure
3. Verify file paths, naming conventions, and data layout
4. Run: `poetry run pytest tests/test_X.py::TestClass::test_method -v`

### Update Documentation

1. Edit Markdown files in `docs/`
2. Use clear headings (##, ###)
3. Include examples where helpful
4. Provide both ES and EN sections if policy-relevant

## Commit Message Format

Clear, concise commits help reviewers and future maintainers.

**Format:**
```
[D-number or feature tag]: Brief description (imperative mood)

- Bullet point 1
- Bullet point 2

Related: #issue-number (if applicable)
```

**Examples:**
```
D7: Test suite fixup — add fastapi, verify all tests pass

- pyproject.toml: add fastapi>=0.100.0,<0.150.0
- poetry lock: updated
- tests/test_custody.py: fix file discovery (subdirs)
- All 27 core tests passing

Related: #102
```

```
Anomaly detector: Z-score threshold tuning

- Lower zscore_threshold from 4.0 to 3.0 for election night
- Matches academic standards (Mebane 2006)
- All 12 anomaly tests passing
```

## Pull Request Checklist

Before submitting a PR:

- [ ] Tests pass: `poetry run pytest tests/ -q`
- [ ] Code style: No obvious violations of standards above
- [ ] Docstrings added for public functions
- [ ] Commits are logical and messages are clear
- [ ] No hardcoded secrets or credentials
- [ ] Changes are focused (not multiple unrelated fixes)

## Reporting Issues

**Security Issues:** Never open a public issue. Report privately via **Security → Report a vulnerability** (see [SECURITY.md](SECURITY.md))

**Bug Reports:** Include:
- Reproduction steps
- Expected vs. actual behavior
- Environment (Python version, OS, Poetry version)
- Relevant error messages or logs

**Feature Requests:** Describe:
- Use case / motivation
- Proposed approach (if any)
- Any design concerns or trade-offs

## Questions?

- Check `docs/` and README.md first
- Review existing code for patterns
- Open a GitHub discussion
- Email maintainer if sensitive

---

Thank you for contributing to electoral integrity!

**Last Updated:** May 2026
