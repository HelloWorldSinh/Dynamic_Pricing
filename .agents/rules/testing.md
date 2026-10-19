---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Testing

> This file extends [common/testing.md](../common/testing.md) with Python specific content.

## Framework

Use **pytest** as the testing framework.

## Coverage

```bash
pytest --cov=src --cov-report=term-missing
```

## Test Organization

Use `pytest.mark` for test categorization:

```python
import pytest

@pytest.mark.unit
def test_calculate_total():
    ...

@pytest.mark.integration
def test_database_connection():
    ...
```

## API Testing Only (No Browser/UI Testing)

- **MANDATORY:** All feature testing, verification, bug checks, and regression tests MUST be executed via API (pytest, FastAPI `TestClient`, direct HTTP requests, integration scripts).
- **PROHIBITED:** NEVER trigger automated browser tools (`browser_subagent`) to click UI elements or test via browser unless the user explicitly requests visual UI inspection.

## Reference

See skill: `python-testing` for detailed pytest patterns and fixtures.
