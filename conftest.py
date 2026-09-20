"""conftest.py – Root conftest for Playwright Python test suite.

IMPORTANT: This file MUST live at the project root (same level as pytest.ini).
pytest auto-discovers hooks and fixtures defined here for the entire test suite.

DO NOT place pytest hooks (e.g. pytest_runtest_makereport) in any other module
(e.g. BaseTest.py) – they will silently be ignored.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

# Load .env at import time so all os.getenv() calls in fixtures pick up values
load_dotenv()

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


# ---------------------------------------------------------------------------
# Hook: expose test result to fixtures (required for screenshot-on-failure)
# ---------------------------------------------------------------------------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
    """Attach test result to ``item.rep_call`` and ``item.rep_setup`` so fixtures can
    detect failures and capture a screenshot/trace before teardown.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def playwright() -> Playwright:
    """Start a single Playwright instance for the entire test session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Browser:
    """Launch one browser process per session."""
    browser_name = os.getenv("BROWSER", "chromium").lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise ValueError(f"Unsupported browser: {browser_name!r}")
    browser = getattr(playwright, browser_name).launch(
        headless=os.getenv("HEADLESS", "true").lower() == "true",
        slow_mo=int(os.getenv("SLOW_MO", "0")),
    )
    try:
        yield browser
    finally:
        browser.close()


@pytest.fixture(scope="class")
def authenticated_session(browser: Browser):
    """
    Logs in once per test class and saves the auth token to artifacts/auth/user-state.json.
    Classes can use this via @pytest.mark.usefixtures('authenticated_session').
    """
    state_path = Path(os.getenv("AUTH_STATE", "artifacts/auth/user-state.json"))
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Chỉ thực hiện thao tác UI Login nếu chưa có sẵn file state
    if not state_path.exists():
        # Mở browser độc lập để xử lý việc lấy token
        context = browser.new_context(
            base_url=os.getenv("BASE_URL"),
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        # Gọi trực tiếp module để tránh vòng lặp import (circular import)
        from tests.pages.login_page import LoginPage
        from tests.utils.test_data_factory import TestDataFactory
        
        valid_user = TestDataFactory.get_valid_user()
        
        login_page = LoginPage(page).open()
        login_page.login_as(valid_user.get("email"), valid_user.get("password"))
        
        # Đợi load xong để chắc chắn có token (URL không còn /login)
        page.wait_for_url(lambda url: "login" not in url, timeout=15000)
        
        # Lưu storage state
        context.storage_state(path=state_path)
        context.close()
    
    yield state_path


# ---------------------------------------------------------------------------
# Function-scoped fixtures (isolated per test)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def context(browser: Browser, request: pytest.FixtureRequest) -> BrowserContext:
    trace_dir = Path("artifacts/traces")
    video_dir = Path("artifacts/videos")
    
    trace_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    base_url = os.getenv("BASE_URL")
    if not base_url:
        raise ValueError("BASE_URL must be set before running browser tests")

    auth_state = Path(os.getenv("AUTH_STATE", "artifacts/auth/user-state.json"))
    context_options: dict = {
        "base_url": base_url,
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "record_video_dir": str(video_dir),
    }

    # CHỈ load storage_state vào context NẾU testcase đó có xin dùng fixture 'authenticated_session'
    if "authenticated_session" in request.fixturenames and auth_state.exists():
        context_options["storage_state"] = str(auth_state)

    context = browser.new_context(**context_options)
    context.set_default_timeout(int(os.getenv("DEFAULT_TIMEOUT", "30000")))
    context.set_default_navigation_timeout(int(os.getenv("NAVIGATION_TIMEOUT", "60000")))
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    try:
        yield context
    finally:
        test_name = request.node.name
        failed = (
            (getattr(request.node, "rep_setup", None) is not None and request.node.rep_setup.failed) or
            (getattr(request.node, "rep_call", None) is not None and request.node.rep_call.failed)
        )
        try:
            if failed:
                trace_path = trace_dir / f"{test_name}.zip"
                context.tracing.stop(path=trace_path)
                try:
                    allure.attach.file(
                        str(trace_path),
                        name="Playwright Trace",
                        extension="zip",
                    )
                except Exception as exc:
                    print(f"[WARN] Could not attach trace: {exc}")
            else:
                context.tracing.stop()
        finally:
            context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext, request: pytest.FixtureRequest) -> Page:
    page = context.new_page()
    try:
        yield page
    finally:
        failed = (
            (getattr(request.node, "rep_setup", None) is not None and request.node.rep_setup.failed) or
            (getattr(request.node, "rep_call", None) is not None and request.node.rep_call.failed)
        )
        if failed and not page.is_closed():
            try:
                allure.attach(
                    page.screenshot(full_page=True),
                    name="Failure Screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception as exc:
                print(f"[WARN] Could not capture failure screenshot: {exc}")
        if not page.is_closed():
            try:
                # Wait 1s so video/trace can record the final state before closing
                page.wait_for_timeout(1000)
            except Exception:
                pass
            page.close()
            
        if page.video:
            if failed:
                test_name = request.node.name
                new_video_path = Path("artifacts/videos") / f"{test_name}.webm"
                try:
                    page.video.save_as(new_video_path)
                    allure.attach.file(
                        str(new_video_path),
                        name="Execution Video",
                        attachment_type=allure.attachment_type.WEBM
                    )
                    page.video.delete()
                except Exception as e:
                    print(f"[WARN] Could not save/attach video: {e}")
            else:
                try:
                    page.video.delete()
                except Exception:
                    pass

@pytest.fixture(autouse=True)
def _allure_browser_parameter():
    """Automatically adds the BROWSER environment variable as a parameter in Allure.
    This prevents tests run on different browsers from being merged as retries of the same test."""
    browser_name = os.getenv("BROWSER", "chromium").lower()
    allure.dynamic.parameter("browser", browser_name)
