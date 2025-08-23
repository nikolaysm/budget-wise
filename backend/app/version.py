"""Centralized version utility for the backend.

Order of precedence:
- project.version from pyproject.toml
- fallback "0.0.0-dev"
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore


def get_version() -> str:
    # Attempt to read pyproject.toml next to this file (backend root)
    try:
        if tomllib is None:
            raise RuntimeError("tomllib unavailable")
        project_root = Path(__file__).resolve().parents[1]  # backend/
        pyproject = project_root / "pyproject.toml"
        if pyproject.is_file():
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            version = data.get("project", {}).get("version")
            if isinstance(version, str) and version:
                return version
    except Exception:
        pass

    return "0.0.0-dev"
