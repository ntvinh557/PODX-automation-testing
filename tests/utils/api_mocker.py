"""api_mocker.py - Network Mocking Layer for API Simulation."""
import json
import os
from typing import Optional

from playwright.sync_api import Page, Route

from tests.utils.settings import settings

class APIMocker:
    """Helper class to mock API responses, keeping network logic out of test scripts."""

    def __init__(self, page: Page):
        self.page = page
        self.api_url = settings.api_url
        self.login_endpoint = f"{self.api_url}/login/"

    def mock_login_error(self, status: int, error_message: str, headers: Optional[dict] = None) -> None:
        """Mock the login endpoint to return a generic JSON error."""
        def fulfill_route(route: Route) -> None:
            route.fulfill(
                status=status,
                headers=headers or {},
                content_type="application/json",
                body=json.dumps({"error": error_message}),
            )
        self.page.route(self.login_endpoint, fulfill_route)

    def mock_login_delayed_success(self, delay_ms: int, body: dict) -> None:
        """Mock the login endpoint with a delayed response to simulate network latency."""
        import time
        def delayed_fulfill(route: Route) -> None:
            time.sleep(delay_ms / 1000.0)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(body),
            )
        self.page.route(self.login_endpoint, delayed_fulfill)

    def mock_login_custom_response(self, status: int, body: dict) -> None:
        """Mock the login endpoint to return a specific status and JSON body."""
        self.page.route(
            self.login_endpoint,
            lambda route: route.fulfill(
                status=status,
                content_type="application/json",
                body=json.dumps(body),
            )
        )
