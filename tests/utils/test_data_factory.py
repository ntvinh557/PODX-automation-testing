import json
import os
import re
from pathlib import Path
from typing import Dict, Any


def _resolve_env_vars(value: Any) -> Any:
    """Thay thế placeholder ``${VAR_NAME}`` bằng giá trị từ environment."""
    if not isinstance(value, str):
        return value
    return re.sub(
        r"\$\{([^}]+)\}",
        lambda m: os.getenv(m.group(1), m.group(0)),
        value,
    )


class TestDataFactory:
    """Factory class to load and manage test data."""

    @staticmethod
    def load_users() -> Dict[str, dict]:
        """Loads users from users.json and resolves environment variables."""
        data_path = Path("tests/data/users.json")
        if not data_path.exists():
            return {}
            
        raw_data: Dict[str, dict] = json.loads(data_path.read_text(encoding="utf-8"))
        
        # Resolve placeholders for all strings in the nested dictionary
        resolved_data = {}
        for user_key, user_dict in raw_data.items():
            resolved_data[user_key] = {
                k: _resolve_env_vars(v) for k, v in user_dict.items()
            }
        return resolved_data

    @staticmethod
    def get_valid_user() -> dict:
        users = TestDataFactory.load_users()
        return users.get("valid_user", {})

    @staticmethod
    def get_invalid_user() -> dict:
        users = TestDataFactory.load_users()
        return users.get("invalid_user", {})
