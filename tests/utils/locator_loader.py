"""locator_loader.py – Load and resolve locator contracts from YAML files."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


_LOCATOR_MAP_PATH = Path("tests/locator_map")


def load_locators(page_name: str) -> dict[str, Any]:
    """Load the locator contract YAML for the given page name."""
    yaml_file = _LOCATOR_MAP_PATH / f"{page_name}.yaml"
    if not yaml_file.exists():
        raise FileNotFoundError(
            f"Locator contract not found: {yaml_file}. "
            "Create tests/locator_map/{page_name}.yaml before running tests."
        )
    with yaml_file.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get(page_name, {})
