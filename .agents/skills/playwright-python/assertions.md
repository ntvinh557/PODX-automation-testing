# Playwright Python – Assertions Reference

## Import Statement

```python
from playwright.sync_api import expect
```

---

## Locator Assertions (Auto-Retry)

Playwright's `expect(locator)` automatically retries until the condition is met or timeout expires.
Prefer these over manual checks with `is_visible()` and `assert` only when necessary.

```python
# Visibility
expect(locator).to_be_visible()
expect(locator).to_be_hidden()

# Enabled / Disabled
expect(locator).to_be_enabled()
expect(locator).to_be_disabled()

# Text content
expect(locator).to_contain_text("partial")
expect(locator).to_have_text("Exact text")
expect(locator).to_have_text(re.compile(r"Order #\d+"))

# Multiple elements
expect(locator).to_have_count(5)

# Locator Uniqueness (Critical for LocatorSpec validation)
# When using locator_map, validate each selector matches EXACTLY 1 element
expect(login_email_field).to_have_count(1)  # Fails if 0 or >1 elements match
expect(login_submit_button).to_have_count(1)  # Ensures no ambiguity

# Attribute
expect(locator).to_have_attribute("aria-expanded", "true")
expect(locator).to_have_attribute("href", "/")

# Class names
expect(locator).to_have_class(re.compile(r"btn-.*"))

# Input value
expect(locator).to_have_value("expected value")
expect(locator).to_have_value(re.compile(r"\d{4}-\d{2}-\d{2}"))

# Checked state
expect(locator).to_be_checked()
expect(locator).not_to_be_checked()

# Focused state
expect(locator).to_be_focused()

# Editable
expect(locator).to_be_editable()
```

---

## Page Assertions

```python
# URL
expect(page).to_have_url("https://example.com/")
expect(page).to_have_url(re.compile(r".*\/$"))

# Title
expect(page).to_have_title("My App")
expect(page).to_have_title(re.compile(r".*App.*"))
```

---

## Negation

```python
expect(locator).not_to_be_visible()
expect(page).not_to_have_url(re.compile(r".*/login"))
expect(locator).not_to_have_text("Error")
```

---

## Custom Timeout on Assertion

```python
expect(locator).to_be_visible(timeout=10_000)
```

---

## Soft Assertions

Use soft assertions when you want to validate multiple conditions without failing immediately:

For richer soft-assert support, many teams use `pytest-check` or a custom helper method:

```python
# Example dependency-free soft assertion helper
class SoftAssert:
    def __init__(self):
        self.errors = []

    def check(self, condition: bool, message: str):
        if not condition:
            self.errors.append(message)

    def assert_all(self):
        if self.errors:
            raise AssertionError("\n".join(self.errors))
```

Usage:

```python
soft = SoftAssert()
soft.check(page.locator("#name").input_value() == "Amal", "Name is incorrect")
soft.check("@" in page.locator("#email").input_value(), "Email format incorrect")
soft.assert_all()
```

---

## Response Assertions

```python
import os

response = page.request.get(f"{os.environ['API_BASE_URL'].rstrip('/')}/api/health")
assert response.ok
assert response.status == 200
assert "application/json" in response.headers["content-type"]
assert response.json()["status"] == "UP"
```

---

## Screenshot Comparison (Visual Testing)

```python
expect(page).to_have_screenshot("home.png", full_page=True, threshold=0.2)
expect(page.locator(".chart-container")).to_have_screenshot("revenue-chart.png")

# Update golden files deliberately by deleting/re-recording the expected snapshot,
# or use the snapshot-update option provided by the visual-testing plugin in use.
```

---

## Common Anti-Patterns to Avoid

```python
# ❌ WRONG
assert page.locator(".spinner").is_hidden()
import time; time.sleep(2)

# ✅ CORRECT
expect(page.locator(".spinner")).to_be_hidden()
```
