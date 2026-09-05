# Playwright Python – Project Configuration

## `requirements.txt`

```txt
playwright==1.46.0
pytest>=8.0.0
pytest-xdist>=3.0.0
allure-pytest>=2.13.0
python-dotenv>=1.0.0
faker>=25.0.0
pytest-rerunfailures>=14.0
```

---

## Install Playwright Browsers

```bash
python -m pip install -r requirements.txt
python -m playwright install

# Install browser dependencies in CI / container
python -m playwright install --with-deps
```

---

## `pytest.ini`

```ini
[pytest]
addopts = -ra --strict-markers
markers =
    smoke: smoke tests
    regression: regression tests
    e2e: end-to-end tests
```

---

## `settings.py`

```python
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# load_dotenv() MUST run before Settings is instantiated so that
# os.getenv() inside default_factory lambdas picks up .env values.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Use field(default_factory=...) so env vars are evaluated at
    # instantiation time, not at class-definition / import time.
    base_url: str = field(default_factory=lambda: os.getenv("BASE_URL", ""))
    api_base_url: str = field(default_factory=lambda: os.getenv("API_BASE_URL", ""))
    browser: str = field(default_factory=lambda: os.getenv("BROWSER", "chromium"))
    headless: bool = field(
        default_factory=lambda: os.getenv("HEADLESS", "true").lower() == "true"
    )
    default_timeout: int = field(
        default_factory=lambda: int(os.getenv("DEFAULT_TIMEOUT", "30000"))
    )
    navigation_timeout: int = field(
        default_factory=lambda: int(os.getenv("NAVIGATION_TIMEOUT", "60000"))
    )


settings = Settings()
```

---

## Session or Environment Example

```bash
export BASE_URL="https://staging.example.com"
export BROWSER="chromium"
export HEADLESS="true"
export LOCATOR_MAP_PATH="tests/locator_map"
export LOCATOR_STRICT="false"
export LOCATOR_DISCOVERY="yaml"
pytest -q
```

---

## Locator Map Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `LOCATOR_MAP_PATH` | `tests/locator_map` | Directory where locator YAML/JSON files are stored. |
| `LOCATOR_STRICT` | `false` | If `true`, test fails fast with clear error when locator contract is missing. If `false`, generates TODO and continues. |
| `LOCATOR_DISCOVERY` | `yaml` | File format for locator maps: `yaml` or `json`. |

### Locator Map Directory Structure

```text
tests/
├── locator_map/          ← Project-specific locator contracts
│   ├── login.yaml       ← Defines email, password, submit, error locators
│   ├── dashboard.yaml   ← Page-specific locators
│   └── .gitignore       ← Ignore auto-generated maps
├── pages/
│   ├── login_page.py
│   └── dashboard_page.py
└── tests/
    └── test_login.py
```

### Example: `tests/locator_map/login.yaml`

```yaml
login:
  url: /login
  
  email:
    strategy: label
    value: Email
    required: true
    description: Login email input
  
  password:
    strategy: label
    value: Password
    required: true
    description: Login password input
  
  submit:
    strategy: role
    role: button
    name: Sign in
    required: true
    description: Submit login button
  
  error:
    strategy: test_id
    value: login-error
    required: false
    description: Error message display
  
  success_url: "**/dashboard"
```

---

## Running Tests

```bash
# All tests
pytest

# Specific browser
BROWSER=firefox pytest

# Headed mode for debugging
HEADLESS=false pytest -q

# Single test file (adjust to your repository layout)
pytest tests/tests/test_login.py -q

# Parallel execution
pytest -n 4
```

---

## Allure Setup

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

## Docker / CI

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.46.0-noble
WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir -r requirements.txt
CMD ["pytest", "--alluredir=allure-results"]
```

GitHub Actions should check out the repository, install dependencies, run a browser
matrix, and retain artifacts:

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
- name: Install dependencies
  run: |
    python -m pip install -r requirements.txt
    python -m playwright install --with-deps
- name: Run tests
  run: pytest --alluredir=allure-results
- name: Upload traces and Allure results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: playwright-artifacts
    path: |
      artifacts/
      allure-results/
```

Use `pytest -n 4` only with per-test artifact names, as provided by `BaseTest.py`.

---

## Browser Installation Notes

- Use `python -m playwright install` once per environment
- Use `--with-deps` when running in CI containers or Linux servers
- Keep browsers isolated by test environment to reduce flaky suites
