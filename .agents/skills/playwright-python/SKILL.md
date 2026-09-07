---
name: playwright-python
description: "Scaffold, write, debug, and enhance enterprise-grade Playwright E2E tests in Python using Page Object Model, pytest, Allure reporting, and parallel execution."
category: test-automation
risk: safe
source: community
date_added: "2026-09-01"
author: amalsam18
tags: [playwright, python, pytest, e2e-testing, page-object-model, allure, browser-automation]
tools: [claude, cursor, antigravity]
---

# Playwright Python – Advanced Test Automation

## Overview

This skill produces production-quality, enterprise-grade Playwright Python test code.
It enforces the Page Object Model (POM), strict locator strategies, resilient waits,
thread-safe browser fixtures, and rich Allure reporting integration. Targets Python 3.11+ and a pinned Playwright version compatible with the project.

Supporting reference files are available for deeper topics:

| Topic | File |
|-------|------|
| Project setup and config | `config.md` |
| Component pattern, dropdowns, uploads, waits | `page-objects.md` |
| Assertion API and soft assertions | `assertions.md` |
| Fixtures, auth state, and test data | `fixtures.md` |
| Drop-in base class templates | `BaseTest.py`, `BasePage.py` |

---

## When to Use This Skill

- Use when scaffolding a new Playwright Python project from scratch
- Use when writing Page Object classes or pytest tests
- Use when the user asks about cross-browser testing, parallel execution, or Allure reports
- Use when fixing flaky tests or replacing `time.sleep()` with stable waits
- Use when setting up Playwright in CI/CD pipelines (GitHub Actions, GitLab, Docker)
- Use when combining API calls and UI assertions in a single test
- Use when the user mentions "POM pattern", "BrowserContext", "pytest fixtures", or "trace"

---

### Step 0: Read Test Cases and Locator Contract Files

Before generating page objects or tests:

1. **Check for test cases and locator files:**
   - Look for test cases in `tests/testcases/*.yaml` (e.g., `tests/testcases/test_login_ui_cases.yaml`). This file defines the test metadata, scenario descriptions, execution steps, and validations.
   - Look for page locators in `tests/locator_map/*.yaml` (e.g., `tests/locator_map/login.yaml`). This file defines the selectors for elements on the page.

2. **Parse YAML files:**
   - The YAML files act as the single source of truth for generating code.
   - They should NOT be read dynamically at runtime by the Python test suite to ensure maximum execution performance and reliability.
   - Extract selector strategies (`css`, `role`, `testid`, `placeholder`, etc.) from the locator map and convert them to explicit Playwright API calls.
   - Extract test steps and validations from the testcases file to structure the pytest functions.

3. **Generate code with hardcoded selectors and test flows:**
   - For Page Objects (`tests/pages/`): Hardcode the locators based on the locator map YAML (e.g., if YAML says `strategy: testid`, `value: "error"`, write `page.get_by_test_id("error")`).
   - For Tests (`tests/tests/`): Map the `action`s from the testcases YAML to the generated Page Object methods and Playwright `expect` assertions. Implement any test data fetching as defined in the testcase (e.g. reading from `tests/data/users.json`).
   - Do NOT guess or use hard-coded template assumptions that conflict with the YAML files.

4. **If contract files are missing:**
   - Ask the user to provide them or ask for selector/flow details.
   - DO NOT guess or use hard-coded example selectors.

This ensures **generated code matches the exact application architecture and user-defined workflow**, not a generic template.

---

### Step 1: Decide the Approach

Use this matrix to pick the right pattern before writing any code:

| User Request | Approach |
|---|---|
| New project from scratch | Full scaffold — see `config.md` |
| Single feature test | POM page class + pytest test class/function |
| API + UI hybrid | `APIRequestContext` beside `Page` |
| Cross-browser | parameterized browser fixture over `chromium`, `firefox`, `webkit` |
| Flaky test fix | replace `sleep` with `expect(...).to_be_visible()` or `wait_for_url` |
| CI integration | `python -m playwright install --with-deps` |
| Parallel execution | pytest-xdist or multiple workers with isolated fixtures |
| Rich reporting | Allure + Playwright trace + video recording |

---

### Step 2: Scaffold the Project Structure

Always use this layout when creating a new project:

```text
project/
├── tests/
│   ├── base/
│   │   ├── __init__.py
│   │   ├── base_test.py        ← BaseTest.py
│   │   └── base_page.py        ← BasePage.py
│   ├── pages/
│   │   └── login_page.py
│   ├── tests/
│   │   └── test_login.py
│   ├── utils/
│   │   ├── config.py
│   │   ├── test_data_factory.py
│   │   └── wait_utils.py
│   └── data/
│       └── users.json
├── conftest.py                 ← [REQUIRED] pytest hooks & session fixtures
├── pytest.ini
├── requirements.txt
├── .env.example
└── README.md
```

---

### Step 3: Set Up BaseTest Fixtures

