from __future__ import annotations

import os
import re
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


# NOTE: pytest_runtest_makereport hook MUST live in conftest.py to be auto-discovered.
# See conftest.py for the correct placement of this hook.


class BaseTest:
    """Base class used by tests that need a reusable Playwright browser setup."""

    @staticmethod
    def resolve_browser_name(name: str | None = None) -> str:
        browser_name = (name or os.getenv("BROWSER", "chromium")).lower()
        if browser_name not in {"chromium", "firefox", "webkit"}:
            raise ValueError(f"Unsupported browser: {browser_name}")
        return browser_name

    @pytest.fixture(scope="session")
    def browser(self, playwright: Playwright):
        browser_name = self.resolve_browser_name()
        browser = getattr(playwright, browser_name).launch(
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            slow_mo=int(os.getenv("SLOW_MO", "0")),
        )
        try:
            yield browser
        finally:
            browser.close()

    @pytest.fixture(scope="function")
    def context(self, browser: Browser, request: pytest.FixtureRequest):
        trace_dir = Path("artifacts/traces")
        video_dir = Path("artifacts/videos")
        trace_dir.mkdir(parents=True, exist_ok=True)
        video_dir.mkdir(parents=True, exist_ok=True)

        auth_state = Path(os.getenv("AUTH_STATE", "artifacts/auth/user-state.json"))
        base_url = os.getenv("BASE_URL")
        if not base_url:
            raise ValueError("BASE_URL must be set before running browser tests")
        context_options = {
            "base_url": base_url,
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone_id": "Asia/Kolkata",
            "record_video_dir": str(video_dir),
        }
        if auth_state.exists():
            context_options["storage_state"] = str(auth_state)
        context = browser.new_context(**context_options)
        context.set_default_timeout(int(os.getenv("DEFAULT_TIMEOUT", "30000")))
        context.set_default_navigation_timeout(
            int(os.getenv("NAVIGATION_TIMEOUT", "60000"))
        )
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        try:
            yield context
        finally:
            safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", request.node.nodeid)[:120]
            try:
                context.tracing.stop(path=trace_dir / f"{safe_name}.zip")
            finally:
                context.close()

    @pytest.fixture(scope="function")
    def page(self, context: BrowserContext, request: pytest.FixtureRequest):
        page = context.new_page()
        try:
            yield page
        finally:
            failed = (
                getattr(request.node, "rep_call", None) is not None
                and request.node.rep_call.failed
            )
            if failed and not page.is_closed():
                try:
                    allure.attach(
                        page.screenshot(full_page=True),
                        name="Failure Screenshot",
                        attachment_type=allure.attachment_type.PNG,
                    )
                except Exception as exc:
                    # Tránh ẩn lỗi gốc của test bởi lỗi chụp screenshot
                    print(f"[WARN] Could not capture failure screenshot: {exc}")
            if not page.is_closed():
                page.close()

    @pytest.fixture(scope="session")
    def playwright(self):
        with sync_playwright() as p:
            yield p
