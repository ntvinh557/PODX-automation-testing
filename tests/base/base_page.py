from __future__ import annotations

import os
from typing import Self
from urllib.parse import urljoin

import allure
from playwright.sync_api import Locator, Page


class BasePage:
    """Common page-object helper methods for Playwright Python tests."""

    def __init__(self, page: Page, base_url: str | None = None):
        self.page = page
        self.base_url = (base_url or os.getenv("BASE_URL", "")).rstrip("/")

    def get_url(self) -> str:
        """Return the page-relative URL; override this in concrete page objects."""
        return ""

    @allure.step("Navigate to page")
    def open(self, path: str | None = None) -> Self:
        relative_path = self.get_url() if path is None else path
        if not self.base_url:
            raise ValueError("base_url is required; set BASE_URL or pass base_url")
        url = urljoin(f"{self.base_url.rstrip('/')}/", relative_path.lstrip("/"))
        self.page.goto(url)
        self.wait_for_page_load()
        return self

    @allure.step("Wait for page load")
    def wait_for_page_load(self) -> None:
        """Wait for the page to be ready after navigation."""
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_load_state("networkidle")

    def by_role(self, role: str, name: str | None = None) -> Locator:
        if name:
            return self.page.get_by_role(role, name=name)
        return self.page.get_by_role(role)

    def by_label(self, label: str) -> Locator:
        return self.page.get_by_label(label)

    def by_test_id(self, test_id: str) -> Locator:
        return self.page.get_by_test_id(test_id)

    def by_text(self, text: str) -> Locator:
        return self.page.get_by_text(text)

    def by_placeholder(self, placeholder: str) -> Locator:
        return self.page.get_by_placeholder(placeholder)

    @allure.step("Fill input")
    def fill(self, locator: Locator, value: str) -> None:
        locator.fill(value)

    @allure.step("Type '{value}' character-by-character")
    def type_slowly(self, locator: Locator, value: str, delay: int = 50) -> None:
        """Type value character-by-character to trigger keystroke events."""
        locator.click()
        locator.press_sequentially(value, delay=delay)

    @allure.step("Click element")
    def click(self, locator: Locator) -> None:
        locator.wait_for(state="visible", timeout=10_000)
        locator.click()

    @allure.step("Click and wait for URL")
    def click_and_wait_for_url(self, locator: Locator, url: str) -> None:
        locator.click()
        self.page.wait_for_url(url, timeout=10_000)

    @allure.step("Wait for element to be visible")
    def wait_for_visible(self, locator: Locator, timeout_ms: int = 10_000) -> None:
        locator.wait_for(state="visible", timeout=timeout_ms)

    @allure.step("Wait for element to be hidden")
    def wait_for_hidden(self, locator: Locator, timeout_ms: int = 15_000) -> None:
        locator.wait_for(state="hidden", timeout=timeout_ms)

    def get_current_url(self) -> str:
        return self.page.url

    def get_page_title(self) -> str:
        return self.page.title()