```python
import os
import re
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from tests.utils.config import settings


@pytest.fixture(scope="session")
def browser(playwright: Playwright):
    browser = getattr(playwright, settings.browser).launch(headless=settings.headless)
    try:
        yield browser
    finally:
        browser.close()


@pytest.fixture
def page(browser: Browser, request: pytest.FixtureRequest) -> Page:
    Path("artifacts/videos").mkdir(parents=True, exist_ok=True)
    Path("artifacts/traces").mkdir(parents=True, exist_ok=True)
    context = browser.new_context(
        base_url=settings.base_url,
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="Asia/Kolkata",
        record_video_dir=str(Path("artifacts/videos")),
    )
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    try:
        yield page
    finally:
        if getattr(request.node, "rep_call", None) and request.node.rep_call.failed and not page.is_closed():
            allure.attach(page.screenshot(full_page=True), "Failure Screenshot",
                          allure.attachment_type.PNG)
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", request.node.nodeid)[:120]
        if not page.is_closed():
            page.close()
        context.tracing.stop(path=Path("artifacts/traces") / f"{safe_name}.zip")
        context.close()


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p
```

---

### Step 4: Build Page Object Classes

```python
from playwright.sync_api import Page

from tests.base.base_page import BasePage


class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.redirect_url = "**/"

        self.email_input = page.get_by_label("Email")
        self.password_input = page.get_by_label("Password")
        self.login_button = page.get_by_role("button", name="Sign in")
        self.error_message = page.get_by_test_id("login-error")

    def open(self):
        self.page.goto(f"{self.base_url}/login")
        self.wait_for_page_load()
        return self

    def login_as(self, email: str, password: str):
        self.fill(self.email_input, email)
        self.fill(self.password_input, password)
        self.click_and_wait_for_url(self.login_button, self.redirect_url)
        return HomePage(self.page)

    def login_expect_error(self, email: str, password: str):
        self.fill(self.email_input, email)
        self.fill(self.password_input, password)
        self.login_button.click()
        self.error_message.wait_for(state="visible")
        return self

    def get_error_message(self) -> str:
        return self.error_message.inner_text()
```

**Pattern:** Read locator file → Generate code with those specific selectors (not template assumptions).

---

### Step 5: Write Tests with pytest and Allure

```python
from playwright.sync_api import expect

from tests.pages.login_page import LoginPage
from tests.utils.test_data_factory import TestDataFactory


def test_should_login_with_valid_credentials(page):
    user = TestDataFactory.get_default_user()
    login_page = LoginPage(page).open()

    home_page = login_page.login_as(user["email"], user["password"])
    
    expect(home_page.welcome_banner).to_contain_text(user["username"])


def test_should_show_error_on_invalid_credentials(page):
    login_page = LoginPage(page).open()
    login_page.login_expect_error("bad@test.com", "wrongpass")

    expect(login_page.error_message).to_contain_text("Invalid credentials")
```


## Examples

### API + UI hybrid

```python
import json
from playwright.sync_api import expect


def test_new_order_is_visible(page):
    # Use API_BASE_URL and an injected token in real tests; never commit credentials.
    response = page.request.post(
        "/api/orders",
        headers={"Authorization": "Bearer token"},
        data={"productId": "SKU-001", "quantity": 2},
    )
    expect(response).to_be_ok()
    order_id = response.json()["id"]
    page.goto("/orders")
    expect(page.locator(f"tr[data-order-id='{order_id}']")).to_be_visible()
```

### Network mocking

```python
import json
from playwright.sync_api import expect


def test_api_failure_is_handled(page):
    page.route(
        "**/api/products",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body=json.dumps({"error": "Service Unavailable"}),
        ),
    )
    page.goto("/products")
    expect(page.get_by_test_id("error-banner")).to_have_text(
        "We're having trouble loading products. Please try again."
    )
```


### Example 3: Parallel Cross-Browser Test

```python
import pytest
from playwright.sync_api import Page, expect

def test_should_render_checkout_on_all_browsers(page: Page):
    checkout_page = CheckoutPage(page)
    checkout_page.navigate()
    expect(page.locator(".checkout-form")).to_be_visible()
```

### Example 4: Parallel Execution Config

```pytest.ini
[pytest]
# Enable parallel execution using the pytest-xdist plugin
# -n 4: Run on 4 workers
# --dist loadscope: Ensure tests in the same class or module run on the same worker
addopts = -n 4 --dist loadscope
```

### Example 5: GitHub Actions CI Pipeline

```yaml
- name: Install dependencies and Playwright browsers
  run: |
    pip install -r requirements.txt
    playwright install --with-deps

- name: Run tests
  run: pytest --browser=${{ matrix.browser }}

- name: Upload traces on failure
  uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-traces
    path: test-results/

- name: Upload Allure results
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: allure-results
    path: allure-results/
```

---
### Cross-browser execution

```bash
for browser in chromium firefox webkit; do BROWSER=$browser pytest; done
```

## Best Practices

