#!/usr/bin/env python3
"""
Version bump script for BudgetWise.

Usage: python scripts/bump_version.py [major|minor|patch|set <x.y.z>]

It updates:
- frontend/package.json "version"
- backend/pyproject.toml [project].version

Then prints the new version. It does not create git tags by itself; the CI can tag after running this.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_PKG = ROOT / "frontend" / "package.json"
BACKEND_PYPROJECT = ROOT / "backend" / "pyproject.toml"


def ensure_files() -> None:
    missing = [p for p in (FRONTEND_PKG, BACKEND_PYPROJECT) if not p.exists()]
    if missing:
        paths = ", ".join(str(p) for p in missing)
        print(f"Missing required file(s): {paths}", file=sys.stderr)
        raise SystemExit(2)


def read_frontend_version() -> str:
    data = json.loads(FRONTEND_PKG.read_text(encoding="utf-8"))
    return str(data.get("version", "0.0.0"))


def write_frontend_version(version: str) -> None:
    data = json.loads(FRONTEND_PKG.read_text(encoding="utf-8"))
    data["version"] = version
    FRONTEND_PKG.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def read_backend_version() -> str:
    text = BACKEND_PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'(?m)^\s*version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', text)
    return m.group(1) if m else "0.0.0"


def write_backend_version(version: str) -> None:
    text = BACKEND_PYPROJECT.read_text(encoding="utf-8")
    # isolate the [project] section (non-greedy up to next section or EOF)
    sec = re.search(r'(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)', text)
    if not sec:
        print("Missing [project] section in backend/pyproject.toml", file=sys.stderr)
        raise SystemExit(2)
    block = sec.group(1)
    # Use a function replacement to avoid back-reference ambiguity (which caused
    # 'invalid group reference' errors when digits directly followed a numbered group).
    pattern = r'(?m)^(\s*version\s*=\s*["\'])\d+\.\d+\.\d+(["\'][^\n]*$)'
    def _repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{version}{match.group(2)}"
    new_block, count = re.subn(pattern, _repl, block)
    if count == 0:
        print('No version key like: version = "X.Y.Z" inside [project]', file=sys.stderr)
        raise SystemExit(2)
    new_text = text[:sec.start(1)] + new_block + text[sec.end(1):]
    BACKEND_PYPROJECT.write_text(new_text, encoding="utf-8")


def bump(ver: str, mode: str) -> str:
    major, minor, patch = map(int, ver.split("."))
    if mode == "major":
        return f"{major + 1}.0.0"
    if mode == "minor":
        return f"{major}.{minor + 1}.0"
    if mode == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError("mode must be major|minor|patch")


def main(argv: list[str]) -> int:
    ensure_files()
    semver = re.compile(r"^\d+\.\d+\.\d+$")
    if len(argv) < 2:
        print("Usage: bump_version.py [major|minor|patch|set <x.y.z>]")
        return 2

    if argv[1] == "set":
        if len(argv) != 3 or not re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", argv[2]):
            print("Usage: bump_version.py set <x.y.z>")
            return 2
        new_version = argv[2]
    else:
        mode = argv[1]
        if mode not in {"major", "minor", "patch"}:
            print("Usage: bump_version.py [major|minor|patch|set <x.y.z>]")
            return 2
        # Source of truth: frontend/package.json
        current = read_frontend_version()
        if not semver.match(current):
            print(
                f'frontend/package.json "version" must be X.Y.Z (got: {current})',
                file=sys.stderr,
            )
            return 2
        new_version = bump(current, mode)

    write_backend_version(new_version)
    write_frontend_version(new_version)
    print(new_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
