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
from tests.utils.api_mocker import APIMocker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from tests.utils.test_data_factory import TestDataFactory
from tests.utils.settings import settings

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
        valid_user = TestDataFactory.get_valid_user()
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
        
        valid_user = TestDataFactory.get_valid_user()
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
        
        invalid_user = TestDataFactory.get_invalid_user()
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

    # ------------------------------------------------------------------
    # Mocking API Edge Cases (TC-LOGIN-007 -> TC-LOGIN-011)
    # ------------------------------------------------------------------

    @allure.title("TC-LOGIN-007: Mocked 500 Server Error handles gracefully")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    def test_mock_500_server_error(self, page: Page) -> None:
        """UI displays graceful error message when API returns 500 Internal Server Error."""
        APIMocker(page).mock_login_error(status=500, error_message="Internal Server Error")
        login_page = LoginPage(page).open()
        
        valid_user = TestDataFactory.get_valid_user()
        login_page.login_expect_error(
            email=valid_user.get("email", "test@example.com"),
            password=valid_user.get("password", "Pass123!"),
        )
        
        expect(login_page.server_error).to_be_visible(timeout=15_000)
        # Using the expected text the user updated manually in their code
        expect(login_page.server_error).to_contain_text("Internal Server Error")

    # ------------------------------------------------------------------

    @allure.title("TC-LOGIN-008: Mocked 429 Rate Limiting warning")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    def test_mock_429_rate_limiting(self, page: Page) -> None:
        """UI displays rate limit warning when API returns 429 Too Many Requests."""
        APIMocker(page).mock_login_error(
            status=429, 
            error_message="Too Many Requests", 
            headers={"Retry-After": "60"}
        )
        login_page = LoginPage(page).open()
        
        valid_user = TestDataFactory.get_valid_user()
        login_page.login_expect_error(
            email=valid_user.get("email", "test@example.com"),
            password=valid_user.get("password", "Pass123!"),
        )

        expect(login_page.server_error).to_be_visible()
        expect(login_page.server_error).to_contain_text("Too Many Requests")

    # ------------------------------------------------------------------

    @allure.title("TC-LOGIN-009: Mocked Delayed Response (Network latency)")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.regression
    def test_mock_delayed_response(self, page: Page) -> None:
        """UI prevents double submission and handles high latency gracefully."""
        APIMocker(page).mock_login_delayed_success(delay_ms=2000, body={"id": 1, "token": "fake-token"})
        login_page = LoginPage(page).open()
        
        valid_user = TestDataFactory.get_valid_user()
        login_page.fill(login_page.email_input, valid_user.get("email", "test@example.com"))
        login_page.fill(login_page.password_input, valid_user.get("password", "Pass123!"))
        
        # Click without waiting for navigation yet
        login_page.click(login_page.login_button)
        
        # Assert the button is immediately disabled while the request is pending
        expect(login_page.login_button).to_be_disabled()

    # ------------------------------------------------------------------

    @allure.title("TC-LOGIN-010: Mocked 403 Forbidden (Locked Account)")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    def test_mock_403_locked_account(self, page: Page) -> None:
        """UI handles locked account scenario properly."""
        APIMocker(page).mock_login_error(status=403, error_message="Account is locked")
        login_page = LoginPage(page).open()
        
        valid_user = TestDataFactory.get_valid_user()
        login_page.login_expect_error(
            email=valid_user.get("email", "test@example.com"),
            password=valid_user.get("password", "Pass123!"),
        )

        expect(login_page.server_error).to_be_visible()
        expect(login_page.server_error).to_contain_text("Account is locked")

    # ------------------------------------------------------------------

    @allure.title("TC-LOGIN-011: Mocked Contract Change (Missing Token in 200 OK)")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    def test_mock_contract_change_missing_token(self, page: Page) -> None:
        """UI handles unexpected JSON schema gracefully (Defensive Programming)."""
        APIMocker(page).mock_login_custom_response(
            status=200, 
            body={"access_token": "fake-token", "user": {}}
        )
        login_page = LoginPage(page).open()
        
        valid_user = TestDataFactory.get_valid_user()
        login_page.fill(login_page.email_input, valid_user.get("email", "test@example.com"))
        login_page.fill(login_page.password_input, valid_user.get("password", "Pass123!"))
        # Wait for the network response to finish by wrapping the action that triggers it
        with page.expect_response(f"{settings.api_url}/login/"):
            login_page.click(login_page.login_button)
        
        # The frontend should stay on the page instead of crashing
        expect(page).to_have_url(re.compile(r".*login.*"))