- ✅ Use Pytest fixtures (`page`, `context`) with `pytest-xdist` to guarantee isolated, parallel-safe test execution
- ✅ Initialize all Locators in the `__init__` method of the Page Object class (`self.button = page.get_by_role("button")`)
- ✅ Return the next Page Object from navigation methods (fluent chaining)
- ✅ Use `expect(locator)` from `playwright.sync_api` — it auto-retries until timeout
- ✅ Use `get_by_role`, `get_by_label`, `get_by_test_id` as first-choice locators
- ✅ Manage tracing in `yield`-based fixtures via `context.tracing.start()` / `context.tracing.stop()` (see `BaseTest.py`)
- ✅ Use `pytest-check` when validating multiple fields without halting on the first failure — standard Playwright `expect` calls stop execution immediately upon assertion failure
- ✅ Place `pytest_runtest_makereport` in `conftest.py` at the project root to ensure hooks are correctly registered
- ✅ Set up saved auth state (`storage_state="state.json"`) in fixtures to skip login across test modules
- ❌ Never dynamically read YAML configuration files (locator maps/test cases) at runtime; they are exclusively for the AI to read and generate native, hardcoded Playwright API calls.
- ❌ Never use `time.sleep()` — replace with `page.wait_for_response()` or auto-retrying assertions
- ❌ Never hardcode base URLs — always use environment variables (`os.getenv("BASE_URL")`) or the `pytest-base-url` plugin
- ❌ Never instantiate `playwright` or `browser` inside a Page Object
- ❌ Never use XPath for dynamic or frequently changing elements

---

## Common Pitfalls

- **Problem:** Tests fail randomly in parallel mode using `pytest-xdist`
  **Solution:** Ensure you use the built-in `page` fixture for every test. Never share a `page` object globally; fixtures guarantee process-level `Playwright → Browser → Context → Page` isolation.
- **Problem:** `expect(locator).to_be_visible()` times out even when the element appears
  **Solution:** Increase timeout directly with `expect(locator).to_be_visible(timeout=10_000)` or globally via `context.set_default_timeout(10_000)` in the `context` fixture.
- **Problem:** `time.sleep(2)` was added but tests are still flaky
  **Solution:** Replace with `with page.expect_response("**/api/endpoint"): action()` or `expect(locator).to_have_text("Done")` which polls the DOM automatically.
- **Problem:** Playwright trace zip is empty or missing
  **Solution:** Verify `context.tracing.stop(path="trace.zip")` is called in the teardown phase (after `yield`) of your `context` fixture. Also confirm that the `pytest_runtest_makereport` hook lives in `conftest.py` — hooks in other modules are silently ignored.
- **Problem:** Allure report is blank or missing steps
  **Solution:** Install `allure-pytest` and run tests with the `--alluredir=allure-results` flag. Decorate Page Object methods with `@allure.step` to capture actions.
- **Problem:** Screenshot on failure is never captured even though the fixture looks correct
  **Solution:** The `pytest_runtest_makereport` hook must be in `conftest.py` at the project root. If it is placed in `BaseTest.py` or any other non-conftest module, pytest will not discover it, so `request.node.rep_call` is never set.
- **Problem:** `${ENV_VAR}` placeholders in config files appear literally at runtime
  **Solution:** Use an environment variable expansion utility (e.g., `os.path.expandvars`) when loading test data from files before consumption by tests.

---

## Related Skills

- `httpx` / `requests` — Python HTTP libraries for pure API test suites without any UI interaction; not agent skills, import directly
- `@selenium-python` — Legacy alternative; prefer Playwright for all new projects
- `@allure-pytest` — Deep-dive into Allure annotations, categories, and history trends
- `@testcontainers-python` — Use alongside this skill when tests need a live database or containerised service
- `@github-actions-ci` — For building complete multi-browser matrix CI pipelines
- `pytest-mock` / `unittest.mock` — Mock internal dependencies or external services during UI tests without full network interception
- `docker` / `docker-compose` — Spin up application stacks locally or in CI before the Playwright suite runs

## Limitations

- **Scope:** Use this skill only when the task clearly matches the scope described above. Do not treat generated code as a substitute for environment-specific validation or expert review.
- **Sync API only:** All patterns in this skill use `sync_playwright`. They are **not** compatible with `async` event loops (e.g. `pytest-asyncio`, FastAPI test clients). Use `async_playwright` and `asyncio` fixtures in those contexts.
- **Mobile emulation:** Native device emulation (touch events, device pixel ratio, geolocation) requires explicit `browser.new_context(device_scale_factor=..., is_mobile=True, ...)` configuration not covered by default fixtures. Refer to the Playwright docs for `playwright.devices` presets.
- **pytest-xdist + session fixtures:** Session-scoped fixtures are shared per-worker process, not globally, when using `pytest-xdist`. Each worker spawns its own `playwright` and `browser` instance. Do not assume a single browser is shared across all parallel workers.
- **Locator contract:** If no `locator_map/*.yaml` file exists for a page, the agent must ask the user for selector details before generating code. Do not guess or hard-code selectors based on common assumptions.
- **Clarification required:** Stop and ask for clarification if required inputs (BASE_URL, browser type, auth credentials, locator contract), permissions, safety boundaries, or success criteria are missing.
