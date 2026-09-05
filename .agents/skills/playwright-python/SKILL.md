---
name: playwright-python
description: "Scaffold, write, debug, and enhance enterprise-grade Playwright E2E tests in Python using Page Object Model, pytest, Allure reporting, and parallel execution."
category: test-automation
risk: safe
source: community
date_added: "2026-09-01"
author: copilot
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

### Step 0: Read Locator Contract File

Before generating page objects or tests:

1. **Ask user or check for locator file:**
   - Look for `tests/locator_map/login.yaml` or similar
   - This file defines selectors for login page elements
   - Example content:
     ```yaml
     login:
       url: /login
       email:
         strategy: label
         value: Email
       password:
         strategy: label
         value: Password
       submit:
         strategy: role
         role: button
         name: Sign in
       error:
         strategy: test_id
         value: login-error
     ```

2. **Parse the locator contract:**
   - Extract selector strategy and value
   - Understand what `strategy: label value: Email` means
   - Convert to Playwright API calls

3. **Generate code with correct selectors:**
   - Use the values from YAML directly in generated code
   - Do NOT hard-code based on template assumptions
   - Example: If YAML says `label "Email"`, use `page.get_by_label("Email")`

4. **If locator file missing:**
   - Ask user to provide it
   - OR ask user for selector details (what label/role/test_id to use)
   - DO NOT guess or use hard-coded example selectors

This ensures **generated code matches the actual application**, not a generic template.

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
        self.click_and_wait_for_url(self.login_button, "**/dashboard")
        return DashboardPage(self.page)

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

    dashboard = login_page.login_as(user["email"], user["password"])
    
    expect(dashboard.welcome_banner).to_contain_text(user["first_name"])


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
- ✅ Rely on `pytest-playwright` CLI flags (`--tracing on`) or manage tracing in `yield`-based fixtures
- ✅ Use `expect.soft(locator)` when validating multiple fields on a single page without halting on the first failure
- ✅ Set up saved auth state (`storage_state="state.json"`) in fixtures to skip login across test modules
- ❌ Never use `time.sleep()` — replace with `page.wait_for_response()` or auto-retrying assertions
- ❌ Never hardcode base URLs — always use environment variables (`os.getenv("BASE_URL")`) or the `pytest-base-url` plugin
- ❌ Never instantiate `playwright` or `browser` inside a Page Object
- ❌ Never use XPath for dynamic or frequently changing elements

---

## Common Pitfalls

- **Problem:** Tests fail randomly in parallel mode using `pytest-xdist`
**Solution:** Ensure you use the built-in `page` fixture for every test. Never share a `page` object globally; fixtures guarantee process-level `Playwright → Browser → Context → Page` isolation.
- **Problem:** `expect(locator).to_be_visible()` times out even when the element appears
**Solution:** Increase timeout directly with `expect(locator).to_be_visible(timeout=10_000)` or globally via `page.context.set_default_timeout(10_000)` in a fixture.
- **Problem:** `time.sleep(2)` was added but tests are still flaky
**Solution:** Replace with `with page.expect_response("**/api/endpoint"): action()` or `expect(locator).to_have_text("Done")` which polls the DOM automatically.
- **Problem:** Playwright trace zip is empty or missing
**Solution:** Ensure you pass `--tracing retain-on-failure` to `pytest`, or manually verify `context.tracing.stop(path="trace.zip")` occurs in the teardown phase (after `yield`) of your fixture.
- **Problem:** Allure report is blank or missing steps
**Solution:** Install `allure-pytest` and run tests with the `--alluredir=allure-results` flag. Decorate Page Object methods with `@allure.step` to capture actions.
- **Problem:** `storage_state` auth file is stale and tests redirect to login
**Solution:** Use a session-scoped fixture or a prerequisite script to regenerate `state.json` via API before the UI test suite begins.

---

## Related Skills

- `@requests` or `@httpx` — Use for pure API test suites without any UI interaction
- `@selenium-python` — Legacy alternative; prefer Playwright for all new projects
- `@allure-pytest` — Deep-dive into Allure annotations, categories, and history trends
- `@testcontainers-python` — Use alongside this skill when tests need a live database or service
- `@github-actions-ci` — For building complete multi-browser matrix CI pipelines

## Limitations

- Use this skill only when the task clearly matches the scope described above.
- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.
