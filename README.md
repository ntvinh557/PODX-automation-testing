# 🚀 PODX Automation Testing

An enterprise-grade End-to-End (E2E) Test Automation Framework designed for the **MPODx** platform ([https://app.mpodx.com](https://app.mpodx.com)), built with **Playwright Python**, **pytest**, and **Allure Report**.

This project implements the **Page Object Model (POM)** architectural pattern combined with a standardized **External Locator Map (YAML)** system, delivering high maintainability, scalability, and robust stability across CI/CD pipelines and local development environments.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Environment Configuration](#-environment-configuration)
- [Test Execution Guide](#-test-execution-guide)
- [Reporting & Debugging](#-reporting--debugging)
- [Extending the Framework](#-extending-the-framework)
- [Development Best Practices](#-development-best-practices)
- [Authors & Contributions](#-authors--contributions)

---

## 🌟 Key Features

- **Page Object Model (POM) + External Locator Contract**: Clear separation between UI locator definitions (`tests/locator_map/*.yaml`), page behaviors (`tests/pages/`), and test specifications (`tests/tests/`).
- **User-Facing Locators First**: Strictly adheres to Playwright's recommended locator philosophy (`get_by_role`, `get_by_placeholder`, `get_by_text`, `get_by_label`), ensuring resilient tests that withstand internal HTML refactoring.
- **Automatic Failure Artifacts Capture**: Automatically captures full-page screenshots attached directly to Allure Reports, records execution videos, and outputs Playwright Traces (`artifacts/traces/`).
- **Flexible Execution Modes**: Seamlessly switch between Headless and Headed modes, with configurable `slow_mo` speed for visual step-by-step debugging.
- **Granular Test Categorization**: Easily target test suites via pytest markers (`smoke`, `regression`, `e2e`).
- **Parallel Test Execution**: Out-of-the-box support for multi-worker parallel execution via `pytest-xdist`.
- **Automatic Flaky Test Retries**: Configured with `pytest-rerunfailures` to minimize false-negative CI test runs.

---

## 🛠 Architecture & Tech Stack

| Component | Technology / Library | Purpose |
|---|---|---|
| **Language** | Python 3.11 | Core development language |
| **Automation Engine** | [Playwright Python](https://playwright.dev/python/) | High-speed browser automation (Chromium, Firefox, WebKit) |
| **Test Runner** | [pytest](https://docs.pytest.org/) | Fixture management, test discovery, and assertions |
| **Reporting** | [Allure Report](https://allurereport.org/) | Comprehensive test reports with steps, severities, and attachments |
| **Locator Management** | PyYAML | Decoupled locator repository stored in declarative YAML files |
| **Parallel Execution** | pytest-xdist | Multi-process test parallelization across CPU cores |
| **Environment Management** | python-dotenv | Secure and decoupled environment variable loading |

---

## 📁 Project Structure

```text
PODX-automation-testing/
├── conftest.py                   # Root fixtures (playwright, browser, context, page) & Allure failure hooks
├── pytest.ini                    # Pytest configuration & registered markers (smoke, regression, e2e)
├── requirements.txt              # Project Python dependencies
├── .env                          # Local environment variables (Base URL, timeouts, test credentials)
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore file (artifacts, caches, virtualenvs)
│
├── tests/
│   ├── base/
│   │   ├── __init__.py
│   │   └── base_page.py          # Abstract BasePage providing reusable interactions (click, fill, wait...)
│   ├── pages/
│   │   ├── __init__.py
│   │   └── login_page.py         # Page Object encapsulation for the Login page
│   ├── locator_map/
│   │   └── login.yaml            # Declarative locator contract for Login elements
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_login.py         # Automated test cases for Login workflows
│   ├── data/
│   │   ├── __init__.py
│   │   └── users.json            # Test datasets and credential structures
│   └── utils/
│       ├── __init__.py
│       ├── locator_loader.py     # Utility to load and parse YAML locator files
│       └── settings.py           # Strongly-typed configuration dataclass
│
└── artifacts/                    # Auto-generated test execution artifacts (ignored by git)
    ├── traces/                   # Playwright trace archive files (.zip)
    └── videos/                   # Full-session test recordings (.webm)
```

---

## 💻 Prerequisitesx

- **Operating System**: macOS, Linux, or Windows
- **Python**: Version `3.11` *(Note: 3.13+ is not recommended yet due to missing wheel support for C-extension dependencies like `greenlet` used by Playwright)*
- **Node.js** *(Optional)*: Required if you wish to run the Allure CLI locally (`allure serve`)

Verify Python installation:
```bash
python3 --version
```

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/ntvinh557/PODX-automation-testing.git
cd PODX-automation-testing
```

### 2. Create and Activate a Virtual Environment
- **macOS / Linux:**
  ```bash
  python3 -m venv env
  source env/bin/activate
  ```
- **Windows (Command Prompt / PowerShell):**
  ```cmd
  python -m venv env
  env\Scripts\activate
  ```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
```bash
playwright install chromium
# Or install all supported browser engines (Chromium, Firefox, WebKit):
# playwright install
```

---

## ⚙️ Environment Configuration

Copy the sample environment file to `.env`:
```bash
cp .env.example .env
```

Review and update the variables in `.env`:
```ini
# Application base URL
BASE_URL=https://app.mpodx.com

# Browser engine: chromium | firefox | webkit
BROWSER=chromium

# Headless execution: true (headless) | false (headed browser window)
HEADLESS=true

# Slow-down delay between actions in milliseconds (useful for live debugging)
SLOW_MO=0

# Timeouts in milliseconds
DEFAULT_TIMEOUT=30000
NAVIGATION_TIMEOUT=60000

# Path to persisted authentication state file
AUTH_STATE=artifacts/auth/user-state.json

# Test user credentials
TEST_USER_EMAIL=your_email_or_username
TEST_USER_PASSWORD=your_password
TEST_USER_USERNAME=your_expected_username_after_login
TEST_ADMIN_EMAIL=admin@example.com
TEST_ADMIN_PASSWORD=your_admin_password
```

> [!IMPORTANT]
> The `.env` file contains sensitive credentials and is explicitly ignored in `.gitignore`. Never commit credentials to version control.

---

## 🚀 Test Execution Guide

Ensure your virtual environment is active before running tests:
```bash
source env/bin/activate
```

### 1. Run All Tests
```bash
pytest
```

### 2. Run a Specific Test Module
```bash
pytest tests/tests/test_login.py -v
```

### 3. Run by Test Marker
- **Run Smoke tests:**
  ```bash
  pytest -m smoke -v
  ```
- **Run Regression suite:**
  ```bash
  pytest -m regression -v
  ```
- **Run End-to-End tests:**
  ```bash
  pytest -m e2e -v
  ```

### 4. Run in Headed Mode (Display Browser UI)
Observe the browser actions directly during execution:
```bash
HEADLESS=false pytest tests/tests/test_login.py -v
```

### 5. Run with Slow-Motion (Visual Step Inspection)
```bash
HEADLESS=false SLOW_MO=500 pytest tests/tests/test_login.py -v
```

### 6. Run Against Different Browsers
```bash
BROWSER=firefox pytest tests/tests/test_login.py -v
BROWSER=webkit pytest tests/tests/test_login.py -v
```

### 7. Parallel Execution
Accelerate execution by distributing tests across multiple CPU cores:
```bash
# Automatically distribute across available CPU cores
pytest -n auto

# Or specify a fixed number of workers
pytest -n 2
```

### 8. Retry Flaky Tests Automatically
```bash
pytest --reruns 2 --reruns-delay 1
```

---

## 📊 Reporting & Debugging

### 1. Allure Report

1. **Install Allure CLI** (if not already installed):
   - **macOS (Homebrew):** `brew install allure`
   - **Linux / Windows:** Refer to the [Allure Installation Guide](https://allurereport.org/docs/install/)

2. **Run tests and generate Allure results:**
   ```bash
   pytest --alluredir=allure-results
   ```

3. **Serve and inspect the interactive report:**
   ```bash
   allure serve allure-results
   ```

> Whenever a test case **FAILS**, a full-page screenshot is automatically captured and attached directly under the **Attachments** section in Allure Report.

### 2. Playwright Trace Viewer

Traces containing full DOM snapshots, network waterfall graphs, and console output are automatically saved to `artifacts/traces/`:
```bash
playwright show-trace artifacts/traces/<trace_filename>.zip
```

### 3. Video Recordings
Video recordings of each test execution are saved under `artifacts/videos/*.webm`.

---

## 🧩 Extending the Framework

### 1. Define Locators for a New Page
Create a YAML file in `tests/locator_map/<page_name>.yaml`:
```yaml
home:
  url: /
  user_avatar:
    strategy: test_id
    value: "user-profile-avatar"
  logout_button:
    strategy: role
    role: button
    name: "Log out"
```

### 2. Implement a New Page Object
Inherit from `BasePage` in `tests/pages/<page_name>_page.py`:
```python
from tests.base.base_page import BasePage

class HomePage(BasePage):
    URL = "/"

    def __init__(self, page):
        super().__init__(page)
        self.avatar = self.by_test_id("user-profile-avatar")
        self.logout_btn = self.by_role("button", name="Log out")

    def logout(self):
        self.click(self.logout_btn)
```

### 3. Write a New Test Case
Create a test file under `tests/tests/test_<feature>.py`:
```python
import allure
import pytest
from playwright.sync_api import Page, expect
from tests.pages.home_page import HomePage

@allure.feature("Home")
class TestHome:

    @allure.title("TC-HOME-001: Verify home page renders successfully post-login")
    @pytest.mark.smoke
    def test_home_page_visible(self, page: Page):
        home_page = HomePage(page).open()
        expect(home_page.avatar).to_be_visible()
```

---

## 🎯 Development Best Practices

1. **No Hardcoded Locators in Tests**: Keep all locators encapsulated inside `tests/locator_map/*.yaml` or Page Object properties.
2. **Use Web-First Assertions**: Always assert via Playwright's `expect(locator).to_be_visible()`, `expect(locator).to_have_text()` instead of standard Python `assert`.
3. **Avoid Explicit Sleeps**: Never use `time.sleep()`. Leverage Playwright's built-in auto-waiting and the explicit wait utilities provided by `BasePage`.
4. **Strict Test Isolation**: Every test function receives an isolated `page` and `context` fixture. Avoid inter-test state dependencies.
5. **Comprehensive Allure Annotations**: Annotate test methods with `@allure.feature`, `@allure.story`, `@allure.title`, `@allure.severity`, and wrap high-level actions with `@allure.step`.

---

## 👥 Authors & Contributions

- **Repository**: [ntvinh557/PODX-automation-testing](https://github.com/ntvinh557/PODX-automation-testing)
- Contributions, issues, and feature requests are welcome! Feel free to open an Issue or submit a Pull Request.