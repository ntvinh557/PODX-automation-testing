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
        self.cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS, PUT, DELETE",
            "Access-Control-Allow-Headers": "*",
        }

    def _handle_route(self, route: Route, status: int, body: dict, custom_headers: Optional[dict] = None) -> None:
        """Centralized route handler to deal with CORS preflight and headers."""
        if route.request.method == "OPTIONS":
            route.fulfill(status=204, headers=self.cors_headers)
            return

        headers = {**self.cors_headers, **(custom_headers or {})}
        route.fulfill(
            status=status,
            headers=headers,
            content_type="application/json",
            body=json.dumps(body),
        )

    def mock_login_error(self, status: int, error_message: str, headers: Optional[dict] = None) -> None:
        """Mock the login endpoint to return a generic JSON error."""
        self.page.route(
            self.login_endpoint, 
            lambda route: self._handle_route(route, status, {"message": error_message, "error": error_message}, headers)
        )

    def mock_login_manual_fulfill(self) -> list[Route]:
        """Intercept the route but do not fulfill it automatically so the test can assert intermediate UI states."""
        routes = []
        def manual_handler(route: Route) -> None:
            if route.request.method == "OPTIONS":
                self._handle_route(route, 204, {})
            else:
                routes.append(route)
        self.page.route(self.login_endpoint, manual_handler)
        return routes

    def mock_login_custom_response(self, status: int, body: dict) -> None:
        """Mock the login endpoint to return a specific status and JSON body."""
        self.page.route(
            self.login_endpoint,
            lambda route: self._handle_route(route, status, body)
        )
