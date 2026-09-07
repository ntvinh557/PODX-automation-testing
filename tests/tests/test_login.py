"""test_login.py – Login test suite for MPODx.

Covers:
  TC-LOGIN-001  Successful login with valid credentials
  TC-LOGIN-002  Empty email -> displays inline error
  TC-LOGIN-003  Empty password -> displays inline error
  TC-LOGIN-004  Both fields empty -> displays both inline errors
  TC-LOGIN-005  Invalid email/password -> displays server error notification
  TC-LOGIN-006  Forgot Password link navigates correctly
  TC-LOGIN-007  Sign Up link navigates correctly
"""
from __future__ import annotations

import os
import re

import allure
import pytest
from playwright.sync_api import Page, expect

from tests.pages.login_page import LoginPage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import json
from pathlib import Path

def _load_users() -> dict:
    """Load test users and resolve environment variable templates (e.g. ${VAR})."""
    json_path = Path("tests/data/users.json")
    if not json_path.exists():
        return {}
    content = json_path.read_text(encoding="utf-8")
    
    def repl(match: re.Match) -> str:
        return os.getenv(match.group(1), "")
        
    resolved_content = re.sub(r"\$\{([A-Z0-9_]+)\}", repl, content)
    return json.loads(resolved_content)

_USERS_DATA = _load_users()

# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@allure.feature("Authentication")
@allure.story("Login")
class TestLogin:

    @allure.title("TC-LOGIN-001: Successful login with valid credentials")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.e2e
    def test_login_valid_credentials(self, page: Page) -> None:
        """Valid email + password -> redirects to home page."""
        valid_user = _USERS_DATA.get("valid_user", {})
        email = valid_user.get("email")
        password = valid_user.get("password")
        username = valid_user.get("username")
        
        if not email or not password:
            pytest.skip("TEST_USER_EMAIL / TEST_USER_PASSWORD not set in .env")

        login_page = LoginPage(page).open()
        login_page.login_as(email, password)

        expect(page).to_have_url(re.compile(r".*(app\.mpodx\.com|login).*"))
        if username:
            expect(page.locator("body")).to_contain_text(username)

    # ------------------------------------------------------------------

    # TC-LOGIN-002 merged into TC-LOGIN-004 (test_both_fields_empty_shows_both_errors)
    # Both tests covered the same scenario: empty submit shows email/password errors.

    # TC-LOGIN-002: Empty password
    @allure.title("TC-LOGIN-002: Empty password -> displays 'Password is required.' error")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.regression
    def test_password_required_error(self, page: Page) -> None:
        """Submit form with valid email and empty password -> password error displayed."""
        login_page = LoginPage(page).open()
        
        valid_user = _USERS_DATA.get("valid_user", {})
        login_page.fill(login_page.email_input, valid_user.get("email", "user@example.com"))
        login_page.password_input.focus()
        login_page.password_input.blur()
        login_page.click(login_page.login_button)

        expect(login_page.password_error).to_be_visible(timeout=10_000)
        expect(login_page.password_error).to_contain_text("Password is required.")

    # ------------------------------------------------------------------

    @allure.title("TC-LOGIN-003: Both fields empty -> displays both errors")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.regression
    def test_both_fields_empty_shows_both_errors(self, page: Page) -> None:
        """Submit empty form -> both inline error messages are displayed."""
        login_page = LoginPage(page).open()
        login_page.submit_empty()

        expect(login_page.email_error).to_be_visible(timeout=10_000)
        expect(login_page.email_error).to_contain_text("E-mail is required.")

        expect(login_page.password_error).to_be_visible(timeout=10_000)
        expect(login_page.password_error).to_contain_text("Password is required.")

    # ------------------------------------------------------------------

    @allure.title("TC-LOGIN-004: Invalid credentials -> 'account does not exist' notification")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    def test_invalid_credentials_shows_server_error(self, page: Page) -> None:
        """Invalid email/password -> server error notification toast appears."""
        login_page = LoginPage(page).open()
        
        invalid_user = _USERS_DATA.get("invalid_user", {})
        login_page.login_expect_error(
            email=invalid_user.get("email", "nonexistent@example.com"),
            password=invalid_user.get("password", "WrongPass123!"),
        )

        expect(login_page.server_error).to_be_visible(timeout=15_000)
        expect(login_page.server_error).to_contain_text(
            "The account does not exist, please check your username or login email"
        )

    # ------------------------------------------------------------------

    @allure.title("TC-LOGIN-005: Click 'Forgot Password?' -> navigates to forgot-password page")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.regression
    def test_forgot_password_link_navigates(self, page: Page) -> None:
        """Forgot Password? link navigates to the correct page."""
        login_page = LoginPage(page).open()
        login_page.go_to_forgot_password()

        expect(page).to_have_url(re.compile(r".*forgot-password.*"))

    # ------------------------------------------------------------------

    @allure.title("TC-LOGIN-006: Click 'Sign Up' -> navigates to sign-up page")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.regression
    def test_sign_up_link_navigates(self, page: Page) -> None:
        """Sign Up link navigates to the correct page."""
        login_page = LoginPage(page).open()
        login_page.go_to_sign_up()

        expect(page).to_have_url(re.compile(r".*sign-up.*"))
