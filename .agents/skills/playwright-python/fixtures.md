# Playwright Python – Fixtures, Hooks & Test Data

## pytest Fixture Pattern

Encapsulate the browser lifecycle with fixtures:

```python
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture
def context(browser: Browser):
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext):
    page = context.new_page()
    yield page
    page.close()



---

## Test Data Factory

```python
import json
from pathlib import Path
import os
import re

from faker import Faker


def _resolve_env_vars(value: str) -> str:
    """Thay thế placeholder ``${VAR_NAME}`` bằng giá trị từ environment.

    Ví dụ: ``"${TEST_ADMIN_PASSWORD}"`` → giá trị của ``os.environ['TEST_ADMIN_PASSWORD']``.
    Nếu biến không tồn tại, giữ nguyên placeholder để lỗi rõ ràng hơn là
    đăng nhập bằng chuỗi sai.
    """
    return re.sub(
        r"\$\{([^}]+)\}",
        lambda m: os.environ.get(m.group(1), m.group(0)),
        value,
    )


class TestDataFactory:
    faker = Faker()

    @staticmethod
    def load_users() -> list[dict]:
        data_path = Path(__file__).resolve().parents[1] / "data" / "users.json"
        raw: list[dict] = json.loads(data_path.read_text(encoding="utf-8"))
        # Resolve ${ENV_VAR} placeholders in every string field.
        return [
            {
                k: _resolve_env_vars(v) if isinstance(v, str) else v
                for k, v in user.items()
            }
            for user in raw
        ]

    @staticmethod
    def get_default_user() -> dict:
        for user in TestDataFactory.load_users():
            if user["role"] == "default":
                return user
        raise RuntimeError("No default user in users.json")

    @staticmethod
    def get_admin_user() -> dict:
        for user in TestDataFactory.load_users():
            if user["role"] == "admin":
                return user
        raise RuntimeError("No admin user in users.json")

    @staticmethod
    def generate_random_user() -> dict:
        return {
            "email": TestDataFactory.faker.email(),
            "password": TestDataFactory.faker.password(
                length=16, special_chars=True, digits=True, upper_case=True, lower_case=True
            ),
            "first_name": TestDataFactory.faker.first_name(),
            "last_name": TestDataFactory.faker.last_name(),
            "role": "default",
        }

    @staticmethod
    def random_phone() -> str:
        return TestDataFactory.faker.phone_number()

    @staticmethod
    def random_postal_code() -> str:
        return TestDataFactory.faker.postcode()
```

---

## `users.json`

```json
[
  {
    "email": "admin@example.test",
    "password": "${TEST_ADMIN_PASSWORD}",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin"
  },
  {
    "email": "user@example.test",
    "password": "${TEST_USER_PASSWORD}",
    "first_name": "Test",
    "last_name": "User",
    "role": "default"
  }
]
```

---

## Reuse Auth State

Save login state once and reuse it across tests:

```python
from pathlib import Path

from playwright.sync_api import sync_playwright


def save_auth_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(f"{os.environ['BASE_URL'].rstrip('/')}/login")
            page.get_by_label("Email").fill(os.environ["TEST_USER_EMAIL"])
            page.get_by_label("Password").fill(os.environ["TEST_USER_PASSWORD"])
            page.get_by_role("button", name="Sign in").click()
            page.wait_for_url("**/dashboard")

            state_path = Path("artifacts/auth/user-state.json")
            state_path.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(state_path))
            context.close()
        finally:
            browser.close()
```

Then reuse state in tests:

```python
context = browser.new_context(storage_state="artifacts/auth/user-state.json")
```

---

## Screenshot on Failure

```python
import pytest
from playwright.sync_api import expect


def test_example(page):
    try:
        expect(page.locator("#result")).to_contain_text("Success")
    except AssertionError:
        screenshot_path = Path("artifacts/screenshots") / "failure-example.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(screenshot_path), full_page=True)
        raise
```

For suite-wide capture, keep screenshot/trace attachment in the shared `page`
fixture (see `BaseTest.py`) rather than repeating `try/except` in every test.

---

## WaitUtils Helper

```python
from playwright.sync_api import Locator


class WaitUtils:
    @staticmethod
    def wait_for_spinner_to_disappear(page):
        page.locator(".loading-spinner").wait_for(state="hidden", timeout=15_000)

    @staticmethod
    def wait_for_toast_message(page, message: str):
        page.get_by_role("alert").filter(has_text=message).wait_for(
            state="visible", timeout=5_000
        )

    @staticmethod
    def wait_for_api_response(page, url_pattern: str, action):
        with page.expect_response(lambda response: url_pattern in response.url) as response_info:
            action()
        return response_info.value
```

---

## Retry Logic for Flaky Tests

Install `pytest-rerunfailures` and opt in explicitly:

```python
import pytest


@pytest.mark.flaky(reruns=2, reruns_delay=1)
def test_eventually_consistent_flow(page):
    ...
```

Retries are not a substitute for fixing synchronization or product defects.

---

## Pre-authenticated Context

```python
from pathlib import Path
from playwright.sync_api import sync_playwright


def save_auth_state(base_url: str, email: str, password: str):
    state_path = Path("artifacts/auth/user-state.json")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{base_url.rstrip('/')}/login")
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url("**/dashboard")
        context.storage_state(path=str(state_path))
        browser.close()
```
