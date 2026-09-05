# Playwright Python – Page Object Patterns

## Component Pattern (Reusable Sub-Page Objects)

For repeated UI components (navbars, modals, tables), create component classes:

```python
from playwright.sync_api import Locator, Page

from tests.base.base_page import BasePage


class DataTable(BasePage):
    def __init__(self, page: Page, table_root: Locator):
        super().__init__(page)
        self.table_root = table_root

    def get_row_count(self) -> int:
        return self.table_root.locator("tbody tr").count()

    def get_cell_value(self, row: int, col: int) -> str:
        return (
            self.table_root.locator("tbody tr")
            .nth(row)
            .locator("td")
            .nth(col)
            .inner_text()
        )

    def click_row_action(self, row: int, action_label: str):
        self.table_root.locator("tbody tr").nth(row).get_by_role("button", name=action_label).click()

    def sort_by_column(self, column_header: str) -> "DataTable":
        self.table_root.get_by_role("columnheader", name=column_header).click()
        return self


class UsersPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.users_table = DataTable(page, page.locator("#users-table"))
        self.search_input = page.get_by_placeholder("Search users...")
        self.add_user_button = page.get_by_role("button", name="Add User")

    def open(self):
        return super().open("/admin/users")

    def search_for(self, query: str):
        self.search_input.fill(query)
        with self.page.expect_response(lambda response: "/api/users" in response.url):
            self.search_input.press("Enter")
        return self
```

---

## Modal / Dialog Component

```python
from playwright.sync_api import Locator, Page

from tests.base.base_page import BasePage


class ConfirmDialog(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.dialog = page.get_by_role("dialog")
        self.confirm_button = self.dialog.get_by_role("button", name="Confirm")
        self.cancel_button = self.dialog.get_by_role("button", name="Cancel")
        self.title_text = self.dialog.get_by_role("heading")

    def wait_for_open(self):
        self.dialog.wait_for(state="visible")

    def confirm(self):
        self.confirm_button.click()
        self.dialog.wait_for(state="hidden")

    def cancel(self):
        self.cancel_button.click()

    def get_title(self) -> str:
        return self.title_text.inner_text()
```

---

## Navigation Chain Pattern

Page methods should return the next page object — not `None` for a navigation flow:

```python
class DashboardPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)


class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Selectors from tests/locator_map/login.yaml
        # strategy: label → get_by_label("Email")
        self.email_input = page.get_by_label("Email")
        # strategy: label → get_by_label("Password")
        self.password_input = page.get_by_label("Password")
        # strategy: role button name="Sign in" → get_by_role()
        self.login_button = page.get_by_role("button", name="Sign in")
        # strategy: test_id → get_by_test_id("login-error")
        self.error_message = page.get_by_test_id("login-error")

    def open(self):
        self.page.goto(f"{self.base_url}/login")
        self.wait_for_page_load()
        return self

    def login_as(self, email: str, password: str) -> DashboardPage:
        self.fill(self.email_input, email)
        self.fill(self.password_input, password)
        self.click_and_wait_for_url(self.login_button, "**/dashboard")
        return DashboardPage(self.page)
```

**Design Note:** When AI generates code for a new project:
1. User provides locator file: `tests/locator_map/login.yaml`
2. AI reads the file, understands strategies (role, label, test_id, etc.)
3. AI generates code with correct selectors baked in
4. Each comment shows the mapping from YAML strategy to Playwright API
5. No runtime loaders—selectors are self-contained in the Page Object class

Usage:

```python
dashboard = LoginPage(page).open().login_as("user@test.com", "secret")
```

---

## Dynamic Locators

For lists of items that share structure:

```python
class ProductPage(BasePage):
    def get_product_card(self, product_name: str):
        return self.page.locator(".product-card").filter(has_text=product_name)

    def wait_for_order_row(self, order_id: str) -> None:
        row_locator = self.page.locator(f"[data-order-id='{order_id}']")
        self.page.locator("tr").filter(has=row_locator).wait_for(
            state="visible", timeout=15_000
        )
```

---

## Dropdown / Select Handling

```python
# Native select
page.select_option("#country-select", "India")

# Custom dropdown
page.get_by_label("Country").click()
page.get_by_role("listbox").get_by_text("India").click()
```

---

## File Upload

```python
page.set_input_files("#file-upload", "src/test/resources/testdata/sample.pdf")
# Target the underlying <input type="file">, not a visual drop-zone container.
page.locator(".upload-zone input[type='file']").set_input_files(
    "src/test/resources/testdata/sample.pdf"
)
page.set_input_files(
    "#file-upload",
    ["src/test/resources/testdata/file1.png", "src/test/resources/testdata/file2.png"],
)
```

---

## Download Handling

```python
with page.expect_download() as download_info:
    page.get_by_role("button", name="Export CSV").click()

download = download_info.value
download_path = download.path()
assert download_path is not None
assert download_path.exists()
```

---

## Hover & Tooltip Verification

```python
page.get_by_test_id("info-icon").hover()
tooltip = page.get_by_role("tooltip")
tooltip.wait_for()
expect(tooltip).to_contain_text("This field is required")
```

---

## Waiting Strategies (Anti-Flake)

```python
# Register the response listener before the action that triggers the request.
with page.expect_response(lambda response: "/api/search" in response.url):
    search_input.fill("test")

# Prefer a concrete readiness assertion over network-idle in SPAs.
expect(page.get_by_test_id("page-ready")).to_be_visible()

# Wait for element count to stabilize
rows = page.locator("tbody tr")
rows.first.wait_for()
expect(rows).to_have_count(10)

# Poll a custom condition
expect(page.locator(".spinner")).to_have_count(0)
```

---

## Common Anti-Patterns to Avoid

```python
# ❌ WRONG
page.locator(".spinner").is_hidden()
import time; time.sleep(2)

# ✅ CORRECT
expect(page.locator(".spinner")).to_be_hidden()
```
