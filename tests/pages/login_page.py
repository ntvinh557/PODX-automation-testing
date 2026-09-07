"""login_page.py – Page Object for MPODx Login page.

Locators are driven from: tests/locator_map/login.yaml

Note on validation error locators:
  Ant Design renders inline errors inside #control-hooks_email_help and
  #control-hooks_password_help with role="alert". These are located via
  page.locator() instead of get_by_text() because the text is nested inside
  a div that may contain other children and exact matching is fragile.
"""
from __future__ import annotations

import allure
from playwright.sync_api import Locator, Page

from tests.base.base_page import BasePage


class LoginPage(BasePage):
    """Page Object for https://app.mpodx.com/login/

    All locators are resolved directly from tests/locator_map/login.yaml:
      email          -> strategy: placeholder  | value: "E-mail..."
      password       -> strategy: placeholder  | value: "Password..."
      submit         -> strategy: role         | role: button, name: "Login"
      forgot_password-> strategy: text         | value: "Forgot Password?"
      sign_up        -> strategy: text         | value: "Sign Up"
      email_error    -> strategy: text         | value: "E-mail is required."
      password_error -> strategy: text         | value: "Password is required."
      server_error   -> strategy: text         | value: "The account does not exist..."
    """

    URL = "/login/"

    def __init__(self, page: Page):
        super().__init__(page)
        from tests.utils.locator_loader import load_locators
        self.locators = load_locators("login")
        self.redirect_url = self.locators.get("redirect_url", "**/")
        # --- Inputs ---
        self.email_input    = self.by_placeholder("E-mail...")
        self.password_input = self.by_placeholder("Password...")

        # --- Actions ---
        self.login_button      = self.by_role("button", name="Login")
        self.forgot_password   = self.by_text("Forgot Password?")
        self.sign_up_link      = self.by_text("Sign Up")

        # --- Validation errors (empty submit) ---
        self.email_error    = self.page.locator("#control-hooks_email_help")
        self.password_error = self.page.locator("#control-hooks_password_help")

        # --- Server-side error (wrong credentials) ---
        self.server_error = page.locator(".ant-notification-notice-message")

    def get_url(self) -> str:
        return self.URL

    @allure.step("Open Login page")
    def open(self) -> "LoginPage":
        super().open()
        return self

    @allure.step("Wait for login page to be ready")
    def wait_for_page_load(self) -> None:
        super().wait_for_page_load()
        self.email_input.wait_for(state="visible", timeout=15_000)

    @allure.step("Login with email='{email}'")
    def login_as(self, email: str, password: str) -> None:
        """Fill credentials and submit; caller should assert redirect URL."""
        self.fill(self.email_input, email)
        self.fill(self.password_input, password)
        self.click_and_wait_for_url(self.login_button, self.redirect_url)

    @allure.step("Submit login expecting validation or server error")
    def login_expect_error(self, email: str = "", password: str = "") -> "LoginPage":
        """Fill (or leave empty) credentials and click Login without waiting
        for a URL change – used when expecting error messages to appear."""
        if email:
            self.fill(self.email_input, email)
        if password:
            self.fill(self.password_input, password)
        self.click(self.login_button)
        return self

    @allure.step("Submit empty form")
    def submit_empty(self) -> "LoginPage":
        """Click Login with both fields empty to trigger required-field errors.

        Ant Design Form only validates 'touched' fields. We must click+blur
        each field before submitting so the form marks them as touched.
        """
        # Touch email field (click then Tab away) to mark as dirty
        self.email_input.click()
        self.page.keyboard.press("Tab")
        # Touch password field
        self.password_input.click()
        self.page.keyboard.press("Tab")
        # Now submit
        self.click(self.login_button)
        return self

    @allure.step("Click Forgot Password")
    def go_to_forgot_password(self) -> None:
        self.click(self.forgot_password)

    @allure.step("Click Sign Up")
    def go_to_sign_up(self) -> None:
        self.click(self.sign_up_link)
