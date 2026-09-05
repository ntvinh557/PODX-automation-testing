"""conftest.py – Root conftest for Playwright Python test suite.

IMPORTANT: This file MUST live at the project root (same level as pytest.ini).
pytest auto-discovers hooks and fixtures defined here for the entire test suite.

DO NOT place pytest hooks (e.g. pytest_runtest_makereport) in any other module
(e.g. BaseTest.py) – they will silently be ignored.
"""
from __future__ import annotations

import os

import pytest
from playwright.sync_api import Browser, Playwright, sync_playwright


# ---------------------------------------------------------------------------
# Hook: expose test result to fixtures (required for screenshot-on-failure)
# ---------------------------------------------------------------------------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
    """Attach test result to ``item.rep_call`` so the ``page`` fixture can
    detect failures and capture a screenshot before teardown.

    Filter to ``call.when == "call"`` to avoid overwriting with the result
    of the setup or teardown phases.
    """
    outcome = yield
    rep = outcome.get_result()
    if call.when == "call":
        item.rep_call = rep


# ---------------------------------------------------------------------------
# Session-scoped fixtures (shared across all workers in pytest-xdist)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def playwright() -> Playwright:
    """Start a single Playwright instance for the entire test session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Browser:
    """Launch one browser process per session.

    Override ``BROWSER`` env var to switch engine: chromium | firefox | webkit.
    """
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
