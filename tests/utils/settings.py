from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    base_url: str = field(default_factory=lambda: os.getenv("BASE_URL", "https://app.mpodx.com"))
    api_url: str = field(default_factory=lambda: os.getenv("API_URL", "**/controller.mpodx.com"))
    browser: str = field(default_factory=lambda: os.getenv("BROWSER", "chromium"))
    headless: bool = field(
        default_factory=lambda: os.getenv("HEADLESS", "true").lower() == "true"
    )
    default_timeout: int = field(
        default_factory=lambda: int(os.getenv("DEFAULT_TIMEOUT", "30000"))
    )
    navigation_timeout: int = field(
        default_factory=lambda: int(os.getenv("NAVIGATION_TIMEOUT", "60000"))
    )
    test_user_email: str = field(
        default_factory=lambda: os.getenv("TEST_USER_EMAIL", "")
    )
    test_user_password: str = field(
        default_factory=lambda: os.getenv("TEST_USER_PASSWORD", "")
    )


settings = Settings()
