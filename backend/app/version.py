"""Centralized version utility for the backend.

Order of precedence:
- project.version from pyproject.toml
- fallback "0.0.0-dev"
"""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path

logger = logging.getLogger(__name__)


def get_version() -> str:
    # Attempt to read pyproject.toml next to this file (backend root)
    try:
        project_root = Path(__file__).resolve().parents[1]  # backend/
        pyproject = project_root / "pyproject.toml"
        if pyproject.is_file():
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            version = data.get("project", {}).get("version")
            if isinstance(version, str) and version:
                return version
    except Exception:
        logger.exception("Failed to read version from pyproject.toml")

    return "0.0.0-dev"
